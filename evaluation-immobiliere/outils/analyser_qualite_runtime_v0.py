#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from statistics import fmean
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.runtime import DEFAULT_STEPS, RuntimeStep, load_steps_from_pipeline_yaml, safe_path_id
from outils.valider_contrats_runtime_v0 import validate_runtime_contracts

RUNTIME_DIR_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels")
SUMMARY_DEFAULT = RUNTIME_DIR_DEFAULT / "runtime_summary.json"
PIPELINE_DEFAULT = Path("evaluation-immobiliere/integration/PIPELINE-RUNTIME-ASTON-V0.yaml")
INGESTION_DIR_DEFAULT = RUNTIME_DIR_DEFAULT / "ingestion_v0"
OUT_JSON_DEFAULT = RUNTIME_DIR_DEFAULT / "quality_report.json"
OUT_MD_DEFAULT = RUNTIME_DIR_DEFAULT / "RAPPORT-QUALITE-RUNTIME-V0.md"
INGESTION_MANIFEST_NAME = "MANIFESTE-INGESTION-PDF-V0.json"
NORMALIZED_NAME = "dossier_normalise.json"
TRACE_NAME = "trace_champs.json"
STATUS_ORDER = ["PRET_REVISION_FINALE", "BROUILLON", "A_REVOIR", "UNKNOWN"]
CALCULATION_ARTIFACTS = [
    "valuation-draft.calculs_approche_comparative.json",
    "valuation-draft.calculs_approche_cout.json",
    "valuation-draft.calculs_approche_revenu.json",
]


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def load_summary(path: Path) -> list[dict]:
    payload = load_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"Sommaire runtime invalide: {path}")
    return [item for item in payload if isinstance(item, dict)]


def expected_artifacts_from_steps(steps: Iterable[RuntimeStep]) -> list[str]:
    return [f"{step.name}.{artifact}" for step in steps for artifact in step.writes]


def load_expected_artifacts(pipeline_path: Path | None = PIPELINE_DEFAULT) -> list[str]:
    if pipeline_path and pipeline_path.exists():
        return expected_artifacts_from_steps(load_steps_from_pipeline_yaml(pipeline_path))
    return expected_artifacts_from_steps(DEFAULT_STEPS)


def resolve_case_dir(case: dict, runtime_dir: Path) -> Path:
    raw_artifact_dir = str(case.get("artifact_dir") or "").strip()
    if raw_artifact_dir:
        artifact_dir = Path(raw_artifact_dir)
        if artifact_dir.is_absolute():
            return artifact_dir
        if artifact_dir.exists():
            return artifact_dir
        if artifact_dir.name:
            return runtime_dir / artifact_dir.name
    return runtime_dir / safe_path_id(str(case.get("dossier_id") or "unknown"))


def artifact_inventory(case_dir: Path, expected_artifacts: list[str]) -> dict[str, object]:
    produced = [artifact for artifact in expected_artifacts if (case_dir / artifact).exists()]
    missing = [artifact for artifact in expected_artifacts if artifact not in produced]
    return {
        "expected_count": len(expected_artifacts),
        "produced_count": len(produced),
        "missing_count": len(missing),
        "produced": produced,
        "missing": missing,
    }


def group_contract_errors(contract_report: dict) -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for failure in contract_report.get("failures", []):
        if not isinstance(failure, dict):
            continue
        failure_path = Path(str(failure.get("path", "")))
        case_name = failure_path.parent.name
        if not case_name:
            continue
        grouped.setdefault(case_name, []).append(
            {
                "artifact": failure.get("artifact", ""),
                "path": failure.get("path", ""),
                "failures": list(failure.get("failures", [])),
            }
        )
    return grouped


def comparable_metrics(case_dir: Path) -> dict[str, object]:
    path = case_dir / "comps-market.comparables_proposes.json"
    payload = read_json_dict(path)
    comparables = payload.get("comparables", []) if payload else []
    if not isinstance(comparables, list):
        comparables = []

    scores: list[float] = []
    for comparable in comparables:
        if not isinstance(comparable, dict):
            continue
        score = comparable.get("score")
        try:
            scores.append(float(score))
        except (TypeError, ValueError):
            continue

    return {
        "count": len(comparables),
        "scored_count": len(scores),
        "average_score": round(fmean(scores), 4) if scores else None,
    }


def calculation_trace_metrics(case_dir: Path) -> dict[str, object]:
    present: list[str] = []
    missing: list[str] = []
    for artifact in CALCULATION_ARTIFACTS:
        payload = read_json_dict(case_dir / artifact)
        if payload and isinstance(payload.get("trace"), dict) and payload.get("trace"):
            present.append(artifact)
        else:
            missing.append(artifact)
    return {
        "present": len(missing) == 0,
        "present_count": len(present),
        "expected_count": len(CALCULATION_ARTIFACTS),
        "missing": missing,
    }


def read_json_dict(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = load_json(path)
    return payload if isinstance(payload, dict) else {}


def read_json_list(path: Path) -> list:
    if not path.exists():
        return []
    payload = load_json(path)
    return payload if isinstance(payload, list) else []


def load_ingestion_index(ingestion_dir: Path | None) -> dict[str, dict[str, object]]:
    if not ingestion_dir or not ingestion_dir.exists():
        return {}

    index: dict[str, dict[str, object]] = {}
    manifest = read_json_dict(ingestion_dir / INGESTION_MANIFEST_NAME)
    entries = manifest.get("entries", [])
    if isinstance(entries, list):
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            dossier_id = str(entry.get("dossier_id") or "").strip()
            if not dossier_id:
                continue
            index[dossier_id] = {
                "available": True,
                "review_flags": sorted_list(entry.get("review_flags", [])),
                "missing_fields": sorted_list(entry.get("missing_fields", [])),
                "text_stats": entry.get("text_stats", {}) if isinstance(entry.get("text_stats", {}), dict) else {},
                "trace_path": "",
            }

    for dossier_dir in sorted(path for path in ingestion_dir.iterdir() if path.is_dir()):
        dossier = read_json_dict(dossier_dir / NORMALIZED_NAME)
        if not dossier:
            continue
        dossier_id = str(dossier.get("dossier_id") or dossier_dir.name)
        quality = dossier.get("quality", {}) if isinstance(dossier.get("quality", {}), dict) else {}
        source_documents = dossier.get("source_documents", [])
        text_stats = {}
        if isinstance(source_documents, list) and source_documents:
            first_source = source_documents[0]
            if isinstance(first_source, dict) and isinstance(first_source.get("text_stats"), dict):
                text_stats = first_source["text_stats"]
        trace_path = dossier_dir / TRACE_NAME
        entry = {
            "available": True,
            "review_flags": sorted_list(quality.get("review_flags", [])),
            "missing_fields": sorted_list(quality.get("missing_fields", [])),
            "text_stats": text_stats,
            "trace_path": trace_path.as_posix() if trace_path.exists() else "",
            "sourcing": sourcing_metrics_from_trace(trace_path),
        }
        previous = index.get(dossier_id, {})
        merged = {**previous, **entry}
        if not merged.get("review_flags"):
            merged["review_flags"] = previous.get("review_flags", [])
        if not merged.get("missing_fields"):
            merged["missing_fields"] = previous.get("missing_fields", [])
        index[dossier_id] = merged

    return index


def sourcing_metrics_from_trace(trace_path: Path) -> dict[str, object]:
    trace = read_json_list(trace_path)
    total = len(trace)
    sourced = 0
    review_counts = Counter()
    value_counts = Counter()
    for item in trace:
        if not isinstance(item, dict):
            continue
        source_ids = item.get("source_ids", [])
        if isinstance(source_ids, list) and any(str(source_id).strip() for source_id in source_ids):
            sourced += 1
        review_counts[str(item.get("review_status") or "UNKNOWN")] += 1
        value_counts[str(item.get("value_status") or "UNKNOWN")] += 1
    return {
        "trace_available": trace_path.exists(),
        "total_fields": total,
        "sourced_fields": sourced,
        "sourced_field_rate": round(sourced / total, 4) if total else None,
        "review_status_counts": dict(review_counts),
        "value_status_counts": dict(value_counts),
    }


def empty_ingestion_metrics() -> dict[str, object]:
    return {
        "available": False,
        "review_flags": [],
        "missing_fields": [],
        "text_stats": {},
        "trace_path": "",
        "sourcing": {
            "trace_available": False,
            "total_fields": 0,
            "sourced_fields": 0,
            "sourced_field_rate": None,
            "review_status_counts": {},
            "value_status_counts": {},
        },
    }


def build_quality_report(
    *,
    runtime_dir: Path,
    summary_path: Path,
    pipeline_path: Path | None = PIPELINE_DEFAULT,
    ingestion_dir: Path | None = INGESTION_DIR_DEFAULT,
    expected_artifacts: list[str] | None = None,
) -> dict[str, object]:
    summary = load_summary(summary_path)
    expected = expected_artifacts or load_expected_artifacts(pipeline_path)
    contract_report = validate_runtime_contracts(runtime_dir)
    contract_errors_by_case = group_contract_errors(contract_report)
    ingestion_index = load_ingestion_index(ingestion_dir)

    cases: list[dict[str, object]] = []
    for case in summary:
        dossier_id = str(case.get("dossier_id") or "unknown")
        case_dir = resolve_case_dir(case, runtime_dir)
        case_name = case_dir.name
        ingestion = ingestion_index.get(dossier_id, empty_ingestion_metrics())
        sourcing = ingestion.get("sourcing", empty_ingestion_metrics()["sourcing"])
        contract_errors = contract_errors_by_case.get(case_name, [])
        cases.append(
            {
                "case_name": case_name,
                "dossier_id": dossier_id,
                "status": case.get("status", "UNKNOWN"),
                "blocking_failures": list(case.get("blocking_failures", [])),
                "warnings": list(case.get("warnings", [])),
                "artifact_dir": case_dir.as_posix(),
                "artifacts": artifact_inventory(case_dir, expected),
                "contract_errors": contract_errors,
                "sourcing": sourcing,
                "comparables": comparable_metrics(case_dir),
                "calculation_traces": calculation_trace_metrics(case_dir),
                "ingestion_pdf": {
                    "available": bool(ingestion.get("available")),
                    "review_flags": list(ingestion.get("review_flags", [])),
                    "missing_fields": list(ingestion.get("missing_fields", [])),
                    "text_stats": ingestion.get("text_stats", {}),
                    "trace_path": ingestion.get("trace_path", ""),
                },
            }
        )

    return build_report_envelope(
        runtime_dir=runtime_dir,
        summary_path=summary_path,
        ingestion_dir=ingestion_dir,
        contract_report=contract_report,
        cases=cases,
    )


def build_report_envelope(
    *,
    runtime_dir: Path,
    summary_path: Path,
    ingestion_dir: Path | None,
    contract_report: dict,
    cases: list[dict[str, object]],
) -> dict[str, object]:
    status_counts = Counter(str(case.get("status") or "UNKNOWN") for case in cases)
    sourced_rates = [
        float(sourcing.get("sourced_field_rate"))
        for case in cases
        for sourcing in [case.get("sourcing", {})]
        if isinstance(sourcing, dict) and sourcing.get("sourced_field_rate") is not None
    ]
    comparable_scores = [
        float(metrics.get("average_score"))
        for case in cases
        for metrics in [case.get("comparables", {})]
        if isinstance(metrics, dict) and metrics.get("average_score") is not None
    ]
    total_expected_artifacts = sum(int(case["artifacts"]["expected_count"]) for case in cases)
    total_produced_artifacts = sum(int(case["artifacts"]["produced_count"]) for case in cases)
    total_missing_artifacts = sum(int(case["artifacts"]["missing_count"]) for case in cases)
    total_contract_errors = sum(
        len(error.get("failures", []))
        for case in cases
        for error in case.get("contract_errors", [])
        if isinstance(error, dict)
    )

    return {
        "schema_version": "runtime_quality_report_v0",
        "runtime_dir": runtime_dir.as_posix(),
        "summary_path": summary_path.as_posix(),
        "ingestion_dir": ingestion_dir.as_posix() if ingestion_dir else "",
        "cases_count": len(cases),
        "status_counts": dict(status_counts),
        "totals": {
            "blocking_failures": sum(len(case.get("blocking_failures", [])) for case in cases),
            "warnings": sum(len(case.get("warnings", [])) for case in cases),
            "contract_errors": total_contract_errors,
            "expected_artifacts": total_expected_artifacts,
            "produced_artifacts": total_produced_artifacts,
            "missing_artifacts": total_missing_artifacts,
            "cases_with_all_calculation_traces": sum(
                1 for case in cases if isinstance(case.get("calculation_traces"), dict) and case["calculation_traces"].get("present")
            ),
            "cases_with_ingestion_pdf": sum(
                1 for case in cases if isinstance(case.get("ingestion_pdf"), dict) and case["ingestion_pdf"].get("available")
            ),
        },
        "averages": {
            "sourced_field_rate": round(fmean(sourced_rates), 4) if sourced_rates else None,
            "comparable_score": round(fmean(comparable_scores), 4) if comparable_scores else None,
        },
        "contract_report": {
            "files_checked": contract_report.get("files_checked", 0),
            "files_invalid": contract_report.get("files_invalid", 0),
            "ok": bool(contract_report.get("ok")),
        },
        "cases": cases,
    }


def build_markdown(report: dict[str, object]) -> str:
    totals = report.get("totals", {}) if isinstance(report.get("totals"), dict) else {}
    averages = report.get("averages", {}) if isinstance(report.get("averages"), dict) else {}
    status_counts = report.get("status_counts", {}) if isinstance(report.get("status_counts"), dict) else {}
    cases = report.get("cases", []) if isinstance(report.get("cases"), list) else []

    lines = [
        "# Rapport qualite runtime v0",
        "",
        "## Synthese",
        "",
        f"- Dossiers analyses: **{report.get('cases_count', 0)}**",
        f"- Blocages: **{totals.get('blocking_failures', 0)}**",
        f"- Warnings: **{totals.get('warnings', 0)}**",
        f"- Erreurs de contrat: **{totals.get('contract_errors', 0)}**",
        f"- Artefacts produits: **{totals.get('produced_artifacts', 0)}/{totals.get('expected_artifacts', 0)}**",
        f"- Artefacts manquants: **{totals.get('missing_artifacts', 0)}**",
        f"- Taux moyen champs sources: **{format_rate(averages.get('sourced_field_rate'))}**",
        f"- Score moyen comparables: **{format_float(averages.get('comparable_score'))}**",
        f"- Dossiers avec traces calcul completes: **{totals.get('cases_with_all_calculation_traces', 0)}**",
        f"- Dossiers avec ingestion PDF: **{totals.get('cases_with_ingestion_pdf', 0)}**",
        "",
        "## Distribution statuts",
        "",
    ]
    for status in ordered_statuses(status_counts):
        lines.append(f"- {status}: {status_counts.get(status, 0)}")

    lines.extend(
        [
            "",
            "## Dossiers",
            "",
            "| Dossier | Statut | Blocages | Warnings | Artefacts | Contrats | Champs sources | Score comps | Traces calcul | Flags PDF |",
            "|---|---|---:|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for case in cases:
        if not isinstance(case, dict):
            continue
        artifacts = case.get("artifacts", {}) if isinstance(case.get("artifacts"), dict) else {}
        sourcing = case.get("sourcing", {}) if isinstance(case.get("sourcing"), dict) else {}
        comparables = case.get("comparables", {}) if isinstance(case.get("comparables"), dict) else {}
        traces = case.get("calculation_traces", {}) if isinstance(case.get("calculation_traces"), dict) else {}
        ingestion = case.get("ingestion_pdf", {}) if isinstance(case.get("ingestion_pdf"), dict) else {}
        flags = ingestion.get("review_flags", [])
        lines.append(
            "| {dossier} | {status} | {blocking} | {warnings} | {produced}/{expected} | {contracts} | {sourcing} | {score} | {traces} | {flags} |".format(
                dossier=case.get("dossier_id", "-"),
                status=case.get("status", "UNKNOWN"),
                blocking=len(case.get("blocking_failures", [])),
                warnings=len(case.get("warnings", [])),
                produced=artifacts.get("produced_count", 0),
                expected=artifacts.get("expected_count", 0),
                contracts=count_contract_failures(case),
                sourcing=format_rate(sourcing.get("sourced_field_rate")),
                score=format_float(comparables.get("average_score")),
                traces="oui" if traces.get("present") else "non",
                flags=format_list(flags),
            )
        )

    lines.extend(["", "## Details", ""])
    for case in cases:
        if not isinstance(case, dict):
            continue
        lines.append(f"### {case.get('dossier_id', '-')}")
        append_case_details(lines, case)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def append_case_details(lines: list[str], case: dict[str, object]) -> None:
    artifacts = case.get("artifacts", {}) if isinstance(case.get("artifacts"), dict) else {}
    missing_artifacts = artifacts.get("missing", [])
    contract_errors = case.get("contract_errors", [])
    blocking = case.get("blocking_failures", [])
    warnings = case.get("warnings", [])
    ingestion = case.get("ingestion_pdf", {}) if isinstance(case.get("ingestion_pdf"), dict) else {}

    lines.append(f"- Repertoire artefacts: `{case.get('artifact_dir', '-')}`")
    if blocking:
        lines.append(f"- Blocages: {format_list(blocking)}")
    if warnings:
        lines.append(f"- Warnings: {format_list(warnings)}")
    if missing_artifacts:
        lines.append(f"- Artefacts manquants: {format_list(missing_artifacts)}")
    if contract_errors:
        for error in contract_errors:
            if not isinstance(error, dict):
                continue
            lines.append(f"- Contrat `{error.get('artifact', '-')}`: {format_list(error.get('failures', []))}")
    if ingestion.get("available"):
        lines.append(f"- Flags ingestion PDF: {format_list(ingestion.get('review_flags', []))}")
        missing_fields = ingestion.get("missing_fields", [])
        if missing_fields:
            lines.append(f"- Champs ingestion manquants: {format_list(missing_fields)}")


def sorted_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted({str(item) for item in value if str(item)})


def ordered_statuses(status_counts: dict[str, int]) -> list[str]:
    ordered = [status for status in STATUS_ORDER if status in status_counts]
    ordered.extend(sorted(status for status in status_counts if status not in STATUS_ORDER))
    return ordered


def count_contract_failures(case: dict[str, object]) -> int:
    return sum(
        len(error.get("failures", []))
        for error in case.get("contract_errors", [])
        if isinstance(error, dict)
    )


def format_rate(value: object) -> str:
    if value is None:
        return "n/d"
    return f"{float(value) * 100:.1f}%"


def format_float(value: object) -> str:
    if value is None:
        return "n/d"
    return f"{float(value):.4f}"


def format_list(value: object) -> str:
    if not isinstance(value, list) or not value:
        return "-"
    return "; ".join(str(item) for item in value)


def write_quality_report(report: dict[str, object], json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(build_markdown(report), encoding="utf-8")


def generate_quality_report(
    *,
    runtime_dir: Path = RUNTIME_DIR_DEFAULT,
    summary_path: Path = SUMMARY_DEFAULT,
    pipeline_path: Path | None = PIPELINE_DEFAULT,
    ingestion_dir: Path | None = INGESTION_DIR_DEFAULT,
    json_out: Path = OUT_JSON_DEFAULT,
    markdown_out: Path = OUT_MD_DEFAULT,
) -> dict[str, object]:
    report = build_quality_report(
        runtime_dir=runtime_dir,
        summary_path=summary_path,
        pipeline_path=pipeline_path,
        ingestion_dir=ingestion_dir,
    )
    write_quality_report(report, json_out, markdown_out)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyse les sorties runtime et genere un rapport qualite global.")
    parser.add_argument("--runtime-dir", type=Path, default=RUNTIME_DIR_DEFAULT)
    parser.add_argument("--summary", type=Path, default=SUMMARY_DEFAULT)
    parser.add_argument("--pipeline", type=Path, default=PIPELINE_DEFAULT)
    parser.add_argument("--ingestion-dir", type=Path, default=INGESTION_DIR_DEFAULT)
    parser.add_argument("--json-out", type=Path, default=OUT_JSON_DEFAULT)
    parser.add_argument("--markdown-out", type=Path, default=OUT_MD_DEFAULT)
    args = parser.parse_args()

    report = generate_quality_report(
        runtime_dir=args.runtime_dir,
        summary_path=args.summary,
        pipeline_path=args.pipeline,
        ingestion_dir=args.ingestion_dir,
        json_out=args.json_out,
        markdown_out=args.markdown_out,
    )
    print(f"Rapport qualite JSON: {args.json_out}")
    print(f"Rapport qualite Markdown: {args.markdown_out}")
    print(f"Dossiers analyses: {report['cases_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
