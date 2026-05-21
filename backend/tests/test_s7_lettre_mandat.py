"""S7 tests — lettre de mandat §6.3 OEAQ : template Jinja2, génération PDF/HTML/MD, pas de placeholder non rempli."""
import json
import sys
import base64
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_session(tmp_path, session_id="sess-s7-1", **extras):
    """Crée un dossier de session minimal + patche SESSIONS_DIR."""
    import api as _api
    session_dir = tmp_path / session_id
    session_dir.mkdir(parents=True)
    session = {
        "session_id": session_id,
        "session_dir": str(session_dir),
        "dossier_id": session_id,
        "status": "CREATED",
        "app_display_name": "123 Rue Exemple, Montréal",
        "app_date_reference": "2026-05-01",
        "app_property_type": "residentiel_unifamilial",
        "app_commanditaire": {
            "nom": "Jean Tremblay",
            "organisation": "Banque Nationale",
            "fin_evaluation": "hypothecaire",
        },
        "app_nom_evaluateur": "Marie Côté, É.A.",
        "app_honoraires": "1 200 $",
        "app_date_livraison": "2026-05-30",
        **extras,
    }
    (session_dir / "session.json").write_text(json.dumps(session), encoding="utf-8")
    original = _api.SESSIONS_DIR
    _api.SESSIONS_DIR = tmp_path
    return original, session_id


# ── TestTemplateRendering ──────────────────────────────────────────────────────

class TestTemplateRendering:
    """Tests du template Jinja2 en mode md — vérifie les variables critiques."""

    def test_template_exists(self):
        import api as _api
        template_path = _api.TEMPLATES_DIR / "lettre_mandat_residentiels.md"
        assert template_path.exists(), f"Template introuvable : {template_path}"

    def test_template_renders_commanditaire(self, tmp_path):
        import api as _api
        original, sid = _make_session(tmp_path)
        try:
            result = _api.app_generate_lettre_mandat({"session_id": sid, "format": "md"})
            assert "Jean Tremblay" in result["content"]
        finally:
            _api.SESSIONS_DIR = original

    def test_template_renders_adresse(self, tmp_path):
        import api as _api
        original, sid = _make_session(tmp_path)
        try:
            result = _api.app_generate_lettre_mandat({"session_id": sid, "format": "md"})
            assert "123 Rue Exemple" in result["content"]
        finally:
            _api.SESSIONS_DIR = original

    def test_template_renders_honoraires(self, tmp_path):
        import api as _api
        original, sid = _make_session(tmp_path)
        try:
            result = _api.app_generate_lettre_mandat({"session_id": sid, "format": "md"})
            assert "1 200 $" in result["content"]
        finally:
            _api.SESSIONS_DIR = original

    def test_template_renders_evaluateur(self, tmp_path):
        import api as _api
        original, sid = _make_session(tmp_path)
        try:
            result = _api.app_generate_lettre_mandat({"session_id": sid, "format": "md"})
            assert "Marie Côté" in result["content"]
        finally:
            _api.SESSIONS_DIR = original

    def test_template_renders_date_livraison(self, tmp_path):
        import api as _api
        original, sid = _make_session(tmp_path)
        try:
            result = _api.app_generate_lettre_mandat({"session_id": sid, "format": "md"})
            assert "2026-05-30" in result["content"]
        finally:
            _api.SESSIONS_DIR = original

    def test_template_renders_type_bien_label(self, tmp_path):
        import api as _api
        original, sid = _make_session(tmp_path)
        try:
            result = _api.app_generate_lettre_mandat({"session_id": sid, "format": "md"})
            assert "Résidentiel unifamilial" in result["content"]
        finally:
            _api.SESSIONS_DIR = original

    def test_template_renders_objet_hypothecaire(self, tmp_path):
        import api as _api
        original, sid = _make_session(tmp_path)
        try:
            result = _api.app_generate_lettre_mandat({"session_id": sid, "format": "md"})
            assert "financement hypothécaire" in result["content"].lower()
        finally:
            _api.SESSIONS_DIR = original

    def test_no_placeholder_when_all_fields_present(self, tmp_path):
        """Critère de done S7 : formulaire complet → aucun placeholder [XXX] dans la lettre."""
        import api as _api
        original, sid = _make_session(tmp_path)
        try:
            result = _api.app_generate_lettre_mandat({"session_id": sid, "format": "md"})
            content = result["content"]
            # Pas de placeholder non résolu
            assert "[COMMANDITAIRE]" not in content
            assert "[ADRESSE]" not in content
            assert "[HONORAIRES]" not in content
            assert "[DATE LIVRAISON]" not in content
            assert "[ÉVALUATEUR AGRÉÉ]" not in content
        finally:
            _api.SESSIONS_DIR = original

    def test_placeholder_when_honoraires_missing(self, tmp_path):
        """Sans honoraires → placeholder [HONORAIRES] attendu."""
        import api as _api
        original, sid = _make_session(tmp_path, app_honoraires=None)
        try:
            result = _api.app_generate_lettre_mandat({"session_id": sid, "format": "md"})
            assert "[HONORAIRES]" in result["content"]
        finally:
            _api.SESSIONS_DIR = original


# ── TestFormatsMd ─────────────────────────────────────────────────────────────

class TestFormatsMd:
    def test_format_md_returns_content_string(self, tmp_path):
        import api as _api
        original, sid = _make_session(tmp_path)
        try:
            result = _api.app_generate_lettre_mandat({"session_id": sid, "format": "md"})
            assert result["format"] == "md"
            assert isinstance(result["content"], str)
            assert result["filename"].endswith(".md")
        finally:
            _api.SESSIONS_DIR = original

    def test_format_html_returns_html_string(self, tmp_path):
        import api as _api
        original, sid = _make_session(tmp_path)
        try:
            result = _api.app_generate_lettre_mandat({"session_id": sid, "format": "html"})
            assert result["format"] == "html"
            assert "<html" in result["content"].lower() or "<!doctype" in result["content"].lower() or "<body" in result["content"].lower()
            assert result["filename"].endswith(".html")
        finally:
            _api.SESSIONS_DIR = original

    def test_format_pdf_returns_base64(self, tmp_path):
        import api as _api
        original, sid = _make_session(tmp_path)
        try:
            result = _api.app_generate_lettre_mandat({"session_id": sid, "format": "pdf"})
            assert result["format"] == "pdf"
            assert "content_b64" in result
            # Valide que c'est du vrai base64 décodable
            raw = base64.b64decode(result["content_b64"])
            assert len(raw) > 0
            assert result["filename"].endswith(".pdf")
        finally:
            _api.SESSIONS_DIR = original

    def test_invalid_format_raises(self, tmp_path):
        import api as _api
        original, sid = _make_session(tmp_path)
        try:
            with pytest.raises(ValueError, match="format"):
                _api.app_generate_lettre_mandat({"session_id": sid, "format": "docx"})
        finally:
            _api.SESSIONS_DIR = original


# ── TestValidation ────────────────────────────────────────────────────────────

class TestValidation:
    def test_missing_session_id_raises(self):
        import api as _api
        with pytest.raises(ValueError, match="session_id"):
            _api.app_generate_lettre_mandat({"format": "md"})

    def test_nonexistent_session_raises(self, tmp_path):
        import api as _api
        original = _api.SESSIONS_DIR
        _api.SESSIONS_DIR = tmp_path
        try:
            with pytest.raises(ValueError, match="introuvable"):
                _api.app_generate_lettre_mandat({"session_id": "no-such-session", "format": "md"})
        finally:
            _api.SESSIONS_DIR = original


# ── TestOeaqConformite ────────────────────────────────────────────────────────

class TestOeaqConformite:
    """Vérifie la présence des éléments §6.3 OEAQ obligatoires dans la lettre."""

    def test_lettre_mentions_oeaq(self, tmp_path):
        import api as _api
        original, sid = _make_session(tmp_path)
        try:
            result = _api.app_generate_lettre_mandat({"session_id": sid, "format": "md"})
            assert "OEAQ" in result["content"]
        finally:
            _api.SESSIONS_DIR = original

    def test_lettre_has_signature_blocks(self, tmp_path):
        import api as _api
        original, sid = _make_session(tmp_path)
        try:
            result = _api.app_generate_lettre_mandat({"session_id": sid, "format": "md"})
            content = result["content"]
            assert "Signature" in content
            assert "Commanditaire" in content
        finally:
            _api.SESSIONS_DIR = original

    def test_lettre_has_date_reference(self, tmp_path):
        import api as _api
        original, sid = _make_session(tmp_path)
        try:
            result = _api.app_generate_lettre_mandat({"session_id": sid, "format": "md"})
            assert "2026-05-01" in result["content"]
        finally:
            _api.SESSIONS_DIR = original

    def test_lettre_has_valeur_marchande(self, tmp_path):
        import api as _api
        original, sid = _make_session(tmp_path)
        try:
            result = _api.app_generate_lettre_mandat({"session_id": sid, "format": "md"})
            assert "Valeur marchande" in result["content"]
        finally:
            _api.SESSIONS_DIR = original
