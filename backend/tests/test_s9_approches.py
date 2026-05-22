"""S9 tests — approches conditionnelles par type_bien + watermark proxy."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ── applicable_approaches ─────────────────────────────────────────────────────

class TestApplicableApproaches:
    def test_unifamiliale_comparative_only(self):
        from engine.valuation import applicable_approaches
        assert applicable_approaches("unifamiliale") == ["approche_comparative", "approche_cout"]

    def test_maison_comparative_only(self):
        from engine.valuation import applicable_approaches
        assert applicable_approaches("maison") == ["approche_comparative", "approche_cout"]

    def test_cottage_comparative_only(self):
        from engine.valuation import applicable_approaches
        assert applicable_approaches("cottage") == ["approche_comparative", "approche_cout"]

    def test_residentiel_unifamilial_comparative_only(self):
        from engine.valuation import applicable_approaches
        assert applicable_approaches("residentiel_unifamilial") == ["approche_comparative", "approche_cout"]

    def test_terrain_comparative_only(self):
        from engine.valuation import applicable_approaches
        assert applicable_approaches("terrain") == ["approche_comparative"]

    def test_immeuble_revenus_includes_revenu(self):
        from engine.valuation import applicable_approaches
        assert "approche_revenu" in applicable_approaches("immeuble_revenus")
        assert "approche_comparative" in applicable_approaches("immeuble_revenus")

    def test_duplex_includes_revenu(self):
        from engine.valuation import applicable_approaches
        assert "approche_revenu" in applicable_approaches("duplex")

    def test_commercial_includes_cout(self):
        from engine.valuation import applicable_approaches
        assert "approche_cout" in applicable_approaches("commercial")

    def test_empty_defaults_to_comparative_only(self):
        from engine.valuation import applicable_approaches
        assert applicable_approaches("") == ["approche_comparative"]

    def test_unknown_type_defaults_to_comparative_only(self):
        from engine.valuation import applicable_approaches
        assert applicable_approaches("propriete_speciale_xyz") == ["approche_comparative"]

    def test_terrain_excludes_cout_and_revenu(self):
        from engine.valuation import applicable_approaches
        for t in ["terrain", "terrain_vacant", "lot"]:
            assert "approche_cout" not in applicable_approaches(t)
            assert "approche_revenu" not in applicable_approaches(t)


# ── deterministic cost/revenue model failures ────────────────────────────────

class TestModelInputFailures:
    _CASE = {
        "comparables": [
            {"comparable_id": "C1", "source_id": "JLR-001", "prix_vente": 400000, "date_vente": "2025-01-01"},
        ],
        "ajustements": [],
    }

    def test_cout_requires_cost_inputs(self):
        from engine.valuation import calculate_valuation_trace
        result = calculate_valuation_trace(self._CASE, "approche_cout")
        assert "AVERTISSEMENT" in result
        assert result["value"] is None
        assert result["calculation_status"] == "INSUFFICIENT_COST_DATA"

    def test_revenu_requires_income_inputs(self):
        from engine.valuation import calculate_valuation_trace
        result = calculate_valuation_trace(self._CASE, "approche_revenu")
        assert "AVERTISSEMENT" in result
        assert result["value"] is None
        assert result["calculation_status"] == "INSUFFICIENT_INCOME_DATA"

    def test_comparative_no_avertissement(self):
        from engine.valuation import calculate_valuation_trace
        result = calculate_valuation_trace(self._CASE, "approche_comparative")
        assert "AVERTISSEMENT" not in result

    def test_no_proxy_watermark(self):
        from engine.valuation import calculate_valuation_trace
        result = calculate_valuation_trace(self._CASE, "approche_cout")
        assert "PROXY" not in str(result.get("AVERTISSEMENT", ""))


# ── calculate_all_valuation_traces — filtrage par type_bien ──────────────────

class TestCalculateAllFilteredByType:
    _CASE = {
        "comparables": [
            {"comparable_id": "C1", "source_id": "JLR-001", "prix_vente": 420000, "date_vente": "2025-03-01"},
        ],
        "ajustements": [],
    }

    def test_unifamiliale_revenu_not_applicable(self):
        from engine.valuation import calculate_all_valuation_traces
        traces = calculate_all_valuation_traces(self._CASE, type_bien="unifamiliale")
        rev = traces["approche_revenu"]
        assert rev.get("applicable") is False
        assert rev.get("value") is None

    def test_unifamiliale_comparative_has_value(self):
        from engine.valuation import calculate_all_valuation_traces
        traces = calculate_all_valuation_traces(self._CASE, type_bien="unifamiliale")
        comp = traces["approche_comparative"]
        assert comp.get("value") is not None
        assert float(comp["value"]) > 0

    def test_immeuble_revenus_revenu_applicable(self):
        from engine.valuation import calculate_all_valuation_traces
        traces = calculate_all_valuation_traces(self._CASE, type_bien="immeuble_revenus")
        rev = traces["approche_revenu"]
        # applicable not set to False → real trace
        assert rev.get("applicable") is not False
        assert rev.get("value") is None
        assert rev.get("calculation_status") == "INSUFFICIENT_INCOME_DATA"

    def test_unifamiliale_cout_applicable_but_requires_inputs(self):
        from engine.valuation import calculate_all_valuation_traces
        traces = calculate_all_valuation_traces(self._CASE, type_bien="unifamiliale")
        cout = traces["approche_cout"]
        assert cout.get("applicable") is not False
        assert cout.get("calculation_status") == "INSUFFICIENT_COST_DATA"

    def test_type_bien_from_case_dict(self):
        """type_bien absent du paramètre → lu depuis case dict."""
        from engine.valuation import calculate_all_valuation_traces
        case = {**self._CASE, "type_bien": "unifamiliale"}
        traces = calculate_all_valuation_traces(case)  # no type_bien param
        assert traces["approche_revenu"].get("applicable") is False


# ── valuation input hardening ─────────────────────────────────────────────────

class TestValuationInputHardening:
    def test_zero_price_comparable_is_excluded(self):
        from engine.valuation import calculate_valuation_trace
        case = {
            "comparables": [
                {"comparable_id": "C0", "source_id": "JLR-000", "prix_vente": 0, "date_vente": "2025-01-01"},
                {"comparable_id": "C1", "source_id": "JLR-001", "prix_vente": 400000, "date_vente": "2025-01-01"},
            ],
            "ajustements": [],
        }
        result = calculate_valuation_trace(case, "approche_comparative")
        assert result["input_count"] == 1
        assert result["excluded_comparable_count"] == 1
        selected = result["trace"]["selected_comparables"]
        assert [c["comparable_id"] for c in selected] == ["C1"]

    def test_no_usable_comparable_sets_status_and_warning(self):
        from engine.valuation import calculate_valuation_trace
        case = {
            "comparables": [
                {"comparable_id": "C0", "source_id": "JLR-000", "prix_vente": 0, "date_vente": "2025-01-01"},
            ],
            "ajustements": [{"montant": "bad", "validation_humaine": True}],
        }
        result = calculate_valuation_trace(case, "approche_comparative")
        assert result["value"] == 0
        assert result["input_count"] == 0
        assert result["calculation_status"] == "INSUFFICIENT_COMPARABLES"
        assert "AVERTISSEMENT" in result


# ── StatCan WDS désactivé ─────────────────────────────────────────────────────

class TestWdsDisabled:
    def test_wds_post_returns_none(self):
        from engine.data_enrichment import _wds_post
        result = _wds_post("getCubeMetadata/123", {})
        assert result is None

    def test_wds_get_returns_none(self):
        from engine.data_enrichment import _wds_get
        result = _wds_get("getCubeMetadata/123")
        assert result is None
