"""engine/amu.py — Analyse du Meilleur Usage (AMU) déterministe (T2.3).

Évalue les 4 critères OEAQ/MEFQ à partir des données structurées du dossier.
Remplace le tampon runtime.py (conformite_zonage=True en dur, 4 critères=True).

Critères :
  C1 — Légalement permis   : zonage, zone agricole, patrimoine, zone inondable
  C2 — Physiquement possible : terrain, inondable, contraintes physiques
  C3 — Financièrement faisable : signaux marché (conditionnel si absent)
  C4 — Maximalement productif : conclusion après C1-C3

Résultat par critère :
  resultat   : True | False | None (données manquantes)
  confiance  : "eleve" | "partielle" | "donnees_manquantes"
  justification : texte court
  signaux    : list[str] de faits observés

Principe : jamais d'invention. Si les données sont absentes → None + "données manquantes".
"""
from __future__ import annotations

from dataclasses import dataclass, field


# ── Types de bien résidentiels courants ───────────────────────────────────────

_TYPES_RESIDENTIELS = {
    "unifamiliale", "unifamilial", "residentiel_unifamilial",
    "maison", "cottage", "bungalow",
    "condo", "condominium",
    "duplex", "triplex", "quadruplex",
    "residentiel_multifamilial", "multifamilial",
    "semi_detache",
}
_TYPES_COMMERCIAUX = {"commercial", "bureau", "magasin", "centre_commercial"}
_TYPES_INDUSTRIELS = {"industriel", "entrepot", "manufacture"}
_TYPES_TERRAIN    = {"terrain", "terrain_vacant", "lot", "terrain_agricole", "terrain_developpement"}


def _type_category(type_bien: str) -> str:
    t = type_bien.lower().replace("-", "_").replace(" ", "_")
    if t in _TYPES_RESIDENTIELS:
        return "residentiel"
    if t in _TYPES_COMMERCIAUX:
        return "commercial"
    if t in _TYPES_INDUSTRIELS:
        return "industriel"
    if t in _TYPES_TERRAIN:
        return "terrain"
    return "autre"


# ── Critère 1 — Légalement permis ─────────────────────────────────────────────

def _eval_legalement_permis(case: dict) -> dict:
    """Évalue si l'usage actuel est légalement permis selon les données réelles."""
    type_bien = str(case.get("type_bien", "")).lower()
    signaux: list[str] = []
    restrictions: list[str] = []

    # Zone agricole (CPTAQ)
    zone_agricole = case.get("zone_agricole") or {}
    if isinstance(zone_agricole, dict) and zone_agricole:
        en_zone_verte = zone_agricole.get("en_zone_verte") or zone_agricole.get("zone_verte")
        if en_zone_verte:
            type_zone = zone_agricole.get("type_zone", "zone verte")
            signaux.append(f"Bien en zone agricole protégée (CPTAQ) : {type_zone}")
            cat = _type_category(type_bien)
            if cat in ("residentiel", "commercial", "industriel"):
                restrictions.append(
                    "Zone verte CPTAQ : usage non agricole soumis à autorisation — "
                    "vérifier décision CPTAQ avant de conclure sur l'UMPP."
                )
        else:
            signaux.append("Zone agricole vérifiée : bien hors zone verte CPTAQ.")

    # Patrimoine culturel
    patrimoine = case.get("patrimoine_culturel") or {}
    if isinstance(patrimoine, dict) and patrimoine:
        statut_pat = patrimoine.get("statut") or patrimoine.get("type_designation", "")
        if statut_pat:
            signaux.append(f"Bien répertorié au patrimoine culturel : {statut_pat}")
            restrictions.append(
                f"Désignation patrimoniale ({statut_pat}) peut restreindre les usages "
                "et les modifications — vérifier règlement municipal."
            )

    # Zone inondable (impact sur droit de construire)
    zone_inond = case.get("zone_inondable") or {}
    if isinstance(zone_inond, dict) and zone_inond:
        en_zone = zone_inond.get("en_zone_inondable") or zone_inond.get("en_zone")
        risque = str(zone_inond.get("risque", "") or "").lower()
        if en_zone:
            if risque in ("fort", "tres_fort", "high", "very_high"):
                signaux.append(f"Zone inondable : risque {risque}")
                restrictions.append(
                    f"Zone inondable à risque {risque} : construction résidentielle "
                    "possiblement interdite ou très encadrée."
                )
            else:
                signaux.append(f"Zone inondable à risque {risque or 'non précisé'} — vérifier règlement.")

    # Zonage urbanisme — vérification directe des usages autorisés
    zu = case.get("zonage_urbanisme") or {}
    if isinstance(zu, dict) and zu:
        usages_auto = zu.get("usages_autorises") or zu.get("usages") or []
        usage_principal = str(zu.get("USAGE_PRINCIPAL") or zu.get("usage_principal") or "")
        zone_code = zu.get("ZONE") or zu.get("zone") or ""
        if zone_code:
            signaux.append(f"Zonage municipal : {zone_code} — {usage_principal}")
        if usages_auto and isinstance(usages_auto, list):
            cat = _type_category(type_bien)
            match = any(
                cat in str(u).lower() or type_bien in str(u).lower()
                for u in usages_auto
            )
            if match:
                signaux.append(f"Usage {type_bien} confirmé dans les usages autorisés de la zone.")
            else:
                signaux.append(f"Usage {type_bien} non explicitement dans usages autorisés : {usages_auto[:3]}")
                restrictions.append(
                    f"L'usage {type_bien} n'est pas explicitement autorisé dans la zone {zone_code} "
                    "selon les données disponibles."
                )

    if not signaux and not zone_agricole and not patrimoine and not zu:
        return {
            "resultat": None,
            "confiance": "donnees_manquantes",
            "justification": "Aucune donnée de zonage disponible — critère non évaluable.",
            "signaux": [],
        }

    if restrictions:
        return {
            "resultat": False,
            "confiance": "partielle" if zone_agricole or zu else "donnees_manquantes",
            "justification": " ".join(restrictions[:2]),
            "signaux": signaux,
        }

    return {
        "resultat": True,
        "confiance": "eleve" if (zone_agricole or zu) else "partielle",
        "justification": (
            "Aucune restriction légale identifiée dans les données disponibles."
            if signaux else "Données de zonage partielles."
        ),
        "signaux": signaux,
    }


# ── Critère 2 — Physiquement possible ────────────────────────────────────────

def _eval_physiquement_possible(case: dict) -> dict:
    """Évalue si l'usage actuel est physiquement possible."""
    type_bien = str(case.get("type_bien", "")).lower()
    signaux: list[str] = []
    contraintes: list[str] = []

    # Zone inondable
    zone_inond = case.get("zone_inondable") or {}
    if isinstance(zone_inond, dict) and zone_inond:
        en_zone = zone_inond.get("en_zone_inondable") or zone_inond.get("en_zone")
        risque = str(zone_inond.get("risque", "") or "").lower()
        if en_zone and risque in ("fort", "tres_fort"):
            contraintes.append(f"Zone inondable risque {risque} : compatibilité physique limitée.")
            signaux.append(f"Zone inondable : risque {risque}")
        elif en_zone:
            signaux.append(f"Zone inondable risque {risque or 'non précisé'} — construction possible sous conditions.")

    # Superficie terrain
    surface_terrain = case.get("surface_terrain")
    if surface_terrain:
        sf = float(surface_terrain) if not isinstance(surface_terrain, dict) else 0.0
        if isinstance(surface_terrain, dict):
            sf = float(surface_terrain.get("value", 0))
        cat = _type_category(type_bien)
        if sf > 0:
            signaux.append(f"Superficie terrain : {sf:.0f} m²")
            if cat == "residentiel" and sf < 100:
                contraintes.append(f"Superficie terrain ({sf:.0f} m²) très réduite pour usage résidentiel.")
            elif cat == "commercial" and sf < 200:
                signaux.append(f"Superficie terrain limitée pour usage commercial.")

    # Services / nuisances (proxy)
    nuisances = case.get("nuisances_environnementales") or {}
    if isinstance(nuisances, dict) and nuisances:
        score_n = nuisances.get("score_nuisances", 0)
        if score_n and int(score_n) >= 3:
            signaux.append(f"Score nuisances environnementales élevé : {score_n}/4")

    if not signaux and not surface_terrain and not zone_inond:
        return {
            "resultat": None,
            "confiance": "donnees_manquantes",
            "justification": "Aucune donnée physique disponible — critère non évaluable.",
            "signaux": [],
        }

    if contraintes:
        return {
            "resultat": False,
            "confiance": "partielle",
            "justification": " ".join(contraintes[:2]),
            "signaux": signaux,
        }

    return {
        "resultat": True,
        "confiance": "partielle" if not surface_terrain and not zone_inond else "eleve",
        "justification": "Caractéristiques physiques compatibles avec l'usage.",
        "signaux": signaux,
    }


# ── Critère 3 — Financièrement faisable ──────────────────────────────────────

def _eval_financierement_faisable(case: dict) -> dict:
    """Évalue la faisabilité financière à partir des signaux de marché."""
    signaux: list[str] = []

    # Score de marché
    score_m = case.get("score_marche") or {}
    if isinstance(score_m, dict) and score_m:
        sm = score_m.get("score_marche")
        tension = score_m.get("tension_locative", "")
        if sm is not None:
            signaux.append(f"Score marché : {sm:.1f}/10")
            if float(sm) < 4.0:
                return {
                    "resultat": False,
                    "confiance": "partielle",
                    "justification": f"Score marché faible ({sm:.1f}/10) — faisabilité financière réduite.",
                    "signaux": signaux,
                }

    # Marché immobilier
    marche = case.get("marche_immobilier") or {}
    if isinstance(marche, dict) and marche:
        months_supply = marche.get("mois_inventaire") or marche.get("months_supply")
        if months_supply:
            msi = float(months_supply)
            signaux.append(f"Inventaire marché : {msi:.1f} mois")
            if msi > 9:
                signaux.append("Marché acheteur (inventaire élevé).")
            elif msi < 3:
                signaux.append("Marché vendeur (faible inventaire).")

    # Valeur indicative comme proxy de demande
    vi = case.get("valeur_indicative") or {}
    if isinstance(vi, dict) and vi.get("valeur_indicative_synthese"):
        signaux.append("Valeur indicative disponible — demande marché implicite.")

    if not signaux:
        return {
            "resultat": None,
            "confiance": "donnees_manquantes",
            "justification": (
                "Aucune donnée de marché disponible. "
                "Faisabilité financière supposée conditionnellement (usage standard)."
            ),
            "signaux": [],
        }

    return {
        "resultat": True,
        "confiance": "partielle",
        "justification": "Signaux marché disponibles — usage financièrement faisable.",
        "signaux": signaux,
    }


# ── Critère 4 — Maximalement productif ──────────────────────────────────────

def _eval_maximalement_productif(
    case: dict,
    c1: dict,
    c2: dict,
    c3: dict,
) -> dict:
    """Conclusion : usage actuel = UMPP si C1+C2+C3 toutes True ou None."""
    type_bien = str(case.get("type_bien", "inconnu")).lower()

    c1_ok = c1["resultat"] is not False
    c2_ok = c2["resultat"] is not False
    c3_ok = c3["resultat"] is not False
    tous_ok = c1_ok and c2_ok and c3_ok

    if tous_ok:
        return {
            "resultat": True,
            "confiance": "eleve" if all(
                x["confiance"] == "eleve" for x in [c1, c2, c3]
            ) else "partielle",
            "justification": (
                f"L'usage actuel ({type_bien}) satisfait les 3 critères préalables — "
                "UMPP = usage actuel."
            ),
            "signaux": [],
        }

    contraintes = [
        msg
        for critere, msg in [
            (c1, f"C1 non satisfait : {c1['justification']}"),
            (c2, f"C2 non satisfait : {c2['justification']}"),
            (c3, f"C3 non satisfait : {c3['justification']}"),
        ]
        if critere["resultat"] is False
    ]
    return {
        "resultat": False,
        "confiance": "partielle",
        "justification": " | ".join(contraintes) if contraintes else "Critères non entièrement satisfaits.",
        "signaux": [],
    }


# ── Point d'entrée principal ──────────────────────────────────────────────────

def evaluate_amu(case: dict) -> dict:
    """Évalue l'AMU et retourne le payload umpp_conclusion.json.

    Priorité : données réelles > conclusion conditionnelle > défaut neutre.
    Ne retourne jamais conformite_zonage=True si les données indiquent le contraire.
    """
    type_bien = str(case.get("type_bien", "inconnu")).lower()
    zone = str(case.get("zone", "")).upper()

    # Normalisation type → catégorie
    usage_map = {
        "residentiel_unifamilial": "residentiel_unifamilial",
        "unifamilial": "residentiel_unifamilial",
        "unifamiliale": "residentiel_unifamilial",
        "maison": "residentiel_unifamilial",
        "condo": "residentiel_condo",
        "duplex": "residentiel_multifamilial",
        "triplex": "residentiel_multifamilial",
        "quadruplex": "residentiel_multifamilial",
        "commercial": "commercial",
        "industriel": "industriel",
        "terrain": "terrain_vacant",
        "terrain_vacant": "terrain_vacant",
    }
    usage_retenu = usage_map.get(type_bien, type_bien or "inconnu")

    c1 = _eval_legalement_permis(case)
    c2 = _eval_physiquement_possible(case)
    c3 = _eval_financierement_faisable(case)
    c4 = _eval_maximalement_productif(case, c1, c2, c3)

    # conformite_zonage : True seulement si C1 explicitement True
    conformite_zonage: bool | None
    if c1["resultat"] is True:
        conformite_zonage = True
    elif c1["resultat"] is False:
        conformite_zonage = False
    else:
        conformite_zonage = None  # données manquantes

    umpp_differe = c4["resultat"] is False
    if umpp_differe:
        conclusion = (
            f"Des contraintes identifiées (voir critères) suggèrent que l'usage actuel "
            f"({type_bien}) pourrait ne pas constituer l'UMPP. "
            "Analyse approfondie requise par l'É.A."
        )
    else:
        conclusion = (
            f"L'usage actuel ({type_bien}) constitue le meilleur usage et le plus "
            f"profitable (UMPP) selon les données disponibles."
        )

    # Avertissements transversaux
    avertissements: list[str] = []
    nb_manquants = sum(
        1 for c in [c1, c2, c3] if c["confiance"] == "donnees_manquantes"
    )
    if nb_manquants > 0:
        avertissements.append(
            f"{nb_manquants}/3 critères avec données manquantes — "
            "conclusion conditionnelle, à valider avec données complètes."
        )
    if conformite_zonage is None:
        avertissements.append("Données de zonage absentes — conformite_zonage non déterminée.")

    # Confiance globale
    confiances = [c["confiance"] for c in [c1, c2, c3]]
    if all(c == "eleve" for c in confiances):
        confidence = 0.90
    elif nb_manquants >= 2:
        confidence = 0.50
    else:
        confidence = 0.70

    return {
        "umpp": {
            "usage_retenu": usage_retenu,
            "usage_actuel": type_bien,
            "zone": zone,
            "conformite_zonage": conformite_zonage,
            "criteres": {
                "legalement_permis": c1,
                "physiquement_possible": c2,
                "financierement_faisable": c3,
                "maximalement_productif": c4,
            },
            "umpp_differe_usage_actuel": umpp_differe,
            "conclusion": conclusion,
            "avertissements": avertissements,
            "methodologie": "deterministe_v1",
        },
        "confidence": confidence,
    }
