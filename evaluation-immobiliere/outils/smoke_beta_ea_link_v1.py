#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_JSON_DEFAULT = PROJECT_ROOT / "runtime_pilotes_reels" / "beta_ea_smoke_v1.json"
OUT_MD_DEFAULT = PROJECT_ROOT / "runtime_pilotes_reels" / "BETA-EA-SMOKE-V1.md"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def request_json(base_url: str, method: str, path: str, *, token: str = "", role: str = "supervisor", body: dict | None = None) -> dict:
    url = base_url.rstrip("/") + path
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {"X-Runtime-Role": role}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        text = response.read().decode("utf-8")
    return json.loads(text) if text else {}


def request_text(base_url: str, path: str) -> str:
    with urllib.request.urlopen(base_url.rstrip("/") + path, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def check(label: str, ok: bool, detail: str) -> dict[str, object]:
    return {"label": label, "ok": ok, "status": "OK" if ok else "ECHEC", "detail": detail}


def build_smoke_report(args: argparse.Namespace) -> dict[str, object]:
    checks: list[dict[str, object]] = []
    readiness: dict[str, object] = {}
    intake: dict[str, object] = {}
    session_summary: dict[str, object] = {}

    try:
        health = request_json(args.base_url, "GET", "/health")
        checks.append(check("health", health.get("status") == "ok", str(health.get("status", ""))))
    except Exception as exc:
        checks.append(check("health", False, f"{type(exc).__name__}: {exc}"))

    try:
        auth = request_json(args.base_url, "GET", "/auth/status", token=args.token, role=args.role)
        auth_ok = (not auth.get("enabled")) or bool(auth.get("authorized"))
        checks.append(check("auth_status", auth_ok, str(auth.get("reason", ""))))
    except Exception as exc:
        checks.append(check("auth_status", False, f"{type(exc).__name__}: {exc}"))

    try:
        product_html = request_text(args.base_url, "/product")
        checks.append(check("product_html_beta_surface", "Beta E.A." in product_html and "betaLaunch" in product_html, "surface beta presente"))
    except Exception as exc:
        checks.append(check("product_html_beta_surface", False, f"{type(exc).__name__}: {exc}"))

    try:
        readiness = request_json(args.base_url, "GET", "/beta/readiness", token=args.token, role=args.role)
        if args.require_external_ready:
            ready_ok = bool(readiness.get("ready_for_external_ea_link"))
        else:
            ready_ok = bool(readiness.get("ready_for_external_ea_link") or readiness.get("ready_for_local_anonymized_beta"))
        checks.append(check("beta_readiness", ready_ok, str(readiness.get("status", ""))))
    except Exception as exc:
        checks.append(check("beta_readiness", False, f"{type(exc).__name__}: {exc}"))

    try:
        intake = request_json(
            args.base_url,
            "POST",
            "/beta/intake",
            token=args.token,
            role=args.role,
            body={
                "fixture": args.fixture,
                "accepted_beta_terms": True,
                "anonymization_attestation": True,
                "operator": "smoke_beta_ea_v1",
                "documents": [{"document_id": "SMOKE-DOC-1", "type": "fixture", "anonymized": True}],
            },
        )
        checks.append(check("beta_intake", bool(intake.get("accepted")), str(intake.get("status", ""))))
    except urllib.error.HTTPError as exc:
        checks.append(check("beta_intake", False, f"HTTPError:{exc.code}"))
    except Exception as exc:
        checks.append(check("beta_intake", False, f"{type(exc).__name__}: {exc}"))

    session_id = str((intake.get("session") or {}).get("session_id") or "") if isinstance(intake, dict) else ""
    if session_id:
        try:
            session_summary = request_json(
                args.base_url,
                "GET",
                f"/session/summary?session_id={session_id}",
                token=args.token,
                role=args.role,
            )
            beta_intake = session_summary.get("beta_intake", {}) if isinstance(session_summary.get("beta_intake"), dict) else {}
            checks.append(check("session_beta_evidence", beta_intake.get("status") == "ACCEPTE", str(beta_intake.get("status", ""))))
        except Exception as exc:
            checks.append(check("session_beta_evidence", False, f"{type(exc).__name__}: {exc}"))
    else:
        checks.append(check("session_beta_evidence", False, "session_id absent"))

    ok = all(bool(item.get("ok")) for item in checks)
    return {
        "schema_version": "beta_ea_smoke_v1",
        "ok": ok,
        "status": "OK" if ok else "A_CORRIGER",
        "base_url": args.base_url.rstrip("/"),
        "role": args.role,
        "token_present": bool(args.token),
        "fixture": args.fixture,
        "require_external_ready": bool(args.require_external_ready),
        "generated_at_utc": utc_now_iso(),
        "checks": checks,
        "readiness_status": readiness.get("status", "") if isinstance(readiness, dict) else "",
        "readiness_blocking_checks": readiness.get("blocking_checks", []) if isinstance(readiness, dict) else [],
        "session_id": session_id,
        "session_status": (session_summary.get("result") or {}).get("status", "") if isinstance(session_summary, dict) else "",
    }


def build_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Smoke beta E.A. v1",
        "",
        f"- Statut: **{report.get('status', 'UNKNOWN')}**",
        f"- URL: `{report.get('base_url', '')}`",
        f"- Role: `{report.get('role', '')}`",
        f"- Token present: **{report.get('token_present', False)}**",
        f"- Readiness: **{report.get('readiness_status', '')}**",
        f"- Session: `{report.get('session_id', '')}`",
        "",
        "| Controle | Statut | Detail |",
        "|---|---:|---|",
    ]
    for item in report.get("checks", []):
        if isinstance(item, dict):
            lines.append(f"| {item.get('label', '')} | {item.get('status', '')} | {str(item.get('detail', '')).replace('|', '\\|')} |")
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(report: dict[str, object], json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(build_markdown(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test du lien beta E.A. via HTTP.")
    parser.add_argument("--base-url", default=os.environ.get("EVAL_IMMO_BETA_HOSTED_URL") or "http://127.0.0.1:8787")
    parser.add_argument("--token", default=os.environ.get("EVAL_RUNTIME_API_TOKEN", ""))
    parser.add_argument("--role", default="supervisor")
    parser.add_argument("--fixture", default="case_pilote_residentiel_standard.json")
    parser.add_argument("--require-external-ready", action="store_true")
    parser.add_argument("--json-out", type=Path, default=OUT_JSON_DEFAULT)
    parser.add_argument("--markdown-out", type=Path, default=OUT_MD_DEFAULT)
    args = parser.parse_args()

    report = build_smoke_report(args)
    write_outputs(report, args.json_out, args.markdown_out)
    print(f"Smoke beta E.A. JSON: {args.json_out}")
    print(f"Smoke beta E.A. Markdown: {args.markdown_out}")
    print(f"Statut: {report['status']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
