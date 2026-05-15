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


# ── TestIngestion_ExtractPDFText ──────────────────────────────────────────────

class TestIngestion_ExtractPDFText:
    def test_extracts_text_from_pdf_with_text_layer(self):
        import sys
        import unittest.mock
        mock_fitz = unittest.mock.MagicMock()
        mock_page = unittest.mock.MagicMock()
        mock_page.get_text.return_value = "Surface : 1200 pi²\nPrix : 350 000 $"
        mock_doc = unittest.mock.MagicMock()
        mock_doc.__iter__ = unittest.mock.Mock(return_value=iter([mock_page]))
        mock_fitz.open.return_value = mock_doc
        with unittest.mock.patch.dict(sys.modules, {"fitz": mock_fitz}):
            from engine.ingestion import extract_text_from_pdf
            text, has_text = extract_text_from_pdf(Path("/fake/doc.pdf"))
        assert has_text is True
        assert "1200" in text

    def test_returns_false_when_no_text(self):
        import sys
        import unittest.mock
        mock_fitz = unittest.mock.MagicMock()
        mock_page = unittest.mock.MagicMock()
        mock_page.get_text.return_value = ""
        mock_doc = unittest.mock.MagicMock()
        mock_doc.__iter__ = unittest.mock.Mock(return_value=iter([mock_page]))
        mock_fitz.open.return_value = mock_doc
        with unittest.mock.patch.dict(sys.modules, {"fitz": mock_fitz}):
            from engine.ingestion import extract_text_from_pdf
            text, has_text = extract_text_from_pdf(Path("/fake/scan.pdf"))
        assert has_text is False
        assert text == ""


# ── TestIngestion_VisionFallback_PDF ─────────────────────────────────────────

class TestIngestion_VisionFallback_PDF:
    def test_vision_called_when_pdf_has_no_text(self):
        import unittest.mock
        mock_client = unittest.mock.MagicMock()
        mock_resp = unittest.mock.MagicMock()
        mock_resp.choices[0].message.content = "Maison de plain-pied en brique"
        mock_client.chat.completions.create.return_value = mock_resp
        with unittest.mock.patch("engine.ingestion.extract_text_from_pdf", return_value=("", False)):
            with unittest.mock.patch("engine.ingestion.pdf_page_to_b64_image", return_value="fakeb64base64"):
                from engine.ingestion import extract_document
                result = extract_document(Path("/fake/scan.pdf"), "application/pdf", mock_client)
        assert result["method"] == "vision"
        assert "Maison" in result["extracted_text"]

    def test_skipped_when_pdf_has_no_text_and_no_client(self):
        import unittest.mock
        with unittest.mock.patch("engine.ingestion.extract_text_from_pdf", return_value=("", False)):
            from engine.ingestion import extract_document
            result = extract_document(Path("/fake/scan.pdf"), "application/pdf", None)
        assert result["method"] == "skipped"
        assert result["extracted_text"] == ""


# ── TestIngestion_VisionImage ─────────────────────────────────────────────────

class TestIngestion_VisionImage:
    def test_vision_called_for_jpeg(self):
        import unittest.mock
        import tempfile
        mock_client = unittest.mock.MagicMock()
        mock_resp = unittest.mock.MagicMock()
        mock_resp.choices[0].message.content = "Belle maison en brique"
        mock_client.chat.completions.create.return_value = mock_resp
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"\xff\xd8\xff\xe0" + b"\x00" * 20)
            tmp_path = Path(f.name)
        try:
            from engine.ingestion import extract_document
            result = extract_document(tmp_path, "image/jpeg", mock_client)
            assert result["method"] == "vision"
            assert "Belle maison" in result["extracted_text"]
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_skipped_for_jpeg_without_client(self):
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"\xff\xd8\xff\xe0" + b"\x00" * 20)
            tmp_path = Path(f.name)
        try:
            from engine.ingestion import extract_document
            result = extract_document(tmp_path, "image/jpeg", None)
            assert result["method"] == "skipped"
            assert result["extracted_text"] == ""
        finally:
            tmp_path.unlink(missing_ok=True)


# ── TestIngestion_NoOpenAI ────────────────────────────────────────────────────

class TestIngestion_NoOpenAI:
    def test_no_crash_when_no_client_pdf(self):
        import sys
        import unittest.mock
        mock_fitz = unittest.mock.MagicMock()
        mock_page = unittest.mock.MagicMock()
        mock_page.get_text.return_value = ""
        mock_doc = unittest.mock.MagicMock()
        mock_doc.__iter__ = unittest.mock.Mock(return_value=iter([mock_page]))
        mock_fitz.open.return_value = mock_doc
        with unittest.mock.patch.dict(sys.modules, {"fitz": mock_fitz}):
            from engine.ingestion import extract_document
            result = extract_document(Path("/fake/scan.pdf"), "application/pdf", None)
        assert result["extracted_text"] == ""
        assert result["method"] == "skipped"


# ── TestIngestion_StructuredFields ────────────────────────────────────────────

class TestIngestion_StructuredFields:
    def test_parse_structured_fields_returns_known_keys(self):
        import unittest.mock
        mock_client = unittest.mock.MagicMock()
        mock_resp = unittest.mock.MagicMock()
        mock_resp.choices[0].message.content = (
            '{"prix_achat": 350000.0, "date_achat": "2025-03-15", "no_lot": null}'
        )
        mock_client.chat.completions.create.return_value = mock_resp
        from engine.ingestion import parse_structured_fields
        docs = [{"filename": "acte.pdf", "extracted_text": "Prix : 350 000 $"}]
        result = parse_structured_fields(docs, mock_client)
        assert result["prix_achat"] == 350000.0
        assert result["date_achat"] == "2025-03-15"
        assert "no_lot" not in result  # null excluded

    def test_returns_empty_when_no_client(self):
        from engine.ingestion import parse_structured_fields
        docs = [{"filename": "acte.pdf", "extracted_text": "Prix : 350 000 $"}]
        result = parse_structured_fields(docs, None)
        assert result == {}


# ── TestIngestion_NullFieldsSkipped ──────────────────────────────────────────

class TestIngestion_NullFieldsSkipped:
    def test_null_fields_not_in_result(self):
        import unittest.mock
        mock_client = unittest.mock.MagicMock()
        mock_resp = unittest.mock.MagicMock()
        mock_resp.choices[0].message.content = '{"prix_achat": null, "date_achat": null}'
        mock_client.chat.completions.create.return_value = mock_resp
        from engine.ingestion import parse_structured_fields
        docs = [{"filename": "photo.jpg", "extracted_text": "Maison en briques"}]
        result = parse_structured_fields(docs, mock_client)
        assert result == {}


# ── TestIngestion_NoUpload ────────────────────────────────────────────────────

class TestIngestion_NoUpload:
    def test_empty_uploaded_docs_returns_empty_dict(self):
        from engine.ingestion import ingest_uploaded_documents
        session = {"session_dir": "/tmp/fake-session", "uploaded_documents": []}
        result = ingest_uploaded_documents(session, None)
        assert result == {}

    def test_missing_uploaded_docs_key_returns_empty_dict(self):
        from engine.ingestion import ingest_uploaded_documents
        session = {"session_dir": "/tmp/fake-session"}
        result = ingest_uploaded_documents(session, None)
        assert result == {}


# ── TestIngestion_ExistingFieldsNotOverwritten ────────────────────────────────

class TestIngestion_ExistingFieldsNotOverwritten:
    def test_fixture_field_wins_over_extracted_field(self):
        """Injection loop: 'not case.get(k)' — existing values win."""
        case = {"prix_achat": 450000.0}
        _fields = {"prix_achat": 350000.0, "date_achat": "2025-03-15"}
        for k, v in _fields.items():
            if v is not None and not case.get(k):
                case[k] = v
        assert case["prix_achat"] == 450000.0  # not overwritten
        assert case["date_achat"] == "2025-03-15"  # new field added

    def test_empty_string_case_field_is_overwritten(self):
        """Empty string is falsy — extraction fills the gap."""
        case = {"prix_achat": ""}
        _fields = {"prix_achat": 350000.0}
        for k, v in _fields.items():
            if v is not None and not case.get(k):
                case[k] = v
        assert case["prix_achat"] == 350000.0


# ── TestFicheBien_IngestedDocs ────────────────────────────────────────────────

class TestFicheBien_IngestedDocs:
    def test_ingested_docs_appended_to_fiche_bien_prompt(self):
        from engine.runtime import _build_enrichment_prompt
        case = {
            "dossier_id": "D-INGEST-TEST",
            "type_bien": "residentiel_unifamilial",
            "date_reference": "2026-05-13",
            "zone": "Laval",
            "ingested_docs": [
                {
                    "filename": "acte_vente.pdf",
                    "extracted_text": "Prix : 350 000 $\nDate : 2025-03-15",
                },
            ],
        }
        payload = {
            "surface": {"value": 1200, "unit": "pi²"},
            "confidence": 0.85,
            "source_ids": ["SRC-001"],
        }
        prompt = _build_enrichment_prompt("data-facts", "fiche_bien.json", payload, case)
        assert "Documents" in prompt
        assert "acte_vente.pdf" in prompt
        assert "350 000" in prompt

    def test_fiche_bien_prompt_unchanged_without_ingested_docs(self):
        from engine.runtime import _build_enrichment_prompt
        case = {
            "dossier_id": "D-NO-INGEST",
            "type_bien": "residentiel_unifamilial",
            "date_reference": "2026-05-13",
            "zone": "Montreal",
        }
        payload = {
            "surface": {"value": 900, "unit": "pi²"},
            "confidence": 0.70,
            "source_ids": [],
        }
        prompt = _build_enrichment_prompt("data-facts", "fiche_bien.json", payload, case)
        assert "DONNÉES DE LA FICHE BIEN" in prompt
        assert "acte_vente.pdf" not in prompt


# ── TestMapComparableInput_Full ───────────────────────────────────────────────

class TestMapComparableInput_Full:
    def test_all_fields_mapped_correctly(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from api import _map_comparable_input
        row = {
            "id": "abc123",
            "adresse": "123 rue Example, Montréal",
            "date_vente": "2024-06-15",
            "prix_vente": 450000,
            "source_id": "CENTRIS-12345678",
            "source_type": "mls_centris",
            "type_propriete": "unifamiliale",
            "surface_hab": 145.0,
            "surface_terrain": 350.0,
            "annee_construction": 1985,
            "nb_logements": None,
            "conditions_vente": "normale",
            "notes": "Belle propriété",
        }
        result = _map_comparable_input(row)
        assert result["comparable_id"] == "CENTRIS-12345678"
        assert result["adresse"] == "123 rue Example, Montréal"
        assert result["date_vente"] == "2024-06-15"
        assert result["prix_vente"] == 450000.0
        assert result["source_id"] == "CENTRIS-12345678"
        assert result["source_type"] == "mls_centris"
        assert result["surface"] == {"value": 145.0, "unit": "m²"}
        assert result["surface_terrain"] == 350.0
        assert result["annee_construction"] == 1985
        assert result["nb_logements"] is None
        assert result["conditions_vente"] == "normale"
        assert result["notes"] == "Belle propriété"
        assert result["confidence"] == 0.80


# ── TestMapComparableInput_NullOptionals ──────────────────────────────────────

class TestMapComparableInput_NullOptionals:
    def test_surface_hab_none_returns_empty_surface_dict(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from api import _map_comparable_input
        row = {
            "surface_hab": None,
            "annee_construction": None,
            "surface_terrain": None,
            "nb_logements": None,
        }
        result = _map_comparable_input(row)
        assert result["surface"] == {}
        assert result["annee_construction"] is None
        assert result["surface_terrain"] is None
        assert result["nb_logements"] is None

    def test_missing_source_id_falls_back_to_id_field(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from api import _map_comparable_input
        row = {"id": "fallback-uuid", "source_id": ""}
        result = _map_comparable_input(row)
        assert result["comparable_id"] == "fallback-uuid"


# ── TestLoadCaseBody_ComparablesInjected ──────────────────────────────────────

class TestLoadCaseBody_ComparablesInjected:
    def test_comparables_mapped_from_body(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from api import load_case_from_body
        body = {
            "comparables": [
                {
                    "id": "c1",
                    "adresse": "456 rue Test",
                    "date_vente": "2024-03-01",
                    "prix_vente": 500000,
                    "source_id": "RF-2024-001",
                    "source_type": "registre_foncier",
                    "surface_hab": 120.0,
                    "surface_terrain": None,
                    "annee_construction": 1992,
                    "nb_logements": None,
                    "conditions_vente": "normale",
                    "notes": "",
                }
            ]
        }
        case, _ = load_case_from_body(body)
        assert len(case["comparables"]) == 1
        comp = case["comparables"][0]
        assert comp["source_id"] == "RF-2024-001"
        assert comp["surface"] == {"value": 120.0, "unit": "m²"}
        assert comp["confidence"] == 0.80

    def test_comparables_body_override_fixture_comparables(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from api import load_case_from_body
        body = {
            "comparables": [
                {
                    "id": "new1",
                    "source_id": "NEW-001",
                    "prix_vente": 300000,
                    "surface_hab": None,
                    "surface_terrain": None,
                    "annee_construction": None,
                    "nb_logements": None,
                }
            ]
        }
        case, _ = load_case_from_body(body)
        assert len(case["comparables"]) >= 1
        assert all(c["source_id"] == "NEW-001" for c in case["comparables"])

    def test_no_comparables_in_body_leaves_fixture_untouched(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from api import load_case_from_body
        case_a, _ = load_case_from_body({})
        fixture_comps = list(case_a.get("comparables", []))
        case_b, _ = load_case_from_body({})
        assert case_b.get("comparables", []) == fixture_comps


# ── TestBuildRapportPromptV2 ───────────────────────────────────────────────────

class TestBuildRapportPromptV2_IncludesCommanditaire:
    def test_commanditaire_nom_in_prompt(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import _build_rapport_prompt_v2
        case = {
            "dossier_id": "D-TEST",
            "commanditaire": {
                "nom": "Jean Tremblay",
                "organisation": "Banque XYZ",
                "fin_evaluation": "hypothecaire",
            },
            "date_reference": "2026-05-15",
            "type_bien": "residentiel_unifamilial",
            "zone": "R-1",
            "surface": {"value": 120, "unit": "m²"},
            "comparables": [],
        }
        prompt = _build_rapport_prompt_v2(case, "abrege", {}, "BROUILLON", [], [])
        assert "Jean Tremblay" in prompt

    def test_commanditaire_organisation_in_prompt(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import _build_rapport_prompt_v2
        case = {
            "commanditaire": {"nom": "Marie Côté", "organisation": "Caisse Pop", "fin_evaluation": "succession"},
        }
        prompt = _build_rapport_prompt_v2(case, "abrege", {}, "BROUILLON", [], [])
        assert "Caisse Pop" in prompt


class TestBuildRapportPromptV2_FormatAbrege:
    def test_format_abrege_label_in_prompt(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import _build_rapport_prompt_v2
        case = {"dossier_id": "D-TEST"}
        prompt = _build_rapport_prompt_v2(case, "abrege", {}, "BROUILLON", [], [])
        assert "abrege" in prompt.lower() or "abrégé" in prompt.lower()

    def test_format_abrege_not_complet(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import _build_rapport_prompt_v2
        case = {"dossier_id": "D-TEST"}
        prompt = _build_rapport_prompt_v2(case, "abrege", {}, "BROUILLON", [], [])
        assert "narratif complet" not in prompt.lower()


class TestBuildRapportPromptV2_FormatComplet:
    def test_format_complet_label_in_prompt(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import _build_rapport_prompt_v2
        case = {"dossier_id": "D-TEST"}
        prompt = _build_rapport_prompt_v2(case, "complet", {}, "BROUILLON", [], [])
        assert "complet" in prompt.lower() or "narratif" in prompt.lower()


class TestGenerateRapportFallbackNoCle:
    def test_returns_deterministic_string_without_api_key(self, monkeypatch):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import generate_brouillon_rapport
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        case = {
            "dossier_id": "D-TEST",
            "type_bien": "residentiel_unifamilial",
            "zone": "R-1",
            "date_reference": "2026-05-15",
            "surface": {"value": 120, "unit": "m²"},
            "comparables": [],
        }
        result = generate_brouillon_rapport(case, {}, "BROUILLON", [], [], format="abrege")
        assert isinstance(result, str)
        assert len(result) > 100
        assert "BROUILLON" in result

    def test_complet_format_also_returns_string(self, monkeypatch):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import generate_brouillon_rapport
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        case = {"dossier_id": "D-TEST", "type_bien": "immeuble_revenus"}
        result = generate_brouillon_rapport(case, {}, "BROUILLON", [], [], format="complet")
        assert isinstance(result, str)
        assert len(result) > 100


class TestSaveRapportContent:
    def test_writes_content_to_artifact_file(self, tmp_path, monkeypatch):
        """app_save_rapport écrase le fichier brouillon_rapport.md dans la session."""
        import sys, json
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        import api as api_module
        monkeypatch.setattr(api_module, "SESSIONS_DIR", tmp_path)

        session_id = "test-session-abc"
        session_dir = tmp_path / session_id
        session_dir.mkdir()
        artifacts_dir = session_dir / "artifacts" / "D-TEST"
        artifacts_dir.mkdir(parents=True)
        rapport_path = artifacts_dir / "redaction.brouillon_rapport.md"
        rapport_path.write_text("# Brouillon original\n", encoding="utf-8")

        artifact_index = {
            "artifacts": [
                {
                    "step": "redaction",
                    "artifact": "brouillon_rapport.md",
                    "event_id": "evt_001",
                    "path": str(rapport_path),
                }
            ]
        }
        (session_dir / "artifact_index.json").write_text(
            json.dumps(artifact_index), encoding="utf-8"
        )
        session_data = {
            "session_id": session_id,
            "session_dir": str(session_dir),
        }
        (session_dir / "session.json").write_text(
            json.dumps(session_data), encoding="utf-8"
        )

        result = api_module.app_save_rapport(
            {"session_id": session_id, "content": "# Contenu modifié\n\nTexte édité."}
        )
        assert result["ok"] is True
        assert rapport_path.read_text(encoding="utf-8") == "# Contenu modifié\n\nTexte édité."


# ── Batch 8b — Export rapport ────────────────────────────────────────────────

class TestGenerateDocx_ContainsWatermark:
    def test_watermark_in_generated_docx(self):
        import sys, io
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.report_export import _generate_docx
        from docx import Document
        data = _generate_docx("## Identification\n\nTestDocument", "D-TEST")
        assert isinstance(data, bytes) and len(data) > 0
        doc = Document(io.BytesIO(data))
        all_text = " ".join(p.text for p in doc.paragraphs)
        assert "BROUILLON NON CERTIFIÉ" in all_text


class TestGenerateDocx_HeadingsRendered:
    def test_h2_becomes_heading2(self):
        import sys, io
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.report_export import _generate_docx
        from docx import Document
        data = _generate_docx("## Section principale\n\nTexte normal.", "D-TEST")
        doc = Document(io.BytesIO(data))
        heading_styles = [p.style.name for p in doc.paragraphs]
        assert "Heading 2" in heading_styles


class TestGenerateHtml_ContainsWatermark:
    def test_watermark_div_present(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.report_export import _generate_html
        html = _generate_html("## Test\n\nContenu.", "D-TEST")
        assert isinstance(html, str)
        assert "BROUILLON NON CERTIFIÉ" in html


class TestGenerateHtml_TablesRendered:
    def test_markdown_table_becomes_html_table(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.report_export import _generate_html
        md = "| Col A | Col B |\n|-------|-------|\n| val1  | val2  |"
        html = _generate_html(md, "D-TEST")
        assert "<table" in html.lower()
        assert "val1" in html


class TestExportRapport_DocxEndpoint:
    def test_docx_export_returns_base64_with_correct_fields(self, tmp_path, monkeypatch):
        import sys, json, base64
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        import api as api_module
        monkeypatch.setattr(api_module, "SESSIONS_DIR", tmp_path)

        session_id = "test-export-docx"
        session_dir = tmp_path / session_id
        session_dir.mkdir()
        artifacts_dir = session_dir / "artifacts" / "D-EXPORT"
        artifacts_dir.mkdir(parents=True)
        rapport_path = artifacts_dir / "redaction.brouillon_rapport.md"
        rapport_path.write_text("## Rapport\n\nContenu test.", encoding="utf-8")
        artifact_index = {"artifacts": [{"step": "redaction", "artifact": "brouillon_rapport.md",
                                          "event_id": "evt_001", "path": str(rapport_path)}]}
        (session_dir / "artifact_index.json").write_text(json.dumps(artifact_index), encoding="utf-8")
        (session_dir / "session.json").write_text(
            json.dumps({"session_id": session_id, "session_dir": str(session_dir), "dossier_id": "D-EXPORT"}),
            encoding="utf-8")

        result = api_module.app_export_rapport({"session_id": session_id, "format": "docx"})
        assert result["ok"] is True
        assert result["content_type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert result["filename"] == "rapport-D-EXPORT.docx"
        data = base64.b64decode(result["data"])
        assert len(data) > 100


class TestExportRapport_HtmlEndpoint:
    def test_html_export_returns_html_string_with_watermark(self, tmp_path, monkeypatch):
        import sys, json
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        import api as api_module
        monkeypatch.setattr(api_module, "SESSIONS_DIR", tmp_path)

        session_id = "test-export-html"
        session_dir = tmp_path / session_id
        session_dir.mkdir()
        artifacts_dir = session_dir / "artifacts" / "D-HTML"
        artifacts_dir.mkdir(parents=True)
        rapport_path = artifacts_dir / "redaction.brouillon_rapport.md"
        rapport_path.write_text("## Test\n\nContenu.", encoding="utf-8")
        artifact_index = {"artifacts": [{"step": "redaction", "artifact": "brouillon_rapport.md",
                                          "event_id": "evt_001", "path": str(rapport_path)}]}
        (session_dir / "artifact_index.json").write_text(json.dumps(artifact_index), encoding="utf-8")
        (session_dir / "session.json").write_text(
            json.dumps({"session_id": session_id, "session_dir": str(session_dir), "dossier_id": "D-HTML"}),
            encoding="utf-8")

        result = api_module.app_export_rapport({"session_id": session_id, "format": "html"})
        assert result["ok"] is True
        assert result["content_type"] == "text/html; charset=utf-8"
        assert "BROUILLON NON CERTIFIÉ" in result["data"]


class TestExportRapport_InvalidFormat:
    def test_format_pdf_raises_value_error(self, tmp_path, monkeypatch):
        import sys, json, pytest
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        import api as api_module
        monkeypatch.setattr(api_module, "SESSIONS_DIR", tmp_path)

        session_id = "test-invalid-fmt"
        session_dir = tmp_path / session_id
        session_dir.mkdir()
        (session_dir / "session.json").write_text(
            json.dumps({"session_id": session_id, "session_dir": str(session_dir)}),
            encoding="utf-8")

        with pytest.raises(ValueError, match="format"):
            api_module.app_export_rapport({"session_id": session_id, "format": "pdf"})


# ── TestDataEnrichment ────────────────────────────────────────────────────────

class TestDataEnrichment_CityDetection:
    def _detect(self, display_name, zone=""):
        from engine.data_enrichment import detect_city
        return detect_city(display_name, zone)

    def test_montreal_explicit(self):
        assert self._detect("1234 rue Sherbrooke, Montréal") == "montreal"

    def test_plateau_maps_to_montreal(self):
        assert self._detect("123 Avenue du Parc", zone="plateau-mont-royal") == "montreal"

    def test_laval_maps_to_montreal(self):
        assert self._detect("456 boul Laval, Laval") == "montreal"

    def test_quebec_city(self):
        assert self._detect("100 Grande Allée, Québec") == "quebec"

    def test_gatineau(self):
        assert self._detect("789 boul Maloney, Gatineau") == "gatineau"

    def test_sherbrooke(self):
        assert self._detect("321 King O, Sherbrooke") == "sherbrooke"

    def test_default_fallback(self):
        assert self._detect("", zone="SECTEUR-ANONYMISE") == "montreal"

    def test_case_insensitive(self):
        assert self._detect("MONTREAL") == "montreal"


class TestDataEnrichment_EnrichCase:
    def test_enrich_case_never_raises(self, tmp_path):
        from engine.data_enrichment import enrich_case
        case = {"dossier_id": "TEST", "zone": "SECTEUR-X"}
        # Should not raise even with no network / no CSV
        enrich_case(case, display_name="9999 rue Inexistante", cache_dir=tmp_path)

    def test_enrich_case_no_side_effect_on_failure(self, tmp_path):
        from engine.data_enrichment import enrich_case
        case = {"dossier_id": "TEST", "zone": "SECTEUR-X", "surface": 150.0}
        enrich_case(case, display_name="", cache_dir=tmp_path)
        # surface must not be overwritten
        assert case["surface"] == 150.0

    def test_role_lookup_empty_when_no_csv(self, tmp_path):
        from engine.data_enrichment import lookup_role_mtl
        result = lookup_role_mtl(tmp_path / "nonexistent.csv")
        assert result == {}

    def test_role_lookup_from_csv(self, tmp_path):
        from engine.data_enrichment import lookup_role_mtl
        csv_path = tmp_path / "role_mtl.csv"
        csv_path.write_text(
            "ID_UEV,CIVIQUE_DEBUT,CIVIQUE_FIN,NOM_RUE,SUITE_DEBUT,ETAGE_HORS_SOL,"
            "NOMBRE_LOGEMENT,ANNEE_CONSTRUCTION,CODE_UTILISATION,LETTRE_DEBUT,"
            "LETTRE_FIN,LIBELLE_UTILISATION,CATEGORIE_UEF,MATRICULE83,"
            "SUPERFICIE_TERRAIN,SUPERFICIE_BATIMENT,NO_ARROND_ILE_CUM,MUNICIPALITE\n"
            "1234567,1000,1000,RUE SHERBROOKE O,,3,6,1958,1000,,,"
            "Résidentiel,Régulier,9999-12-3456-7-001-0,312.5,420.0,10,Montréal\n",
            encoding="utf-8",
        )
        result = lookup_role_mtl(csv_path, matricule="9999-12-3456-7-001-0")
        assert result["annee_construction"] == 1958
        assert result["nb_logements"] == 6
        assert result["superficie_terrain_m2"] == 312.5

    def test_role_lookup_by_address(self, tmp_path):
        from engine.data_enrichment import lookup_role_mtl
        csv_path = tmp_path / "role_mtl.csv"
        csv_path.write_text(
            "ID_UEV,CIVIQUE_DEBUT,CIVIQUE_FIN,NOM_RUE,SUITE_DEBUT,ETAGE_HORS_SOL,"
            "NOMBRE_LOGEMENT,ANNEE_CONSTRUCTION,CODE_UTILISATION,LETTRE_DEBUT,"
            "LETTRE_FIN,LIBELLE_UTILISATION,CATEGORIE_UEF,MATRICULE83,"
            "SUPERFICIE_TERRAIN,SUPERFICIE_BATIMENT,NO_ARROND_ILE_CUM,MUNICIPALITE\n"
            "1234567,1000,1000,RUE SHERBROOKE O,,3,6,1958,1000,,,"
            "Résidentiel,Régulier,9999-12-3456-7-001-0,312.5,420.0,10,Montréal\n",
            encoding="utf-8",
        )
        result = lookup_role_mtl(csv_path, display_name="1000 rue Sherbrooke O")
        assert result["annee_construction"] == 1958

    def test_enrich_case_injects_role_from_csv(self, tmp_path):
        from engine.data_enrichment import enrich_case
        csv_path = tmp_path / "role_mtl.csv"
        csv_path.write_text(
            "ID_UEV,CIVIQUE_DEBUT,CIVIQUE_FIN,NOM_RUE,SUITE_DEBUT,ETAGE_HORS_SOL,"
            "NOMBRE_LOGEMENT,ANNEE_CONSTRUCTION,CODE_UTILISATION,LETTRE_DEBUT,"
            "LETTRE_FIN,LIBELLE_UTILISATION,CATEGORIE_UEF,MATRICULE83,"
            "SUPERFICIE_TERRAIN,SUPERFICIE_BATIMENT,NO_ARROND_ILE_CUM,MUNICIPALITE\n"
            "1234567,500,500,AV DU PARC,,2,4,1975,1000,,,"
            "Résidentiel,Régulier,ABCD-12-3456-7-000-0000,400.0,300.0,10,Montréal\n",
            encoding="utf-8",
        )
        case = {"dossier_id": "TEST", "matricule": "ABCD-12-3456-7-000-0000"}
        enrich_case(case, display_name="500 av du Parc", cache_dir=tmp_path)
        assert case.get("role_municipal", {}).get("annee_construction") == 1975
        assert case.get("annee_construction") == 1975
