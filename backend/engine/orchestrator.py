"""Orchestrateur de mandat — routing automatique par type de dossier.

Responsabilités :
- classify_dossier(case) → mandat_type (str)
- load_plan_for_mandat(mandat_type) → PlanMandat
- PlanOrchestrator.build_engine(case) → (RuntimeEngine, PlanMandat)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

PLANS_PATH = Path(__file__).resolve().parent.parent / "integration" / "PLANS-MANDATS-V0.yaml"

# ──────────────────────────────────────────────────────────────────────────────
# Modèle de plan
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class PlanMandat:
    mandat_type: str
    label: str
    format_rapport: str                      # abrege | narratif_complet | mise_a_jour
    methodes_requises: list[str]
    methodes_optionnelles: list[str]
    methode_preponderante: str
    umpp_requis: bool
    visite_physique: str                     # obligatoire | selon_etendue_travail
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "mandat_type": self.mandat_type,
            "label": self.label,
            "format_rapport": self.format_rapport,
            "methodes_requises": self.methodes_requises,
            "methodes_optionnelles": self.methodes_optionnelles,
            "methode_preponderante": self.methode_preponderante,
            "umpp_requis": self.umpp_requis,
            "visite_physique": self.visite_physique,
            "notes": self.notes,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Parsing YAML minimal (sans dépendance externe)
# ──────────────────────────────────────────────────────────────────────────────

def _parse_plans_yaml(path: Path) -> tuple[dict[str, PlanMandat], dict[str, str], str]:
    """Parse PLANS-MANDATS-V0.yaml. Retourne (plans, mapping, default_type)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    plans: dict[str, PlanMandat] = {}
    type_bien_mapping: dict[str, str] = {}
    default_type = "residentiel_standard"

    # Sections principales
    section: str | None = None       # "plans" | "type_bien_mapping"
    plan_key: str | None = None
    plan_data: dict = {}
    list_field: str | None = None    # nom du champ liste en cours

    def _flush_plan() -> None:
        if plan_key and plan_data:
            plans[plan_key] = PlanMandat(
                mandat_type=plan_key,
                label=plan_data.get("label", plan_key),
                format_rapport=plan_data.get("format_rapport", "narratif_complet"),
                methodes_requises=plan_data.get("methodes_requises", []),
                methodes_optionnelles=plan_data.get("methodes_optionnelles", []),
                methode_preponderante=plan_data.get("methode_preponderante", "approche_comparative"),
                umpp_requis=bool(plan_data.get("umpp_requis", True)),
                visite_physique=plan_data.get("visite_physique", "obligatoire"),
                notes=plan_data.get("notes", ""),
            )

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        # Détection sections de premier niveau
        if re.match(r"^plans\s*:", line):
            if plan_key:
                _flush_plan()
                plan_key = None
                plan_data = {}
            section = "plans"
            list_field = None
            continue

        if re.match(r"^type_bien_mapping\s*:", line):
            if plan_key:
                _flush_plan()
                plan_key = None
                plan_data = {}
            section = "type_bien_mapping"
            list_field = None
            continue

        if re.match(r"^default_mandat_type\s*:", line):
            val = line.split(":", 1)[1].strip()
            if val:
                default_type = val
            continue

        if section == "plans":
            indent = len(line) - len(line.lstrip())

            # Nouveau plan (indent=2)
            if indent == 2 and re.match(r"^\s{2}\w[\w_-]*\s*:", line):
                _flush_plan()
                plan_key = stripped.rstrip(":")
                plan_data = {}
                list_field = None
                continue

            # Champs d'un plan (indent=4)
            if indent == 4 and plan_key:
                if ":" in stripped:
                    key, _, val = stripped.partition(":")
                    key = key.strip()
                    val = val.strip()
                    if val == "" or val == "[]":
                        list_field = key
                        plan_data[key] = []
                    elif val in {"true", "false"}:
                        plan_data[key] = val == "true"
                        list_field = None
                    elif val.startswith(">"):
                        plan_data[key] = ""
                        list_field = None
                    else:
                        plan_data[key] = val
                        list_field = None
                continue

            # Continuation bloc scalaire multiligne (indent=6, sans -)
            if indent == 6 and plan_key and not stripped.startswith("-"):
                for k, v in plan_data.items():
                    if isinstance(v, str) and k not in ("format_rapport", "methode_preponderante", "visite_physique", "label"):
                        # Champ notes (continuation ">" block)
                        if k == "notes":
                            plan_data[k] = (v + " " + stripped).strip()
                continue

            # Items de liste (indent=6, commence par -)
            if indent == 6 and plan_key and stripped.startswith("-"):
                item = stripped[1:].strip()
                if list_field and list_field in plan_data and isinstance(plan_data[list_field], list):
                    plan_data[list_field].append(item)
                continue

        if section == "type_bien_mapping":
            if ":" in stripped:
                key, _, val = stripped.partition(":")
                key = key.strip()
                val = val.strip()
                if key and val:
                    type_bien_mapping[key] = val

    _flush_plan()
    return plans, type_bien_mapping, default_type


# Cache module-level
_PLANS_CACHE: dict[str, PlanMandat] | None = None
_MAPPING_CACHE: dict[str, str] | None = None
_DEFAULT_TYPE_CACHE: str | None = None


def _load_plans() -> tuple[dict[str, PlanMandat], dict[str, str], str]:
    global _PLANS_CACHE, _MAPPING_CACHE, _DEFAULT_TYPE_CACHE
    if _PLANS_CACHE is None:
        _PLANS_CACHE, _MAPPING_CACHE, _DEFAULT_TYPE_CACHE = _parse_plans_yaml(PLANS_PATH)
    return _PLANS_CACHE, _MAPPING_CACHE or {}, _DEFAULT_TYPE_CACHE or "residentiel_standard"


# ──────────────────────────────────────────────────────────────────────────────
# API publique
# ──────────────────────────────────────────────────────────────────────────────

def classify_dossier(case: dict) -> str:
    """Détermine le type de mandat à partir du dossier.

    Règles de priorité :
    1. ``mandat_type`` explicite dans le case
    2. ``but_evaluation`` == "assurance" → assurance
    3. ``type_bien`` → lookup dans le mapping YAML
    4. Recherche partielle par mot-clé dans ``type_bien``
    5. Default configuré dans YAML (residentiel_standard)
    """
    _, mapping, default = _load_plans()

    # 1. Mandat explicite
    if case.get("mandat_type"):
        return str(case["mandat_type"]).strip().lower()

    # 2. But évaluation → routing spécialisé (T4.1+T4.2)
    but = str(case.get("but_evaluation", "")).lower()
    if "assurance" in but:
        return "assurance"
    if any(k in but for k in ("succession", "héritage", "heritage", "décès", "deces")):
        return "succession"
    if any(k in but for k in ("donation", "roulement", "transfert")):
        return "donation"
    if any(k in but for k in ("contestation", "rôle", "role", "triennal", "evaluation_municipale")):
        return "contestation_role"
    if any(k in but for k in ("financement", "hypothécaire", "hypothecaire", "prêt", "pret")):
        return "financement"
    if any(k in but for k in ("expropriation", "expropriateur")):
        return "expropriation"
    if any(k in but for k in ("liquidation", "vente_forcée", "vente_forcee", "forcé", "force")):
        return "liquidation"

    # 3. Lookup exact type_bien
    type_bien = str(case.get("type_bien", "")).strip().lower()
    if type_bien in mapping:
        return mapping[type_bien]

    # 4. Recherche partielle par mot-clé
    keywords_to_mandat = [
        (["plex", "duplex", "triplex", "quadruplex", "quintuplex"], "residentiel_multifamilial"),
        (["multiresidentiel", "immeuble_revenus", "immeuble_locatif", "grand_multi"], "immeuble_revenus"),
        (["industriel", "entrepot", "entrepôt", "manufacture", "usine"], "industriel"),
        (["commercial", "bureau", "bureaux", "commerce", "magasin", "institutionnel"], "commercial"),
        (["terrain", "lot", "vacant"], "terrain"),
        (["mise_a_jour", "mise_à_jour", "update"], "mise_a_jour"),
        (["assurance"], "assurance"),
        (["unifamilial", "maison", "bungalow", "condo", "condominium", "jumelé", "jumele", "rangee", "rangée"], "residentiel_standard"),
    ]
    for keywords, mandat in keywords_to_mandat:
        if any(kw in type_bien for kw in keywords):
            return mandat

    return default


def load_plan_for_mandat(mandat_type: str) -> PlanMandat:
    """Charge le PlanMandat pour un type de mandat. Lève KeyError si introuvable."""
    plans, _, _ = _load_plans()
    if mandat_type not in plans:
        raise KeyError(f"Type de mandat inconnu: '{mandat_type}'. Plans disponibles: {sorted(plans)}")
    return plans[mandat_type]


def available_mandat_types() -> list[str]:
    """Retourne la liste des types de mandats configurés."""
    plans, _, _ = _load_plans()
    return sorted(plans)


# ──────────────────────────────────────────────────────────────────────────────
# Orchestrateur
# ──────────────────────────────────────────────────────────────────────────────

class PlanOrchestrator:
    """Route un dossier vers le plan de mandat approprié et configure le RuntimeEngine.

    Usage :
        orchestrator = PlanOrchestrator()
        engine, plan = orchestrator.build_engine(case)
        result = engine.run_case_data(enriched_case, out_dir)
    """

    def classify(self, case: dict) -> str:
        return classify_dossier(case)

    def build_engine(self, case: dict) -> tuple:
        """Classifie le dossier, charge le plan et retourne (RuntimeEngine, PlanMandat).

        Le ``case`` n'est PAS modifié. L'appelant doit fusionner ``plan.to_dict()``
        dans le case avant de passer au RuntimeEngine si les champs de plan
        doivent apparaître dans les artefacts.
        """
        # Import ici pour éviter import circulaire
        from engine.runtime import RuntimeEngine

        mandat_type = classify_dossier(case)
        plan = load_plan_for_mandat(mandat_type)
        engine = RuntimeEngine()
        return engine, plan

    def enrich_case(self, case: dict, plan: PlanMandat) -> dict:
        """Retourne un nouveau dict case enrichi des champs du plan.

        Les champs du plan sont ajoutés sans écraser les champs existants.
        """
        plan_fields = {
            "mandat_type": plan.mandat_type,
            "format_rapport": plan.format_rapport,
            "methodes_requises": plan.methodes_requises,
            "methode_preponderante": plan.methode_preponderante,
            "umpp_requis": plan.umpp_requis,
        }
        return {**plan_fields, **case}
