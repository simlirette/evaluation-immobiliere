"""Pure-function unit tests — no I/O, no sessions, no server."""
import sys
from pathlib import Path

# Allow importing api.py directly without the full package installed
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import (
    app_date_label,
    app_money,
    app_source_documents,
    app_surface_label,
    app_status_label,
)
from engine.orchestrator import (
    PlanOrchestrator,
    available_mandat_types,
    classify_dossier,
    load_plan_for_mandat,
)


# ── app_money ────────────────────────────────────────────────────────────────

class TestAppMoney:
    def test_integer(self):
        assert app_money(500000) == "500 000 $"

    def test_float_rounds(self):
        assert app_money(499999.9) == "500 000 $"

    def test_zero(self):
        assert app_money(0) == "0 $"

    def test_string_numeric(self):
        assert app_money("250000") == "250 000 $"

    def test_none_returns_dash(self):
        assert app_money(None) == "-"

    def test_empty_string_returns_dash(self):
        assert app_money("") == "-"

    def test_non_numeric_returns_dash(self):
        assert app_money("abc") == "-"

    def test_negative(self):
        result = app_money(-10000)
        assert "$" in result


# ── app_date_label ────────────────────────────────────────────────────────────

class TestAppDateLabel:
    def test_iso_datetime(self):
        assert app_date_label("2025-03-15T10:30:00") == "2025-03-15"

    def test_iso_with_z(self):
        assert app_date_label("2025-03-15T10:30:00Z") == "2025-03-15"

    def test_date_only(self):
        assert app_date_label("2025-03-15") == "2025-03-15"

    def test_none_returns_empty(self):
        assert app_date_label(None) == ""

    def test_empty_string_returns_empty(self):
        assert app_date_label("") == ""

    def test_invalid_returns_raw(self):
        assert app_date_label("not-a-date") == "not-a-date"

    def test_with_timezone_offset(self):
        assert app_date_label("2025-06-01T00:00:00+05:00") == "2025-06-01"


# ── app_surface_label ─────────────────────────────────────────────────────────

class TestAppSurfaceLabel:
    def test_basic(self):
        assert app_surface_label({"value": 120, "unit": "m²"}) == "120 m²"

    def test_no_value_returns_dash(self):
        assert app_surface_label({"value": None, "unit": "m²"}) == "-"

    def test_empty_value_returns_dash(self):
        assert app_surface_label({"value": "", "unit": "m²"}) == "-"

    def test_not_dict_returns_dash(self):
        assert app_surface_label("120 m²") == "-"
        assert app_surface_label(None) == "-"

    def test_no_unit(self):
        result = app_surface_label({"value": 80, "unit": ""})
        assert "80" in result


# ── app_source_documents ──────────────────────────────────────────────────────

class TestAppSourceDocuments:
    def test_empty_knowledge(self):
        assert app_source_documents({}) == []

    def test_sources_from_knowledge(self):
        knowledge = {
            "sources": {
                "items": [
                    {"source_id": "SRC-1", "source_type": "mls", "reliability_level": "A"},
                    {"source_id": "SRC-2", "source_type": "mpac"},
                ]
            }
        }
        docs = app_source_documents(knowledge)
        assert len(docs) == 2
        ids = [d["id"] for d in docs]
        assert "SRC-1" in ids
        assert "SRC-2" in ids

    def test_uploaded_docs_merged_from_session(self):
        knowledge = {}
        session = {
            "uploaded_documents": [
                {"id": "upl-1", "name": "Acte.pdf", "filename": "acte.pdf", "size_bytes": 204800},
            ]
        }
        docs = app_source_documents(knowledge, session)
        assert len(docs) == 1
        assert docs[0]["id"] == "upl-1"
        assert docs[0]["name"] == "Acte.pdf"
        assert "200" in docs[0]["sizeLabel"]  # 204800 // 1024 == 200

    def test_knowledge_and_uploaded_merged(self):
        knowledge = {
            "sources": {
                "items": [{"source_id": "SRC-1"}]
            }
        }
        session = {
            "uploaded_documents": [
                {"id": "upl-1", "name": "Doc.pdf", "filename": "doc.pdf", "size_bytes": 1024},
            ]
        }
        docs = app_source_documents(knowledge, session)
        assert len(docs) == 2

    def test_invalid_items_skipped(self):
        knowledge = {
            "sources": {
                "items": ["not-a-dict", None, {"source_id": "OK"}]
            }
        }
        docs = app_source_documents(knowledge)
        assert len(docs) == 1
        assert docs[0]["id"] == "OK"

    def test_no_session_is_fine(self):
        docs = app_source_documents({}, session=None)
        assert docs == []


# ── app_status_label ──────────────────────────────────────────────────────────

class TestAppStatusLabel:
    def test_complet(self):
        assert app_status_label({"package_status": "PRET_REVUE_EVALUATEUR_AGREE"}) == "complet"

    def test_en_cours_pret_revision(self):
        assert app_status_label({"status": "PRET_REVISION_FINALE"}) == "en-cours"

    def test_en_cours_a_revoir(self):
        assert app_status_label({"status": "A_REVOIR"}) == "en-cours"

    def test_brouillon_default(self):
        assert app_status_label({"status": "CREATED"}) == "brouillon"

    def test_empty_record(self):
        assert app_status_label({}) == "brouillon"


# ── classify_dossier ──────────────────────────────────────────────────────────

class TestClassifyDossier:
    def test_explicit_mandat_type(self):
        assert classify_dossier({"mandat_type": "commercial"}) == "commercial"

    def test_assurance_via_but_evaluation(self):
        assert classify_dossier({"but_evaluation": "fins d'assurance"}) == "assurance"

    def test_unifamilial_exact(self):
        assert classify_dossier({"type_bien": "residentiel_unifamilial"}) == "residentiel_standard"

    def test_duplex_exact(self):
        assert classify_dossier({"type_bien": "duplex"}) == "residentiel_multifamilial"

    def test_triplex_partial(self):
        assert classify_dossier({"type_bien": "triplex_clé_en_main"}) == "residentiel_multifamilial"

    def test_industriel_partial(self):
        assert classify_dossier({"type_bien": "entrepot_logistique"}) == "industriel"

    def test_terrain_exact(self):
        assert classify_dossier({"type_bien": "terrain_vacant"}) == "terrain"

    def test_immeuble_revenus(self):
        assert classify_dossier({"type_bien": "immeuble_revenus"}) == "immeuble_revenus"

    def test_empty_defaults_to_residentiel_standard(self):
        assert classify_dossier({}) == "residentiel_standard"

    def test_unknown_type_bien_defaults(self):
        assert classify_dossier({"type_bien": "xyz_inconnu"}) == "residentiel_standard"

    def test_case_insensitive_partial(self):
        assert classify_dossier({"type_bien": "PLEX"}) == "residentiel_multifamilial"

    def test_assurance_type_bien(self):
        assert classify_dossier({"type_bien": "assurance"}) == "assurance"


# ── load_plan_for_mandat ──────────────────────────────────────────────────────

class TestLoadPlanForMandat:
    def test_all_types_loadable(self):
        for mt in available_mandat_types():
            plan = load_plan_for_mandat(mt)
            assert plan.mandat_type == mt
            assert plan.format_rapport in {"abrege", "narratif_complet", "mise_a_jour"}
            assert len(plan.methodes_requises) >= 1
            assert plan.methode_preponderante in plan.methodes_requises

    def test_residentiel_standard_plan(self):
        plan = load_plan_for_mandat("residentiel_standard")
        assert plan.format_rapport == "abrege"
        assert "approche_comparative" in plan.methodes_requises
        assert plan.methode_preponderante == "approche_comparative"
        assert plan.umpp_requis is True

    def test_assurance_cout_only(self):
        plan = load_plan_for_mandat("assurance")
        assert plan.methodes_requises == ["approche_cout"]
        assert plan.methode_preponderante == "approche_cout"
        assert plan.umpp_requis is False

    def test_immeuble_revenus_preponderance(self):
        plan = load_plan_for_mandat("immeuble_revenus")
        assert plan.methode_preponderante == "approche_revenu"
        assert plan.format_rapport == "narratif_complet"

    def test_unknown_raises_key_error(self):
        import pytest
        with pytest.raises(KeyError, match="inconnu"):
            load_plan_for_mandat("type_inexistant")


# ── PlanOrchestrator ──────────────────────────────────────────────────────────

class TestPlanOrchestrator:
    def test_build_engine_returns_engine_and_plan(self):
        orch = PlanOrchestrator()
        case = {"dossier_id": "D-TEST", "type_bien": "residentiel_unifamilial"}
        engine, plan = orch.build_engine(case)
        assert engine is not None
        assert plan.mandat_type == "residentiel_standard"

    def test_enrich_case_adds_plan_fields(self):
        orch = PlanOrchestrator()
        case = {"dossier_id": "D-TEST", "type_bien": "duplex"}
        _, plan = orch.build_engine(case)
        enriched = orch.enrich_case(case, plan)
        assert enriched["mandat_type"] == "residentiel_multifamilial"
        assert "methodes_requises" in enriched
        assert enriched["dossier_id"] == "D-TEST"  # original preserved

    def test_enrich_case_does_not_mutate_original(self):
        orch = PlanOrchestrator()
        case = {"dossier_id": "D-TEST", "type_bien": "terrain"}
        _, plan = orch.build_engine(case)
        orch.enrich_case(case, plan)
        assert "mandat_type" not in case  # original untouched

    def test_explicit_mandat_type_in_case_respected(self):
        orch = PlanOrchestrator()
        case = {"dossier_id": "D-TEST", "type_bien": "maison", "mandat_type": "assurance"}
        _, plan = orch.build_engine(case)
        assert plan.mandat_type == "assurance"


# ── DEFAULT_SKILLS_BY_AGENT ───────────────────────────────────────────────────

class TestDefaultSkillsByAgent:
    def test_amu_analyst_in_default_skills(self):
        from engine.skills import DEFAULT_SKILLS_BY_AGENT
        assert "amu-analyst" in DEFAULT_SKILLS_BY_AGENT
        skills = DEFAULT_SKILLS_BY_AGENT["amu-analyst"]
        assert "analyse-amu" in skills
        assert "recherche-urbanisme-construction" in skills
        assert "recherche-normes-professionnelles" in skills

    def test_mandat_intake_in_default_skills(self):
        from engine.skills import DEFAULT_SKILLS_BY_AGENT
        assert "mandat-intake" in DEFAULT_SKILLS_BY_AGENT
        skills = DEFAULT_SKILLS_BY_AGENT["mandat-intake"]
        assert "redaction-lettre-mandat" in skills

    def test_fta_in_valuation_draft_skills(self):
        from engine.skills import DEFAULT_SKILLS_BY_AGENT
        assert "analyse-approche-fta" in DEFAULT_SKILLS_BY_AGENT["valuation-draft"]


# ── TestAmuDeterministic ──────────────────────────────────────────────────────

class TestAmuDeterministic:
    def test_umpp_conclusion_fields(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import RuntimeEngine
        engine = RuntimeEngine()
        case = {
            "dossier_id": "D-AMU-TEST",
            "type_bien": "residentiel_unifamilial",
            "zone": "R-2",
            "date_reference": "2026-05-01",
        }
        payload = engine._artifact_payload(
            "amu-analyst", "umpp_conclusion.json", case, "BROUILLON", [], []
        )
        assert payload["dossier_id"] == "D-AMU-TEST"
        assert payload["step"] == "amu-analyst"
        assert "umpp" in payload
        umpp = payload["umpp"]
        assert "usage_retenu" in umpp
        assert "criteres" in umpp
        criteres = umpp["criteres"]
        assert "physiquement_possible" in criteres
        assert "legalement_permis" in criteres
        assert "financierement_faisable" in criteres
        assert "maximalement_productif" in criteres
        assert "umpp_differe_usage_actuel" in umpp
        assert isinstance(payload.get("confidence"), float)

    def test_amu_analyse_md_fields(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import RuntimeEngine
        engine = RuntimeEngine()
        case = {
            "dossier_id": "D-AMU-TEST",
            "type_bien": "terrain_vacant",
            "zone": "C-1",
            "date_reference": "2026-05-01",
        }
        payload = engine._artifact_payload(
            "amu-analyst", "amu_analyse.md", case, "BROUILLON", [], []
        )
        assert payload["step"] == "amu-analyst"
        assert "_raw_md" in payload
        assert "AMU" in payload["_raw_md"] or "meilleur usage" in payload["_raw_md"].lower()


# ── TestPipelineStepCount ─────────────────────────────────────────────────────

class TestPipelineStepCount:
    def test_default_steps_has_seven(self):
        from engine.runtime import DEFAULT_STEPS
        assert len(DEFAULT_STEPS) == 7

    def test_mandat_intake_at_index_zero(self):
        from engine.runtime import DEFAULT_STEPS
        assert DEFAULT_STEPS[0].name == "mandat-intake"

    def test_data_facts_at_index_one(self):
        from engine.runtime import DEFAULT_STEPS
        assert DEFAULT_STEPS[1].name == "data-facts"

    def test_amu_analyst_at_index_two(self):
        from engine.runtime import DEFAULT_STEPS
        assert DEFAULT_STEPS[2].name == "amu-analyst"

    def test_amu_analyst_reads_fiche_bien(self):
        from engine.runtime import DEFAULT_STEPS
        amu_step = DEFAULT_STEPS[2]
        assert "fiche_bien.json" in amu_step.reads

    def test_amu_analyst_writes_umpp_conclusion(self):
        from engine.runtime import DEFAULT_STEPS
        amu_step = DEFAULT_STEPS[2]
        assert "umpp_conclusion.json" in amu_step.writes
        assert "amu_analyse.md" in amu_step.writes

    def test_mandat_intake_writes_lettre_mandat(self):
        from engine.runtime import DEFAULT_STEPS
        step = DEFAULT_STEPS[0]
        assert "lettre_mandat.md" in step.writes
        assert "conflit_interets.json" in step.writes

    def test_redaction_reads_lettre_mandat(self):
        from engine.runtime import DEFAULT_STEPS
        redaction = DEFAULT_STEPS[6]
        assert redaction.name == "redaction"
        assert "lettre_mandat.md" in redaction.reads


# ── TestMandatIntakeDeterministic ─────────────────────────────────────────────

class TestMandatIntakeDeterministic:
    def test_conflit_interets_fields(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import RuntimeEngine
        engine = RuntimeEngine()
        case = {
            "dossier_id": "D-MANDAT-TEST",
            "type_bien": "residentiel_unifamilial",
            "date_reference": "2026-05-12",
            "mandat_type": "residentiel_standard",
            "format_rapport": "abrege",
        }
        payload = engine._artifact_payload(
            "mandat-intake", "conflit_interets.json", case, "BROUILLON", [], []
        )
        assert payload["dossier_id"] == "D-MANDAT-TEST"
        assert payload["step"] == "mandat-intake"
        assert payload["artifact"] == "conflit_interets.json"
        assert payload["conflit_detecte"] is False
        assert payload["verification_completee"] is True
        assert "commentaire" in payload

    def test_lettre_mandat_md_raw_md(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import RuntimeEngine
        engine = RuntimeEngine()
        case = {
            "dossier_id": "D-MANDAT-TEST",
            "type_bien": "residentiel_unifamilial",
            "date_reference": "2026-05-12",
            "mandat_type": "residentiel_standard",
            "format_rapport": "abrege",
        }
        payload = engine._artifact_payload(
            "mandat-intake", "lettre_mandat.md", case, "BROUILLON", [], []
        )
        assert payload["step"] == "mandat-intake"
        assert "_raw_md" in payload
        assert "Lettre de mandat" in payload["_raw_md"] or "mandat" in payload["_raw_md"].lower()


# ── TestCommanditaireInCase ───────────────────────────────────────────────────

class TestCommanditaireInCase:
    def test_commanditaire_merged_from_body(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from api import load_case_from_body
        body = {
            "commanditaire": {
                "nom": "Banque Nationale",
                "organisation": "Financement immobilier",
                "fin_evaluation": "hypothecaire",
            }
        }
        case, _ = load_case_from_body(body)
        assert case["commanditaire"]["nom"] == "Banque Nationale"
        assert case["commanditaire"]["organisation"] == "Financement immobilier"
        assert case["commanditaire"]["fin_evaluation"] == "hypothecaire"

    def test_commanditaire_defaults_when_absent(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from api import load_case_from_body
        case, _ = load_case_from_body({})
        # commanditaire key absent — no crash, no injection
        assert "commanditaire" not in case

    def test_commanditaire_nom_default_placeholder(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from api import load_case_from_body
        body = {"commanditaire": {"nom": "", "fin_evaluation": "succession"}}
        case, _ = load_case_from_body(body)
        assert case["commanditaire"]["nom"] == "[COMMANDITAIRE]"


# ── TestLettreMandat_Commanditaire ────────────────────────────────────────────

class TestLettreMandat_Commanditaire:
    def test_lettre_mandat_uses_commanditaire_nom(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import RuntimeEngine
        engine = RuntimeEngine()
        case = {
            "dossier_id": "D-CMD-TEST",
            "type_bien": "residentiel_unifamilial",
            "date_reference": "2026-05-13",
            "mandat_type": "residentiel_standard",
            "format_rapport": "abrege",
            "commanditaire": {
                "nom": "Banque Nationale",
                "organisation": "Financement immobilier",
                "fin_evaluation": "hypothecaire",
            },
        }
        payload = engine._artifact_payload(
            "mandat-intake", "lettre_mandat.md", case, "BROUILLON", [], []
        )
        assert "[COMMANDITAIRE]" not in payload["_raw_md"]
        assert "Banque Nationale" in payload["_raw_md"]

    def test_lettre_mandat_placeholder_when_no_commanditaire(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import RuntimeEngine
        engine = RuntimeEngine()
        case = {
            "dossier_id": "D-CMD-TEST",
            "type_bien": "residentiel_unifamilial",
            "date_reference": "2026-05-13",
            "mandat_type": "residentiel_standard",
            "format_rapport": "abrege",
        }
        payload = engine._artifact_payload(
            "mandat-intake", "lettre_mandat.md", case, "BROUILLON", [], []
        )
        assert "[COMMANDITAIRE]" in payload["_raw_md"]


# ── TestConflit_Deterministic_False ──────────────────────────────────────────

class TestConflit_Deterministic_False:
    def test_conflit_detecte_false_without_llm(self):
        """Without LLM (no OPENAI_API_KEY), conflit_detecte stays False."""
        import sys
        import os
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import RuntimeEngine
        original_key = os.environ.pop("OPENAI_API_KEY", None)
        try:
            engine = RuntimeEngine()
            case = {
                "dossier_id": "D-CONFLIT-TEST",
                "type_bien": "residentiel_unifamilial",
                "date_reference": "2026-05-13",
                "mandat_type": "residentiel_standard",
                "format_rapport": "abrege",
                "commanditaire": {"nom": "BNC", "organisation": "", "fin_evaluation": "hypothecaire"},
            }
            payload = engine._artifact_payload(
                "mandat-intake", "conflit_interets.json", case, "BROUILLON", [], []
            )
            assert payload["conflit_detecte"] is False
            assert payload["verification_completee"] is True
        finally:
            if original_key is not None:
                os.environ["OPENAI_API_KEY"] = original_key


# ── TestConflit_Gate_Blocks ───────────────────────────────────────────────────

class TestConflit_Gate_Blocks:
    def test_pipeline_raises_on_conflit_detecte(self, tmp_path):
        """run_case_data raises PipelineConflitError when conflit_detecte: True in artifact."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import RuntimeEngine, PipelineConflitError, DEFAULT_STEPS

        engine = RuntimeEngine(steps=DEFAULT_STEPS[:1])  # mandat-intake only
        case = {
            "dossier_id": "D-GATE-TEST",
            "type_bien": "residentiel_unifamilial",
            "date_reference": "2026-05-13",
            "mandat_type": "residentiel_standard",
            "format_rapport": "abrege",
        }

        import pytest

        original_payload = engine._artifact_payload

        def patched_payload(step, artifact, case, status, blocking, warnings, valuation_values=None):
            p = original_payload(step, artifact, case, status, blocking, warnings, valuation_values)
            if step == "mandat-intake" and artifact == "conflit_interets.json":
                p["conflit_detecte"] = True
                p["conflit_motif"] = "Test: conflit injecte"
            return p

        engine._artifact_payload = patched_payload

        with pytest.raises(PipelineConflitError, match="Test: conflit injecte"):
            engine.run_case_data(case, tmp_path, source_fixture="test", case_stem="test", case_subdir=True)

    def test_pipeline_no_exception_when_conflit_false(self, tmp_path):
        """run_case_data runs normally when conflit_detecte: False."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import RuntimeEngine, DEFAULT_STEPS

        engine = RuntimeEngine(steps=DEFAULT_STEPS[:1])
        case = {
            "dossier_id": "D-GATE-OK-TEST",
            "type_bien": "residentiel_unifamilial",
            "date_reference": "2026-05-13",
            "mandat_type": "residentiel_standard",
            "format_rapport": "abrege",
        }
        result = engine.run_case_data(case, tmp_path, source_fixture="test", case_stem="test", case_subdir=True)
        assert result["dossier_id"] == "D-GATE-OK-TEST"


# ── TestConflit_ForceOverride ─────────────────────────────────────────────────

class TestConflit_ForceOverride:
    def test_force_conflit_continue_bypasses_gate(self, tmp_path):
        """force_conflit_continue: True lets pipeline continue despite conflit_detecte."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import RuntimeEngine, DEFAULT_STEPS

        engine = RuntimeEngine(steps=DEFAULT_STEPS[:1])
        case = {
            "dossier_id": "D-OVERRIDE-TEST",
            "type_bien": "residentiel_unifamilial",
            "date_reference": "2026-05-13",
            "mandat_type": "residentiel_standard",
            "format_rapport": "abrege",
            "force_conflit_continue": True,
        }

        original_payload = engine._artifact_payload

        def patched_payload(step, artifact, case, status, blocking, warnings, valuation_values=None):
            p = original_payload(step, artifact, case, status, blocking, warnings, valuation_values)
            if step == "mandat-intake" and artifact == "conflit_interets.json":
                p["conflit_detecte"] = True
                p["conflit_motif"] = "Test: conflit injecte"
            return p

        engine._artifact_payload = patched_payload

        result = engine.run_case_data(case, tmp_path, source_fixture="test", case_stem="test", case_subdir=True)
        assert result["dossier_id"] == "D-OVERRIDE-TEST"


# ── TestConflitLLMParsing ─────────────────────────────────────────────────────

class TestConflitLLMParsing:
    def _make_mock_openai(self, llm_response: str):
        """Build a mock openai module whose OpenAI().chat.completions.create() returns llm_response."""
        import unittest.mock
        mock_resp = unittest.mock.MagicMock()
        mock_resp.choices[0].message.content = llm_response
        mock_client = unittest.mock.MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp
        mock_openai_module = unittest.mock.MagicMock()
        mock_openai_module.OpenAI.return_value = mock_client
        return mock_openai_module

    def test_conflit_detecte_set_on_sentinel_prefix(self):
        """_enrich_artifact_llm sets conflit_detecte: True when LLM returns CONFLIT_DETECTE: prefix."""
        import sys
        import os
        import unittest.mock
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import RuntimeEngine, RuntimeStep

        engine = RuntimeEngine()
        payload = {
            "dossier_id": "D-LLM-TEST",
            "step": "mandat-intake",
            "artifact": "conflit_interets.json",
            "conflit_detecte": False,
            "verification_completee": True,
            "commentaire": "V0 deterministe.",
            "analyse_conflit": "",
        }
        case = {"dossier_id": "D-LLM-TEST", "type_bien": "residentiel_unifamilial"}
        step = RuntimeStep(
            name="mandat-intake",
            reads=[],
            writes=["conflit_interets.json"],
            skills=[],
            agent_config="AGENTCONFIG-MANDAT-INTAKE-V0.yaml",
        )
        llm_response = "CONFLIT_DETECTE: Lien familial avec le vendeur\n\nAnalyse détaillée..."
        mock_openai = self._make_mock_openai(llm_response)

        with unittest.mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with unittest.mock.patch.dict(sys.modules, {"openai": mock_openai}):
                result = engine._enrich_artifact_llm(step, "conflit_interets.json", payload, case)

        assert result["conflit_detecte"] is True
        assert result["conflit_motif"] == "Lien familial avec le vendeur"
        assert result["analyse_conflit"] == llm_response

    def test_no_conflit_when_llm_returns_normal_response(self):
        """_enrich_artifact_llm leaves conflit_detecte: False when LLM returns normal text."""
        import sys
        import os
        import unittest.mock
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import RuntimeEngine, RuntimeStep

        engine = RuntimeEngine()
        payload = {
            "dossier_id": "D-LLM-OK-TEST",
            "step": "mandat-intake",
            "artifact": "conflit_interets.json",
            "conflit_detecte": False,
            "verification_completee": True,
            "commentaire": "V0 deterministe.",
            "analyse_conflit": "",
        }
        case = {"dossier_id": "D-LLM-OK-TEST", "type_bien": "residentiel_unifamilial"}
        step = RuntimeStep(
            name="mandat-intake",
            reads=[],
            writes=["conflit_interets.json"],
            skills=[],
            agent_config="AGENTCONFIG-MANDAT-INTAKE-V0.yaml",
        )
        llm_response = "Aucun conflit détecté. L'évaluateur est indépendant de toutes les parties."
        mock_openai = self._make_mock_openai(llm_response)

        with unittest.mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with unittest.mock.patch.dict(sys.modules, {"openai": mock_openai}):
                result = engine._enrich_artifact_llm(step, "conflit_interets.json", payload, case)

        assert result["conflit_detecte"] is False
        assert result["analyse_conflit"] == llm_response
