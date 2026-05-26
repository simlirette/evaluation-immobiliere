from __future__ import annotations

from pathlib import Path
import json
import re


def parse_yaml_subset(path: Path) -> dict[str, object]:
    lines = path.read_text(encoding="utf-8").splitlines()
    parsed, index = _parse_block(lines, 0, -1)
    if index < len(lines):
        return dict(parsed) if isinstance(parsed, dict) else {}
    return dict(parsed) if isinstance(parsed, dict) else {}


def render_template(template: str, context: dict[str, object]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        value = context.get(key, "NON_FOURNI")
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        return str(value)

    return re.sub(r"\{\{\s*([^}]+?)\s*\}\}", replace, template)


def _parse_block(lines: list[str], index: int, parent_indent: int) -> tuple[object, int]:
    index = _skip_empty(lines, index)
    if index >= len(lines):
        return {}, index

    first = lines[index]
    if _indent(first) <= parent_indent:
        return {}, index

    if first.strip().startswith("-"):
        items: list[object] = []
        while index < len(lines):
            if not lines[index].strip():
                index += 1
                continue
            indent = _indent(lines[index])
            if indent <= parent_indent:
                break
            stripped = lines[index].strip()
            if not stripped.startswith("-"):
                break
            items.append(_parse_scalar(stripped[1:].strip()))
            index += 1
        return items, index

    data: dict[str, object] = {}
    while index < len(lines):
        raw = lines[index]
        if not raw.strip():
            index += 1
            continue
        indent = _indent(raw)
        if indent <= parent_indent:
            break
        stripped = raw.strip()
        if ":" not in stripped:
            index += 1
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value in {"|", ">"}:
            block, index = _collect_block_scalar(lines, index + 1, indent)
            data[key] = block
            continue
        if value == "":
            child, index = _parse_block(lines, index + 1, indent)
            data[key] = child
            continue
        data[key] = _parse_scalar(value)
        index += 1
    return data, index


def _collect_block_scalar(lines: list[str], index: int, parent_indent: int) -> tuple[str, int]:
    block_lines: list[str] = []
    base_indent: int | None = None
    while index < len(lines):
        raw = lines[index]
        if raw.strip():
            indent = _indent(raw)
            if indent <= parent_indent:
                break
            if base_indent is None:
                base_indent = indent
            block_lines.append(raw[min(base_indent, len(raw)) :])
        else:
            block_lines.append("")
        index += 1
    return "\n".join(block_lines).rstrip(), index


def _skip_empty(lines: list[str], index: int) -> int:
    while index < len(lines) and not lines[index].strip():
        index += 1
    return index


def _indent(raw: str) -> int:
    return len(raw) - len(raw.lstrip(" "))


def _parse_scalar(value: str) -> object:
    if value in {"true", "false"}:
        return value == "true"
    if value == "null":
        return None
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, str) and value:
        return [value]
    return []


def as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def as_optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            out.append(value)
            seen.add(value)
    return out


def handoff_string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, str) and value:
        return [value]
    return []


_as_list = as_list
_as_dict = as_dict
_as_optional_int = as_optional_int
_unique = unique
_handoff_string_list = handoff_string_list
