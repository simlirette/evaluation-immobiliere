from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_cost_approach_uses_replacement_cost_depreciation_and_land():
    from engine.valuation import calculate_cost_approach

    result = calculate_cost_approach({
        "type_bien": "unifamiliale",
        "surface_habitable": 100,
        "couts_reference": {
            "cout_unitaire_m2": 2000,
            "valeur_terrain": 100000,
            "taux_depreciation_pct": 10,
            "facteurs": {"temps": 1.10},
        },
    })

    assert result["method"] == "replacement_cost_less_depreciation_v1"
    assert result["calculation_status"] == "OK"
    assert result["value"] == pytest.approx(298000)
    trace = result["trace"]
    assert trace["cout_neuf"] == pytest.approx(220000)
    assert trace["depreciation"] == pytest.approx(22000)
    assert trace["valeur_terrain"] == pytest.approx(100000)


def test_cost_approach_insurance_excludes_land_and_depreciation():
    from engine.valuation import calculate_cost_approach

    result = calculate_cost_approach({
        "mandat_type": "assurance",
        "type_bien": "unifamiliale",
        "surface_habitable": 100,
        "couts_reference": {
            "cout_unitaire_m2": 2000,
            "valeur_terrain": 100000,
            "taux_depreciation_pct": 50,
        },
    })

    assert result["method"] == "replacement_cost_insurance_v1"
    assert result["value"] == pytest.approx(200000)
    assert result["trace"]["valeur_terrain"] == 0
    assert result["trace"]["depreciation"] == 0


def test_income_approach_direct_capitalization_uses_rbp_vacancy_expenses_and_cap_rate():
    from engine.valuation import calculate_income_approach

    result = calculate_income_approach({
        "type_bien": "immeuble_revenus",
        "revenus_depenses": {
            "revenu_brut_potentiel": 120000,
            "taux_vacance_pct": 5,
            "depenses_exploitation": 35000,
            "taux_capitalisation_pct": 5,
        },
    })

    assert result["method"] == "direct_capitalization_v1"
    assert result["calculation_status"] == "OK"
    assert result["trace"]["revenu_brut_effectif"] == pytest.approx(114000)
    assert result["trace"]["rne"] == pytest.approx(79000)
    assert result["value"] == pytest.approx(1580000)


def test_income_approach_fta_dcf_matches_documented_example():
    from engine.valuation import calculate_valuation_trace

    result = calculate_valuation_trace({
        "type_bien": "commercial_revenus",
        "fta": {
            "rne_initial": 100000,
            "projection_years": 5,
            "croissance_rne_pct": 3,
            "taux_actualisation_pct": 7,
            "taux_capitalisation_sortie_pct": 6.5,
            "croissance_terminale_pct": 2,
        },
    }, "approche_revenu")

    assert result["method"] == "fta_dcf_v1"
    assert result["calculation_status"] == "OK"
    assert result["value"] == pytest.approx(1_692_400, rel=0.002)
    assert result["trace"]["projection_years"] == 5
    assert len(result["trace"]["cash_flows"]) == 5
    assert result["trace"]["pv_terminal"] > result["trace"]["pv_cash_flows"]


def test_approaches_for_case_honors_mandate_required_methods():
    from engine.valuation import approaches_for_case

    assert approaches_for_case({
        "type_bien": "terrain",
        "methodes_requises": ["approche_cout"],
    }) == ["approche_cout"]


def test_cost_approach_does_not_use_comparable_sale_prices_as_proxy():
    from engine.valuation import calculate_cost_approach

    result = calculate_cost_approach({
        "type_bien": "unifamiliale",
        "comparables": [
            {"source_id": "SRC-1", "prix_vente": 999999, "date_vente": "2025-01-01"},
        ],
    })

    assert result["value"] is None
    assert result["calculation_status"] == "INSUFFICIENT_COST_DATA"
    assert "selected_comparables" not in result["trace"]
