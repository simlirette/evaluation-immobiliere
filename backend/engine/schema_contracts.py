from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_SCHEMA_DIR = ROOT / "mvp" / "PIPELINE-IO-SCHEMAS"
KNOWLEDGE_SCHEMA_PATH = ROOT / "schemas" / "knowledge_immobilier_session_v1.schema.json"


def artifact_schema_path(artifact: str) -> Path:
    return ARTIFACT_SCHEMA_DIR / f"{artifact.replace('.json', '')}.schema.json"


@lru_cache(maxsize=64)
def _load_schema(path_text: str) -> dict[str, Any]:
    path = Path(path_text)
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def validate_artifact_schema(artifact: str, payload: dict[str, Any]) -> list[str]:
    path = artifact_schema_path(artifact)
    schema = _load_schema(path.as_posix())
    if not schema:
        return []
    return validate_json_schema(payload, schema)


def validate_knowledge_schema(payload: dict[str, Any]) -> list[str]:
    schema = _load_schema(KNOWLEDGE_SCHEMA_PATH.as_posix())
    if not schema:
        return [f"schema introuvable: {KNOWLEDGE_SCHEMA_PATH.as_posix()}"]
    return validate_json_schema(payload, schema)


def validate_json_schema(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    """Minimal JSON Schema validator for local runtime contracts.

    Supports the subset used by the repo schemas: type, required, properties,
    items, enum, const, minItems, minimum, maximum, and additionalProperties.
    """
    errors: list[str] = []

    expected_type = schema.get("type")
    if expected_type is not None and not _matches_type(value, expected_type):
        errors.append(f"{path}: type attendu {_type_label(expected_type)}, obtenu {_json_type(value)}")
        return errors

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: valeur attendue {schema['const']!r}")

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: valeur non permise {value!r}")

    if isinstance(value, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            for key in required:
                if key not in value:
                    errors.append(f"{path}.{key}: champ requis manquant")

        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for key, child_schema in properties.items():
                if key in value and isinstance(child_schema, dict):
                    errors.extend(validate_json_schema(value[key], child_schema, f"{path}.{key}"))

        if schema.get("additionalProperties") is False and isinstance(properties, dict):
            extra = sorted(set(value) - set(properties))
            for key in extra:
                errors.append(f"{path}.{key}: propriete non declaree")

    if isinstance(value, list):
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            errors.append(f"{path}: au moins {min_items} element(s) requis")

        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(validate_json_schema(item, item_schema, f"{path}[{index}]"))

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if isinstance(minimum, (int, float)) and value < minimum:
            errors.append(f"{path}: valeur inferieure au minimum {minimum}")
        if isinstance(maximum, (int, float)) and value > maximum:
            errors.append(f"{path}: valeur superieure au maximum {maximum}")

    return errors


def _matches_type(value: Any, expected: Any) -> bool:
    if isinstance(expected, list):
        return any(_matches_type(value, item) for item in expected)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def _type_label(expected: Any) -> str:
    if isinstance(expected, list):
        return "|".join(str(item) for item in expected)
    return str(expected)


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    return type(value).__name__
