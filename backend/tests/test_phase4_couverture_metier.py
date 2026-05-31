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
