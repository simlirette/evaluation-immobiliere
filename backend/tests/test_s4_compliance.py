"""S4 tests — Compliance Python pur B001-B007.

Un test par règle, plus tests d'intégration run_compliance().
Critère de done : B002 violé → rapport bloqué, message actionnable en français.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.compliance import (
    ComplianceReport,
    ComplianceResult,
    check_B001,
    check_B002,
    check_B003,
    check_B004,
    check_B005,
    check_B006,
    check_B007,
    run_compliance,
)


# ── Fixtures communes ─────────────────────────────────────────────────────────

def _base_case(**kwargs) -> dict:
    """Dossier valide minimal — pas de violation."""
    case = {
        "dossier_id": "D-TEST-001",
        "date_reference": "2026-01-01",
        "comparables": [
            {"source_id": "JLR-001", "date_vente": "2025-06-01", "distance_km": 5, "prix_vente": 400_000,
             "surface": {"value": 100, "unit": "m2"}},
            {"source_id": "JLR-002", "date_vente": "2025-09-01", "distance_km": 8, "prix_vente": 420_000,
             "surface": {"value": 105, "unit": "m2"}},
        ],
        "ajustements": [],
        "surface": {"value": 102, "unit": "m2"},
        "valeur_estimee": 410_000,
        "confidence": 0.85,
        "hypotheses": [],
    }
    case.update(kwargs)
    return case


# ── B001 — champs obligatoires manquants ─────────────────────────────────────

class TestB001:
    def test_ok_when_fields_present(self):
        result = check_B001(_base_case())
        assert not result.violated

    def test_violated_when_dossier_id_missing(self):
        case = _base_case()
        del case["dossier_id"]
        result = check_B001(case)
        assert result.violated
        assert result.rule == "B001"
        assert "dossier_id" in result.explanation_fr

    def test_violated_when_date_reference_missing(self):
        case = _base_case()
        del case["date_reference"]
        result = check_B001(case)
        assert result.violated
        assert "date_reference" in result.explanation_fr

    def test_violated_when_both_missing(self):
        result = check_B001({})
        assert result.violated
        assert "dossier_id" in result.explanation_fr
        assert "date_reference" in result.explanation_fr


# ── B002 — source_id absent ───────────────────────────────────────────────────

class TestB002:
    def test_ok_when_all_sources_present(self):
        assert not check_B002(_base_case()).violated

    def test_violated_when_comparable_missing_source_id(self):
        case = _base_case()
        del case["comparables"][0]["source_id"]
        result = check_B002(case)
        assert result.violated
        assert result.rule == "B002"
        assert "JLR" in result.explanation_fr or "comparable #1" in result.explanation_fr

    def test_violated_when_ajustement_missing_source_id(self):
        case = _base_case(ajustements=[{"montant": 5000}])  # no source_id
        result = check_B002(case)
        assert result.violated
        assert "ajustement" in result.explanation_fr

    def test_explanation_is_actionnable(self):
        """Message doit contenir une instruction concrète (JLR ou Centris)."""
        case = _base_case()
        del case["comparables"][1]["source_id"]
        result = check_B002(case)
        assert result.violated
        assert "JLR" in result.explanation_fr or "Centris" in result.explanation_fr

    def test_pipeline_blocked_when_b002_violated(self):
        """Critère de done S4 : B002 violé → pipeline bloqué."""
        case = _base_case()
        del case["comparables"][0]["source_id"]
        report = run_compliance(case)
        assert report.is_blocked
        assert any(r.rule == "B002" for r in report.blocking)
        assert report.status == "BLOCKED"


# ── B003 — date future ────────────────────────────────────────────────────────

class TestB003:
    def test_ok_when_all_dates_past(self):
        assert not check_B003(_base_case()).violated

    def test_violated_when_sale_after_reference(self):
        case = _base_case()
        case["comparables"][0]["date_vente"] = "2026-06-01"  # after 2026-01-01
        result = check_B003(case)
        assert result.violated
        assert result.rule == "B003"
        assert "2026-06-01" in result.explanation_fr

    def test_not_violated_when_same_day(self):
        case = _base_case()
        case["comparables"][0]["date_vente"] = "2026-01-01"  # same as reference
        assert not check_B003(case).violated

    def test_no_reference_date_skips_check(self):
        case = _base_case()
        del case["date_reference"]
        result = check_B003(case)
        assert not result.violated  # B001 handles missing date_reference


# ── B004 — unités incohérentes ────────────────────────────────────────────────

class TestB004:
    def test_ok_when_units_match(self):
        assert not check_B004(_base_case()).violated

    def test_violated_when_comp_uses_different_unit(self):
        case = _base_case()
        case["comparables"][0]["surface"] = {"value": 1100, "unit": "pi2"}
        result = check_B004(case)
        assert result.violated
        assert result.rule == "B004"
        assert "m2" in result.explanation_fr or "pi2" in result.explanation_fr

    def test_ok_when_no_subject_unit(self):
        case = _base_case()
        del case["surface"]
        assert not check_B004(case).violated  # can't compare without subject unit

    def test_ok_when_all_comps_same_different_unit(self):
        """Si sujet sans unité et comps cohérents entre eux → OK."""
        case = _base_case()
        case["comparables"][0]["surface"] = {"value": 1000, "unit": "pi2"}
        case["comparables"][1]["surface"] = {"value": 1050, "unit": "pi2"}
        case["surface"] = {"value": 1020, "unit": "pi2"}
        assert not check_B004(case).violated


# ── B005 — ajustement sans validation ────────────────────────────────────────

class TestB005:
    def test_ok_when_no_ajustements(self):
        assert not check_B005(_base_case()).violated

    def test_ok_when_ajustement_small(self):
        case = _base_case(ajustements=[{"source_id": "X", "montant": 5000}])
        assert not check_B005(case).violated

    def test_violated_when_large_ajustement_unvalidated(self):
        case = _base_case(ajustements=[
            {"source_id": "X", "montant": 30_000, "validation_humaine": False},
        ])
        result = check_B005(case)
        assert result.violated
        assert result.rule == "B005"
        assert "30" in result.explanation_fr or "30 000" in result.explanation_fr.replace(",", " ")

    def test_ok_when_large_ajustement_validated(self):
        case = _base_case(ajustements=[
            {"source_id": "X", "montant": 30_000, "validation_humaine": True},
        ])
        assert not check_B005(case).violated

    def test_custom_threshold(self):
        case = _base_case(ajustements=[
            {"source_id": "X", "montant": 10_000, "validation_humaine": False},
        ])
        result = check_B005(case, sensitive_amount_min=5_000)
        assert result.violated


# ── B006 — valeur hors plage plausible ───────────────────────────────────────

class TestB006:
    def test_ok_when_value_in_range(self):
        assert not check_B006(_base_case()).violated

    def test_violated_when_value_too_low(self):
        case = _base_case(valeur_estimee=10_000)
        result = check_B006(case)
        assert result.violated
        assert result.rule == "B006"
        assert "10" in result.explanation_fr or "plage" in result.explanation_fr

    def test_violated_when_value_too_high(self):
        case = _base_case(valeur_estimee=15_000_000)
        result = check_B006(case)
        assert result.violated

    def test_violated_when_far_from_comps(self):
        case = _base_case(valeur_estimee=900_000)  # comps avg ~410k, 900k > 2x
        result = check_B006(case)
        assert result.violated
        assert "comparables" in result.explanation_fr.lower() or "dévie" in result.explanation_fr

    def test_ok_when_no_valeur_estimee(self):
        case = _base_case()
        del case["valeur_estimee"]
        result = check_B006(case)
        assert not result.violated  # absent = non vérifiable


# ── B007 — comparable hors zone ───────────────────────────────────────────────

class TestB007:
    def test_ok_when_all_comps_in_zone(self):
        assert not check_B007(_base_case()).violated

    def test_violated_when_comp_too_far(self):
        case = _base_case()
        case["comparables"][0]["distance_km"] = 60
        result = check_B007(case)
        assert result.violated
        assert result.rule == "B007"
        assert "60" in result.explanation_fr

    def test_ok_at_exact_threshold(self):
        case = _base_case()
        case["comparables"][0]["distance_km"] = 50  # = default max, not > max
        assert not check_B007(case).violated

    def test_violated_beyond_threshold(self):
        case = _base_case()
        case["comparables"][1]["distance_km"] = 51
        result = check_B007(case)
        assert result.violated

    def test_custom_threshold(self):
        case = _base_case()
        case["comparables"][0]["distance_km"] = 25
        result = check_B007(case, max_distance_blocking_km=20)
        assert result.violated


# ── run_compliance — intégration ──────────────────────────────────────────────

class TestRunCompliance:
    def test_ok_case_not_blocked(self):
        report = run_compliance(_base_case())
        assert not report.is_blocked
        assert report.status == "OK"
        assert isinstance(report, ComplianceReport)

    def test_blocking_strings_format(self):
        case = _base_case()
        del case["comparables"][0]["source_id"]
        report = run_compliance(case)
        strings = report.blocking_strings()
        assert any("B002" in s for s in strings)

    def test_w001_warning_low_confidence(self):
        case = _base_case(confidence=0.40)
        report = run_compliance(case)
        assert not report.is_blocked
        assert any("W001" in w for w in report.warnings)
        assert report.status == "WARNING"

    def test_w002_warning_distant_comp(self):
        case = _base_case()
        case["comparables"][0]["distance_km"] = 35  # >30 warning but <50 blocking
        report = run_compliance(case)
        assert not report.is_blocked
        assert any("W002" in w for w in report.warnings)

    def test_multiple_violations_all_reported(self):
        case = _base_case()
        del case["dossier_id"]
        del case["comparables"][0]["source_id"]
        report = run_compliance(case)
        rules = {r.rule for r in report.blocking}
        assert "B001" in rules
        assert "B002" in rules
