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
        assert applicable_approaches("unifamiliale") == ["approche_comparative"]

    def test_maison_comparative_only(self):
        from engine.valuation import applicable_approaches
        assert applicable_approaches("maison") == ["approche_comparative"]

    def test_cottage_comparative_only(self):
        from engine.valuation import applicable_approaches
        assert applicable_approaches("cottage") == ["approche_comparative"]

    def test_residentiel_unifamilial_comparative_only(self):
        from engine.valuation import applicable_approaches
        assert applicable_approaches("residentiel_unifamilial") == ["approche_comparative"]

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

    def test_commercial_includes_revenu(self):
        from engine.valuation import applicable_approaches
        assert "approche_revenu" in applicable_approaches("commercial")

    def test_empty_defaults_to_comparative_only(self):
        from engine.valuation import applicable_approaches
        assert applicable_approaches("") == ["approche_comparative"]

    def test_unknown_type_defaults_to_comparative_only(self):
        from engine.valuation import applicable_approaches
        assert applicable_approaches("propriete_speciale_xyz") == ["approche_comparative"]

    def test_cout_never_in_applicable(self):
        """L'approche coût n'est jamais retournée — données Altus absentes."""
        from engine.valuation import applicable_approaches
        for t in ["unifamiliale", "immeuble_revenus", "commercial", "terrain", ""]:
            assert "approche_cout" not in applicable_approaches(t)


# ── watermark proxy ───────────────────────────────────────────────────────────

class TestWatermarkProxy:
    _CASE = {
        "comparables": [
            {"comparable_id": "C1", "source_id": "JLR-001", "prix_vente": 400000, "date_vente": "2025-01-01"},
        ],
        "ajustements": [],
    }

    def test_cout_has_avertissement(self):
        from engine.valuation import calculate_valuation_trace
        result = calculate_valuation_trace(self._CASE, "approche_cout")
        assert "AVERTISSEMENT" in result
        assert "PROXY" in str(result["AVERTISSEMENT"])
        assert "OEAQ" in str(result["AVERTISSEMENT"])

    def test_revenu_has_avertissement(self):
        from engine.valuation import calculate_valuation_trace
        result = calculate_valuation_trace(self._CASE, "approche_revenu")
        assert "AVERTISSEMENT" in result
        assert "PROXY" in str(result["AVERTISSEMENT"])

    def test_comparative_no_avertissement(self):
        from engine.valuation import calculate_valuation_trace
        result = calculate_valuation_trace(self._CASE, "approche_comparative")
        assert "AVERTISSEMENT" not in result

    def test_watermark_mentions_altus(self):
        from engine.valuation import calculate_valuation_trace
        result = calculate_valuation_trace(self._CASE, "approche_cout")
        assert "Altus" in str(result["AVERTISSEMENT"])


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
        assert rev.get("value") is not None

    def test_cout_always_not_applicable(self):
        from engine.valuation import calculate_all_valuation_traces
        for t in ["unifamiliale", "immeuble_revenus", "commercial"]:
            traces = calculate_all_valuation_traces(self._CASE, type_bien=t)
            cout = traces["approche_cout"]
            assert cout.get("applicable") is False, f"cout should not be applicable for {t}"

    def test_type_bien_from_case_dict(self):
        """type_bien absent du paramètre → lu depuis case dict."""
        from engine.valuation import calculate_all_valuation_traces
        case = {**self._CASE, "type_bien": "unifamiliale"}
        traces = calculate_all_valuation_traces(case)  # no type_bien param
        assert traces["approche_revenu"].get("applicable") is False


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
