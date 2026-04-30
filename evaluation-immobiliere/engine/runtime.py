from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import json
import os
import re
import time
import ast

from engine.audit import append_audit_log
from engine.tools import search_comparables, validate_schema
from engine.valuation import calculate_valuation_trace


@dataclass
class RuntimeStep:
    name: str
    reads: list[str]
    writes: list[str]


class PipelineValidationError(ValueError):
    pass


REQUIRED_FIELDS_BY_ARTIFACT = {
    "default": ["dossier_id", "step", "artifact", "source_fixture"],
    "statut_sortie.json": ["dossier_id", "step", "artifact", "source_fixture", "status", "blocking_failures", "warnings"],
    "comparables_proposes.json": ["dossier_id", "step", "artifact", "source_fixture", "comparables"],
    "calculs_approche_comparative.json": ["dossier_id", "step", "artifact", "source_fixture", "method", "value", "input_count", "trace"],
    "calculs_approche_cout.json": ["dossier_id", "step", "artifact", "source_fixture", "method", "value", "input_count", "trace"],
    "calculs_approche_revenu.json": ["dossier_id", "step", "artifact", "source_fixture", "method", "value", "input_count", "trace"],
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
    current_reads: list[str] = []
    current_writes: list[str] = []
    mode: str | None = None

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        if re.match(r"^\s*- step:\s*\d+", line):
            if current_name:
                steps.append(RuntimeStep(current_name, current_reads, current_writes))
            current_name = None
            current_reads = []
            current_writes = []
            mode = None
            continue

        if stripped.startswith("agent_config:"):
            agent_file = stripped.split(":", 1)[1].strip()
            current_name = _name_from_agent_config(agent_file)
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
        steps.append(RuntimeStep(current_name, current_reads, current_writes))

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


DEFAULT_STEPS = [
    RuntimeStep("data-facts", ["dossier_input", "documents_sources"], ["fiche_bien.json", "timeline_faits.json", "source_index.json"]),
    RuntimeStep("comps-market", ["fiche_bien.json", "source_index.json", "market_data_sources"], ["comparables_proposes.json", "justifications_comparables.json", "source_index.json"]),
    RuntimeStep("valuation-draft", ["comparables_proposes.json", "couts_reference", "revenus_depenses", "source_index.json"], ["calculs_approche_comparative.json", "calculs_approche_cout.json", "calculs_approche_revenu.json", "hypotheses_explicites.json", "brouillon_valeur.md"]),
    RuntimeStep("compliance-qa", ["calculs_approche_comparative.json", "calculs_approche_cout.json", "calculs_approche_revenu.json", "hypotheses_explicites.json", "source_index.json"], ["rapport_non_conformites.json", "statut_sortie.json", "recommandations_corrections.md"]),
    RuntimeStep("redaction", ["statut_sortie.json", "recommandations_corrections.md", "source_index.json"], ["brouillon_rapport.md", "annexe_sources.md"]),
]


class RuntimeEngine:
    def __init__(self, steps: list[RuntimeStep] | None = None, strict_mode: bool = True) -> None:
        self.steps = steps or DEFAULT_STEPS
        self.strict_mode = strict_mode
        validate_pipeline_steps(self.steps)

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
            payload["sections"] = {
                "dossier": case.get("dossier_id"),
                "statut": status,
                "resume": "Brouillon genere par le runtime v0 a partir des artefacts valides.",
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
            self._record_event(events, audit_log_path, {"event": "step_start", "step": step.name, "dossier_id": dossier_id})

            for artifact in step.writes:
                artifact_path = case_dir / f"{case_key}.{step.name}.{artifact}" if not case_subdir else case_dir / f"{step.name}.{artifact}"
                artifact_path.parent.mkdir(parents=True, exist_ok=True)

                payload = self._artifact_payload(step.name, artifact, case, status, blocking, warnings, valuation_values)
                payload["source_fixture"] = source_fixture
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


def write_artifact_payload(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".md":
        path.write_text(render_markdown_payload(payload), encoding="utf-8")
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
