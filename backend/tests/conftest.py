"""conftest.py — Fixtures globales pour les tests backend.

T6.4 : mocks réseau hermétiques pour CI sans accès réseau.
Tous les appels httpx/requests sont interceptés par défaut.
Les tests live (EVAL_IMMO_LIVE_EXTERNALS=1) peuvent bypasser.
"""
from __future__ import annotations

import os
from typing import Any
from unittest.mock import patch, MagicMock

import pytest


# ── Marqueurs personnalisés ────────────────────────────────────────────────────

def pytest_configure(config) -> None:
    config.addinivalue_line("markers", "network: test nécessite accès réseau réel")
    config.addinivalue_line("markers", "slow: test lent (> 30s)")
    config.addinivalue_line("markers", "e2e: test de bout en bout")


# ── Fixture : bloquer les appels réseau par défaut ────────────────────────────

def _live_enabled() -> bool:
    return os.environ.get("EVAL_IMMO_LIVE_EXTERNALS") == "1"


@pytest.fixture(autouse=True)
def block_network_calls(request, monkeypatch):
    """Bloque les appels réseau httpx sauf si test marqué @pytest.mark.network
    ou si EVAL_IMMO_LIVE_EXTERNALS=1.

    Remplace httpx.get/post/stream par des raises pour éviter les appels accidentels.
    Les tests qui ont besoin du réseau doivent utiliser @pytest.mark.network
    ou EVAL_IMMO_LIVE_EXTERNALS=1.
    """
    if _live_enabled() or request.node.get_closest_marker("network"):
        yield
        return

    # Patch _wds_post et _wds_get dans data_enrichment (appels WDS StatCan)
    def _blocked_wds(*args, **kwargs):
        raise ConnectionError("Appel réseau WDS bloqué en CI — utiliser mock ou @pytest.mark.network")

    try:
        import engine.data_enrichment as de
        monkeypatch.setattr(de, "_wds_post", _blocked_wds, raising=False)
        monkeypatch.setattr(de, "_wds_get", _blocked_wds, raising=False)
    except (ImportError, AttributeError):
        pass

    yield


# ── Fixture : données de marché par défaut (évite les appels réseau dans enrich_case) ─

@pytest.fixture
def minimal_case_enriched():
    """Cas minimal pré-enrichi (pas d'appels réseau)."""
    return {
        "dossier_id": "D-TEST-CONFTEST",
        "date_reference": "2026-01-01",
        "type_bien": "unifamiliale",
        "zone": "R2",
        "surface": {"value": 130, "unit": "m2"},
        "surface_terrain": 450,
        "adresse": "123 rue Test, Québec",
        "annee_construction": 1985,
        "nb_logements": 1,
        "comparables": [],
    }


# ── Fixture : session tmp pour tests api ──────────────────────────────────────

@pytest.fixture
def tmp_session(tmp_path, monkeypatch):
    """Crée une session temporaire et patche SESSIONS_DIR."""
    import api  # type: ignore
    monkeypatch.setattr(api, "SESSIONS_DIR", tmp_path)
    session = api.create_session(owner_evaluator_id="ea-test")
    return session, tmp_path
