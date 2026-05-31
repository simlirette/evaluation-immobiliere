"""engine/adjustments.py — Grille d'ajustements par comparable (T2.1).

Calcule les ajustements ligne par ligne pour chaque comparable :
  1. Date / conditions de marché
  2. Superficie habitable
  3. Superficie terrain
  4. Garage / stationnement
  5. État / condition
  6. Sous-sol fini
  7. Localisation

Chaque ligne indique son statut :
  "calcule"          — données disponibles, taux paramétré
  "a_valider"        — données disponibles mais taux par défaut (À valider par É.A.)
  "donnees_manquantes" — données comparables absentes, montant = 0

Taux par défaut : MEFQ 2025 / APCIQ / SCHL / barèmes OEAQ — tous "à valider" É.A.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


# ── Taux par défaut (paramétrables) ──────────────────────────────────────────

@dataclass
class AdjustmentRates:
    """Taux d'ajustement par caractéristique. Tous "à valider" sans données marché."""

    # Date/marché : % mensuel d'évolution (APCIQ Québec résidentiel ~0.3-0.5%/mois)
    taux_marche_mensuel_pct: float = 0.35

    # Superficie habitable : $/m² de différence
    taux_superficie_hab_par_m2: float = 1800.0

    # Superficie terrain : $/m² de différence
    taux_superficie_terrain_par_m2: float = 250.0

    # Garage/stationnement : $ par espace de différence
    montant_par_garage: float = 15_000.0

    # État : % du prix vendu par catégorie de différence
    #   catégories : excellent=5, bon=4, moyen=3, mauvais=2, très_mauvais=1
    taux_etat_pct_par_categorie: float = 4.0

    # Sous-sol fini : $/m² de superficie finie
    taux_sous_sol_par_m2: float = 350.0

    # Localisation : % du prix vendu (positif = sujet mieux situé)
    taux_localisation_pct: float = 0.0  # nécessite analyse É.A.

    source: str = "defaults_MEFQ_APCIQ_2025"


_ETAT_RANK: dict[str, int] = {
    "excellent": 5,
    "tres_bon": 4,
    "bon": 4,
    "moyen": 3,
    "mediocre": 2,
    "mauvais": 2,
    "tres_mauvais": 1,
}

_PI2_TO_M2 = 0.092903  # 1 pi² = 0.092903 m²


# ── Utilitaires ──────────────────────────────────────────────────────────────

def _to_m2(surface: object) -> float | None:
    """Convertit surface (dict {value, unit} ou float) en m²."""
    if isinstance(surface, (int, float)):
        return float(surface) if surface > 0 else None
    if isinstance(surface, dict):
        v = surface.get("value")
        u = str(surface.get("unit", "m2")).lower()
        if v is None or float(v) <= 0:
            return None
        v = float(v)
        if "pi" in u or "ft" in u or "sq" in u:
            return v * _PI2_TO_M2
        return v  # m²
    return None


def _parse_date(s: object) -> date | None:
    if not isinstance(s, str) or not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def _months_diff(d1: date, d2: date) -> float:
    """Différence en mois (d2 - d1), positif si d2 après d1."""
    return (d2.year - d1.year) * 12 + (d2.month - d1.month)


def _etat_rank(etat: object) -> int | None:
    if not isinstance(etat, str):
        return None
    return _ETAT_RANK.get(etat.lower().replace("-", "_").replace(" ", "_"))


# ── Ligne d'ajustement ────────────────────────────────────────────────────────

@dataclass
class AdjLine:
    caracteristique: str
    detail: str
    montant: float
    taux_info: str
    statut: str  # "calcule" | "a_valider" | "donnees_manquantes"

    def to_dict(self) -> dict:
        return {
            "caracteristique": self.caracteristique,
            "detail": self.detail,
            "montant": round(self.montant),
            "taux_info": self.taux_info,
            "statut": self.statut,
        }


@dataclass
class ComparableGrid:
    comparable_id: str
    source_id: str
    adresse: str
    prix_vendu: float
    ajustements: list[AdjLine] = field(default_factory=list)

    @property
    def total_ajustements(self) -> float:
        return sum(a.montant for a in self.ajustements)

    @property
    def total_brut_abs(self) -> float:
        return sum(abs(a.montant) for a in self.ajustements)

    @property
    def pct_total_brut(self) -> float:
        return round(self.total_brut_abs / self.prix_vendu * 100, 1) if self.prix_vendu else 0.0

    @property
    def prix_ajuste(self) -> float:
        return round(self.prix_vendu + self.total_ajustements, 0)

    @property
    def alerte_seuil_25pct(self) -> bool:
        return self.pct_total_brut > 25.0

    @property
    def statut(self) -> str:
        if all(a.statut == "calcule" for a in self.ajustements):
            return "grille_complete"
        if any(a.statut == "donnees_manquantes" for a in self.ajustements):
            return "grille_partielle"
        return "grille_a_valider"

    def to_dict(self) -> dict:
        return {
            "comparable_id": self.comparable_id,
            "source_id": self.source_id,
            "adresse": self.adresse,
            "prix_vendu": self.prix_vendu,
            "ajustements": [a.to_dict() for a in self.ajustements],
            "total_ajustements": round(self.total_ajustements),
            "pct_total_brut": self.pct_total_brut,
            "prix_ajuste": self.prix_ajuste,
            "statut": self.statut,
            "alerte_seuil_25pct": self.alerte_seuil_25pct,
        }


# ── Calcul des lignes par caractéristique ────────────────────────────────────

def _adj_date(
    comp: dict,
    date_reference: date,
    prix_vendu: float,
    rates: AdjustmentRates,
) -> AdjLine:
    date_vente = _parse_date(comp.get("date_vente"))
    if date_vente is None:
        return AdjLine("date_marche", "date_vente manquante", 0.0, "—", "donnees_manquantes")
    mois = _months_diff(date_vente, date_reference)
    montant = round(mois * (rates.taux_marche_mensuel_pct / 100) * prix_vendu, 0)
    detail = f"{mois:+.1f} mois ({date_vente} → {date_reference})"
    return AdjLine(
        "date_marche", detail, montant,
        f"{rates.taux_marche_mensuel_pct:.2f}%/mois",
        "a_valider",
    )


def _adj_superficie_hab(
    sujet_m2: float | None,
    comp: dict,
    rates: AdjustmentRates,
) -> AdjLine:
    comp_m2 = _to_m2(comp.get("surface"))
    if sujet_m2 is None or comp_m2 is None:
        return AdjLine("superficie_habitable", "surface manquante", 0.0, "—", "donnees_manquantes")
    diff = sujet_m2 - comp_m2
    montant = round(diff * rates.taux_superficie_hab_par_m2, 0)
    detail = f"sujet {sujet_m2:.0f} m² vs comp {comp_m2:.0f} m² (Δ {diff:+.0f} m²)"
    return AdjLine(
        "superficie_habitable", detail, montant,
        f"{rates.taux_superficie_hab_par_m2:,.0f} $/m²",
        "a_valider",
    )


def _adj_superficie_terrain(
    sujet_terrain: float | None,
    comp: dict,
    rates: AdjustmentRates,
) -> AdjLine:
    comp_terrain = _to_m2(comp.get("surface_terrain"))
    if sujet_terrain is None or comp_terrain is None:
        return AdjLine("superficie_terrain", "surface terrain manquante", 0.0, "—", "donnees_manquantes")
    diff = sujet_terrain - comp_terrain
    montant = round(diff * rates.taux_superficie_terrain_par_m2, 0)
    detail = f"sujet {sujet_terrain:.0f} m² vs comp {comp_terrain:.0f} m² (Δ {diff:+.0f} m²)"
    return AdjLine(
        "superficie_terrain", detail, montant,
        f"{rates.taux_superficie_terrain_par_m2:,.0f} $/m²",
        "a_valider",
    )


def _adj_garage(
    sujet_garages: int | None,
    comp: dict,
    rates: AdjustmentRates,
) -> AdjLine:
    for key in ("nb_garages", "nb_garage", "nb_stationnements", "nb_places_stationnement"):
        val = comp.get(key)
        if val is not None:
            comp_garages = int(val)
            break
    else:
        return AdjLine("garage_stationnement", "nb garages manquant", 0.0, "—", "donnees_manquantes")
    if sujet_garages is None:
        return AdjLine("garage_stationnement", "nb garages sujet manquant", 0.0, "—", "donnees_manquantes")
    diff = sujet_garages - comp_garages
    montant = round(diff * rates.montant_par_garage, 0)
    detail = f"sujet {sujet_garages} vs comp {comp_garages} (Δ {diff:+d} espace)"
    return AdjLine(
        "garage_stationnement", detail, montant,
        f"{rates.montant_par_garage:,.0f} $/espace",
        "a_valider",
    )


def _adj_etat(
    sujet_etat: str | None,
    comp: dict,
    prix_vendu: float,
    rates: AdjustmentRates,
) -> AdjLine:
    comp_etat_str = comp.get("etat") or comp.get("etat_batiment") or comp.get("condition")
    if not sujet_etat or not comp_etat_str:
        return AdjLine("etat_condition", "état manquant", 0.0, "—", "donnees_manquantes")
    sujet_rank = _etat_rank(sujet_etat)
    comp_rank = _etat_rank(comp_etat_str)
    if sujet_rank is None or comp_rank is None:
        return AdjLine("etat_condition", f"code état inconnu ({sujet_etat}/{comp_etat_str})", 0.0, "—", "donnees_manquantes")
    diff = sujet_rank - comp_rank
    montant = round(diff * (rates.taux_etat_pct_par_categorie / 100) * prix_vendu, 0)
    detail = f"sujet {sujet_etat}({sujet_rank}) vs comp {comp_etat_str}({comp_rank}) (Δ {diff:+d})"
    return AdjLine(
        "etat_condition", detail, montant,
        f"{rates.taux_etat_pct_par_categorie:.1f}%/catégorie",
        "a_valider",
    )


def _adj_sous_sol(
    sujet_sous_sol_m2: float | None,
    comp: dict,
    rates: AdjustmentRates,
) -> AdjLine:
    comp_ss = _to_m2(comp.get("sous_sol_fini_m2") or comp.get("surface_sous_sol_fini"))
    if sujet_sous_sol_m2 is None or comp_ss is None:
        return AdjLine("sous_sol_fini", "superficie sous-sol manquante", 0.0, "—", "donnees_manquantes")
    diff = sujet_sous_sol_m2 - comp_ss
    montant = round(diff * rates.taux_sous_sol_par_m2, 0)
    detail = f"sujet {sujet_sous_sol_m2:.0f} m² vs comp {comp_ss:.0f} m² (Δ {diff:+.0f} m²)"
    return AdjLine(
        "sous_sol_fini", detail, montant,
        f"{rates.taux_sous_sol_par_m2:,.0f} $/m²",
        "a_valider",
    )


def _adj_localisation(
    rates: AdjustmentRates,
    prix_vendu: float,
    comp: dict,
) -> AdjLine:
    pct = rates.taux_localisation_pct
    if pct == 0.0:
        return AdjLine(
            "localisation", "taux non paramétré (analyse É.A. requise)", 0.0,
            "0 $/analyse É.A.", "donnees_manquantes",
        )
    montant = round((pct / 100) * prix_vendu, 0)
    detail = f"{pct:+.2f}% du prix vendu"
    return AdjLine("localisation", detail, montant, f"{pct:+.2f}%", "a_valider")


# ── Grille complète pour un comparable ───────────────────────────────────────

def compute_adjustment_grid_one(
    sujet: dict,
    comp: dict,
    date_reference: date,
    rates: AdjustmentRates,
) -> ComparableGrid:
    prix_vendu = float(comp.get("prix_vente") or comp.get("sale_price") or 0)
    if prix_vendu <= 0:
        prix_vendu = 0.0

    sujet_m2    = _to_m2(sujet.get("surface"))
    sujet_terrain = _to_m2(sujet.get("surface_terrain"))
    sujet_garages = sujet.get("nb_garages") or sujet.get("nb_garage")
    sujet_garages = int(sujet_garages) if sujet_garages is not None else None
    sujet_etat  = sujet.get("etat") or sujet.get("etat_batiment") or sujet.get("condition")
    sujet_ss_m2 = _to_m2(sujet.get("sous_sol_fini_m2") or sujet.get("surface_sous_sol_fini"))

    lines = [
        _adj_date(comp, date_reference, prix_vendu, rates),
        _adj_superficie_hab(sujet_m2, comp, rates),
        _adj_superficie_terrain(sujet_terrain, comp, rates),
        _adj_garage(sujet_garages, comp, rates),
        _adj_etat(sujet_etat, comp, prix_vendu, rates),
        _adj_sous_sol(sujet_ss_m2, comp, rates),
        _adj_localisation(rates, prix_vendu, comp),
    ]

    return ComparableGrid(
        comparable_id=str(comp.get("comparable_id") or comp.get("source_id") or "?"),
        source_id=str(comp.get("source_id") or "?"),
        adresse=str(comp.get("adresse") or "—"),
        prix_vendu=prix_vendu,
        ajustements=lines,
    )


# ── Grille complète pour le dossier ──────────────────────────────────────────

def compute_adjustment_grid(
    case: dict,
    rates: AdjustmentRates | None = None,
) -> dict:
    """Calcule la grille d'ajustements pour tous les comparables du dossier.

    Returns dict avec :
      - grilles: list[ComparableGrid.to_dict()]
      - prix_ajustes: list[float] — pour la moyenne pondérée
      - valeur_indiquee: float — médiane des prix ajustés
      - fourchette: {min, max, ecart_pct}
      - nb_grilles_completes: int
      - rates_used: dict
      - avertissements: list[str]
    """
    if rates is None:
        rates = AdjustmentRates()

    date_ref_str = case.get("date_reference", "")
    date_ref = _parse_date(date_ref_str) or date.today()

    comparables = [c for c in case.get("comparables", []) if isinstance(c, dict)]
    if not comparables:
        return {
            "grilles": [],
            "prix_ajustes": [],
            "valeur_indiquee": 0.0,
            "fourchette": {"min": 0.0, "max": 0.0, "ecart_pct": 0.0},
            "nb_grilles_completes": 0,
            "rates_used": rates.__dict__,
            "avertissements": ["Aucun comparable disponible."],
        }

    grilles: list[ComparableGrid] = []
    for comp in comparables[:7]:  # max 7 comparables (MEFQ)
        g = compute_adjustment_grid_one(case, comp, date_ref, rates)
        grilles.append(g)

    prix_ajustes = [g.prix_ajuste for g in grilles if g.prix_vendu > 0]
    avertissements: list[str] = []

    if prix_ajustes:
        sorted_prix = sorted(prix_ajustes)
        n = len(sorted_prix)
        valeur_indiquee = sorted_prix[n // 2] if n % 2 else (sorted_prix[n // 2 - 1] + sorted_prix[n // 2]) / 2
        p_min = min(prix_ajustes)
        p_max = max(prix_ajustes)
        ecart_pct = round((p_max - p_min) / valeur_indiquee * 100, 1) if valeur_indiquee else 0.0
    else:
        valeur_indiquee = 0.0
        p_min = p_max = 0.0
        ecart_pct = 0.0

    # Avertissements MEFQ
    for g in grilles:
        if g.alerte_seuil_25pct:
            avertissements.append(
                f"{g.comparable_id}: ajustements bruts {g.pct_total_brut:.1f}% > 25% "
                "(seuil MEFQ — fiabilité réduite)"
            )
    nb_partielles = sum(1 for g in grilles if "partielle" in g.statut or "a_valider" in g.statut)
    if nb_partielles:
        avertissements.append(
            f"{nb_partielles}/{len(grilles)} grilles partielles — "
            "données comparables incomplètes, ajustements à valider par É.A."
        )

    return {
        "grilles": [g.to_dict() for g in grilles],
        "prix_ajustes": prix_ajustes,
        "valeur_indiquee": round(valeur_indiquee),
        "fourchette": {"min": round(p_min), "max": round(p_max), "ecart_pct": ecart_pct},
        "nb_grilles_completes": sum(1 for g in grilles if g.statut == "grille_complete"),
        "rates_used": rates.__dict__,
        "avertissements": avertissements,
    }
