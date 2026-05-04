#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

FIXTURES_DIR_DEFAULT = Path("evaluation-immobiliere/tests/fixtures_external")
TEXT_DIR_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels/source_text")
OUT_DIR_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels/ingestion_v0")
CASE_PATTERN = "case_pilote_reel_*.json"
MANIFEST_NAME = "MANIFESTE-INGESTION-PDF-V0.json"
REPORT_NAME = "RAPPORT-INGESTION-PDF-V0.md"
NORMALIZED_NAME = "dossier_normalise.json"
TRACE_NAME = "trace_champs.json"

MASKED_TOKEN_RE = re.compile(r"\[(DATE|MONTANT|ADRESSE|NOM|VILLE|LOT|CADASTRE|CLIENT|MUNICIPALITE)\]", re.IGNORECASE)
PRECISE_ADDRESS_RE = re.compile(r"\b\d{1,6}\s+(rue|avenue|boulevard|boul\.|chemin|ch\.|route)\b", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b")


class IngestionError(RuntimeError):
    pass


@dataclass(frozen=True)
class SourceInput:
    document_id: str
    pdf_path: Path | None
    text_path: Path | None


def safe_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip())
    return cleaned.strip("-") or "unknown"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_case_fixtures(fixtures_dir: Path = FIXTURES_DIR_DEFAULT) -> dict[str, dict]:
    cases: dict[str, dict] = {}
    for path in sorted(fixtures_dir.glob(CASE_PATTERN)):
        data = load_json(path)
        dossier_id = str(data.get("dossier_id") or path.stem)
        cases[dossier_id] = data
        source_pdf = data.get("source_pdf")
        if source_pdf:
            cases[Path(str(source_pdf)).stem] = data
    return cases


def extract_text_with_pdftotext(pdf_path: Path, text_path: Path, pdftotext_exe: Path) -> None:
    text_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [str(pdftotext_exe), "-layout", str(pdf_path), str(text_path)],
        check=True,
        capture_output=True,
        text=True,
    )


def build_text_stats(text: str) -> dict[str, object]:
    pages = text.count("\f") + 1 if text else 0
    masked_tokens = MASKED_TOKEN_RE.findall(text)
    return {
        "chars": len(text),
        "lines": len(text.splitlines()),
        "pages_estimate": pages,
        "masked_token_count": len(masked_tokens),
        "masked_token_types": sorted({token.upper() for token in masked_tokens}),
        "has_possible_precise_address": bool(PRECISE_ADDRESS_RE.search(text)),
        "has_possible_email": bool(EMAIL_RE.search(text)),
        "has_possible_phone": bool(PHONE_RE.search(text)),
    }


def discover_source_inputs(pdfs: Iterable[Path], text_dir: Path) -> list[SourceInput]:
    inputs: list[SourceInput] = []
    for raw_pdf in pdfs:
        pdf_path = raw_pdf.expanduser()
        document_id = pdf_path.stem
        text_path = text_dir / f"{document_id}.txt"
        inputs.append(SourceInput(document_id=document_id, pdf_path=pdf_path, text_path=text_path))
    return inputs


def discover_from_cases(fixtures_dir: Path, text_dir: Path) -> list[SourceInput]:
    inputs: list[SourceInput] = []
    seen: set[str] = set()
    for path in sorted(fixtures_dir.glob(CASE_PATTERN)):
        data = load_json(path)
        document_name = str(data.get("source_pdf") or f"{data.get('dossier_id', path.stem)}.pdf")
        document_id = Path(document_name).stem
        if document_id in seen:
            continue
        seen.add(document_id)
        inputs.append(SourceInput(document_id=document_id, pdf_path=None, text_path=text_dir / f"{document_id}.txt"))
    return inputs


def match_case(source: SourceInput, cases: dict[str, dict]) -> dict | None:
    return cases.get(source.document_id)


def source_document_payload(source: SourceInput, text_stats: dict[str, object] | None) -> dict[str, object]:
    payload: dict[str, object] = {
        "document_id": source.document_id,
        "file_name": source.pdf_path.name if source.pdf_path else f"{source.document_id}.pdf",
        "sha256": sha256_file(source.pdf_path) if source.pdf_path and source.pdf_path.exists() else "",
        "text_file_name": source.text_path.name if source.text_path else "",
        "text_sha256": sha256_file(source.text_path) if source.text_path and source.text_path.exists() else "",
        "text_stats": text_stats or {},
    }
    return payload


def field_trace(
    field_path: str,
    value: object,
    *,
    source_ids: list[str],
    confidence: float,
    notes: list[str],
    extraction_method: str = "fixture_from_anonymized_pdf",
) -> dict[str, object]:
    value_status = "PRESENT"
    lower_notes = " ".join(notes).lower()
    if value in (None, "", [], {}):
        value_status = "ABSENT"
    elif "approx" in lower_notes and "prix_vente" in field_path:
        value_status = "APPROXIMATED"
    elif field_path == "date_reference" and (
        "date de reference" in lower_notes and ("retenue" in lower_notes or "infer" in lower_notes)
    ):
        value_status = "INFERRED"
    review_status = "NEEDS_HUMAN_REVIEW" if confidence < 0.60 or value_status in {"APPROXIMATED", "INFERRED"} else "MACHINE_READY"
    return {
        "field_path": field_path,
        "value_status": value_status,
        "source_ids": source_ids,
        "extraction_method": extraction_method,
        "confidence": confidence,
        "review_status": review_status,
    }


def build_trace(case: dict, text_stats: dict[str, object] | None) -> list[dict[str, object]]:
    confidence = float(case.get("confidence", 0) or 0)
    notes = [str(note) for note in case.get("extraction_notes", [])]
    default_sources = collect_source_ids(case)
    trace = [
        field_trace("dossier_id", case.get("dossier_id"), source_ids=default_sources, confidence=confidence, notes=notes),
        field_trace("date_reference", case.get("date_reference"), source_ids=default_sources, confidence=confidence, notes=notes),
        field_trace("type_bien", case.get("type_bien"), source_ids=default_sources, confidence=confidence, notes=notes),
        field_trace("zone", case.get("zone"), source_ids=default_sources, confidence=confidence, notes=notes),
        field_trace("surface.value", nested(case, "surface", "value"), source_ids=default_sources, confidence=confidence, notes=notes),
        field_trace("surface.unit", nested(case, "surface", "unit"), source_ids=default_sources, confidence=confidence, notes=notes),
        field_trace("confidence", case.get("confidence"), source_ids=default_sources, confidence=confidence, notes=notes),
    ]

    for index, comp in enumerate(case.get("comparables", []), start=1):
        source_ids = [str(comp.get("source_id"))] if comp.get("source_id") else []
        comp_confidence = float(comp.get("confidence", confidence) or 0)
        prefix = f"comparables[{index}]"
        trace.extend(
            [
                field_trace(f"{prefix}.comparable_id", comp.get("comparable_id"), source_ids=source_ids, confidence=comp_confidence, notes=notes),
                field_trace(f"{prefix}.prix_vente", comp.get("prix_vente"), source_ids=source_ids, confidence=comp_confidence, notes=notes),
                field_trace(f"{prefix}.date_vente", comp.get("date_vente"), source_ids=source_ids, confidence=comp_confidence, notes=notes),
                field_trace(f"{prefix}.distance_km", comp.get("distance_km"), source_ids=source_ids, confidence=comp_confidence, notes=notes),
                field_trace(f"{prefix}.surface.value", nested(comp, "surface", "value"), source_ids=source_ids, confidence=comp_confidence, notes=notes),
                field_trace(f"{prefix}.surface.unit", nested(comp, "surface", "unit"), source_ids=source_ids, confidence=comp_confidence, notes=notes),
            ]
        )

    for index, adjustment in enumerate(case.get("ajustements", []), start=1):
        source_ids = [str(adjustment.get("source_id"))] if adjustment.get("source_id") else []
        prefix = f"ajustements[{index}]"
        trace.extend(
            [
                field_trace(f"{prefix}.ajustement_id", adjustment.get("ajustement_id"), source_ids=source_ids, confidence=confidence, notes=notes),
                field_trace(f"{prefix}.montant", adjustment.get("montant"), source_ids=source_ids, confidence=confidence, notes=notes),
                field_trace(
                    f"{prefix}.validation_humaine",
                    adjustment.get("validation_humaine"),
                    source_ids=source_ids,
                    confidence=confidence,
                    notes=notes,
                    extraction_method="fixture_from_anonymized_pdf_and_human_flag",
                ),
            ]
        )

    if text_stats and int(text_stats.get("masked_token_count", 0) or 0) > 0:
        for item in trace:
            if item["review_status"] == "MACHINE_READY":
                item["review_status"] = "NEEDS_HUMAN_REVIEW"
    return trace


def build_normalized_dossier(case: dict, source_doc: dict[str, object], trace: list[dict[str, object]]) -> dict[str, object]:
    confidence = float(case.get("confidence", 0) or 0)
    missing_fields = [
        field
        for field in ["date_reference", "type_bien", "surface.value", "surface.unit"]
        if nested(case, *field.split(".")) in (None, "", [], {})
    ]
    review_flags = []
    if confidence < 0.60:
        review_flags.append("LOW_CONFIDENCE")
    if any(item.get("value_status") in {"APPROXIMATED", "INFERRED", "MASKED_IN_SOURCE"} for item in trace):
        review_flags.append("TRACE_CONTAINS_INFERRED_OR_APPROXIMATED_VALUES")
    text_stats = source_doc.get("text_stats", {})
    if isinstance(text_stats, dict) and int(text_stats.get("masked_token_count", 0) or 0) > 0:
        review_flags.append("SOURCE_TEXT_CONTAINS_MASKED_VALUES")
    if isinstance(text_stats, dict) and (
        text_stats.get("has_possible_precise_address") or text_stats.get("has_possible_email") or text_stats.get("has_possible_phone")
    ):
        review_flags.append("ANONYMIZATION_REVIEW_REQUIRED")

    return {
        "schema_version": "dossier_normalise_v0",
        "dossier_id": case.get("dossier_id"),
        "anonymization_status": "SOURCE_ANONYMISEE_REQUISE",
        "source_documents": [source_doc],
        "mandate": {
            "date_reference": case.get("date_reference"),
            "type_rapport": case.get("type_rapport", "rapport_evaluation_anonymise"),
            "droits_evalues": case.get("droits_evalues", "NON_EXTRAIT_V0"),
            "review_required": bool(review_flags or missing_fields),
        },
        "subject_property": {
            "type_bien": case.get("type_bien", "NON_EXTRAIT_V0"),
            "zone": case.get("zone", "ANONYMISEE_OU_NON_FOURNIE"),
            "surface": case.get("surface", {}),
            "adresse": "ANONYMISEE_OU_NON_FOURNIE",
        },
        "market_evidence": {
            "comparables": case.get("comparables", []),
        },
        "adjustments": case.get("ajustements", []),
        "hypotheses": case.get("hypotheses", []),
        "timeline": case.get("timeline", []),
        "quality": {
            "confidence": confidence,
            "extraction_notes": case.get("extraction_notes", []),
            "missing_fields": missing_fields,
            "review_flags": sorted(set(review_flags)),
        },
        "traceability": {
            "trace_file": TRACE_NAME,
            "source_index": [{"source_id": source_id} for source_id in collect_source_ids(case)],
        },
    }


def ingest_source(source: SourceInput, case: dict, out_dir: Path, *, text: str | None) -> dict[str, object]:
    text_stats = build_text_stats(text or "") if text is not None else None
    source_doc = source_document_payload(source, text_stats)
    trace = build_trace(case, text_stats)
    dossier = build_normalized_dossier(case, source_doc, trace)
    dossier_dir = out_dir / safe_id(str(case.get("dossier_id") or source.document_id))
    write_json(dossier_dir / NORMALIZED_NAME, dossier)
    write_json(dossier_dir / TRACE_NAME, trace)
    return {
        "document_id": source.document_id,
        "dossier_id": case.get("dossier_id"),
        "status": "NORMALISE",
        "normalized_path": (dossier_dir / NORMALIZED_NAME).as_posix(),
        "trace_path": (dossier_dir / TRACE_NAME).as_posix(),
        "review_flags": dossier["quality"]["review_flags"],
        "missing_fields": dossier["quality"]["missing_fields"],
        "text_stats": text_stats or {},
    }


def run_ingestion(
    sources: list[SourceInput],
    *,
    fixtures_dir: Path,
    out_dir: Path,
    pdftotext_exe: Path | None = None,
    allow_missing_text: bool = False,
    allow_missing_fixture: bool = False,
) -> dict[str, object]:
    cases = load_case_fixtures(fixtures_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, object]] = []
    errors: list[str] = []

    for source in sources:
        if source.pdf_path and source.pdf_path.exists() and source.text_path and not source.text_path.exists() and pdftotext_exe:
            extract_text_with_pdftotext(source.pdf_path, source.text_path, pdftotext_exe)

        text: str | None = None
        if source.text_path and source.text_path.exists():
            text = source.text_path.read_text(encoding="utf-8", errors="replace")
        elif not allow_missing_text:
            errors.append(f"{source.document_id}: texte extrait manquant ({source.text_path})")

        case = match_case(source, cases)
        if case is None:
            message = f"{source.document_id}: fixture active {CASE_PATTERN} manquante"
            if allow_missing_fixture:
                entries.append({"document_id": source.document_id, "status": "FIXTURE_MANQUANTE", "error": message})
                continue
            errors.append(message)
            continue

        if text is None and not allow_missing_text:
            continue
        entries.append(ingest_source(source, case, out_dir, text=text))

    manifest = {
        "schema_version": "ingestion_pdf_v0",
        "generated_at_utc": utc_now_iso(),
        "fixtures_dir": fixtures_dir.as_posix(),
        "out_dir": out_dir.as_posix(),
        "sources_count": len(sources),
        "normalized_count": sum(1 for item in entries if item.get("status") == "NORMALISE"),
        "errors": errors,
        "entries": entries,
    }
    write_json(out_dir / MANIFEST_NAME, manifest)
    (out_dir / REPORT_NAME).write_text(build_markdown_report(manifest), encoding="utf-8")
    if errors:
        raise IngestionError("; ".join(errors))
    return manifest


def build_markdown_report(manifest: dict[str, object]) -> str:
    entries = manifest.get("entries", [])
    errors = manifest.get("errors", [])
    lines = [
        "# Ingestion PDF anonymises v0",
        "",
        f"- Sources analysees: **{manifest.get('sources_count', 0)}**",
        f"- Dossiers normalises: **{manifest.get('normalized_count', 0)}**",
        f"- Erreurs: **{len(errors) if isinstance(errors, list) else 0}**",
        f"- Repertoire sortie: `{manifest.get('out_dir')}`",
        "",
        "## Dossiers",
        "",
        "| Document | Dossier | Statut | Review flags | Champs manquants |",
        "|---|---|---|---|---|",
    ]
    if isinstance(entries, list):
        for item in entries:
            flags = item.get("review_flags", [])
            missing = item.get("missing_fields", [])
            lines.append(
                "| {document} | {dossier} | {status} | {flags} | {missing} |".format(
                    document=item.get("document_id", "-"),
                    dossier=item.get("dossier_id", "-"),
                    status=item.get("status", "-"),
                    flags=", ".join(flags) if isinstance(flags, list) and flags else "-",
                    missing=", ".join(missing) if isinstance(missing, list) and missing else "-",
                )
            )
    lines.extend(["", "## Erreurs", ""])
    if errors:
        for error in errors if isinstance(errors, list) else []:
            lines.append(f"- {error}")
    else:
        lines.append("- Aucune erreur.")
    lines.extend(
        [
            "",
            "## Utilisation",
            "",
            f"- Chaque dossier contient `{NORMALIZED_NAME}` et `{TRACE_NAME}`.",
            "- Les chemins de PDF source complets ne sont pas ecrits dans les artefacts pour limiter les fuites locales.",
            "- Les dossiers generes restent dans `runtime_pilotes_reels/`, donc non versionnes.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def collect_source_ids(case: dict) -> list[str]:
    source_ids: list[str] = []
    for section in ("comparables", "ajustements"):
        for item in case.get(section, []):
            if item.get("source_id"):
                source_ids.append(str(item["source_id"]))
    for hypothesis in case.get("hypotheses", []):
        for source_id in hypothesis.get("source_ids", []):
            source_ids.append(str(source_id))
    return unique(source_ids)


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            out.append(value)
            seen.add(value)
    return out


def nested(data: dict, *keys: str) -> object:
    current: object = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare les dossiers normalises et traces de champs depuis PDF anonymises hors repo.")
    parser.add_argument("--pdf", dest="pdfs", type=Path, action="append", default=[], help="Chemin d'un PDF anonymise. Repetable.")
    parser.add_argument("--fixtures-dir", type=Path, default=FIXTURES_DIR_DEFAULT)
    parser.add_argument("--text-dir", type=Path, default=TEXT_DIR_DEFAULT)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR_DEFAULT)
    parser.add_argument("--pdftotext-exe", type=Path, help="Chemin optionnel vers pdftotext.exe pour generer les .txt manquants.")
    parser.add_argument("--allow-missing-text", action="store_true")
    parser.add_argument("--allow-missing-fixture", action="store_true")
    args = parser.parse_args()

    if args.pdfs:
        sources = discover_source_inputs(args.pdfs, args.text_dir)
    else:
        sources = discover_from_cases(args.fixtures_dir, args.text_dir)

    try:
        manifest = run_ingestion(
            sources,
            fixtures_dir=args.fixtures_dir,
            out_dir=args.out_dir,
            pdftotext_exe=args.pdftotext_exe,
            allow_missing_text=args.allow_missing_text,
            allow_missing_fixture=args.allow_missing_fixture,
        )
    except IngestionError as exc:
        print(f"Ingestion incomplete: {exc}")
        raise SystemExit(1)

    print(f"Manifest ingestion: {args.out_dir / MANIFEST_NAME}")
    print(f"Rapport ingestion: {args.out_dir / REPORT_NAME}")
    print(f"Dossiers normalises: {manifest['normalized_count']}/{manifest['sources_count']}")


if __name__ == "__main__":
    main()
