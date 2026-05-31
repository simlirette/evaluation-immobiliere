"""Phase 0 — Tests d'assainissement, conformité et sécurité.

T0.1  amu_analyse.md ne contient pas de sections investissement/QdV.
T0.2  check_conflit_interets déterministe par signal structuré.
T0.4  _auth_context fail-closed quand ENV=production et token absent.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ── T0.1 : sections investissement bannies de amu_analyse.md ─────────────────

_BANNED_TITLES = [
    "## Score composite d'investissement",
    "## Indice de qualité de vie",
    "## Score de risque global",
    "## Projection de valeur à 5 ans",
    "## Ratio prix/loyer",
    "## Coûts de possession totaux",
    "## Rendement locatif estimé",
    "## Score de marché synthétique",
    "## Alertes et signaux de risque",
    "## Estimation de valeur indicative",
    "## Profil de sécurité",
    "Score global",
]


def _build_amu_md(case_overrides: dict | None = None) -> str:
    from engine.runtime import _build_deterministic_payload  # type: ignore

    case: dict = {
        "dossier_id": "D-P0-001",
        "type_bien": "unifamiliale",
        "zone": "R2",
        "zone_code": "R2",
        # inject all investment fields to confirm they are stripped
        "score_investissement": {"score_investissement": 7.5, "recommandation": "Acheter"},
        "indice_qualite_vie": {"indice_qualite_vie": 8.0, "interpretation": "Excellent"},
        "score_risque": {"score_risque": 3.0, "categorie": "Faible"},
        "projection_valeur": {"valeur_base": 400_000, "taux_base_pct": 2.5},
        "ratio_prix_loyer": {"ratio_prix_loyer": 22.5, "signal": "Surcoté"},
        "couts_possession": {"total_mensuel": 2500},
        "rendement_locatif": {"taux_capitalisation_brut_pct": 4.5},
        "score_marche": {"score_marche": 6.0},
        "alertes": {"alertes": [{"niveau": "info", "categorie": "marché", "message": "Test"}]},
        "valeur_indicative": {"valeur_indicative_synthese": 410_000},
        "crime_stats": {"taux_criminalite_total": 3500.0, "ville": "Québec"},
        "score_global": {"score_global": 7.0, "grade": "B"},
    }
    if case_overrides:
        case.update(case_overrides)

    payload = _build_deterministic_payload("amu-analyst", "amu_analyse.md", case)
    return payload.get("_raw_md", "")


def test_amu_md_no_investment_sections():
    md = _build_amu_md()
    for title in _BANNED_TITLES:
        assert title not in md, f"Section investissement interdite trouvée : {title!r}"


def test_amu_md_retains_amu_sections():
    md = _build_amu_md()
    assert "## Critere 1" in md
    assert "## Critere 4" in md
    assert "## Conclusion UMPP" in md


# ── T0.2 : conflit d'intérêts déterministe ───────────────────────────────────

from engine.compliance import check_conflit_interets, ConflitResult


def test_conflit_c001_lien_evaluateur():
    case = {"commanditaire": {"lien_evaluateur": "ami personnel"}}
    r = check_conflit_interets(case)
    assert r.conflit_detecte
    assert "C001" in r.motif


def test_conflit_c002_valeur_cible():
    case = {"commanditaire": {"valeur_cible_conditionnelle": True}}
    r = check_conflit_interets(case)
    assert r.conflit_detecte
    assert "C002" in r.motif


def test_conflit_c003_interet_propriete():
    case = {"evaluateur": {"interet_propriete": True}}
    r = check_conflit_interets(case)
    assert r.conflit_detecte
    assert "C003" in r.motif


def test_conflit_aucun_signal():
    case = {"commanditaire": {"nom": "Banque XYZ"}, "evaluateur": {"nom": "Jean Martin"}}
    r = check_conflit_interets(case)
    assert not r.conflit_detecte
    assert r.motif == ""


def test_conflit_sans_cle_openai(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    case = {"commanditaire": {"lien_evaluateur": "frère"}}
    r = check_conflit_interets(case)
    assert r.conflit_detecte  # déterministe, pas besoin de LLM


# ── T0.4 : fail-closed auth en prod ──────────────────────────────────────────

def _make_handler(env_overrides: dict):
    """Crée un handler minimal avec les env vars overridées."""
    import http.server
    import io
    import socket

    class FakeSocket:
        def makefile(self, *a, **kw):
            return io.BytesIO(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")

        def getsockname(self):
            return ("127.0.0.1", 8080)

        def getpeername(self):
            return ("127.0.0.1", 12345)

        sendall = lambda self, *a, **kw: None  # noqa: E731

    for k, v in env_overrides.items():
        os.environ[k] = v
    try:
        from api import EvalRuntimeHandler  # type: ignore
        request = FakeSocket()
        client_address = ("127.0.0.1", 12345)
        server = type("S", (), {"server_address": ("127.0.0.1", 8080)})()
        with pytest.MonkeyPatch().context() as mp:
            # Suppress __init__ side effects
            handler = object.__new__(EvalRuntimeHandler)
            handler.headers = {}
            handler._auth_context_env = env_overrides
        # Patch os.environ directly and reinstantiate _auth_context
        import types
        handler.headers = type("H", (), {"get": lambda self, k, d="": env_overrides.get(f"_header_{k}", d)})()

        def _patched_auth(self=handler):
            # re-read from current os.environ
            return EvalRuntimeHandler._auth_context(handler)

        handler._auth_context = _patched_auth
        return handler
    finally:
        for k in env_overrides:
            os.environ.pop(k, None)


def test_fail_closed_no_token_prod(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("EVAL_RUNTIME_API_TOKEN", raising=False)

    from api import EvalRuntimeHandler  # type: ignore

    handler = object.__new__(EvalRuntimeHandler)
    handler.headers = type("H", (), {"get": staticmethod(lambda k, d="": "")})()

    ctx = EvalRuntimeHandler._auth_context(handler)
    assert ctx["authorized"] is False
    assert ctx["reason"] == "token_not_configured"


def test_fail_closed_no_token_require_auth(monkeypatch):
    monkeypatch.setenv("EVAL_RUNTIME_REQUIRE_AUTH", "1")
    monkeypatch.delenv("EVAL_RUNTIME_API_TOKEN", raising=False)
    monkeypatch.delenv("ENV", raising=False)

    from api import EvalRuntimeHandler  # type: ignore

    handler = object.__new__(EvalRuntimeHandler)
    handler.headers = type("H", (), {"get": staticmethod(lambda k, d="": "")})()

    ctx = EvalRuntimeHandler._auth_context(handler)
    assert ctx["authorized"] is False
    assert ctx["reason"] == "token_not_configured"


def test_local_dev_allowed_without_token(monkeypatch):
    monkeypatch.delenv("EVAL_RUNTIME_API_TOKEN", raising=False)
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("EVAL_RUNTIME_REQUIRE_AUTH", raising=False)

    from api import EvalRuntimeHandler  # type: ignore

    handler = object.__new__(EvalRuntimeHandler)
    handler.headers = type("H", (), {"get": staticmethod(lambda k, d="": "")})()

    ctx = EvalRuntimeHandler._auth_context(handler)
    assert ctx["authorized"] is True
    assert ctx["role"] == "local_dev"
