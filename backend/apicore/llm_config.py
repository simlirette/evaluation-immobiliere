"""api/llm_config.py — Constantes LLM et définitions des outils agent (T6.1).

Aucune dépendance sur SESSIONS_DIR ou modules engine.
Extrait de api.py (T6.1 — découpe api.py).
"""
from __future__ import annotations

_OPENAI_MODEL_DEFAULT = "gpt-4o-mini"
_LLM_MAX_TOKENS = 1400

_AGENT_SYSTEM_PROMPTS: dict[str, str] = {
    "auto": (
        "Tu es un assistant expert en évaluation immobilière québécoise, formé selon les normes OEAQ et CUSPAP 2026.\n"
        "Réponds en français. Sois concis et précis. N'invente aucune donnée.\n"
    ),
    "data-facts": (
        "Tu es un agent de collecte et d'analyse de faits pour l'évaluation immobilière. "
        "Extraits les données pertinentes et identifie les sources.\n"
    ),
    "comps-market": (
        "Tu es un agent d'analyse de marché et de sélection de comparables. "
        "Évalue la pertinence et la qualité des ventes comparables.\n"
    ),
    "valuation-draft": (
        "Tu es un agent de calcul de valeur pour l'évaluation immobilière. "
        "Applique les approches comparative, coût et revenu selon les normes OEAQ.\n"
    ),
    "compliance-qa": (
        "Tu es un agent de contrôle de conformité OEAQ/CUSPAP. "
        "Identifie les non-conformités et formule des recommandations.\n"
    ),
    "redaction": (
        "Tu es un agent de rédaction de rapports d'évaluation immobilière. "
        "Rédige en français canadien professionnel, normes OEAQ/CUSPAP.\n"
    ),
}

_AGENT_SYSTEM_LIMITS = (
    "\n\n---\n"
    "LIMITES ABSOLUES :\n"
    "- N'invente aucune donnée non fournie dans le contexte.\n"
    "- Ne certifie pas, ne signe pas — tu es un assistant, pas un É.A.\n"
    "- Si une information manque, dis-le explicitement.\n"
)

# Tool definitions (JSON schema pour l'API OpenAI)
_FETCH_ARTIFACT_TOOL = {
    "type": "function",
    "function": {
        "name": "fetch_artifact",
        "description": (
            "Récupère le contenu d'un artefact produit par le pipeline d'évaluation. "
            "Utilise cet outil pour obtenir des données précises : fiche bien, "
            "comparables retenus, calculs de valeur, non-conformités, brouillon rapport."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "step": {
                    "type": "string",
                    "enum": [
                        "mandat-intake", "data-facts", "amu-analyst",
                        "comps-market", "valuation-draft", "compliance-qa", "redaction",
                    ],
                    "description": "L'agent/étape qui a produit l'artefact.",
                },
                "artifact_name": {
                    "type": "string",
                    "description": (
                        "Nom du fichier artefact, ex: fiche_bien.json, "
                        "comparables_proposes.json, calculs_approche_comparative.json, "
                        "rapport_non_conformites.json, brouillon_rapport.md"
                    ),
                },
            },
            "required": ["step", "artifact_name"],
        },
    },
}

_SEARCH_KNOWLEDGE_TOOL = {
    "type": "function",
    "function": {
        "name": "search_knowledge",
        "description": (
            "Recherche sémantique dans la base de connaissances normative "
            "(NPP OEAQ, CUSPAP 2026, MEFQ 2025, LFM, règlements OEAQ). "
            "Utilise cet outil pour citer une règle spécifique, vérifier une norme, "
            "ou appuyer une affirmation sur une source officielle."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Question ou extrait à rechercher dans les normes.",
                },
                "domain": {
                    "type": "string",
                    "description": "Filtrer par domaine (optionnel).",
                },
            },
            "required": ["query"],
        },
    },
}

_SEARCH_COMPARABLES_TOOL = {
    "type": "function",
    "function": {
        "name": "search_comparables",
        "description": (
            "Recherche et filtre les comparables disponibles dans le dossier. "
            "Utilise cet outil pour trouver des ventes selon des critères précis."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "prix_min": {"type": "number", "description": "Prix minimum en $"},
                "prix_max": {"type": "number", "description": "Prix maximum en $"},
                "distance_max_km": {"type": "number", "description": "Distance max en km"},
                "date_min": {"type": "string", "description": "Date minimale ISO 8601"},
                "date_max": {"type": "string", "description": "Date maximale ISO 8601"},
                "top_n": {"type": "integer", "description": "Max résultats (défaut 10)"},
            },
            "required": [],
        },
    },
}

_RUN_CALCULATION_TOOL = {
    "type": "function",
    "function": {
        "name": "run_calculation",
        "description": (
            "Recalcule la valeur par une approche avec des paramètres optionnels. "
            "Lecture seule — ne modifie pas le dossier."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "approche": {
                    "type": "string",
                    "enum": ["approche_comparative", "approche_cout", "approche_revenu",
                             "approche_liquidation", "approche_avant_apres"],
                },
                "overrides": {
                    "type": "object",
                    "description": "Paramètres à surcharger pour ce calcul.",
                },
            },
            "required": ["approche"],
        },
    },
}

_RERUN_STEP_TOOL = {
    "type": "function",
    "function": {
        "name": "rerun_step",
        "description": (
            "Déclenche la ré-exécution d'une étape pipeline. "
            "Gate checkpoint vérifié automatiquement."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "step": {
                    "type": "string",
                    "enum": ["comps-market", "valuation-draft", "compliance-qa", "redaction"],
                },
                "raison": {"type": "string", "description": "Raison de la ré-exécution"},
            },
            "required": ["step"],
        },
    },
}

AGENT_TOOLS = [
    _FETCH_ARTIFACT_TOOL,
    _SEARCH_KNOWLEDGE_TOOL,
    _SEARCH_COMPARABLES_TOOL,
    _RUN_CALCULATION_TOOL,
    _RERUN_STEP_TOOL,
]
