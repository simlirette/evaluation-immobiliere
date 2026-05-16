"""
data_enrichment.py — enrichissement du case depuis sources données externes.

Sources actives V0 :
  - SCHL marché locatif  : StatCan WDS API, table 34-10-0133-01 (cache 24 h)
  - Rôle municipal Mtl   : CSV MAMH (~72 MB, si data_cache/role_mtl.csv présent)
  - Rôle municipal XML   : MAMH XML (Qc/Laval/Longueuil/Gatineau/Sherbrooke)
  - Zonage urbanisme     : GeoJSON open data + Nominatim geocoding + PiP lookup

Tout est non-bloquant : une exception n'interrompt jamais le pipeline.
"""
from __future__ import annotations

import csv
import json
import logging
import math
import time
import unicodedata
from pathlib import Path
from typing import Any

logger = logging.getLogger("data_enrichment")

_CACHE_TTL = 86_400  # 24 h
_HTTP_TIMEOUT = 8.0
_WDS_BASE = "https://www150.statcan.gc.ca/t1/wds/rest/"
_SCHL_TABLE = 3410013301  # CANSIM 34-10-0133-01 : loyers moyens CMHC


# ── Helpers ───────────────────────────────────────────────────────────────────

def _norm(text: str) -> str:
    """Lowercase + remove accents + strip."""
    nfkd = unicodedata.normalize("NFKD", text.lower().strip())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _read_cache(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(d, dict) and time.time() - d.get("_ts", 0) < _CACHE_TTL:
            return d
    except Exception:
        pass
    return None


def _write_cache(path: Path, data: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


# ── City detection ────────────────────────────────────────────────────────────

# Keyword → SCHL city code  (subset relevant to QC V0)
_CITY_KEYWORDS: list[tuple[str, str]] = [
    ("saguenay", "saguenay"),
    ("jonquiere", "saguenay"),
    ("chicoutimi", "saguenay"),
    ("drummondville", "drummondville"),
    ("sherbrooke", "sherbrooke"),
    ("trois-riviere", "trois-rivieres"),
    ("trois riviere", "trois-rivieres"),
    ("gatineau", "gatineau"),
    ("hull", "gatineau"),
    ("aylmer", "gatineau"),
    ("quebec", "quebec"),
    ("sainte-foy", "quebec"),
    ("levis", "quebec"),
    ("beauport", "quebec"),
    ("longueuil", "montreal"),
    ("laval", "montreal"),
    ("brossard", "montreal"),
    ("saint-lambert", "montreal"),
    ("westmount", "montreal"),
    ("outremont", "montreal"),
    ("montreal", "montreal"),
    ("mtl", "montreal"),
]

# SCHL city code → StatCan GEO label (table 34-10-0133-01)
_SCHL_TO_STATCAN_GEO: dict[str, str] = {
    "montreal": "Montréal, Quebec",
    "quebec": "Québec, Quebec",
    "gatineau": "Ottawa - Gatineau, Quebec part, Quebec",
    "sherbrooke": "Sherbrooke, Quebec",
    "saguenay": "Saguenay, Quebec",
    "trois-rivieres": "Trois-Rivières, Quebec",
    "drummondville": "Drummondville, Quebec",
}

_SCHL_TO_DISPLAY: dict[str, str] = {
    "montreal": "Montréal",
    "quebec": "Québec",
    "gatineau": "Gatineau",
    "sherbrooke": "Sherbrooke",
    "saguenay": "Saguenay",
    "trois-rivieres": "Trois-Rivières",
    "drummondville": "Drummondville",
}

# ── Taux d'inoccupation SCHL (StatCan 34-10-0131-01) ─────────────────────────
_VACANCE_TABLE = 3410013101  # 34-10-0131-01 : Rental vacancy rates (October survey)

# Same GEO labels as 34-10-0133-01 (same SCHL survey universe)
_VACANCE_UNIT_SEARCHES: dict[str, list[str]] = {
    "total":    ["total"],
    "bachelor": ["bachelor", "studio"],
    "1ch":      ["1 bedroom", "1 chambre"],
    "2ch":      ["2 bedroom", "2 chambre"],
    "3ch_plus": ["3 bedroom", "3 chambre", "3+"],
}

# ── Taux Bank of Canada (Valet API) ──────────────────────────────────────────
_BOC_VALET_BASE = "https://www.bankofcanada.ca/valet/observations"
_BOC_TTL = 86_400  # 24 h (taux changent peu souvent)

# Series IDs → field key  (Bank of Canada Valet series codes)
_BOC_SERIES: dict[str, str] = {
    "CAOVRNIGH":    "taux_directeur_pct",        # Overnight rate (taux directeur)
    "V80691311":    "taux_preferentiel_pct",      # Prime business loan rate
    "V122495":      "taux_hypo_5ans_conv_pct",    # 5-year conventional mortgage
    "V122496":      "taux_hypo_1an_pct",          # 1-year conventional mortgage
}

# ── Proximité services (OpenStreetMap Overpass API) ──────────────────────────
_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_OVERPASS_TTL = 7 * 86_400  # 7 jours (OSM change peu)

# Radius in metres for each amenity category
_OVERPASS_QUERIES: list[tuple[str, int, str]] = [
    # (field_key,            radius_m, OSM filter)
    ("ecoles_1km",            1000, '["amenity"~"school|college|university"]'),
    ("arrets_transport_500m",  500, '["public_transport"="stop_position"]["name"]'),
    ("epiceries_500m",         500, '["shop"~"supermarket|grocery"]'),
    ("parcs_1km",             1000, '["leisure"~"park|garden"]'),
    ("hopitaux_2km",          2000, '["amenity"~"hospital|clinic"]'),
    ("pharmacies_500m",        500, '["amenity"="pharmacy"]'),
]

# ── Enseignement post-secondaire (OSM Overpass) ───────────────────────────────
_POSTSEC_TTL = 30 * 86_400  # 30 jours (établissements stables)
_POSTSEC_RADIUS_CEGEP = 5_000     # 5 km pour CÉGEP/college
_POSTSEC_RADIUS_UNIV  = 10_000    # 10 km pour université

# ── Nuisances environnementales (OSM Overpass) ───────────────────────────────
_NUISANCES_TTL = 30 * 86_400  # 30 jours (infra stable)

# (field_key, radius_m, overpass_filter) — count queries
_NUISANCES_QUERIES: list[tuple[str, int, str]] = [
    ("aeroports_10km",         10_000, '["aeroway"~"aerodrome|airport"]'),
    ("voies_ferrees_500m",        500, '["railway"="rail"]'),
    ("zones_industrielles_1km", 1_000, '["landuse"="industrial"]'),
    ("carrieres_2km",           2_000, '["landuse"~"quarry|landfill"]'),
]

# ── Données climatiques historiques (Open-Meteo archive API) ─────────────────
_CLIMAT_BASE = "https://archive-api.open-meteo.com/v1/archive"
_CLIMAT_TTL = 365 * 86_400  # 1 an (données historiques stables)
_CLIMAT_YEAR = 2023           # année de référence (complète, stable)

# ── Proximité axes routiers (OSM Overpass) ────────────────────────────────────
# Reuses _OVERPASS_URL and _OVERPASS_TTL from services section above.
# highway values ordered from most to least impactful for real estate.
_ROUTE_TYPES: list[tuple[str, str]] = [
    # (field_key,            OSM highway= value)
    ("autoroute_km",         "motorway"),
    ("route_nationale_km",   "trunk"),
    ("artere_km",            "primary"),
]
_ROUTES_SEARCH_RADIUS_M = 15_000  # 15 km max search radius

# ── Indice d'abordabilité (calcul interne) ────────────────────────────────────
# Seuils standards (SCHL / CMHC) pour l'abordabilité du logement
_ABORD_SEUIL_ABORDABLE = 30.0   # < 30 % du revenu brut → abordable
_ABORD_SEUIL_LIMITE    = 40.0   # 30–40 % → limite
# > 40 % → non abordable
_ABORD_AMORT_MOIS = 300         # 25 ans × 12 mois
_ABORD_MISE_DE_FONDS = 0.20     # 20 % de mise de fonds

# ── Score marché synthétique (calcul interne) ─────────────────────────────────
# Seuils pour attribution des points par indicateur
_MARCHE_INOCCUPATION_TENDU  = 3.0    # % : taux inoccupation locative tendu
_MARCHE_INOCCUPATION_NORMAL = 5.0    # % : taux normal
_MARCHE_NHPI_FORT            = 3.0   # % : croissance prix neuf forte
_MARCHE_CHOMAGE_BAS          = 5.0   # % : chômage faible
_MARCHE_CHOMAGE_MOYEN        = 7.0   # % : chômage modéré
_MARCHE_POP_FORTE            = 1.0   # % : croissance démo forte
_MARCHE_CRIME_BAS            = 4000  # /100k : seuil criminalité faible QC

# ── Taux de capitalisation / rendement locatif (calcul interne) ───────────────
_CAPRATE_FRAIS_OPERATION = 0.35   # 35 % des revenus bruts (taxes + assurance + entretien)
_CAPRATE_EXCELLENT = 8.0          # % : taux cap brut excellent
_CAPRATE_BON       = 5.0          # % : bon rendement
_CAPRATE_FAIBLE    = 3.0          # % : faible mais acceptable (marché tendu QC)

# ── Score composite d'investissement (calcul interne) ─────────────────────────
# Poids des trois composantes (total = 1.0)
_INVEST_POIDS_MARCHE      = 0.40   # score_marche (B31) — dynamique du marché
_INVEST_POIDS_RENDEMENT   = 0.35   # rendement_locatif (B32) — rentabilité immédiate
_INVEST_POIDS_ABORDABILITE = 0.25  # indice_abordabilite (B30) — pression demand/abord.

# Seuils recommandation (sur 10)
_INVEST_SEUIL_FORT   = 7.0   # ≥ 7 → "fort potentiel"
_INVEST_SEUIL_MODERE = 5.0   # ≥ 5 → "potentiel modéré"
_INVEST_SEUIL_FAIBLE = 3.0   # ≥ 3 → "potentiel faible"
                              # < 3 → "déconseillé"

# ── Profil fiscal municipal (taux de taxation résidentiel) ────────────────────
# Taux exprimé en % de la valeur d'évaluation municipale (ex.: 0.701 % = 7,01 $/1 000 $)
# Sources : budgets municipaux 2023-2024 (taux ordinaire, premier palier)
_TAXES_TAUX_PCT: dict[str, float] = {
    "montreal":       0.701,  # Montréal 2024 (taux résidentiel 1er palier)
    "quebec":         1.008,  # Québec 2024
    "laval":          0.614,  # Laval 2024
    "longueuil":      0.832,  # Longueuil 2024
    "gatineau":       1.087,  # Gatineau 2024
    "sherbrooke":     1.098,  # Sherbrooke 2024
    "saguenay":       1.290,  # Saguenay 2024
    "trois_rivieres": 1.198,  # Trois-Rivières 2024
}
_TAXES_MOYENNE_QC_PCT = 0.95   # Moyenne provinciale QC estimée (toutes municipalités)

# ── Coûts de possession totaux (calcul interne) ───────────────────────────────
_POSSESSION_ENTRETIEN_PCT  = 1.0   # % valeur/an : entretien courant (norme SCHL/APCHQ)
_POSSESSION_ASSURANCE_PCT  = 0.35  # % valeur/an : assurance habitation (estimation QC)
_POSSESSION_SEUIL_ELEVE    = 40.0  # % revenu : seuil coûts élevés (SCHL)
_POSSESSION_SEUIL_MODERE   = 30.0  # % revenu : seuil modéré

# ── Ratio prix/loyer (calcul interne) ─────────────────────────────────────────
# Seuils standards (marché nord-américain, SCHL/Economist)
_PLR_FAVEUR_ACHAT   = 15.0  # ratio < 15 → avantage à l'achat
_PLR_EQUILIBRE      = 20.0  # 15-20 → marché équilibré
_PLR_FAVEUR_LOCATION = 25.0  # 20-25 → légère faveur location
                              # > 25 → forte faveur location (marché très cher)

# ── Analyse de vieillissement du bâtiment (calcul interne) ───────────────────
_VETUSTE_VIE_UTILE         = 80   # ans : vie utile standard résidentiel (SCHL)
_VETUSTE_DEPRECIATION_MAX  = 80.0 # % : dépréciation physique maximale retenue
_VETUSTE_SEUIL_NEUF        = 10   # < 10 ans = neuf
_VETUSTE_SEUIL_RECENT      = 20   # 10-20 ans = récent
_VETUSTE_SEUIL_MOYEN       = 40   # 20-40 ans = mi-vie
_VETUSTE_SEUIL_VIEUX       = 60   # 40-60 ans = vieux (> 60 = très vieux)
_VETUSTE_RENOVATION_ANS    = 25   # seuil : rénovation majeure généralement requise
_ANNEE_REFERENCE           = 2025 # année de calcul (fixe, reproductible)

# ── Statistiques criminelles par CMA (StatCan 35-10-0078-01) ─────────────────
_CRIME_TABLE = 3510007801  # 35-10-0078-01 : Police-reported crime statistics, by CMA
_CRIME_TTL = 365 * 86_400  # 1 an (données annuelles)

_CRIME_GEO_LABELS: dict[str, list[str]] = {
    "montreal":       ["Montréal", "Montreal"],
    "quebec":         ["Québec", "Quebec City", "Quebec"],
    "gatineau":       ["Gatineau", "Ottawa - Gatineau"],
    "sherbrooke":     ["Sherbrooke"],
    "saguenay":       ["Saguenay"],
    "trois-rivieres": ["Trois-Rivières", "Trois-Rivieres"],
    "drummondville":  ["Drummondville"],
    "laval":          ["Laval"],
}

# Violation type searches for dim 1 (Criminal Code violation type)
_CRIME_VIOLATION_SEARCHES: dict[str, list[str]] = {
    "taux_crimes_violents":        ["Violent violations", "Total violent", "Violent Criminal Code"],
    "taux_crimes_contre_propriete": ["Property violations", "Total property", "Property Criminal Code"],
    "taux_criminalite_total":      ["Total Criminal Code", "Total, Criminal Code", "Criminal Code violations"],
}

# Statistic type searches for dim 2 (Statistic)
_CRIME_STAT_SEARCHES: list[str] = ["Rate per 100,000 population", "Rate per 100,000", "Taux pour 100 000"]

# ── Ratio dette/revenu ménages (StatCan 11-10-0065-01) ───────────────────────
_DETTE_TABLE = 1110006501  # 11-10-0065-01 : Household sector credit market summary
_DETTE_TTL = 90 * 86_400   # 90 jours (données trimestrielles)

# Dim 0 adjustment type → prefer seasonally adjusted
_DETTE_ADJ_SEARCHES = [
    "Seasonally adjusted annual rates",
    "Seasonally adjusted",
    "Unadjusted",
]

# Dim 1 — financial indicators to extract
_DETTE_INDICATORS: dict[str, list[str]] = {
    "ratio_dette_revenu_pct": [
        "Credit market debt as a percentage of household disposable income",
        "percentage of household disposable income",
        "Debt to income",
    ],
    "ratio_hypotheque_revenu_pct": [
        "Mortgage liabilities as a percentage of household disposable income",
        "Mortgage debt as a percentage",
        "Mortgage liabilities",
    ],
    "taux_epargne_pct": [
        "Net saving rate",
        "Household saving rate",
        "Saving rate",
    ],
}

# ── Unités absorbées — marché neuf SCHL (StatCan 34-10-0149-01) ──────────────
_ABSORB_TABLE = 3410014901  # 34-10-0149-01 : Absorbed housing units by type and price range
_ABSORB_TTL = 90 * 86_400  # 90 jours (données trimestrielles)

# city_code → GEO labels (CMA, same as chantier/neuf)
_ABSORB_GEO_LABELS: dict[str, list[str]] = {
    "montreal":       ["Montréal", "Montreal"],
    "quebec":         ["Québec", "Quebec"],
    "gatineau":       ["Ottawa - Gatineau", "Gatineau"],
    "sherbrooke":     ["Sherbrooke"],
    "saguenay":       ["Saguenay"],
    "trois-rivieres": ["Trois-Rivières", "Trois-Rivieres"],
    "drummondville":  ["Drummondville"],
    "laval":          ["Laval"],
}

# Dwelling type → field key (Dim 1)
_ABSORB_TYPE_SEARCHES: dict[str, list[str]] = {
    "unites_absorbees_total":        ["Total units", "Total"],
    "unites_absorbees_unifamilial":  ["Single-detached", "Single detached", "Maisons individuelles"],
    "unites_absorbees_appartement":  ["Apartment and other", "Apartments", "Appartements"],
}

# Price range → "Total" for all price ranges combined (Dim 2)
_ABSORB_PRICE_TOTAL = ["Total, all price ranges", "All price ranges", "Total"]

# ── Distance au CBD — coordonnées des centres-villes QC ──────────────────────
# (lat, lng, nom_officiel)  — référence: place centrale de chaque CMA
_CBD_COORDS: dict[str, tuple[float, float, str]] = {
    "montreal":       (45.5088, -73.5540, "Montréal"),     # Place d'Armes
    "quebec":         (46.8139, -71.2080, "Québec"),        # Place d'Youville
    "gatineau":       (45.4765, -75.7013, "Gatineau"),      # Centre-ville Hull
    "sherbrooke":     (45.4042, -71.8929, "Sherbrooke"),    # Place du Marché
    "saguenay":       (48.4284, -71.0537, "Saguenay"),      # Centre Chicoutimi
    "trois-rivieres": (46.3432, -72.5418, "Trois-Rivières"),
    "drummondville":  (45.8836, -72.4832, "Drummondville"),
    "laval":          (45.5636, -73.6924, "Laval"),         # Carrefour Laval
}

# ── Marché neuf — completions & pipeline (StatCan 34-10-0093-01) ─────────────
_NEUF_TABLE = 3410009301   # 34-10-0093-01 : Starts, under construction, completions
_NEUF_TTL = 86_400         # 24 h (données mensuelles)

# Same GEO labels as mises en chantier (same SCHL CMA survey)
_NEUF_GEO_LABELS: dict[str, list[str]] = {
    "montreal":       ["Montréal", "Montreal"],
    "quebec":         ["Québec", "Quebec"],
    "gatineau":       ["Ottawa - Gatineau", "Gatineau"],
    "sherbrooke":     ["Sherbrooke"],
    "saguenay":       ["Saguenay"],
    "trois-rivieres": ["Trois-Rivières", "Trois-Rivieres"],
    "drummondville":  ["Drummondville"],
    "laval":          ["Laval"],
}

# Variable searches for dim 2 (housing market variable)
_NEUF_VAR_SEARCHES: dict[str, list[str]] = {
    "completions_mois":      ["Completed", "Completions", "Completées"],
    "unites_en_construction": ["Under construction", "En construction"],
}

# ── Mises en chantier SCHL (StatCan 34-10-0056-01) ───────────────────────────
_CHANTIER_TABLE = 3410005601  # 34-10-0056-01 : Housing starts by CMA (CMHC)

# city_code → GEO labels (CMA level)
_CHANTIER_GEO_LABELS: dict[str, list[str]] = {
    "montreal":       ["Montréal", "Montreal"],
    "quebec":         ["Québec", "Quebec"],
    "gatineau":       ["Ottawa - Gatineau", "Gatineau"],
    "sherbrooke":     ["Sherbrooke"],
    "saguenay":       ["Saguenay"],
    "trois-rivieres": ["Trois-Rivières", "Trois-Rivieres"],
    "drummondville":  ["Drummondville"],
    "laval":          ["Laval"],
}

# Dwelling type searches for dim 1
_CHANTIER_TYPE_SEARCHES: dict[str, list[str]] = {
    "total":       ["Total units", "Total", "Ensemble"],
    "unifamilial": ["Single-detached", "Single detached", "Maison individuelle"],
    "collectif":   ["Apartments and other", "Multi-unit", "Appartements"],
}

# ── IPC (Indice des prix à la consommation) — StatCan 18-10-0004-01 ──────────
_IPC_TABLE = 1810000401  # 18-10-0004-01 : CPI by component, annual

# Geography — use Canada total or Quebec province
_IPC_GEO_SEARCHES = ["Canada", "Québec", "Quebec"]

# Components to extract (dim search terms)
_IPC_COMPONENTS: dict[str, list[str]] = {
    "ipc_total":    ["All-items", "Ensemble"],
    "ipc_logement": ["Shelter", "Logement"],
    "ipc_energie":  ["Energy", "Énergie"],
}

# ── Marché du travail CMA (StatCan 14-10-0096-01) ────────────────────────────
_TRAVAIL_TABLE = 1410009601  # 14-10-0096-01 : Labour force characteristics by CMA (SA)

# city_code → StatCan GEO labels (CMA, EN)
_TRAVAIL_GEO_LABELS: dict[str, list[str]] = {
    "montreal":       ["Montréal", "Montreal"],
    "quebec":         ["Québec", "Quebec"],
    "gatineau":       ["Ottawa - Gatineau", "Gatineau"],
    "sherbrooke":     ["Sherbrooke"],
    "saguenay":       ["Saguenay"],
    "trois-rivieres": ["Trois-Rivières", "Trois-Rivieres"],
    "drummondville":  ["Drummondville"],
}

# Labour force characteristics to extract (dim 1 member search terms)
_TRAVAIL_INDICATORS: dict[str, list[str]] = {
    "taux_chomage_pct":    ["Unemployment rate"],
    "taux_emploi_pct":     ["Employment rate"],
    "taux_participation_pct": ["Participation rate"],
}

# ── Population CMA (StatCan 17-10-0135-01) ───────────────────────────────────
_POP_TABLE = 1710013501  # 17-10-0135-01 : Estimations de population par CMA

# city_code → StatCan GEO labels (CMA level, EN)
_POP_GEO_LABELS: dict[str, list[str]] = {
    "montreal":       ["Montréal", "Montreal"],
    "quebec":         ["Québec", "Quebec"],
    "gatineau":       ["Ottawa - Gatineau", "Gatineau"],
    "sherbrooke":     ["Sherbrooke"],
    "saguenay":       ["Saguenay"],
    "trois-rivieres": ["Trois-Rivières", "Trois-Rivieres"],
    "drummondville":  ["Drummondville"],
    "laval":          ["Laval"],
}

# ── NHPI — New Housing Price Index (StatCan 18-10-0205-01) ───────────────────
_NHPI_TABLE = 1810020501  # table 18-10-0205-01

# city_code → StatCan GEO label for NHPI (CMA level)
_NHPI_GEO_LABELS: dict[str, list[str]] = {
    "montreal":      ["Montréal", "Montreal"],
    "quebec":        ["Québec", "Quebec city"],
    "gatineau":      ["Ottawa - Gatineau", "Gatineau"],
    "sherbrooke":    ["Sherbrooke"],
    "saguenay":      ["Saguenay"],
    "trois-rivieres":["Trois-Rivières", "Trois-Rivieres"],
    "drummondville": ["Drummondville"],
}

# NHPI type → field key
_NHPI_TYPE_SEARCHES: dict[str, list[str]] = {
    "total":    ["Total (house and land)", "Total"],
    "batiment": ["Building", "Bâtiment"],
    "terrain":  ["Land", "Terrain"],
}

# ── Permis de construction (StatCan 34-10-0066-01) ────────────────────────────
_PERMIS_TABLE = 3410006601  # 34-10-0066-01 : Building permits by type of structure and work

# city_code → StatCan GEO labels (CMA level, EN)
_PERMIS_GEO_LABELS: dict[str, list[str]] = {
    "montreal":       ["Montréal, Quebec", "Montréal"],
    "quebec":         ["Québec, Quebec", "Québec"],
    "gatineau":       ["Ottawa - Gatineau, Quebec part, Quebec", "Gatineau, Quebec part",
                       "Ottawa-Gatineau, Quebec part"],
    "sherbrooke":     ["Sherbrooke, Quebec", "Sherbrooke"],
    "saguenay":       ["Saguenay, Quebec", "Saguenay"],
    "trois-rivieres": ["Trois-Rivières, Quebec", "Trois-Rivières"],
    "drummondville":  ["Drummondville, Quebec", "Drummondville"],
    "laval":          ["Laval, Quebec", "Laval"],
}

_PERMIS_STRUCTURE_SEARCHES = ["Residential", "Résidentiel"]
_PERMIS_WORK_SEARCHES_NEW  = ["New construction", "Nouvelle construction"]
_PERMIS_WORK_SEARCHES_ALL  = ["All work", "Toutes catégories", "Total"]
_PERMIS_UNIT_SEARCHES      = ["Number of units", "Units", "Unités"]
_PERMIS_VALUE_SEARCHES     = ["Value of permits", "Value", "Valeur"]

# ── Census Profile 2021 (StatCan REST) ───────────────────────────────────────
_CENSUS_BASE = "https://www12.statcan.gc.ca/rest/census-recensement/CR2021/fr/json"
_CENSUS_TTL = 30 * 86_400  # 30 jours — données stables (recensement 2021)

# city_code → DGUID Census Subdivision (SDR/CSD) 2021
# Format: 2021A0005{SGC-7-digits}   A = CSD level
_CENSUS_DGUIDS: dict[str, str] = {
    "montreal":       "2021A000524462023",  # Montréal (Île-de-Montréal CD)
    "laval":          "2021A000524290",     # Laval
    "longueuil":      "2021A000524458227",  # Longueuil (Agglomération)
    "quebec":         "2021A000523305",     # Québec (Capitale-Nationale)
    "gatineau":       "2021A000524813",     # Gatineau
    "sherbrooke":     "2021A000245005",     # Sherbrooke
    "saguenay":       "2021A000224006",     # Saguenay
    "trois-rivieres": "2021A000237012",     # Trois-Rivières
    "levis":          "2021A000223023",     # Lévis
    "drummondville":  "2021A000220016",     # Drummondville
}

# Substring patterns to extract from CHARACTERISTIC_NAME (FR)
# topic → [(field_key, search_substring), ...]
_CENSUS_TOPICS: dict[str, list[tuple[str, str]]] = {
    "9": [  # Logements
        ("pct_proprietaires",      "Propriétaires"),
        ("pct_locataires",         "Locataires"),
        ("valeur_mediane_logement","Valeur médiane ($)"),
        ("frais_loyer_median",     "Frais mensuels médians ($)"),
    ],
    "5": [  # Revenu
        ("revenu_median_menage",   "Revenu total médian des ménages"),
    ],
}


def fetch_census_profile(city_code: str, cache_dir: Path) -> dict:
    """Fetch 2021 Census Profile for a given city (demographic + housing indicators).

    Returns dict with keys: pct_proprietaires, pct_locataires,
    valeur_mediane_logement, frais_loyer_median, revenu_median_menage, ville, source.
    Returns {} if city unsupported or data unavailable.
    """
    import urllib.request

    dguid = _CENSUS_DGUIDS.get(city_code)
    if not dguid:
        return {}

    cache_path = cache_dir / f"census_{city_code}.json"
    cached = _read_cache_ttl(cache_path, _CENSUS_TTL)
    if cached is not None:
        return cached

    result: dict = {"ville": city_code, "source": "StatCan Recensement 2021"}
    char_rows: list[dict] = []

    for topic_id in _CENSUS_TOPICS:
        url = (
            f"{_CENSUS_BASE}?dguid={dguid}&topic={topic_id}&notes=0&lang=F"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "eval-immo/1.0"})
            with urllib.request.urlopen(req, timeout=int(_HTTP_TIMEOUT)) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if isinstance(data, list):
                    char_rows.extend(data)
        except Exception as exc:
            logger.debug("census topic %s fetch error: %s", topic_id, exc)

    if not char_rows:
        return {}

    # Build lookup dict: characteristic_name → C1_COUNT_TOTAL value
    char_lookup: dict[str, str] = {}
    for row in char_rows:
        name = str(row.get("CHARACTERISTIC_NAME") or row.get("Caractéristique") or "")
        value = str(row.get("C1_COUNT_TOTAL") or row.get("C1_TOTAL") or "").strip()
        if name and value and value not in ("", "x", "...", "F", "..F"):
            char_lookup[name] = value

    # Extract fields by substring match
    for topic_id, fields in _CENSUS_TOPICS.items():
        for field_key, search_sub in fields:
            for name, value in char_lookup.items():
                if search_sub.lower() in name.lower():
                    try:
                        num = float(value.replace(",", "").replace(" ", ""))
                        result[field_key] = num
                    except ValueError:
                        pass
                    break  # first match wins

    _write_cache_ttl(cache_path, result, _CENSUS_TTL)
    logger.debug("census_profile injecté: %s (%d champs)", city_code, len(result) - 2)
    return result


def _read_cache_ttl(path: Path, ttl: int) -> dict | None:
    """Read JSON cache file if it exists and is within TTL. Returns None on miss."""
    if not path.exists():
        return None
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(d, dict) and time.time() - d.get("_ts", 0) < ttl:
            return d
    except Exception:
        pass
    return None


def _write_cache_ttl(path: Path, data: dict, ttl: int) -> None:  # noqa: ARG001
    """Write data to JSON cache with current timestamp."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        out = dict(data)
        out["_ts"] = time.time()
        path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def detect_city(display_name: str, zone: str = "") -> str:
    """Return SCHL city code inferred from display_name + zone (default: 'montreal').

    Strategy: try the last comma-segment of the address first (most likely the city),
    then fall back to the zone field, then the full text.
    """
    # 1. Last segment of comma-separated address (usually the city)
    parts = display_name.split(",")
    candidates = [_norm(parts[-1])] if len(parts) > 1 else []
    # 2. Zone field
    if zone:
        candidates.append(_norm(zone))
    # 3. Full display name (fallback)
    candidates.append(_norm(display_name))

    for haystack in candidates:
        for kw, code in _CITY_KEYWORDS:
            if kw in haystack:
                return code
    return "montreal"


# ── SCHL rental market (StatCan WDS) ─────────────────────────────────────────

def _wds_post(endpoint: str, payload: Any, timeout: float = _HTTP_TIMEOUT) -> Any:
    import httpx  # type: ignore
    url = _WDS_BASE + endpoint
    r = httpx.post(url, json=payload, timeout=timeout, follow_redirects=True)
    r.raise_for_status()
    return r.json()


def _wds_get(endpoint: str, timeout: float = _HTTP_TIMEOUT) -> Any:
    import httpx  # type: ignore
    url = _WDS_BASE + endpoint
    r = httpx.get(url, timeout=timeout, follow_redirects=True)
    r.raise_for_status()
    return r.json()


def _cube_metadata(pid: int, cache_dir: Path) -> dict:
    """Fetch cube metadata with member ordinals; cache 24 h."""
    cache_path = cache_dir / f"wds_meta_{pid}.json"
    cached = _read_cache(cache_path)
    if cached:
        return cached
    data = _wds_get(f"getCubeMetadata/{pid}")
    if not isinstance(data, dict) or data.get("status") != "SUCCESS":
        return {}
    obj = data.get("object", {})
    result = {"_ts": time.time(), "dims": obj.get("dimension", [])}
    _write_cache(cache_path, result)
    return result


def _find_member_ordinal(dims: list[dict], dim_idx: int, search_terms: list[str]) -> int | None:
    """Return ordinal of best-matching member in dimension dim_idx.

    Tries exact match first, then substring match — avoids false positives
    like "employment rate" matching inside "unemployment rate".
    """
    if dim_idx >= len(dims):
        return None
    members = dims[dim_idx].get("member", [])
    # Pass 1: exact match
    for term in search_terms:
        t = _norm(term)
        for m in members:
            if t == _norm(str(m.get("memberNameEn", ""))):
                return int(m["memberId"])
    # Pass 2: substring match (fallback)
    for term in search_terms:
        t = _norm(term)
        for m in members:
            if t in _norm(str(m.get("memberNameEn", ""))):
                return int(m["memberId"])
    return None


def _build_coordinate(*ordinals: int | None) -> str | None:
    if any(o is None for o in ordinals):
        return None
    return ".".join(str(o) for o in ordinals)  # type: ignore[arg-type]


def _fetch_series(pid: int, coordinate: str, cache_dir: Path) -> float | None:
    """Fetch latest scalar value for a series; cache 24 h."""
    cache_path = cache_dir / f"wds_{pid}_{coordinate.replace('.', '_')}.json"
    cached = _read_cache(cache_path)
    if cached:
        return cached.get("value")

    payload = [{"productId": pid, "coordinate": coordinate, "latestN": 1}]
    data = _wds_post("getDataFromCubePidCoordAndLatestNPeriods", payload)
    if not isinstance(data, list) or not data:
        return None
    item = data[0]
    if item.get("status") != "SUCCESS":
        return None
    points = item.get("object", {}).get("vectorDataPoint", [])
    if not points:
        return None
    raw_val = points[0].get("value")
    try:
        val = float(raw_val)
    except (TypeError, ValueError):
        return None
    result = {"_ts": time.time(), "value": val}
    _write_cache(cache_path, result)
    return val


def fetch_taux_boc(cache_dir: Path) -> dict:
    """
    Fetch current Bank of Canada key rates via Valet REST API.

    Returns dict with keys: taux_directeur_pct, taux_preferentiel_pct,
    taux_hypo_5ans_conv_pct, taux_hypo_1an_pct, date, source.
    Returns {} on any failure (non-blocking).
    """
    import urllib.request

    cache_path = cache_dir / "boc_rates.json"
    cached = _read_cache_ttl(cache_path, _BOC_TTL)
    if cached is not None:
        return cached

    result: dict = {"source": "bankofcanada-valet"}

    # Fetch all series in one call: /observations/S1,S2,...?recent=1
    series_ids = ",".join(_BOC_SERIES.keys())
    url = f"{_BOC_VALET_BASE}/{series_ids}/json?recent=1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "eval-immo/1.0"})
        with urllib.request.urlopen(req, timeout=int(_HTTP_TIMEOUT)) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        logger.debug("BOC Valet fetch error: %s", exc)
        return {}

    observations = data.get("observations", [])
    if not observations:
        return {}

    latest = observations[-1]
    result["date"] = str(latest.get("d", ""))[:10]

    for series_id, field_key in _BOC_SERIES.items():
        entry = latest.get(series_id, {})
        raw = entry.get("v") if isinstance(entry, dict) else None
        if raw is not None:
            try:
                result[field_key] = float(raw)
            except (TypeError, ValueError):
                pass

    if len(result) <= 2:  # only source + date
        return {}

    _write_cache_ttl(cache_path, result, _BOC_TTL)
    logger.debug("taux_boc injecté : directeur=%.2f%% hypo5=%.2f%%",
                 result.get("taux_directeur_pct", 0),
                 result.get("taux_hypo_5ans_conv_pct", 0))
    return result


def fetch_marche_travail(city_code: str, cache_dir: Path) -> dict:
    """
    Return labour market indicators for a QC CMA via StatCan WDS (14-10-0096-01).

    Returns dict with keys: taux_chomage_pct, taux_emploi_pct,
    taux_participation_pct, periode, ville, source.
    Returns {} on any failure or unsupported city.
    """
    geo_labels = _TRAVAIL_GEO_LABELS.get(city_code)
    if not geo_labels:
        return {}

    try:
        meta = _cube_metadata(_TRAVAIL_TABLE, cache_dir)
        dims = meta.get("dims", [])
        if not dims:
            return {}

        # Dim 0 = GEO
        geo_ord = _find_member_ordinal(dims, 0, geo_labels)
        if geo_ord is None:
            return {}

        # Optional dim 2 (sex) → Both sexes / Total
        sex_ord: int | None = None
        if len(dims) >= 3:
            sex_ord = _find_member_ordinal(dims, 2,
                                           ["Both sexes", "Total - sex", "Total"])
            if sex_ord is None:
                members = dims[2].get("member", [])
                if members:
                    sex_ord = int(members[0]["memberId"])

        result: dict = {
            "source": "statcan-14-10-0096-01",
            "ville": _SCHL_TO_DISPLAY.get(city_code, city_code),
        }

        for field_key, searches in _TRAVAIL_INDICATORS.items():
            ind_ord = _find_member_ordinal(dims, 1, searches)
            coord = _build_coordinate(geo_ord, ind_ord,
                                      *([] if sex_ord is None else [sex_ord]))
            if coord:
                # latestN=1 for current value
                payload = [{"productId": _TRAVAIL_TABLE,
                            "coordinate": coord, "latestN": 1}]
                data = _wds_post("getDataFromCubePidCoordAndLatestNPeriods", payload)
                if (isinstance(data, list) and data
                        and data[0].get("status") == "SUCCESS"):
                    pts = data[0].get("object", {}).get("vectorDataPoint", [])
                    if pts:
                        try:
                            result[field_key] = float(pts[0]["value"])
                            if "periode" not in result:
                                ref = pts[0].get("refPer") or pts[0].get("refper") or ""
                                if ref:
                                    result["periode"] = str(ref)[:7]
                        except (TypeError, ValueError):
                            pass

        if len(result) <= 2:
            return {}

        return result

    except Exception as exc:  # pragma: no cover
        logger.debug("Marché travail fetch failed for %s: %s", city_code, exc)
        return {}


def fetch_proximite_services(lat: float, lng: float, cache_dir: Path) -> dict:
    """
    Count nearby OSM amenities around (lat, lng) via Overpass API.

    Returns dict with counts per category (ecoles_1km, arrets_transport_500m, …)
    plus source and coords. Cache keyed by rounded coordinates (4 decimals ≈ 11m).
    Returns {} on any failure (non-blocking).
    """
    import urllib.request
    import urllib.parse

    # Round to 4 decimals for cache key (~11m precision, stable between runs)
    lat_r = round(lat, 4)
    lng_r = round(lng, 4)
    cache_path = cache_dir / f"overpass_{lat_r}_{lng_r}.json"
    cached = _read_cache_ttl(cache_path, _OVERPASS_TTL)
    if cached is not None:
        return cached

    result: dict = {
        "source": "openstreetmap-overpass",
        "lat": lat_r,
        "lng": lng_r,
    }

    for field_key, radius_m, osm_filter in _OVERPASS_QUERIES:
        query = (
            f"[out:json][timeout:15];"
            f"("
            f"  node{osm_filter}(around:{radius_m},{lat_r},{lng_r});"
            f"  way{osm_filter}(around:{radius_m},{lat_r},{lng_r});"
            f");"
            f"out count;"
        )
        try:
            data_enc = urllib.parse.urlencode({"data": query}).encode()
            req = urllib.request.Request(
                _OVERPASS_URL,
                data=data_enc,
                headers={"User-Agent": "eval-immo/1.0"},
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
            # Overpass "out count" response: {"elements": [{"type":"count","tags":{"total":"N"}}]}
            elements = resp_data.get("elements", [])
            if elements:
                count_tags = elements[0].get("tags", {})
                total = count_tags.get("total", "0")
                result[field_key] = int(total)
        except Exception as exc:
            logger.debug("Overpass %s skip: %s", field_key, exc)
            # Leave key absent — partial results still useful

    if len(result) <= 3:  # only source + lat + lng
        return {}

    _write_cache_ttl(cache_path, result, _OVERPASS_TTL)
    logger.debug("proximite_services injecté : écoles=%s transports=%s",
                 result.get("ecoles_1km"), result.get("arrets_transport_500m"))
    return result


def fetch_nuisances_environnementales(lat: float, lng: float, cache_dir: Path) -> dict:
    """
    Count environmental nuisance features (airport, railway, industrial, quarry)
    around the property via OSM Overpass API.

    Returns dict with keys: aeroports_10km, voies_ferrees_500m,
    zones_industrielles_1km, carrieres_2km, score_nuisances, interpretation,
    source, lat, lng.
    score_nuisances: 0 (aucune) → 4 (nuisances multiples).
    Returns {} if all queries fail (non-blocking).  Cache: 30 days.
    """
    import urllib.request
    import urllib.parse

    lat_r = round(lat, 4)
    lng_r = round(lng, 4)
    cache_path = cache_dir / f"nuisances_{lat_r}_{lng_r}.json"
    cached = _read_cache_ttl(cache_path, _NUISANCES_TTL)
    if cached is not None:
        return cached

    result: dict = {
        "source": "openstreetmap-overpass-nuisances",
        "lat": lat_r,
        "lng": lng_r,
    }

    for field_key, radius_m, osm_filter in _NUISANCES_QUERIES:
        query = (
            f"[out:json][timeout:15];"
            f"("
            f"  node{osm_filter}(around:{radius_m},{lat_r},{lng_r});"
            f"  way{osm_filter}(around:{radius_m},{lat_r},{lng_r});"
            f"  relation{osm_filter}(around:{radius_m},{lat_r},{lng_r});"
            f");"
            f"out count;"
        )
        try:
            data_enc = urllib.parse.urlencode({"data": query}).encode()
            req = urllib.request.Request(
                _OVERPASS_URL,
                data=data_enc,
                headers={"User-Agent": "eval-immo/1.0"},
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
            elements = resp_data.get("elements", [])
            if elements:
                count_tags = elements[0].get("tags", {})
                total = count_tags.get("total", "0")
                result[field_key] = int(total)
        except Exception as exc:
            logger.debug("Overpass nuisances %s skip: %s", field_key, exc)

    if len(result) <= 3:  # only source + lat + lng
        return {}

    # Score: 1 point per nuisance type present
    score = sum(
        1 for k in ("aeroports_10km", "voies_ferrees_500m",
                    "zones_industrielles_1km", "carrieres_2km")
        if result.get(k, 0) > 0
    )
    result["score_nuisances"] = score

    if score == 0:
        interpretation = "aucune nuisance environnementale détectée"
    elif score == 1:
        interpretation = "nuisance mineure détectée"
    elif score == 2:
        interpretation = "nuisances modérées — impact potentiel sur la valeur"
    else:
        interpretation = "nuisances importantes — analyse approfondie requise"
    result["interpretation"] = interpretation

    _write_cache_ttl(cache_path, result, _NUISANCES_TTL)
    logger.debug("nuisances_environnementales injecté : score=%s (%s)",
                 score, interpretation)
    return result


def fetch_proximite_routes(lat: float, lng: float, cache_dir: Path) -> dict:
    """
    Return distance to nearest major road axes (motorway / trunk / primary) via
    OSM Overpass API.

    Uses 'out 1 center;' to retrieve the nearest way's bounding-box centre, then
    Haversine for distance. Cache keyed by rounded coordinates (4 dp ≈ 11 m).
    Returns dict with keys: autoroute_km, route_nationale_km, artere_km,
    interpretation, source, lat, lng. Absent key = no road of that type within
    15 km. Returns {} on total failure (non-blocking).
    """
    import urllib.request
    import urllib.parse

    lat_r = round(lat, 4)
    lng_r = round(lng, 4)
    cache_path = cache_dir / f"routes_{lat_r}_{lng_r}.json"
    cached = _read_cache_ttl(cache_path, _OVERPASS_TTL)
    if cached is not None:
        return cached

    result: dict = {
        "source": "openstreetmap-overpass-routes",
        "lat": lat_r,
        "lng": lng_r,
    }

    for field_key, hw_value in _ROUTE_TYPES:
        query = (
            f"[out:json][timeout:20];"
            f"way[\"highway\"=\"{hw_value}\"]"
            f"(around:{_ROUTES_SEARCH_RADIUS_M},{lat_r},{lng_r});"
            f"out 1 center;"
        )
        try:
            data_enc = urllib.parse.urlencode({"data": query}).encode()
            req = urllib.request.Request(
                _OVERPASS_URL,
                data=data_enc,
                headers={"User-Agent": "eval-immo/1.0"},
            )
            with urllib.request.urlopen(req, timeout=25) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
            elements = resp_data.get("elements", [])
            if elements:
                center = elements[0].get("center", {})
                c_lat = center.get("lat")
                c_lon = center.get("lon")
                if c_lat is not None and c_lon is not None:
                    dist_km = _haversine_km(lat_r, lng_r, float(c_lat), float(c_lon))
                    result[field_key] = round(dist_km, 2)
        except Exception as exc:
            logger.debug("Overpass routes %s skip: %s", field_key, exc)

    # Interpretation based on nearest autoroute distance
    auto_km = result.get("autoroute_km")
    artere_km = result.get("artere_km")
    if auto_km is not None and auto_km <= 2.0:
        interpretation = "excellent accès autoroutier"
    elif auto_km is not None and auto_km <= 5.0:
        interpretation = "bon accès autoroutier"
    elif artere_km is not None and artere_km <= 1.0:
        interpretation = "bon accès artériel"
    elif auto_km is not None and auto_km <= 10.0:
        interpretation = "accès modéré"
    else:
        interpretation = "accès éloigné des grands axes"
    result["interpretation"] = interpretation

    if len(result) <= 4:  # only source + lat + lng + interpretation
        return {}

    _write_cache_ttl(cache_path, result, _OVERPASS_TTL)
    logger.debug("proximite_routes injecté : autoroute=%.1f km, artere=%.1f km",
                 result.get("autoroute_km", 0), result.get("artere_km", 0))
    return result


def fetch_donnees_climatiques(lat: float, lng: float, cache_dir: Path) -> dict:
    """
    Return historical climate summary for the property location via Open-Meteo
    archive API (year _CLIMAT_YEAR).

    Returns dict with keys: temperature_moyenne_annuelle, precipitations_annuelles_mm,
    jours_gel, jours_chaleur_extreme, annee_reference, source, lat, lng.
    Cache: 1 year (historical data is stable).
    Returns {} on any failure (non-blocking).
    """
    import urllib.request
    import urllib.parse

    lat_r = round(lat, 4)
    lng_r = round(lng, 4)
    cache_path = cache_dir / f"climat_{lat_r}_{lng_r}.json"
    cached = _read_cache_ttl(cache_path, _CLIMAT_TTL)
    if cached is not None:
        return cached

    try:
        params = urllib.parse.urlencode({
            "latitude": lat_r,
            "longitude": lng_r,
            "start_date": f"{_CLIMAT_YEAR}-01-01",
            "end_date": f"{_CLIMAT_YEAR}-12-31",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "America/Montreal",
        })
        url = f"{_CLIMAT_BASE}?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "eval-immo/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        daily = data.get("daily", {})
        tmax_list = daily.get("temperature_2m_max", [])
        tmin_list = daily.get("temperature_2m_min", [])
        precip_list = daily.get("precipitation_sum", [])

        if not tmax_list or not tmin_list:
            return {}

        # Filter out None values (API returns null for missing data)
        tmean_list = [
            (tmax + tmin) / 2
            for tmax, tmin in zip(tmax_list, tmin_list)
            if tmax is not None and tmin is not None
        ]
        if not tmean_list:
            return {}

        temp_moy = round(sum(tmean_list) / len(tmean_list), 1)
        precip_ann = round(sum(p for p in precip_list if p is not None), 0)
        jours_gel = sum(
            1 for tmin in tmin_list if tmin is not None and tmin < 0
        )
        jours_chaleur = sum(
            1 for tmax in tmax_list if tmax is not None and tmax >= 30
        )

        result = {
            "source": "open-meteo-archive",
            "lat": lat_r,
            "lng": lng_r,
            "annee_reference": _CLIMAT_YEAR,
            "temperature_moyenne_annuelle": temp_moy,
            "precipitations_annuelles_mm": precip_ann,
            "jours_gel": jours_gel,
            "jours_chaleur_extreme": jours_chaleur,
        }

        _write_cache_ttl(cache_path, result, _CLIMAT_TTL)
        logger.debug("donnees_climatiques injecté : T_moy=%.1f°C pluie=%.0f mm gel=%d j",
                     temp_moy, precip_ann, jours_gel)
        return result

    except Exception as exc:
        logger.debug("donnees_climatiques fetch failed: %s", exc)
        return {}


def fetch_enseignement_postsecondaire(lat: float, lng: float, cache_dir: Path) -> dict:
    """
    Count CÉGEP/colleges (5 km) and universities (10 km) via OSM Overpass.

    Distinct from B20 (which counts all schools within 1 km).  Post-secondary
    density is a proxy for student rental demand and employment-centre proximity.
    Cache: 30 days (institutions rarely change).

    Returns dict with keys: cegep_5km, universite_10km, total_postsecondaire,
    interpretation, source, lat, lng.
    Returns {} if all queries fail (non-blocking).
    """
    import urllib.request
    import urllib.parse

    lat_r = round(lat, 4)
    lng_r = round(lng, 4)
    cache_path = cache_dir / f"postsec_{lat_r}_{lng_r}.json"
    cached = _read_cache_ttl(cache_path, _POSTSEC_TTL)
    if cached is not None:
        return cached

    result: dict = {
        "source": "openstreetmap-overpass-postsec",
        "lat": lat_r,
        "lng": lng_r,
    }

    queries = [
        ("cegep_5km",      _POSTSEC_RADIUS_CEGEP, '["amenity"="college"]'),
        ("universite_10km", _POSTSEC_RADIUS_UNIV,  '["amenity"="university"]'),
    ]

    for field_key, radius_m, osm_filter in queries:
        query = (
            f"[out:json][timeout:15];"
            f"("
            f"  node{osm_filter}(around:{radius_m},{lat_r},{lng_r});"
            f"  way{osm_filter}(around:{radius_m},{lat_r},{lng_r});"
            f"  relation{osm_filter}(around:{radius_m},{lat_r},{lng_r});"
            f");"
            f"out count;"
        )
        try:
            data_enc = urllib.parse.urlencode({"data": query}).encode()
            req = urllib.request.Request(
                _OVERPASS_URL,
                data=data_enc,
                headers={"User-Agent": "eval-immo/1.0"},
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
            elements = resp_data.get("elements", [])
            if elements:
                count_tags = elements[0].get("tags", {})
                total = count_tags.get("total", "0")
                result[field_key] = int(total)
        except Exception as exc:
            logger.debug("Overpass postsec %s skip: %s", field_key, exc)

    # Compute total and interpretation
    cegep = result.get("cegep_5km", 0)
    univ = result.get("universite_10km", 0)
    total = cegep + univ
    result["total_postsecondaire"] = total

    if univ >= 1 and cegep >= 1:
        interpretation = "secteur universitaire et collégial"
    elif univ >= 1:
        interpretation = "proximité universitaire"
    elif cegep >= 2:
        interpretation = "secteur collégial dense"
    elif cegep >= 1:
        interpretation = "proximité CÉGEP"
    else:
        interpretation = "pas d'établissement post-secondaire proche"
    result["interpretation"] = interpretation

    # Need at least one real count to be useful
    if "cegep_5km" not in result and "universite_10km" not in result:
        return {}

    _write_cache_ttl(cache_path, result, _POSTSEC_TTL)
    logger.debug("enseignement_postsecondaire injecté : cégep=%s univ=%s (%s)",
                 cegep, univ, interpretation)
    return result


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in kilometres (Haversine formula)."""
    R = 6_371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlng / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def compute_distance_cbd(lat: float, lng: float, city_code: str) -> dict:
    """
    Compute straight-line distance (Haversine) from (lat, lng) to the city
    centre reference point for city_code.

    Returns dict with:
      distance_cbd_km, ville_reference, interpretation, source
    Returns {} if city_code is not in _CBD_COORDS.
    """
    cbd = _CBD_COORDS.get(city_code)
    if not cbd:
        return {}
    cbd_lat, cbd_lng, cbd_name = cbd
    dist = _haversine_km(lat, lng, cbd_lat, cbd_lng)
    if dist < 5:
        interpretation = "centre-ville"
    elif dist < 15:
        interpretation = "péri-central"
    elif dist < 35:
        interpretation = "banlieue proche"
    else:
        interpretation = "banlieue éloignée"
    return {
        "source": "calcul-haversine",
        "distance_cbd_km": round(dist, 2),
        "ville_reference": cbd_name,
        "interpretation": interpretation,
    }


def fetch_marche_neuf(city_code: str, cache_dir: Path) -> dict:
    """
    Return new housing completions and units under construction for a QC CMA
    via StatCan WDS (34-10-0093-01).

    Returns dict with:
      completions_mois, completions_12mois, unites_en_construction,
      taux_absorption_pct (completions / starts × 100 if starts available),
      ville, periode, source
    Returns {} if city not supported or data unavailable.
    """
    geo_labels = _NEUF_GEO_LABELS.get(city_code)
    if not geo_labels:
        return {}

    cache_path = cache_dir / f"marche_neuf_{city_code}.json"
    cached = _read_cache_ttl(cache_path, _NEUF_TTL)
    if cached is not None:
        return cached

    meta = _cube_metadata(_NEUF_TABLE, cache_dir)
    if not meta:
        return {}

    dims = meta.get("dims", [])
    # Table has at least 3 dims: Geography, Dwelling type, Variable
    if len(dims) < 3:
        return {}

    # Dim 0 = Geography, Dim 1 = Dwelling type, Dim 2 = Variable
    geo_ord = None
    for lbl in geo_labels:
        geo_ord = _find_member_ordinal(dims, 0, [lbl])
        if geo_ord is not None:
            break
    if geo_ord is None:
        return {}

    total_type_ord = _find_member_ordinal(dims, 1, ["Total units", "Total", "Ensemble", "All types"])
    if total_type_ord is None:
        return {}

    result: dict = {
        "source": "statcan-34-10-0093-01",
        "ville": geo_labels[0],
    }
    periode = ""

    for field_key, searches in _NEUF_VAR_SEARCHES.items():
        var_ord = _find_member_ordinal(dims, 2, searches)
        if var_ord is None:
            continue
        coord = _build_coordinate([geo_ord, total_type_ord, var_ord])
        try:
            payload = [{"productId": _NEUF_TABLE, "coordinate": coord, "latestN": 12}]
            rows = _wds_post("getDataFromCubePidCoordAndLatestNPeriods", payload)
            if rows:
                pts = rows[0].get("object", {}).get("vectorDataPoint", [])
                valid = [float(p["value"]) for p in pts
                         if p.get("status") != "E" and p.get("value") not in (None, "")]
                if valid:
                    result[field_key] = round(valid[-1], 0)  # latest month
                    if field_key == "completions_mois":
                        result["completions_12mois"] = round(sum(valid), 0)
                        if pts:
                            periode = pts[-1].get("refPer", "")
        except Exception as exc:
            logger.debug("marche_neuf %s skip: %s", field_key, exc)

    if periode:
        result["periode"] = periode

    # Compute absorption rate if starts available (from mises_en_chantier cache)
    starts_cache = cache_dir / f"mises_en_chantier_{city_code}.json"
    starts_cached = _read_cache_ttl(starts_cache, _NEUF_TTL * 30)  # accept older starts data
    if starts_cached and result.get("completions_mois") and starts_cached.get("total_mois"):
        starts_val = starts_cached["total_mois"]
        compl_val = result["completions_mois"]
        if starts_val > 0:
            result["taux_absorption_pct"] = round(compl_val / starts_val * 100, 1)

    if len(result) <= 3:
        return {}

    _write_cache_ttl(cache_path, result, _NEUF_TTL)
    logger.debug("marche_neuf injecté : %s completions=%s en_constr=%s",
                 city_code, result.get("completions_mois"), result.get("unites_en_construction"))
    return result


def fetch_crime_stats(city_code: str, cache_dir: Path) -> dict:
    """
    Return police-reported crime statistics (rate per 100,000 population) for a
    Quebec CMA via StatCan WDS (35-10-0078-01).

    Returns dict with:
      taux_criminalite_total, taux_crimes_violents, taux_crimes_contre_propriete,
      ville, annee, source
    Returns {} if city not supported or data unavailable.
    """
    geo_labels = _CRIME_GEO_LABELS.get(city_code)
    if not geo_labels:
        return {}

    cache_path = cache_dir / f"crime_{city_code}.json"
    cached = _read_cache_ttl(cache_path, _CRIME_TTL)
    if cached is not None:
        return cached

    meta = _cube_metadata(_CRIME_TABLE, cache_dir)
    if not meta:
        return {}

    dims = meta.get("dims", [])
    if len(dims) < 3:
        return {}

    # Dim 0 = Geography, Dim 1 = Violation type, Dim 2 = Statistic
    geo_ord = None
    for lbl in geo_labels:
        geo_ord = _find_member_ordinal(dims, 0, [lbl])
        if geo_ord is not None:
            break
    if geo_ord is None:
        return {}

    stat_ord = _find_member_ordinal(dims, 2, _CRIME_STAT_SEARCHES)
    if stat_ord is None:
        return {}

    result: dict = {
        "source": "statcan-35-10-0078-01",
        "ville": geo_labels[0],
    }

    for field_key, searches in _CRIME_VIOLATION_SEARCHES.items():
        viol_ord = _find_member_ordinal(dims, 1, searches)
        if viol_ord is None:
            continue
        coord = _build_coordinate([geo_ord, viol_ord, stat_ord])
        val = _fetch_series(_CRIME_TABLE, coord, cache_dir)
        if val is not None:
            result[field_key] = round(val, 1)

    # Get reference year from latest data point
    try:
        any_viol_ord = _find_member_ordinal(dims, 1, _CRIME_VIOLATION_SEARCHES["taux_criminalite_total"])
        if any_viol_ord:
            coord_total = _build_coordinate([geo_ord, any_viol_ord, stat_ord])
            payload = [{"productId": _CRIME_TABLE, "coordinate": coord_total, "latestN": 1}]
            rows = _wds_post("getDataFromCubePidCoordAndLatestNPeriods", payload)
            if rows:
                pts = rows[0].get("object", {}).get("vectorDataPoint", [])
                if pts:
                    result["annee"] = pts[-1].get("refPer", "")[:4]
    except Exception:
        pass

    if len(result) <= 3:
        return {}

    _write_cache_ttl(cache_path, result, _CRIME_TTL)
    logger.debug("crime_stats injecté : total=%s violents=%s",
                 result.get("taux_criminalite_total"), result.get("taux_crimes_violents"))
    return result


def fetch_dette_revenu(cache_dir: Path) -> dict:
    """
    Return national household debt-to-income ratio via StatCan WDS (11-10-0065-01).

    Non city-specific (Canada aggregate, quarterly).
    Returns dict with keys: ratio_dette_revenu_pct, ratio_hypotheque_revenu_pct,
    taux_epargne_pct, variation_dette_revenu_pct, periode, source.
    Returns {} on any failure.
    """
    cache_path = cache_dir / "dette_revenu.json"
    cached = _read_cache_ttl(cache_path, _DETTE_TTL)
    if cached is not None:
        return cached

    try:
        meta = _cube_metadata(_DETTE_TABLE, cache_dir)
        dims = meta.get("dims", [])
        if not dims:
            return {}

        # Dim 0 = Adjustment type → prefer seasonally adjusted
        adj_ord = _find_member_ordinal(dims, 0, _DETTE_ADJ_SEARCHES)
        if adj_ord is None:
            members0 = dims[0].get("member", [])
            if not members0:
                return {}
            adj_ord = int(members0[0]["memberId"])

        result: dict = {"source": "statcan-11-10-0065-01"}
        periode = ""

        for field_key, searches in _DETTE_INDICATORS.items():
            ind_ord = _find_member_ordinal(dims, 1, searches)
            if ind_ord is None:
                continue
            coord = _build_coordinate(adj_ord, ind_ord)
            if not coord:
                continue
            try:
                payload = [{"productId": _DETTE_TABLE, "coordinate": coord, "latestN": 5}]
                rows = _wds_post("getDataFromCubePidCoordAndLatestNPeriods", payload)
                if not rows:
                    continue
                pts = rows[0].get("object", {}).get("vectorDataPoint", [])
                valid = [
                    (p.get("refPer", ""), float(p["value"]))
                    for p in pts
                    if p.get("value") not in (None, "") and p.get("status") != "E"
                ]
                if not valid:
                    continue
                ref_per, latest_val = valid[-1]
                result[field_key] = round(latest_val, 1)
                if field_key == "ratio_dette_revenu_pct":
                    if ref_per:
                        periode = str(ref_per)[:7]
                    # Annual variation: compare latest vs ~4 quarters ago
                    if len(valid) >= 5:
                        _, prior_val = valid[0]
                        if prior_val > 0:
                            result["variation_dette_revenu_pct"] = round(
                                (latest_val - prior_val) / prior_val * 100, 1
                            )
            except Exception as exc:
                logger.debug("dette_revenu %s skip: %s", field_key, exc)

        if "ratio_dette_revenu_pct" not in result:
            return {}

        if periode:
            result["periode"] = periode

        _write_cache_ttl(cache_path, result, _DETTE_TTL)
        logger.debug("dette_revenu injecté : ratio=%.1f%%",
                     result.get("ratio_dette_revenu_pct", 0))
        return result

    except Exception as exc:  # pragma: no cover
        logger.debug("dette_revenu fetch failed: %s", exc)
        return {}


def fetch_unites_absorbees(city_code: str, cache_dir: Path) -> dict:
    """
    Return absorbed (sold) housing units in new construction for a QC CMA via
    StatCan WDS (34-10-0149-01).

    Quarterly data by dwelling type (total / single-detached / apartment).
    Returns dict with keys: unites_absorbees_total, unites_absorbees_unifamilial,
    unites_absorbees_appartement, variation_pct_4q, periode, ville, source.
    Returns {} if city not supported or data unavailable.
    """
    geo_labels = _ABSORB_GEO_LABELS.get(city_code)
    if not geo_labels:
        return {}

    cache_path = cache_dir / f"unites_absorbees_{city_code}.json"
    cached = _read_cache_ttl(cache_path, _ABSORB_TTL)
    if cached is not None:
        return cached

    try:
        meta = _cube_metadata(_ABSORB_TABLE, cache_dir)
        dims = meta.get("dims", [])
        if len(dims) < 2:
            return {}

        # Dim 0 = Geography
        geo_ord = None
        for lbl in geo_labels:
            geo_ord = _find_member_ordinal(dims, 0, [lbl])
            if geo_ord is not None:
                break
        if geo_ord is None:
            return {}

        # Dim 2 = Price range → "Total"
        price_ord: int | None = None
        if len(dims) >= 3:
            price_ord = _find_member_ordinal(dims, 2, _ABSORB_PRICE_TOTAL)
            if price_ord is None:
                members2 = dims[2].get("member", [])
                if members2:
                    price_ord = int(members2[0]["memberId"])

        result: dict = {
            "source": "statcan-34-10-0149-01",
            "ville": geo_labels[0],
        }
        periode = ""

        for field_key, searches in _ABSORB_TYPE_SEARCHES.items():
            type_ord = _find_member_ordinal(dims, 1, searches)
            if type_ord is None:
                continue

            coord = (
                _build_coordinate(geo_ord, type_ord, price_ord)
                if price_ord is not None
                else _build_coordinate(geo_ord, type_ord)
            )
            if not coord:
                continue

            try:
                # 5 quarters for annual variation
                payload = [{"productId": _ABSORB_TABLE, "coordinate": coord, "latestN": 5}]
                rows = _wds_post("getDataFromCubePidCoordAndLatestNPeriods", payload)
                if not rows:
                    continue
                pts = rows[0].get("object", {}).get("vectorDataPoint", [])
                valid = [
                    (p.get("refPer", ""), float(p["value"]))
                    for p in pts
                    if p.get("value") not in (None, "") and p.get("status") != "E"
                    and float(p["value"]) > 0
                ]
                if not valid:
                    continue
                ref_per, latest_val = valid[-1]
                result[field_key] = round(latest_val, 0)
                if field_key == "unites_absorbees_total":
                    if ref_per:
                        periode = str(ref_per)[:7]
                    if len(valid) >= 5:
                        _, prior_val = valid[0]
                        if prior_val > 0:
                            result["variation_pct_4q"] = round(
                                (latest_val - prior_val) / prior_val * 100, 1
                            )
            except Exception as exc:
                logger.debug("unites_absorbees %s skip: %s", field_key, exc)

        if "unites_absorbees_total" not in result:
            return {}

        if periode:
            result["periode"] = periode

        _write_cache_ttl(cache_path, result, _ABSORB_TTL)
        logger.debug("unites_absorbees injecté : %s total=%s",
                     city_code, result.get("unites_absorbees_total"))
        return result

    except Exception as exc:  # pragma: no cover
        logger.debug("unites_absorbees fetch failed: %s", exc)
        return {}


def fetch_mises_en_chantier(city_code: str, cache_dir: Path) -> dict:
    """
    Return housing starts for a QC CMA via StatCan WDS (34-10-0056-01).

    Returns dict with keys: total_mois, unifamilial_mois, collectif_mois,
    total_12mois, variation_pct_6m, periode, ville, source.
    Returns {} on any failure or unsupported city.
    """
    geo_labels = _CHANTIER_GEO_LABELS.get(city_code)
    if not geo_labels:
        return {}

    try:
        meta = _cube_metadata(_CHANTIER_TABLE, cache_dir)
        dims = meta.get("dims", [])
        if not dims:
            return {}

        geo_ord = _find_member_ordinal(dims, 0, geo_labels)
        if geo_ord is None:
            return {}

        # Optional extra dims (seasonal adjustment, year)
        extra_ords: list[int] = []
        for extra_dim_idx in range(2, len(dims)):
            members_ex = dims[extra_dim_idx].get("member", [])
            if members_ex:
                # Prefer "seasonally adjusted" or just take first member
                sa_ord = _find_member_ordinal(dims, extra_dim_idx,
                                              ["Seasonally adjusted",
                                               "Désaisonnalisé", "Annual rate"])
                extra_ords.append(sa_ord if sa_ord is not None
                                  else int(members_ex[0]["memberId"]))

        result: dict = {
            "source": "statcan-34-10-0056-01",
            "ville": _SCHL_TO_DISPLAY.get(city_code, city_code),
        }

        # Fetch 12-month series for total to get rolling sum + trend
        total_ord = _find_member_ordinal(dims, 1, _CHANTIER_TYPE_SEARCHES["total"])
        if total_ord is None:
            return {}

        coord_total = _build_coordinate(geo_ord, total_ord, *extra_ords)
        if coord_total:
            try:
                payload = [{"productId": _CHANTIER_TABLE,
                            "coordinate": coord_total, "latestN": 12}]
                data = _wds_post("getDataFromCubePidCoordAndLatestNPeriods", payload)
                if isinstance(data, list) and data and data[0].get("status") == "SUCCESS":
                    pts = data[0].get("object", {}).get("vectorDataPoint", [])
                    vals = []
                    for pt in pts:
                        try:
                            vals.append(float(pt["value"]))
                        except (TypeError, ValueError):
                            pass
                    if vals:
                        result["total_mois"] = vals[0]
                        result["total_12mois"] = round(sum(vals), 0)
                        ref = pts[0].get("refPer") or pts[0].get("refper") or ""
                        if ref:
                            result["periode"] = str(ref)[:7]
                        if len(vals) >= 12:
                            avg_rec  = sum(vals[:6]) / 6
                            avg_prev = sum(vals[6:12]) / 6
                            if avg_prev > 0:
                                result["variation_pct_6m"] = round(
                                    (avg_rec - avg_prev) / avg_prev * 100, 1
                                )
            except Exception:
                pass

        # Fetch latest value for sub-types (unifamilial, collectif)
        for field_key, searches in [
            ("unifamilial_mois", _CHANTIER_TYPE_SEARCHES["unifamilial"]),
            ("collectif_mois",   _CHANTIER_TYPE_SEARCHES["collectif"]),
        ]:
            type_ord = _find_member_ordinal(dims, 1, searches)
            coord = _build_coordinate(geo_ord, type_ord, *extra_ords)
            if coord:
                val = _fetch_series(_CHANTIER_TABLE, coord, cache_dir)
                if val is not None:
                    result[field_key] = val

        if len(result) <= 2:
            return {}

        return result

    except Exception as exc:  # pragma: no cover
        logger.debug("Mises en chantier fetch failed for %s: %s", city_code, exc)
        return {}


def fetch_ipc_logement(cache_dir: Path) -> dict:
    """
    Return CPI housing component + annual variation via StatCan WDS (18-10-0004-01).

    Non city-specific (Canada or Quebec aggregate).
    Returns dict with keys: ipc_total, ipc_logement, ipc_energie,
    variation_logement_pct, periode, source.
    Returns {} on any failure.
    """
    try:
        meta = _cube_metadata(_IPC_TABLE, cache_dir)
        dims = meta.get("dims", [])
        if not dims:
            return {}

        # Dim 0 = GEO — prefer Canada total
        geo_ord = _find_member_ordinal(dims, 0, _IPC_GEO_SEARCHES)
        if geo_ord is None:
            return {}

        result: dict = {"source": "statcan-18-10-0004-01"}

        for field_key, searches in _IPC_COMPONENTS.items():
            comp_ord = _find_member_ordinal(dims, 1, searches)
            if comp_ord is None:
                continue
            # Try 3-dim coordinate if extra dim present
            extra_ord: int | None = None
            if len(dims) >= 3:
                members3 = dims[2].get("member", [])
                if members3:
                    extra_ord = int(members3[0]["memberId"])
            coord = _build_coordinate(geo_ord, comp_ord,
                                      *([] if extra_ord is None else [extra_ord]))
            if not coord:
                continue
            val = _fetch_series(_IPC_TABLE, coord, cache_dir)
            if val is not None:
                result[field_key] = val

        if "ipc_logement" not in result:
            return {}

        # Compute annual variation for logement component using latestN=13
        comp_ord_log = _find_member_ordinal(dims, 1, _IPC_COMPONENTS["ipc_logement"])
        extra_ord2: int | None = None
        if len(dims) >= 3:
            members3 = dims[2].get("member", [])
            if members3:
                extra_ord2 = int(members3[0]["memberId"])
        coord_log = _build_coordinate(geo_ord, comp_ord_log,
                                      *([] if extra_ord2 is None else [extra_ord2]))
        if coord_log:
            try:
                payload = [{"productId": _IPC_TABLE, "coordinate": coord_log,
                            "latestN": 13}]
                data = _wds_post("getDataFromCubePidCoordAndLatestNPeriods", payload)
                if isinstance(data, list) and data and data[0].get("status") == "SUCCESS":
                    pts = data[0].get("object", {}).get("vectorDataPoint", [])
                    if pts:
                        ref = pts[0].get("refPer") or pts[0].get("refper") or ""
                        if ref:
                            result["periode"] = str(ref)[:7]
                    if len(pts) >= 13:
                        latest = float(pts[0]["value"])
                        year_ago = float(pts[12]["value"])
                        if year_ago > 0:
                            result["variation_logement_pct"] = round(
                                (latest - year_ago) / year_ago * 100, 1
                            )
            except Exception:
                pass

        return result

    except Exception as exc:  # pragma: no cover
        logger.debug("IPC fetch failed: %s", exc)
        return {}


def fetch_population_growth(city_code: str, cache_dir: Path) -> dict:
    """
    Return population estimate + annual growth for a QC CMA via StatCan WDS (17-10-0135-01).

    Returns dict with keys: population, variation_annuelle_pct, annee, ville, source.
    Returns {} on any failure or unsupported city.
    """
    geo_labels = _POP_GEO_LABELS.get(city_code)
    if not geo_labels:
        return {}

    try:
        meta = _cube_metadata(_POP_TABLE, cache_dir)
        dims = meta.get("dims", [])
        if not dims:
            return {}

        # Dim 0 = GEO
        geo_ord = _find_member_ordinal(dims, 0, geo_labels)
        if geo_ord is None:
            return {}

        # Dim 1 = Age group → Total / All ages
        age_ord = _find_member_ordinal(dims, 1,
                                       ["Total - all ages", "All ages", "Total"])

        # Dim 2 = Sex → Both sexes / Total
        sex_ord = _find_member_ordinal(dims, 2,
                                       ["Both sexes", "Total - sex", "Total"])

        # Optional dim 3 (estimate type: low/medium/high) → prefer medium or first member
        extra_ord: int | None = None
        if len(dims) >= 4:
            extra_ord = _find_member_ordinal(dims, 3,
                                             ["Medium", "medium projection", "Estimate"])
            if extra_ord is None:
                members = dims[3].get("member", [])
                if members:
                    extra_ord = int(members[0]["memberId"])

        coord = _build_coordinate(geo_ord, age_ord, sex_ord,
                                  *([] if extra_ord is None else [extra_ord]))
        if not coord:
            return {}

        # Fetch 2 years (latestN=2) to compute annual change
        payload = [{"productId": _POP_TABLE, "coordinate": coord, "latestN": 2}]
        data = _wds_post("getDataFromCubePidCoordAndLatestNPeriods", payload)
        if not isinstance(data, list) or not data or data[0].get("status") != "SUCCESS":
            return {}

        pts = data[0].get("object", {}).get("vectorDataPoint", [])
        if not pts:
            return {}

        try:
            latest_val = float(pts[0]["value"])
        except (TypeError, ValueError, KeyError):
            return {}

        result: dict = {
            "source": "statcan-17-10-0135-01",
            "ville": _SCHL_TO_DISPLAY.get(city_code, city_code),
            "population": round(latest_val),
        }

        ref = pts[0].get("refPer") or pts[0].get("refper") or ""
        if ref:
            result["annee"] = str(ref)[:4]

        if len(pts) >= 2:
            try:
                prior_val = float(pts[1]["value"])
                if prior_val > 0:
                    result["variation_annuelle_pct"] = round(
                        (latest_val - prior_val) / prior_val * 100, 2
                    )
            except (TypeError, ValueError, KeyError):
                pass

        return result

    except Exception as exc:  # pragma: no cover
        logger.debug("Population growth fetch failed for %s: %s", city_code, exc)
        return {}


_BEDROOM_SEARCHES: dict[str, list[str]] = {
    "bachelor": ["bachelor", "studio"],
    "1ch": ["1 bedroom", "1 chambre"],
    "2ch": ["2 bedroom", "2 chambre"],
    "3ch_plus": ["3 bedroom", "3 chambre", "3+"],
    "total": ["total"],
}


def fetch_rental_market(city_code: str, cache_dir: Path) -> dict:
    """
    Return SCHL rental market data for a QC city via StatCan WDS.

    Returns dict with keys: loyer_moyen_{bachelor,1ch,2ch,3ch_plus,total},
    taux_inoccupation_total, annee, ville, source.
    Returns {} on any failure.
    """
    geo_label = _SCHL_TO_STATCAN_GEO.get(city_code)
    if not geo_label:
        return {}

    try:
        meta = _cube_metadata(_SCHL_TABLE, cache_dir)
        dims = meta.get("dims", [])
        if not dims:
            return {}

        # dim 0 = GEO, dim 1 = Type of unit
        geo_ord = _find_member_ordinal(dims, 0, [geo_label, city_code])
        if geo_ord is None:
            return {}

        result: dict = {
            "source": "statcan-34-10-0133-01",
            "ville": _SCHL_TO_DISPLAY.get(city_code, city_code),
        }

        # Average Rent series (survey index 1 usually covers primary rental)
        # Table may have a 3rd dim for survey type; try dim 2 = 1 as default
        extra_ord: list[int] = []
        if len(dims) >= 3:
            # Try to find "Private apartments" or first member
            members = dims[2].get("member", [])
            if members:
                extra_ord = [int(members[0]["memberId"])]

        # Vacancy Rate uses a different table (SCHL 34-10-0031) — skip for V0
        # We only parse Average Rent here

        for field_key, searches in _BEDROOM_SEARCHES.items():
            unit_ord = _find_member_ordinal(dims, 1, searches)
            coord = _build_coordinate(geo_ord, unit_ord, *extra_ord if extra_ord else [])
            if coord:
                val = _fetch_series(_SCHL_TABLE, coord, cache_dir)
                if val is not None:
                    result[f"loyer_moyen_{field_key}"] = val

        if len(result) <= 2:  # only source + ville
            return {}

        return result

    except Exception as exc:  # pragma: no cover
        logger.debug("SCHL fetch failed for %s: %s", city_code, exc)
        return {}


def fetch_vacancy_rate(city_code: str, cache_dir: Path) -> dict:
    """
    Return SCHL rental vacancy rates for a QC city via StatCan WDS (34-10-0131-01).

    Returns dict with keys: taux_total_pct, taux_bachelor_pct, taux_1ch_pct,
    taux_2ch_pct, taux_3ch_plus_pct, annee, ville, source.
    Returns {} on any failure or unsupported city.
    """
    geo_label = _SCHL_TO_STATCAN_GEO.get(city_code)
    if not geo_label:
        return {}

    try:
        meta = _cube_metadata(_VACANCE_TABLE, cache_dir)
        dims = meta.get("dims", [])
        if not dims:
            return {}

        # dim 0 = GEO, dim 1 = Type of unit
        geo_ord = _find_member_ordinal(dims, 0, [geo_label, city_code])
        if geo_ord is None:
            return {}

        result: dict = {
            "source": "statcan-34-10-0131-01",
            "ville": _SCHL_TO_DISPLAY.get(city_code, city_code),
        }

        # Optional dim 2 (survey type) — take first member if present
        extra_ord: list[int] = []
        if len(dims) >= 3:
            members = dims[2].get("member", [])
            if members:
                extra_ord = [int(members[0]["memberId"])]

        for field_key, searches in _VACANCE_UNIT_SEARCHES.items():
            unit_ord = _find_member_ordinal(dims, 1, searches)
            coord = _build_coordinate(geo_ord, unit_ord, *extra_ord if extra_ord else [])
            if coord:
                val = _fetch_series(_VACANCE_TABLE, coord, cache_dir)
                if val is not None:
                    result[f"taux_{field_key}_pct"] = val

        if len(result) <= 2:
            return {}

        # Try to capture reference period (year) from first successful series fetch
        if "taux_total_pct" in result:
            try:
                coord_total = _build_coordinate(
                    geo_ord,
                    _find_member_ordinal(dims, 1, _VACANCE_UNIT_SEARCHES["total"]),
                    *extra_ord if extra_ord else [],
                )
                if coord_total:
                    payload = [{"productId": _VACANCE_TABLE, "coordinate": coord_total, "latestN": 1}]
                    data = _wds_post("getDataFromCubePidCoordAndLatestNPeriods", payload)
                    if isinstance(data, list) and data and data[0].get("status") == "SUCCESS":
                        pts = data[0].get("object", {}).get("vectorDataPoint", [])
                        if pts:
                            ref = pts[0].get("refPer") or pts[0].get("refper") or ""
                            if ref:
                                result["annee"] = str(ref)[:4]
            except Exception:
                pass

        return result

    except Exception as exc:  # pragma: no cover
        logger.debug("Vacancy rate fetch failed for %s: %s", city_code, exc)
        return {}


def fetch_nhpi(city_code: str, cache_dir: Path) -> dict:
    """
    Return NHPI (New Housing Price Index) for a QC city via StatCan WDS.

    Returns dict with keys: indice_total, indice_batiment, indice_terrain,
    variation_annuelle_pct (if 12 prior periods available), ville, source.
    Returns {} on any failure or unsupported city.
    """
    geo_labels = _NHPI_GEO_LABELS.get(city_code)
    if not geo_labels:
        return {}

    try:
        meta = _cube_metadata(_NHPI_TABLE, cache_dir)
        dims = meta.get("dims", [])
        if not dims:
            return {}

        # dim 0 = GEO, dim 1 = Type of unit/structure
        geo_ord = _find_member_ordinal(dims, 0, geo_labels)
        if geo_ord is None:
            return {}

        result: dict = {
            "source": "statcan-18-10-0205-01",
            "ville": _SCHL_TO_DISPLAY.get(city_code, city_code),
        }

        for field_key, searches in _NHPI_TYPE_SEARCHES.items():
            type_ord = _find_member_ordinal(dims, 1, searches)
            coord = _build_coordinate(geo_ord, type_ord)
            if coord:
                val = _fetch_series(_NHPI_TABLE, coord, cache_dir)
                if val is not None:
                    result[f"indice_{field_key}"] = val

        if len(result) <= 2:
            return {}

        # Compute annual change using a second series fetch (latestN=13, compare first vs last)
        total_ord = _find_member_ordinal(dims, 1, _NHPI_TYPE_SEARCHES["total"])
        coord_total = _build_coordinate(geo_ord, total_ord)
        if coord_total:
            try:
                payload = [{"productId": _NHPI_TABLE, "coordinate": coord_total, "latestN": 13}]
                data = _wds_post("getDataFromCubePidCoordAndLatestNPeriods", payload)
                if isinstance(data, list) and data and data[0].get("status") == "SUCCESS":
                    points = data[0].get("object", {}).get("vectorDataPoint", [])
                    if len(points) >= 13:
                        latest = float(points[0]["value"])
                        year_ago = float(points[12]["value"])
                        if year_ago > 0:
                            result["variation_annuelle_pct"] = round(
                                (latest - year_ago) / year_ago * 100, 1
                            )
            except Exception:
                pass

        return result

    except Exception as exc:  # pragma: no cover
        logger.debug("NHPI fetch failed for %s: %s", city_code, exc)
        return {}


def fetch_permis_construction(city_code: str, cache_dir: Path) -> dict:
    """
    Return building permit activity for a QC city via StatCan WDS (34-10-0066-01).

    Returns dict with keys:
      - unites_residentielles_mois  : latest month (new residential units)
      - unites_residentielles_12mois: rolling 12-month sum
      - variation_pct_6m            : (avg last 6m / avg prior 6m - 1) × 100
      - valeur_permis_k_mois        : latest month value (k$) if available
      - periode                     : YYYY-MM label of latest data point
      - ville, source
    Returns {} on any failure or unsupported city.
    """
    geo_labels = _PERMIS_GEO_LABELS.get(city_code)
    if not geo_labels:
        return {}

    try:
        meta = _cube_metadata(_PERMIS_TABLE, cache_dir)
        dims = meta.get("dims", [])
        if not dims:
            return {}

        # Dim 0 = GEO
        geo_ord = _find_member_ordinal(dims, 0, geo_labels)
        if geo_ord is None:
            return {}

        # Dim 1 = Type of structure  →  Residential
        struct_ord = _find_member_ordinal(dims, 1, _PERMIS_STRUCTURE_SEARCHES)
        if struct_ord is None:
            return {}

        # Dim 2 = Type of work  →  New construction (preferred) or All work
        work_ord_new = _find_member_ordinal(dims, 2, _PERMIS_WORK_SEARCHES_NEW)
        work_ord_all = _find_member_ordinal(dims, 2, _PERMIS_WORK_SEARCHES_ALL)
        work_ord = work_ord_new if work_ord_new is not None else work_ord_all
        if work_ord is None:
            return {}

        # Optional dim 3 = measure (units vs value)
        unit_ord: int | None = None
        value_ord: int | None = None
        if len(dims) >= 4:
            unit_ord  = _find_member_ordinal(dims, 3, _PERMIS_UNIT_SEARCHES)
            value_ord = _find_member_ordinal(dims, 3, _PERMIS_VALUE_SEARCHES)

        # Build coordinates
        coord_units = _build_coordinate(geo_ord, struct_ord, work_ord, unit_ord)
        coord_value = _build_coordinate(geo_ord, struct_ord, work_ord, value_ord)

        # Fallback: 3-dim coordinate if dim 3 not present
        if coord_units is None:
            coord_units = _build_coordinate(geo_ord, struct_ord, work_ord)
        if coord_value is None and value_ord is not None:
            coord_value = _build_coordinate(geo_ord, struct_ord, work_ord_all, value_ord)

        result: dict = {
            "source": "statcan-34-10-0066-01",
            "ville": _SCHL_TO_DISPLAY.get(city_code, city_code),
        }

        # Fetch 12-month series for units
        if coord_units:
            try:
                payload = [{"productId": _PERMIS_TABLE, "coordinate": coord_units, "latestN": 12}]
                data = _wds_post("getDataFromCubePidCoordAndLatestNPeriods", payload)
                if isinstance(data, list) and data and data[0].get("status") == "SUCCESS":
                    pts = data[0].get("object", {}).get("vectorDataPoint", [])
                    values = []
                    for pt in pts:
                        try:
                            values.append(float(pt["value"]))
                        except (TypeError, ValueError):
                            pass
                    if values:
                        result["unites_residentielles_mois"] = values[0]
                        result["unites_residentielles_12mois"] = round(sum(values), 0)
                        # Ref period label from first point
                        ref = pts[0].get("refPer") or pts[0].get("refper") or ""
                        if ref:
                            result["periode"] = str(ref)[:7]  # YYYY-MM
                        # 6-month variation
                        if len(values) >= 12:
                            avg_rec  = sum(values[:6]) / 6
                            avg_prev = sum(values[6:12]) / 6
                            if avg_prev > 0:
                                result["variation_pct_6m"] = round(
                                    (avg_rec - avg_prev) / avg_prev * 100, 1
                                )
            except Exception:
                pass

        # Fetch latest value of permits (k$)
        if coord_value:
            try:
                val = _fetch_series(_PERMIS_TABLE, coord_value, cache_dir)
                if val is not None:
                    result["valeur_permis_k_mois"] = val
            except Exception:
                pass

        if len(result) <= 2:
            return {}

        return result

    except Exception as exc:  # pragma: no cover
        logger.debug("Permis construction fetch failed for %s: %s", city_code, exc)
        return {}


# ── Rôle municipal Montréal CSV ───────────────────────────────────────────────

_ROLE_MTL_CSV_URL = (
    "https://donnees.montreal.ca/dataset/4ad6baea-4d2c-460f-a8bf-5d000db498f7"
    "/resource/2b9dfc3d-91d3-48de-b32c-a2a6d9417079/download/uniteevaluationfonciere.csv"
)
_ROLE_INDEX_CACHE: dict[str, dict] = {}  # module-level in-process cache


def download_role_mtl(cache_dir: Path, force: bool = False) -> Path:
    """Download the Montréal rôle CSV (~72 MB) once and cache it."""
    import httpx  # type: ignore
    csv_path = cache_dir / "role_mtl.csv"
    if csv_path.exists() and not force:
        return csv_path
    cache_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Téléchargement rôle Montréal CSV (~72 MB)…")
    with httpx.stream("GET", _ROLE_MTL_CSV_URL, timeout=300, follow_redirects=True) as r:
        r.raise_for_status()
        with csv_path.open("wb") as fh:
            for chunk in r.iter_bytes(chunk_size=256 * 1024):
                fh.write(chunk)
    logger.info("Rôle Montréal téléchargé : %s", csv_path)
    return csv_path


def _load_role_index(csv_path: Path) -> dict[str, dict]:
    """Load CSV into module-level dict indexed by MATRICULE83 (lazy, once per process)."""
    global _ROLE_INDEX_CACHE
    key = str(csv_path)
    if key in _ROLE_INDEX_CACHE:
        return _ROLE_INDEX_CACHE[key]
    idx: dict[str, dict] = {}
    address_idx: dict[str, list[dict]] = {}
    with csv_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mat = row.get("MATRICULE83", "").strip()
            if mat:
                idx[mat] = row
            # Secondary index: (civique_debut, nom_rue)
            civique = row.get("CIVIQUE_DEBUT", "").strip()
            rue = _norm(row.get("NOM_RUE", ""))
            addr_key = f"{civique}|{rue}"
            address_idx.setdefault(addr_key, []).append(row)
    _ROLE_INDEX_CACHE[key] = {"matricule": idx, "address": address_idx}
    return _ROLE_INDEX_CACHE[key]


def _parse_civic_from_display(display_name: str) -> tuple[str, str]:
    """Extract (civic_number, street_name) from a free-text address best-effort."""
    import re
    m = re.match(r"^\s*(\d+)\s+(.+?)(?:\s*,.*)?$", display_name.strip())
    if m:
        return m.group(1).strip(), _norm(m.group(2).strip())
    return "", _norm(display_name.strip())


def lookup_role_mtl(
    csv_path: Path,
    matricule: str | None = None,
    display_name: str = "",
) -> dict:
    """
    Look up a property in the Montréal rôle CSV.

    Attempts lookup by MATRICULE83 first; falls back to civic + street.
    Returns {} if not found or CSV absent.
    """
    if not csv_path.exists():
        return {}
    try:
        idx = _load_role_index(csv_path)
    except Exception as exc:
        logger.debug("Role CSV load failed: %s", exc)
        return {}

    row: dict | None = None

    # 1. By matricule
    if matricule:
        mat_norm = matricule.strip().upper()
        row = idx["matricule"].get(mat_norm)

    # 2. By civic + street from display_name
    if row is None and display_name:
        civic, street = _parse_civic_from_display(display_name)
        if civic and street:
            addr_key = f"{civic}|{street}"
            candidates = idx["address"].get(addr_key, [])
            if candidates:
                row = candidates[0]

    if row is None:
        return {}

    def _int(v: str) -> int | None:
        try:
            return int(v) if v and v.strip() not in ("0", "") else None
        except (ValueError, TypeError):
            return None

    def _float(v: str) -> float | None:
        try:
            return float(v) if v and v.strip() not in ("0", "0.0", "") else None
        except (ValueError, TypeError):
            return None

    return {
        "source": "role-mtl-csv",
        "matricule83": row.get("MATRICULE83", ""),
        "adresse_civique": row.get("CIVIQUE_DEBUT", ""),
        "nom_rue": row.get("NOM_RUE", ""),
        "annee_construction": _int(row.get("ANNEE_CONSTRUCTION", "")),
        "superficie_batiment_m2": _float(row.get("SUPERFICIE_BATIMENT", "")),
        "superficie_terrain_m2": _float(row.get("SUPERFICIE_TERRAIN", "")),
        "nb_logements": _int(row.get("NOMBRE_LOGEMENT", "")),
        "code_cubf": _int(row.get("CODE_UTILISATION", "")),
        "libelle_cubf": row.get("LIBELLE_UTILISATION", ""),
        "municipalite": row.get("MUNICIPALITE", ""),
        "etages": _int(row.get("ETAGE_HORS_SOL", "")),
    }


# ── Rôle municipal XML (autres villes — MAMH XML → JSON index) ───────────────

# city_code → (code_geo, display_name, xml_url)
_ROLE_XML_CITIES: dict[str, tuple[str, str, str]] = {
    "quebec":       ("23027", "Ville de Québec",
                     "https://donneesouvertes.affmunqc.net/role/RL23027_2026.xml"),
    "laval":        ("65005", "Laval",
                     "https://donneesouvertes.affmunqc.net/role/RL65005_2026.xml"),
    "longueuil":    ("58227", "Longueuil",
                     "https://donneesouvertes.affmunqc.net/role/RL58227_2026.xml"),
    "gatineau":     ("81017", "Gatineau",
                     "https://donneesouvertes.affmunqc.net/role/RL81017_2026.xml"),
    "sherbrooke":   ("43027", "Sherbrooke",
                     "https://donneesouvertes.affmunqc.net/role/RL43027_2026.xml"),
}

# in-process cache for loaded XML indexes
_XML_INDEX_CACHE: dict[str, dict] = {}


def download_role_xml(city_code: str, cache_dir: Path, force: bool = False) -> Path | None:
    """Download MAMH XML for a non-Montreal city (100–400 MB). Returns path or None."""
    import httpx  # type: ignore
    info = _ROLE_XML_CITIES.get(city_code)
    if not info:
        return None
    code_geo, city_name, url = info
    xml_path = cache_dir / f"role_{city_code}.xml"
    if xml_path.exists() and not force:
        return xml_path
    cache_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Téléchargement rôle %s XML…", city_name)
    with httpx.stream("GET", url, timeout=600, follow_redirects=True) as r:
        r.raise_for_status()
        with xml_path.open("wb") as fh:
            for chunk in r.iter_bytes(chunk_size=256 * 1024):
                fh.write(chunk)
    logger.info("Rôle %s téléchargé : %s", city_name, xml_path)
    return xml_path


def _xml_text(elem, tag: str) -> str | None:
    """Extract text from a direct child tag; return None if absent/empty."""
    child = elem.find(tag)
    if child is None:
        return None
    t = (child.text or "").strip()
    return t or None


def _xml_int(elem, tag: str) -> int | None:
    t = _xml_text(elem, tag)
    if t is None:
        return None
    try:
        v = int(t)
        return v if v != 0 else None
    except ValueError:
        return None


def _xml_float(elem, tag: str) -> float | None:
    t = _xml_text(elem, tag)
    if t is None:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def _xml_build_matricule(a: str | None, b: str | None, c: str | None, d: str | None,
                          e: str | None = None, f: str | None = None) -> str | None:
    if not all([a, b, c, d]):
        return None
    try:
        sub1 = int(e) if e else 0
        sub2 = int(f) if f else 0
        return f"{int(a):04d}-{int(b):02d}-{int(c):04d}-{d}-{sub1:03d}-{sub2:04d}"
    except (ValueError, TypeError):
        return None


def build_role_xml_index(xml_path: Path, index_path: Path, city_code: str = "") -> int:
    """
    Parse a MAMH XML file (iterparse) and write a compact JSON index.

    Index structure:
      {
        "by_matricule": {"XXXX-YY-ZZZZ-W-000-0000": {...record...}},
        "by_address":   {"1000|rue sherbrooke o": [{...record...}]},
        "city_code": "...",
        "_built_at": <timestamp>,
      }

    Returns the number of UEVs indexed.
    """
    from xml.etree import ElementTree as ET

    logger.info("Building XML index for %s → %s", xml_path.name, index_path.name)
    by_matricule: dict[str, dict] = {}
    by_address: dict[str, list[dict]] = {}
    count = 0

    for _event, elem in ET.iterparse(str(xml_path), events=("end",)):
        if elem.tag != "RLUEx":
            continue  # do NOT clear sub-elements before RLUEx is processed

        # Adresse
        addr_parent = elem.find("RL0101")
        addr = addr_parent.find("RL0101x") if addr_parent is not None else None
        civique = _xml_text(addr, "RL0101Ax") if addr is not None else None
        nom_voie = _xml_text(addr, "RL0101Gx") if addr is not None else None
        type_voie = _xml_text(addr, "RL0101Ex") if addr is not None else None

        # Matricule
        rl0104 = elem.find("RL0104")
        mat = _xml_build_matricule(
            _xml_text(rl0104, "RL0104A") if rl0104 is not None else None,
            _xml_text(rl0104, "RL0104B") if rl0104 is not None else None,
            _xml_text(rl0104, "RL0104C") if rl0104 is not None else None,
            _xml_text(rl0104, "RL0104D") if rl0104 is not None else None,
            _xml_text(rl0104, "RL0104E") if rl0104 is not None else None,
            _xml_text(rl0104, "RL0104F") if rl0104 is not None else None,
        ) if rl0104 is not None else None

        # Lot
        rl0103_parent = elem.find("RL0103")
        rl0103x = rl0103_parent.find("RL0103x") if rl0103_parent is not None else None

        rec: dict = {
            "source": "mamh-xml",
            "city_code": city_code,
            "matricule83": mat or "",
            "adresse_civique": civique or "",
            "nom_rue": f"{type_voie or ''} {nom_voie or ''}".strip(),
            "no_lot": _xml_int(rl0103x, "RL0103Ax") if rl0103x is not None else None,
            "annee_construction": _xml_int(elem, "RL0307A"),
            "superficie_batiment_m2": _xml_float(elem, "RL0308A"),
            "superficie_terrain_m2": _xml_float(elem, "RL0302A"),
            "nb_logements": _xml_int(elem, "RL0311A") or 0,
            "code_cubf": _xml_int(elem, "RL0105A"),
            "valeur_terrain": _xml_float(elem, "RL0402A"),
            "valeur_batiment": _xml_float(elem, "RL0403A"),
            "valeur_totale": _xml_float(elem, "RL0404A"),
            "valeur_imposable": _xml_float(elem, "RL0405A"),
        }

        if mat:
            by_matricule[mat.upper()] = rec

        if civique and nom_voie:
            addr_key = f"{civique}|{_norm(f'{type_voie or ''} {nom_voie}')}"
            by_address.setdefault(addr_key, []).append(rec)

        count += 1
        if count % 50_000 == 0:
            logger.info("  %d UEV indexées…", count)

        elem.clear()

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps({
            "by_matricule": by_matricule,
            "by_address": by_address,
            "city_code": city_code,
            "_built_at": time.time(),
            "_count": count,
        }, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Index built: %d UEVs → %s (%.1f MB)",
                count, index_path.name, index_path.stat().st_size / 1e6)
    return count


def _load_xml_index(index_path: Path) -> dict:
    """Load XML JSON index; module-level cache (one load per process)."""
    key = str(index_path)
    if key in _XML_INDEX_CACHE:
        return _XML_INDEX_CACHE[key]
    data = json.loads(index_path.read_text(encoding="utf-8"))
    _XML_INDEX_CACHE[key] = data
    return data


def lookup_role_xml(
    index_path: Path,
    matricule: str | None = None,
    display_name: str = "",
) -> dict:
    """Look up a property in a MAMH XML index (JSON). Returns {} if not found."""
    if not index_path.exists():
        return {}
    try:
        idx = _load_xml_index(index_path)
    except Exception as exc:
        logger.debug("XML index load failed: %s", exc)
        return {}

    by_mat = idx.get("by_matricule", {})
    by_addr = idx.get("by_address", {})

    row: dict | None = None

    if matricule:
        row = by_mat.get(matricule.strip().upper())

    if row is None and display_name:
        civic, street = _parse_civic_from_display(display_name)
        if civic and street:
            addr_key = f"{civic}|{street}"
            candidates = by_addr.get(addr_key, [])
            if candidates:
                row = candidates[0]

    return row or {}


# ── Geocoding (Nominatim OSM) ─────────────────────────────────────────────────

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_GEOCODE_TTL = 7 * 86_400  # 7 days


def _geocode_cache_path(display_name: str, cache_dir: Path) -> Path:
    import hashlib
    key = hashlib.md5(display_name.encode("utf-8")).hexdigest()[:12]
    return cache_dir / f"geo_{key}.json"


def geocode_address(display_name: str, cache_dir: Path) -> tuple[float, float] | None:
    """
    Geocode via Nominatim OSM. Returns (lat, lng) or None. Cache 7 days.

    Appends ', Québec, Canada' when city not explicit, to bias results.
    Respects Nominatim's 1 req/s policy — caller must not hammer this.
    """
    import httpx  # type: ignore

    cp = _geocode_cache_path(display_name, cache_dir)
    if cp.exists():
        try:
            d = json.loads(cp.read_text(encoding="utf-8"))
            if time.time() - d.get("_ts", 0) < _GEOCODE_TTL:
                lat, lng = d.get("lat"), d.get("lng")
                if lat is not None and lng is not None:
                    return float(lat), float(lng)
                return None  # cached "not found"
        except Exception:
            pass

    query = display_name.strip()
    low = query.lower()
    if "québec" not in low and "quebec" not in low and "canada" not in low:
        query += ", Québec, Canada"

    try:
        r = httpx.get(
            _NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": 1},
            headers={"User-Agent": "eval-immo/1.0 contact=eval-immo@example.com"},
            timeout=_HTTP_TIMEOUT,
            follow_redirects=True,
        )
        r.raise_for_status()
        results = r.json()
    except Exception as exc:
        logger.debug("geocode_address HTTP failed: %s", exc)
        return None

    if not results:
        # Cache negative result
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_text(json.dumps({"_ts": time.time(), "lat": None, "lng": None}),
                      encoding="utf-8")
        return None

    lat = float(results[0]["lat"])
    lng = float(results[0]["lon"])
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps({"_ts": time.time(), "lat": lat, "lng": lng}),
                  encoding="utf-8")
    return lat, lng


# ── Zonage urbanisme (GeoJSON open data + PiP) ────────────────────────────────

# city_code → CKAN config + rough bounding box [minlng, minlat, maxlng, maxlat]
_ZONING_CITIES: dict[str, dict] = {
    "montreal": {
        "ckan_api": "https://donnees.montreal.ca/api/3/action",
        # Try multiple package IDs (open data slugs may change)
        "package_ids": ["zones-urbanistiques", "zonage", "plan-urbanisme-zones"],
        "bbox": [-74.05, 45.39, -73.45, 45.75],
    },
    "quebec": {
        # Ville de Québec — portail données ouvertes provincial
        "ckan_api": "https://www.donneesquebec.ca/api/3/action",
        "package_ids": [
            "vmqc-plan-zonage",
            "plan-de-zonage-ville-de-quebec",
            "zonage-ville-de-quebec",
            "plan-zonage",
        ],
        "bbox": [-71.55, 46.70, -71.10, 47.05],
    },
    "laval": {
        "ckan_api": "https://www.donneesouvertes.laval.ca/api/3/action",
        "package_ids": ["plan-urbanisme-zonage", "zonage-laval", "plan-zonage"],
        "bbox": [-73.92, 45.49, -73.58, 45.68],
    },
    "longueuil": {
        # Longueuil — portail propriétaire (URL directe, pas CKAN standardisé)
        "ckan_api": None,
        "package_ids": [],
        "direct_url": "https://donneesouvertes.longueuil.quebec/datasets/zonage.geojson",
        "bbox": [-73.60, 45.46, -73.41, 45.58],
    },
    "gatineau": {
        "ckan_api": "https://www.donneesouvertes.gatineau.ca/api/3/action",
        "package_ids": ["zonage-gatineau", "plan-urbanisme-zonage", "reglements-zonage"],
        "bbox": [-76.15, 45.38, -75.55, 45.65],
    },
    "sherbrooke": {
        "ckan_api": "https://www.donneesouvertes.sherbrooke.ca/api/3/action",
        "package_ids": ["plan-urbanisme-zones", "zonage-sherbrooke", "plan-zonage"],
        "bbox": [-72.00, 45.35, -71.78, 45.55],
    },
}

# module-level spatial index cache: city_code → list[zone_record]
_ZONING_INDEX_CACHE: dict[str, list] = {}


def _find_ckan_geojson(ckan_api: str, package_id: str) -> str | None:
    """Find first GeoJSON resource URL in a CKAN package."""
    import httpx  # type: ignore
    r = httpx.get(f"{ckan_api}/package_show",
                  params={"id": package_id}, timeout=10, follow_redirects=True)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        return None
    for res in data["result"].get("resources", []):
        fmt = (res.get("format") or "").lower()
        url = res.get("url", "")
        if "geojson" in fmt or url.lower().endswith(".geojson"):
            return url
    return None


def download_zoning_geojson(city_code: str, cache_dir: Path, force: bool = False) -> Path | None:
    """
    Download zoning GeoJSON for a city.

    Discovery order:
      1. CKAN API (package_ids list) — for cities with a CKAN portal
      2. direct_url — for cities with a stable direct GeoJSON endpoint
    Returns local path or None if unavailable.
    """
    import httpx  # type: ignore

    city = _ZONING_CITIES.get(city_code)
    if not city:
        return None

    geojson_path = cache_dir / f"zoning_{city_code}.geojson"
    if geojson_path.exists() and not force:
        return geojson_path

    # 1. CKAN discovery
    url: str | None = None
    ckan_api = city.get("ckan_api")
    if ckan_api:
        for pkg_id in city.get("package_ids", []):
            try:
                url = _find_ckan_geojson(ckan_api, pkg_id)
                if url:
                    break
            except Exception as exc:
                logger.debug("CKAN discovery %s / %s failed: %s", city_code, pkg_id, exc)

    # 2. Fallback: direct_url
    if not url:
        url = city.get("direct_url")

    if not url:
        logger.debug("No GeoJSON URL found for zoning %s", city_code)
        return None

    logger.info("Downloading zoning GeoJSON %s …", city_code)
    cache_dir.mkdir(parents=True, exist_ok=True)
    try:
        with httpx.stream("GET", url, timeout=300, follow_redirects=True) as r:
            r.raise_for_status()
            with geojson_path.open("wb") as fh:
                for chunk in r.iter_bytes(chunk_size=256 * 1024):
                    fh.write(chunk)
    except Exception as exc:
        logger.debug("Zoning download failed: %s", exc)
        if geojson_path.exists():
            geojson_path.unlink()
        return None

    logger.info("Zoning %s downloaded: %.1f MB", city_code,
                geojson_path.stat().st_size / 1e6)
    return geojson_path


def _simplify_ring(ring: list, max_pts: int = 300) -> list:
    """Downsample a coordinate ring to at most max_pts vertices."""
    if len(ring) <= max_pts:
        return ring
    step = len(ring) / max_pts
    return [ring[int(i * step)] for i in range(max_pts)]


def _pip_exterior(lng: float, lat: float, ring: list) -> bool:
    """
    Ray casting point-in-polygon test.
    ring: list of [lng, lat] pairs (GeoJSON coordinate order).
    Exterior ring only — holes are ignored (acceptable for zoning lookups).
    """
    x, y = lng, lat
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y):
            denom = yj - yi
            if denom == 0.0:
                denom = 1e-15
            if x < (xj - xi) * (y - yi) / denom + xi:
                inside = not inside
        j = i
    return inside


def build_zoning_index(geojson_path: Path, index_path: Path) -> int:
    """
    Parse a GeoJSON zoning file and write a compact spatial index.

    Index structure (JSON):
      {
        "zones": [
          {
            "props": {<original GeoJSON properties>},
            "bbox":  [minlng, minlat, maxlng, maxlat],
            "ring":  [[lng, lat], ...],   # simplified exterior ring
          },
          ...
        ],
        "_built_at": <timestamp>,
        "_count": <int>,
      }

    Only Polygon / MultiPolygon geometries are indexed.
    Returns the number of zones indexed.
    """
    data = json.loads(geojson_path.read_text(encoding="utf-8"))
    features = data.get("features") or []
    zones: list[dict] = []

    for feat in features:
        geom = feat.get("geometry") or {}
        props = feat.get("properties") or {}
        gtype = geom.get("type", "")

        if gtype == "Polygon":
            polys = [geom["coordinates"]]
        elif gtype == "MultiPolygon":
            polys = geom["coordinates"]
        else:
            continue

        for poly in polys:
            if not poly:
                continue
            exterior = poly[0]
            if len(exterior) < 3:
                continue
            xs = [p[0] for p in exterior]
            ys = [p[1] for p in exterior]
            bbox = [min(xs), min(ys), max(xs), max(ys)]
            zones.append({
                "props": props,
                "bbox": bbox,
                "ring": _simplify_ring(exterior),
            })

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps({"zones": zones, "_built_at": time.time(), "_count": len(zones)},
                   ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Zoning index built: %d zones → %s (%.1f MB)",
                len(zones), index_path.name, index_path.stat().st_size / 1e6)
    return len(zones)


def lookup_zoning_point(city_code: str, lat: float, lng: float, cache_dir: Path) -> dict:
    """
    Return zone properties for the point (lat, lng) in the given city.

    Auto-downloads GeoJSON and builds index if not cached.
    Returns {} if not found, city unsupported, or any failure.
    """
    if city_code not in _ZONING_CITIES:
        return {}

    index_path = cache_dir / f"zoning_{city_code}_index.json"

    # Build index from GeoJSON if needed
    if not index_path.exists():
        geojson_path = cache_dir / f"zoning_{city_code}.geojson"
        if not geojson_path.exists():
            try:
                geojson_path = download_zoning_geojson(city_code, cache_dir)
            except Exception as exc:
                logger.debug("Zoning download skip: %s", exc)
                return {}
        if geojson_path and geojson_path.exists():
            try:
                build_zoning_index(geojson_path, index_path)
            except Exception as exc:
                logger.debug("Zoning index build skip: %s", exc)
                return {}

    if not index_path.exists():
        return {}

    # Load index into module-level cache
    global _ZONING_INDEX_CACHE
    key = str(index_path)
    if key not in _ZONING_INDEX_CACHE:
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
            _ZONING_INDEX_CACHE[key] = data.get("zones", [])
        except Exception as exc:
            logger.debug("Zoning index load failed: %s", exc)
            return {}

    zones = _ZONING_INDEX_CACHE[key]

    # Spatial lookup: bbox pre-filter → PiP on exterior ring
    for zone in zones:
        bbox = zone["bbox"]
        if not (bbox[0] <= lng <= bbox[2] and bbox[1] <= lat <= bbox[3]):
            continue
        if _pip_exterior(lng, lat, zone["ring"]):
            return {"source": f"zonage-{city_code}", **zone["props"]}

    return {}


# ── CPTAQ zone agricole ───────────────────────────────────────────────────────

# GeoQuébec / données.gouv.qc.ca — Zone agricole CPTAQ (tout le Québec)
# File is large (~150 MB uncompressed) but indexes down to ~10 MB.
_CPTAQ_GEOJSON_URL = (
    "https://diffusion.mern.gouv.qc.ca/Diffusion/RGQ/Vectoriel/Theme-Series/"
    "Produits_geobase/Reglementaires/SHP_AQreseau%2B/"
    # Fallback: données.gouv.qc.ca canonical GeoJSON
)
_CPTAQ_GEOJSON_URLS: list[str] = [
    # données.gouv.qc.ca open data — zone agricole permanente CPTAQ
    "https://diffusion.mern.gouv.qc.ca/Diffusion/RGQ/Vectoriel/Theme-Series/"
    "Produits_geobase/Reglementaires/SHP_AQreseau%2B/",
    # Alternate: GeoQuébec WFS service (GeoJSON output)
    (
        "https://geoegl.msp.gouv.qc.ca/apis/wss/zone_agricole.fcgi"
        "?SERVICE=WFS&REQUEST=GetFeature&TYPENAME=ms:zone_agricole"
        "&OUTPUTFORMAT=geojson&SRSNAME=EPSG:4326"
    ),
]

# module-level CPTAQ index cache
_CPTAQ_INDEX_CACHE: list | None = None


def _download_file(url: str, dest: Path, timeout: int = 600) -> None:
    """Stream-download url → dest."""
    import httpx  # type: ignore
    with httpx.stream("GET", url, timeout=timeout, follow_redirects=True) as r:
        r.raise_for_status()
        with dest.open("wb") as fh:
            for chunk in r.iter_bytes(chunk_size=256 * 1024):
                fh.write(chunk)


def download_cptaq(cache_dir: Path, force: bool = False) -> Path | None:
    """
    Download the CPTAQ zone agricole GeoJSON (all of Québec, cached once).

    Tries the GeoQuébec WFS service first (direct GeoJSON), falls back to
    static file if known URL is configured. Returns local path or None.
    """
    geojson_path = cache_dir / "cptaq_zone_agricole.geojson"
    if geojson_path.exists() and not force:
        return geojson_path

    cache_dir.mkdir(parents=True, exist_ok=True)

    # Try WFS GeoJSON endpoint (direct, no parsing needed)
    wfs_url = (
        "https://geoegl.msp.gouv.qc.ca/apis/wss/zone_agricole.fcgi"
        "?SERVICE=WFS&REQUEST=GetFeature&TYPENAME=ms:zone_agricole"
        "&OUTPUTFORMAT=geojson&SRSNAME=EPSG:4326"
    )
    try:
        logger.info("Downloading CPTAQ zone agricole (WFS GeoJSON)…")
        _download_file(wfs_url, geojson_path, timeout=600)
        logger.info("CPTAQ downloaded: %.1f MB", geojson_path.stat().st_size / 1e6)
        return geojson_path
    except Exception as exc:
        logger.debug("CPTAQ WFS download failed: %s", exc)
        if geojson_path.exists():
            geojson_path.unlink()

    logger.debug("CPTAQ download unavailable — place cptaq_zone_agricole.geojson in data_cache/")
    return None


def build_cptaq_index(geojson_path: Path, index_path: Path) -> int:
    """
    Build compact spatial index from CPTAQ GeoJSON.

    Unlike zonage, we only keep bbox + simplified ring (props minimal).
    Returns count of polygons indexed.
    """
    data = json.loads(geojson_path.read_text(encoding="utf-8"))
    features = data.get("features") or []
    zones: list[dict] = []

    for feat in features:
        geom = feat.get("geometry") or {}
        props = feat.get("properties") or {}
        gtype = geom.get("type", "")

        if gtype == "Polygon":
            polys = [geom["coordinates"]]
        elif gtype == "MultiPolygon":
            polys = geom["coordinates"]
        else:
            continue

        for poly in polys:
            if not poly:
                continue
            exterior = poly[0]
            if len(exterior) < 3:
                continue
            xs = [p[0] for p in exterior]
            ys = [p[1] for p in exterior]
            # Keep only relevant props (zone designation)
            keep = {k: v for k, v in props.items()
                    if k.upper() in ("NM_MRC", "NM_MUNIC", "NM_REGION", "TYPE_ZONE",
                                      "CATEGORIE", "STATUT", "NO_DECISION", "CODE")}
            zones.append({
                "props": keep,
                "bbox": [min(xs), min(ys), max(xs), max(ys)],
                "ring": _simplify_ring(exterior, max_pts=200),
            })

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps({"zones": zones, "_built_at": time.time(), "_count": len(zones)},
                   ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("CPTAQ index built: %d zones → %s (%.1f MB)",
                len(zones), index_path.name, index_path.stat().st_size / 1e6)
    return len(zones)


def lookup_cptaq(lat: float, lng: float, cache_dir: Path) -> dict | None:
    """
    Return CPTAQ zone info if point (lat, lng) is inside the agricultural zone.

    Returns dict with source + props if inside, {} if outside, None if data unavailable.
    Auto-downloads and builds index if not cached.
    """
    global _CPTAQ_INDEX_CACHE

    index_path = cache_dir / "cptaq_index.json"

    # Build index if needed
    if not index_path.exists():
        geojson_path = cache_dir / "cptaq_zone_agricole.geojson"
        if not geojson_path.exists():
            try:
                geojson_path = download_cptaq(cache_dir)
            except Exception as exc:
                logger.debug("CPTAQ download skip: %s", exc)
                return None
        if geojson_path and geojson_path.exists():
            try:
                build_cptaq_index(geojson_path, index_path)
            except Exception as exc:
                logger.debug("CPTAQ index build skip: %s", exc)
                return None

    if not index_path.exists():
        return None

    # Load into module-level cache
    key = str(index_path)
    if _CPTAQ_INDEX_CACHE is None:
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
            _CPTAQ_INDEX_CACHE = data.get("zones", [])
        except Exception as exc:
            logger.debug("CPTAQ index load failed: %s", exc)
            return None

    for zone in _CPTAQ_INDEX_CACHE:
        bbox = zone["bbox"]
        if not (bbox[0] <= lng <= bbox[2] and bbox[1] <= lat <= bbox[3]):
            continue
        if _pip_exterior(lng, lat, zone["ring"]):
            return {"source": "cptaq", "en_zone_agricole": True, **zone["props"]}

    return {"source": "cptaq", "en_zone_agricole": False}


# ── Patrimoine culturel (Répertoire du patrimoine culturel du Québec) ─────────

# module-level cache
_PATRIMOINE_INDEX_CACHE: list | None = None

# Known WFS endpoint types for patrimoine culturel QC
_PATRIMOINE_WFS_URLS: list[str] = [
    # Immeubles patrimoniaux (bâtiments classés/cités/reconnus)
    (
        "https://geoegl.msp.gouv.qc.ca/apis/wss/patrimoine.fcgi"
        "?SERVICE=WFS&REQUEST=GetFeature"
        "&TYPENAME=ms:immeuble_patrimonial"
        "&OUTPUTFORMAT=geojson&SRSNAME=EPSG:4326"
    ),
    # Alternate: données.gouv.qc.ca package
]


def download_patrimoine(cache_dir: Path, force: bool = False) -> Path | None:
    """
    Download the Répertoire du patrimoine culturel du Québec GeoJSON (WFS).

    Covers immeubles patrimoniaux (classés, cités, reconnus).
    Returns local path or None if unavailable.
    """
    geojson_path = cache_dir / "patrimoine_culturel.geojson"
    if geojson_path.exists() and not force:
        return geojson_path

    cache_dir.mkdir(parents=True, exist_ok=True)

    for url in _PATRIMOINE_WFS_URLS:
        try:
            logger.info("Downloading patrimoine culturel (WFS GeoJSON)…")
            _download_file(url, geojson_path, timeout=300)
            logger.info("Patrimoine culturel downloaded: %.1f MB",
                        geojson_path.stat().st_size / 1e6)
            return geojson_path
        except Exception as exc:
            logger.debug("Patrimoine WFS download failed: %s", exc)
            if geojson_path.exists():
                geojson_path.unlink()

    logger.debug("Patrimoine download unavailable — place patrimoine_culturel.geojson in data_cache/")
    return None


def build_patrimoine_index(geojson_path: Path, index_path: Path) -> int:
    """
    Build compact spatial index from patrimoine culturel GeoJSON.

    For Point geometries (common for individual buildings): store as tiny bbox.
    For Polygon/MultiPolygon: same as CPTAQ.
    Returns number of features indexed.
    """
    data = json.loads(geojson_path.read_text(encoding="utf-8"))
    features = data.get("features") or []
    zones: list[dict] = []

    _KEEP_PROPS = {
        "NOM", "NM_BIEN", "STATUT", "CATEGORIE", "TYPE_BIEN",
        "COTE_PATRIMONIALE", "MUNICIPALITE", "MRC", "REGION",
        "NM_STATUT", "NM_CATEGORIE",
    }

    for feat in features:
        geom = feat.get("geometry") or {}
        props = feat.get("properties") or {}
        gtype = geom.get("type", "")
        keep = {k: v for k, v in props.items() if k.upper() in _KEEP_PROPS and v}

        if gtype == "Point":
            lng, lat = geom["coordinates"][0], geom["coordinates"][1]
            # Small buffer ~50m in degrees at QC latitude
            buf = 0.0005
            zones.append({
                "props": keep,
                "bbox": [lng - buf, lat - buf, lng + buf, lat + buf],
                "point": [lng, lat],
            })
        elif gtype == "Polygon":
            polys = [geom["coordinates"]]
        elif gtype == "MultiPolygon":
            polys = geom["coordinates"]
        else:
            continue

        if gtype in ("Polygon", "MultiPolygon"):
            for poly in polys:
                if not poly:
                    continue
                exterior = poly[0]
                if len(exterior) < 3:
                    continue
                xs = [p[0] for p in exterior]
                ys = [p[1] for p in exterior]
                zones.append({
                    "props": keep,
                    "bbox": [min(xs), min(ys), max(xs), max(ys)],
                    "ring": _simplify_ring(exterior, max_pts=100),
                })

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps({"zones": zones, "_built_at": time.time(), "_count": len(zones)},
                   ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Patrimoine index built: %d features → %s (%.1f MB)",
                len(zones), index_path.name, index_path.stat().st_size / 1e6)
    return len(zones)


def _point_near(lng: float, lat: float, feat_lng: float, feat_lat: float,
                threshold_deg: float = 0.0005) -> bool:
    """Return True if (lng, lat) is within threshold degrees of a point feature."""
    return abs(lng - feat_lng) <= threshold_deg and abs(lat - feat_lat) <= threshold_deg


def lookup_patrimoine(lat: float, lng: float, cache_dir: Path) -> dict | None:
    """
    Return first patrimoine culturel feature near/containing (lat, lng).

    Returns dict with source + props if found, {} if not found,
    None if data unavailable.
    """
    global _PATRIMOINE_INDEX_CACHE

    index_path = cache_dir / "patrimoine_index.json"

    if not index_path.exists():
        geojson_path = cache_dir / "patrimoine_culturel.geojson"
        if not geojson_path.exists():
            try:
                geojson_path = download_patrimoine(cache_dir)
            except Exception as exc:
                logger.debug("Patrimoine download skip: %s", exc)
                return None
        if geojson_path and geojson_path.exists():
            try:
                build_patrimoine_index(geojson_path, index_path)
            except Exception as exc:
                logger.debug("Patrimoine index build skip: %s", exc)
                return None

    if not index_path.exists():
        return None

    if _PATRIMOINE_INDEX_CACHE is None:
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
            _PATRIMOINE_INDEX_CACHE = data.get("zones", [])
        except Exception as exc:
            logger.debug("Patrimoine index load failed: %s", exc)
            return None

    for feat in _PATRIMOINE_INDEX_CACHE:
        bbox = feat["bbox"]
        if not (bbox[0] <= lng <= bbox[2] and bbox[1] <= lat <= bbox[3]):
            continue
        # Point feature: proximity check
        if "point" in feat:
            fl, flat = feat["point"]
            if _point_near(lng, lat, fl, flat):
                return {"source": "patrimoine-culturel", **feat["props"]}
        # Polygon feature: PiP
        elif "ring" in feat:
            if _pip_exterior(lng, lat, feat["ring"]):
                return {"source": "patrimoine-culturel", **feat["props"]}

    return {}


# ── Zones inondables (MELCC / GeoQuébec) ─────────────────────────────────────

# module-level cache
_INONDABLE_INDEX_CACHE: list | None = None

# MELCC WFS — zones de contrainte (inondation 0-20 ans, 20-100 ans)
# Source: Atlas des zones inondables du MELCC
_INONDABLE_WFS_URLS: list[str] = [
    (
        "https://geoegl.msp.gouv.qc.ca/apis/wss/complet.fcgi"
        "?SERVICE=WFS&REQUEST=GetFeature"
        "&TYPENAME=ms:igo_inondation"
        "&OUTPUTFORMAT=geojson&SRSNAME=EPSG:4326"
    ),
    # Alternate: direct MELCC GeoServer
    (
        "https://geoserver.environnement.gouv.qc.ca/geoserver/ows"
        "?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature"
        "&TYPENAMES=MELCC:zone_inondable"
        "&OUTPUTFORMAT=application/json&SRSNAME=EPSG:4326"
    ),
]

# Récurrence → label FR
_RECURRENCE_LABELS: dict[str, str] = {
    "0_20": "0-20 ans (grand courant)",
    "20_100": "20-100 ans (crue centennale)",
    "100": "100+ ans",
    "2": "2 ans",
    "20": "20 ans",
    "100_500": "100-500 ans",
}


def download_inondable(cache_dir: Path, force: bool = False) -> Path | None:
    """
    Download MELCC zones inondables GeoJSON (tout le Québec, WFS).
    Returns local path or None if unavailable.
    """
    geojson_path = cache_dir / "zones_inondables.geojson"
    if geojson_path.exists() and not force:
        return geojson_path

    cache_dir.mkdir(parents=True, exist_ok=True)

    for url in _INONDABLE_WFS_URLS:
        try:
            logger.info("Downloading zones inondables MELCC (WFS GeoJSON)…")
            _download_file(url, geojson_path, timeout=600)
            logger.info("Zones inondables downloaded: %.1f MB",
                        geojson_path.stat().st_size / 1e6)
            return geojson_path
        except Exception as exc:
            logger.debug("Zones inondables WFS failed: %s", exc)
            if geojson_path.exists():
                geojson_path.unlink()

    logger.debug("Zones inondables unavailable — place zones_inondables.geojson in data_cache/")
    return None


def build_inondable_index(geojson_path: Path, index_path: Path) -> int:
    """
    Build compact spatial index from zones inondables GeoJSON.
    Keeps récurrence/type fields for risk classification.
    Returns number of polygons indexed.
    """
    data = json.loads(geojson_path.read_text(encoding="utf-8"))
    features = data.get("features") or []
    zones: list[dict] = []

    _KEEP_PROPS = {
        "RECURRENCE", "TYPE_ZONE", "NM_ZONE", "DESCRIPTION",
        "CLASSE", "SOURCE", "MRC", "MUNICIPALITE",
        # alternate field names from different WFS schemas
        "RECURR", "TYPE", "STATUT",
    }

    for feat in features:
        geom = feat.get("geometry") or {}
        props = feat.get("properties") or {}
        gtype = geom.get("type", "")
        keep = {k: v for k, v in props.items() if k.upper() in _KEEP_PROPS and v}

        if gtype == "Polygon":
            polys = [geom["coordinates"]]
        elif gtype == "MultiPolygon":
            polys = geom["coordinates"]
        else:
            continue

        for poly in polys:
            if not poly:
                continue
            exterior = poly[0]
            if len(exterior) < 3:
                continue
            xs = [p[0] for p in exterior]
            ys = [p[1] for p in exterior]
            zones.append({
                "props": keep,
                "bbox": [min(xs), min(ys), max(xs), max(ys)],
                "ring": _simplify_ring(exterior, max_pts=150),
            })

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps({"zones": zones, "_built_at": time.time(), "_count": len(zones)},
                   ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Zones inondables index built: %d zones → %s (%.1f MB)",
                len(zones), index_path.name, index_path.stat().st_size / 1e6)
    return len(zones)


def lookup_inondable(lat: float, lng: float, cache_dir: Path) -> dict | None:
    """
    Return first zone inondable containing (lat, lng).

    Returns dict with source + récurrence if in flood zone,
    {} if outside all zones, None if data unavailable.
    """
    global _INONDABLE_INDEX_CACHE

    index_path = cache_dir / "inondable_index.json"

    if not index_path.exists():
        geojson_path = cache_dir / "zones_inondables.geojson"
        if not geojson_path.exists():
            try:
                geojson_path = download_inondable(cache_dir)
            except Exception as exc:
                logger.debug("Zones inondables download skip: %s", exc)
                return None
        if geojson_path and geojson_path.exists():
            try:
                build_inondable_index(geojson_path, index_path)
            except Exception as exc:
                logger.debug("Inondable index build skip: %s", exc)
                return None

    if not index_path.exists():
        return None

    if _INONDABLE_INDEX_CACHE is None:
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
            _INONDABLE_INDEX_CACHE = data.get("zones", [])
        except Exception as exc:
            logger.debug("Inondable index load failed: %s", exc)
            return None

    # Return the most restrictive zone (smallest recurrence period = highest risk)
    hits: list[dict] = []
    for zone in _INONDABLE_INDEX_CACHE:
        bbox = zone["bbox"]
        if not (bbox[0] <= lng <= bbox[2] and bbox[1] <= lat <= bbox[3]):
            continue
        if _pip_exterior(lng, lat, zone["ring"]):
            hits.append(zone["props"])

    if not hits:
        return {}

    # Prefer zone with smallest recurrence number (highest risk)
    def _risk_key(props: dict) -> int:
        rec = str(props.get("RECURRENCE") or props.get("RECURR") or "999")
        try:
            return int(rec.split("_")[0].split("-")[0])
        except ValueError:
            return 999

    best = sorted(hits, key=_risk_key)[0]
    rec = best.get("RECURRENCE") or best.get("RECURR") or ""
    label = _RECURRENCE_LABELS.get(rec, rec)
    return {
        "source": "melcc-zones-inondables",
        "en_zone_inondable": True,
        "recurrence": rec,
        "recurrence_label": label,
        **{k: v for k, v in best.items() if k not in ("RECURRENCE", "RECURR")},
    }


def compute_score_marche(case: dict) -> dict:
    """
    Synthesize available market indicators into an actionable market score (0–10).

    Pure function — no external calls, no cache.  Inputs (all optional):
      - taux_inoccupation.taux_total_pct      (B14)
      - indice_prix_logement.variation_annuelle_pct  (B10)
      - marche_travail.taux_chomage_pct       (B17)
      - population_cma.variation_annuelle_pct (B16)
      - mises_en_chantier.variation_pct_6m    (B19)
      - crime_stats.taux_criminalite_total    (B21)

    Returns dict with keys: score_marche, score_max, indicateurs_utilises,
    tension_locative, interpretation, source.
    Returns {} if fewer than 2 indicators available.
    """
    points = 0
    max_possible = 0
    indicateurs: list[str] = []

    # ── Taux d'inoccupation (B14) — marché locatif ───────────────────────────
    tx_inoc = (case.get("taux_inoccupation") or {}).get("taux_total_pct")
    if tx_inoc is not None:
        max_possible += 2
        indicateurs.append("inoccupation")
        if tx_inoc < _MARCHE_INOCCUPATION_TENDU:
            points += 2  # marché très tendu = favorable au vendeur/proprio
        elif tx_inoc < _MARCHE_INOCCUPATION_NORMAL:
            points += 1

    # ── NHPI variation (B10) — croissance prix logement neuf ─────────────────
    nhpi_var = (case.get("indice_prix_logement") or {}).get("variation_annuelle_pct")
    if nhpi_var is not None:
        max_possible += 2
        indicateurs.append("nhpi_variation")
        if nhpi_var >= _MARCHE_NHPI_FORT:
            points += 2
        elif nhpi_var >= 0:
            points += 1

    # ── Marché du travail (B17) — taux de chômage ────────────────────────────
    chomage = (case.get("marche_travail") or {}).get("taux_chomage_pct")
    if chomage is not None:
        max_possible += 2
        indicateurs.append("marche_travail")
        if chomage < _MARCHE_CHOMAGE_BAS:
            points += 2
        elif chomage < _MARCHE_CHOMAGE_MOYEN:
            points += 1

    # ── Croissance démographique CMA (B16) ────────────────────────────────────
    pop_var = (case.get("population_cma") or {}).get("variation_annuelle_pct")
    if pop_var is not None:
        max_possible += 2
        indicateurs.append("population")
        if pop_var >= _MARCHE_POP_FORTE:
            points += 2
        elif pop_var >= 0:
            points += 1

    # ── Mises en chantier tendance (B19) — dynamisme offre ───────────────────
    chantier_var = (case.get("mises_en_chantier") or {}).get("variation_pct_6m")
    if chantier_var is not None:
        max_possible += 1
        indicateurs.append("mises_en_chantier")
        if chantier_var > 0:
            points += 1  # offre en croissance = économie active

    # ── Criminalité (B21) — attractivité du secteur ───────────────────────────
    crime_total = (case.get("crime_stats") or {}).get("taux_criminalite_total")
    if crime_total is not None:
        max_possible += 1
        indicateurs.append("crime")
        if crime_total < _MARCHE_CRIME_BAS:
            points += 1

    if len(indicateurs) < 2:
        return {}

    # Normalize to 0–10
    score_norm = round(points / max_possible * 10, 1) if max_possible > 0 else 0.0

    # Tension locative label
    if tx_inoc is not None:
        if tx_inoc < _MARCHE_INOCCUPATION_TENDU:
            tension = "marché locatif tendu"
        elif tx_inoc < _MARCHE_INOCCUPATION_NORMAL:
            tension = "marché équilibré"
        else:
            tension = "marché locatif détendu"
    else:
        tension = "données inoccupation indisponibles"

    # Overall interpretation
    if score_norm >= 8.0:
        interp = "marché très favorable — conditions idéales pour la valorisation"
    elif score_norm >= 6.0:
        interp = "marché favorable — bonne dynamique globale"
    elif score_norm >= 4.0:
        interp = "marché modéré — conditions mixtes"
    else:
        interp = "marché difficile — vigilance recommandée"

    result = {
        "source": "calcul-interne",
        "score_marche": score_norm,
        "score_max": 10.0,
        "points_bruts": points,
        "points_max_bruts": max_possible,
        "indicateurs_utilises": indicateurs,
        "tension_locative": tension,
        "interpretation": interp,
    }

    logger.debug("score_marche : %.1f/10 (%d indicateurs) — %s",
                 score_norm, len(indicateurs), interp)
    return result


def compute_indice_abordabilite(case: dict) -> dict:
    """
    Compute a housing affordability index from already-enriched case data.

    Pure function — no external calls, no cache.  Uses:
      - marche_locatif.loyer_moyen_total  (B5)
      - donnees_sociodemographiques.revenu_median_menage  (B11)
      - donnees_sociodemographiques.valeur_mediane_logement  (B11)
      - taux_bancaires.taux_hypo_5ans_conv_pct  (B15)

    Returns dict with keys:
      ratio_loyer_revenu_pct, ratio_propriete_revenu,
      versement_mensuel_estime, ratio_mensualite_revenu_pct,
      seuil_loyer, seuil_propriete, source.
    Returns {} if minimum inputs are unavailable.
    """
    revenu = (case.get("donnees_sociodemographiques") or {}).get("revenu_median_menage")
    if not revenu or revenu <= 0:
        return {}

    revenu_mensuel = revenu / 12.0
    result: dict = {
        "source": "calcul-interne",
        "revenu_median_menage": revenu,
    }

    # ── Ratio loyer / revenu ──────────────────────────────────────────────────
    loyer = (case.get("marche_locatif") or {}).get("loyer_moyen_total")
    if loyer and loyer > 0:
        ratio_loyer = round(loyer / revenu_mensuel * 100, 1)
        result["ratio_loyer_revenu_pct"] = ratio_loyer
        if ratio_loyer < _ABORD_SEUIL_ABORDABLE:
            result["seuil_loyer"] = "abordable"
        elif ratio_loyer < _ABORD_SEUIL_LIMITE:
            result["seuil_loyer"] = "limite"
        else:
            result["seuil_loyer"] = "non abordable"

    # ── Ratio valeur propriété / revenu annuel ────────────────────────────────
    valeur = (case.get("donnees_sociodemographiques") or {}).get("valeur_mediane_logement")
    if valeur and valeur > 0:
        ratio_prop = round(valeur / revenu, 1)
        result["ratio_propriete_revenu"] = ratio_prop

        # Mensualité hypothécaire estimée (25 ans, 20 % mise de fonds, taux B15)
        taux_annuel = (case.get("taux_bancaires") or {}).get("taux_hypo_5ans_conv_pct")
        if taux_annuel and taux_annuel > 0:
            principal = valeur * (1 - _ABORD_MISE_DE_FONDS)
            r = taux_annuel / 100 / 12  # taux mensuel
            n = _ABORD_AMORT_MOIS
            # Formule annuité constante: M = P × r(1+r)^n / ((1+r)^n - 1)
            facteur = (1 + r) ** n
            mensualite = principal * r * facteur / (facteur - 1)
            result["versement_mensuel_estime"] = round(mensualite, 0)
            ratio_mens = round(mensualite / revenu_mensuel * 100, 1)
            result["ratio_mensualite_revenu_pct"] = ratio_mens
            if ratio_mens < _ABORD_SEUIL_ABORDABLE:
                result["seuil_propriete"] = "abordable"
            elif ratio_mens < _ABORD_SEUIL_LIMITE:
                result["seuil_propriete"] = "limite"
            else:
                result["seuil_propriete"] = "non abordable"

    if len(result) <= 2:  # only source + revenu
        return {}

    logger.debug("indice_abordabilite : loyer=%s%% proprio=%s%%",
                 result.get("ratio_loyer_revenu_pct"),
                 result.get("ratio_mensualite_revenu_pct"))
    return result


def compute_rendement_locatif(case: dict) -> dict:
    """
    Compute gross and estimated net capitalization rate (cap rate) for the property.

    Pure function — no external calls, no cache.  Uses:
      - evaluation_municipale_totale  (case-level field, or role_municipal.valeur_totale)
      - marche_locatif.loyer_moyen_total  (B5 — median monthly rent for the CMA)

    Returns dict with keys:
      valeur_reference, loyer_mensuel_reference,
      revenus_locatifs_bruts_annuels,
      taux_capitalisation_brut_pct,
      taux_capitalisation_net_estime_pct,
      frais_operation_pct, interpretation, source.
    Returns {} if minimum inputs are unavailable.
    """
    # ── Valeur de référence ───────────────────────────────────────────────────
    valeur = case.get("evaluation_municipale_totale")
    if not valeur:
        valeur = (case.get("role_municipal") or {}).get("valeur_totale")
    if not valeur or valeur <= 0:
        return {}

    # ── Loyer de référence (loyer médian CMA) ─────────────────────────────────
    loyer = (case.get("marche_locatif") or {}).get("loyer_moyen_total")
    if not loyer or loyer <= 0:
        return {}

    # ── Calcul ───────────────────────────────────────────────────────────────
    revenus_bruts = loyer * 12
    taux_brut = revenus_bruts / valeur * 100
    frais_pct = _CAPRATE_FRAIS_OPERATION * 100
    taux_net = taux_brut * (1 - _CAPRATE_FRAIS_OPERATION)

    if taux_brut >= _CAPRATE_EXCELLENT:
        interpretation = "excellent"
    elif taux_brut >= _CAPRATE_BON:
        interpretation = "bon"
    elif taux_brut >= _CAPRATE_FAIBLE:
        interpretation = "acceptable"
    else:
        interpretation = "faible"

    result = {
        "valeur_reference": round(valeur, 0),
        "loyer_mensuel_reference": round(loyer, 0),
        "revenus_locatifs_bruts_annuels": round(revenus_bruts, 0),
        "taux_capitalisation_brut_pct": round(taux_brut, 2),
        "frais_operation_pct": round(frais_pct, 1),
        "taux_capitalisation_net_estime_pct": round(taux_net, 2),
        "interpretation": interpretation,
        "source": "calcul-interne",
    }

    logger.debug("rendement_locatif : taux_brut=%.2f%% taux_net=%.2f%% (%s)",
                 taux_brut, taux_net, interpretation)
    return result


def compute_score_investissement(case: dict) -> dict:
    """
    Compute a composite investment-attractiveness score (0–10).

    Pure function — no external calls, no cache.  Synthesizes:
      - score_marche (B31)          — market momentum (weight 40 %)
      - rendement_locatif (B32)     — rental yield (weight 35 %)
      - indice_abordabilite (B30)   — demand pressure / affordability (weight 25 %)

    Each component is normalised to [0, 10] before weighting.
    Returns {} if fewer than 2 components are available.

    Returns dict with keys:
      score_investissement, composantes, poids, recommandation, source.
    """
    composantes: dict[str, float] = {}

    # ── Composante 1 : score de marché (déjà 0-10) ───────────────────────────
    score_m = case.get("score_marche") or {}
    sm_val = score_m.get("score_marche")
    if sm_val is not None and 0 <= sm_val <= 10:
        composantes["score_marche"] = float(sm_val)

    # ── Composante 2 : rendement locatif (normalise taux brut 0-12% → 0-10) ──
    rend = case.get("rendement_locatif") or {}
    taux_brut = rend.get("taux_capitalisation_brut_pct")
    if taux_brut is not None and taux_brut >= 0:
        # 0 % = 0 pts / 12 % (plafond réaliste QC) = 10 pts, linéaire, capped
        rend_norm = min(taux_brut / 12.0 * 10.0, 10.0)
        composantes["rendement_locatif"] = round(rend_norm, 2)

    # ── Composante 3 : abordabilité inversée (ratio loyer/revenu) ────────────
    # Ratio bas = abordable = attractif pour locataires → score élevé
    # 0 % ratio = 10 pts (idéal) / ≥ 50 % = 0 pt, linéaire
    abord = case.get("indice_abordabilite") or {}
    ratio_loyer = abord.get("ratio_loyer_revenu_pct")
    if ratio_loyer is not None and ratio_loyer >= 0:
        abord_norm = max(0.0, min(10.0, (50.0 - ratio_loyer) / 50.0 * 10.0))
        composantes["abordabilite"] = round(abord_norm, 2)

    if len(composantes) < 2:
        return {}

    # ── Score pondéré ─────────────────────────────────────────────────────────
    poids_map = {
        "score_marche":    _INVEST_POIDS_MARCHE,
        "rendement_locatif": _INVEST_POIDS_RENDEMENT,
        "abordabilite":    _INVEST_POIDS_ABORDABILITE,
    }
    score_num = 0.0
    poids_total = 0.0
    for cle, val in composantes.items():
        p = poids_map[cle]
        score_num += val * p
        poids_total += p

    # Re-normalise si composantes manquantes
    score_final = round(score_num / poids_total * 10.0 / 10.0, 2) if poids_total else 0.0

    if score_final >= _INVEST_SEUIL_FORT:
        recommandation = "fort potentiel"
    elif score_final >= _INVEST_SEUIL_MODERE:
        recommandation = "potentiel modéré"
    elif score_final >= _INVEST_SEUIL_FAIBLE:
        recommandation = "potentiel faible"
    else:
        recommandation = "déconseillé"

    result = {
        "score_investissement": score_final,
        "composantes": composantes,
        "poids": {k: poids_map[k] for k in composantes},
        "recommandation": recommandation,
        "source": "calcul-interne",
    }

    logger.debug("score_investissement : %.2f/10 → %s (%d composantes)",
                 score_final, recommandation, len(composantes))
    return result


def compute_taxes_municipales(case: dict, city_code: str) -> dict:
    """
    Estimate annual municipal property taxes for the property.

    Pure function — no external calls.  Uses:
      - city_code → hardcoded tax rate table (_TAXES_TAUX_PCT)
      - evaluation_municipale_totale (or role_municipal.valeur_totale) as assessment base

    Returns dict with keys:
      taux_taxation_pct, taxes_annuelles_estimees, taxes_mensuelles_estimees,
      vs_moyenne_provinciale_pct, ecart_moyenne_pct, ville_reference, source.
    Returns {} if city_code unknown or assessment value unavailable.
    """
    taux = _TAXES_TAUX_PCT.get(city_code)
    if taux is None:
        return {}

    valeur = case.get("evaluation_municipale_totale")
    if not valeur:
        valeur = (case.get("role_municipal") or {}).get("valeur_totale")
    if not valeur or valeur <= 0:
        return {}

    taxes_annuelles = valeur * taux / 100.0
    taxes_mensuelles = taxes_annuelles / 12.0
    ecart = round(taux - _TAXES_MOYENNE_QC_PCT, 3)

    if taux < _TAXES_MOYENNE_QC_PCT:
        vs_moy = "sous la moyenne provinciale"
    elif taux > _TAXES_MOYENNE_QC_PCT:
        vs_moy = "au-dessus de la moyenne provinciale"
    else:
        vs_moy = "dans la moyenne provinciale"

    result = {
        "taux_taxation_pct": taux,
        "taxes_annuelles_estimees": round(taxes_annuelles, 0),
        "taxes_mensuelles_estimees": round(taxes_mensuelles, 0),
        "vs_moyenne_provinciale_pct": _TAXES_MOYENNE_QC_PCT,
        "ecart_moyenne_pct": ecart,
        "comparaison": vs_moy,
        "ville_reference": city_code,
        "source": "calcul-interne",
    }

    logger.debug("taxes_municipales : %.3f%% → %d $/an (%s)",
                 taux, taxes_annuelles, vs_moy)
    return result


def compute_couts_possession(case: dict) -> dict:
    """
    Estimate total monthly and annual ownership carrying costs.

    Pure function — no external calls.  Synthesizes:
      - indice_abordabilite.versement_mensuel_estime  (B30 — mortgage payment)
      - taxes_municipales.taxes_mensuelles_estimees    (B34 — property tax)
      - evaluation_municipale_totale / role_municipal.valeur_totale
        → entretien  (_POSSESSION_ENTRETIEN_PCT %/an)
        → assurance  (_POSSESSION_ASSURANCE_PCT %/an)
      - donnees_sociodemographiques.revenu_median_menage (B11 — for ratio)

    Returns dict with:
      versement_hypothecaire_mensuel, taxes_mensuelles, entretien_mensuel,
      assurance_mensuelle, total_mensuel, total_annuel,
      ratio_revenu_pct (optional), interpretation, source.
    Returns {} if no cost component can be computed.
    """
    composantes: dict[str, float] = {}

    # ── Versement hypothécaire (B30) ─────────────────────────────────────────
    hypo = (case.get("indice_abordabilite") or {}).get("versement_mensuel_estime")
    if hypo and hypo > 0:
        composantes["versement_hypothecaire_mensuel"] = float(hypo)

    # ── Taxes municipales (B34) ───────────────────────────────────────────────
    taxes_m = (case.get("taxes_municipales") or {}).get("taxes_mensuelles_estimees")
    if taxes_m and taxes_m > 0:
        composantes["taxes_mensuelles"] = float(taxes_m)

    # ── Valeur de référence pour entretien + assurance ────────────────────────
    valeur = case.get("evaluation_municipale_totale")
    if not valeur:
        valeur = (case.get("role_municipal") or {}).get("valeur_totale")

    if valeur and valeur > 0:
        composantes["entretien_mensuel"] = round(valeur * _POSSESSION_ENTRETIEN_PCT / 100 / 12, 0)
        composantes["assurance_mensuelle"] = round(valeur * _POSSESSION_ASSURANCE_PCT / 100 / 12, 0)

    if not composantes:
        return {}

    total_mensuel = round(sum(composantes.values()), 0)
    total_annuel = round(total_mensuel * 12, 0)

    result: dict = {
        **{k: round(v, 0) for k, v in composantes.items()},
        "total_mensuel": total_mensuel,
        "total_annuel": total_annuel,
        "source": "calcul-interne",
    }

    # ── Ratio coûts / revenu ──────────────────────────────────────────────────
    revenu = (case.get("donnees_sociodemographiques") or {}).get("revenu_median_menage")
    if revenu and revenu > 0:
        revenu_mensuel = revenu / 12.0
        ratio = round(total_mensuel / revenu_mensuel * 100, 1)
        result["ratio_revenu_pct"] = ratio
        if ratio >= _POSSESSION_SEUIL_ELEVE:
            result["interpretation"] = "coûts élevés"
        elif ratio >= _POSSESSION_SEUIL_MODERE:
            result["interpretation"] = "coûts modérés"
        else:
            result["interpretation"] = "coûts abordables"
    else:
        result["interpretation"] = "données revenu indisponibles"

    logger.debug("couts_possession : total=%d $/mois ratio=%s%%",
                 total_mensuel, result.get("ratio_revenu_pct", "n/a"))
    return result


def compute_ratio_prix_loyer(case: dict) -> dict:
    """
    Compute the price-to-rent ratio (P/L) for the property.

    Pure function — no external calls.  Uses:
      - evaluation_municipale_totale (or role_municipal.valeur_totale) as price proxy
      - marche_locatif.loyer_moyen_total (B5 — monthly CMA rent)

    P/L = valeur / (loyer_mensuel × 12)

    Interpretation thresholds (SCHL / Economist convention):
      < 15  → avantage à l'achat
      15-20 → marché équilibré
      20-25 → légère faveur location
      > 25  → forte faveur location (marché surcoté)

    Also computes loyer_equivalent_mensuel: the monthly rent implied by
    the property's carrying costs (from couts_possession.total_mensuel).

    Returns {} if price or rent data unavailable.
    """
    valeur = case.get("evaluation_municipale_totale")
    if not valeur:
        valeur = (case.get("role_municipal") or {}).get("valeur_totale")
    if not valeur or valeur <= 0:
        return {}

    loyer = (case.get("marche_locatif") or {}).get("loyer_moyen_total")
    if not loyer or loyer <= 0:
        return {}

    ratio = round(valeur / (loyer * 12), 1)

    if ratio < _PLR_FAVEUR_ACHAT:
        signal = "avantage achat"
    elif ratio < _PLR_EQUILIBRE:
        signal = "marché équilibré"
    elif ratio < _PLR_FAVEUR_LOCATION:
        signal = "légère faveur location"
    else:
        signal = "forte faveur location"

    result: dict = {
        "valeur_reference": round(valeur, 0),
        "loyer_mensuel_reference": round(loyer, 0),
        "ratio_prix_loyer": ratio,
        "signal": signal,
        "source": "calcul-interne",
    }

    # Loyer équivalent depuis coûts de possession
    total_m = (case.get("couts_possession") or {}).get("total_mensuel")
    if total_m and total_m > 0:
        result["loyer_equivalent_mensuel"] = round(total_m, 0)
        ecart_pct = round((total_m - loyer) / loyer * 100, 1)
        result["ecart_loyer_marche_pct"] = ecart_pct
        if ecart_pct > 20:
            result["ecart_signal"] = "posséder coûte significativement plus cher"
        elif ecart_pct > 0:
            result["ecart_signal"] = "posséder coûte légèrement plus cher"
        elif ecart_pct > -20:
            result["ecart_signal"] = "posséder coûte légèrement moins cher"
        else:
            result["ecart_signal"] = "posséder coûte significativement moins cher"

    logger.debug("ratio_prix_loyer : %.1f (%s)", ratio, signal)
    return result


def compute_vetuste_batiment(case: dict) -> dict:
    """
    Estimate building age, physical depreciation, and renovation needs.

    Pure function — no external calls.  Uses:
      - case["annee_construction"]  (or role_municipal.annee_construction as fallback)

    Depreciation: linear, 1.25 %/year (100 % / 80-year useful life), capped at
    _VETUSTE_DEPRECIATION_MAX (80 %).

    Returns dict with keys:
      annee_construction, age_ans, categorie, taux_depreciation_pct,
      valeur_residuelle_pct, renovation_recommandee, source.
    Returns {} if construction year unavailable.
    """
    annee = case.get("annee_construction")
    if not annee:
        annee = (case.get("role_municipal") or {}).get("annee_construction")
    if not annee:
        return {}

    try:
        annee = int(annee)
    except (ValueError, TypeError):
        return {}

    if annee < 1800 or annee > _ANNEE_REFERENCE:
        return {}

    age = _ANNEE_REFERENCE - annee
    taux_depr = min(age / _VETUSTE_VIE_UTILE * 100.0, _VETUSTE_DEPRECIATION_MAX)
    valeur_residuelle = round(100.0 - taux_depr, 1)

    if age < _VETUSTE_SEUIL_NEUF:
        categorie = "neuf"
    elif age < _VETUSTE_SEUIL_RECENT:
        categorie = "récent"
    elif age < _VETUSTE_SEUIL_MOYEN:
        categorie = "mi-vie"
    elif age < _VETUSTE_SEUIL_VIEUX:
        categorie = "vieux"
    else:
        categorie = "très vieux"

    result = {
        "annee_construction": annee,
        "age_ans": age,
        "categorie": categorie,
        "taux_depreciation_pct": round(taux_depr, 1),
        "valeur_residuelle_pct": valeur_residuelle,
        "renovation_recommandee": age >= _VETUSTE_RENOVATION_ANS,
        "source": "calcul-interne",
    }

    logger.debug("vetuste_batiment : %d ans (%s) deprec=%.1f%%",
                 age, categorie, taux_depr)
    return result


# ── Main entry point ──────────────────────────────────────────────────────────

def enrich_case(
    case: dict,
    display_name: str = "",
    cache_dir: Path | None = None,
) -> None:
    """
    Enrich case dict in-place with external data.

    Injects (when available) :
      - case["marche_locatif"]    : SCHL rental market data (StatCan WDS)
      - case["role_municipal"]    : building characteristics + valeurs foncières
      - case["zonage_urbanisme"]    : official zone code + description (open data GeoJSON)
      - case["zone_agricole"]       : CPTAQ agricultural zone status (bool + MRC info)
      - case["patrimoine_culturel"] : {} if not listed, dict with statut/nom if found
      - case["zone_inondable"]        : {} if outside, dict with recurrence if in flood zone
      - case["indice_prix_logement"]  : NHPI (indice + variation annuelle %) via StatCan WDS

    Never raises — all failures logged at DEBUG level.
    """
    if cache_dir is None:
        cache_dir = Path(__file__).resolve().parent.parent / "data_cache"

    zone = str(case.get("zone", ""))
    city_code = detect_city(display_name, zone)

    # ── IPC logement (national, non spécifique à la ville) ───────────────────
    if not case.get("ipc_logement"):
        try:
            ipc = fetch_ipc_logement(cache_dir)
            if ipc:
                case["ipc_logement"] = ipc
                logger.debug("ipc_logement injecté : logement=%.1f var=%.1f%%",
                             ipc.get("ipc_logement", 0),
                             ipc.get("variation_logement_pct", 0))
        except Exception as exc:
            logger.debug("ipc_logement skip: %s", exc)

    # ── Marché du travail CMA ─────────────────────────────────────────────────
    if not case.get("marche_travail"):
        try:
            travail = fetch_marche_travail(city_code, cache_dir)
            if travail:
                case["marche_travail"] = travail
                logger.debug("marche_travail injecté : %s chômage=%.1f%%",
                             city_code, travail.get("taux_chomage_pct", 0))
        except Exception as exc:
            logger.debug("marche_travail skip: %s", exc)

    # ── Croissance démographique CMA ──────────────────────────────────────────
    if not case.get("population_cma"):
        try:
            pop = fetch_population_growth(city_code, cache_dir)
            if pop:
                case["population_cma"] = pop
                logger.debug("population_cma injecté : %s pop=%d var=%.2f%%",
                             city_code, pop.get("population", 0),
                             pop.get("variation_annuelle_pct", 0))
        except Exception as exc:
            logger.debug("population_cma skip: %s", exc)

    # ── Taux Bank of Canada (nationaux, non spécifiques à la ville) ──────────
    if not case.get("taux_bancaires"):
        try:
            taux = fetch_taux_boc(cache_dir)
            if taux:
                case["taux_bancaires"] = taux
                logger.debug("taux_bancaires injecté : directeur=%.2f%%",
                             taux.get("taux_directeur_pct", 0))
        except Exception as exc:
            logger.debug("taux_boc skip: %s", exc)

    # ── Ratio dette/revenu ménages (StatCan 11-10-0065-01) ───────────────────
    if not case.get("dette_revenu"):
        try:
            dette = fetch_dette_revenu(cache_dir)
            if dette:
                case["dette_revenu"] = dette
                logger.debug("dette_revenu injecté : ratio=%.1f%%",
                             dette.get("ratio_dette_revenu_pct", 0))
        except Exception as exc:
            logger.debug("dette_revenu skip: %s", exc)

    # ── Unités absorbées marché neuf (StatCan 34-10-0149-01) ─────────────────
    if not case.get("unites_absorbees"):
        try:
            absorb = fetch_unites_absorbees(city_code, cache_dir)
            if absorb:
                case["unites_absorbees"] = absorb
                logger.debug("unites_absorbees injecté : %s total=%s",
                             city_code, absorb.get("unites_absorbees_total"))
        except Exception as exc:
            logger.debug("unites_absorbees skip: %s", exc)

    # ── SCHL rental market ────────────────────────────────────────────────────
    if not case.get("marche_locatif"):
        try:
            rental = fetch_rental_market(city_code, cache_dir)
            if rental:
                case["marche_locatif"] = rental
                logger.debug("marche_locatif injecté : %s", rental.get("ville"))
        except Exception as exc:
            logger.debug("marche_locatif skip: %s", exc)

    # ── Taux d'inoccupation SCHL ──────────────────────────────────────────────
    if not case.get("taux_inoccupation"):
        try:
            vacance = fetch_vacancy_rate(city_code, cache_dir)
            if vacance:
                case["taux_inoccupation"] = vacance
                logger.debug("taux_inoccupation injecté : %s total=%.1f%%",
                             city_code, vacance.get("taux_total_pct", 0))
        except Exception as exc:
            logger.debug("taux_inoccupation skip: %s", exc)

    # ── NHPI (indice prix logement neuf) ──────────────────────────────────────
    if not case.get("indice_prix_logement"):
        try:
            nhpi = fetch_nhpi(city_code, cache_dir)
            if nhpi:
                case["indice_prix_logement"] = nhpi
                logger.debug("indice_prix_logement injecté : %s indice=%.1f",
                             nhpi.get("ville"), nhpi.get("indice_total", 0))
        except Exception as exc:
            logger.debug("nhpi skip: %s", exc)

    # ── Census démographique (Recensement 2021) ───────────────────────────────
    if not case.get("donnees_sociodemographiques"):
        try:
            census = fetch_census_profile(city_code, cache_dir)
            if census:
                case["donnees_sociodemographiques"] = census
                logger.debug("donnees_sociodemographiques injecté : %s", city_code)
        except Exception as exc:
            logger.debug("census skip: %s", exc)

    # ── Mises en chantier SCHL (StatCan 34-10-0056-01) ───────────────────────
    if not case.get("mises_en_chantier"):
        try:
            chantier = fetch_mises_en_chantier(city_code, cache_dir)
            if chantier:
                case["mises_en_chantier"] = chantier
                logger.debug("mises_en_chantier injecté : %s total=%s/mois",
                             city_code, chantier.get("total_mois"))
        except Exception as exc:
            logger.debug("mises_en_chantier skip: %s", exc)

    # ── Marché neuf — completions & pipeline (StatCan 34-10-0093-01) ────────────
    if not case.get("marche_neuf"):
        try:
            neuf = fetch_marche_neuf(city_code, cache_dir)
            if neuf:
                case["marche_neuf"] = neuf
                logger.debug("marche_neuf injecté : %s completions=%s",
                             city_code, neuf.get("completions_mois"))
        except Exception as exc:
            logger.debug("marche_neuf skip: %s", exc)

    # ── Permis de construction (StatCan 34-10-0066-01) ────────────────────────
    if not case.get("permis_construction"):
        try:
            permis = fetch_permis_construction(city_code, cache_dir)
            if permis:
                case["permis_construction"] = permis
                logger.debug("permis_construction injecté : %s unités/mois=%.0f",
                             city_code, permis.get("unites_residentielles_mois", 0))
        except Exception as exc:
            logger.debug("permis_construction skip: %s", exc)

    # ── Statistiques criminelles CMA (StatCan 35-10-0078-01) ─────────────────
    if not case.get("crime_stats"):
        try:
            crime = fetch_crime_stats(city_code, cache_dir)
            if crime:
                case["crime_stats"] = crime
                logger.debug("crime_stats injecté : %s total=%.1f/100k",
                             city_code, crime.get("taux_criminalite_total", 0))
        except Exception as exc:
            logger.debug("crime_stats skip: %s", exc)

    # ── Rôle municipal ────────────────────────────────────────────────────────
    if not case.get("role_municipal"):
        matricule = str(case.get("matricule") or "").strip() or None
        role: dict = {}

        if city_code == "montreal":
            # Montréal: CSV lookup
            csv_path = cache_dir / "role_mtl.csv"
            if csv_path.exists():
                try:
                    role = lookup_role_mtl(csv_path, matricule=matricule, display_name=display_name)
                except Exception as exc:
                    logger.debug("role_municipal (mtl csv) skip: %s", exc)
        elif city_code in _ROLE_XML_CITIES:
            # Autres villes: XML JSON index lookup
            index_path = cache_dir / f"role_{city_code}_index.json"
            if not index_path.exists():
                # Try to build index from XML if XML is cached
                xml_path = cache_dir / f"role_{city_code}.xml"
                if xml_path.exists():
                    try:
                        build_role_xml_index(xml_path, index_path, city_code)
                    except Exception as exc:
                        logger.debug("role XML index build skip: %s", exc)
            if index_path.exists():
                try:
                    role = lookup_role_xml(index_path, matricule=matricule, display_name=display_name)
                except Exception as exc:
                    logger.debug("role_municipal (xml) skip: %s", exc)

        if role:
            case["role_municipal"] = role
            if not case.get("annee_construction") and role.get("annee_construction"):
                case["annee_construction"] = role["annee_construction"]
            if not case.get("surface") and role.get("superficie_batiment_m2"):
                case["surface"] = role["superficie_batiment_m2"]
            # Backfill evaluation municipale from XML valeur_totale
            if not case.get("evaluation_municipale_totale") and role.get("valeur_totale"):
                case["evaluation_municipale_totale"] = role["valeur_totale"]
            logger.debug("role_municipal injecté : %s (%s)", role.get("matricule83"), city_code)

    # ── Geocode (shared by zonage + CPTAQ + patrimoine + inondable) ─────────
    _coords: tuple[float, float] | None = None
    if display_name and (
        not case.get("zonage_urbanisme")
        or not case.get("zone_agricole")
        or not case.get("patrimoine_culturel")
        or "zone_inondable" not in case
        or "proximite_services" not in case
        or "distance_cbd" not in case
    ):
        try:
            _coords = geocode_address(display_name, cache_dir)
        except Exception as exc:
            logger.debug("geocode skip: %s", exc)

    # ── Distance au CBD (Haversine) ───────────────────────────────────────────
    if "distance_cbd" not in case and _coords and city_code:
        try:
            lat, lng = _coords
            dist_data = compute_distance_cbd(lat, lng, city_code)
            if dist_data:
                case["distance_cbd"] = dist_data
                logger.debug("distance_cbd injecté : %s %.2f km (%s)",
                             city_code, dist_data["distance_cbd_km"],
                             dist_data["interpretation"])
        except Exception as exc:
            logger.debug("distance_cbd skip: %s", exc)

    # ── Zonage urbanisme ──────────────────────────────────────────────────────
    if not case.get("zonage_urbanisme") and _coords:
        try:
            lat, lng = _coords
            zone_info = lookup_zoning_point(city_code, lat, lng, cache_dir)
            if zone_info:
                case["zonage_urbanisme"] = zone_info
                logger.debug("zonage_urbanisme injecté : %s", zone_info)
        except Exception as exc:
            logger.debug("zonage skip: %s", exc)

    # ── CPTAQ zone agricole ───────────────────────────────────────────────────
    if not case.get("zone_agricole") and _coords:
        try:
            lat, lng = _coords
            cptaq = lookup_cptaq(lat, lng, cache_dir)
            if cptaq is not None:
                case["zone_agricole"] = cptaq
                logger.debug("zone_agricole injecté : en_zone=%s", cptaq.get("en_zone_agricole"))
        except Exception as exc:
            logger.debug("cptaq skip: %s", exc)

    # ── Patrimoine culturel ───────────────────────────────────────────────────
    if not case.get("patrimoine_culturel") and _coords:
        try:
            lat, lng = _coords
            pat = lookup_patrimoine(lat, lng, cache_dir)
            if pat is not None:
                case["patrimoine_culturel"] = pat  # {} = not listed, dict = found
                if pat:
                    logger.debug("patrimoine_culturel injecté : %s", pat.get("NOM") or pat.get("NM_BIEN"))
        except Exception as exc:
            logger.debug("patrimoine skip: %s", exc)

    # ── Zones inondables (MELCC) ──────────────────────────────────────────────
    if "zone_inondable" not in case and _coords:
        try:
            lat, lng = _coords
            inond = lookup_inondable(lat, lng, cache_dir)
            if inond is not None:
                case["zone_inondable"] = inond  # {} = hors zone, dict = en zone
                if inond:
                    logger.debug("zone_inondable injectée : récurrence=%s",
                                 inond.get("recurrence"))
        except Exception as exc:
            logger.debug("inondable skip: %s", exc)

    # ── Proximité services (OSM Overpass) ─────────────────────────────────────
    if not case.get("proximite_services") and _coords:
        try:
            lat, lng = _coords
            prox = fetch_proximite_services(lat, lng, cache_dir)
            if prox:
                case["proximite_services"] = prox
                logger.debug("proximite_services injecté : écoles=%s transports=%s",
                             prox.get("ecoles_1km"), prox.get("arrets_transport_500m"))
        except Exception as exc:
            logger.debug("proximite_services skip: %s", exc)

    # ── Proximité axes routiers (OSM Overpass) ────────────────────────────────
    if not case.get("proximite_routes") and _coords:
        try:
            lat, lng = _coords
            routes = fetch_proximite_routes(lat, lng, cache_dir)
            if routes:
                case["proximite_routes"] = routes
                logger.debug("proximite_routes injecté : autoroute=%.1f km interp=%s",
                             routes.get("autoroute_km", 0), routes.get("interpretation"))
        except Exception as exc:
            logger.debug("proximite_routes skip: %s", exc)

    # ── Enseignement post-secondaire (OSM Overpass) ───────────────────────────
    if not case.get("enseignement_postsecondaire") and _coords:
        try:
            lat, lng = _coords
            postsec = fetch_enseignement_postsecondaire(lat, lng, cache_dir)
            if postsec:
                case["enseignement_postsecondaire"] = postsec
                logger.debug("enseignement_postsecondaire injecté : total=%s (%s)",
                             postsec.get("total_postsecondaire"), postsec.get("interpretation"))
        except Exception as exc:
            logger.debug("enseignement_postsecondaire skip: %s", exc)

    # ── Nuisances environnementales (OSM Overpass) ────────────────────────────
    if not case.get("nuisances_environnementales") and _coords:
        try:
            lat, lng = _coords
            nuisances = fetch_nuisances_environnementales(lat, lng, cache_dir)
            if nuisances:
                case["nuisances_environnementales"] = nuisances
                logger.debug("nuisances_environnementales injecté : score=%s (%s)",
                             nuisances.get("score_nuisances"), nuisances.get("interpretation"))
        except Exception as exc:
            logger.debug("nuisances_environnementales skip: %s", exc)

    # ── Données climatiques (Open-Meteo archive) ──────────────────────────────
    if not case.get("donnees_climatiques") and _coords:
        try:
            lat, lng = _coords
            climat = fetch_donnees_climatiques(lat, lng, cache_dir)
            if climat:
                case["donnees_climatiques"] = climat
                logger.debug("donnees_climatiques injecté : T_moy=%.1f°C gel=%d j",
                             climat.get("temperature_moyenne_annuelle", 0),
                             climat.get("jours_gel", 0))
        except Exception as exc:
            logger.debug("donnees_climatiques skip: %s", exc)

    # ── Indice d'abordabilité (calcul interne, dépend B5+B11+B15) ────────────
    if not case.get("indice_abordabilite"):
        try:
            abord = compute_indice_abordabilite(case)
            if abord:
                case["indice_abordabilite"] = abord
                logger.debug("indice_abordabilite : loyer=%s%% mensualite=%s%%",
                             abord.get("ratio_loyer_revenu_pct"),
                             abord.get("ratio_mensualite_revenu_pct"))
        except Exception as exc:
            logger.debug("indice_abordabilite skip: %s", exc)

    # ── Score marché synthétique (calcul interne, dépend B10+B14+B16+B17+B19+B21)
    if not case.get("score_marche"):
        try:
            score = compute_score_marche(case)
            if score:
                case["score_marche"] = score
                logger.debug("score_marche : %.1f/10 (%s)",
                             score.get("score_marche", 0), score.get("interpretation"))
        except Exception as exc:
            logger.debug("score_marche skip: %s", exc)

    # ── Rendement locatif / taux de capitalisation (calcul interne) ───────────
    if not case.get("rendement_locatif"):
        try:
            rend = compute_rendement_locatif(case)
            if rend:
                case["rendement_locatif"] = rend
                logger.debug("rendement_locatif : brut=%.2f%% net=%.2f%% (%s)",
                             rend.get("taux_capitalisation_brut_pct", 0),
                             rend.get("taux_capitalisation_net_estime_pct", 0),
                             rend.get("interpretation"))
        except Exception as exc:
            logger.debug("rendement_locatif skip: %s", exc)

    # ── Score composite d'investissement (calcul interne, dépend B30+B31+B32) ─
    if not case.get("score_investissement"):
        try:
            invest = compute_score_investissement(case)
            if invest:
                case["score_investissement"] = invest
                logger.debug("score_investissement : %.2f/10 → %s",
                             invest.get("score_investissement", 0),
                             invest.get("recommandation"))
        except Exception as exc:
            logger.debug("score_investissement skip: %s", exc)

    # ── Profil fiscal municipal (calcul interne, taux 2024 hardcodés) ─────────
    if not case.get("taxes_municipales"):
        try:
            taxes = compute_taxes_municipales(case, city_code)
            if taxes:
                case["taxes_municipales"] = taxes
                logger.debug("taxes_municipales : %s %.3f%% → %d $/an",
                             city_code,
                             taxes.get("taux_taxation_pct", 0),
                             taxes.get("taxes_annuelles_estimees", 0))
        except Exception as exc:
            logger.debug("taxes_municipales skip: %s", exc)

    # ── Coûts de possession totaux (calcul interne, dépend B30+B34) ──────────
    if not case.get("couts_possession"):
        try:
            couts = compute_couts_possession(case)
            if couts:
                case["couts_possession"] = couts
                logger.debug("couts_possession : total=%d $/mois (%s)",
                             couts.get("total_mensuel", 0),
                             couts.get("interpretation"))
        except Exception as exc:
            logger.debug("couts_possession skip: %s", exc)

    # ── Ratio prix/loyer (calcul interne, dépend B5 + évaluation) ─────────────
    if not case.get("ratio_prix_loyer"):
        try:
            plr = compute_ratio_prix_loyer(case)
            if plr:
                case["ratio_prix_loyer"] = plr
                logger.debug("ratio_prix_loyer : %.1f (%s)",
                             plr.get("ratio_prix_loyer", 0), plr.get("signal"))
        except Exception as exc:
            logger.debug("ratio_prix_loyer skip: %s", exc)

    # ── Vétusté du bâtiment (calcul interne, depuis annee_construction) ───────
    if not case.get("vetuste_batiment"):
        try:
            vetuste = compute_vetuste_batiment(case)
            if vetuste:
                case["vetuste_batiment"] = vetuste
                logger.debug("vetuste_batiment : %d ans (%s) deprec=%.1f%%",
                             vetuste.get("age_ans", 0),
                             vetuste.get("categorie"),
                             vetuste.get("taux_depreciation_pct", 0))
        except Exception as exc:
            logger.debug("vetuste_batiment skip: %s", exc)
