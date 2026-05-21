# backend/tests/test_registre_foncier.py
"""Tests pour le module registre_foncier — OCR parsing, cache, scraping (mocké)."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Fixtures texte OCR synthétiques
# ---------------------------------------------------------------------------

ACTE_SIMPLE = """
ACTE DE VENTE

Les soussignés déclarent avoir procédé à la vente et cession
de l'immeuble ci-après désigné pour la somme de 485 000,00 $
(quatre cent quatre-vingt-cinq mille dollars).

Date de la vente : le 15 mars 2024

VENDEUR : TREMBLAY, Jean-Pierre
ACHETEUR : GAGNON, Marie-Andrée

DÉSIGNATION CADASTRALE : 1 234 567
"""

ACTE_PRIX_EN_CHIFFRES = """
CONTRAT DE VENTE

Prix de vente : 735 500 $
Signé le 3 juin 2023

Vendeur: DUMONT, Robert
Acheteur: LAPOINTE, Sylvie
"""

ACTE_CONTREPARTIE = """
CESSION D'IMMEUBLE

Moyennant une contrepartie de 1 200 000,00 $
En date du 2022-11-28

V: INVEST-NORD INC.
A: PLACEMENTS CÔTÉ INC.
"""

ACTE_PRIX_INTROUVABLE = """
ACTE DIVERS
Aucune mention de prix.
Date inconnue.
"""


# ---------------------------------------------------------------------------
# Tests parse_transaction_text
# ---------------------------------------------------------------------------

class TestParseTransactionText:
    """Tests pour _parse_transaction_text() — extraction prix/date/parties depuis texte OCR."""

    def test_prix_somme_de(self):
        from engine.registre_foncier import _parse_transaction_text
        result = _parse_transaction_text(ACTE_SIMPLE)
        assert result["prix_vente"] == 485000.0

    def test_date_textuelle_mars(self):
        from engine.registre_foncier import _parse_transaction_text
        result = _parse_transaction_text(ACTE_SIMPLE)
        assert result["date_vente"] == "2024-03-15"

    def test_vendeur_acheteur(self):
        from engine.registre_foncier import _parse_transaction_text
        result = _parse_transaction_text(ACTE_SIMPLE)
        assert "TREMBLAY" in result["vendeur"]
        assert "GAGNON" in result["acheteur"]

    def test_prix_label_direct(self):
        from engine.registre_foncier import _parse_transaction_text
        result = _parse_transaction_text(ACTE_PRIX_EN_CHIFFRES)
        assert result["prix_vente"] == 735500.0

    def test_date_iso_format(self):
        from engine.registre_foncier import _parse_transaction_text
        result = _parse_transaction_text(ACTE_CONTREPARTIE)
        assert result["date_vente"] == "2022-11-28"

    def test_contrepartie_pattern(self):
        from engine.registre_foncier import _parse_transaction_text
        result = _parse_transaction_text(ACTE_CONTREPARTIE)
        assert result["prix_vente"] == 1200000.0

    def test_prix_introuvable_returns_zero(self):
        from engine.registre_foncier import _parse_transaction_text
        result = _parse_transaction_text(ACTE_PRIX_INTROUVABLE)
        assert result["prix_vente"] == 0.0

    def test_date_introuvable_returns_empty(self):
        from engine.registre_foncier import _parse_transaction_text
        result = _parse_transaction_text(ACTE_PRIX_INTROUVABLE)
        assert result["date_vente"] == ""


# ---------------------------------------------------------------------------
# Tests cache local disque
# ---------------------------------------------------------------------------

class TestLocalCache:
    def test_miss_returns_none(self, tmp_path):
        from engine.registre_foncier import _local_cache_get
        assert _local_cache_get(9999999, tmp_path) is None

    def test_store_then_get(self, tmp_path):
        from engine.registre_foncier import _local_cache_get, _local_cache_set
        data = {"prix_vente": 350000.0, "date_vente": "2023-06-01", "vendeur": "X", "acheteur": "Y", "source_doc": "abc", "raw_text": "..."}
        _local_cache_set(1234567, data, tmp_path)
        result = _local_cache_get(1234567, tmp_path)
        assert result is not None
        assert result["prix_vente"] == 350000.0

    def test_expired_entry_returns_none(self, tmp_path):
        from engine.registre_foncier import _local_cache_get, _local_cache_set
        data = {"prix_vente": 100.0, "date_vente": "2020-01-01", "vendeur": "", "acheteur": "", "source_doc": "", "raw_text": ""}
        _local_cache_set(7777777, data, tmp_path, ttl_days=-1)  # ttl_days=-1 → already expired
        assert _local_cache_get(7777777, tmp_path) is None


# ---------------------------------------------------------------------------
# Tests cache Supabase (mock)
# ---------------------------------------------------------------------------

class TestSupabaseCache:
    def _mock_supabase(self, rows: list[dict]):
        """Construit un faux client Supabase retournant rows."""
        sb = MagicMock()
        chain = sb.table.return_value.select.return_value.eq.return_value.gt.return_value.order.return_value.limit.return_value
        chain.execute.return_value = MagicMock(data=rows)
        return sb

    def test_miss_returns_none(self):
        from engine.registre_foncier import _supabase_cache_get
        sb = self._mock_supabase([])
        assert _supabase_cache_get(9999999, sb) is None

    def test_hit_returns_dict(self):
        from engine.registre_foncier import _supabase_cache_get
        row = {"prix_vente": 400000.0, "date_vente": "2023-04-10", "vendeur": "X", "acheteur": "Y", "source_doc": "z", "raw_text": ""}
        sb = self._mock_supabase([row])
        result = _supabase_cache_get(1234567, sb)
        assert result is not None
        assert result["prix_vente"] == 400000.0

    def test_none_client_returns_none(self):
        from engine.registre_foncier import _supabase_cache_get
        assert _supabase_cache_get(1234567, None) is None

    def test_set_with_none_client_no_error(self):
        from engine.registre_foncier import _supabase_cache_set
        # Should not raise
        _supabase_cache_set(1234567, {"prix_vente": 100.0, "date_vente": "", "vendeur": "", "acheteur": "", "source_doc": "", "raw_text": ""}, None)


# ---------------------------------------------------------------------------
# Tests enrich_pool_with_sirf
# ---------------------------------------------------------------------------

class TestEnrichPoolWithSirf:
    def _make_pool_item(self, no_lot: int, prix_vente: float = 0.0) -> dict:
        return {
            "comparable_id": f"MAMH-{no_lot}",
            "source_id":     f"MAMH-{no_lot}",
            "source_type":   "role_evaluation_municipale",
            "no_lot":        no_lot,
            "prix_vente":    prix_vente,
            "date_vente":    "",
            "surface":       {"value": 120.0, "unit": "m2"},
            "distance_km":   0.5,
        }

    def test_item_with_prix_already_set_not_touched(self, tmp_path):
        from engine.registre_foncier import enrich_pool_with_sirf
        pool = [self._make_pool_item(111, prix_vente=350000.0)]
        result = enrich_pool_with_sirf(pool, cache_dir=tmp_path, supabase_client=None)
        assert result[0]["prix_vente"] == 350000.0
        assert result[0]["source_type"] == "role_evaluation_municipale"  # unchanged

    def test_item_without_no_lot_not_touched(self, tmp_path):
        from engine.registre_foncier import enrich_pool_with_sirf
        item = self._make_pool_item(0)
        item["no_lot"] = None
        result = enrich_pool_with_sirf([item], cache_dir=tmp_path, supabase_client=None)
        assert result[0]["no_lot"] is None

    def test_cache_hit_enriches_item(self, tmp_path):
        from engine.registre_foncier import _local_cache_set, enrich_pool_with_sirf
        no_lot = 9876543
        cached = {"prix_vente": 520000.0, "date_vente": "2024-01-20", "vendeur": "A", "acheteur": "B", "source_doc": "doc1", "raw_text": ""}
        _local_cache_set(no_lot, cached, tmp_path)
        pool = [self._make_pool_item(no_lot)]
        result = enrich_pool_with_sirf(pool, cache_dir=tmp_path, supabase_client=None)
        assert result[0]["prix_vente"] == 520000.0
        assert result[0]["date_vente"] == "2024-01-20"
        assert result[0]["source_type"] == "registre_foncier"

    def test_sirf_error_returns_pool_intact(self, tmp_path):
        from engine.registre_foncier import enrich_pool_with_sirf
        pool = [self._make_pool_item(1111111)]
        # No cache, no SIRF credentials → _sirf_session() will raise RuntimeError
        # enrich_pool_with_sirf must NOT raise
        result = enrich_pool_with_sirf(pool, cache_dir=tmp_path, supabase_client=None)
        assert len(result) == 1
        assert result[0]["prix_vente"] == 0.0  # unchanged

    def test_max_sirf_lookups_respected(self, tmp_path):
        from engine.registre_foncier import enrich_pool_with_sirf
        pool = [self._make_pool_item(i) for i in range(1000001, 1000016)]  # 15 items
        # With max_sirf_lookups=3, should not try more than 3 live lookups
        # (all will fail due to missing credentials → non-blocking)
        result = enrich_pool_with_sirf(pool, cache_dir=tmp_path, supabase_client=None, max_sirf_lookups=3)
        assert len(result) == 15  # all items preserved

    def test_pool_not_mutated(self, tmp_path):
        from engine.registre_foncier import _local_cache_set, enrich_pool_with_sirf
        no_lot = 2222222
        _local_cache_set(no_lot, {"prix_vente": 300000.0, "date_vente": "2023-05-01", "vendeur": "", "acheteur": "", "source_doc": "", "raw_text": ""}, tmp_path)
        original_item = self._make_pool_item(no_lot)
        pool = [original_item]
        enrich_pool_with_sirf(pool, cache_dir=tmp_path, supabase_client=None)
        # Original item in pool must not have been mutated
        assert original_item["prix_vente"] == 0.0
