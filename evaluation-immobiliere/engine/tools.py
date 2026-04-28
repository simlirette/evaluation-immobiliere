from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Comparable:
    comparable_id: str
    prix_vente: float
    source_id: str


def search_comparables(pool: list[dict], max_items: int = 5) -> list[Comparable]:
    """Stub v0: retourne les comparables avec source_id, triés par prix décroissant."""
    valid = [c for c in pool if c.get("source_id")]
    valid.sort(key=lambda x: float(x.get("prix_vente", 0)), reverse=True)
    return [
        Comparable(
            comparable_id=str(c.get("comparable_id", "")),
            prix_vente=float(c.get("prix_vente", 0)),
            source_id=str(c.get("source_id", "")),
        )
        for c in valid[:max_items]
    ]


def run_calculation(values: list[float], method: str = "mean") -> float:
    """Stub v0 pour calculs approche valeur."""
    if not values:
        return 0.0
    if method == "mean":
        return sum(values) / len(values)
    if method == "median":
        sorted_values = sorted(values)
        n = len(sorted_values)
        mid = n // 2
        if n % 2 == 1:
            return sorted_values[mid]
        return (sorted_values[mid - 1] + sorted_values[mid]) / 2
    return sum(values) / len(values)


def validate_schema(payload: dict, required_fields: list[str]) -> tuple[bool, list[str]]:
    missing = [k for k in required_fields if k not in payload]
    return (len(missing) == 0, missing)
