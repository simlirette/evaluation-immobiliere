from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import api  # noqa: E402
from engine.acceptance import build_acceptance_report, validate_anonymized_case  # noqa: E402


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an anonymized EA acceptance dossier end to end.")
    parser.add_argument("case_path", type=Path, help="JSON case fixture to run")
    parser.add_argument("--sessions-dir", type=Path, help="override SESSIONS_DIR for the run")
    parser.add_argument("--evaluator-id", default="ea-acceptance-reviewer", help="reviewer/evaluator identifier")
    parser.add_argument("--reviewer", default="Evaluateur acceptance anonymise", help="reviewer display name")
    parser.add_argument(
        "--notes",
        default="Acceptance anonymisee: pipeline, revue interne et paquet V1 verifies.",
        help="review notes persisted in review.json",
    )
    parser.add_argument("--output", type=Path, help="write acceptance report to this path")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    return parser.parse_args(argv)


def _load_case(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("case JSON must contain an object")
    return payload


def run_acceptance(args: argparse.Namespace) -> dict:
    if args.sessions_dir:
        args.sessions_dir.mkdir(parents=True, exist_ok=True)
        api.SESSIONS_DIR = args.sessions_dir

    case = _load_case(args.case_path)
    anonymization = validate_anonymized_case(case)
    if not anonymization["ok"]:
        report = build_acceptance_report(case=case, anonymization=anonymization, output_path=args.output)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report

    os.environ.setdefault("RUNTIME_DETERMINISTIC", "1")
    started = api.start_runtime({
        "case": case,
        "strict_mode": True,
        "_evaluator_id": args.evaluator_id,
    })
    session = started["session"]
    result = started["result"]
    review_payload: dict = {}
    package_payload: dict = {}

    pre_review_gate = api.certifiability_gate(session, require_review=False, require_report=True)
    if pre_review_gate.get("ok"):
        reviewed = api.app_validate_review({
            "session_id": session["session_id"],
            "_evaluator_id": args.evaluator_id,
            "reviewer": args.reviewer,
            "notes": args.notes,
        })
        saved_review = reviewed.get("review", {})
        review_payload = saved_review.get("review", saved_review) if isinstance(saved_review, dict) else {}
        package_payload = api.generate_v1_package_for_session(session["session_id"])
        session = api.require_session(session["session_id"])

    report_path = args.output or (Path(str(session.get("session_dir") or api.SESSIONS_DIR)) / "acceptance_ea_report.json")
    report = build_acceptance_report(
        case=case,
        anonymization=anonymization,
        session=session,
        result=result,
        review=review_payload,
        package=package_payload,
        output_path=report_path,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    report = run_acceptance(args)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"status: {report['status']}")
        print(f"dossier_id: {report.get('dossier_id', '')}")
        print(f"session_id: {report.get('session_id', '')}")
        if report.get("output_path"):
            print(f"report: {report['output_path']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
