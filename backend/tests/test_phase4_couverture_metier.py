"""Phase 4 T4.1–T4.4 — Mandats spéciaux : succession, contestation, expropriation, liquidation.

DoD T4.1 : mandat succession route correctement, date rétrospective gérée.
DoD T4.2 : JVM/valeur réelle injectées dans le prompt rapport.
DoD T4.3 : expropriation avant-après produit indemnité = avant − après + préjudices.
DoD T4.4 : liquidation produit valeur avec décote quantifiée.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.orchestrator import classify_dossier, available_mandat_types
from engine.valuation import calculate_expropriation, calculate_liquidation_value
from engine.runtime import _mandat_special_lines


# ── T4.1+T4.2 : routing mandats spéciaux ────────────────────────────────────

def test_classify_succession_from_but():
    case = {"type_bien": "unifamiliale", "but_evaluation": "succession"}
    assert classify_dossier(case) == "succession"


def test_classify_succession_from_mandat_type():
    case = {"type_bien": "unifamiliale", "mandat_type": "succession"}
    assert classify_dossier(case) == "succession"


def test_classify_donation_from_but():
    case = {"but_evaluation": "donation entre vifs"}
    assert classify_dossier(case) == "donation"


def test_classify_contestation_from_but():
    case = {"but_evaluation": "contestation rôle municipal triennal"}
    assert classify_dossier(case) == "contestation_role"


def test_classify_expropriation_from_but():
    case = {"but_evaluation": "expropriation partielle par la ville"}
    assert classify_dossier(case) == "expropriation"


def test_classify_liquidation_from_but():
    case = {"but_evaluation": "liquidation vente forcée"}
    assert classify_dossier(case) == "liquidation"


def test_classify_financement_from_but():
    case = {"but_evaluation": "financement hypothécaire"}
    assert classify_dossier(case) == "financement"


def test_all_new_mandats_available():
    available = available_mandat_types()
    for mandat in ("succession", "donation", "contestation_role",
                   "expropriation", "liquidation", "financement"):
        assert mandat in available, f"{mandat} non dans available_mandat_types"


def test_mandat_special_lines_succession():
    case = {"mandat_type": "succession", "date_reference": "2024-12-15"}
    lines = _mandat_special_lines(case)
    text = "\n".join(lines)
    assert "JVM" in text or "Juste valeur marchande" in text
    assert "LIR" in text or "impôt sur le revenu" in text.lower()
    assert "antérieurs" in text or "CONTRAINTE DATE" in text or "rétrospective" in text.lower()


def test_mandat_special_lines_contestation():
    case = {"mandat_type": "contestation_role"}
    lines = _mandat_special_lines(case)
    text = "\n".join(lines)
    assert "valeur réelle" in text.lower() or "valeur_reelle" in text
    assert "LFM" in text or "art. 42" in text or "triennal" in text.lower()


def test_mandat_special_lines_expropriation():
    case = {"mandat_type": "expropriation"}
    lines = _mandat_special_lines(case)
    text = "\n".join(lines)
    assert "avant-après" in text or "avant" in text.lower()
    assert "indemnité" in text.lower() or "indemnite" in text.lower()


def test_mandat_special_lines_standard_empty():
    case = {"mandat_type": "residentiel_standard"}
    lines = _mandat_special_lines(case)
    # Pas de consignes spéciales pour le résidentiel standard
    text = "\n".join(lines)
    assert "CONTRAINTE DATE" not in text
    assert "MÉTHODE OBLIGATOIRE" not in text


# ── T4.3 : Expropriation avant-après ────────────────────────────────────────

def test_expropriation_basic():
    case = {
        "type_bien": "unifamiliale",
        "expropriation": {
            "valeur_avant": 600_000,
            "valeur_apres": 420_000,
            "prejudices": [{"description": "Dépréciation contiguïté", "montant": 15_000}],
        }
    }
    result = calculate_expropriation(case)
    assert result["calculation_status"] == "OK"
    assert result["value"] == 195_000  # 600k - 420k + 15k


def test_expropriation_no_prejudices():
    case = {"expropriation": {"valeur_avant": 500_000, "valeur_apres": 380_000}}
    result = calculate_expropriation(case)
    assert result["value"] == 120_000  # 500k - 380k + 0


def test_expropriation_missing_avant():
    case = {"expropriation": {"valeur_apres": 300_000}}
    result = calculate_expropriation(case)
    assert result["calculation_status"] == "MISSING_VALEUR_AVANT"
    assert result["value"] is None


def test_expropriation_trace_structure():
    case = {"expropriation": {"valeur_avant": 700_000, "valeur_apres": 500_000,
                               "prejudices": 25_000}}
    result = calculate_expropriation(case)
    trace = result["trace"]
    assert "valeur_avant" in trace
    assert "valeur_apres" in trace
    assert "total_prejudices" in trace
    assert "indemnite_totale" in trace
    assert trace["indemnite_totale"] == 225_000  # 700k - 500k + 25k


def test_expropriation_approach_name():
    result = calculate_expropriation({"expropriation": {"valeur_avant": 400_000}})
    assert result["approach"] == "approche_avant_apres"


# ── T4.4 : Liquidation ──────────────────────────────────────────────────────

def test_liquidation_with_decote():
    case = {"liquidation": {"valeur_marchande": 500_000, "decote_pct": 20}}
    result = calculate_liquidation_value(case)
    assert result["calculation_status"] == "OK"
    assert result["value"] == 400_000  # 500k * (1 - 0.20)


def test_liquidation_default_decote():
    case = {"liquidation": {"valeur_marchande": 400_000}}
    result = calculate_liquidation_value(case)
    assert result["calculation_status"] == "OK"
    assert result["value"] < 400_000
    assert "AVERTISSEMENT" in result  # décote par défaut → proxy warning


def test_liquidation_from_case_level():
    case = {"valeur_marchande": 300_000, "liquidation": {"decote_pct": 10}}
    result = calculate_liquidation_value(case)
    assert result["value"] == 270_000  # 300k * 0.90


def test_liquidation_missing_valeur():
    case = {"liquidation": {}}
    result = calculate_liquidation_value(case)
    assert result["calculation_status"] == "MISSING_VALEUR_MARCHANDE"
    assert result["value"] is None


def test_liquidation_trace_decote_pct():
    case = {"liquidation": {"valeur_marchande": 600_000, "decote_pct": 12,
                             "type_liquidation": "ordonnee",
                             "justification": "Période d'exposition de 30 jours"}}
    result = calculate_liquidation_value(case)
    trace = result["trace"]
    assert trace["decote_pct"] == 12
    assert trace["decote_source"] == "fournie"
    assert trace["type_liquidation"] == "ordonnee"
    assert "30 jours" in trace["justification"]


# ── T4.7 : outils assistant d'action ─────────────────────────────────────────

def test_agent_tools_list():
    """Les 5 outils doivent être dans _AGENT_TOOLS."""
    import api  # type: ignore
    tool_names = {t["function"]["name"] for t in api._AGENT_TOOLS}
    assert "fetch_artifact" in tool_names
    assert "search_knowledge" in tool_names
    assert "search_comparables" in tool_names
    assert "run_calculation" in tool_names
    assert "rerun_step" in tool_names
    assert len(api._AGENT_TOOLS) == 5


def test_search_comparables_tool_schema():
    import api  # type: ignore
    tool = next(t for t in api._AGENT_TOOLS if t["function"]["name"] == "search_comparables")
    params = tool["function"]["parameters"]["properties"]
    assert "prix_min" in params
    assert "prix_max" in params
    assert "distance_max_km" in params
    assert "date_min" in params
    assert "date_max" in params


def test_run_calculation_tool_schema():
    import api  # type: ignore
    tool = next(t for t in api._AGENT_TOOLS if t["function"]["name"] == "run_calculation")
    params = tool["function"]["parameters"]["properties"]
    assert "approche" in params
    assert "overrides" in params
    approaches = tool["function"]["parameters"]["properties"]["approche"]["enum"]
    assert "approche_comparative" in approaches
    assert "approche_revenu" in approaches
    assert "approche_liquidation" in approaches


def test_rerun_step_tool_schema():
    import api  # type: ignore
    tool = next(t for t in api._AGENT_TOOLS if t["function"]["name"] == "rerun_step")
    params = tool["function"]["parameters"]["properties"]
    assert "step" in params
    assert "raison" in params
    steps = tool["function"]["parameters"]["properties"]["step"]["enum"]
    assert "comps-market" in steps
    assert "valuation-draft" in steps
    assert "redaction" in steps


def test_execute_tool_call_dispatch_unknown():
    import api  # type: ignore
    result = api._execute_tool_call("outil_inexistant", {}, "s-001", "D-001")
    assert "inconnu" in result.lower()


def test_execute_run_calculation_no_session(tmp_path, monkeypatch):
    """Sans session valide, run_calculation retourne un message d'erreur."""
    import api  # type: ignore
    monkeypatch.setattr(api, "SESSIONS_DIR", tmp_path)
    result = api._execute_run_calculation("session-inexistante", "D-000", "approche_comparative")
    assert "introuvable" in result.lower() or "non trouvée" in result.lower()


def test_execute_search_comparables_no_session(tmp_path, monkeypatch):
    import api  # type: ignore
    monkeypatch.setattr(api, "SESSIONS_DIR", tmp_path)
    result = api._execute_search_comparables("session-inexistante", "D-000")
    assert "introuvable" in result.lower()


# ── T4.5 : immeubles revenus complets ─────────────────────────────────────────

from engine.valuation import _income_inputs


def test_income_provision_remplacement_7plus():
    """Immeuble 7+ logements → provision remplacement par défaut 3%."""
    case = {
        "type_bien": "immeuble_revenus",
        "nb_logements": 8,
        "revenus_depenses": {
            "revenu_brut_potentiel": 120_000,
            "depenses_exploitation": 30_000,
        },
    }
    income = _income_inputs(case)
    assert income["provision_remplacement"] > 0
    assert "provision_remplacement_defaut_3pct_a_valider" in income["notes"]


def test_income_provision_fournie():
    """Provision fournie explicitement — pas de défaut."""
    case = {
        "type_bien": "immeuble_revenus",
        "nb_logements": 10,
        "revenus_depenses": {
            "revenu_brut_potentiel": 200_000,
            "depenses_exploitation": 60_000,
            "provision_remplacement": 8_000,
        },
    }
    income = _income_inputs(case)
    assert income["provision_remplacement"] == 8_000
    assert income["provision_remplacement_source"] == "fournie"
    assert "provision_remplacement_defaut_3pct_a_valider" not in income["notes"]


def test_income_baux_summary():
    """Revenus depuis baux individuels."""
    case = {
        "type_bien": "triplex",
        "nb_logements": 3,
        "revenus_depenses": {
            "baux": [
                {"loyer_mensuel": 1200},
                {"loyer_mensuel": 1350},
                {"loyer_mensuel": 1100},
            ],
        },
    }
    income = _income_inputs(case)
    assert "baux_summary" in income
    assert income["baux_summary"]["nb_baux"] == 3
    assert income["revenu_brut_potentiel"] == pytest.approx(3650 * 12, abs=1)


def test_income_no_provision_for_small_building():
    """Immeuble < 7 logements → pas de provision par défaut."""
    case = {
        "type_bien": "triplex",
        "nb_logements": 3,
        "revenus_depenses": {
            "revenu_brut_potentiel": 48_000,
        },
    }
    income = _income_inputs(case)
    assert income.get("provision_remplacement", 0) == 0


# ── T4.6 : types spécialisés ──────────────────────────────────────────────────

from engine.specialized_valuation import (
    analyze_copropriation_indivise,
    analyze_agricole,
    analyze_patrimonial,
    analyze_rpa,
    analyze_specialized_property,
    specialized_mentions_for_prompt,
)


def test_indivise_applicable():
    case = {"type_bien": "copropriation_indivise", "convention_indivision": {"part_pct": 40}}
    note = analyze_copropriation_indivise(case)
    assert note.statut == "applicable"
    assert any("décote" in m.lower() for m in note.mentions)
    assert len(note.ajustements) == 1
    assert note.ajustements[0]["montant_relatif_pct"] < 0


def test_indivise_not_applicable():
    case = {"type_bien": "unifamiliale"}
    note = analyze_copropriation_indivise(case)
    assert note.statut == "non_applicable"


def test_agricole_zone_verte():
    case = {
        "type_bien": "terrain_agricole",
        "surface_terrain": 50_000,  # 5 ha
        "zone_agricole": {"en_zone_verte": True, "type_zone": "zone_verte_cptaq"},
        "prix_par_hectare": 20_000,
    }
    note = analyze_agricole(case)
    assert note.statut == "applicable"
    assert any("CPTAQ" in m or "zone verte" in m.lower() for m in note.mentions)
    assert any("LPTA" in m or "autorisation" in m for m in note.mentions)


def test_patrimonial_applicable():
    case = {
        "type_bien": "maison",
        "patrimoine_culturel": {"statut": "cite_du_patrimoine_de_quebec"},
    }
    note = analyze_patrimonial(case)
    assert note.statut == "applicable"
    assert any("patrimonial" in m.lower() or "désignation" in m.lower() for m in note.mentions)
    assert len(note.avertissements) > 0  # avertissement analyse requise


def test_patrimonial_not_applicable():
    case = {"type_bien": "unifamiliale"}
    note = analyze_patrimonial(case)
    assert note.statut == "non_applicable"


def test_rpa_applicable():
    case = {
        "type_bien": "rpa",
        "nb_unites": 80,
        "certification_msss": True,
    }
    note = analyze_rpa(case)
    assert note.statut == "applicable"
    assert any("MSSS" in m for m in note.mentions)
    assert any("achalandage" in m.lower() for m in note.mentions)


def test_dispatch_multiple_notes():
    case = {
        "type_bien": "terrain_agricole",
        "zone_agricole": {"en_zone_verte": True},
        "patrimoine_culturel": {"statut": "site_patrimonial"},
    }
    notes = analyze_specialized_property(case)
    types = {n.type_bien for n in notes}
    assert "terrain_agricole" in types
    assert "bien_patrimonial" in types


def test_specialized_mentions_for_prompt_indivise():
    case = {"type_bien": "copropriation_indivise", "convention_indivision": {"part_pct": 50}}
    lines = specialized_mentions_for_prompt(case)
    text = "\n".join(lines)
    assert "TYPES DE BIENS SPÉCIALISÉS" in text
    assert "COPROPRIATION_INDIVISE" in text or "indivise" in text.lower()
