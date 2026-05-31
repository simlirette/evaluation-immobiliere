# backend/tests/test_registre_foncier.py
"""Tests pour le module registre_foncier — HTML parsing, cache, scraping (mocké)."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Fixture HTML synthétique — structure SIRF validée 2026-05-21
# ---------------------------------------------------------------------------

# Table SIRF réelle : colonnes Date | Numéro d'inscription | Nature de l'acte |
# Qualité | Nom des parties | Remarques | Avis d'adresse | Radiations
# Prix dans la colonne Remarques. Vendeur/Acheteur via rowspan (2 rangées).

SIRF_HTML_VENTE_SIMPLE = """
<html><body>
<table>
  <tr>
    <td>2024-05-23</td>
    <td><a href="#">20 145 678</a></td>
    <td>Vente</td>
    <td>Vendeur</td>
    <td>TREMBLAY, Jean-Pierre</td>
    <td>848&nbsp;000,00&nbsp;$</td>
    <td></td>
    <td></td>
  </tr>
  <tr>
    <td></td>
    <td></td>
    <td></td>
    <td>Acheteur</td>
    <td>GAGNON, Marie-Andrée</td>
    <td></td>
    <td></td>
    <td></td>
  </tr>
</table>
</body></html>
"""

SIRF_HTML_VENTE_INLINE_PARTIES = """
<html><body>
<table>
  <tr>
    <td>2023-11-10</td>
    <td><a href="#">19 999 001</a></td>
    <td>Vente</td>
    <td>Vendeur</td>
    <td>DUMONT, Robert</td>
    <td>735 500,00 $</td>
    <td></td>
    <td></td>
  </tr>
</table>
</body></html>
"""

SIRF_HTML_MULTI_VENTES = """
<html><body>
<table>
  <tr>
    <td>2019-06-01</td>
    <td><a href="#">11 000 001</a></td>
    <td>Vente</td>
    <td>Vendeur</td>
    <td>ANCIENNE, Corp.</td>
    <td>300 000,00 $</td>
    <td></td><td></td>
  </tr>
  <tr>
    <td>2023-03-15</td>
    <td><a href="#">18 500 222</a></td>
    <td>Vente</td>
    <td>Vendeur</td>
    <td>RÉCENTE, Inc.</td>
    <td>1 200 000,00 $</td>
    <td></td><td></td>
  </tr>
</table>
</body></html>
"""

SIRF_HTML_SANS_VENTE = """
<html><body>
<table>
  <tr>
    <td>2022-01-01</td>
    <td><a href="#">15 000 000</a></td>
    <td>Hypothèque</td>
    <td>Créancier</td>
    <td>BANQUE X</td>
    <td></td><td></td><td></td>
  </tr>
</table>
</body></html>
"""

SIRF_HTML_PRIX_SANS_CENTS = """
<html><body>
<table>
  <tr>
    <td>2024-09-01</td>
    <td><a href="#">21 000 000</a></td>
    <td>Vente</td>
    <td>Vendeur</td>
    <td>VENDOR X</td>
    <td>500 000 $</td>
    <td></td><td></td>
  </tr>
</table>
</body></html>
"""


# ---------------------------------------------------------------------------
# Tests _format_lot_number
# ---------------------------------------------------------------------------

class TestFormatLotNumber:
    def test_7_digits(self):
        from engine.registre_foncier import _format_lot_number
        assert _format_lot_number(2274178) == " 2 274 178"

    def test_leading_space(self):
        from engine.registre_foncier import _format_lot_number
        result = _format_lot_number(1234567)
        assert result.startswith(" ")

    def test_1_000_000(self):
        from engine.registre_foncier import _format_lot_number
        assert _format_lot_number(1000000) == " 1 000 000"

    def test_small_lot(self):
        from engine.registre_foncier import _format_lot_number
        # 6-digit lot : 123456 → " 123 456"
        assert _format_lot_number(123456) == " 123 456"


# ---------------------------------------------------------------------------
# Tests _parse_index_html
# ---------------------------------------------------------------------------

class TestParseIndexHtml:
    def test_prix_extrait(self):
        from engine.registre_foncier import _parse_index_html
        result = _parse_index_html(SIRF_HTML_VENTE_SIMPLE)
        assert result["prix_vente"] == 848000.0

    def test_date_extraite(self):
        from engine.registre_foncier import _parse_index_html
        result = _parse_index_html(SIRF_HTML_VENTE_SIMPLE)
        assert result["date_vente"] == "2024-05-23"

    def test_source_doc_extrait(self):
        from engine.registre_foncier import _parse_index_html
        result = _parse_index_html(SIRF_HTML_VENTE_SIMPLE)
        assert result["source_doc"] == "20145678"

    def test_vendeur_via_rowspan(self):
        """Loi 25 : vendeur_hash présent (non vide), pas le nom brut."""
        from engine.registre_foncier import _parse_index_html, _anonymize_party
        result = _parse_index_html(SIRF_HTML_VENTE_SIMPLE)
        assert "vendeur" not in result, "Le nom brut vendeur ne doit pas être exposé (Loi 25)"
        assert "vendeur_hash" in result
        assert len(result["vendeur_hash"]) == 8  # SHA256[:8]

    def test_acheteur_via_rowspan(self):
        """Loi 25 : acheteur_hash présent (non vide), pas le nom brut."""
        from engine.registre_foncier import _parse_index_html
        result = _parse_index_html(SIRF_HTML_VENTE_SIMPLE)
        assert "acheteur" not in result, "Le nom brut acheteur ne doit pas être exposé (Loi 25)"
        assert "acheteur_hash" in result
        assert len(result["acheteur_hash"]) == 8

    def test_prix_sans_cents(self):
        from engine.registre_foncier import _parse_index_html
        result = _parse_index_html(SIRF_HTML_PRIX_SANS_CENTS)
        assert result["prix_vente"] == 500000.0

    def test_sans_vente_returns_empty(self):
        from engine.registre_foncier import _parse_index_html
        result = _parse_index_html(SIRF_HTML_SANS_VENTE)
        assert result == {}

    def test_multi_ventes_retourne_plus_recente(self):
        from engine.registre_foncier import _parse_index_html
        # rdOrdreAffch=C → chronologique → dernier = plus récent
        result = _parse_index_html(SIRF_HTML_MULTI_VENTES)
        assert result["prix_vente"] == 1200000.0
        assert result["date_vente"] == "2023-03-15"

    def test_vendeur_inline(self):
        """Loi 25 : vendeur_hash non vide même pour les parties inline."""
        from engine.registre_foncier import _parse_index_html
        result = _parse_index_html(SIRF_HTML_VENTE_INLINE_PARTIES)
        assert "vendeur" not in result
        assert "vendeur_hash" in result
        assert len(result["vendeur_hash"]) == 8


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
