"""Package V1 generation — ZIP bundle: rapport PDF + artifacts + manifest."""
from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

PACKAGE_FILES = {
    "manifest": "manifest_v1.json",
    "rapport_pdf": "rapport.pdf",
    "rapport_md": "rapport.md",
    "professional_workfile_gate": "professional_workfile_gate.json",
    "npp_compliance_matrix": "npp_compliance_matrix.json",
    "source_provenance": "source_provenance.json",
    "zip": "paquet_v1.zip",
}

_KEY_ARTIFACTS = [
    ("data-facts", "fiche_bien.json"),
    ("comps-market", "comparables_proposes.json"),
    ("valuation-draft", "calculs_approche_comparative.json"),
    ("compliance-qa", "rapport_non_conformites.json"),
    ("compliance-qa", "statut_sortie.json"),
]


def _resolve_session_file(session: dict, raw_path: object) -> Path | None:
    raw = Path(str(raw_path or ""))
    if not raw:
        return None
    try:
        resolved = raw.resolve()
        session_dir = Path(str(session.get("session_dir") or "")).resolve()
        resolved.relative_to(session_dir)
    except (OSError, ValueError):
        return None
    return resolved if resolved.exists() and resolved.is_file() else None


def _load_artifact_index(session: dict) -> dict:
    artifact_index_path = Path(str(session.get("session_dir") or "")) / "artifact_index.json"
    if not artifact_index_path.exists():
        return {}
    try:
        payload = json.loads(artifact_index_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _find_rapport_md(session: dict) -> tuple[str, Path | None]:
    """Locate brouillon_rapport.md artifact. Returns (md_text, path|None)."""
    index = _load_artifact_index(session)

    for record in index.get("artifacts", []) if isinstance(index.get("artifacts"), list) else []:
        if record.get("step") != "redaction" or record.get("artifact") != "brouillon_rapport.md":
            continue
        art_path = _resolve_session_file(session, record.get("path"))
        if art_path:
            return art_path.read_text(encoding="utf-8"), art_path

    for event in index.get("events", []) if isinstance(index.get("events"), list) else []:
        for art in event.get("artifacts", []) if isinstance(event.get("artifacts"), list) else []:
            if art.get("artifact") == "brouillon_rapport.md":
                art_path = _resolve_session_file(session, art.get("path"))
                if art_path:
                    return art_path.read_text(encoding="utf-8"), art_path
    return "", None


def _collect_artifact_paths(case: dict, session: dict | None = None) -> list[tuple[str, Path]]:
    """Collect existing key artifact JSON files from artifact_dir."""
    if session:
        index = _load_artifact_index(session)
        collected: list[tuple[str, Path]] = []
        for step, artifact in _KEY_ARTIFACTS:
            for record in index.get("artifacts", []) if isinstance(index.get("artifacts"), list) else []:
                if record.get("step") != step or record.get("artifact") != artifact:
                    continue
                path = _resolve_session_file(session, record.get("path"))
                if path:
                    collected.append((artifact, path))
                break
        if collected:
            return collected

    artifact_dir = Path(str(case.get("artifact_dir") or ""))
    if not artifact_dir.exists():
        return []
    collected: list[tuple[str, Path]] = []
    for agent, filename in _KEY_ARTIFACTS:
        candidate = artifact_dir / agent / filename
        if candidate.exists():
            collected.append((filename, candidate))
    return collected


def generate_package_from_case(
    *,
    case: dict,
    out_dir: Path,
    session: dict,
    review: dict,
    integrity: dict,
    package_origin: str = "validated_runtime_session",
    certifiability_gate: dict | None = None,
    professional_workfile_gate: dict | None = None,
    npp_compliance_matrix: dict | None = None,
    source_provenance: dict | None = None,
    require_report_md: bool = False,
    require_report_pdf: bool = False,
) -> dict:
    """Generate package V1 ZIP bundle.

    Returns:
        {status, dossier_id, out_dir, files}
    """
    from engine.report_export import _generate_pdf  # lazy import

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    dossier_id = str(case.get("dossier_id") or session.get("dossier_id") or "rapport")
    generated_at = datetime.now(timezone.utc).isoformat()
    files: list[dict] = []

    # ── 1. Rapport markdown ────────────────────────────────────────────────────
    md_text, _md_src = _find_rapport_md(session)
    rapport_md_path = out_dir / PACKAGE_FILES["rapport_md"]
    if md_text:
        rapport_md_path.write_text(md_text, encoding="utf-8")
        files.append({"name": PACKAGE_FILES["rapport_md"], "size": len(md_text.encode())})
    elif require_report_md:
        raise ValueError("paquet V1 refuse: brouillon_rapport.md introuvable")

    # ── 2. Rapport PDF ─────────────────────────────────────────────────────────
    rapport_pdf_path = out_dir / PACKAGE_FILES["rapport_pdf"]
    if md_text:
        try:
            pdf_bytes = _generate_pdf(md_text, dossier_id)
            rapport_pdf_path.write_bytes(pdf_bytes)
            files.append({"name": PACKAGE_FILES["rapport_pdf"], "size": len(pdf_bytes)})
        except Exception as exc:
            if require_report_pdf:
                raise ValueError(f"paquet V1 refuse: generation PDF impossible ({type(exc).__name__})") from exc
            pass  # PDF generation remains best-effort for direct helper usage.
    elif require_report_pdf:
        raise ValueError("paquet V1 refuse: rapport PDF impossible sans brouillon")

    # ── 3. Key artifacts ───────────────────────────────────────────────────────
    artifact_files = _collect_artifact_paths(case, session)
    for filename, src_path in artifact_files:
        dst = out_dir / filename
        dst.write_bytes(src_path.read_bytes())
        files.append({"name": filename, "size": src_path.stat().st_size})

    # 4. Professional E.A. evidence
    evidence_payloads = {
        PACKAGE_FILES["professional_workfile_gate"]: professional_workfile_gate or {},
        PACKAGE_FILES["npp_compliance_matrix"]: npp_compliance_matrix or {},
        PACKAGE_FILES["source_provenance"]: source_provenance or {},
    }
    for filename, payload in evidence_payloads.items():
        if not payload:
            continue
        path = out_dir / filename
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        files.append({"name": filename, "size": path.stat().st_size})

    # 5. Manifest
    status = "PRET_REVUE_EVALUATEUR_AGREE"
    manifest = {
        "schema_version": "package_v1",
        "status": status,
        "dossier_id": dossier_id,
        "session_id": session.get("session_id", ""),
        "run_id": session.get("run_id", ""),
        "generated_at": generated_at,
        "package_origin": package_origin,
        "review": {
            "decision": review.get("decision", ""),
            "reviewer": review.get("reviewer", ""),
            "notes": review.get("notes", ""),
            "reviewed_at": review.get("reviewed_at", ""),
        },
        "integrity_ok": bool(integrity.get("ok")),
        "certifiability_gate": certifiability_gate or {},
        "professional_workfile_gate": professional_workfile_gate or {},
        "npp_compliance_matrix": npp_compliance_matrix or {},
        "source_provenance": source_provenance or {},
        "requires_human_validation": True,
        "certification_automatic": False,
        "external_evaluator_responses_included": False,
        "artifacts_count": len(files),
        "package_files": {f["name"]: f["size"] for f in files},
    }
    manifest_path = out_dir / PACKAGE_FILES["manifest"]
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    files.append({"name": PACKAGE_FILES["manifest"], "size": manifest_path.stat().st_size})

    # 6. ZIP archive
    zip_path = out_dir / PACKAGE_FILES["zip"]
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            src = out_dir / f["name"]
            if src.exists():
                zf.write(src, arcname=f["name"])
    zip_size = zip_path.stat().st_size

    return {
        "status": status,
        "dossier_id": dossier_id,
        "out_dir": str(out_dir),
        "files": files + [{"name": PACKAGE_FILES["zip"], "size": zip_size}],
    }
