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
