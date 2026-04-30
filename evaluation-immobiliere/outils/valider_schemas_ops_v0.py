#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels")
SCHEMAS_DIR_DEFAULT = Path("evaluation-immobiliere/schemas/ops")
OUT_JSON_DEFAULT = RUNTIME_DIR_DEFAULT / "schema_validation_report.json"
OUT_MD_DEFAULT = RUNTIME_DIR_DEFAULT / "RAPPORT-SCHEMAS-OPS-V0.md"


@dataclass(frozen=True)
class SchemaTarget:
    name: str
    report_path: str
    schema_path: str


SCHEMA_TARGETS = [
    SchemaTarget("quality", "quality_report.json", "runtime_quality_report_v0.schema.json"),
    SchemaTarget("readiness", "readiness_pre_reponses.json", "readiness_pre_reponses_v0.schema.json"),
    SchemaTarget("registry", "runtime_registry.json", "runtime_registry_v0.schema.json"),
    SchemaTarget("delta", "runtime_delta_report.json", "runtime_delta_report_v0.schema.json"),
    SchemaTarget("handoff", "ops_handoff_manifest.json", "ops_handoff_manifest_v0.schema.json"),
    SchemaTarget("infra_contracts", "infra_contracts_report.json", "infra_contracts_report_v0.schema.json"),
]


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_type(value: object, expected: object) -> bool:
    expected_types = expected if isinstance(expected, list) else [expected]
    for type_name in expected_types:
        if type_name == "object" and isinstance(value, dict):
            return True
        if type_name == "array" and isinstance(value, list):
            return True
        if type_name == "string" and isinstance(value, str):
            return True
        if type_name == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if type_name == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if type_name == "boolean" and isinstance(value, bool):
            return True
        if type_name == "null" and value is None:
            return True
    return False


def validate_schema(value: object, schema: dict[str, object], path: str = "$") -> list[str]:
    failures: list[str] = []
    if "type" in schema and not validate_type(value, schema["type"]):
        failures.append(f"{path}:TYPE:{schema['type']}")
        return failures
    if "const" in schema and value != schema["const"]:
        failures.append(f"{path}:CONST:{schema['const']}")
    if "enum" in schema and value not in schema["enum"]:
        failures.append(f"{path}:ENUM:{schema['enum']}")
    if isinstance(value, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            for key in required:
                if isinstance(key, str) and key not in value:
                    failures.append(f"{path}:REQUIRED:{key}")
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for key, subschema in properties.items():
                if key in value and isinstance(subschema, dict):
                    failures.extend(validate_schema(value[key], subschema, f"{path}.{key}"))
    if isinstance(value, list):
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                failures.extend(validate_schema(item, item_schema, f"{path}[{index}]"))
    return failures


def validate_target(target: SchemaTarget, runtime_dir: Path, schemas_dir: Path) -> dict[str, object]:
    report_path = runtime_dir / target.report_path
    schema_path = schemas_dir / target.schema_path
    failures: list[str] = []
    if not report_path.exists():
        failures.append("REPORT_MISSING")
        return target_result(target, report_path, schema_path, failures)
    if not schema_path.exists():
        failures.append("SCHEMA_MISSING")
        return target_result(target, report_path, schema_path, failures)
    try:
        report = load_json(report_path)
    except json.JSONDecodeError:
        failures.append("REPORT_JSON_INVALID")
        return target_result(target, report_path, schema_path, failures)
    try:
        schema = load_json(schema_path)
    except json.JSONDecodeError:
        failures.append("SCHEMA_JSON_INVALID")
        return target_result(target, report_path, schema_path, failures)
    if not isinstance(schema, dict):
        failures.append("SCHEMA_ROOT_NOT_OBJECT")
    else:
        failures.extend(validate_schema(report, schema))
    return target_result(target, report_path, schema_path, failures)


def target_result(target: SchemaTarget, report_path: Path, schema_path: Path, failures: list[str]) -> dict[str, object]:
    return {
        "name": target.name,
        "report_path": report_path.as_posix(),
        "schema_path": schema_path.as_posix(),
        "ok": not failures,
        "failures": failures,
    }


def build_schema_validation_report(runtime_dir: Path, schemas_dir: Path, targets: list[SchemaTarget] | None = None) -> dict[str, object]:
    checks = [validate_target(target, runtime_dir, schemas_dir) for target in (targets or SCHEMA_TARGETS)]
    failures = [failure for check in checks for failure in check["failures"]]
    return {
        "schema_version": "schema_validation_report_v0",
        "status": "OK" if not failures else "A_CORRIGER",
        "runtime_dir": runtime_dir.as_posix(),
        "schemas_dir": schemas_dir.as_posix(),
        "files_checked": len(checks),
        "files_invalid": sum(1 for check in checks if not check["ok"]),
        "checks": checks,
    }


def build_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Rapport schemas ops v0",
        "",
        f"- Statut: **{report.get('status', 'UNKNOWN')}**",
        f"- Fichiers verifies: **{report.get('files_checked', 0)}**",
        f"- Fichiers invalides: **{report.get('files_invalid', 0)}**",
        "",
        "| Rapport | Statut | Echecs |",
        "|---|---|---|",
    ]
    for check in report.get("checks", []):
        if isinstance(check, dict):
            failures = check.get("failures", [])
            lines.append(
                "| {name} | {status} | {failures} |".format(
                    name=check.get("name", "-"),
                    status="OK" if check.get("ok") else "A_CORRIGER",
                    failures=", ".join(failures) if isinstance(failures, list) and failures else "-",
                )
            )
    return "\n".join(lines).rstrip() + "\n"


def write_report(report: dict[str, object], json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(build_markdown(report), encoding="utf-8")


def run_validation(runtime_dir: Path, schemas_dir: Path, json_out: Path, markdown_out: Path) -> dict[str, object]:
    report = build_schema_validation_report(runtime_dir, schemas_dir)
    write_report(report, json_out, markdown_out)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Valide les rapports ops avec les JSON Schemas versionnes.")
    parser.add_argument("--runtime-dir", type=Path, default=RUNTIME_DIR_DEFAULT)
    parser.add_argument("--schemas-dir", type=Path, default=SCHEMAS_DIR_DEFAULT)
    parser.add_argument("--json-out", type=Path, default=OUT_JSON_DEFAULT)
    parser.add_argument("--markdown-out", type=Path, default=OUT_MD_DEFAULT)
    args = parser.parse_args()

    report = run_validation(args.runtime_dir, args.schemas_dir, args.json_out, args.markdown_out)
    print(f"Validation schemas JSON: {args.json_out}")
    print(f"Validation schemas Markdown: {args.markdown_out}")
    print(f"Statut: {report['status']}")
    return 0 if report["status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
