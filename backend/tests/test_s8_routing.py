"""S8 tests — LLM routing par tâche + templates rapport + estimation coût."""
import os
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ── TestLlmRoutingDict ────────────────────────────────────────────────────────

class TestLlmRoutingDict:
    def test_all_required_keys_present(self):
        from engine.llm_routing import LLM_ROUTING
        required_tasks = {
            "extraction_pdf",
            "parse_structured",
            "compliance_warnings",
            "amu_analyse",
            "redaction_rapport",
            "assistant_qa",
        }
        assert required_tasks.issubset(set(LLM_ROUTING.keys()))

    def test_redaction_uses_gpt4o(self):
        from engine.llm_routing import LLM_ROUTING
        assert LLM_ROUTING["redaction_rapport"] == "gpt-4o"

    def test_extraction_pdf_uses_gpt4o(self):
        from engine.llm_routing import LLM_ROUTING
        assert LLM_ROUTING["extraction_pdf"] == "gpt-4o"

    def test_assistant_qa_uses_mini(self):
        from engine.llm_routing import LLM_ROUTING
        assert LLM_ROUTING["assistant_qa"] == "gpt-4o-mini"

    def test_parse_structured_uses_mini(self):
        from engine.llm_routing import LLM_ROUTING
        assert LLM_ROUTING["parse_structured"] == "gpt-4o-mini"


# ── TestGetLlmModel ───────────────────────────────────────────────────────────

class TestGetLlmModel:
    def test_redaction_returns_gpt4o(self, monkeypatch):
        monkeypatch.delenv("OPENAI_MODEL", raising=False)
        monkeypatch.delenv("OPENAI_MODEL_REDACTION_RAPPORT", raising=False)
        from engine.llm_routing import get_llm_model
        assert get_llm_model("redaction_rapport") == "gpt-4o"

    def test_assistant_qa_returns_mini(self, monkeypatch):
        monkeypatch.delenv("OPENAI_MODEL", raising=False)
        monkeypatch.delenv("OPENAI_MODEL_ASSISTANT_QA", raising=False)
        from engine.llm_routing import get_llm_model
        assert get_llm_model("assistant_qa") == "gpt-4o-mini"

    def test_unknown_task_returns_fallback(self, monkeypatch):
        monkeypatch.delenv("OPENAI_MODEL", raising=False)
        from engine.llm_routing import get_llm_model
        assert get_llm_model("unknown_task_xyz") == "gpt-4o-mini"

    def test_task_specific_env_var_overrides(self, monkeypatch):
        monkeypatch.delenv("OPENAI_MODEL", raising=False)
        monkeypatch.setenv("OPENAI_MODEL_REDACTION_RAPPORT", "gpt-4o-128k")
        from engine.llm_routing import get_llm_model
        assert get_llm_model("redaction_rapport") == "gpt-4o-128k"

    def test_global_env_var_overrides_routing(self, monkeypatch):
        monkeypatch.setenv("OPENAI_MODEL", "gpt-3.5-turbo")
        monkeypatch.delenv("OPENAI_MODEL_ASSISTANT_QA", raising=False)
        from engine.llm_routing import get_llm_model
        assert get_llm_model("assistant_qa") == "gpt-3.5-turbo"

    def test_task_specific_takes_priority_over_global(self, monkeypatch):
        monkeypatch.setenv("OPENAI_MODEL", "gpt-3.5-turbo")
        monkeypatch.setenv("OPENAI_MODEL_REDACTION_RAPPORT", "gpt-4o")
        from engine.llm_routing import get_llm_model
        assert get_llm_model("redaction_rapport") == "gpt-4o"

    def test_no_env_var_uses_routing_table(self, monkeypatch):
        monkeypatch.delenv("OPENAI_MODEL", raising=False)
        monkeypatch.delenv("OPENAI_MODEL_EXTRACTION_PDF", raising=False)
        from engine.llm_routing import get_llm_model
        assert get_llm_model("extraction_pdf") == "gpt-4o"


# ── TestEstimateLlmCost ───────────────────────────────────────────────────────

class TestEstimateLlmCost:
    def test_gpt4o_cost_positive(self):
        from engine.llm_routing import estimate_llm_cost
        cost = estimate_llm_cost("gpt-4o", 1000, 500)
        assert cost > 0

    def test_gpt4o_mini_cheaper_than_gpt4o(self):
        from engine.llm_routing import estimate_llm_cost
        cost_full = estimate_llm_cost("gpt-4o", 1000, 500)
        cost_mini = estimate_llm_cost("gpt-4o-mini", 1000, 500)
        assert cost_mini < cost_full

    def test_zero_tokens_returns_zero(self):
        from engine.llm_routing import estimate_llm_cost
        assert estimate_llm_cost("gpt-4o", 0, 0) == 0.0

    def test_typical_rapport_cost_under_10_cents(self):
        """Un rapport résidentiel typique (~3k tokens in, ~2k out) doit coûter < $0.10."""
        from engine.llm_routing import estimate_llm_cost
        # gpt-4o: 3000 in + 2000 out
        cost = estimate_llm_cost("gpt-4o", 3000, 2000)
        assert cost < 0.10, f"Coût trop élevé : {cost:.4f} USD"

    def test_unknown_model_uses_fallback_rates(self):
        from engine.llm_routing import estimate_llm_cost
        cost = estimate_llm_cost("unknown-model-xyz", 1000, 500)
        assert cost > 0  # fallback rates applied

    def test_returns_float(self):
        from engine.llm_routing import estimate_llm_cost
        cost = estimate_llm_cost("gpt-4o-mini", 500, 200)
        assert isinstance(cost, float)


# ── TestRapportTemplates ──────────────────────────────────────────────────────

class TestRapportTemplates:
    def _templates_dir(self):
        return Path(__file__).resolve().parent.parent / "templates"

    def test_template_residentiel_exists(self):
        assert (self._templates_dir() / "rapport_residentiel_unifamilial.md").exists()

    def test_template_immeuble_revenus_exists(self):
        assert (self._templates_dir() / "rapport_immeuble_revenus.md").exists()

    def test_template_commercial_exists(self):
        assert (self._templates_dir() / "rapport_commercial.md").exists()

    def test_residentiel_template_has_section_reconciliation(self):
        content = (self._templates_dir() / "rapport_residentiel_unifamilial.md").read_text(encoding="utf-8")
        assert "RÉCONCILIATION" in content.upper()

    def test_residentiel_template_has_certification(self):
        content = (self._templates_dir() / "rapport_residentiel_unifamilial.md").read_text(encoding="utf-8")
        assert "CERTIFICATION" in content.upper()

    def test_residentiel_template_has_valeur_marchande(self):
        content = (self._templates_dir() / "rapport_residentiel_unifamilial.md").read_text(encoding="utf-8")
        assert "Valeur marchande" in content

    def test_immeuble_template_has_revenu_section(self):
        content = (self._templates_dir() / "rapport_immeuble_revenus.md").read_text(encoding="utf-8")
        assert "revenu" in content.lower()

    def test_templates_all_have_oeaq_mention(self):
        templates_dir = self._templates_dir()
        for template_name in [
            "rapport_residentiel_unifamilial.md",
            "rapport_immeuble_revenus.md",
            "rapport_commercial.md",
        ]:
            content = (templates_dir / template_name).read_text(encoding="utf-8")
            assert "OEAQ" in content, f"OEAQ manquant dans {template_name}"


# ── TestTemplateLoading ───────────────────────────────────────────────────────

class TestTemplateLoading:
    def test_load_residentiel_template(self):
        from engine.runtime import _load_rapport_template
        tmpl = _load_rapport_template("residentiel_unifamilial")
        assert tmpl is not None
        assert len(tmpl) > 100

    def test_load_immeuble_revenus_template(self):
        from engine.runtime import _load_rapport_template
        tmpl = _load_rapport_template("immeuble_revenus")
        assert tmpl is not None
        assert "revenu" in tmpl.lower()

    def test_condo_uses_residentiel_template(self):
        from engine.runtime import _load_rapport_template
        tmpl = _load_rapport_template("condo")
        assert tmpl is not None  # mapped to residentiel_unifamilial

    def test_unknown_type_uses_residentiel_fallback(self):
        from engine.runtime import _load_rapport_template
        tmpl = _load_rapport_template("bien_inconnu_xyz")
        # Falls back to rapport_residentiel_unifamilial.md
        assert tmpl is not None

    def test_prompt_includes_template_for_residentiel(self):
        from engine.runtime import _build_rapport_prompt_v2
        case = {
            "dossier_id": "D-TEST-S8",
            "type_bien": "residentiel_unifamilial",
            "adresse": "123 Rue Test",
            "zone": "Sherbrooke",
            "date_reference": "2026-05-20",
        }
        prompt = _build_rapport_prompt_v2(case, "abrege", {}, "BROUILLON", [], [])
        assert "STRUCTURE DU RAPPORT" in prompt
        # Template est tronqué à 3000 chars — vérifier une section dans la fenêtre (section 4)
        assert "APPROCHE PAR COMPARAISON" in prompt.upper()

    def test_prompt_includes_template_for_immeuble_revenus(self):
        from engine.runtime import _build_rapport_prompt_v2
        case = {
            "dossier_id": "D-TEST-S8-REV",
            "type_bien": "immeuble_revenus",
            "adresse": "456 Rue Revenus",
            "date_reference": "2026-05-20",
        }
        prompt = _build_rapport_prompt_v2(case, "abrege", {}, "BROUILLON", [], [])
        assert "STRUCTURE DU RAPPORT" in prompt


# ── TestGenerateBrouillonRegression ──────────────────────────────────────────

class TestGenerateBrouillonRegression:
    """Vérifie que generate_brouillon_rapport() retourne toujours un str (pas de régression S8)."""

    def test_returns_str_no_llm(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        from engine.runtime import generate_brouillon_rapport
        case = {
            "dossier_id": "D-S8-REG",
            "type_bien": "residentiel_unifamilial",
            "adresse": "Test",
            "date_reference": "2026-05-20",
            "zone": "Sherbrooke",
            "comparables": [],
        }
        result = generate_brouillon_rapport(case, {}, "BROUILLON", [], [], format="abrege")
        assert isinstance(result, str)
        assert len(result) > 100

    def test_returns_str_complet_format_no_llm(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        from engine.runtime import generate_brouillon_rapport
        case = {"dossier_id": "D-S8-COMPLET", "type_bien": "immeuble_revenus"}
        result = generate_brouillon_rapport(case, {}, "BROUILLON", [], [], format="complet")
        assert isinstance(result, str)
        assert len(result) > 100


# ── TestGenerateRapportLlmReturnType ─────────────────────────────────────────

class TestGenerateRapportLlmReturnType:
    def test_returns_none_without_api_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        from engine.runtime import _generate_rapport_llm
        result = _generate_rapport_llm("test prompt")
        assert result is None

    def test_returns_dict_when_mocked(self, monkeypatch):
        """Vérifie la structure du dict retourné quand LLM disponible (mock)."""
        import unittest.mock as mock

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.delenv("OPENAI_MODEL", raising=False)
        monkeypatch.delenv("OPENAI_MODEL_REDACTION_RAPPORT", raising=False)

        fake_usage = mock.MagicMock()
        fake_usage.prompt_tokens = 1500
        fake_usage.completion_tokens = 800

        fake_choice = mock.MagicMock()
        fake_choice.message.content = "Rapport généré par LLM mock."

        fake_resp = mock.MagicMock()
        fake_resp.choices = [fake_choice]
        fake_resp.usage = fake_usage

        fake_client = mock.MagicMock()
        fake_client.chat.completions.create.return_value = fake_resp

        with mock.patch("openai.OpenAI", return_value=fake_client):
            from engine.runtime import _generate_rapport_llm
            result = _generate_rapport_llm("prompt test", "abrege")

        assert result is not None
        assert "text" in result
        assert "model" in result
        assert "tokens_in" in result
        assert "tokens_out" in result
        assert "cost_usd" in result
        assert result["model"] == "gpt-4o"  # redaction_rapport routing
        assert result["tokens_in"] == 1500
        assert result["tokens_out"] == 800
        assert result["cost_usd"] > 0
        assert "Rapport généré" in result["text"]
