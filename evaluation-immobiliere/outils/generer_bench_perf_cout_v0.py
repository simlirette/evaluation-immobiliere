#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from math import ceil, floor
from pathlib import Path
from statistics import fmean

RUNTIME_DIR_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels")
SUMMARY_DEFAULT = RUNTIME_DIR_DEFAULT / "runtime_summary.json"
QUALITY_DEFAULT = RUNTIME_DIR_DEFAULT / "quality_report.json"
MANIFEST_DEFAULT = RUNTIME_DIR_DEFAULT / "runtime_manifest.json"
DELTA_DEFAULT = RUNTIME_DIR_DEFAULT / "runtime_delta_report.json"
OUT_JSON_DEFAULT = RUNTIME_DIR_DEFAULT / "perf_cost_phase_g_report.json"
ATELIER_DIR_DEFAULT = Path("evaluation-immobiliere/atelier")
BENCH_MD_DEFAULT = ATELIER_DIR_DEFAULT / "BENCH-PERF-COUT-V1.md"
SLO_MD_DEFAULT = ATELIER_DIR_DEFAULT / "SLO-SLA-V1.md"
PLAN_MD_DEFAULT = ATELIER_DIR_DEFAULT / "PLAN-OPTIMISATION-V1.md"

STATUS_REVIEW_REQUIRED = {"BROUILLON", "A_REVOIR"}
WALL_CLOCK_TARGET_P95_SECONDS = 900.0
ARTIFACT_COMPLETION_TARGET = 0.98
SOURCE_COVERAGE_TARGET = 0.95
CONTRACT_ERROR_TARGET = 0
REGRESSION_TARGET = 0


def load_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def int_value(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def float_value(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def rate(numerator: int | float, denominator: int | float) -> float | None:
    if not denominator:
        return None
    return round(float(numerator) / float(denominator), 4)


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 4)
    position = (len(ordered) - 1) * pct
    low = floor(position)
    high = ceil(position)
    if low == high:
        return round(ordered[int(position)], 4)
    lower = ordered[low] * (high - position)
    upper = ordered[high] * (position - low)
    return round(lower + upper, 4)


def list_dicts(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def dict_value(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def quality_cases_by_id(quality_report: object) -> dict[str, dict[str, object]]:
    quality = dict_value(quality_report)
    cases = list_dicts(quality.get("cases", []))
    return {str(case.get("dossier_id") or ""): case for case in cases if case.get("dossier_id")}


def count_contract_failures(case_quality: dict[str, object]) -> int:
    count = 0
    for error in list_dicts(case_quality.get("contract_errors", [])):
        failures = error.get("failures", [])
        if isinstance(failures, list):
            count += len(failures)
    return count


def build_case_metrics(summary: object, quality_report: object) -> list[dict[str, object]]:
    quality_by_id = quality_cases_by_id(quality_report)
    cases: list[dict[str, object]] = []
    for case in list_dicts(summary):
        dossier_id = str(case.get("dossier_id") or "unknown")
        case_quality = quality_by_id.get(dossier_id, {})
        artifacts = dict_value(case_quality.get("artifacts", {}))
        ingestion = dict_value(case_quality.get("ingestion_pdf", {}))
        text_stats = dict_value(ingestion.get("text_stats", {}))
        sourcing = dict_value(case_quality.get("sourcing", {}))
        events = list_dicts(case.get("events", []))
        metrics = dict_value(case.get("metrics", {}))
        wall_clock = float_value(metrics.get("wall_clock_seconds"))
        expected_artifacts = int_value(artifacts.get("expected_count"))
        produced_artifacts = int_value(artifacts.get("produced_count"))

        cases.append(
            {
                "dossier_id": dossier_id,
                "status": str(case.get("status") or "UNKNOWN"),
                "events_count": len(events),
                "artifact_written_events": sum(1 for event in events if event.get("event") == "artifact_written"),
                "wall_clock_seconds": wall_clock if wall_clock and wall_clock > 0 else None,
                "blocking_count": len(case.get("blocking_failures", [])) if isinstance(case.get("blocking_failures"), list) else 0,
                "warning_count": len(case.get("warnings", [])) if isinstance(case.get("warnings"), list) else 0,
                "source_chars": int_value(text_stats.get("chars")),
                "source_pages_estimate": int_value(text_stats.get("pages_estimate")),
                "sourced_field_rate": float_value(sourcing.get("sourced_field_rate")),
                "expected_artifacts": expected_artifacts,
                "produced_artifacts": produced_artifacts,
                "missing_artifacts": int_value(artifacts.get("missing_count")),
                "artifact_completion_rate": rate(produced_artifacts, expected_artifacts),
                "contract_errors": count_contract_failures(case_quality),
            }
        )
    return cases


def build_step_event_counts(summary: object) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for case in list_dicts(summary):
        for event in list_dicts(case.get("events", [])):
            step = str(event.get("step") or "session")
            event_type = str(event.get("event") or "UNKNOWN")
            counts.setdefault(step, {})
            counts[step][event_type] = counts[step].get(event_type, 0) + 1
    return {step: dict(sorted(events.items())) for step, events in sorted(counts.items())}


def manifest_bytes_by_category(manifest: object) -> dict[str, int]:
    totals: dict[str, int] = {}
    for artifact in list_dicts(dict_value(manifest).get("artifacts", [])):
        category = str(artifact.get("category") or "unknown")
        totals[category] = totals.get(category, 0) + int_value(artifact.get("bytes"))
    return dict(sorted(totals.items()))


def build_cost_proxy(cases: list[dict[str, object]], manifest: object, events_total: int) -> dict[str, object]:
    bytes_by_category = manifest_bytes_by_category(manifest)
    source_chars = sum(int_value(case.get("source_chars")) for case in cases)
    source_pages = sum(int_value(case.get("source_pages_estimate")) for case in cases)
    case_artifact_bytes = bytes_by_category.get("case_artifact", 0)
    runtime_control_bytes = sum(bytes_by_category.values()) - case_artifact_bytes
    input_kchar_units = round(source_chars / 1000, 2)
    output_kb_units = round(case_artifact_bytes / 1024, 2)
    control_kb_units = round(max(runtime_control_bytes, 0) / 1024, 2)
    total_proxy_units = round(input_kchar_units + output_kb_units + events_total, 2)

    return {
        "source_chars": source_chars,
        "source_pages_estimate": source_pages,
        "case_artifact_bytes": case_artifact_bytes,
        "runtime_control_bytes": max(runtime_control_bytes, 0),
        "input_kchar_units": input_kchar_units,
        "output_kb_units": output_kb_units,
        "runtime_control_kb_units": control_kb_units,
        "orchestration_event_units": events_total,
        "total_proxy_units": total_proxy_units,
        "proxy_units_per_case": rate(total_proxy_units, len(cases)),
        "bytes_by_category": bytes_by_category,
        "unit_note": "Proxy v0: kchar sources + KB artefacts dossier + evenements runtime. Ne remplace pas les couts tokens/provider reels.",
    }


def build_latency_section(cases: list[dict[str, object]], events_total: int, step_event_counts: dict[str, dict[str, int]]) -> dict[str, object]:
    event_counts = [int_value(case.get("events_count")) for case in cases]
    wall_clock_values = [
        float(case["wall_clock_seconds"])
        for case in cases
        if isinstance(case.get("wall_clock_seconds"), (int, float)) and float(case["wall_clock_seconds"]) > 0
    ]
    return {
        "wall_clock_seconds_available": bool(wall_clock_values),
        "p50_wall_clock_seconds": percentile(wall_clock_values, 0.50),
        "p95_wall_clock_seconds": percentile(wall_clock_values, 0.95),
        "average_wall_clock_seconds": round(fmean(wall_clock_values), 4) if wall_clock_values else None,
        "events_total": events_total,
        "average_events_per_case": round(fmean(event_counts), 4) if event_counts else 0,
        "p95_events_per_case": percentile([float(value) for value in event_counts], 0.95),
        "step_event_counts": step_event_counts,
        "note": "Les runs deterministes existants exposent des compteurs d'evenements; le wall-clock doit etre mesure sur un run non deterministe avant SLO final.",
    }


def build_reliability_section(cases: list[dict[str, object]], quality_report: object, delta_report: object) -> dict[str, object]:
    quality = dict_value(quality_report)
    totals = dict_value(quality.get("totals", {}))
    status_counts = dict_value(quality.get("status_counts", {}))
    cases_count = len(cases)
    expected_artifacts = int_value(totals.get("expected_artifacts"))
    produced_artifacts = int_value(totals.get("produced_artifacts"))
    delta = dict_value(delta_report)
    regressions = list_dicts(delta.get("regressions", []))

    return {
        "ready_rate": rate(int_value(status_counts.get("PRET_REVISION_FINALE")), cases_count),
        "review_required_rate": rate(sum(int_value(status_counts.get(status)) for status in STATUS_REVIEW_REQUIRED), cases_count),
        "artifact_completion_rate": rate(produced_artifacts, expected_artifacts),
        "blocking_failures": int_value(totals.get("blocking_failures")),
        "warnings": int_value(totals.get("warnings")),
        "contract_errors": int_value(totals.get("contract_errors")),
        "missing_artifacts": int_value(totals.get("missing_artifacts")),
        "blocking_failures_per_case": rate(int_value(totals.get("blocking_failures")), cases_count),
        "warnings_per_case": rate(int_value(totals.get("warnings")), cases_count),
        "delta_status": str(delta.get("status") or "UNKNOWN"),
        "regressions_count": len(regressions),
    }


def build_slo_candidates(report: dict[str, object]) -> list[dict[str, object]]:
    reliability = dict_value(report.get("reliability", {}))
    latency = dict_value(report.get("latency", {}))
    cost_proxy = dict_value(report.get("cost_proxy", {}))
    averages = dict_value(report.get("quality_averages", {}))
    wall_clock_p95 = latency.get("p95_wall_clock_seconds")
    wall_clock_available = bool(latency.get("wall_clock_seconds_available"))
    artifact_completion = float_value(reliability.get("artifact_completion_rate"))
    source_coverage = float_value(averages.get("sourced_field_rate"))
    contract_errors = int_value(reliability.get("contract_errors"))
    regressions = int_value(reliability.get("regressions_count"))

    return [
        {
            "metric": "latence_p95_dossier",
            "current": wall_clock_p95,
            "target": f"<= {int(WALL_CLOCK_TARGET_P95_SECONDS)} sec",
            "status": "INSTRUMENTATION_REQUISE"
            if not wall_clock_available
            else "OK"
            if float(wall_clock_p95 or 0) <= WALL_CLOCK_TARGET_P95_SECONDS
            else "A_TRAITER",
            "owner": "Platform",
            "evidence": "runtime_summary.json metrics.wall_clock_seconds",
        },
        {
            "metric": "completion_artefacts",
            "current": artifact_completion,
            "target": f">= {ARTIFACT_COMPLETION_TARGET:.2f}",
            "status": "OK" if artifact_completion is not None and artifact_completion >= ARTIFACT_COMPLETION_TARGET else "A_TRAITER",
            "owner": "QA/Runtime",
            "evidence": "quality_report.json totals",
        },
        {
            "metric": "couverture_champs_sources",
            "current": source_coverage,
            "target": f">= {SOURCE_COVERAGE_TARGET:.2f}",
            "status": "OK" if source_coverage is not None and source_coverage >= SOURCE_COVERAGE_TARGET else "A_TRAITER",
            "owner": "Data/Ops",
            "evidence": "quality_report.json averages.sourced_field_rate",
        },
        {
            "metric": "erreurs_contrat",
            "current": contract_errors,
            "target": f"<= {CONTRACT_ERROR_TARGET}",
            "status": "OK" if contract_errors <= CONTRACT_ERROR_TARGET else "A_TRAITER",
            "owner": "QA/Platform",
            "evidence": "quality_report.json totals.contract_errors",
        },
        {
            "metric": "regressions_delta_runtime",
            "current": regressions,
            "target": f"<= {REGRESSION_TARGET}",
            "status": "OK" if regressions <= REGRESSION_TARGET else "A_TRAITER",
            "owner": "Platform",
            "evidence": "runtime_delta_report.json regressions",
        },
        {
            "metric": "cout_proxy_par_dossier",
            "current": cost_proxy.get("proxy_units_per_case"),
            "target": "baseline v0; alerte si +25% vs dernier run stable",
            "status": "BASELINE",
            "owner": "Product/Platform",
            "evidence": "perf_cost_phase_g_report.json cost_proxy",
        },
    ]


def build_phase_decision(report: dict[str, object]) -> dict[str, object]:
    reliability = dict_value(report.get("reliability", {}))
    latency = dict_value(report.get("latency", {}))
    blockers: list[str] = []
    conditions: list[str] = []

    if reliability.get("delta_status") == "A_CONTROLER" or int_value(reliability.get("regressions_count")) > 0:
        blockers.append("Regression runtime detectee dans le delta.")
    if not latency.get("wall_clock_seconds_available"):
        conditions.append("Mesure wall-clock par dossier/etape requise avant SLO final.")
    if int_value(reliability.get("contract_errors")) > 0:
        conditions.append("Separer erreurs contrat attendues des cas garde-fous et regressions bloquantes.")
    artifact_completion = float_value(reliability.get("artifact_completion_rate"))
    if artifact_completion is not None and artifact_completion < ARTIFACT_COMPLETION_TARGET:
        conditions.append("Porter la completion artefacts a la cible Phase G ou documenter l'exception du cas negatif.")

    return {
        "status": "NO_GO" if blockers else "GO_CONDITIONNEL" if conditions else "GO",
        "blockers": blockers,
        "conditions": conditions,
    }


def build_phase_g_report(summary: object, quality_report: object, manifest: object, delta_report: object) -> dict[str, object]:
    cases = build_case_metrics(summary, quality_report)
    quality = dict_value(quality_report)
    step_event_counts = build_step_event_counts(summary)
    events_total = sum(int_value(case.get("events_count")) for case in cases)
    reliability = build_reliability_section(cases, quality_report, delta_report)
    latency = build_latency_section(cases, events_total, step_event_counts)
    cost_proxy = build_cost_proxy(cases, manifest, events_total)

    report: dict[str, object] = {
        "schema_version": "phase_g_perf_cost_report_v0",
        "source_reports": {
            "summary": SUMMARY_DEFAULT.as_posix(),
            "quality": QUALITY_DEFAULT.as_posix(),
            "manifest": MANIFEST_DEFAULT.as_posix(),
            "delta": DELTA_DEFAULT.as_posix(),
        },
        "cases_count": len(cases),
        "status_counts": quality.get("status_counts", {}) if isinstance(quality.get("status_counts"), dict) else {},
        "quality_averages": quality.get("averages", {}) if isinstance(quality.get("averages"), dict) else {},
        "reliability": reliability,
        "latency": latency,
        "cost_proxy": cost_proxy,
        "cases": cases,
    }
    report["slo_candidates"] = build_slo_candidates(report)
    report["decision"] = build_phase_decision(report)
    return report


def format_rate(value: object) -> str:
    number = float_value(value)
    if number is None:
        return "n/d"
    return f"{number * 100:.1f}%"


def format_number(value: object, decimals: int = 2) -> str:
    number = float_value(value)
    if number is None:
        return "n/d"
    if number.is_integer():
        return str(int(number))
    return f"{number:.{decimals}f}"


def format_seconds(value: object) -> str:
    number = float_value(value)
    if number is None:
        return "n/d"
    return f"{number:.2f}s"


def build_bench_markdown(report: dict[str, object]) -> str:
    reliability = dict_value(report.get("reliability", {}))
    latency = dict_value(report.get("latency", {}))
    cost_proxy = dict_value(report.get("cost_proxy", {}))
    decision = dict_value(report.get("decision", {}))
    cases = list_dicts(report.get("cases", []))

    lines = [
        "# BENCH PERF COUT V1",
        "",
        "_As-of date: 2026-04-30 (UTC)_",
        "",
        "## Objectif",
        "Etablir la baseline Phase G performance, fiabilite et cout a partir des sorties runtime pilotes deja produites.",
        "",
        "## Synthese",
        "",
        "| Indicateur | Valeur |",
        "|---|---:|",
        f"| Dossiers analyses | {report.get('cases_count', 0)} |",
        f"| Evenements runtime | {latency.get('events_total', 0)} |",
        f"| Evenements moyens / dossier | {format_number(latency.get('average_events_per_case'))} |",
        f"| P95 evenements / dossier | {format_number(latency.get('p95_events_per_case'))} |",
        f"| P95 wall-clock / dossier | {format_seconds(latency.get('p95_wall_clock_seconds'))} |",
        f"| Completion artefacts | {format_rate(reliability.get('artifact_completion_rate'))} |",
        f"| Erreurs contrat | {reliability.get('contract_errors', 0)} |",
        f"| Regressions delta | {reliability.get('regressions_count', 0)} |",
        f"| Sources analysees | {cost_proxy.get('source_pages_estimate', 0)} pages / {cost_proxy.get('source_chars', 0)} chars |",
        f"| Cout proxy total | {format_number(cost_proxy.get('total_proxy_units'))} unites |",
        f"| Cout proxy / dossier | {format_number(cost_proxy.get('proxy_units_per_case'))} unites |",
        f"| Decision Phase G | {decision.get('status', 'UNKNOWN')} |",
        "",
        "## Limite de mesure",
        "",
        "- Les runs actuels sont deterministes: la latence wall-clock n'est pas encore une mesure exploitable.",
        "- Le cout est un proxy reproductible, pas une facture tokens/provider: kchar sources + KB artefacts dossier + evenements runtime.",
        "- Le prochain run Phase G doit activer des durees par dossier et par etape avant de figer les SLO finaux.",
        "",
        "## Charge par etape",
        "",
        "| Etape | step_start | artifact_written | step_done | blocking_detected | warning_detected | contract_invalid |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    step_counts = dict_value(latency.get("step_event_counts", {}))
    for step, raw_counts in step_counts.items():
        counts = dict_value(raw_counts)
        lines.append(
            "| {step} | {step_start} | {artifact_written} | {step_done} | {blocking_detected} | {warning_detected} | {contract_invalid} |".format(
                step=step,
                step_start=int_value(counts.get("step_start")),
                artifact_written=int_value(counts.get("artifact_written")),
                step_done=int_value(counts.get("step_done")),
                blocking_detected=int_value(counts.get("blocking_detected")),
                warning_detected=int_value(counts.get("warning_detected")),
                contract_invalid=int_value(counts.get("contract_invalid")),
            )
        )

    lines.extend(
        [
            "",
            "## Dossiers",
            "",
            "| Dossier | Statut | Events | Artefacts | Completion | Blocages | Warnings | Contrats | Sources | Wall-clock |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for case in cases:
        lines.append(
            "| {dossier} | {status} | {events} | {produced}/{expected} | {completion} | {blocking} | {warnings} | {contracts} | {pages} p | {wall_clock} |".format(
                dossier=case.get("dossier_id", "-"),
                status=case.get("status", "UNKNOWN"),
                events=case.get("events_count", 0),
                produced=case.get("produced_artifacts", 0),
                expected=case.get("expected_artifacts", 0),
                completion=format_rate(case.get("artifact_completion_rate")),
                blocking=case.get("blocking_count", 0),
                warnings=case.get("warning_count", 0),
                contracts=case.get("contract_errors", 0),
                pages=case.get("source_pages_estimate", 0),
                wall_clock=format_seconds(case.get("wall_clock_seconds")),
            )
        )

    lines.extend(["", "## Decision et conditions", ""])
    conditions = decision.get("conditions", [])
    blockers = decision.get("blockers", [])
    if blockers:
        for blocker in blockers:
            lines.append(f"- Bloquant: {blocker}")
    if conditions:
        for condition in conditions:
            lines.append(f"- Condition: {condition}")
    if not blockers and not conditions:
        lines.append("- Aucune condition ouverte.")

    return "\n".join(lines).rstrip() + "\n"


def build_slo_markdown(report: dict[str, object]) -> str:
    decision = dict_value(report.get("decision", {}))
    slo_candidates = list_dicts(report.get("slo_candidates", []))
    lines = [
        "# SLO SLA V1",
        "",
        "_As-of date: 2026-04-30 (UTC)_",
        "",
        "## Objectif",
        "Fixer les SLO/SLA initiaux Phase G et les alertes minimales avant la campagne terrain Phase H.",
        "",
        f"Decision de phase: **{decision.get('status', 'UNKNOWN')}**.",
        "",
        "## SLO initiaux",
        "",
        "| SLO | Courant | Cible | Statut | Owner | Preuve |",
        "|---|---:|---:|---|---|---|",
    ]
    for item in slo_candidates:
        metric = item.get("metric", "-")
        current = item.get("current")
        if isinstance(current, float):
            current_text = format_rate(current) if current <= 1 and metric != "cout_proxy_par_dossier" else format_number(current)
        elif current is None:
            current_text = "n/d"
        else:
            current_text = str(current)
        lines.append(
            "| {metric} | {current} | {target} | {status} | {owner} | `{evidence}` |".format(
                metric=metric,
                current=current_text,
                target=item.get("target", "-"),
                status=item.get("status", "-"),
                owner=item.get("owner", "-"),
                evidence=item.get("evidence", "-"),
            )
        )

    lines.extend(
        [
            "",
            "## SLA operationnel v1",
            "",
            "| Flux | Engagement initial | Escalade |",
            "|---|---|---|",
            "| Run pilote batch | Rapport perf/cout disponible le meme jour ouvre | Platform si rapport absent |",
            "| Regression delta | Triage en moins de 1 jour ouvre | QA/Platform si `A_CONTROLER` |",
            "| Erreur contrat non attendue | Correction ou exception documentee avant Phase H | Lead Runtime + Lead Metier |",
            "| Depassement budget cout proxy | Revue prompt/outils avant nouveau lot | Product + Platform |",
            "",
            "## Alertes minimales",
            "",
            "- Alerte `runtime_delta_regression` si `runtime_delta_report.status == A_CONTROLER`.",
            "- Alerte `artifact_completion_low` si completion artefacts < 98% hors cas garde-fou documente.",
            "- Alerte `contract_errors_unclassified` si erreurs contrat > 0 sans classification attendu/non-attendu.",
            "- Alerte `cost_proxy_growth` si cout proxy par dossier augmente de 25% vs dernier run stable.",
            "- Alerte `wall_clock_missing` tant que p95 wall-clock n'est pas mesure sur un run non deterministe.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_optimization_plan_markdown(report: dict[str, object]) -> str:
    reliability = dict_value(report.get("reliability", {}))
    latency = dict_value(report.get("latency", {}))
    cost_proxy = dict_value(report.get("cost_proxy", {}))
    lines = [
        "# PLAN OPTIMISATION V1",
        "",
        "_As-of date: 2026-04-30 (UTC)_",
        "",
        "## Objectif",
        "Transformer la baseline Phase G en actions d'optimisation mesurables sans degrader la qualite de justification.",
        "",
        "## Constats de depart",
        "",
        f"- Delta runtime: **{reliability.get('delta_status', 'UNKNOWN')}** avec {reliability.get('regressions_count', 0)} regression(s).",
        f"- Completion artefacts: **{format_rate(reliability.get('artifact_completion_rate'))}**.",
        f"- Erreurs contrat: **{reliability.get('contract_errors', 0)}**.",
        f"- Evenements moyens par dossier: **{format_number(latency.get('average_events_per_case'))}**.",
        f"- Cout proxy par dossier: **{format_number(cost_proxy.get('proxy_units_per_case'))}** unites.",
        "",
        "## Actions P0",
        "",
        "| Action | Resultat attendu | Owner | Preuve de fermeture |",
        "|---|---|---|---|",
        "| Instrumenter wall-clock par dossier et par etape | p50/p95 reels disponibles | Platform | `runtime_summary.json.metrics` non nul + bench regenere |",
        "| Classifier les erreurs contrat attendues vs regressions | Cas garde-fou ne brouille plus les gates | QA/Runtime | matrice erreurs contrat + test cible |",
        "| Definir commande benchmark batch | Run reproductible N dossiers / N iterations | Platform | script CLI + rapport Phase G |",
        "| Fixer budget cout reel tokens/provider | Cout proxy relie aux couts reels | Product/Platform | table cout unitaire + seuil alerte |",
        "",
        "## Actions P1",
        "",
        "| Action | Resultat attendu | Owner | Preuve de fermeture |",
        "|---|---|---|---|",
        "| Cache ingestion/source_index | Moins de recalcul source sur rerun | Data/Ops | baisse cout proxy source/output |",
        "| Paralleliser calculs valuation compatibles | Reduction p95 sans perte audit | Runtime | traces calcul completes + p95 ameliore |",
        "| Compresser ou archiver artefacts verbeux | Baisse stockage et transfert | Platform | baisse KB artefacts dossier |",
        "| Ajouter alerte qualite/cout dans readiness | Gate avant campagne Phase H | QA/Platform | readiness inclut SLO Phase G |",
        "",
        "## Actions P2",
        "",
        "- Reexecution incrementale par dossier et par etape modifiee.",
        "- Budget adaptatif par type de dossier et complexite source.",
        "- Drift detection sur cout proxy, qualite comparables et taux de revue humaine.",
        "",
        "## Dependances Phase H",
        "",
        "- Aucun passage Phase H sans p95 wall-clock mesure.",
        "- Les erreurs contrat du cas negatif doivent etre classees comme attendues ou corrigees.",
        "- Les SLO doivent etre revus avec au moins un evaluateur avant campagne terrain.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_phase_g_deliverables(
    report: dict[str, object],
    *,
    json_out: Path = OUT_JSON_DEFAULT,
    bench_out: Path = BENCH_MD_DEFAULT,
    slo_out: Path = SLO_MD_DEFAULT,
    plan_out: Path = PLAN_MD_DEFAULT,
) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_text(bench_out, build_bench_markdown(report))
    write_text(slo_out, build_slo_markdown(report))
    write_text(plan_out, build_optimization_plan_markdown(report))


def generate_phase_g_deliverables(
    *,
    summary_path: Path = SUMMARY_DEFAULT,
    quality_path: Path = QUALITY_DEFAULT,
    manifest_path: Path = MANIFEST_DEFAULT,
    delta_path: Path = DELTA_DEFAULT,
    json_out: Path = OUT_JSON_DEFAULT,
    bench_out: Path = BENCH_MD_DEFAULT,
    slo_out: Path = SLO_MD_DEFAULT,
    plan_out: Path = PLAN_MD_DEFAULT,
) -> dict[str, object]:
    report = build_phase_g_report(
        load_json(summary_path, []),
        load_json(quality_path, {}),
        load_json(manifest_path, {}),
        load_json(delta_path, {}),
    )
    report["source_reports"] = {
        "summary": summary_path.as_posix(),
        "quality": quality_path.as_posix(),
        "manifest": manifest_path.as_posix(),
        "delta": delta_path.as_posix(),
    }
    write_phase_g_deliverables(report, json_out=json_out, bench_out=bench_out, slo_out=slo_out, plan_out=plan_out)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Genere les livrables Phase G performance, fiabilite et cout.")
    parser.add_argument("--summary", type=Path, default=SUMMARY_DEFAULT)
    parser.add_argument("--quality", type=Path, default=QUALITY_DEFAULT)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_DEFAULT)
    parser.add_argument("--delta", type=Path, default=DELTA_DEFAULT)
    parser.add_argument("--json-out", type=Path, default=OUT_JSON_DEFAULT)
    parser.add_argument("--bench-out", type=Path, default=BENCH_MD_DEFAULT)
    parser.add_argument("--slo-out", type=Path, default=SLO_MD_DEFAULT)
    parser.add_argument("--plan-out", type=Path, default=PLAN_MD_DEFAULT)
    args = parser.parse_args()

    report = generate_phase_g_deliverables(
        summary_path=args.summary,
        quality_path=args.quality,
        manifest_path=args.manifest,
        delta_path=args.delta,
        json_out=args.json_out,
        bench_out=args.bench_out,
        slo_out=args.slo_out,
        plan_out=args.plan_out,
    )
    print(f"Rapport Phase G JSON: {args.json_out}")
    print(f"Bench Phase G: {args.bench_out}")
    print(f"SLO/SLA Phase G: {args.slo_out}")
    print(f"Plan optimisation Phase G: {args.plan_out}")
    print(f"Decision: {dict_value(report.get('decision', {})).get('status', 'UNKNOWN')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
