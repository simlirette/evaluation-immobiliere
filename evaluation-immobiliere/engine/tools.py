from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Comparable:
    comparable_id: str
    prix_vente: float
    source_id: str
    score: float = 0.0


def search_comparables(pool: list[dict], max_items: int = 5) -> list[Comparable]:
    """Stub v0: filtre les comparables sources et les classe par score metier simple."""
    valid = [c for c in pool if c.get("source_id")]
    valid.sort(key=_comparable_score, reverse=True)
    return [
        Comparable(
            comparable_id=str(c.get("comparable_id", "")),
            prix_vente=_to_float(c.get("prix_vente")),
            source_id=str(c.get("source_id", "")),
            score=round(_comparable_score(c), 4),
        )
        for c in valid[:max_items]
    ]


def run_calculation(values: list[float], method: str = "mean", weights: list[float] | None = None) -> float:
    """Stub v0 pour calculs d'approche valeur."""
    numeric_values = [_to_float(v) for v in values]
    if not numeric_values:
        return 0.0
    if method == "mean":
        return sum(numeric_values) / len(numeric_values)
    if method == "median":
        sorted_values = sorted(numeric_values)
        n = len(sorted_values)
        mid = n // 2
        if n % 2 == 1:
            return sorted_values[mid]
        return (sorted_values[mid - 1] + sorted_values[mid]) / 2
    if method == "weighted_mean":
        if not weights or len(weights) != len(numeric_values):
            return sum(numeric_values) / len(numeric_values)
        total_weight = sum(_to_float(w) for w in weights)
        if total_weight <= 0:
            return sum(numeric_values) / len(numeric_values)
        return sum(v * _to_float(w) for v, w in zip(numeric_values, weights)) / total_weight
    return sum(numeric_values) / len(numeric_values)


def validate_schema(payload: dict, required_fields: list[str]) -> tuple[bool, list[str]]:
    missing = [field for field in required_fields if not _has_field(payload, field)]
    return (len(missing) == 0, missing)


def _comparable_score(item: dict) -> float:
    price = _to_float(item.get("prix_vente"))
    distance = _to_float(item.get("distance_km"))
    confidence = _to_float(item.get("confidence", 1.0))
    distance_penalty = min(distance / 100, 0.5) if distance else 0.0
    return max(confidence - distance_penalty, 0.0) + min(price / 1_000_000, 1.0) * 0.01


def _has_field(payload: dict, field: str) -> bool:
    current: object = payload
    for part in field.split("."):
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    return True


def _to_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
