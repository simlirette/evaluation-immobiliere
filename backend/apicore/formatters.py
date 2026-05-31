"""api/formatters.py — Fonctions de formatage et utilitaires purs (T6.1).

Aucune dépendance sur SESSIONS_DIR ou modules engine.
Extrait de api.py (T6.1 — découpe api.py).
"""
from __future__ import annotations

from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def utc_now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def bounded_limit(value: str, default: int = 50, maximum: int = 100) -> int:
    try:
        n = int(value)
        return max(1, min(n, maximum))
    except (TypeError, ValueError):
        return default


def app_money(value: object) -> str:
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return "-"
    return f"{amount:,.0f} $".replace(",", " ")


def app_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def app_is_iso_date(value: object) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def app_date_label(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    return parsed.date().isoformat()


def app_surface_label(surface: object) -> str:
    if not isinstance(surface, dict):
        return "-"
    value = surface.get("value")
    unit = surface.get("unit") or ""
    if value in (None, ""):
        return "-"
    return f"{value} {unit}".strip()


def app_property_type_label(raw: object) -> str:
    value = str(raw or "").strip()
    labels = {
        "residentiel_unifamilial": "Residentiel unifamilial",
        "residentiel": "Residentiel",
        "commercial": "Commercial",
        "multilogement": "Multilogement",
    }
    return labels.get(value, value.replace("_", " ").title() if value else "Type a confirmer")


def app_status_label(record: dict) -> str:
    if record.get("package_status") == "PRET_REVUE_EVALUATEUR_AGREE":
        return "complet"
    status = str(record.get("status") or "")
    if status in {"PRET_REVISION_FINALE", "A_REVOIR"}:
        return "en-cours"
    return "brouillon"
