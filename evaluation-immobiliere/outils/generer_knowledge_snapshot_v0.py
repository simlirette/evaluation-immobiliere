#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

RUNTIME_DIR_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels")
QUALITY_DEFAULT = RUNTIME_DIR_DEFAULT / "quality_report.json"
MANIFEST_DEFAULT = RUNTIME_DIR_DEFAULT / "runtime_manifest.json"
OUT_JSON_DEFAULT = RUNTIME_DIR_DEFAULT / "knowledge_snapshot.json"
OUT_MD_DEFAULT = RUNTIME_DIR_DEFAULT / "KNOWLEDGE-SNAPSHOT-V0.md"


def load_json(path: Path) -> object:
    if not path.exists() or path.is_dir():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_dict(path: Path) -> dict:
    payload = load_json(path)
    return payload if isinstance(payload, dict) else {}


def load_list(path: Path) -> list:
    payload = load_json(path)
    return payload if isinstance(payload, list) else []


def resolve_case_dir(case: dict, runtime_dir: Path) -> Path:
    artifact_dir = Path(str(case.get("artifact_dir") or ""))
    if artifact_dir.is_absolute():
        return artifact_dir
    if artifact_dir.exists():
        return artifact_dir
    return runtime_dir / artifact_dir.name


def build_case_knowledge(case: dict, runtime_dir: Path) -> dict[str, object]:
    case_dir = resolve_case_dir(case, runtime_dir)
    fiche = load_dict(case_dir / "data-facts.fiche_bien.json")
    timeline = load_dict(case_dir / "data-facts.timeline_faits.json")
    data_sources = load_dict(case_dir / "data-facts.source_index.json")
    comp_sources = load_dict(case_dir / "comps-market.source_index.json")
    comparables = load_dict(case_dir / "comps-market.comparables_proposes.json")
    justifications = load_dict(case_dir / "comps-market.justifications_comparables.json")
    comparative = load_dict(case_dir / "valuation-draft.calculs_approche_comparative.json")
    cost = load_dict(case_dir / "valuation-draft.calculs_approche_cout.json")
    income = load_dict(case_dir / "valuation-draft.calculs_approche_revenu.json")
    hypotheses = load_dict(case_dir / "valuation-draft.hypotheses_explicites.json")
    qa_report = load_dict(case_dir / "compliance-qa.rapport_non_conformites.json")
    status = load_dict(case_dir / "compliance-qa.statut_sortie.json")
    ingestion = case.get("ingestion_pdf", {}) if isinstance(case.get("ingestion_pdf"), dict) else {}
    trace_path_value = str(ingestion.get("trace_path") or "")
    trace = load_list(Path(trace_path_value)) if trace_path_value else []

    return {
        "dossier_id": case.get("dossier_id"),
        "case_name": case.get("case_name"),
        "artifact_dir": case_dir.as_posix(),
        "mandate": {
            "dossier_id": case.get("dossier_id"),
            "date_reference": fiche.get("date_reference"),
        },
        "subject_property": {
            "surface": fiche.get("surface"),
            "timeline": timeline.get("events", []),
        },
        "sources": {
            "source_ids": sorted(
                {
                    str(source.get("source_id"))
                    for group in [data_sources.get("sources", []), comp_sources.get("sources", [])]
                    for source in group
                    if isinstance(source, dict) and source.get("source_id")
                }
            ),
            "field_trace_count": len(trace),
            "field_sourced_rate": nested(case, "sourcing", "sourced_field_rate"),
        },
        "market_evidence": {
            "comparables": comparables.get("comparables", []),
            "justifications": justifications.get("justifications", []),
            "average_score": nested(case, "comparables", "average_score"),
        },
        "valuation": {
            "approche_comparative": compact_trace(comparative),
            "approche_cout": compact_trace(cost),
            "approche_revenu": compact_trace(income),
            "hypotheses": hypotheses.get("hypotheses", []),
        },
        "compliance": {
            "status": case.get("status") or status.get("status"),
            "blocking_failures": case.get("blocking_failures", qa_report.get("blocking_failures", [])),
            "warnings": case.get("warnings", qa_report.get("warnings", [])),
            "contract_errors": case.get("contract_errors", []),
        },
        "redaction": {
            "brouillon_present": (case_dir / "redaction.brouillon_rapport.md").exists(),
            "annexe_sources_present": (case_dir / "redaction.annexe_sources.md").exists(),
        },
        "human_review": {
            "ingestion_review_flags": ingestion.get("review_flags", []),
            "missing_artifacts": nested(case, "artifacts", "missing") or [],
        },
    }


def nested(data: dict, *keys: str) -> object:
    current: object = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def compact_trace(payload: dict) -> dict[str, object]:
    return {
        "value": payload.get("value"),
        "method": payload.get("method"),
        "input_count": payload.get("input_count"),
        "trace_present": isinstance(payload.get("trace"), dict) and bool(payload.get("trace")),
    }


def build_knowledge_snapshot(runtime_dir: Path, quality_path: Path, manifest_path: Path) -> dict[str, object]:
    quality = load_dict(quality_path)
    manifest = load_dict(manifest_path)
    cases = [
        build_case_knowledge(case, runtime_dir)
        for case in quality.get("cases", [])
        if isinstance(case, dict)
    ]
    return {
        "schema_version": "knowledge_snapshot_v0",
        "runtime_dir": runtime_dir.as_posix(),
        "source_quality_report": quality_path.as_posix(),
        "source_manifest": manifest_path.as_posix(),
        "runtime_fingerprint_sha256": manifest.get("fingerprint_sha256", ""),
        "cases_count": len(cases),
        "cases": cases,
    }


def build_markdown(snapshot: dict[str, object]) -> str:
    lines = [
        "# Knowledge snapshot v0",
        "",
        f"- Runtime: `{snapshot.get('runtime_dir', '-')}`",
        f"- Fingerprint runtime: `{snapshot.get('runtime_fingerprint_sha256', '')}`",
        f"- Dossiers: **{snapshot.get('cases_count', 0)}**",
        "",
        "| Dossier | Statut | Sources | Comparables | Score moyen | Traces calcul | Redaction |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    cases = snapshot.get("cases", [])
    if isinstance(cases, list):
        for case in cases:
            if not isinstance(case, dict):
                continue
            sources = case.get("sources", {}) if isinstance(case.get("sources"), dict) else {}
            market = case.get("market_evidence", {}) if isinstance(case.get("market_evidence"), dict) else {}
            valuation = case.get("valuation", {}) if isinstance(case.get("valuation"), dict) else {}
            redaction = case.get("redaction", {}) if isinstance(case.get("redaction"), dict) else {}
            lines.append(
                "| {dossier} | {status} | {sources} | {comparables} | {score} | {traces} | {redaction} |".format(
                    dossier=case.get("dossier_id", "-"),
                    status=nested(case, "compliance", "status") or "-",
                    sources=len(sources.get("source_ids", [])),
                    comparables=len(market.get("comparables", [])),
                    score=format_optional_float(market.get("average_score")),
                    traces=format_trace_count(valuation),
                    redaction="oui" if redaction.get("brouillon_present") else "non",
                )
            )
    return "\n".join(lines).rstrip() + "\n"


def format_optional_float(value: object) -> str:
    if value is None:
        return "n/d"
    return f"{float(value):.4f}"


def format_trace_count(valuation: dict) -> str:
    count = sum(
        1
        for key in ["approche_comparative", "approche_cout", "approche_revenu"]
        if isinstance(valuation.get(key), dict) and valuation[key].get("trace_present")
    )
    return f"{count}/3"


def write_snapshot(snapshot: dict[str, object], json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(build_markdown(snapshot), encoding="utf-8")


def generate_snapshot(runtime_dir: Path, quality_path: Path, manifest_path: Path, json_out: Path, markdown_out: Path) -> dict[str, object]:
    snapshot = build_knowledge_snapshot(runtime_dir, quality_path, manifest_path)
    write_snapshot(snapshot, json_out, markdown_out)
    return snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description="Genere un snapshot knowledge depuis les artefacts runtime.")
    parser.add_argument("--runtime-dir", type=Path, default=RUNTIME_DIR_DEFAULT)
    parser.add_argument("--quality-report", type=Path, default=QUALITY_DEFAULT)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_DEFAULT)
    parser.add_argument("--json-out", type=Path, default=OUT_JSON_DEFAULT)
    parser.add_argument("--markdown-out", type=Path, default=OUT_MD_DEFAULT)
    args = parser.parse_args()

    snapshot = generate_snapshot(args.runtime_dir, args.quality_report, args.manifest, args.json_out, args.markdown_out)
    print(f"Knowledge JSON: {args.json_out}")
    print(f"Knowledge Markdown: {args.markdown_out}")
    print(f"Dossiers: {snapshot['cases_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
