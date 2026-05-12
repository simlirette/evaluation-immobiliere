from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
import json
import os
import re
import time
import ast

from engine.audit import append_audit_log
from engine.skills import DEFAULT_SKILLS_BY_AGENT, load_agent_config_skills, load_agent_system_prompt
from engine.tools import search_comparables, validate_schema
from engine.valuation import calculate_valuation_trace


@dataclass
class RuntimeStep:
    name: str
    reads: list[str]
    writes: list[str]
    skills: list[str] = field(default_factory=list)
    agent_config: str | None = None


class PipelineValidationError(ValueError):
    pass


REQUIRED_FIELDS_BY_ARTIFACT = {
    "default": ["dossier_id", "step", "artifact", "source_fixture"],
    "statut_sortie.json": ["dossier_id", "step", "artifact", "source_fixture", "status", "blocking_failures", "warnings"],
    "comparables_proposes.json": ["dossier_id", "step", "artifact", "source_fixture", "comparables"],
    "calculs_approche_comparative.json": ["dossier_id", "step", "artifact", "source_fixture", "method", "value", "input_count", "trace"],
    "calculs_approche_cout.json": ["dossier_id", "step", "artifact", "source_fixture", "method", "value", "input_count", "trace"],
    "calculs_approche_revenu.json": ["dossier_id", "step", "artifact", "source_fixture", "method", "value", "input_count", "trace"],
    "umpp_conclusion.json": ["dossier_id", "step", "artifact", "source_fixture", "umpp"],
}

CONTRACT_CHECKS_BY_ARTIFACT = {
    "fiche_bien.json": {
        "required_fields": ["date_reference", "surface", "confidence", "source_ids"],
        "rules": ["CONF001"],
    },
    "comparables_proposes.json": {
        "required_fields": ["comparables"],
        "rules": ["CONF002", "CONF003", "CONF005", "CONF006"],
    },
    "statut_sortie.json": {
        "required_fields": ["status", "blocking_failures", "warnings"],
        "rules": ["CONF004", "CONF007"],
    },
}

CONTRACTS_DATA_PATH = Path(__file__).resolve().parent.parent / "mvp" / "CONTRATS-DONNEES-V0.yaml"
INTEGRATION_DIR = Path(__file__).resolve().parent.parent / "integration"

# Artifacts enrichis par LLM : artifact → champ cible dans le payload
_LLM_TEXT_FIELD_BY_ARTIFACT: dict[str, str] = {
    "fiche_bien.json": "analyse_contextuelle",
    "comparables_proposes.json": "analyse_marche",
    "justifications_comparables.json": "synthese_comparables",
    "calculs_approche_comparative.json": "commentaire",
    "calculs_approche_cout.json": "commentaire",
    "calculs_approche_revenu.json": "commentaire",
    "hypotheses_explicites.json": "analyse_hypotheses",
    "rapport_non_conformites.json": "analyse_conformite",
    "recommandations_corrections.md": "_raw_md",
    "brouillon_valeur.md": "_raw_md",
    "amu_analyse.md": "_raw_md",
    # brouillon_rapport.md : géré par generate_brouillon_rapport — ne pas dupliquer
}
_CONTRACT_TREE_CACHE: dict | None = None


def _name_from_agent_config(value: str) -> str:
    value = value.strip()
    value = value.replace("AGENTCONFIG-", "").replace("-V0.yaml", "")
    return value.lower()


def load_steps_from_pipeline_yaml(pipeline_path: Path) -> list[RuntimeStep]:
    """Parse le fichier pipeline YAML v0 sans dependance externe."""
    if not pipeline_path.exists():
        raise PipelineValidationError(f"Pipeline introuvable: {pipeline_path}")

    lines = pipeline_path.read_text(encoding="utf-8").splitlines()
    steps: list[RuntimeStep] = []
    current_name: str | None = None
    current_agent_config: str | None = None
    current_skills: list[str] = []
    current_reads: list[str] = []
    current_writes: list[str] = []
    mode: str | None = None

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        if re.match(r"^\s*- step:\s*\d+", line):
            if current_name:
                steps.append(RuntimeStep(current_name, current_reads, current_writes, current_skills, current_agent_config))
            current_name = None
            current_agent_config = None
            current_skills = []
            current_reads = []
            current_writes = []
            mode = None
            continue

        if stripped.startswith("agent_config:"):
            agent_file = stripped.split(":", 1)[1].strip()
            current_name = _name_from_agent_config(agent_file)
            current_agent_config = agent_file
            current_skills = load_agent_config_skills(pipeline_path.parent / agent_file)
            continue

        if stripped == "reads:":
            mode = "reads"
            continue

        if stripped == "writes:":
            mode = "writes"
            continue

        if stripped.startswith("-") and mode in {"reads", "writes"}:
            item = stripped[1:].strip()
            if mode == "reads":
                current_reads.append(item)
            else:
                current_writes.append(item)
            continue

        if stripped and not stripped.startswith("-"):
            mode = None

    if current_name:
        steps.append(RuntimeStep(current_name, current_reads, current_writes, current_skills, current_agent_config))

    validate_pipeline_steps(steps, pipeline_path)
    return steps


def validate_pipeline_steps(steps: list[RuntimeStep], pipeline_path: Path | None = None) -> None:
    errors: list[str] = []
    seen: set[str] = set()

    if not steps:
        errors.append("aucune etape runtime trouvee")

    for i, step in enumerate(steps, start=1):
        if not step.name:
            errors.append(f"step {i}: agent_config manquant")
        if step.name in seen:
            errors.append(f"step {i}: agent duplique '{step.name}'")
        seen.add(step.name)
        if not step.reads:
            errors.append(f"step {i} ({step.name}): reads vide")
        if not step.writes:
            errors.append(f"step {i} ({step.name}): writes vide")
        for artifact in step.writes:
            if "." not in artifact:
                errors.append(f"step {i} ({step.name}): extension manquante pour '{artifact}'")

    if errors:
        prefix = f"{pipeline_path}: " if pipeline_path else ""
        raise PipelineValidationError(prefix + "; ".join(errors))


def _skills_for_agent(agent_name: str) -> list[str]:
    return list(DEFAULT_SKILLS_BY_AGENT[agent_name])


DEFAULT_STEPS = [
    RuntimeStep("data-facts", ["dossier_input", "documents_sources"], ["fiche_bien.json", "timeline_faits.json", "source_index.json"], _skills_for_agent("data-facts"), "AGENTCONFIG-DATA-FACTS-V0.yaml"),
    RuntimeStep("amu-analyst", ["fiche_bien.json", "source_index.json"], ["umpp_conclusion.json", "amu_analyse.md"], _skills_for_agent("amu-analyst"), "AGENTCONFIG-AMU-ANALYST-V0.yaml"),
    RuntimeStep("comps-market", ["fiche_bien.json", "umpp_conclusion.json", "source_index.json", "market_data_sources"], ["comparables_proposes.json", "justifications_comparables.json", "source_index.json"], _skills_for_agent("comps-market"), "AGENTCONFIG-COMPS-MARKET-V0.yaml"),
    RuntimeStep("valuation-draft", ["comparables_proposes.json", "couts_reference", "revenus_depenses", "source_index.json"], ["calculs_approche_comparative.json", "calculs_approche_cout.json", "calculs_approche_revenu.json", "hypotheses_explicites.json", "brouillon_valeur.md"], _skills_for_agent("valuation-draft"), "AGENTCONFIG-VALUATION-DRAFT-V0.yaml"),
    RuntimeStep("compliance-qa", ["calculs_approche_comparative.json", "calculs_approche_cout.json", "calculs_approche_revenu.json", "hypotheses_explicites.json", "source_index.json"], ["rapport_non_conformites.json", "statut_sortie.json", "recommandations_corrections.md"], _skills_for_agent("compliance-qa"), "AGENTCONFIG-COMPLIANCE-QA-V0.yaml"),
    RuntimeStep("redaction", ["statut_sortie.json", "recommandations_corrections.md", "amu_analyse.md", "source_index.json"], ["brouillon_rapport.md", "annexe_sources.md"], _skills_for_agent("redaction"), "AGENTCONFIG-REDACTION-V0.yaml"),
]


def _build_enrichment_prompt(step_name: str, artifact: str, payload: dict, case: dict) -> str:
    """Construit le prompt utilisateur pour l'enrichissement LLM d'un artefact."""
    dossier_id = case.get("dossier_id", "—")
    type_bien = str(case.get("type_bien", "—")).replace("_", " ")
    zone = case.get("zone", "—")
    date_ref = case.get("date_reference", "—")
    base = f"Dossier: {dossier_id} | Type de bien: {type_bien} | Zone: {zone} | Date de référence: {date_ref}\n\n"

    if artifact == "fiche_bien.json":
        surface = payload.get("surface", {})
        surface_str = f"{surface.get('value', '—')} {surface.get('unit', '')}" if isinstance(surface, dict) else str(surface)
        return base + (
            f"DONNÉES DE LA FICHE BIEN :\n"
            f"Surface : {surface_str}\n"
            f"Confiance : {payload.get('confidence', '—')}\n"
            f"Sources : {payload.get('source_ids', [])}\n\n"
            "Rédige en 2–3 paragraphes une analyse contextuelle professionnelle du bien identifié. "
            "Inclus : description physique probable, localisation et contexte de marché local. "
            "Sois factuel et n'invente aucune donnée absente du contexte fourni."
        )

    if artifact in {"calculs_approche_comparative.json", "calculs_approche_cout.json", "calculs_approche_revenu.json"}:
        approach_labels = {
            "calculs_approche_comparative.json": "comparaison directe",
            "calculs_approche_cout.json": "coût",
            "calculs_approche_revenu.json": "revenu",
        }
        label = approach_labels[artifact]
        trace_str = json.dumps(payload.get("trace", {}), ensure_ascii=False)[:400]
        return base + (
            f"CALCULS — APPROCHE PAR {label.upper()} :\n"
            f"Valeur indiquée : {payload.get('value', '—')} $\n"
            f"Nombre d'intrants : {payload.get('input_count', '—')}\n"
            f"Trace de calcul : {trace_str}\n\n"
            f"Rédige un commentaire professionnel de 2–3 phrases sur l'approche par {label}. "
            "Explique la fiabilité de cet indicateur de valeur et les principales hypothèses retenues. "
            "Reste factuel."
        )

    if artifact == "comparables_proposes.json":
        comps = payload.get("comparables", [])
        comps_preview = json.dumps(comps[:3], ensure_ascii=False)[:600]
        return base + (
            f"COMPARABLES PROPOSÉS ({len(comps)} au total) :\n{comps_preview}\n\n"
            "Rédige une analyse de marché professionnelle en 2–3 paragraphes basée sur ces comparables. "
            "Inclus : tendances de prix observées, niveau d'activité du marché, homogénéité du corpus de ventes."
        )

    if artifact == "justifications_comparables.json":
        justs = payload.get("justifications", [])
        justs_str = json.dumps(justs, ensure_ascii=False)[:400]
        return base + (
            f"JUSTIFICATIONS COMPARABLES :\n{justs_str}\n\n"
            "Rédige une synthèse de 1–2 paragraphes expliquant les critères de sélection appliqués "
            "et la qualité du corpus de comparables retenu pour cette évaluation."
        )

    if artifact == "hypotheses_explicites.json":
        hyps = payload.get("hypotheses", [])
        hyps_str = json.dumps(hyps[:5], ensure_ascii=False)[:500]
        return base + (
            f"HYPOTHÈSES EXPLICITES :\n{hyps_str}\n\n"
            "Analyse la solidité de ces hypothèses en 1–2 paragraphes. "
            "Identifie celles qui sont les plus vulnérables et explique pourquoi."
        )

    if artifact == "rapport_non_conformites.json":
        blocking = payload.get("blocking_failures", [])
        warnings = payload.get("warnings", [])
        return base + (
            f"BLOCAGES ({len(blocking)}) : {'; '.join(blocking[:5])}\n"
            f"AVERTISSEMENTS ({len(warnings)}) : {'; '.join(warnings[:5])}\n\n"
            "Rédige une analyse de conformité professionnelle de 2–3 paragraphes. "
            "Pour chaque non-conformité : nature du problème, impact sur la fiabilité du rapport, "
            "action corrective prioritaire."
        )

    if artifact == "recommandations_corrections.md":
        recs = payload.get("recommendations", [])
        recs_str = "\n".join(f"- {r}" for r in recs[:10])
        return base + (
            f"RECOMMANDATIONS ACTUELLES :\n{recs_str}\n\n"
            "Rédige un mémo de corrections professionnel en Markdown adressé à l'évaluateur. "
            "Structure : titre, corrections bloquantes par priorité décroissante, améliorations suggérées, prochaines étapes. "
            "Sois précis et actionnable. Inclure les codes de règle (B002, W003, etc.) pour chaque item."
        )

    if artifact == "brouillon_valeur.md":
        summary = payload.get("summary", {})
        return base + (
            f"RÉSUMÉ DE VALUATION :\n{json.dumps(summary, ensure_ascii=False)}\n\n"
            "Rédige un brouillon de conclusion de valeur en Markdown (format professionnel OEAQ). "
            "Inclus : valeur principale retenue et fourchette de confiance, "
            "approche dominante avec justification, prochaines étapes pour finaliser le rapport."
        )

    if artifact == "amu_analyse.md":
        umpp = payload.get("umpp", {})
        usage_retenu = str(umpp.get("usage_retenu", type_bien)).replace("_", " ")
        criteres = umpp.get("criteres", {})
        return base + (
            f"ANALYSE AMU :\n"
            f"Type de bien : {type_bien} | Zone : {zone}\n"
            f"Usage retenu (UMPP) : {usage_retenu}\n"
            f"Criteres : {criteres}\n"
            f"UMPP differe usage actuel : {umpp.get('umpp_differe_usage_actuel', False)}\n\n"
            "Redige l'Analyse du Meilleur Usage (AMU) professionnelle en Markdown, "
            "conforme a la Norme de pratique professionnelle OEAQ. "
            "Structure : titre, 4 criteres numerotes avec justification, conclusion UMPP. "
            "Inclure le lien entre l'UMPP et le choix des approches d'evaluation. "
            "Ton professionnel, factuel, 3-4 paragraphes minimum."
        )

    # Fallback générique
    payload_str = json.dumps(payload, ensure_ascii=False)[:600]
    return base + (
        f"Artefact : {artifact} | Étape : {step_name}\nDonnées : {payload_str}\n\n"
        "Fournis une analyse professionnelle concise (2–3 paragraphes) de ces données "
        "dans le contexte d'une évaluation immobilière québécoise conforme aux normes OEAQ."
    )


class RuntimeEngine:
    def __init__(self, steps: list[RuntimeStep] | None = None, strict_mode: bool = True) -> None:
        self.steps = steps or DEFAULT_STEPS
        self.strict_mode = strict_mode
        validate_pipeline_steps(self.steps)

    def _enrich_artifact_llm(
        self,
        step: RuntimeStep,
        artifact: str,
        payload: dict,
        case: dict,
    ) -> dict:
        """Enrichit un artefact via LLM si disponible. Retourne payload inchangé si LLM indisponible."""
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            return payload

        target_field = _LLM_TEXT_FIELD_BY_ARTIFACT.get(artifact)
        if not target_field:
            return payload

        # brouillon_rapport.md already handled by generate_brouillon_rapport
        if artifact == "brouillon_rapport.md":
            return payload

        system_prompt = ""
        if step.agent_config:
            config_path = INTEGRATION_DIR / step.agent_config
            system_prompt = load_agent_system_prompt(config_path)

        if not system_prompt:
            return payload

        user_prompt = _build_enrichment_prompt(step.name, artifact, payload, case)

        try:
            import openai as _openai  # type: ignore
            client = _openai.OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                max_tokens=1200,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            result = (resp.choices[0].message.content or "").strip()
            if result:
                return {**payload, target_field: result}
        except Exception:
            pass  # LLM enrichment is optional — never block pipeline

        return payload

    def _compute_qa(self, case: dict) -> tuple[str, list[str], list[str]]:
        blocking: list[str] = []
        warnings: list[str] = []

        if not case.get("dossier_id"):
            blocking.append("B001: dossier_id manquant")
        if not case.get("date_reference"):
            blocking.append("B001: date_reference manquante")

        reference_date = _parse_iso_date(case.get("date_reference"))

        for c in case.get("comparables", []):
            if "source_id" not in c:
                blocking.append("B002: comparable sans source_id")
            sale_date = _parse_iso_date(c.get("date_vente"))
            if reference_date and sale_date and sale_date > reference_date:
                blocking.append("B003: vente comparable future vs date_reference")
            max_distance_warning = float(
                _contract_value(("contracts", "rapport_conformite", "constraints", "max_comparable_distance_km_warning"), 30)
            )
            if c.get("distance_km", 0) and float(c.get("distance_km", 0)) > max_distance_warning:
                warnings.append("W002: comparable eloigne")

        for a in case.get("ajustements", []):
            if "source_id" not in a:
                blocking.append("B002: ajustement sans source_id")
            sensitive_amount_min = float(
                _contract_value(("contracts", "rapport_conformite", "constraints", "ajustement_sensible_montant_min"), 25000)
            )
            if a.get("montant", 0) >= sensitive_amount_min and not a.get("validation_humaine", False):
                blocking.append("B005: ajustement sensible sans validation_humaine")

        if self.strict_mode and case.get("comparables") and not all("source_id" in c for c in case.get("comparables", [])):
            blocking.append("STRICT: sortie refusee, comparable sans source")

        subject_unit = case.get("surface", {}).get("unit")
        comp_units = {c.get("surface", {}).get("unit") for c in case.get("comparables", []) if isinstance(c.get("surface"), dict)}
        if subject_unit and comp_units and any(u and u != subject_unit for u in comp_units):
            blocking.append("B004: unite incoherente sujet/comparables")

        confidence_min_warning = float(
            _contract_value(("contracts", "rapport_conformite", "constraints", "confidence_min_warning"), 0.60)
        )
        if case.get("confidence", 1) < confidence_min_warning:
            warnings.append("W001: confiance faible")

        for h in case.get("hypotheses", []):
            source_ids = h.get("source_ids", [])
            if len(source_ids) < 2:
                warnings.append("W003: hypothese non corroboree par une deuxieme source")

        blocking = _unique(blocking)
        warnings = _unique(warnings)
        status = _status_from_contracts(has_blocking=bool(blocking), has_warnings=bool(warnings))
        return status, blocking, warnings

    def _artifact_payload(
        self,
        step: str,
        artifact: str,
        case: dict,
        status: str,
        blocking: list[str],
        warnings: list[str],
        valuation_values: dict[str, float] | None = None,
    ) -> dict:
        payload = {
            "dossier_id": case.get("dossier_id"),
            "step": step,
            "artifact": artifact,
        }

        if step == "data-facts" and artifact == "fiche_bien.json":
            payload.update(
                {
                    "date_reference": case.get("date_reference"),
                    "surface": case.get("surface"),
                    "type_bien": case.get("type_bien"),
                    "zone": case.get("zone"),
                    "adresse_anonymisee": case.get("adresse_anonymisee", "NON_FOURNIE"),
                    "confidence": case.get("confidence"),
                    "source_ids": collect_source_ids(case),
                }
            )

        if step == "data-facts" and artifact == "timeline_faits.json":
            payload["events"] = [
                {"type": "date_reference", "date": case.get("date_reference")},
                *case.get("timeline", []),
            ]

        if artifact == "source_index.json":
            payload["sources"] = [{"source_id": source_id} for source_id in collect_source_ids(case)]

        if step == "amu-analyst" and artifact == "umpp_conclusion.json":
            type_bien = str(case.get("type_bien", "inconnu")).lower()
            usage_map = {
                "residentiel_unifamilial": "residentiel_unifamilial",
                "unifamilial": "residentiel_unifamilial",
                "maison": "residentiel_unifamilial",
                "condo": "residentiel_condo",
                "duplex": "residentiel_multifamilial",
                "triplex": "residentiel_multifamilial",
                "commercial": "commercial",
                "industriel": "industriel",
                "terrain": "terrain_vacant",
                "terrain_vacant": "terrain_vacant",
            }
            usage_retenu = usage_map.get(type_bien, type_bien or "inconnu")
            payload.update({
                "umpp": {
                    "usage_retenu": usage_retenu,
                    "usage_actuel": type_bien,
                    "conformite_zonage": True,
                    "criteres": {
                        "physiquement_possible": True,
                        "legalement_permis": True,
                        "financierement_faisable": True,
                        "maximalement_productif": True,
                    },
                    "conclusion": (
                        f"L'usage actuel ({type_bien.replace('_', ' ')}) constitue le "
                        f"meilleur usage du bien."
                        if usage_retenu == type_bien else
                        f"L'usage optimal ({usage_retenu.replace('_', ' ')}) differe "
                        f"de l'usage actuel ({type_bien.replace('_', ' ')})."
                    ),
                    "umpp_differe_usage_actuel": usage_retenu != type_bien,
                },
                "confidence": 0.70,
            })

        if step == "amu-analyst" and artifact == "amu_analyse.md":
            type_bien = str(case.get("type_bien", "inconnu")).replace("_", " ")
            zone = str(case.get("zone", "non specifiee"))
            dossier_id = case.get("dossier_id", "—")
            payload["_raw_md"] = (
                f"# Analyse du Meilleur Usage (AMU)\n\n"
                f"**Dossier :** {dossier_id}  \n"
                f"**Type de bien :** {type_bien}  \n"
                f"**Zone :** {zone}\n\n"
                f"## Critere 1 — Legalement permis\n\n"
                f"L'usage de type {type_bien} est conforme au zonage {zone}. "
                f"Aucune restriction legale identifiee.\n\n"
                f"## Critere 2 — Physiquement possible\n\n"
                f"Les caracteristiques physiques du terrain et du batiment sont "
                f"compatibles avec l'usage de type {type_bien}.\n\n"
                f"## Critere 3 — Financierement faisable\n\n"
                f"Le marche supporte l'usage de type {type_bien} dans ce secteur.\n\n"
                f"## Critere 4 — Maximalement productif\n\n"
                f"L'usage actuel ({type_bien}) constitue l'usage le meilleur et le "
                f"plus profitable (UMPP) pour ce bien.\n\n"
                f"## Conclusion UMPP\n\n"
                f"L'usage actuel correspond a l'UMPP. L'evaluation procede selon "
                f"les methodes appropriees a ce type de bien.\n"
            )

        if step == "comps-market" and artifact == "comparables_proposes.json":
            payload["date_reference"] = case.get("date_reference")
            payload["comparables"] = [
                c.__dict__
                for c in search_comparables(
                    case.get("comparables", []),
                    max_items=5,
                    subject=case,
                    date_reference=case.get("date_reference"),
                )
            ]

        if step == "comps-market" and artifact == "justifications_comparables.json":
            payload["justifications"] = [
                {
                    "comparable_id": c.get("comparable_id"),
                    "source_id": c.get("source_id"),
                    "decision": "retenu" if c.get("source_id") else "rejete",
                    "raison": "source presente" if c.get("source_id") else "source manquante",
                }
                for c in case.get("comparables", [])
            ]

        if step == "valuation-draft" and artifact in {
            "calculs_approche_comparative.json",
            "calculs_approche_cout.json",
            "calculs_approche_revenu.json",
        }:
            approach_by_artifact = {
                "calculs_approche_comparative.json": "approche_comparative",
                "calculs_approche_cout.json": "approche_cout",
                "calculs_approche_revenu.json": "approche_revenu",
            }
            payload.update(calculate_valuation_trace(case, approach_by_artifact[artifact]))

        if step == "valuation-draft" and artifact == "hypotheses_explicites.json":
            payload["hypotheses"] = case.get("hypotheses", [])
            payload["confidence"] = case.get("confidence")

        if step == "valuation-draft" and artifact == "brouillon_valeur.md":
            comparative = calculate_valuation_trace(case, "approche_comparative")
            payload["summary"] = {
                "approche_comparative": comparative["value"],
                "comparables_count": comparative["input_count"],
                "status": status,
            }

        if step == "compliance-qa" and artifact == "rapport_non_conformites.json":
            payload.update({"blocking_failures": blocking, "warnings": warnings})

        if step == "compliance-qa" and artifact == "statut_sortie.json":
            payload.update(
                {
                    "status": status,
                    "blocking_failures": blocking,
                    "warnings": warnings,
                    "valuation_values": valuation_values or {},
                }
            )

        if step == "compliance-qa" and artifact == "recommandations_corrections.md":
            payload["recommendations"] = build_recommendations(blocking, warnings)

        if step == "redaction" and artifact == "brouillon_rapport.md":
            rapport_md = generate_brouillon_rapport(case, valuation_values or {}, status, blocking, warnings)
            payload["_raw_md"] = rapport_md
            payload["sections"] = {
                "dossier": case.get("dossier_id"),
                "statut": status,
                "resume": rapport_md[:300].replace("\n", " ").strip(),
            }

        if step == "redaction" and artifact == "annexe_sources.md":
            payload["sources"] = collect_source_ids(case)

        return payload

    def run_case(self, case_path: Path, out_dir: Path, *, case_subdir: bool = False) -> dict:
        return self.run_case_data(
            json.loads(case_path.read_text(encoding="utf-8")),
            out_dir,
            source_fixture=case_path.name,
            case_stem=case_path.stem,
            case_subdir=case_subdir,
        )

    def run_case_data(
        self,
        case: dict,
        out_dir: Path,
        *,
        source_fixture: str = "inline",
        case_stem: str | None = None,
        case_subdir: bool = False,
    ) -> dict:
        started_at = time.perf_counter()
        events: list[dict] = []
        dossier_id = str(case.get("dossier_id") or "unknown")
        case_key = safe_path_id(case_stem or dossier_id)
        case_dir = out_dir / case_key if case_subdir else out_dir
        audit_log_path = case_dir / f"{case_key}.audit.jsonl"

        status, blocking, warnings = self._compute_qa(case)
        case_dir.mkdir(parents=True, exist_ok=True)
        valuation_values: dict[str, float] = {}

        for warning in warnings:
            self._record_event(events, audit_log_path, {"event": "warning_detected", "dossier_id": dossier_id, "warning": warning})

        for step in self.steps:
            step_start_event = {"event": "step_start", "step": step.name, "dossier_id": dossier_id}
            if step.skills:
                step_start_event["skills_allowed"] = step.skills
            if step.agent_config:
                step_start_event["agent_config"] = step.agent_config
            self._record_event(events, audit_log_path, step_start_event)

            for artifact in step.writes:
                artifact_path = case_dir / f"{case_key}.{step.name}.{artifact}" if not case_subdir else case_dir / f"{step.name}.{artifact}"
                artifact_path.parent.mkdir(parents=True, exist_ok=True)

                payload = self._artifact_payload(step.name, artifact, case, status, blocking, warnings, valuation_values)
                payload = self._enrich_artifact_llm(step, artifact, payload, case)
                payload["source_fixture"] = source_fixture
                if step.skills:
                    payload["agent_skills_allowed"] = step.skills
                if step.agent_config:
                    payload["agent_config"] = step.agent_config
                if step.name == "valuation-draft" and artifact in {
                    "calculs_approche_comparative.json",
                    "calculs_approche_cout.json",
                    "calculs_approche_revenu.json",
                }:
                    approach_by_artifact = {
                        "calculs_approche_comparative.json": "approche_comparative",
                        "calculs_approche_cout.json": "approche_cout",
                        "calculs_approche_revenu.json": "approche_revenu",
                    }
                    value = payload.get("value")
                    if isinstance(value, (int, float)):
                        valuation_values[approach_by_artifact[artifact]] = float(value)

                required = REQUIRED_FIELDS_BY_ARTIFACT.get(artifact, REQUIRED_FIELDS_BY_ARTIFACT["default"])
                ok, missing = validate_schema(payload, required)
                if not ok:
                    schema_block = f"SCHEMA: champs manquants {missing}"
                    blocking = _unique([*blocking, schema_block])
                    status = _status_from_contracts(has_blocking=True, has_warnings=bool(warnings))
                    self._record_event(events, audit_log_path, {"event": "schema_invalid", "step": step.name, "artifact": artifact, "missing": missing})
                    if step.name == "compliance-qa":
                        payload.setdefault("blocking_failures", []).append(schema_block)

                contract_failures = validate_contract_rules(artifact, payload)
                if contract_failures:
                    blocking = _unique([*blocking, *contract_failures])
                    status = _status_from_contracts(has_blocking=True, has_warnings=bool(warnings))
                    self._record_event(
                        events,
                        audit_log_path,
                        {"event": "contract_invalid", "step": step.name, "artifact": artifact, "failures": contract_failures},
                    )
                    if step.name == "compliance-qa":
                        payload.setdefault("blocking_failures", []).extend(contract_failures)

                write_artifact_payload(artifact_path, payload)
                self._record_event(
                    events,
                    audit_log_path,
                    {"event": "artifact_written", "step": step.name, "artifact": artifact, "path": artifact_path.as_posix()},
                )

            self._record_event(events, audit_log_path, {"event": "step_done", "step": step.name, "dossier_id": dossier_id})

            review_status = _status_from_contracts(has_blocking=True, has_warnings=bool(warnings))
            if step.name == "compliance-qa" and status == review_status:
                blocking_event = {"event": "blocking_detected", "step": step.name, "dossier_id": dossier_id, "blocking_count": len(blocking)}
                self._record_event(events, audit_log_path, blocking_event)
                break

        wall_clock_seconds = 0.0 if os.environ.get("RUNTIME_DETERMINISTIC") else round(time.perf_counter() - started_at, 4)
        return {
            "dossier_id": dossier_id,
            "status": status,
            "blocking_failures": blocking,
            "warnings": warnings,
            "events": events,
            "audit_log": audit_log_path.as_posix(),
            "artifact_dir": case_dir.as_posix(),
            "skills_by_agent": {step.name: step.skills for step in self.steps},
            "metrics": {
                "wall_clock_seconds": wall_clock_seconds,
                "total_tokens": 0,
                "blocking_count": len(blocking),
                "warning_count": len(warnings),
            },
        }

    def _record_event(self, events: list[dict], audit_log_path: Path, event: dict) -> None:
        events.append(event)
        append_audit_log(audit_log_path, event)


def _parse_iso_date(value: object) -> date | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            out.append(value)
            seen.add(value)
    return out


def _parse_scalar(value: str) -> object:
    text = value.strip()
    if not text:
        return {}
    if text.startswith("[") and text.endswith("]"):
        try:
            return ast.literal_eval(text)
        except (SyntaxError, ValueError):
            return [v.strip() for v in text[1:-1].split(",") if v.strip()]
    if text in {"true", "false"}:
        return text == "true"
    try:
        return int(text) if "." not in text else float(text)
    except ValueError:
        return text


def _load_contract_tree() -> dict:
    global _CONTRACT_TREE_CACHE
    if _CONTRACT_TREE_CACHE is not None:
        return _CONTRACT_TREE_CACHE

    root: dict = {}
    stack: list[tuple[int, dict]] = [(-1, root)]
    for raw in CONTRACTS_DATA_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, value = line.strip().split(":", 1)
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        parsed_value = _parse_scalar(value)
        parent[key] = parsed_value
        if parsed_value == {}:
            node: dict = {}
            parent[key] = node
            stack.append((indent, node))
    _CONTRACT_TREE_CACHE = root
    return root


def _contract_value(path: tuple[str, ...], default: object) -> object:
    node: object = _load_contract_tree()
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node


def _status_from_contracts(*, has_blocking: bool, has_warnings: bool) -> str:
    mapping = _contract_value(("contracts", "rapport_conformite", "constraints", "status_decision"), {})
    if not isinstance(mapping, dict):
        mapping = {}
    if has_blocking:
        return str(mapping.get("blocking", "A_REVOIR"))
    if has_warnings:
        return str(mapping.get("warning", "BROUILLON"))
    return str(mapping.get("clean", "PRET_REVISION_FINALE"))


def safe_path_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip())
    return safe.strip("-") or "unknown"


def collect_source_ids(case: dict) -> list[str]:
    source_ids: list[str] = []
    for section in ("comparables", "ajustements"):
        for item in case.get(section, []):
            source_id = item.get("source_id")
            if source_id:
                source_ids.append(str(source_id))
    for h in case.get("hypotheses", []):
        for source_id in h.get("source_ids", []):
            if source_id:
                source_ids.append(str(source_id))
    return _unique(source_ids)


def build_recommendations(blocking: list[str], warnings: list[str]) -> list[str]:
    recommendations: list[str] = []
    for failure in blocking:
        if failure.startswith("B002"):
            recommendations.append("Ajouter ou corriger les source_id manquants avant toute conclusion.")
        elif failure.startswith("B003"):
            recommendations.append("Verifier les dates de ventes et la date de reference du dossier.")
        elif failure.startswith("B004"):
            recommendations.append("Normaliser les surfaces dans une seule unite ou documenter la conversion.")
        elif failure.startswith("B005"):
            recommendations.append("Obtenir une validation humaine explicite pour les ajustements sensibles.")
        else:
            recommendations.append(f"Corriger: {failure}")
    for warning in warnings:
        recommendations.append(f"Revoir warning: {warning}")
    return _unique(recommendations) or ["Aucune correction bloquante detectee."]


def validate_contract_rules(artifact: str, payload: dict) -> list[str]:
    failures: list[str] = []
    contract = CONTRACT_CHECKS_BY_ARTIFACT.get(artifact)
    if not contract:
        return failures

    required = contract.get("required_fields", [])
    ok, missing = validate_schema(payload, required)
    if not ok:
        failures.append(f"SCHEMA_CONTRACT: champs manquants {missing}")

    for rule in contract.get("rules", []):
        if rule == "CONF001":
            if not isinstance(payload.get("source_ids"), list) or len(payload.get("source_ids", [])) == 0:
                failures.append("CONF001: fiche_bien sans source_ids")
        elif rule == "CONF002":
            comparables = payload.get("comparables", [])
            if not isinstance(comparables, list) or len(comparables) == 0:
                failures.append("CONF002: aucun comparable propose")
        elif rule == "CONF003":
            for idx, comp in enumerate(payload.get("comparables", [])):
                if not comp.get("source_id"):
                    failures.append(f"CONF003: comparable[{idx}] sans source_id")
        elif rule == "CONF005":
            reference_date = _parse_iso_date(payload.get("date_reference"))
            max_delta_days = int(_contract_value(("contracts", "comparables_proposes", "constraints", "date_vente_max_delta_days"), 1095))
            for idx, comp in enumerate(payload.get("comparables", [])):
                sale_date = _parse_iso_date(comp.get("date_vente"))
                if reference_date and sale_date and abs((reference_date - sale_date).days) > max_delta_days:
                    failures.append(f"CONF005: comparable[{idx}] hors fenetre temporelle")
        elif rule == "CONF006":
            score_range = _contract_value(("contracts", "comparables_proposes", "constraints", "similarite_score_range"), [0, 1])
            min_score, max_score = float(score_range[0]), float(score_range[1])
            for idx, comp in enumerate(payload.get("comparables", [])):
                score = comp.get("score")
                if score is None:
                    continue
                try:
                    score_value = float(score)
                except (TypeError, ValueError):
                    failures.append(f"CONF006: comparable[{idx}] score invalide")
                    continue
                if score_value < min_score or score_value > max_score:
                    failures.append(f"CONF006: comparable[{idx}] score hors bornes [{min_score},{max_score}]")
        elif rule == "CONF004":
            statuses = _contract_value(
                ("contracts", "rapport_conformite", "constraints", "status"),
                ["BROUILLON", "A_REVOIR", "PRET_REVISION_FINALE"],
            )
            if payload.get("status") not in set(statuses):
                failures.append("CONF004: statut_sortie invalide")
        elif rule == "CONF007":
            values = payload.get("valuation_values", {})
            if not isinstance(values, dict):
                continue
            comparative = values.get("approche_comparative")
            cout = values.get("approche_cout")
            revenu = values.get("approche_revenu")
            if all(isinstance(v, (int, float)) for v in [comparative, cout, revenu]):
                min_val = min(comparative, cout, revenu)
                max_val = max(comparative, cout, revenu)
                if min_val > 0:
                    ratio = (max_val - min_val) / min_val
                    max_ratio = float(
                        _contract_value(
                            ("contracts", "rapport_conformite", "constraints", "valuation_inter_approach_max_delta_ratio"),
                            0.35,
                        )
                    )
                    if ratio > max_ratio:
                        failures.append("CONF007: incoherence inter-approches de valuation")

    return failures


_RAPPORT_MAX_TOKENS = 2000

_RAPPORT_SYSTEM_PROMPT = (
    "Tu es un assistant spécialisé en rédaction de rapports d'évaluation immobilière au Canada.\n"
    "Génère un brouillon de rapport structuré et professionnel en français canadien.\n\n"
    "RÈGLES ABSOLUES :\n"
    "- N'invente aucune donnée non fournie dans le prompt\n"
    "- Ne prétends jamais que le rapport est certifié ou signé\n"
    "- Indique clairement le statut BROUILLON NON CERTIFIÉ\n"
    "- Utilise uniquement les valeurs et comparables fournis\n"
    "- Format Markdown structuré avec sections numérotées\n\n"
    "STRUCTURE REQUISE :\n"
    "1. Identification du bien\n"
    "2. Conclusion de valeur marchande proposée\n"
    "3. Réconciliation des approches (tableau)\n"
    "4. Soutien du marché — comparables retenus\n"
    "5. Hypothèses et conditions limitatives\n"
    "6. Mention légale (brouillon IA, validation évaluateur agréé requise)\n"
)


def _fmt_cad(value: float) -> str:
    """Formate un montant en dollars canadiens."""
    return f"{round(value):,}".replace(",", "\u00a0") + " $"


def _build_rapport_prompt(case: dict, valuation_values: dict, status: str, blocking: list, warnings: list) -> str:
    surface = case.get("surface", {})
    surface_str = f"{surface.get('value', '—')} {surface.get('unit', '')}" if isinstance(surface, dict) else str(surface)
    comp_lines = []
    for i, c in enumerate(case.get("comparables", [])[:5], 1):
        price = c.get("prix_vente") or c.get("sale_price")
        price_str = _fmt_cad(float(price)) if price else "—"
        comp_lines.append(
            f"  Comparable {i}: prix={price_str}, date={c.get('date_vente', '—')}, "
            f"source={c.get('source_id', '—')}, score={c.get('score', '—')}"
        )
    approach_lines = [
        f"  - Approche comparative : {_fmt_cad(valuation_values['approche_comparative'])}"
        if "approche_comparative" in valuation_values else "",
        f"  - Approche par le coût : {_fmt_cad(valuation_values['approche_cout'])}"
        if "approche_cout" in valuation_values else "",
        f"  - Approche par le revenu : {_fmt_cad(valuation_values['approche_revenu'])}"
        if "approche_revenu" in valuation_values else "",
    ]
    lines = [
        f"DOSSIER : {case.get('dossier_id', '—')}",
        f"DATE DE RÉFÉRENCE : {case.get('date_reference', '—')}",
        f"TYPE DE BIEN : {case.get('type_bien', '—')}",
        f"ZONE : {case.get('zone', '—')}",
        f"SURFACE : {surface_str}",
        f"STATUT CONFORMITÉ : {status}",
        "",
        "APPROCHES DE VALEUR :",
        *[l for l in approach_lines if l],
        "",
        f"COMPARABLES RETENUS ({len(case.get('comparables', []))}) :",
        *comp_lines,
    ]
    if blocking:
        lines += ["", f"BLOCAGES ({len(blocking)}) : " + "; ".join(blocking[:3])]
    if warnings:
        lines += [f"AVERTISSEMENTS : " + "; ".join(warnings[:3])]
    return "\n".join(lines)


def _generate_rapport_llm(prompt: str) -> str | None:
    """Appelle OpenAI pour générer le rapport. Retourne None si indisponible."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return None
    try:
        import openai as _openai  # type: ignore
        client = _openai.OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            max_tokens=_RAPPORT_MAX_TOKENS,
            messages=[
                {"role": "system", "content": _RAPPORT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content or None
    except Exception:
        return None


def _generate_rapport_deterministic(case: dict, valuation_values: dict, status: str, blocking: list, warnings: list) -> str:
    """Template déterministe avec vraies données — utilisé si aucun LLM disponible."""
    dossier_id = case.get("dossier_id", "—")
    date_ref = case.get("date_reference", "—")
    type_bien = case.get("type_bien", "—").replace("_", " ").capitalize()
    zone = case.get("zone", "—")
    surface = case.get("surface", {})
    surface_str = f"{surface.get('value', '—')} {surface.get('unit', '')}" if isinstance(surface, dict) else str(surface)
    today = date.today().isoformat()

    # Valeur principale = approche comparative si disponible
    val_principale = valuation_values.get("approche_comparative") or next(iter(valuation_values.values()), None)
    val_str = _fmt_cad(val_principale) if val_principale else "—"

    comparables = case.get("comparables", [])[:5]
    comp_rows = ""
    for i, c in enumerate(comparables, 1):
        price = c.get("prix_vente") or c.get("sale_price")
        price_str = _fmt_cad(float(price)) if price else "—"
        score = c.get("score", "—")
        score_str = f"{float(score):.2f}" if isinstance(score, float) else str(score)
        comp_rows += f"| {i} | {c.get('source_id', '—')} | {price_str} | {c.get('date_vente', '—')} | {score_str} |\n"

    approach_rows = ""
    labels = {
        "approche_comparative": "Approche comparative",
        "approche_cout": "Approche par le coût",
        "approche_revenu": "Approche par le revenu",
    }
    for key, label in labels.items():
        if key in valuation_values:
            approach_rows += f"| {label} | {_fmt_cad(valuation_values[key])} |\n"

    blocking_section = ""
    if blocking:
        items = "\n".join(f"- {b}" for b in blocking)
        blocking_section = f"\n**Blocages ({len(blocking)}) :**\n{items}\n"

    warnings_section = ""
    if warnings:
        items = "\n".join(f"- {w}" for w in warnings)
        warnings_section = f"\n**Avertissements ({len(warnings)}) :**\n{items}\n"

    return f"""\
# BROUILLON DE RAPPORT D'ÉVALUATION

> **BROUILLON NON CERTIFIÉ** — Produit par assistant IA le {today}.
> Validation et signature d'un évaluateur agréé requises avant toute diffusion.

---

## 1. Identification du bien

| Champ | Valeur |
|-------|--------|
| Dossier | {dossier_id} |
| Type de bien | {type_bien} |
| Zone | {zone} |
| Surface | {surface_str} |
| Date de référence | {date_ref} |
| Statut conformité | {status} |

---

## 2. Conclusion de valeur marchande proposée

**Valeur estimée : {val_str}**

Cette valeur est établie principalement par l'approche comparative, corroborée par les approches
par le coût et par le revenu. Elle n'est pas certifiée et ne constitue pas une opinion formelle
d'un évaluateur agréé.

---

## 3. Réconciliation des approches

| Méthode | Valeur indiquée |
|---------|-----------------|
{approach_rows}
---

## 4. Soutien du marché — comparables retenus

{len(comparables)} comparable(s) retenu(s) pour l'analyse comparative :

| # | Référence source | Prix de vente | Date de vente | Score similarité |
|---|------------------|---------------|---------------|-----------------|
{comp_rows}
---

## 5. Hypothèses et conditions limitatives

- L'analyse est basée exclusivement sur les données et sources référencées dans ce dossier.
- Aucune inspection physique du bien n'a été effectuée par le système IA.
- Les valeurs des approches par le coût et par le revenu sont des proxys V0 et ne remplacent
  pas un calcul de coût ou de capitalisation complet par un évaluateur agréé.
- Toute donnée manquante ou incomplète est signalée dans la section conformité ci-dessous.
{blocking_section}{warnings_section}
---

## 6. Mention légale

Ce document est un brouillon produit par un assistant IA à titre d'aide à la rédaction.
Il **ne constitue pas** un rapport d'évaluation certifié au sens des normes professionnelles
applicables et ne peut être utilisé à des fins de transaction, de financement ou de litige
sans validation et signature d'un évaluateur agréé autorisé.
"""


def generate_brouillon_rapport(case: dict, valuation_values: dict, status: str, blocking: list, warnings: list) -> str:
    """Génère le brouillon de rapport : LLM si disponible, sinon template déterministe."""
    prompt = _build_rapport_prompt(case, valuation_values, status, blocking, warnings)
    llm_text = _generate_rapport_llm(prompt)
    if llm_text:
        disclaimer = (
            "> **BROUILLON NON CERTIFIÉ** — Produit par assistant IA.\n"
            "> Validation et signature d'un évaluateur agréé requises avant toute diffusion.\n\n---\n\n"
        )
        return disclaimer + llm_text
    return _generate_rapport_deterministic(case, valuation_values, status, blocking, warnings)


def write_artifact_payload(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".md":
        raw = payload.get("_raw_md")
        path.write_text(raw if isinstance(raw, str) else render_markdown_payload(payload), encoding="utf-8")
        return
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def render_markdown_payload(payload: dict) -> str:
    title = payload.get("artifact", "artifact")
    lines = [f"# {title}", "", f"- Dossier: {payload.get('dossier_id')}", f"- Step: {payload.get('step')}", ""]
    for key, value in payload.items():
        if key in {"dossier_id", "step", "artifact", "source_fixture"}:
            continue
        lines.append(f"## {key}")
        if isinstance(value, (dict, list)):
            lines.append("```json")
            lines.append(json.dumps(value, ensure_ascii=False, indent=2))
            lines.append("```")
        else:
            lines.append(str(value))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
