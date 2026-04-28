from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re

from engine.audit import append_audit_log
from engine.tools import run_calculation, search_comparables, validate_schema


@dataclass
class RuntimeStep:
    name: str
    reads: list[str]
    writes: list[str]


REQUIRED_FIELDS_BY_ARTIFACT = {
    "default": ["dossier_id", "step", "artifact", "source_fixture"],
    "statut_sortie.json": ["dossier_id", "step", "artifact", "source_fixture", "status", "blocking_failures", "warnings"],
    "comparables_proposes.json": ["dossier_id", "step", "artifact", "source_fixture", "comparables"],
    "calculs_approche_comparative.json": ["dossier_id", "step", "artifact", "source_fixture", "method", "value", "input_count"],
    "calculs_approche_cout.json": ["dossier_id", "step", "artifact", "source_fixture", "method", "value", "input_count"],
    "calculs_approche_revenu.json": ["dossier_id", "step", "artifact", "source_fixture", "method", "value", "input_count"],
}


def _name_from_agent_config(value: str) -> str:
    value = value.strip()
    value = value.replace("AGENTCONFIG-", "").replace("-V0.yaml", "")
    return value.lower().replace("-", "-")


def load_steps_from_pipeline_yaml(pipeline_path: Path) -> list[RuntimeStep]:
    """Parse le fichier pipeline YAML v0 sans dépendance externe."""
    lines = pipeline_path.read_text(encoding="utf-8").splitlines()
    steps: list[RuntimeStep] = []

    current_name: str | None = None
    current_reads: list[str] = []
    current_writes: list[str] = []
    mode: str | None = None

    for raw in lines:
        line = raw.rstrip()

        if re.match(r"^\s*- step:\s*\d+", line):
            if current_name:
                steps.append(RuntimeStep(current_name, current_reads, current_writes))
            current_name = None
            current_reads = []
            current_writes = []
            mode = None
            continue

        stripped = line.strip()

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

    return steps


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

    def _compute_qa(self, case: dict) -> tuple[str, list[str], list[str]]:
        blocking: list[str] = []
        warnings: list[str] = []

        for c in case.get("comparables", []):
            if "source_id" not in c:
                blocking.append("B002: comparable sans source_id")

        for a in case.get("ajustements", []):
            if "source_id" not in a:
                blocking.append("B002: ajustement sans source_id")
            if a.get("montant", 0) >= 25000 and not a.get("validation_humaine", False):
                blocking.append("B005: ajustement sensible sans validation_humaine")

        if self.strict_mode and case.get("comparables") and not all("source_id" in c for c in case.get("comparables", [])):
            blocking.append("STRICT: sortie refusée, comparable sans source")

        subject_unit = case.get("surface", {}).get("unit")
        comp_units = {c.get("surface", {}).get("unit") for c in case.get("comparables", []) if isinstance(c.get("surface"), dict)}
        if subject_unit and comp_units and any(u and u != subject_unit for u in comp_units):
            blocking.append("B004: unité incohérente sujet/comparables")

        if case.get("confidence", 1) < 0.60:
            warnings.append("W001: confiance faible")

        status = "A_REVOIR" if blocking else ("BROUILLON" if warnings else "PRET_REVISION_FINALE")
        return status, blocking, warnings

    def _artifact_payload(self, step: str, artifact: str, case: dict, status: str, blocking: list[str], warnings: list[str]) -> dict:
        payload = {
            "dossier_id": case.get("dossier_id"),
            "step": step,
            "artifact": artifact,
        }

        if step == "comps-market" and artifact == "comparables_proposes.json":
            comparables = [c.__dict__ for c in search_comparables(case.get("comparables", []), max_items=5)]
            payload["comparables"] = comparables

        if step == "valuation-draft" and artifact in {
            "calculs_approche_comparative.json",
            "calculs_approche_cout.json",
            "calculs_approche_revenu.json",
        }:
            prices = [float(c.get("prix_vente", 0)) for c in case.get("comparables", []) if c.get("prix_vente")]
            method = "mean" if artifact != "calculs_approche_revenu.json" else "median"
            payload["method"] = method
            payload["value"] = run_calculation(prices, method=method)
            payload["input_count"] = len(prices)

        if step == "compliance-qa" and artifact == "statut_sortie.json":
            payload.update({"status": status, "blocking_failures": blocking, "warnings": warnings})

        return payload

    def run_case(self, case_path: Path, out_dir: Path) -> dict:
        case = json.loads(case_path.read_text(encoding="utf-8"))
        events: list[dict] = []
        audit_log_path = out_dir / f"{case_path.stem}.audit.jsonl"

        status, blocking, warnings = self._compute_qa(case)

        for step in self.steps:
            events.append({"event": "step_start", "step": step.name, "dossier_id": case.get("dossier_id", "unknown")})
            append_audit_log(audit_log_path, {"event": "step_start", "step": step.name, "dossier_id": case.get("dossier_id", "unknown")})

            for artifact in step.writes:
                artifact_path = out_dir / f"{case_path.stem}.{step.name}.{artifact}"
                artifact_path.parent.mkdir(parents=True, exist_ok=True)

                payload = self._artifact_payload(step.name, artifact, case, status, blocking, warnings)
                payload["source_fixture"] = case_path.name

                required = REQUIRED_FIELDS_BY_ARTIFACT.get(artifact, REQUIRED_FIELDS_BY_ARTIFACT["default"])
                ok, missing = validate_schema(payload, required)
                if not ok:
                    schema_block = f"SCHEMA: champs manquants {missing}"
                    blocking.append(schema_block)
                    status = "A_REVOIR"
                    append_audit_log(audit_log_path, {"event": "schema_invalid", "step": step.name, "artifact": artifact, "missing": missing})
                    if step.name == "compliance-qa":
                        payload.setdefault("blocking_failures", []).append(schema_block)

                artifact_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                append_audit_log(audit_log_path, {"event": "artifact_written", "step": step.name, "artifact": artifact, "path": str(artifact_path)})

            events.append({"event": "step_done", "step": step.name, "dossier_id": case.get("dossier_id", "unknown")})
            append_audit_log(audit_log_path, {"event": "step_done", "step": step.name, "dossier_id": case.get("dossier_id", "unknown")})

            if step.name == "compliance-qa" and status == "A_REVOIR":
                blocking_event = {"event": "blocking_detected", "step": step.name, "dossier_id": case.get("dossier_id", "unknown"), "blocking_count": len(blocking)}
                events.append(blocking_event)
                append_audit_log(audit_log_path, blocking_event)
                break

        return {
            "dossier_id": case.get("dossier_id", "unknown"),
            "status": status,
            "blocking_failures": blocking,
            "warnings": warnings,
            "events": events,
            "audit_log": str(audit_log_path),
        }
