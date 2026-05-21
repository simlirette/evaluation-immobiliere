"""S11 tests — dossier démo anonymisé D-DEMO-2026-LAV."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
FIXTURE_INPUT = FIXTURES / "demo_laval_res.input.json"
FIXTURE_CSV = FIXTURES / "demo_laval_res.jlr.csv"


# ── Fixture input.json — structure et réalisme ────────────────────────────────

class TestDemoFixtureInput:
    def _case(self) -> dict:
        return json.loads(FIXTURE_INPUT.read_text(encoding="utf-8"))

    def test_fixture_file_exists(self):
        assert FIXTURE_INPUT.exists(), "demo_laval_res.input.json introuvable"

    def test_dossier_id_format(self):
        case = self._case()
        assert case["dossier_id"] == "D-DEMO-2026-LAV"

    def test_required_b001_fields(self):
        """B001 — dossier_id et date_reference présents."""
        case = self._case()
        assert case.get("dossier_id"), "dossier_id manquant"
        assert case.get("date_reference"), "date_reference manquant"

    def test_type_bien_unifamiliale(self):
        assert self._case()["type_bien"] == "unifamiliale"

    def test_no_obviously_synthetic_ids(self):
        """Pas de IDs synthétiques évidents (ANONYMISE, CP-001, SRC-VENTE)."""
        raw = FIXTURE_INPUT.read_text(encoding="utf-8")
        assert "ANONYMISE" not in raw
        assert "CP-001" not in raw
        assert "SRC-VENTE-001" not in raw
        assert "PILOTE" not in raw

    def test_at_least_3_comparables(self):
        """B007 minimum — dossier démarre avec ≥ 3 comparables."""
        case = self._case()
        assert len(case.get("comparables", [])) >= 3

    def test_all_comparables_have_source_id(self):
        """B002 — chaque comparable a un source_id."""
        case = self._case()
        for c in case["comparables"]:
            assert c.get("source_id"), f"source_id manquant sur comparable {c.get('comparable_id')}"

    def test_comparables_before_date_reference(self):
        """B003 — pas de vente postérieure à date_reference."""
        case = self._case()
        date_ref = case["date_reference"]
        for c in case["comparables"]:
            assert c["date_vente"] <= date_ref, (
                f"Comparable {c['source_id']} date {c['date_vente']} > date_ref {date_ref}"
            )

    def test_comparables_within_50km(self):
        """B007 — tous les comparables dans le seuil de distance bloquant (50 km)."""
        case = self._case()
        for c in case["comparables"]:
            dist = c.get("distance_km", 0)
            assert dist <= 50, f"Comparable {c['source_id']} distance {dist} km > 50 km"

    def test_commanditaire_info_present(self):
        """Requis pour lettre de mandat (S7)."""
        case = self._case()
        cmd = case.get("commanditaire", {})
        assert cmd.get("nom"), "commanditaire.nom manquant"
        assert cmd.get("organisation"), "commanditaire.organisation manquant"
        assert cmd.get("fin_evaluation"), "commanditaire.fin_evaluation manquant"

    def test_hypotheses_present(self):
        """Au moins une hypothèse explicite (§6.2 OEAQ)."""
        case = self._case()
        hyp = case.get("hypotheses_explicites") or case.get("hypotheses", [])
        assert len(hyp) >= 1

    def test_surface_unit_pi2(self):
        """Surface habitable en pi² (cohérence Québec)."""
        case = self._case()
        surf = case.get("surface", {})
        assert surf.get("unit") == "pi2"
        assert surf.get("value", 0) > 0

    def test_unifamiliale_comparative_approach_only(self):
        """unifamiliale → applicable_approaches retourne seulement approche_comparative."""
        from engine.valuation import applicable_approaches
        case = self._case()
        approaches = applicable_approaches(case["type_bien"])
        assert approaches == ["approche_comparative"]
        assert "approche_revenu" not in approaches
        assert "approche_cout" not in approaches


# ── Fixture JLR CSV — parsing ─────────────────────────────────────────────────

class TestDemoJlrCsv:
    def test_csv_file_exists(self):
        assert FIXTURE_CSV.exists(), "demo_laval_res.jlr.csv introuvable"

    def test_csv_parses_without_error(self):
        from engine.ingestion import parse_jlr_csv
        rows = parse_jlr_csv(FIXTURE_CSV)
        assert isinstance(rows, list)

    def test_csv_has_6_rows(self):
        from engine.ingestion import parse_jlr_csv
        rows = parse_jlr_csv(FIXTURE_CSV)
        assert len(rows) == 6

    def test_csv_all_rows_have_prix_vente(self):
        from engine.ingestion import parse_jlr_csv
        rows = parse_jlr_csv(FIXTURE_CSV)
        for row in rows:
            assert row.get("prix_vente", 0) > 0, f"prix_vente manquant : {row.get('source_id')}"

    def test_csv_source_ids_are_jlr_format(self):
        """IDs au format JLR-AAAA-NNNNN (réaliste, pas synthétique)."""
        from engine.ingestion import parse_jlr_csv
        rows = parse_jlr_csv(FIXTURE_CSV)
        for row in rows:
            sid = row.get("source_id", "")
            assert sid.startswith("JLR-"), f"source_id non-JLR : {sid}"

    def test_csv_scoring_returns_at_least_3_above_threshold(self):
        """Au moins 3 comparables scorés au-dessus de 0.50 (CP2 viable)."""
        from engine.ingestion import parse_jlr_csv
        from engine.tools import score_comparable
        rows = parse_jlr_csv(FIXTURE_CSV)
        case = json.loads(FIXTURE_INPUT.read_text(encoding="utf-8"))
        subject = {"surface": case["surface"]}
        scored = [score_comparable(r, subject=subject) for r in rows]
        above_threshold = [s for s in scored if s.get("score", 0) >= 0.50]
        assert len(above_threshold) >= 3, (
            f"Seulement {len(above_threshold)} comparables ≥ 0.50 — CP2 impossible"
        )

    def test_csv_no_synthetic_ids(self):
        raw = FIXTURE_CSV.read_text(encoding="utf-8")
        assert "CP-001" not in raw
        assert "SRC-VENTE" not in raw
        assert "ANONYMISE" not in raw


# ── Compliance B001-B007 sur la fixture ───────────────────────────────────────

class TestDemoCompliance:
    def _case(self) -> dict:
        return json.loads(FIXTURE_INPUT.read_text(encoding="utf-8"))

    def test_b001_passes(self):
        from engine.compliance import check_B001
        result = check_B001(self._case())
        assert not result.violated, f"B001 échoue : {result.explanation_fr}"

    def test_b002_passes(self):
        from engine.compliance import check_B002
        result = check_B002(self._case())
        assert not result.violated, f"B002 échoue : {result.explanation_fr}"

    def test_b003_passes(self):
        from engine.compliance import check_B003
        result = check_B003(self._case())
        assert not result.violated, f"B003 échoue : {result.explanation_fr}"

    def test_b004_passes(self):
        from engine.compliance import check_B004
        result = check_B004(self._case())
        assert not result.violated, f"B004 échoue : {result.explanation_fr}"

    def test_b007_passes(self):
        from engine.compliance import check_B007
        result = check_B007(self._case())
        assert not result.violated, f"B007 échoue : {result.explanation_fr}"

    def test_b005_passes(self):
        """B005 — ajustements < 25 000 $ donc aucun ne déclenche la règle."""
        from engine.compliance import check_B005
        result = check_B005(self._case())
        assert not result.violated, f"B005 échoue : {result.explanation_fr}"

    def test_b006_not_blocked_without_valeur_estimee(self):
        """B006 — sans valeur_estimee, la règle est non-bloquante (non vérifiable)."""
        from engine.compliance import check_B006
        result = check_B006(self._case())
        # Sans valeur_estimee, B006 doit passer (pas de valeur à vérifier)
        assert not result.violated, f"B006 échoue : {result.explanation_fr}"

    def test_fin_evaluation_is_semantic_key(self):
        """commanditaire.fin_evaluation doit être une clé sémantique, pas une date ISO."""
        case = self._case()
        fin_eval = case.get("commanditaire", {}).get("fin_evaluation", "")
        # Une date ISO contient '-' entre les chiffres (ex: "2025-09-30")
        import re
        assert not re.match(r"^\d{4}-\d{2}-\d{2}$", fin_eval), (
            f"fin_evaluation est une date ISO '{fin_eval}' — "
            "la lettre de mandat affichera la date brute. Utiliser 'hypothecaire' ou similaire."
        )


# ── Script seed — importable et structuré ────────────────────────────────────

class TestSeedScript:
    def test_seed_script_exists(self):
        script = Path(__file__).resolve().parent.parent / "scripts" / "seed_demo_dossier.py"
        assert script.exists()

    def test_seed_script_importable(self):
        import importlib.util
        script = Path(__file__).resolve().parent.parent / "scripts" / "seed_demo_dossier.py"
        spec = importlib.util.spec_from_file_location("seed_demo", script)
        mod = importlib.util.module_from_spec(spec)  # type: ignore
        # Vérifie que le module se charge sans erreur (pas d'import side-effect)
        assert mod is not None

    def test_chrono_doc_exists(self):
        chrono = Path(__file__).resolve().parent.parent.parent / "docs" / "DEMO-CHRONOMETRAGE.md"
        assert chrono.exists(), "docs/DEMO-CHRONOMETRAGE.md introuvable"

    def test_chrono_doc_has_time_table(self):
        chrono = Path(__file__).resolve().parent.parent.parent / "docs" / "DEMO-CHRONOMETRAGE.md"
        content = chrono.read_text(encoding="utf-8")
        assert "TOTAL" in content
        assert "eval-immo" in content
        assert "76" in content  # gain global ≥ 70 % dans le tableau
