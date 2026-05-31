"""engine/specialized_valuation.py — Types de biens spécialisés (T4.6).

Couvre les ajustements et mentions obligatoires pour :
  - Copropriété indivise (décote illiquidité + convention)
  - Agricole CPTAQ (contraintes zone verte, $/hectare)
  - Patrimonial (prime ou décote selon désignation)
  - RPA — résidence personnes âgées (composante immobilière vs achalandage)

Utilisé par valuation.py et runtime.py pour injecter les mentions
et ajustements spécifiques dans le rapport.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SpecializedNote:
    type_bien: str
    statut: str        # "applicable" | "non_applicable" | "a_verifier"
    mentions: list[str] = field(default_factory=list)
    ajustements: list[dict] = field(default_factory=list)
    avertissements: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type_bien": self.type_bien,
            "statut": self.statut,
            "mentions": self.mentions,
            "ajustements": self.ajustements,
            "avertissements": self.avertissements,
        }


# ── Copropriété indivise ──────────────────────────────────────────────────────

def analyze_copropriation_indivise(case: dict) -> SpecializedNote:
    """Analyse les contraintes de copropriété indivise.

    Décote d'illiquidité standard : 10-20% selon la convention et la part.
    """
    type_bien = str(case.get("type_bien", "")).lower()
    if "indivise" not in type_bien and "indivis" not in type_bien:
        if not case.get("copropriation_indivise") and not case.get("convention_indivision"):
            return SpecializedNote(type_bien=type_bien, statut="non_applicable")

    convention = case.get("convention_indivision") or {}
    part_pct = float(convention.get("part_pct", 50) if isinstance(convention, dict) else 50)
    decote_fournie = float((convention.get("decote_illiquidite_pct", 0) if isinstance(convention, dict) else 0))

    # Décote par défaut si non fournie
    if decote_fournie <= 0:
        # Décote typique OEAQ pour indivision : 10-20% selon part
        decote_pct = 15.0 if part_pct <= 50 else 10.0
        decote_source = "defaut_a_valider"
    else:
        decote_pct = decote_fournie
        decote_source = "fournie_convention"

    mentions = [
        "COPROPRIÉTÉ INDIVISE : évaluation de la part proportionnelle.",
        f"Part évaluée : {part_pct:.1f}%",
        f"Décote d'illiquidité : {decote_pct:.1f}% ({decote_source})",
        "La décote doit être justifiée par rapport aux ventes de parts similaires.",
        "Vérifier l'existence et les clauses de la convention d'indivision.",
        "Mention obligatoire : droits de préemption entre co-indivisaires (art. 1022 C.c.Q.).",
    ]
    ajustements = [
        {
            "caracteristique": "illiquidite_indivision",
            "montant_relatif_pct": -decote_pct,
            "taux_info": f"{decote_pct:.1f}% — décote illiquidité copropriété indivise",
            "statut": "a_valider" if decote_source == "defaut_a_valider" else "calcule",
        }
    ]
    avert = []
    if decote_source == "defaut_a_valider":
        avert.append(f"Décote d'illiquidité par défaut ({decote_pct:.1f}%) — à valider avec données marché de parts indivises.")

    return SpecializedNote(
        type_bien="copropriation_indivise",
        statut="applicable",
        mentions=mentions,
        ajustements=ajustements,
        avertissements=avert,
    )


# ── Terrain agricole / zone CPTAQ ─────────────────────────────────────────────

def analyze_agricole(case: dict) -> SpecializedNote:
    """Analyse les contraintes CPTAQ et l'approche $/hectare pour terrain agricole."""
    type_bien = str(case.get("type_bien", "")).lower()
    if "agric" not in type_bien and not case.get("zone_agricole"):
        return SpecializedNote(type_bien=type_bien, statut="non_applicable")

    zone_agricole = case.get("zone_agricole") or {}
    en_zone_verte = bool(zone_agricole.get("en_zone_verte") if isinstance(zone_agricole, dict) else False)
    type_zone = str(zone_agricole.get("type_zone", "") if isinstance(zone_agricole, dict) else "")

    surface_terrain = case.get("surface_terrain") or 0.0
    if isinstance(case.get("surface_terrain"), dict):
        surface_terrain = float(case["surface_terrain"].get("value", 0))
    surface_ha = float(surface_terrain) / 10000.0 if float(surface_terrain) > 0 else 0.0

    # Valeur $/hectare (si disponible)
    prix_par_ha = case.get("prix_par_hectare") or 0.0
    valeur_calculee = surface_ha * float(prix_par_ha) if surface_ha > 0 and float(prix_par_ha) > 0 else None

    mentions = [
        "TERRAIN AGRICOLE — analyse CPTAQ obligatoire.",
        f"Zone verte CPTAQ : {'OUI — restrictions importantes sur usage non agricole' if en_zone_verte else 'NON — vérifier tout de même'}",
    ]
    if type_zone:
        mentions.append(f"Type de zone : {type_zone}")
    if surface_ha > 0:
        mentions.append(f"Superficie : {surface_ha:.2f} ha ({float(surface_terrain):.0f} m²)")
    if valeur_calculee:
        mentions.append(f"Valeur indicative $/ha : {prix_par_ha} $/ha → {valeur_calculee:,.0f} $ total")
    mentions += [
        "L'approche comparative utilise le $/hectare comme unité de mesure.",
        "Vérifier les droits d'exploitation, les droits d'eau et les baux agricoles.",
        "La LPTA s'applique — décrire les restrictions dans le rapport.",
    ]
    if en_zone_verte:
        mentions.append("Mention obligatoire : usage résidentiel/commercial soumis à autorisation CPTAQ.")

    avert = []
    if not float(prix_par_ha):
        avert.append("Prix par hectare non fourni — comparables agricoles requis pour valider la valeur.")

    return SpecializedNote(
        type_bien="terrain_agricole",
        statut="applicable",
        mentions=mentions,
        ajustements=[],
        avertissements=avert,
    )


# ── Bien patrimonial ──────────────────────────────────────────────────────────

def analyze_patrimonial(case: dict) -> SpecializedNote:
    """Analyse l'impact de la désignation patrimoniale sur la valeur."""
    type_bien = str(case.get("type_bien", "")).lower()
    patrimoine = case.get("patrimoine_culturel") or {}
    if not isinstance(patrimoine, dict) or not patrimoine:
        return SpecializedNote(type_bien=type_bien, statut="non_applicable")

    statut_pat = str(patrimoine.get("statut") or patrimoine.get("type_designation", ""))
    if not statut_pat:
        return SpecializedNote(type_bien=type_bien, statut="non_applicable")

    # Impact sur la valeur : prime ou décote selon le contexte
    # Prime : cachet historique attire les acheteurs
    # Décote : restrictions sur modifications réduisent la liquidité
    impact_type = patrimoine.get("impact_valeur", "a_analyser")
    impact_pct = float(patrimoine.get("impact_pct", 0))

    mentions = [
        f"BIEN PATRIMONIAL — désignation : {statut_pat}",
        "Les restrictions de modification affectent la liquidité et potentiellement la valeur.",
        "Mentionner explicitement la désignation dans les hypothèses et conditions limitatives.",
        "Comparer avec des ventes de biens patrimoniaux similaires (si disponibles).",
        "Vérifier les subventions disponibles (PCNB, programme municipal patrimoine).",
    ]

    ajustements = []
    if impact_pct != 0:
        ajustements.append({
            "caracteristique": "designation_patrimoniale",
            "montant_relatif_pct": impact_pct,
            "taux_info": f"{impact_pct:+.1f}% — impact désignation {statut_pat}",
            "statut": "a_valider",
        })
    else:
        mentions.append("Impact sur la valeur : à analyser par l'É.A. selon le marché local.")

    avert = []
    if impact_type == "a_analyser" or impact_pct == 0:
        avert.append("Impact de la désignation patrimoniale non quantifié — analyse É.A. requise.")

    return SpecializedNote(
        type_bien="bien_patrimonial",
        statut="applicable",
        mentions=mentions,
        ajustements=ajustements,
        avertissements=avert,
    )


# ── RPA — Résidence personnes âgées ──────────────────────────────────────────

def analyze_rpa(case: dict) -> SpecializedNote:
    """Analyse les contraintes RPA : séparation immobilière vs achalandage."""
    type_bien = str(case.get("type_bien", "")).lower()
    if "rpa" not in type_bien and "personnes_agees" not in type_bien and "residence_agees" not in type_bien:
        return SpecializedNote(type_bien=type_bien, statut="non_applicable")

    certif_msss = case.get("certification_msss", False)
    nb_unites = _safe_int(case.get("nb_unites") or case.get("nb_logements"))
    composante_immobiliere_pct = float(case.get("composante_immobiliere_pct", 0))

    mentions = [
        "RPA — RÉSIDENCE POUR PERSONNES ÂGÉES : analyse spécialisée obligatoire.",
        "Séparer la composante immobilière de l'achalandage (going concern).",
        f"Certification MSSS : {'Oui' if certif_msss else 'Non / À vérifier'}",
    ]
    if nb_unites:
        mentions.append(f"Nombre d'unités : {nb_unites}")
    if composante_immobiliere_pct > 0:
        mentions.append(f"Composante immobilière retenue : {composante_immobiliere_pct:.0f}%")
    else:
        mentions.append("Composante immobilière vs achalandage : à déterminer par l'É.A.")
    mentions += [
        "Analyser les revenus par unité, taux d'occupation, services inclus.",
        "Vérifier la conformité aux normes MSSS si certifié.",
        "Approche revenu prépondérante (TGA spécifique RPA de marché).",
    ]

    avert = ["RPA : expertise spécialisée recommandée — compétence É.A. à déclarer."]
    if not certif_msss:
        avert.append("Statut certification MSSS non confirmé — vérifier avant de conclure.")

    return SpecializedNote(
        type_bien="rpa",
        statut="applicable",
        mentions=mentions,
        ajustements=[],
        avertissements=avert,
    )


def _safe_int(value: object) -> int | None:
    try:
        v = int(float(str(value)))
        return v if v > 0 else None
    except (TypeError, ValueError):
        return None


# ── Dispatch principal ────────────────────────────────────────────────────────

_ANALYZERS = [
    analyze_copropriation_indivise,
    analyze_agricole,
    analyze_patrimonial,
    analyze_rpa,
]


def analyze_specialized_property(case: dict) -> list[SpecializedNote]:
    """Retourne les notes spécialisées applicables au dossier."""
    notes = []
    for analyzer in _ANALYZERS:
        try:
            note = analyzer(case)
            if note.statut == "applicable":
                notes.append(note)
        except Exception:
            pass
    return notes


def specialized_mentions_for_prompt(case: dict) -> list[str]:
    """Retourne les mentions spécialisées à injecter dans le prompt rapport."""
    notes = analyze_specialized_property(case)
    if not notes:
        return []
    lines: list[str] = ["", "TYPES DE BIENS SPÉCIALISÉS — MENTIONS OBLIGATOIRES :"]
    for note in notes:
        lines.append(f"  [{note.type_bien.upper()}]")
        for m in note.mentions[:5]:
            lines.append(f"    - {m}")
        for a in note.avertissements:
            lines.append(f"    ⚠ {a}")
    return lines
