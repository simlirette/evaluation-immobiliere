from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import date


SCORING_WEIGHTS = {
    "distance": 0.30,
    "recency": 0.25,
    "surface_similarity": 0.20,
    "confidence": 0.15,
    "source_quality": 0.10,
}

SCORING_LIMITS = {
    "max_distance_km": 30.0,
    "max_recency_days": 1095.0,
}

SOURCE_QUALITY = {
    "registre_foncier": 1.0,
    "certificat_localisation": 0.95,
    "role_evaluation_municipale": 0.85,
    "inspection_preachat": 0.80,
    "mls_centris": 0.75,
    "rapport_pdf_anonymise": 0.70,
    "photo_non_geolocalisee": 0.45,
}

# Pondération S6 — scoring comparable JLR (plan 2026-05-20)
JLR_SCORING_WEIGHTS = {
    "surface_similarity": 0.40,
    "recency":            0.30,
    "distance":           0.20,
    "type_match":         0.10,
}


@dataclass
class Comparable:
    comparable_id: str
    prix_vente: float
    source_id: str
    score: float = 0.0
    date_vente: str = ""
    score_details: dict[str, object] = field(default_factory=dict)


def search_comparables(
    pool: list[dict],
    max_items: int = 5,
    *,
    subject: dict | None = None,
    date_reference: str | None = None,
) -> list[Comparable]:
    """Filtre les comparables sources et les classe par score metier explicable."""
    scored = [
        (c, score_comparable(c, subject=subject, date_reference=date_reference))
        for c in pool
        if is_usable_comparable(c)
    ]
    scored.sort(key=lambda item: (float(item[1]["score"]), _comparable_price(item[0])), reverse=True)
    return [
        Comparable(
            comparable_id=str(c.get("comparable_id") or c.get("id") or c.get("source_id") or ""),
            prix_vente=_comparable_price(c),
            source_id=_source_id(c),
            score=round(float(details["score"]), 4),
            date_vente=_sale_date_text(c),
            score_details=details,
        )
        for c, details in scored[:max_items]
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


def score_comparable(
    item: dict,
    *,
    subject: dict | None = None,
    date_reference: str | None = None,
    weights: dict[str, float] | None = None,
    limits: dict[str, float] | None = None,
) -> dict[str, object]:
    """Retourne un score 0..1 avec composantes, poids et penalites explicites."""
    active_weights = weights or SCORING_WEIGHTS
    active_limits = limits or SCORING_LIMITS

    components = {
        "distance": _distance_score(item, active_limits),
        "recency": _recency_score(item, date_reference, active_limits),
        "surface_similarity": _surface_similarity_score(item, subject),
        "confidence": _bounded(_to_float(item.get("confidence", 0.65))),
        "source_quality": _source_quality_score(item),
        "type_match": _type_match_score(item, subject),
    }
    weighted_score = sum(components[key] * active_weights.get(key, 0.0) for key in components)
    penalties = _score_penalties(item, subject=subject, date_reference=date_reference)
    penalty_total = sum(penalties.values())
    final_score = _bounded(weighted_score - penalty_total)
    return {
        "score": round(final_score, 4),
        "weighted_score": round(weighted_score, 4),
        "components": {key: round(value, 4) for key, value in components.items()},
        "weights": active_weights,
        "penalties": {key: round(value, 4) for key, value in penalties.items()},
        "rationale": _score_rationale(components, penalties),
    }


def _comparable_score(item: dict) -> float:
    return float(score_comparable(item)["score"])


def is_usable_comparable(item: dict) -> bool:
    """Comparable usable for value calculations, not just display."""
    return (
        _source_id(item) != ""
        and _comparable_price(item) > 0
        and _parse_iso_date(_sale_date_text(item)) is not None
    )


def _distance_score(item: dict, limits: dict[str, float]) -> float:
    raw = item.get("distance_km")
    distance = _to_float(raw)
    if raw is None:          # distance inconnue → neutre
        return 0.5
    if distance <= 0:        # distance nulle = même secteur → parfait
        return 1.0
    max_distance = max(_to_float(limits.get("max_distance_km")), 1.0)
    return _bounded(1 - min(distance / max_distance, 1.0))


def _recency_score(item: dict, date_reference: str | None, limits: dict[str, float]) -> float:
    sale_date = _parse_iso_date(item.get("date_vente"))
    reference = _parse_iso_date(date_reference)
    if sale_date is None or reference is None:
        return 0.5
    max_days = max(_to_float(limits.get("max_recency_days")), 1.0)
    return _bounded(1 - min(abs((reference - sale_date).days) / max_days, 1.0))


def _surface_similarity_score(item: dict, subject: dict | None) -> float:
    if not subject:
        return 0.5
    subject_surface = subject.get("surface", {}) if isinstance(subject.get("surface"), dict) else {}
    comp_surface = item.get("surface", {}) if isinstance(item.get("surface"), dict) else {}
    subject_value = _to_float(subject_surface.get("value"))
    comp_value = _to_float(comp_surface.get("value"))
    if subject_value <= 0 or comp_value <= 0:
        return 0.5
    if subject_surface.get("unit") and comp_surface.get("unit") and subject_surface.get("unit") != comp_surface.get("unit"):
        return 0.0
    return _bounded(min(subject_value, comp_value) / max(subject_value, comp_value))


def _type_match_score(item: dict, subject: dict | None) -> float:
    """Score 0..1 selon la correspondance type_bien sujet/comparable."""
    if not subject:
        return 0.5
    subj_type = str(subject.get("type_bien") or "").lower().strip()
    comp_type = str(item.get("type_bien") or "").lower().strip()
    if not subj_type or not comp_type:
        return 0.5
    if subj_type == comp_type:
        return 1.0
    # Correspondances partielles (familles de biens)
    _FAMILIES = [
        {"unifamiliale", "maison", "cottage", "jumelé", "jumelé détaché"},
        {"condo", "appartement", "copropriété"},
        {"duplex", "triplex", "plex", "immeuble_revenus"},
        {"commercial", "bureau", "commercial mixte"},
        {"terrain", "lot"},
    ]
    for family in _FAMILIES:
        if any(t in subj_type for t in family) and any(t in comp_type for t in family):
            return 0.7
    return 0.2


def score_justification_fr(score_details: dict) -> str:
    """Résume le score en une phrase française pour l'interface UI CHECKPOINT 2."""
    score = float(score_details.get("score") or score_details.get("weighted_score") or 0)
    components = score_details.get("components") or {}
    rationale = score_details.get("rationale") or []

    if score >= 0.75:
        qualif = "Très pertinent"
    elif score >= 0.55:
        qualif = "Pertinent"
    elif score >= 0.35:
        qualif = "Acceptable"
    else:
        qualif = "Faible pertinence"

    # Composante dominante
    if components:
        strongest = max(components, key=lambda k: components.get(k) or 0)
        label_map = {
            "surface_similarity": "surface similaire",
            "recency":            "vente récente",
            "distance":           "proximité géographique",
            "type_match":         "même type de bien",
            "confidence":         "données de confiance",
            "source_quality":     "source fiable",
        }
        dominant = label_map.get(strongest, strongest)
        return f"{qualif} — {dominant} ({score:.0%})"

    return f"{qualif} ({score:.0%})"


def _source_quality_score(item: dict) -> float:
    source_type = str(item.get("source_type") or item.get("source_quality") or "").strip().lower()
    if source_type in SOURCE_QUALITY:
        return SOURCE_QUALITY[source_type]
    source_id = str(item.get("source_id") or "").upper()
    if "REGISTRE" in source_id:
        return SOURCE_QUALITY["registre_foncier"]
    if "CENTRIS" in source_id or "MLS" in source_id:
        return SOURCE_QUALITY["mls_centris"]
    if "RAPPORT" in source_id or "PDF" in source_id:
        return SOURCE_QUALITY["rapport_pdf_anonymise"]
    return 0.65


def _score_penalties(item: dict, *, subject: dict | None, date_reference: str | None) -> dict[str, float]:
    penalties: dict[str, float] = {}
    if not _source_id(item):
        penalties["missing_source"] = 0.40
    if _comparable_price(item) <= 0:
        penalties["missing_price"] = 0.45
    sale_date = _parse_iso_date(_sale_date_text(item))
    if sale_date is None:
        penalties["missing_sale_date"] = 0.20
    reference = _parse_iso_date(date_reference)
    if sale_date is not None and reference is not None and sale_date > reference:
        penalties["future_sale"] = 0.35
    if subject:
        subject_surface = subject.get("surface", {}) if isinstance(subject.get("surface"), dict) else {}
        comp_surface = item.get("surface", {}) if isinstance(item.get("surface"), dict) else {}
        if subject_surface.get("unit") and comp_surface.get("unit") and subject_surface.get("unit") != comp_surface.get("unit"):
            penalties["unit_mismatch"] = 0.25
    return penalties


def _score_rationale(components: dict[str, float], penalties: dict[str, float]) -> list[str]:
    rationale: list[str] = []
    strongest = max(components, key=components.get)
    weakest = min(components, key=components.get)
    rationale.append(f"Meilleure composante: {strongest}={components[strongest]:.2f}")
    rationale.append(f"Composante la plus faible: {weakest}={components[weakest]:.2f}")
    for name, value in penalties.items():
        rationale.append(f"Penalite {name}: -{value:.2f}")
    return rationale


def _parse_iso_date(value: object) -> date | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _source_id(item: dict) -> str:
    return str(item.get("source_id") or item.get("meta") or "").strip()


def _sale_date_text(item: dict) -> str:
    return str(item.get("date_vente") or item.get("sale_date") or "").strip()


def _comparable_price(item: dict) -> float:
    return _to_float(item.get("prix_vente") if "prix_vente" in item else item.get("sale_price"))


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


def _bounded(value: float) -> float:
    return max(0.0, min(float(value), 1.0))
