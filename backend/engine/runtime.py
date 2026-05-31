from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
import json
import os
import re
import time
import ast
import uuid

from engine.audit import append_audit_log
from engine.amu import evaluate_amu
from engine.compliance import run_compliance, check_conflit_interets
from engine.report_check import check_rapport_elements, build_rapport_check_section
from engine.llm_routing import get_llm_model, estimate_llm_cost
from engine.schema_contracts import validate_artifact_schema
from engine.skills import DEFAULT_SKILLS_BY_AGENT, load_agent_config_skills, load_agent_system_prompt, load_skill_knowledge
from engine.tools import search_comparables, validate_schema
from engine.valuation import calculate_valuation_trace, approaches_for_case


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
    "calculs_approche_cout.json": ["dossier_id", "step", "artifact", "source_fixture", "approach", "value", "input_count"],
    "calculs_approche_revenu.json": ["dossier_id", "step", "artifact", "source_fixture", "approach", "value", "input_count"],
    "umpp_conclusion.json": ["dossier_id", "step", "artifact", "source_fixture", "umpp"],
    "conflit_interets.json": ["dossier_id", "step", "artifact", "source_fixture", "conflit_detecte"],
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

class PipelineConflitError(ValueError):
    """Raised when a conflict of interest is detected and the pipeline must stop."""
    pass


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
    "conflit_interets.json": "analyse_conflit",
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
    RuntimeStep("mandat-intake", ["dossier_input"], ["lettre_mandat.md", "conflit_interets.json"], _skills_for_agent("mandat-intake"), "AGENTCONFIG-MANDAT-INTAKE-V0.yaml"),
    RuntimeStep("data-facts", ["dossier_input", "documents_sources"], ["fiche_bien.json", "timeline_faits.json", "source_index.json"], _skills_for_agent("data-facts"), "AGENTCONFIG-DATA-FACTS-V0.yaml"),
    RuntimeStep("amu-analyst", ["fiche_bien.json", "source_index.json"], ["umpp_conclusion.json", "amu_analyse.md"], _skills_for_agent("amu-analyst"), "AGENTCONFIG-AMU-ANALYST-V0.yaml"),
    RuntimeStep("comps-market", ["fiche_bien.json", "umpp_conclusion.json", "source_index.json", "market_data_sources"], ["comparables_proposes.json", "justifications_comparables.json", "source_index.json"], _skills_for_agent("comps-market"), "AGENTCONFIG-COMPS-MARKET-V0.yaml"),
    RuntimeStep("valuation-draft", ["comparables_proposes.json", "couts_reference", "revenus_depenses", "source_index.json"], ["calculs_approche_comparative.json", "calculs_approche_cout.json", "calculs_approche_revenu.json", "hypotheses_explicites.json", "brouillon_valeur.md"], _skills_for_agent("valuation-draft"), "AGENTCONFIG-VALUATION-DRAFT-V0.yaml"),
    RuntimeStep("compliance-qa", ["calculs_approche_comparative.json", "calculs_approche_cout.json", "calculs_approche_revenu.json", "hypotheses_explicites.json", "source_index.json"], ["rapport_non_conformites.json", "statut_sortie.json", "recommandations_corrections.md"], _skills_for_agent("compliance-qa"), "AGENTCONFIG-COMPLIANCE-QA-V0.yaml"),
    RuntimeStep("redaction", ["statut_sortie.json", "recommandations_corrections.md", "amu_analyse.md", "lettre_mandat.md", "source_index.json"], ["brouillon_rapport.md", "annexe_sources.md"], _skills_for_agent("redaction"), "AGENTCONFIG-REDACTION-V0.yaml"),
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
        ingested_section = ""
        if case.get("ingested_docs"):
            doc_parts = []
            for d in case["ingested_docs"]:
                fname = str(d.get("filename", "document"))
                text = str(d.get("extracted_text", "")).strip()
                if text:
                    doc_parts.append(f"[{fname}]\n{text[:600]}")
            if doc_parts:
                ingested_section = "\n\n## Documents uploadés\n\n" + "\n\n".join(doc_parts)
        return base + (
            f"DONNÉES DE LA FICHE BIEN :\n"
            f"Surface : {surface_str}\n"
            f"Confiance : {payload.get('confidence', '—')}\n"
            f"Sources : {payload.get('source_ids', [])}"
            f"{ingested_section}\n\n"
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

    if artifact == "lettre_mandat.md":
        mandat_type = str(case.get("mandat_type", "residentiel_standard"))
        format_rapport = str(case.get("format_rapport", "abrege"))
        methodes = case.get("methodes_requises", [])
        return base + (
            f"MANDAT :\n"
            f"Type de bien : {type_bien} | Mandat : {mandat_type} | Format rapport : {format_rapport}\n"
            f"Methodes requises : {methodes}\n\n"
            "Redige la lettre de mandat professionnelle en Markdown conforme au Code de deontologie OEAQ. "
            "Structure obligatoire : identification du bien, identification du commanditaire (laisser [COMMANDITAIRE] si absent), "
            "type d'acte professionnel, type de rapport, fin d'evaluation, date de reference, "
            "etendue de l'inspection, hypotheses et limitations prealables, honoraires ([A CONFIRMER]), "
            "date de livraison prevue ([A CONFIRMER]), lignes de signature. "
            "Ton professionnel, juridiction Quebec, references deontologiques OEAQ."
        )

    if artifact == "conflit_interets.json":
        commanditaire = case.get("commanditaire", {})
        nom_cmd = str(commanditaire.get("nom", "") or "[COMMANDITAIRE]")
        org_cmd = str(commanditaire.get("organisation", ""))
        fin_eval = str(commanditaire.get("fin_evaluation", "non specifie"))
        return base + (
            f"VÉRIFICATION CONFLIT D'INTÉRÊTS :\n"
            f"Commanditaire : {nom_cmd} | Organisation : {org_cmd} | Fin : {fin_eval}\n"
            f"Type de bien : {type_bien} | Zone : {case.get('zone', '—')}\n\n"
            "Tu es un expert en déontologie de l'évaluation immobilière OEAQ. "
            "Vérifie s'il existe un conflit d'intérêts RÉEL entre l'évaluateur et le commanditaire. "
            "Critères OEAQ : lien financier/familial/professionnel avéré; mandat conditionnel à une valeur cible; intérêt direct dans la propriété. "
            "RÈGLE STRICTE DE FORMAT : "
            "— Si conflit réel identifié : commence EXACTEMENT par 'CONFLIT_DETECTE: <motif>' (1 ligne), puis développe. "
            "— Si PAS de conflit (cas normal, absence d'info, commanditaire externe) : commence par 'Aucun conflit détecté.' puis explique brièvement. "
            "Ne commence JAMAIS par 'CONFLIT_DETECTE:' si tu n'as pas identifié un conflit réel et concret. "
            "L'absence de déclaration de liens n'est pas un conflit — c'est la situation par défaut."
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

        # Injecter analysis.md des skills de l'étape dans le system prompt
        if step.skills:
            skill_blocks: list[str] = []
            budget = 3000
            used = 0
            for skill_name in step.skills:
                if used >= budget:
                    break
                remaining = budget - used
                block = load_skill_knowledge(skill_name, max_chars=min(1500, remaining))
                if block:
                    skill_blocks.append(f"### {skill_name}\n{block}")
                    used += len(block)
            if skill_blocks:
                system_prompt += (
                    "\n\n---\nCONNAISSANCE MÉTHODOLOGIQUE (analysis.md) :\n"
                    + "\n\n".join(skill_blocks)
                )

        # Injecter RAG normatif pour les agents de recherche et rédaction
        _rag_steps = {"data-facts", "amu-analyst", "comps-market", "valuation-draft",
                      "compliance-qa", "redaction"}
        if step.name in _rag_steps:
            try:
                from engine.knowledge_rag import retrieve_context  # type: ignore
                _rag_query = f"{step.name} {artifact} {case.get('type_bien', '')} {case.get('zone', '')}"
                _rag_context = retrieve_context(_rag_query, top_k=3)
                if _rag_context:
                    system_prompt += (
                        "\n\n---\nSOURCES NORMATIVES PERTINENTES (RAG) :\n"
                        + _rag_context
                    )
            except Exception:
                pass  # RAG is optional — never block pipeline

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
                if artifact == "conflit_interets.json":
                    _first_line = next((l.strip() for l in result.splitlines() if l.strip()), "")
                    if _first_line.startswith("CONFLIT_DETECTE:"):
                        motif = _first_line.replace("CONFLIT_DETECTE:", "").strip()
                        # Guard: LLM sometimes uses CONFLIT_DETECTE as a header even for "no conflict" — ignore false positives
                        _motif_lower = motif.lower()
                        _false_positive = any(kw in _motif_lower for kw in ("aucun", "pas de", "absence", "no conflict", "aucune", "sans conflit", "non détecté", "non detecte"))
                        if not _false_positive:
                            return {**payload, target_field: result, "conflit_detecte": True, "conflit_motif": motif}
                return {**payload, target_field: result}
        except Exception:
            pass  # LLM enrichment is optional — never block pipeline

        return payload

    def _compute_qa(self, case: dict) -> tuple[str, list[str], list[str]]:
        # Délègue à engine/compliance.py (B001-B007 + W001-W003 déterministes)
        sensitive_amount_min = float(
            _contract_value(("contracts", "rapport_conformite", "constraints", "ajustement_sensible_montant_min"), 25000)
        )
        max_distance_warning = float(
            _contract_value(("contracts", "rapport_conformite", "constraints", "max_comparable_distance_km_warning"), 30)
        )
        confidence_min = float(
            _contract_value(("contracts", "rapport_conformite", "constraints", "confidence_min_warning"), 0.60)
        )
        report = run_compliance(
            case,
            sensitive_amount_min=sensitive_amount_min,
            max_distance_warning_km=max_distance_warning,
            confidence_min=confidence_min,
        )

        blocking = report.blocking_strings()
        warnings = list(report.warnings)

        if self.strict_mode and case.get("comparables") and not all("source_id" in c for c in case.get("comparables", [])):
            blocking.append("STRICT: sortie refusee, comparable sans source")

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
            fb: dict = {
                "date_reference": case.get("date_reference"),
                "surface": case.get("surface"),
                "type_bien": case.get("type_bien"),
                "zone": case.get("zone"),
                "adresse_anonymisee": case.get("adresse_anonymisee", "NON_FOURNIE"),
                "confidence": case.get("confidence"),
                "source_ids": collect_source_ids(case),
            }
            # Inject enrichment data when available
            if case.get("annee_construction"):
                fb["annee_construction"] = case["annee_construction"]
            if case.get("source_diagnostics"):
                fb["source_diagnostics"] = case.get("source_diagnostics")
            if case.get("source_coverage"):
                fb["source_coverage"] = case.get("source_coverage")
            if case.get("role_municipal"):
                role = case["role_municipal"]
                fb["role_municipal"] = {
                    k: v for k, v in role.items()
                    if k not in ("source",) and v is not None
                }
            if case.get("zonage_urbanisme"):
                z = case["zonage_urbanisme"]
                fb["zonage_urbanisme"] = {
                    k: v for k, v in z.items()
                    if k not in ("source",) and v is not None
                }
            if case.get("zone_agricole"):
                za = case["zone_agricole"]
                fb["zone_agricole"] = {
                    k: v for k, v in za.items()
                    if k not in ("source",) and v is not None
                }
            pat = case.get("patrimoine_culturel")
            if pat is not None:  # include even empty dict (means "checked, not listed")
                fb["patrimoine_culturel"] = {
                    k: v for k, v in pat.items()
                    if k not in ("source",) and v is not None
                }
            inond = case.get("zone_inondable")
            if inond is not None:
                fb["zone_inondable"] = {
                    k: v for k, v in inond.items()
                    if k not in ("source",) and v is not None
                }
            ipc = case.get("ipc_logement")
            if ipc:
                fb["ipc_logement"] = {
                    k: v for k, v in ipc.items()
                    if k not in ("source",) and v is not None
                }
            travail = case.get("marche_travail")
            if travail:
                fb["marche_travail"] = {
                    k: v for k, v in travail.items()
                    if k not in ("source",) and v is not None
                }
            pop_cma = case.get("population_cma")
            if pop_cma:
                fb["population_cma"] = {
                    k: v for k, v in pop_cma.items()
                    if k not in ("source",) and v is not None
                }
            taux_boc = case.get("taux_bancaires")
            if taux_boc:
                fb["taux_bancaires"] = {
                    k: v for k, v in taux_boc.items()
                    if k not in ("source",) and v is not None
                }
            dette = case.get("dette_revenu")
            if dette:
                fb["dette_revenu"] = {
                    k: v for k, v in dette.items()
                    if k not in ("source",) and v is not None
                }
            absorb = case.get("unites_absorbees")
            if absorb:
                fb["unites_absorbees"] = {
                    k: v for k, v in absorb.items()
                    if k not in ("source",) and v is not None
                }
            vacance = case.get("taux_inoccupation")
            if vacance:
                fb["taux_inoccupation"] = {
                    k: v for k, v in vacance.items()
                    if k not in ("source",) and v is not None
                }
            nhpi = case.get("indice_prix_logement")
            if nhpi:
                fb["indice_prix_logement"] = {
                    k: v for k, v in nhpi.items()
                    if k not in ("source",) and v is not None
                }
            census = case.get("donnees_sociodemographiques")
            if census:
                fb["donnees_sociodemographiques"] = {
                    k: v for k, v in census.items()
                    if k not in ("source", "_ts") and v is not None
                }
            chantier = case.get("mises_en_chantier")
            if chantier:
                fb["mises_en_chantier"] = {
                    k: v for k, v in chantier.items()
                    if k not in ("source",) and v is not None
                }
            permis = case.get("permis_construction")
            if permis:
                fb["permis_construction"] = {
                    k: v for k, v in permis.items()
                    if k not in ("source",) and v is not None
                }
            prox = case.get("proximite_services")
            if prox:
                fb["proximite_services"] = {
                    k: v for k, v in prox.items()
                    if k not in ("source",) and v is not None
                }
            routes = case.get("proximite_routes")
            if routes:
                fb["proximite_routes"] = {
                    k: v for k, v in routes.items()
                    if k not in ("source",) and v is not None
                }
            postsec = case.get("enseignement_postsecondaire")
            if postsec:
                fb["enseignement_postsecondaire"] = {
                    k: v for k, v in postsec.items()
                    if k not in ("source",) and v is not None
                }
            nuisances = case.get("nuisances_environnementales")
            if nuisances:
                fb["nuisances_environnementales"] = {
                    k: v for k, v in nuisances.items()
                    if k not in ("source",) and v is not None
                }
            climat = case.get("donnees_climatiques")
            if climat:
                fb["donnees_climatiques"] = {
                    k: v for k, v in climat.items()
                    if k not in ("source",) and v is not None
                }
            abord = case.get("indice_abordabilite")
            if abord:
                fb["indice_abordabilite"] = {
                    k: v for k, v in abord.items()
                    if k not in ("source",) and v is not None
                }
            score_m = case.get("score_marche")
            if score_m:
                fb["score_marche"] = {
                    k: v for k, v in score_m.items()
                    if k not in ("source",) and v is not None
                }
            rend = case.get("rendement_locatif")
            if rend:
                fb["rendement_locatif"] = {
                    k: v for k, v in rend.items()
                    if k not in ("source",) and v is not None
                }
            invest = case.get("score_investissement")
            if invest:
                fb["score_investissement"] = {
                    k: v for k, v in invest.items()
                    if k not in ("source",) and v is not None
                }
            taxes = case.get("taxes_municipales")
            if taxes:
                fb["taxes_municipales"] = {
                    k: v for k, v in taxes.items()
                    if k not in ("source",) and v is not None
                }
            couts = case.get("couts_possession")
            if couts:
                fb["couts_possession"] = {
                    k: v for k, v in couts.items()
                    if k not in ("source",) and v is not None
                }
            plr = case.get("ratio_prix_loyer")
            if plr:
                fb["ratio_prix_loyer"] = {
                    k: v for k, v in plr.items()
                    if k not in ("source",) and v is not None
                }
            vet = case.get("vetuste_batiment")
            if vet:
                fb["vetuste_batiment"] = {
                    k: v for k, v in vet.items()
                    if k not in ("source",) and v is not None
                }
            qdv = case.get("indice_qualite_vie")
            if qdv:
                fb["indice_qualite_vie"] = {
                    k: v for k, v in qdv.items()
                    if k not in ("source",) and v is not None
                }
            risque = case.get("score_risque")
            if risque:
                fb["score_risque"] = {
                    k: v for k, v in risque.items()
                    if k not in ("source",) and v is not None
                }
            val_ind = case.get("valeur_indicative")
            if val_ind:
                fb["valeur_indicative"] = {
                    k: v for k, v in val_ind.items()
                    if k not in ("source",) and v is not None
                }
            sg = case.get("score_global")
            if sg:
                fb["score_global"] = {
                    k: v for k, v in sg.items()
                    if k not in ("source",) and v is not None
                }
            cout_ren = case.get("cout_renovation")
            if cout_ren:
                fb["cout_renovation"] = {
                    k: v for k, v in cout_ren.items()
                    if k not in ("source",) and v is not None
                }
            proj_val = case.get("projection_valeur")
            if proj_val:
                fb["projection_valeur"] = {
                    k: v for k, v in proj_val.items()
                    if k not in ("source", "source_taux") and v is not None
                }
            alrt = case.get("alertes")
            if alrt:
                fb["alertes"] = {
                    k: v for k, v in alrt.items()
                    if k not in ("source",) and v is not None
                }
            crime = case.get("crime_stats")
            if crime:
                fb["crime_stats"] = {
                    k: v for k, v in crime.items()
                    if k not in ("source",) and v is not None
                }
            neuf = case.get("marche_neuf")
            if neuf:
                fb["marche_neuf"] = {
                    k: v for k, v in neuf.items()
                    if k not in ("source",) and v is not None
                }
            dist_cbd = case.get("distance_cbd")
            if dist_cbd:
                fb["distance_cbd"] = {
                    k: v for k, v in dist_cbd.items()
                    if k not in ("source",) and v is not None
                }
            payload.update(fb)

        if step == "data-facts" and artifact == "timeline_faits.json":
            payload["events"] = [
                {"type": "date_reference", "date": case.get("date_reference")},
                *case.get("timeline", []),
            ]

        if artifact == "source_index.json":
            payload["sources"] = [{"source_id": source_id} for source_id in collect_source_ids(case)]

        if step == "amu-analyst" and artifact == "umpp_conclusion.json":
            payload.update(evaluate_amu(case))

        if step == "amu-analyst" and artifact == "amu_analyse.md":
            type_bien = str(case.get("type_bien", "inconnu")).replace("_", " ")
            zone = str(case.get("zone", "non specifiee"))
            dossier_id = case.get("dossier_id", "—")
            # Build zonage section from enrichment (if available)
            zu = case.get("zonage_urbanisme") or {}
            if zu:
                zone_code = zu.get("ZONE") or zu.get("CODE_ZONE") or zu.get("zone") or zone
                zone_desc = zu.get("DESCRIPTION") or zu.get("CATEGORIE_ZONE") or zu.get("NOM_ZONE") or ""
                zone_usage = zu.get("USAGE_PRINCIPAL") or zu.get("usage") or ""
                zonage_section = (
                    f"## Données de zonage (open data)\n\n"
                    f"Code de zone : **{zone_code}**  \n"
                    + (f"Description : {zone_desc}  \n" if zone_desc else "")
                    + (f"Usage principal autorisé : {zone_usage}  \n" if zone_usage else "")
                    + "\n"
                )
            else:
                zone_code = zone
                zonage_section = ""
            # Build patrimoine culturel section if data available
            pat = case.get("patrimoine_culturel")
            if pat:  # non-empty dict = listed
                pat_nom = pat.get("NOM") or pat.get("NM_BIEN") or "—"
                pat_statut = pat.get("STATUT") or pat.get("NM_STATUT") or "désigné"
                pat_categorie = pat.get("CATEGORIE") or pat.get("NM_CATEGORIE") or ""
                patrimoine_section = (
                    f"## Patrimoine culturel\n\n"
                    f"**ATTENTION : bien répertorié au patrimoine culturel.**  \n"
                    f"Nom : {pat_nom}  \n"
                    f"Statut : {pat_statut}  \n"
                    + (f"Catégorie : {pat_categorie}  \n" if pat_categorie else "")
                    + "\nNote : modifications soumises à autorisation du Ministre de la Culture. "
                    "Impact sur la valeur à analyser selon les restrictions applicables.\n\n"
                )
            else:
                patrimoine_section = ""
            # Build zone inondable section if data available
            inond = case.get("zone_inondable")
            if inond:  # non-empty = en zone inondable
                rec_label = inond.get("recurrence_label") or inond.get("recurrence") or "—"
                inond_section = (
                    f"## Zone inondable (MELCC)\n\n"
                    f"**ATTENTION : bien situé en zone inondable.**  \n"
                    f"Récurrence : **{rec_label}**  \n"
                    "\nNote : impact sur la valeur, le financement hypothécaire et l'assurabilité. "
                    "Analyser selon les nouvelles normes 2024 (cartographie MELCC).\n\n"
                )
            else:
                inond_section = ""
            # Build CPTAQ section if relevant
            za = case.get("zone_agricole") or {}
            if za:
                en_zone = za.get("en_zone_agricole", False)
                mrc = za.get("NM_MRC") or za.get("nm_mrc") or ""
                cptaq_section = (
                    f"## Zone agricole (CPTAQ)\n\n"
                    f"Statut : **{'EN ZONE AGRICOLE PROTÉGÉE' if en_zone else 'hors zone agricole'}**  \n"
                    + (f"MRC : {mrc}  \n" if mrc else "")
                    + ("\nNote : les usages non agricoles sont soumis à autorisation CPTAQ.\n\n"
                       if en_zone else "\n")
                )
            else:
                cptaq_section = ""
            # Build population + labour market section
            pop_cma = case.get("population_cma") or {}
            travail = case.get("marche_travail") or {}
            if pop_cma or travail:
                ville_demo = (pop_cma or travail).get("ville", zone)
                pop_val = pop_cma.get("population")
                pop_var = pop_cma.get("variation_annuelle_pct")
                pop_annee = pop_cma.get("annee", "")
                tx_chom = travail.get("taux_chomage_pct")
                tx_empl = travail.get("taux_emploi_pct")
                tx_part = travail.get("taux_participation_pct")
                periode_trav = travail.get("periode", "")
                pop_section = (
                    f"## Démographie et marché du travail — CMA {ville_demo}\n\n"
                    + (
                        f"**Population ({pop_annee})**  \n"
                        + (f"Population : **{pop_val:,.0f}**  \n" if pop_val else "")
                        + (f"Croissance annuelle : **{pop_var:+.2f} %**  \n" if pop_var is not None else "")
                        + "\n"
                        if pop_cma else ""
                    )
                    + (
                        f"**Marché du travail ({periode_trav})**  \n"
                        + (f"Taux de chômage : **{tx_chom:.1f} %**  \n" if tx_chom is not None else "")
                        + (f"Taux d'emploi : **{tx_empl:.1f} %**  \n" if tx_empl is not None else "")
                        + (f"Taux de participation : **{tx_part:.1f} %**  \n" if tx_part is not None else "")
                        + "\n"
                        if travail else ""
                    )
                )
            else:
                pop_section = ""
            # Build Bank of Canada rates section
            taux_boc = case.get("taux_bancaires") or {}
            if taux_boc:
                td = taux_boc.get("taux_directeur_pct")
                tp = taux_boc.get("taux_preferentiel_pct")
                th5 = taux_boc.get("taux_hypo_5ans_conv_pct")
                th1 = taux_boc.get("taux_hypo_1an_pct")
                date_boc = taux_boc.get("date", "")
                financement_section = (
                    f"## Contexte financier (Banque du Canada)\n\n"
                    + (f"Date : {date_boc}  \n" if date_boc else "")
                    + (f"Taux directeur : **{td:.2f} %**  \n" if td is not None else "")
                    + (f"Taux préférentiel : **{tp:.2f} %**  \n" if tp is not None else "")
                    + (f"Taux hypothécaire 5 ans (conventionnel) : **{th5:.2f} %**  \n" if th5 is not None else "")
                    + (f"Taux hypothécaire 1 an (conventionnel) : **{th1:.2f} %**  \n" if th1 is not None else "")
                    + "\n"
                )
            else:
                financement_section = ""
            # Build household debt-to-income section
            dette = case.get("dette_revenu") or {}
            if dette:
                dette_ratio = dette.get("ratio_dette_revenu_pct")
                dette_hypo = dette.get("ratio_hypotheque_revenu_pct")
                dette_ep = dette.get("taux_epargne_pct")
                dette_var = dette.get("variation_dette_revenu_pct")
                dette_per = dette.get("periode", "")
                dette_section = (
                    f"## Endettement des ménages (StatCan 11-10-0065-01)"
                    + (f" — {dette_per}" if dette_per else "")
                    + "\n\n"
                    + (f"Ratio dette/revenu disponible : **{dette_ratio:.1f} %**  \n" if dette_ratio is not None else "")
                    + (f"Dont hypothèques : **{dette_hypo:.1f} %** du revenu disponible  \n" if dette_hypo is not None else "")
                    + (f"Taux d'épargne net : **{dette_ep:.1f} %**  \n" if dette_ep is not None else "")
                    + (f"Variation annuelle ratio : **{dette_var:+.1f} %**  \n" if dette_var is not None else "")
                    + "\n"
                )
            else:
                dette_section = ""
            # Build affordability index section
            abord = case.get("indice_abordabilite") or {}
            if abord:
                a_loyer_r  = abord.get("ratio_loyer_revenu_pct")
                a_loyer_s  = abord.get("seuil_loyer", "")
                a_mens     = abord.get("versement_mensuel_estime")
                a_mens_r   = abord.get("ratio_mensualite_revenu_pct")
                a_prop_s   = abord.get("seuil_propriete", "")
                a_prop_rev = abord.get("ratio_propriete_revenu")
                a_revenu   = abord.get("revenu_median_menage")
                abord_section = (
                    "## Indice d'abordabilité du logement (calcul interne)\n\n"
                    + (f"Revenu médian ménages : **{a_revenu:,.0f} $**  \n" if a_revenu else "")
                    + (
                        f"\n**Location**  \n"
                        + (f"Ratio loyer/revenu mensuel : **{a_loyer_r:.1f} %** — {a_loyer_s}  \n"
                           if a_loyer_r is not None else "")
                        if a_loyer_r is not None else ""
                    )
                    + (
                        f"\n**Accession à la propriété**  \n"
                        + (f"Multiple valeur/revenu : **{a_prop_rev:.1f}×**  \n" if a_prop_rev else "")
                        + (f"Mensualité estimée (25 ans, 20 % MDP) : **{a_mens:,.0f} $/mois**  \n"
                           if a_mens else "")
                        + (f"Ratio mensualité/revenu : **{a_mens_r:.1f} %** — {a_prop_s}  \n"
                           if a_mens_r is not None else "")
                        if a_mens is not None else ""
                    )
                    + "\n"
                )
            else:
                abord_section = ""
            # Build IPC / inflation section
            ipc = case.get("ipc_logement") or {}
            if ipc:
                ipc_log = ipc.get("ipc_logement")
                ipc_tot = ipc.get("ipc_total")
                ipc_var = ipc.get("variation_logement_pct")
                ipc_per = ipc.get("periode", "")
                ipc_section = (
                    f"## Indice des prix à la consommation — logement"
                    + (f" ({ipc_per})" if ipc_per else "")
                    + "\n\n"
                    + (f"IPC total : **{ipc_tot:.1f}**  \n" if ipc_tot else "")
                    + (f"IPC logement (Shelter) : **{ipc_log:.1f}**  \n" if ipc_log else "")
                    + (f"Variation annuelle logement : **{ipc_var:+.1f} %**  \n" if ipc_var is not None else "")
                    + "\n"
                )
            else:
                ipc_section = ""
            # Build market data section from enrichment (if available)
            ml = case.get("marche_locatif") or {}
            nhpi = case.get("indice_prix_logement") or {}
            vacance = case.get("taux_inoccupation") or {}
            if ml or nhpi or vacance:
                ville_ml = (ml or nhpi or vacance).get("ville", zone)
                loyer_1ch = ml.get("loyer_moyen_1ch")
                loyer_2ch = ml.get("loyer_moyen_2ch")
                loyer_total = ml.get("loyer_moyen_total")
                source_ml = ml.get("source", "")
                indice_total = nhpi.get("indice_total")
                variation_pct = nhpi.get("variation_annuelle_pct")
                source_nhpi = nhpi.get("source", "")
                tx_total = vacance.get("taux_total_pct")
                tx_1ch = vacance.get("taux_1ch_pct")
                tx_2ch = vacance.get("taux_2ch_pct")
                annee_vac = vacance.get("annee", "")
                source_vac = vacance.get("source", "")
                marche_section = (
                    f"## Données marché ({ville_ml})\n\n"
                    + (
                        f"**Loyers moyens (SCHL / {source_ml})**  \n"
                        + (f"1 ch. : {loyer_1ch:,.0f} $/mois  \n" if loyer_1ch else "")
                        + (f"2 ch. : {loyer_2ch:,.0f} $/mois  \n" if loyer_2ch else "")
                        + (f"Total : {loyer_total:,.0f} $/mois  \n" if loyer_total else "")
                        if ml else ""
                    )
                    + (
                        f"\n**Taux d'inoccupation (SCHL / {source_vac})"
                        + (f" — {annee_vac}" if annee_vac else "")
                        + "**  \n"
                        + (f"Total : {tx_total:.1f} %  \n" if tx_total is not None else "")
                        + (f"1 ch. : {tx_1ch:.1f} %  \n" if tx_1ch is not None else "")
                        + (f"2 ch. : {tx_2ch:.1f} %  \n" if tx_2ch is not None else "")
                        if vacance else ""
                    )
                    + (
                        f"\n**Indice des prix du logement neuf (NHPI / {source_nhpi})**  \n"
                        + (f"Indice : {indice_total:.1f}  \n" if indice_total else "")
                        + (f"Variation annuelle : {variation_pct:+.1f} %  \n" if variation_pct is not None else "")
                        if nhpi else ""
                    )
                    + "\n"
                )
            else:
                marche_section = (
                    "## Données marché\n\n"
                    "Données de marché non disponibles pour ce secteur (sources externes non connectées).\n\n"
                )
            # Build construction activity section (permis + mises en chantier + completions)
            permis = case.get("permis_construction") or {}
            chantier = case.get("mises_en_chantier") or {}
            neuf = case.get("marche_neuf") or {}
            if permis or chantier or neuf:
                ville_constr = (permis or chantier or neuf).get("ville", zone)
                u_mois = permis.get("unites_residentielles_mois")
                u_12m  = permis.get("unites_residentielles_12mois")
                val_k  = permis.get("valeur_permis_k_mois")
                var_6m_p = permis.get("variation_pct_6m")
                periode_p = permis.get("periode", "")
                ch_tot = chantier.get("total_mois")
                ch_uni = chantier.get("unifamilial_mois")
                ch_col = chantier.get("collectif_mois")
                ch_12m = chantier.get("total_12mois")
                var_6m_c = chantier.get("variation_pct_6m")
                periode_c = chantier.get("periode", "")
                neuf_comp = neuf.get("completions_mois")
                neuf_12m = neuf.get("completions_12mois")
                neuf_constr = neuf.get("unites_en_construction")
                neuf_abs = neuf.get("taux_absorption_pct")
                periode_n = neuf.get("periode", "")
                permis_section = (
                    f"## Activité de construction ({ville_constr})\n\n"
                    + (
                        f"**Permis de construire ({periode_p})**  \n"
                        + (f"Unités autorisées (mois) : **{u_mois:,.0f}**  \n" if u_mois else "")
                        + (f"Total 12 mois : **{u_12m:,.0f} unités**  \n" if u_12m else "")
                        + (f"Valeur permis (mois) : **{val_k:,.0f} k$**  \n" if val_k else "")
                        + (f"Tendance 6m : **{var_6m_p:+.1f} %**  \n" if var_6m_p is not None else "")
                        if permis else ""
                    )
                    + (
                        f"\n**Mises en chantier ({periode_c})**  \n"
                        + (f"Total (mois) : **{ch_tot:,.0f}**  \n" if ch_tot else "")
                        + (f"Unifamilial : **{ch_uni:,.0f}**  \n" if ch_uni else "")
                        + (f"Collectif : **{ch_col:,.0f}**  \n" if ch_col else "")
                        + (f"Total 12 mois : **{ch_12m:,.0f}**  \n" if ch_12m else "")
                        + (f"Tendance 6m : **{var_6m_c:+.1f} %**  \n" if var_6m_c is not None else "")
                        if chantier else ""
                    )
                    + (
                        f"\n**Completions et pipeline ({periode_n})**  \n"
                        + (f"Completions (mois) : **{neuf_comp:,.0f}**  \n" if neuf_comp else "")
                        + (f"Total completions 12 mois : **{neuf_12m:,.0f}**  \n" if neuf_12m else "")
                        + (f"Unités en construction : **{neuf_constr:,.0f}**  \n" if neuf_constr else "")
                        + (f"Taux d'absorption : **{neuf_abs:.1f} %**  \n" if neuf_abs is not None else "")
                        if neuf else ""
                    )
                    + "\n"
                )
                # Append absorbed units subsection if available
                absorb = case.get("unites_absorbees") or {}
                if absorb:
                    ab_tot = absorb.get("unites_absorbees_total")
                    ab_uni = absorb.get("unites_absorbees_unifamilial")
                    ab_app = absorb.get("unites_absorbees_appartement")
                    ab_var = absorb.get("variation_pct_4q")
                    ab_per = absorb.get("periode", "")
                    permis_section += (
                        f"\n**Unités absorbées — marché neuf (StatCan 34-10-0149-01"
                        + (f", {ab_per}" if ab_per else "")
                        + ")**  \n"
                        + (f"Total absorbées (trimestre) : **{ab_tot:,.0f}**  \n" if ab_tot is not None else "")
                        + (f"Unifamilial : **{ab_uni:,.0f}**  \n" if ab_uni is not None else "")
                        + (f"Appartement/condo : **{ab_app:,.0f}**  \n" if ab_app is not None else "")
                        + (f"Variation annuelle : **{ab_var:+.1f} %**  \n" if ab_var is not None else "")
                        + "\n"
                    )
            else:
                permis_section = ""
            # Build census socio-demographic section
            census = case.get("donnees_sociodemographiques") or {}
            if census:
                pct_prop = census.get("pct_proprietaires")
                pct_loc = census.get("pct_locataires")
                val_med = census.get("valeur_mediane_logement")
                loyer_med = census.get("frais_loyer_median")
                revenu_med = census.get("revenu_median_menage")
                census_section = (
                    f"## Données socio-démographiques (Recensement 2021)\n\n"
                    + (f"Propriétaires : **{pct_prop:,.0f}**  \n" if pct_prop else "")
                    + (f"Locataires : **{pct_loc:,.0f}**  \n" if pct_loc else "")
                    + (f"Valeur médiane logements propriétaires : **{val_med:,.0f} $**  \n" if val_med else "")
                    + (f"Frais mensuels médians (locataires) : **{loyer_med:,.0f} $/mois**  \n" if loyer_med else "")
                    + (f"Revenu médian des ménages : **{revenu_med:,.0f} $**  \n" if revenu_med else "")
                    + "\n"
                )
            else:
                census_section = ""
            # Build proximity services section
            prox = case.get("proximite_services") or {}
            if prox:
                ecoles = prox.get("ecoles_1km")
                transports = prox.get("arrets_transport_500m")
                epiceries = prox.get("epiceries_500m")
                parcs = prox.get("parcs_1km")
                hopitaux = prox.get("hopitaux_2km")
                pharmacies = prox.get("pharmacies_500m")
                proximite_section = (
                    "## Proximité des services (OpenStreetMap)\n\n"
                    + (f"Écoles (1 km) : **{ecoles}**  \n" if ecoles is not None else "")
                    + (f"Arrêts de transport (500 m) : **{transports}**  \n" if transports is not None else "")
                    + (f"Épiceries (500 m) : **{epiceries}**  \n" if epiceries is not None else "")
                    + (f"Parcs/jardins (1 km) : **{parcs}**  \n" if parcs is not None else "")
                    + (f"Hôpitaux/cliniques (2 km) : **{hopitaux}**  \n" if hopitaux is not None else "")
                    + (f"Pharmacies (500 m) : **{pharmacies}**  \n" if pharmacies is not None else "")
                    + "\n"
                )
            else:
                proximite_section = ""
            # Build road proximity section
            routes = case.get("proximite_routes") or {}
            if routes:
                r_auto = routes.get("autoroute_km")
                r_nat = routes.get("route_nationale_km")
                r_art = routes.get("artere_km")
                r_interp = routes.get("interpretation", "")
                routes_section = (
                    "## Accès aux axes routiers (OpenStreetMap)\n\n"
                    + (f"Autoroute la plus proche : **{r_auto:.1f} km**  \n" if r_auto is not None else "")
                    + (f"Route nationale (trunk) : **{r_nat:.1f} km**  \n" if r_nat is not None else "")
                    + (f"Artère principale : **{r_art:.1f} km**  \n" if r_art is not None else "")
                    + (f"Évaluation : **{r_interp}**  \n" if r_interp else "")
                    + "\n"
                )
            else:
                routes_section = ""
            # Build post-secondary education section
            postsec = case.get("enseignement_postsecondaire") or {}
            if postsec:
                ps_cegep = postsec.get("cegep_5km")
                ps_univ  = postsec.get("universite_10km")
                ps_total = postsec.get("total_postsecondaire")
                ps_interp = postsec.get("interpretation", "")
                postsec_section = (
                    "## Enseignement post-secondaire (OpenStreetMap)\n\n"
                    + (f"CÉGEP / collèges (5 km) : **{ps_cegep}**  \n" if ps_cegep is not None else "")
                    + (f"Universités (10 km) : **{ps_univ}**  \n" if ps_univ is not None else "")
                    + (f"Total établissements : **{ps_total}**  \n" if ps_total is not None else "")
                    + (f"Profil : **{ps_interp}**  \n" if ps_interp else "")
                    + "\n"
                )
            else:
                postsec_section = ""
            # Build environmental nuisances section
            nuisances = case.get("nuisances_environnementales") or {}
            if nuisances:
                n_aero = nuisances.get("aeroports_10km")
                n_rail = nuisances.get("voies_ferrees_500m")
                n_ind  = nuisances.get("zones_industrielles_1km")
                n_carr = nuisances.get("carrieres_2km")
                n_score = nuisances.get("score_nuisances", 0)
                n_interp = nuisances.get("interpretation", "")
                nuisances_section = (
                    "## Nuisances environnementales (OpenStreetMap)\n\n"
                    + (f"Aéroports/aérodromes (10 km) : **{n_aero}**  \n" if n_aero is not None else "")
                    + (f"Voies ferrées (500 m) : **{n_rail}**  \n" if n_rail is not None else "")
                    + (f"Zones industrielles (1 km) : **{n_ind}**  \n" if n_ind is not None else "")
                    + (f"Carrières/dépotoirs (2 km) : **{n_carr}**  \n" if n_carr is not None else "")
                    + (f"Score nuisances : **{n_score}/4**  \n" if n_score is not None else "")
                    + (f"Évaluation : **{n_interp}**  \n" if n_interp else "")
                    + ("\n> ⚠️ Analyse approfondie des nuisances recommandée.\n" if n_score >= 2 else "")
                    + "\n"
                )
            else:
                nuisances_section = ""
            # Build climate data section
            climat = case.get("donnees_climatiques") or {}
            if climat:
                c_temp = climat.get("temperature_moyenne_annuelle")
                c_prec = climat.get("precipitations_annuelles_mm")
                c_gel  = climat.get("jours_gel")
                c_chal = climat.get("jours_chaleur_extreme")
                c_annee = climat.get("annee_reference", "")
                climat_section = (
                    f"## Données climatiques — {c_annee} (Open-Meteo)\n\n"
                    + (f"Température moyenne annuelle : **{c_temp:.1f} °C**  \n" if c_temp is not None else "")
                    + (f"Précipitations annuelles : **{c_prec:,.0f} mm**  \n" if c_prec is not None else "")
                    + (f"Jours de gel (T_min < 0 °C) : **{c_gel}**  \n" if c_gel is not None else "")
                    + (f"Jours de chaleur extrême (T_max ≥ 30 °C) : **{c_chal}**  \n" if c_chal is not None else "")
                    + "\n"
                )
            else:
                climat_section = ""
            # Build distance to CBD section
            dist_cbd = case.get("distance_cbd") or {}
            if dist_cbd:
                d_km = dist_cbd.get("distance_cbd_km")
                d_ref = dist_cbd.get("ville_reference", zone)
                d_interp = dist_cbd.get("interpretation", "")
                dist_section = (
                    f"## Localisation — distance au centre-ville\n\n"
                    + (f"Centre de référence : {d_ref}  \n" if d_ref else "")
                    + (f"Distance (Haversine) : **{d_km:.2f} km**  \n" if d_km is not None else "")
                    + (f"Secteur : **{d_interp}**  \n" if d_interp else "")
                    + "\n"
                )
            else:
                dist_section = ""
            # Build renovation cost section
            cr_d = case.get("cout_renovation") or {}
            if cr_d:
                cr_min = cr_d.get("cout_min")
                cr_max = cr_d.get("cout_max")
                cr_med = cr_d.get("cout_median")
                cr_type = cr_d.get("type_travaux", "")
                cr_surf = cr_d.get("surface_m2")
                renov_section = (
                    "## Coût estimé de rénovation (calcul interne)\n\n"
                    + (f"Surface de référence : **{cr_surf:.0f} m²**  \n" if cr_surf else "")
                    + (f"Type de travaux : **{cr_type}**  \n" if cr_type else "")
                    + (f"Fourchette estimée : **{cr_min:,.0f} $ – {cr_max:,.0f} $**  \n" if cr_min is not None else "")
                    + (f"Valeur médiane : **{cr_med:,.0f} $**  \n" if cr_med else "")
                    + "\n*Source : barèmes APCHQ/CAA-Québec 2024 — estimation indicative.*\n\n"
                )
            else:
                renov_section = ""
            # Build building age / depreciation section
            vet_d = case.get("vetuste_batiment") or {}
            if vet_d:
                vet_age = vet_d.get("age_ans")
                vet_annee = vet_d.get("annee_construction")
                vet_cat = vet_d.get("categorie", "")
                vet_depr = vet_d.get("taux_depreciation_pct")
                vet_resid = vet_d.get("valeur_residuelle_pct")
                vet_renov = vet_d.get("renovation_recommandee")
                vetuste_section = (
                    "## Vétusté du bâtiment (calcul interne)\n\n"
                    + (f"Année de construction : **{vet_annee}** ({vet_age} ans)  \n" if vet_annee else "")
                    + (f"Catégorie : **{vet_cat}**  \n" if vet_cat else "")
                    + (f"Dépréciation physique estimée : **{vet_depr:.1f} %**  \n" if vet_depr is not None else "")
                    + (f"Valeur résiduelle estimée : **{vet_resid:.1f} %**  \n" if vet_resid is not None else "")
                    + (f"Rénovation majeure recommandée : **{'Oui' if vet_renov else 'Non'}**  \n" if vet_renov is not None else "")
                    + "\n"
                )
            else:
                vetuste_section = ""
            # Build municipal taxes section
            tx = case.get("taxes_municipales") or {}
            if tx:
                tx_taux = tx.get("taux_taxation_pct")
                tx_annuel = tx.get("taxes_annuelles_estimees")
                tx_mensuel = tx.get("taxes_mensuelles_estimees")
                tx_comp = tx.get("comparaison", "")
                taxes_section = (
                    "## Profil fiscal municipal\n\n"
                    + (f"Taux de taxation résidentiel : **{tx_taux:.3f} %** de la valeur d'évaluation  \n" if tx_taux else "")
                    + (f"Taxes annuelles estimées : **{tx_annuel:,.0f} $**  \n" if tx_annuel else "")
                    + (f"Taxes mensuelles estimées : **{tx_mensuel:,.0f} $/mois**  \n" if tx_mensuel else "")
                    + (f"Comparaison : {tx_comp}  \n" if tx_comp else "")
                    + "\n"
                )
            else:
                taxes_section = ""
            payload["_raw_md"] = (
                f"# Analyse du Meilleur Usage (AMU)\n\n"
                f"**Dossier :** {dossier_id}  \n"
                f"**Type de bien :** {type_bien}  \n"
                f"**Zone :** {zone_code}\n\n"
                + zonage_section
                + patrimoine_section
                + inond_section
                + cptaq_section
                + dist_section
                + f"## Critere 1 — Legalement permis\n\n"
                f"L'usage de type {type_bien} est conforme au zonage {zone_code}. "
                f"Aucune restriction legale identifiee.\n\n"
                f"## Critere 2 — Physiquement possible\n\n"
                f"Les caracteristiques physiques du terrain et du batiment sont "
                f"compatibles avec l'usage de type {type_bien}.\n\n"
                f"## Critere 3 — Financierement faisable\n\n"
                f"Le marche supporte l'usage de type {type_bien} dans ce secteur.\n\n"
                + pop_section
                + financement_section
                + dette_section
                + abord_section
                + ipc_section
                + marche_section
                + permis_section
                + census_section
                + proximite_section
                + routes_section
                + postsec_section
                + nuisances_section
                + climat_section
                + vetuste_section
                + renov_section
                + taxes_section
                + f"## Critere 4 — Maximalement productif\n\n"
                f"L'usage actuel ({type_bien}) constitue l'usage le meilleur et le "
                f"plus profitable (UMPP) pour ce bien.\n\n"
                f"## Conclusion UMPP\n\n"
                f"L'usage actuel correspond a l'UMPP. L'evaluation procede selon "
                f"les methodes appropriees a ce type de bien.\n"
            )

        if step == "mandat-intake" and artifact == "conflit_interets.json":
            _conflit = check_conflit_interets(case)
            payload.update({
                "conflit_detecte": _conflit.conflit_detecte,
                "conflit_motif": _conflit.motif,
                "verification_completee": True,
                "commentaire": (
                    f"Conflit détecté : {_conflit.motif}"
                    if _conflit.conflit_detecte
                    else "Aucun conflit d'intérêts détecté — vérification déterministe."
                ),
                "analyse_conflit": "",
            })

        if step == "mandat-intake" and artifact == "lettre_mandat.md":
            type_bien = str(case.get("type_bien", "inconnu")).replace("_", " ")
            mandat_type = str(case.get("mandat_type", "residentiel_standard"))
            format_rapport = str(case.get("format_rapport", "abrege"))
            date_ref = case.get("date_reference", "—")
            dossier_id = case.get("dossier_id", "—")
            commanditaire = case.get("commanditaire", {})
            nom_cmd = str(commanditaire.get("nom", "") or "[COMMANDITAIRE]") if commanditaire else "[COMMANDITAIRE]"
            org_cmd = str(commanditaire.get("organisation", "")) if commanditaire else ""
            cmd_label = f"{nom_cmd} — {org_cmd}" if org_cmd else nom_cmd
            fin_eval = str(commanditaire.get("fin_evaluation", "non specifie")).replace("_", " ") if commanditaire else "non specifie"
            payload["_raw_md"] = (
                f"# Lettre de mandat\n\n"
                f"**Dossier :** {dossier_id}  \n"
                f"**Type de bien :** {type_bien}  \n"
                f"**Type de mandat :** {mandat_type}  \n"
                f"**Format du rapport :** {format_rapport}  \n"
                f"**Date de référence :** {date_ref}\n\n"
                f"## Identification du bien\n\n"
                f"Bien de type {type_bien} tel que décrit dans le dossier {dossier_id}.\n\n"
                f"## Identification du commanditaire\n\n"
                f"Commanditaire : {cmd_label}\n\n"
                f"## Type d'acte professionnel\n\n"
                f"Évaluation immobilière — rapport {format_rapport}.\n\n"
                f"## Fin d'évaluation\n\n"
                f"Mandat de type {mandat_type} — fin : {fin_eval}.\n\n"
                f"## Honoraires et conditions\n\n"
                f"À confirmer selon entente avec le commanditaire.\n\n"
                f"## Signatures\n\n"
                f"_Évaluateur agréé (É.A.) — signature requise_  \n"
                f"_Commanditaire — signature requise_\n"
            )

        if step == "comps-market" and artifact == "comparables_proposes.json":
            payload["date_reference"] = case.get("date_reference")

            # Auto-alimenter le pool si aucun comparable n'a été chargé (CSV JLR absent)
            if not case.get("comparables"):
                try:
                    from engine.comparables_builder import build_comparable_pool
                    from engine.data_enrichment import get_data_cache_dir
                    from engine.source_diagnostics import attach_source_coverage, ensure_source_diagnostics
                    address = str(case.get("adresse_complete") or "")
                    if address:
                        diagnostics = ensure_source_diagnostics(case)
                        auto_pool = build_comparable_pool(
                            subject_address=address,
                            subject_surface_m2=float(case.get("surface_habitable") or 0),
                            subject_type_bien=str(case.get("type_bien") or ""),
                            subject_annee_construction=int(case.get("annee_construction") or 0),
                            cache_dir=get_data_cache_dir(),
                            diagnostics=diagnostics,
                        )
                        attach_source_coverage(case)
                        if auto_pool:
                            case["comparables"] = auto_pool
                            logger.info(
                                "Pool auto-alimenté Infolot+MAMH: %d candidats pour '%s'",
                                len(auto_pool), address,
                            )
                except Exception as exc:
                    logger.warning("build_comparable_pool failed (non-bloquant): %s", exc)

            payload["comparables"] = [
                c.__dict__
                for c in search_comparables(
                    case.get("comparables", []),
                    max_items=5,
                    subject=case,
                    date_reference=case.get("date_reference"),
                )
            ]
            if case.get("marche_locatif"):
                payload["marche_locatif"] = case["marche_locatif"]

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
            approach_id = approach_by_artifact[artifact]
            if approach_id in ("approche_cout", "approche_revenu") and approach_id not in approaches_for_case(case):
                payload.update({
                    "approach": approach_id,
                    "applicable": False,
                    "value": None,
                    "input_count": 0,
                    "calculation_status": "NOT_APPLICABLE",
                })
            else:
                payload.update(calculate_valuation_trace(case, approach_id))

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
            payload["_raw_md"] = _build_annexe_sources_md(case)

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
        on_step_done=None,
        steps_filter: list[str] | None = None,
    ) -> dict:
        """Execute pipeline steps.

        Args:
            steps_filter: If provided, only run steps whose name is in this list.
                          Used by run_pipeline_until() to execute one checkpoint segment.
                          None = run all steps (legacy / one-shot mode).
        """
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
            if steps_filter is not None and step.name not in steps_filter:
                continue  # skip steps not in this checkpoint segment
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

                schema_failures = validate_artifact_schema(artifact, payload)
                if schema_failures:
                    formatted_failures = [f"JSON_SCHEMA: {failure}" for failure in schema_failures]
                    blocking = _unique([*blocking, *formatted_failures])
                    status = _status_from_contracts(has_blocking=True, has_warnings=bool(warnings))
                    self._record_event(
                        events,
                        audit_log_path,
                        {
                            "event": "json_schema_invalid",
                            "step": step.name,
                            "artifact": artifact,
                            "failures": schema_failures,
                        },
                    )
                    if step.name == "compliance-qa":
                        payload.setdefault("blocking_failures", []).extend(formatted_failures)

                write_artifact_payload(artifact_path, payload)
                self._record_event(
                    events,
                    audit_log_path,
                    {"event": "artifact_written", "step": step.name, "artifact": artifact, "path": artifact_path.as_posix()},
                )

            self._record_event(events, audit_log_path, {"event": "step_done", "step": step.name, "dossier_id": dossier_id})
            if on_step_done is not None:
                try:
                    on_step_done(step.name)
                except Exception:
                    pass  # progress callback never blocks pipeline

            # Gate conflit après mandat-intake
            if step.name == "mandat-intake":
                if case_subdir:
                    _conflit_path = case_dir / "mandat-intake.conflit_interets.json"
                else:
                    _conflit_path = case_dir / f"{case_key}.mandat-intake.conflit_interets.json"
                if _conflit_path.exists():
                    _conflit = json.loads(_conflit_path.read_text(encoding="utf-8"))
                    if _conflit.get("conflit_detecte") and not case.get("force_conflit_continue"):
                        motif = _conflit.get("conflit_motif", "Conflit detecte par analyse mandat-intake")
                        raise PipelineConflitError(motif)

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


# Domaines normatifs prioritaires par type de mandat/bien
_NORMATIVE_DOMAINS_ALWAYS = {
    "oeaq_professional_standards",   # NPP OEAQ
    "cuspap_nuppec_professional_standards",  # CUSPAP 2026
}
_NORMATIVE_DOMAINS_RESIDENTIAL = {
    "municipal_assessment_manual",   # MEFQ
    "municipal_statute_regulation",  # LFM
    "oeaq_regulation",               # Règlements OEAQ
}
_NORMATIVE_SOURCE_FAMILIES_KEY = {
    # source_family → abréviation de citation
    "NPP OEAQ": "NPP OEAQ",
    "CUSPAP/NUPPEC 2026": "CUSPAP 2026",
    "Manuel d'évaluation foncière du Québec": "MEFQ 2025",
    "Loi sur la fiscalité municipale": "LFM",
    "OEAQ Règlements": "Règl. OEAQ",
    "AIC Canada": "AIC",
}


def _normative_sources_for_case(case: dict) -> list[dict]:
    """Retourne les entrées du source-catalog normatives pertinentes pour le dossier.

    Sélectionne selon le type de bien et le mandat. Toujours inclus : NPP + CUSPAP.
    Pour résidentiel standard : ajoute MEFQ + LFM.
    """
    try:
        from engine.knowledge_rag import load_catalog  # type: ignore
        catalog = load_catalog()
    except Exception:
        return []

    type_bien = str(case.get("type_bien", "")).lower()
    mandat_type = str(case.get("mandat_type", "residentiel_standard")).lower()

    active_domains = set(_NORMATIVE_DOMAINS_ALWAYS)
    if any(k in type_bien or k in mandat_type for k in ("resident", "unifami", "duplex", "triplex", "condo")):
        active_domains |= _NORMATIVE_DOMAINS_RESIDENTIAL
    elif any(k in type_bien or k in mandat_type for k in ("commercial", "bureau", "industriel", "agricole")):
        active_domains.add("municipal_assessment_manual")
        active_domains.add("municipal_statute_regulation")

    seen_families: set[str] = set()
    sources: list[dict] = []
    for entry in catalog:
        if entry.get("domain") not in active_domains:
            continue
        family = entry.get("source_family", "")
        if family in seen_families:
            continue
        seen_families.add(family)
        short = _NORMATIVE_SOURCE_FAMILIES_KEY.get(family, family)
        sources.append({
            "source_id": entry["source_id"],
            "source_family": family,
            "short": short,
            "domain": entry["domain"],
            "folder": entry["folder"],
            "official_source": entry.get("official_source", ""),
        })
    return sources


def _build_annexe_sources_md(case: dict) -> str:
    """Construit le contenu markdown de annexe_sources.md.

    Inclut : sources de données (comparables/hypothèses) + sources normatives.
    """
    data_ids = collect_source_ids(case)
    normative = _normative_sources_for_case(case)

    lines: list[str] = [
        "# Annexe — Sources et références\n",
        f"**Dossier :** {case.get('dossier_id', '—')}  \n",
        f"**Date de référence :** {case.get('date_reference', '—')}  \n",
        "",
    ]

    # Sources de données
    lines += [
        "## Sources de données\n",
        f"Nombre de sources : {len(data_ids)}\n",
    ]
    if data_ids:
        lines.append("\n| # | source_id |")
        lines.append("|---|---|")
        for i, sid in enumerate(data_ids, 1):
            lines.append(f"| {i} | {sid} |")
    else:
        lines.append("_Aucune source de données identifiée._")
    lines.append("")

    # Sources normatives
    lines += [
        "## Sources normatives applicables\n",
        "Les règles et normes suivantes s'appliquent à ce dossier :\n",
    ]
    if normative:
        lines.append("\n| Abréviation | Document | Domaine | Source officielle |")
        lines.append("|---|---|---|---|")
        for s in normative:
            url = s["official_source"]
            url_cell = f"[lien]({url})" if url else "—"
            lines.append(
                f"| **{s['short']}** | {s['source_family']} | {s['domain']} | {url_cell} |"
            )
    else:
        lines.append("_Catalogue normatif non disponible._")
    lines.append("")

    lines += [
        "## Note de traçabilité\n",
        "Chaque affirmation quantitative du rapport est rattachée à un `source_id` de données.  \n",
        "Chaque règle normative citée dans le corps du rapport correspond à une entrée du tableau ci-dessus.  \n",
        "Le corpus complet est disponible dans `backend/knowledge/corpus/`.  \n",
    ]

    return "\n".join(lines)


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


_RAPPORT_MAX_TOKENS = 4000

_RAPPORT_SYSTEM_PROMPT_ABREGE = (
    "Tu es un expert en rédaction de rapports d'évaluation immobilière au Québec, conforme aux normes OEAQ/CUSPAP 2026.\n\n"
    "Génère un RAPPORT ABRÉGÉ (formulaire) professionnel en Markdown. Format cible : 5-6 pages, "
    "tous les 16 éléments obligatoires CUSPAP présents.\n\n"
    "STRUCTURE OBLIGATOIRE (rapport abrégé) :\n"
    "1. Identification — dossier, mandant, propriétaire, conclusion de valeur, but et fin\n"
    "2. Généralités — secteur, marché, données municipales, zonage\n"
    "3. Description — terrain, UMPP (analyse brève), bâtiment (généralités, composantes, finition)\n"
    "4. Approches de valeur — méthode du coût et/ou de comparaison (3-5 comparables avec ajustements)\n"
    "5. Réconciliation et attestation — jugement pondéré (jamais une moyenne), valeur en chiffres ET lettres\n"
    "6. Réserves et hypothèses — clauses standards OEAQ\n\n"
    "RÈGLES ABSOLUES :\n"
    "- BROUILLON NON CERTIFIÉ bien visible en tête\n"
    "- N'invente aucune donnée non fournie dans le prompt\n"
    "- Valeur finale en chiffres ET en lettres (ex: 475 000 $ (quatre cent soixante-quinze mille dollars))\n"
    "- Réconciliation = jugement professionnel pondéré, jamais une moyenne arithmétique\n"
    "- La méthode du coût ne peut servir aux fins d'assurance\n"
    "- Justifier tout rejet de méthode (élément 10 CUSPAP)\n"
    "- Langue : français canadien professionnel\n"
    "- Format : Markdown avec titres numérotés, tableaux pour comparables et ajustements\n"
)

_RAPPORT_SYSTEM_PROMPT_COMPLET = (
    "Tu es un expert en rédaction de rapports d'évaluation immobilière au Québec, conforme aux normes OEAQ/CUSPAP 2026.\n\n"
    "Génère un RAPPORT NARRATIF COMPLET en Markdown. Format cible : 15+ sections, "
    "tous les 16 éléments obligatoires CUSPAP.\n\n"
    "STRUCTURE OBLIGATOIRE (15 sections) :\n"
    "0. Lettre de transmission — client, objet, conclusion (chiffres + lettres), référence OEAQ\n"
    "1. Page titre — titre, adresse, référence, date\n"
    "2. Table des matières\n"
    "3. Identification de l'immeuble (éléments 1-5) — adresse, cadastre, droits évalués, but/fin, définition valeur, date référence, historique\n"
    "4. Étendue du travail (élément 6) — visite, collecte, recherches, analyses, vérifications\n"
    "5. Réserves et hypothèses (élément 7) — 11 clauses standard OEAQ + extraordinaires si applicable\n"
    "6. Informations générales — ville, secteur, marché, données municipales, zonage, infrastructures\n"
    "7. Description de l'immeuble (éléments 1, 8) — terrain, UMPP (élément 9), bâtiment (généralités, composantes, finition)\n"
    "8. Évaluation et analyse (éléments 10, 11) — présentation des 3 méthodes, justification retenues/rejetées\n"
    "9. Méthode du coût — terrain (comparables $/m²), coût neuf, dépréciations, conclusion\n"
    "10. Méthode de comparaison — tableau comparables, fiches détaillées, ajustements, taux, conclusion\n"
    "11. Méthode du revenu — RBP, vacance, RBE, frais, RNE, TGA, capitalisation, conclusion ou justification non-application\n"
    "12. Réconciliation (élément 13) — résultats, analyse chaque indication, méthode prépondérante, valeur finale\n"
    "13. Attestation (élément 12) — 7 déclarations OEAQ, inspection, conclusion chiffres+lettres, [SIGNATURE É.A.]\n"
    "14. Extrait NPP — éléments applicables\n"
    "15. Annexes (élément 16) — liste pièces jointes\n\n"
    "RÈGLES ABSOLUES :\n"
    "- BROUILLON NON CERTIFIÉ bien visible en tête ET à l'attestation\n"
    "- N'invente aucune donnée non fournie dans le prompt\n"
    "- Valeur finale en chiffres ET en lettres\n"
    "- Réconciliation = jugement professionnel pondéré, jamais une moyenne arithmétique\n"
    "- Attestation avec les 7 déclarations OEAQ (à signer par l'É.A.)\n"
    "- Justifier tout rejet de méthode (élément 10)\n"
    "- Langue : français canadien professionnel\n"
    "- Format : Markdown structuré avec titres numérotés\n"
)


_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

# Mapping type_bien → fichier template rapport
_RAPPORT_TEMPLATE_MAP: dict[str, str] = {
    "residentiel_unifamilial": "rapport_residentiel_unifamilial.md",
    "condo":                   "rapport_residentiel_unifamilial.md",  # même structure
    "duplex":                  "rapport_residentiel_unifamilial.md",
    "triplex":                 "rapport_residentiel_unifamilial.md",
    "quadruplex":              "rapport_residentiel_unifamilial.md",
    "immeuble_revenus":        "rapport_immeuble_revenus.md",
    "commercial":              "rapport_commercial.md",
    "terrain":                 "rapport_residentiel_unifamilial.md",  # même structure de base
}


def _load_rapport_template(type_bien: str) -> str | None:
    """Charge le template de rapport selon le type de bien. Retourne None si absent."""
    filename = _RAPPORT_TEMPLATE_MAP.get(str(type_bien or "").lower())
    if not filename:
        filename = "rapport_residentiel_unifamilial.md"
    path = _TEMPLATES_DIR / filename
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _fmt_cad(value: float) -> str:
    """Formate un montant en dollars canadiens."""
    return f"{round(value):,}".replace(",", "\u00a0") + " $"


def _build_rapport_prompt_v2(
    case: dict,
    format: str,
    valuation_values: dict,
    status: str,
    blocking: list,
    warnings: list,
) -> str:
    """Construit le prompt utilisateur enrichi pour la génération du rapport."""
    surface = case.get("surface", {})
    surface_str = (
        f"{surface.get('value', '—')} {surface.get('unit', 'm²')}"
        if isinstance(surface, dict)
        else str(surface or "—")
    )
    cmd = case.get("commanditaire", {}) if isinstance(case.get("commanditaire"), dict) else {}
    format_label = (
        "Rapport abrégé (formulaire)"
        if format == "abrege"
        else "Rapport narratif complet 15 sections CUSPAP"
    )
    comp_lines = []
    for i, c in enumerate(case.get("comparables", [])[:5], 1):
        price = c.get("prix_vente") or c.get("sale_price")
        price_str = _fmt_cad(float(price)) if price else "—"
        score = c.get("score", "—")
        score_str = f"{float(score):.2f}" if isinstance(score, (int, float)) else str(score)
        comp_lines.append(
            f"  {i}. source={c.get('source_id', '—')} | adresse={c.get('adresse', '—')} | "
            f"prix={price_str} | date={c.get('date_vente', '—')} | score={score_str}"
        )
    approach_lines = []
    labels = {
        "approche_comparative": "Approche comparative",
        "approche_cout": "Approche par le coût",
        "approche_revenu": "Approche par le revenu",
    }
    for key, label in labels.items():
        if key in valuation_values:
            approach_lines.append(f"  - {label} : {_fmt_cad(valuation_values[key])}")
    lines = [
        f"FORMAT: {format} — {format_label}",
        f"DOSSIER: {case.get('dossier_id', '—')}",
        f"COMMANDITAIRE: {cmd.get('nom', '—')} — {cmd.get('organisation', '—')}",
        f"FIN ÉVALUATION: {cmd.get('fin_evaluation', '—')}",
        f"TYPE MANDAT: {case.get('mandat_type', case.get('type_bien', '—'))}",
        f"DATE RÉFÉRENCE: {case.get('date_reference', '—')}",
        "",
        "IDENTIFICATION:",
        f"  Adresse: {case.get('adresse', case.get('display_name', '—'))}",
        f"  Type de bien: {case.get('type_bien', '—')}",
        f"  Zone / secteur: {case.get('zone', '—')}",
        f"  Surface habitable: {surface_str}",
        f"  Surface terrain: {case.get('surface_terrain', '—')} m²",
        f"  Année construction: {case.get('annee_construction', '—')}",
        f"  Nb logements: {case.get('nb_logements', '—')}",
        "",
        f"APPROCHES DE VALEUR ({len(approach_lines)}):",
        *approach_lines,
        "",
        f"COMPARABLES RETENUS ({len(case.get('comparables', []))}):",
        *comp_lines,
        "",
        f"STATUT CONFORMITÉ: {status}",
    ]
    if blocking:
        lines += [f"BLOCAGES ({len(blocking)}): " + "; ".join(str(b) for b in blocking[:3])]
    if warnings:
        lines += [f"AVERTISSEMENTS ({len(warnings)}): " + "; ".join(str(w) for w in warnings[:3])]
    hypotheses = case.get("hypotheses_explicites") or case.get("hypotheses", [])
    if hypotheses and isinstance(hypotheses, list):
        lines += ["", f"HYPOTHÈSES ({len(hypotheses)}):"]
        for h in hypotheses[:3]:
            lines.append(f"  - {h}")

    # T3.2 — Injecter la grille d'ajustements calculée (évite les [ADJ] vides)
    grille_data = case.get("_grille_ajustements")  # injecté par run_case_data si disponible
    if not grille_data:
        from engine.adjustments import compute_adjustment_grid  # type: ignore
        grille_result = compute_adjustment_grid(case)
        grille_data = grille_result.get("grilles", [])
    if grille_data:
        grille_lines = ["", "GRILLE D'AJUSTEMENTS (à utiliser dans la table comparative du rapport) :"]
        for g in grille_data[:5]:
            prix_ajuste = g.get("prix_ajuste", 0)
            prix_vendu = g.get("prix_vendu", 0)
            total_adj = g.get("total_ajustements", 0)
            pct = g.get("pct_total_brut", 0)
            grille_lines.append(
                f"  Comparable {g.get('comparable_id', '?')} : "
                f"prix vendu {_fmt_cad(prix_vendu)} | "
                f"ajustements {_fmt_cad(total_adj)} ({pct:.1f}%) | "
                f"prix ajusté {_fmt_cad(prix_ajuste)}"
            )
            for adj in g.get("ajustements", []):
                if adj.get("montant", 0) != 0:
                    grille_lines.append(
                        f"    • {adj['caracteristique']}: {_fmt_cad(adj['montant'])} "
                        f"({adj.get('taux_info', '—')}) [{adj.get('statut', '?')}]"
                    )
        fourchette = grille_result.get("fourchette", {}) if not case.get("_grille_ajustements") else {}
        if fourchette:
            grille_lines.append(
                f"  Fourchette : {_fmt_cad(fourchette.get('min', 0))} – {_fmt_cad(fourchette.get('max', 0))} "
                f"(écart {fourchette.get('ecart_pct', 0):.1f}%)"
            )
        lines += grille_lines

    # Inject normative references so LLM cites them in the report
    normative = _normative_sources_for_case(case)
    if normative:
        norm_lines = [
            "",
            "SOURCES NORMATIVES APPLICABLES (à citer dans les sections pertinentes) :",
        ]
        for s in normative:
            norm_lines.append(f"  - {s['short']} : {s['source_family']}")
        norm_lines += [
            "CONSIGNE : chaque règle invoquée dans le rapport doit citer son abréviation entre crochets,",
            "ex. « L'évaluateur doit analyser les quatre critères [NPP OEAQ §8] ».",
            "ex. « La valeur retenue respecte les limites plausibles [MEFQ 2025 Partie 3] ».",
        ]
        lines += norm_lines

    # Inject template structure as guidance if available
    template_txt = _load_rapport_template(case.get("type_bien", ""))
    if template_txt:
        lines += [
            "",
            "STRUCTURE DU RAPPORT (respecter cet ordre de sections) :",
            "---",
            template_txt[:3000],  # cap at 3000 chars to stay within context
            "---",
        ]
    return "\n".join(lines)


def _generate_rapport_llm(prompt: str, format: str = "abrege") -> dict | None:
    """Appelle OpenAI pour générer le rapport.

    Retourne None si indisponible, sinon dict avec:
        {"text": str, "model": str, "tokens_in": int, "tokens_out": int, "cost_usd": float}
    """
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return None
    try:
        import openai as _openai  # type: ignore
        client = _openai.OpenAI(api_key=api_key)
        system_prompt = (
            _RAPPORT_SYSTEM_PROMPT_COMPLET if format == "complet" else _RAPPORT_SYSTEM_PROMPT_ABREGE
        )
        model = get_llm_model("redaction_rapport")
        resp = client.chat.completions.create(
            model=model,
            max_tokens=_RAPPORT_MAX_TOKENS,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        text = resp.choices[0].message.content or None
        if not text:
            return None
        tokens_in = getattr(resp.usage, "prompt_tokens", 0) or 0
        tokens_out = getattr(resp.usage, "completion_tokens", 0) or 0
        return {
            "text": text,
            "model": model,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": estimate_llm_cost(model, tokens_in, tokens_out),
        }
    except Exception:
        return None


def _generate_rapport_deterministic(case: dict, valuation_values: dict, status: str, blocking: list, warnings: list) -> str:
    """Repli déterministe — 16 éléments structurels, mode dégradé honnête (T3.4).

    Produit quand OpenAI est indisponible. Les sections nécessitant la prose É.A. sont
    marquées explicitement « À RÉDIGER PAR L'É.A. ». Jamais un faux rapport complet.
    """
    dossier_id = case.get("dossier_id", "—")
    date_ref = case.get("date_reference", "—")
    type_bien = str(case.get("type_bien", "—")).replace("_", " ").capitalize()
    zone = case.get("zone", "—")
    surface = case.get("surface", {})
    surface_str = f"{surface.get('value', '—')} {surface.get('unit', '')}" if isinstance(surface, dict) else str(surface)
    adresse = str(case.get("adresse") or case.get("display_name") or "Non fournie")
    annee_constr = case.get("annee_construction") or "—"
    nb_logements = case.get("nb_logements") or "—"
    surface_terrain = case.get("surface_terrain") or "—"
    today = date.today().isoformat()

    cmd = case.get("commanditaire", {}) or {}
    cmd_nom = cmd.get("nom", "[COMMANDITAIRE]") if isinstance(cmd, dict) else "[COMMANDITAIRE]"
    cmd_org = cmd.get("organisation", "") if isinstance(cmd, dict) else ""
    cmd_label = f"{cmd_nom} — {cmd_org}" if cmd_org else cmd_nom
    fin_eval = str((cmd.get("fin_evaluation", "non spécifié") if isinstance(cmd, dict) else "non spécifié")).replace("_", " ")

    # Valeur principale
    val_principale = valuation_values.get("approche_comparative") or next(iter(valuation_values.values()), None)
    val_str = _fmt_cad(val_principale) if val_principale else "—"

    # AMU / UMPP
    umpp_data = (case.get("umpp") or {})
    if isinstance(umpp_data, dict):
        usage_retenu = umpp_data.get("usage_retenu", type_bien)
        umpp_conclusion = umpp_data.get("conclusion", "À compléter par l'É.A.")
        conformite_zonage = umpp_data.get("conformite_zonage")
        zone_conf_str = "Oui" if conformite_zonage is True else ("Non" if conformite_zonage is False else "Données manquantes")
    else:
        usage_retenu = type_bien
        umpp_conclusion = "À compléter par l'É.A."
        zone_conf_str = "Données manquantes"

    # Comparables + grille
    comparables = case.get("comparables", [])[:5]
    comp_rows = ""
    for i, c in enumerate(comparables, 1):
        price = c.get("prix_vente") or c.get("sale_price")
        price_str = _fmt_cad(float(price)) if price else "—"
        score = c.get("score", "—")
        score_str = f"{float(score):.2f}" if isinstance(score, float) else str(score)
        comp_rows += f"| {i} | {c.get('source_id', '—')} | {price_str} | {c.get('date_vente', '—')} | {score_str} |\n"

    # Grille d'ajustements (T3.2)
    from engine.adjustments import compute_adjustment_grid  # type: ignore
    grille_result = compute_adjustment_grid(case)
    grilles = grille_result.get("grilles", [])
    grille_rows = ""
    for g in grilles[:5]:
        for adj in g.get("ajustements", []):
            montant = adj.get("montant", 0)
            montant_str = _fmt_cad(montant) if montant != 0 else "0"
            statut = adj.get("statut", "?")
            grille_rows += (
                f"| {g.get('comparable_id', '?')} | {adj['caracteristique']} | "
                f"{montant_str} | {adj.get('taux_info', '—')} | {statut} |\n"
            )
    valeur_indiquee = grille_result.get("valeur_indiquee", 0)
    fourchette = grille_result.get("fourchette", {})

    # Approches
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
# RAPPORT D'ÉVALUATION IMMOBILIÈRE — MODE DÉGRADÉ

> **⚠ MODE DÉGRADÉ — Service IA indisponible au moment de la génération.**
> Ce rapport contient la structure des 16 éléments obligatoires avec les données calculées.
> Les sections marquées « À RÉDIGER PAR L'É.A. » requièrent la prose de l'évaluateur agréé.
> **Ce document ne constitue pas un rapport certifié sans révision et signature É.A.**

---

## 1. Identification et but du mandat

| Champ | Valeur |
|---|---|
| Dossier | {dossier_id} |
| Adresse | {adresse} |
| Type de bien | {type_bien} |
| Zone / secteur | {zone} |
| Surface habitable | {surface_str} |
| Surface terrain | {surface_terrain} m² |
| Année construction | {annee_constr} |
| Nb logements | {nb_logements} |
| Commanditaire | {cmd_label} |
| But et fin de l'évaluation | {fin_eval} |
| Date de référence | {date_ref} |

**Droits évalués :** Pleine propriété (à confirmer par É.A.)
**Définition de la valeur :** Valeur marchande au sens de NPP OEAQ et CUSPAP 2026
**Historique des transactions :** À RÉDIGER PAR L'É.A.

---

## 2. Étendue du travail

- Collecte de données : sources structurées du dossier ({dossier_id})
- Inspection du bien : **voir section 14**
- Vérifications effectuées : données cadastrales, zonage, marché (sources automatisées)
- Analyses : approche comparative (grille d'ajustements), approche par le coût (si applicable)

---

## 3. Réserves et hypothèses

1. L'analyse est fondée exclusivement sur les données fournies et vérifiées.
2. Aucune inspection de structure cachée n'a été effectuée.
3. L'évaluateur suppose l'absence de contamination environnementale sauf mention contraire.
4. Les données de registre foncier sont présumées exactes.
5. Les droits réels et servitudes sont ceux déclarés au dossier.
6. La valeur est exprimée en dollars canadiens courants à la date de référence.
7. Cette évaluation est préparée pour l'usage identifié ci-dessus seulement.
8. Les comparables sont issus de sources validées (source_id traçable).
9. Les taux d'ajustement marqués « à_valider » sont des défauts à confirmer par l'É.A.
10. Les sections en mode dégradé nécessitent la révision d'un évaluateur agréé.
11. À RÉDIGER PAR L'É.A. : hypothèses extraordinaires si applicable.

---

## 4. Informations générales et marché

**Ville / Secteur :** {zone}
**Marché immobilier :** À RÉDIGER PAR L'É.A. (données de marché disponibles dans le dossier)
**Données municipales :** À RÉDIGER PAR L'É.A.
**Conformité au zonage :** {zone_conf_str}

---

## 5. Description du terrain

**Superficie :** {surface_terrain} m²
**Zone :** {zone}
**Accès / Services :** À RÉDIGER PAR L'É.A.
**Caractéristiques particulières :** À RÉDIGER PAR L'É.A.

---

## 6. Meilleur usage (UMPP/AMU)

**Usage actuel :** {type_bien}
**Usage retenu (UMPP) :** {usage_retenu}
**Conformité au zonage :** {zone_conf_str}

**Conclusion AMU :** {umpp_conclusion}

*Les 4 critères (légalement permis, physiquement possible, financièrement faisable, maximalement productif) sont évalués dans l'artefact umpp_conclusion.json du dossier.*

---

## 7. Description du bâtiment

**Type :** {type_bien}
**Surface habitable :** {surface_str}
**Année de construction :** {annee_constr}
**Nombre de logements :** {nb_logements}
**État général :** À RÉDIGER PAR L'É.A.
**Composantes principales :** À RÉDIGER PAR L'É.A.

---

## 8. Approches de valeur — Présentation et justification

| Méthode | Statut |
|---|---|
| Approche comparative | Appliquée |
| Approche par le coût | {'Appliquée' if 'approche_cout' in valuation_values else 'Non appliquée — terrain ou coûts indisponibles'} |
| Approche par le revenu | {'Appliquée' if 'approche_revenu' in valuation_values else 'Non appliquée — bien non locatif ou données manquantes'} |

**Justification des méthodes rejetées :** À RÉDIGER PAR L'É.A.

---

## 9. Approche comparative — Grille d'ajustements

**{len(comparables)} comparable(s) retenu(s)** | Valeur indiquée : **{_fmt_cad(valeur_indiquee) if valeur_indiquee else '—'}**
{f"Fourchette : {_fmt_cad(fourchette.get('min', 0))} – {_fmt_cad(fourchette.get('max', 0))} (écart {fourchette.get('ecart_pct', 0):.1f}%)" if fourchette.get('min') else ""}

| # | Source | Prix de vente | Date | Score |
|---|---|---|---|---|
{comp_rows if comp_rows else "| — | Aucun comparable disponible | — | — | — |\n"}

**Grille d'ajustements par comparable :**

| Comparable | Caractéristique | Ajustement | Taux | Statut |
|---|---|---|---|---|
{grille_rows if grille_rows else "| — | Données insuffisantes | — | — | — |\n"}

*Lignes « a_valider » = taux par défaut MEFQ/APCIQ, à confirmer par É.A.*
*Lignes « donnees_manquantes » = champ absent dans les données comparables.*

---

## 10. Approche par le coût

{'*Non appliquée dans ce dossier — données de coûts insuffisantes.*' if 'approche_cout' not in valuation_values else f"Valeur indiquée : {_fmt_cad(valuation_values['approche_cout'])}"}

---

## 11. Approche par le revenu

{'*Non appliquée dans ce dossier — bien non locatif ou données de revenus manquantes.*' if 'approche_revenu' not in valuation_values else f"Valeur indiquée : {_fmt_cad(valuation_values['approche_revenu'])}"}

---

## 12. Réconciliation et valeur finale

| Méthode | Valeur indiquée |
|---|---|
{approach_rows if approach_rows else "| — | Aucune approche disponible |\n"}

**Valeur finale retenue : {val_str}**

Réconciliation (jugement pondéré) : À RÉDIGER PAR L'É.A.
La valeur comparative est la méthode prépondérante pour ce type de bien résidentiel.

---

## 13. Attestation

> **BROUILLON NON CERTIFIÉ — Signatures requises avant toute utilisation.**

Je/Nous soussigné(e)(s), évaluateur(s) agréé(s) membre(s) de l'OEAQ, atteste(ons) :

1. Les affirmations contenues dans ce rapport sont exactes et véridiques selon ma connaissance.
2. Les analyses, opinions et conclusions sont limitées aux hypothèses et conditions stipulées.
3. Je n'ai aucun intérêt personnel actuel ou futur dans le bien évalué.
4. L'indemnisation n'est aucunement liée à la valeur estimée.
5. L'évaluation a été effectuée en conformité avec les normes professionnelles OEAQ/CUSPAP.
6. J'ai inspecté personnellement le bien évalué (voir section 14).
7. Les règles de conduite et normes OEAQ ont été respectées.

**Valeur marchande au {date_ref} : {val_str}**
*(Montant en lettres : À RÉDIGER PAR L'É.A.)*

_[SIGNATURE É.A. — N° PERMIS OEAQ]_
_[DATE DE SIGNATURE]_
_[SCEAU PROFESSIONNEL]_
{blocking_section}{warnings_section}

---

## 14. Information sur l'inspection

**Date de visite :** À compléter par l'É.A.
**Étendue de l'inspection :** À compléter par l'É.A.
**Type d'inspection :** Intérieure et extérieure (à confirmer)
**Observations :** À RÉDIGER PAR L'É.A.

*⚠ Section 14 non complétée — Attestation conditionnelle à la saisie d'inspection.*

---

## 15. Annexes

- [ ] Plan du terrain (à joindre)
- [ ] Photos du bien (à joindre)
- [ ] Extrait du rôle municipal
- [ ] Certificat de localisation
- [ ] Données comparables (source_ids : {', '.join(c.get('source_id', '?') for c in comparables[:3]) if comparables else '—'})

---

## 16. Statut de conformité

**Statut :** {status}
{blocking_section}{warnings_section}
*Produit le {today} en mode dégradé (sans LLM). Révision É.A. obligatoire.*
"""


def generate_brouillon_rapport(
    case: dict,
    valuation_values: dict,
    status: str,
    blocking: list,
    warnings: list,
    format: str = "abrege",
) -> str:
    """Génère le brouillon de rapport : LLM si disponible, sinon template déterministe.

    Retourne toujours un str. Métadonnées LLM (modèle, coût) disponibles via _generate_rapport_llm().
    """
    prompt = _build_rapport_prompt_v2(case, format, valuation_values, status, blocking, warnings)
    llm_result = _generate_rapport_llm(prompt, format)
    if llm_result and llm_result.get("text"):
        disclaimer = (
            "> **BROUILLON NON CERTIFIÉ** — Produit par assistant IA.\n"
            "> Validation et signature d'un évaluateur agréé requises avant toute diffusion.\n\n---\n\n"
        )
        rapport = disclaimer + llm_result["text"]
    else:
        rapport = _generate_rapport_deterministic(case, valuation_values, status, blocking, warnings)

    # T3.1 — Validation post-génération des 16 éléments CUSPAP/NPP
    check = check_rapport_elements(rapport)
    rapport += build_rapport_check_section(check)
    return rapport


def write_artifact_payload(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    def _replace_tmp() -> None:
        last_error: PermissionError | None = None
        for _ in range(5):
            try:
                os.replace(tmp_path, path)
                last_error = None
                break
            except PermissionError as exc:
                last_error = exc
                time.sleep(0.02)
        if last_error is not None:
            raise last_error

    if path.suffix == ".md":
        raw = payload.get("_raw_md")
        text = raw if isinstance(raw, str) else render_markdown_payload(payload)
        try:
            with tmp_path.open("w", encoding="utf-8") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            _replace_tmp()
        finally:
            tmp_path.unlink(missing_ok=True)
        return
    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, indent=2))
            handle.flush()
            os.fsync(handle.fileno())
        _replace_tmp()
    finally:
        tmp_path.unlink(missing_ok=True)


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
