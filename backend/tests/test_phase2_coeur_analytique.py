"""Phase 2 T2.1 — Grille d'ajustements par comparable.

DoD : l'artefact comparatif contient la grille complète (≥7 lignes/comp,
prix ajustés, fourchette) ; tests sur un dossier de référence.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.adjustments import (
    AdjustmentRates,
    ComparableGrid,
    compute_adjustment_grid,
    compute_adjustment_grid_one,
    _to_m2,
    _months_diff,
)


# ── Utilitaires ───────────────────────────────────────────────────────────────

def test_to_m2_dict_m2():
    assert _to_m2({"value": 100, "unit": "m2"}) == 100.0


def test_to_m2_dict_pi2():
    result = _to_m2({"value": 1000, "unit": "pi2"})
    assert result is not None
    assert 90 < result < 95  # 1000 * 0.0929 ≈ 92.9


def test_to_m2_float():
    assert _to_m2(150.0) == 150.0


def test_to_m2_none():
    assert _to_m2(None) is None
    assert _to_m2(0) is None


def test_months_diff():
    assert _months_diff(date(2025, 1, 1), date(2025, 7, 1)) == 6
    assert _months_diff(date(2025, 6, 1), date(2025, 1, 1)) == -5


# ── ComparableGrid ────────────────────────────────────────────────────────────

def _make_comp(prix=500_000, date_vente="2025-06-01",
               surface={"value": 120, "unit": "m2"},
               surface_terrain=400):
    return {
        "comparable_id": "C-001",
        "source_id": "JLR-001",
        "adresse": "123 rue Test",
        "prix_vente": prix,
        "date_vente": date_vente,
        "surface": surface,
        "surface_terrain": surface_terrain,
    }


def _make_sujet(surface={"value": 130, "unit": "m2"}, surface_terrain=450):
    return {
        "dossier_id": "D-T21",
        "date_reference": "2026-01-01",
        "type_bien": "unifamiliale",
        "surface": surface,
        "surface_terrain": surface_terrain,
        "comparables": [],
    }


def test_grid_one_has_7_lines():
    sujet = _make_sujet()
    comp = _make_comp()
    rates = AdjustmentRates()
    g = compute_adjustment_grid_one(sujet, comp, date.fromisoformat("2026-01-01"), rates)
    assert len(g.ajustements) == 7


def test_grid_one_caracteristiques():
    sujet = _make_sujet()
    comp = _make_comp()
    g = compute_adjustment_grid_one(sujet, comp, date.fromisoformat("2026-01-01"), AdjustmentRates())
    caract = [a.caracteristique for a in g.ajustements]
    assert "date_marche" in caract
    assert "superficie_habitable" in caract
    assert "superficie_terrain" in caract
    assert "garage_stationnement" in caract
    assert "etat_condition" in caract
    assert "sous_sol_fini" in caract
    assert "localisation" in caract


def test_grid_one_date_adj_positive():
    sujet = _make_sujet()
    comp = _make_comp(date_vente="2025-01-01", prix=500_000)
    g = compute_adjustment_grid_one(sujet, comp, date.fromisoformat("2026-01-01"), AdjustmentRates())
    date_line = next(a for a in g.ajustements if a.caracteristique == "date_marche")
    # 12 mois × 0.35% × 500000 = 17500
    assert date_line.montant > 10_000


def test_grid_one_superficie_adj_positive_when_sujet_bigger():
    sujet = _make_sujet(surface={"value": 150, "unit": "m2"})
    comp = _make_comp(surface={"value": 100, "unit": "m2"})
    g = compute_adjustment_grid_one(sujet, comp, date.fromisoformat("2026-01-01"), AdjustmentRates())
    surf_line = next(a for a in g.ajustements if a.caracteristique == "superficie_habitable")
    assert surf_line.montant > 0  # sujet plus grand → comp sous-évalué → adj positif


def test_grid_one_prix_ajuste_computed():
    sujet = _make_sujet()
    comp = _make_comp(prix=500_000)
    g = compute_adjustment_grid_one(sujet, comp, date.fromisoformat("2026-01-01"), AdjustmentRates())
    assert g.prix_ajuste > 0
    assert g.prix_ajuste != g.prix_vendu  # ajustements non nuls


def test_grid_one_pct_total_brut():
    sujet = _make_sujet()
    comp = _make_comp()
    g = compute_adjustment_grid_one(sujet, comp, date.fromisoformat("2026-01-01"), AdjustmentRates())
    assert 0.0 <= g.pct_total_brut <= 100.0


def test_grid_one_missing_data_status():
    """Quand la surface comp est absente, la ligne doit être 'donnees_manquantes'."""
    sujet = _make_sujet()
    comp = {"comparable_id": "C-001", "source_id": "JLR-001", "prix_vente": 400_000, "date_vente": "2025-06-01"}
    g = compute_adjustment_grid_one(sujet, comp, date.fromisoformat("2026-01-01"), AdjustmentRates())
    surf_line = next(a for a in g.ajustements if a.caracteristique == "superficie_habitable")
    assert surf_line.statut == "donnees_manquantes"
    assert surf_line.montant == 0


# ── compute_adjustment_grid (dossier complet) ─────────────────────────────────

def _make_case_with_comps():
    return {
        "dossier_id": "D-T21-FULL",
        "date_reference": "2026-01-01",
        "type_bien": "unifamiliale",
        "surface": {"value": 130, "unit": "m2"},
        "surface_terrain": 450,
        "comparables": [
            {
                "comparable_id": f"C-00{i}",
                "source_id": f"JLR-00{i}",
                "prix_vente": 480_000 + i * 20_000,
                "date_vente": f"2025-0{i + 3}-01",
                "surface": {"value": 115 + i * 5, "unit": "m2"},
                "surface_terrain": 380 + i * 20,
            }
            for i in range(1, 4)
        ],
    }


def test_compute_grid_returns_grilles():
    case = _make_case_with_comps()
    result = compute_adjustment_grid(case)
    assert len(result["grilles"]) == 3
    for g in result["grilles"]:
        assert len(g["ajustements"]) == 7


def test_compute_grid_valeur_indiquee_in_range():
    case = _make_case_with_comps()
    result = compute_adjustment_grid(case)
    vi = result["valeur_indiquee"]
    f = result["fourchette"]
    assert vi > 0
    assert f["min"] <= vi <= f["max"]


def test_compute_grid_fourchette_ecart():
    case = _make_case_with_comps()
    result = compute_adjustment_grid(case)
    f = result["fourchette"]
    assert f["ecart_pct"] >= 0


def test_compute_grid_empty_comparables():
    case = {"dossier_id": "D-EMPTY", "date_reference": "2026-01-01", "comparables": []}
    result = compute_adjustment_grid(case)
    assert result["valeur_indiquee"] == 0.0
    assert "Aucun comparable" in result["avertissements"][0]


def test_compute_grid_to_dict_schema():
    case = _make_case_with_comps()
    result = compute_adjustment_grid(case)
    for g in result["grilles"]:
        assert "comparable_id" in g
        assert "prix_vendu" in g
        assert "prix_ajuste" in g
        assert "total_ajustements" in g
        assert "pct_total_brut" in g
        assert "statut" in g
        assert "alerte_seuil_25pct" in g


# ── Intégration dans valuation.py ─────────────────────────────────────────────

def test_calculate_comparative_includes_grille():
    from engine.valuation import calculate_valuation_trace
    case = _make_case_with_comps()
    comp_result = calculate_valuation_trace(case, "approche_comparative")
    assert comp_result is not None
    trace = comp_result.get("trace", {})
    assert "grille_ajustements" in trace
    assert len(trace["grille_ajustements"]) >= 1
    assert "fourchette" in trace
    assert "valeur_indiquee_grille" in trace


# ── T2.3 : AMU réelle ──────────────────────────────────────────────────────────

from engine.amu import evaluate_amu


def _base_amu_case(**overrides):
    case = {
        "dossier_id": "D-T23",
        "type_bien": "unifamiliale",
        "zone": "R2",
        "date_reference": "2026-01-01",
    }
    case.update(overrides)
    return case


def test_amu_sans_donnees_returns_none_conformite():
    result = evaluate_amu(_base_amu_case())
    umpp = result["umpp"]
    assert umpp["conformite_zonage"] is None
    assert umpp["criteres"]["legalement_permis"]["confiance"] == "donnees_manquantes"


def test_amu_zone_agricole_detecte_restriction():
    case = _base_amu_case(
        zone_agricole={"en_zone_verte": True, "type_zone": "zone_verte_CPTAQ"}
    )
    result = evaluate_amu(case)
    c1 = result["umpp"]["criteres"]["legalement_permis"]
    assert c1["resultat"] is False
    assert "CPTAQ" in c1["justification"] or "CPTAQ" in " ".join(c1["signaux"])


def test_amu_zone_inondable_fort_affecte_c2():
    case = _base_amu_case(
        zone_inondable={"en_zone_inondable": True, "risque": "fort"}
    )
    result = evaluate_amu(case)
    c2 = result["umpp"]["criteres"]["physiquement_possible"]
    assert c2["resultat"] is False
    assert "inondable" in c2["justification"].lower()


def test_amu_patrimoine_culturel_signale():
    case = _base_amu_case(
        patrimoine_culturel={"statut": "cite_du_patrimoine"}
    )
    result = evaluate_amu(case)
    c1 = result["umpp"]["criteres"]["legalement_permis"]
    assert any("patrimoine" in s.lower() for s in c1["signaux"])
    assert c1["resultat"] is False


def test_amu_zonage_urbanisme_usage_autorise():
    case = _base_amu_case(
        zonage_urbanisme={
            "ZONE": "R-2",
            "USAGE_PRINCIPAL": "Résidentiel",
            "usages_autorises": ["residentiel", "unifamiliale"],
        }
    )
    result = evaluate_amu(case)
    c1 = result["umpp"]["criteres"]["legalement_permis"]
    assert c1["resultat"] is True
    assert result["umpp"]["conformite_zonage"] is True


def test_amu_no_restriction_conclusion_umpp_actuel():
    case = _base_amu_case(
        zonage_urbanisme={"ZONE": "R-2", "usages_autorises": ["unifamiliale"]},
        zone_inondable={"en_zone_inondable": False},
        surface_terrain=500,
    )
    result = evaluate_amu(case)
    umpp = result["umpp"]
    assert umpp["umpp_differe_usage_actuel"] is False
    assert "constitue le meilleur usage" in umpp["conclusion"]


def test_amu_umpp_differe_when_c1_false():
    case = _base_amu_case(
        zone_agricole={"en_zone_verte": True, "type_zone": "zone_verte"}
    )
    result = evaluate_amu(case)
    assert result["umpp"]["umpp_differe_usage_actuel"] is True
    assert "contraintes" in result["umpp"]["conclusion"].lower()


def test_amu_confidence_partielle_without_data():
    result = evaluate_amu(_base_amu_case())
    assert result["confidence"] <= 0.70


def test_amu_payload_schema_keys():
    result = evaluate_amu(_base_amu_case())
    umpp = result["umpp"]
    for key in ("usage_retenu", "usage_actuel", "conformite_zonage",
                "criteres", "umpp_differe_usage_actuel", "conclusion",
                "avertissements", "methodologie"):
        assert key in umpp, f"Clé manquante : {key}"
    for crit in ("legalement_permis", "physiquement_possible",
                 "financierement_faisable", "maximalement_productif"):
        assert crit in umpp["criteres"]
        c = umpp["criteres"][crit]
        assert "resultat" in c and "confiance" in c and "justification" in c


def test_amu_methodologie_deterministe():
    result = evaluate_amu(_base_amu_case())
    assert result["umpp"]["methodologie"] == "deterministe_v1"


def test_amu_no_hardcoded_true():
    """Constat A3 : conformite_zonage ne doit plus être True en dur sans données."""
    case = _base_amu_case()  # sans zonage_urbanisme
    result = evaluate_amu(case)
    # Sans données, doit être None pas True
    assert result["umpp"]["conformite_zonage"] is not True
