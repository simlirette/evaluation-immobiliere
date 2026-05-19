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
    "zip": "paquet_v1.zip",
}

_KEY_ARTIFACTS = [
    ("data-facts", "fiche_bien.json"),
    ("comps-market", "comparables_proposes.json"),
    ("valuation-draft", "calculs_approche_comparative.json"),
    ("compliance-qa", "rapport_conformite.json"),
]


def _find_rapport_md(session: dict) -> tuple[str, Path | None]:
    """Locate brouillon_rapport.md artifact. Returns (md_text, path|None)."""
    artifact_index_path = Path(str(session.get("session_dir") or "")) / "artifact_index.json"
    if not artifact_index_path.exists():
        return "", None
    try:
        index = json.loads(artifact_index_path.read_text(encoding="utf-8"))
    except Exception:
        return "", None

    for event in index.get("events", []) if isinstance(index.get("events"), list) else []:
        for art in event.get("artifacts", []) if isinstance(event.get("artifacts"), list) else []:
            if art.get("artifact") == "brouillon_rapport.md":
                art_path = Path(str(art.get("path") or ""))
                if art_path.exists():
                    return art_path.read_text(encoding="utf-8"), art_path
    return "", None


def _collect_artifact_paths(case: dict) -> list[tuple[str, Path]]:
    """Collect existing key artifact JSON files from artifact_dir."""
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

    # ── 2. Rapport PDF ─────────────────────────────────────────────────────────
    rapport_pdf_path = out_dir / PACKAGE_FILES["rapport_pdf"]
    if md_text:
        try:
            pdf_bytes = _generate_pdf(md_text, dossier_id)
            rapport_pdf_path.write_bytes(pdf_bytes)
            files.append({"name": PACKAGE_FILES["rapport_pdf"], "size": len(pdf_bytes)})
        except Exception:
            pass  # PDF generation is best-effort

    # ── 3. Key artifacts ───────────────────────────────────────────────────────
    artifact_files = _collect_artifact_paths(case)
    for filename, src_path in artifact_files:
        dst = out_dir / filename
        dst.write_bytes(src_path.read_bytes())
        files.append({"name": filename, "size": src_path.stat().st_size})

    # ── 4. Manifest ────────────────────────────────────────────────────────────
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
        "artifacts_count": len(files),
        "package_files": {f["name"]: f["size"] for f in files},
    }
    manifest_path = out_dir / PACKAGE_FILES["manifest"]
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    files.append({"name": PACKAGE_FILES["manifest"], "size": manifest_path.stat().st_size})

    # ── 5. ZIP archive ─────────────────────────────────────────────────────────
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
