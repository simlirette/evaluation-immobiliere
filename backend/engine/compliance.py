"""engine/compliance.py — Règles de conformité déterministes B001-B007 (S4).

Les règles B (bloquantes) sont calculées en Python pur, sans LLM.
Les avertissements W (non-bloquants) simples sont aussi calculés ici.
Les avertissements W complexes (W004-W005) restent dans le prompt LLM.

Règles B :
  B001  Champs obligatoires manquants (dossier_id, date_reference)
  B002  source_id absent sur un comparable ou ajustement
  B003  Date de vente d'un comparable postérieure à date_reference
  B004  Unités de surface incohérentes entre sujet et comparables
  B005  Ajustement sensible (≥ seuil) sans validation_humaine = True
  B006  valeur_estimee hors plage plausible ou > ±50 % de la moyenne comparables
  B007  Comparable situé au-delà du seuil de distance bloquant

Avertissements W déterministes :
  W001  Confiance globale faible (case["confidence"] < 0.60)
  W002  Comparable éloigné (distance > seuil avertissement, mais < seuil bloquant)
  W003  Hypothèse appuyée par une seule source
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


# ── Constantes par défaut ────────────────────────────────────────────────────

_REQUIRED_CASE_FIELDS = ["dossier_id", "date_reference"]
_B006_MIN = 50_000.0       # $ CAD plancher raisonnable résidentiel Québec
_B006_MAX = 10_000_000.0   # $ CAD plafond raisonnable
_B006_COMP_RATIO_MAX = 2.0 # valeur / moyenne comparables ne doit pas dépasser ce ratio
_B006_COMP_RATIO_MIN = 0.5

_DEFAULT_SENSITIVE_AMOUNT_MIN = 25_000.0  # B005 — ajustement sensible ($)
_DEFAULT_MAX_DISTANCE_WARNING_KM = 30.0   # W002
_DEFAULT_MAX_DISTANCE_BLOCKING_KM = 50.0  # B007


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class ComplianceResult:
    """Résultat d'une règle B individuelle."""

    rule: str           # ex. "B002"
    violated: bool
    explanation_fr: str # message actionnable en français pour l'évaluateur


@dataclass
class ComplianceReport:
    """Rapport agrégé de toutes les vérifications."""

    blocking: list[ComplianceResult] = field(default_factory=list)  # règles B violées
    warnings: list[str] = field(default_factory=list)               # messages W

    @property
    def status(self) -> str:
        if self.blocking:
            return "BLOCKED"
        if self.warnings:
            return "WARNING"
        return "OK"

    @property
    def is_blocked(self) -> bool:
        return bool(self.blocking)

    def blocking_strings(self) -> list[str]:
        """Format compatible avec le pipeline existant : «B002: message»."""
        return [f"{r.rule}: {r.explanation_fr}" for r in self.blocking]


# ── Utilitaire date ───────────────────────────────────────────────────────────

def _parse_date(value: object) -> date | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


# ── Règles B ─────────────────────────────────────────────────────────────────

def check_B001(case: dict) -> ComplianceResult:
    """Champs obligatoires du dossier (dossier_id, date_reference)."""
    missing = [f for f in _REQUIRED_CASE_FIELDS if not case.get(f)]
    violated = bool(missing)
    return ComplianceResult(
        rule="B001",
        violated=violated,
        explanation_fr=(
            f"Champs obligatoires manquants : {', '.join(missing)}. "
            "Complétez le dossier avant de continuer."
            if violated
            else "Champs obligatoires présents."
        ),
    )


def check_B002(case: dict) -> ComplianceResult:
    """source_id absent sur au moins un comparable ou ajustement."""
    missing: list[str] = []
    for i, c in enumerate(case.get("comparables", []), 1):
        if "source_id" not in c:
            missing.append(f"comparable #{i}")
    for i, a in enumerate(case.get("ajustements", []), 1):
        if "source_id" not in a:
            missing.append(f"ajustement #{i}")
    violated = bool(missing)
    return ComplianceResult(
        rule="B002",
        violated=violated,
        explanation_fr=(
            f"source_id absent pour : {', '.join(missing)}. "
            "Ajoutez le numéro de fiche JLR ou la référence Centris avant de continuer."
            if violated
            else "Toutes les sources sont identifiées."
        ),
    )


def check_B003(case: dict) -> ComplianceResult:
    """Date de vente d'un comparable postérieure à date_reference."""
    reference_date = _parse_date(case.get("date_reference"))
    if not reference_date:
        return ComplianceResult(
            rule="B003",
            violated=False,
            explanation_fr="date_reference absente — vérification B003 non applicable (voir B001).",
        )
    future: list[str] = []
    for i, c in enumerate(case.get("comparables", []), 1):
        sale_date = _parse_date(c.get("date_vente"))
        if sale_date and sale_date > reference_date:
            future.append(f"#{i} (vendu le {c.get('date_vente')})")
    violated = bool(future)
    return ComplianceResult(
        rule="B003",
        violated=violated,
        explanation_fr=(
            f"Comparables postérieurs à la date de référence ({case.get('date_reference')}) : "
            f"{', '.join(future)}. Utilisez des ventes antérieures ou ajustez la date de référence."
            if violated
            else "Toutes les dates de vente sont antérieures à la date de référence."
        ),
    )


def check_B004(case: dict) -> ComplianceResult:
    """Unités de surface incohérentes entre le sujet et les comparables."""
    surface = case.get("surface")
    subject_unit = surface.get("unit") if isinstance(surface, dict) else None
    comp_units = {
        c["surface"]["unit"]
        for c in case.get("comparables", [])
        if isinstance(c.get("surface"), dict) and c["surface"].get("unit")
    }
    incoherent_units = comp_units - ({subject_unit} if subject_unit else set())
    violated = bool(subject_unit and incoherent_units)
    return ComplianceResult(
        rule="B004",
        violated=violated,
        explanation_fr=(
            f"Unité de surface incohérente : sujet en «{subject_unit}», "
            f"certains comparables en {sorted(incoherent_units)}. "
            "Convertissez toutes les surfaces dans la même unité."
            if violated
            else "Unités de surface cohérentes."
        ),
    )


def check_B005(
    case: dict,
    sensitive_amount_min: float = _DEFAULT_SENSITIVE_AMOUNT_MIN,
) -> ComplianceResult:
    """Ajustement sensible (≥ seuil $) sans validation_humaine = True."""
    bad: list[str] = [
        f"#{i} ({a.get('montant', '?')} $)"
        for i, a in enumerate(case.get("ajustements", []), 1)
        if float(a.get("montant", 0)) >= sensitive_amount_min
        and not a.get("validation_humaine", False)
    ]
    violated = bool(bad)
    return ComplianceResult(
        rule="B005",
        violated=violated,
        explanation_fr=(
            f"Ajustements ≥ {sensitive_amount_min:,.0f} $ sans validation humaine : "
            f"{', '.join(bad)}. Cochez validation_humaine = true après vérification."
            if violated
            else "Tous les ajustements sensibles ont été validés."
        ),
    )


def check_B006(case: dict) -> ComplianceResult:
    """valeur_estimee hors plage plausible ou déviant de > 50 % des comparables."""
    val = case.get("valeur_estimee")
    if val is None:
        return ComplianceResult(
            rule="B006",
            violated=False,
            explanation_fr="valeur_estimee absente — non vérifiable à cette étape.",
        )
    try:
        val = float(val)
    except (TypeError, ValueError):
        return ComplianceResult(
            rule="B006",
            violated=True,
            explanation_fr=f"valeur_estimee invalide : {val!r}. Doit être un nombre.",
        )

    if val < _B006_MIN or val > _B006_MAX:
        return ComplianceResult(
            rule="B006",
            violated=True,
            explanation_fr=(
                f"valeur_estimee ({val:,.0f} $) hors plage plausible "
                f"[{_B006_MIN:,.0f} $ – {_B006_MAX:,.0f} $]. "
                "Vérifiez les calculs avant de continuer."
            ),
        )

    prices = [float(c["prix_vente"]) for c in case.get("comparables", []) if c.get("prix_vente")]
    if prices:
        mean_price = sum(prices) / len(prices)
        if mean_price > 0 and (
            val < mean_price * _B006_COMP_RATIO_MIN
            or val > mean_price * _B006_COMP_RATIO_MAX
        ):
            return ComplianceResult(
                rule="B006",
                violated=True,
                explanation_fr=(
                    f"valeur_estimee ({val:,.0f} $) dévie de plus de 50 % "
                    f"de la moyenne des comparables ({mean_price:,.0f} $). "
                    "Justifiez l'écart avant de continuer."
                ),
            )

    return ComplianceResult(
        rule="B006",
        violated=False,
        explanation_fr="valeur_estimee dans la plage plausible.",
    )


def check_B007(
    case: dict,
    max_distance_blocking_km: float = _DEFAULT_MAX_DISTANCE_BLOCKING_KM,
) -> ComplianceResult:
    """Comparable situé au-delà du seuil de distance bloquant."""
    far: list[str] = [
        f"#{i} ({c.get('distance_km')} km)"
        for i, c in enumerate(case.get("comparables", []), 1)
        if c.get("distance_km") is not None
        and float(c.get("distance_km", 0)) > max_distance_blocking_km
    ]
    violated = bool(far)
    return ComplianceResult(
        rule="B007",
        violated=violated,
        explanation_fr=(
            f"Comparables hors zone (> {max_distance_blocking_km:.0f} km du sujet) : "
            f"{', '.join(far)}. Remplacez par des comparables de proximité."
            if violated
            else "Tous les comparables sont dans la zone acceptable."
        ),
    )


# ── Avertissements W déterministes ────────────────────────────────────────────

def _compute_warnings(
    case: dict,
    max_distance_warning_km: float = _DEFAULT_MAX_DISTANCE_WARNING_KM,
    max_distance_blocking_km: float = _DEFAULT_MAX_DISTANCE_BLOCKING_KM,
    confidence_min: float = 0.60,
) -> list[str]:
    warnings: list[str] = []

    if case.get("confidence", 1) < confidence_min:
        warnings.append(
            f"W001: Confiance globale faible ({case.get('confidence'):.2f} < {confidence_min}). "
            "Revérifiez les données avant de finaliser l'évaluation."
        )

    for i, c in enumerate(case.get("comparables", []), 1):
        dist = c.get("distance_km")
        if dist is not None:
            dist_f = float(dist)
            if max_distance_warning_km < dist_f <= max_distance_blocking_km:
                warnings.append(
                    f"W002: Comparable #{i} éloigné ({dist_f} km). "
                    "Vérifiez la pertinence géographique."
                )

    for i, h in enumerate(case.get("hypotheses", []), 1):
        if len(h.get("source_ids", [])) < 2:
            warnings.append(
                f"W003: Hypothèse #{i} appuyée par une seule source. "
                "Corroborez avec au moins deux références."
            )

    return warnings


# ── Point d'entrée principal ──────────────────────────────────────────────────

def run_compliance(
    case: dict,
    *,
    sensitive_amount_min: float = _DEFAULT_SENSITIVE_AMOUNT_MIN,
    max_distance_warning_km: float = _DEFAULT_MAX_DISTANCE_WARNING_KM,
    max_distance_blocking_km: float = _DEFAULT_MAX_DISTANCE_BLOCKING_KM,
    confidence_min: float = 0.60,
) -> ComplianceReport:
    """Exécute toutes les règles B001-B007 + avertissements W001-W003.

    Args:
        case: dictionnaire du dossier (case data)
        sensitive_amount_min: seuil B005 en dollars (défaut 25 000 $)
        max_distance_warning_km: seuil W002 en km (défaut 30 km)
        max_distance_blocking_km: seuil B007 en km (défaut 50 km)
        confidence_min: seuil W001 (défaut 0.60)

    Returns:
        ComplianceReport avec blocking (règles B violées), warnings (W), status.
    """
    results = [
        check_B001(case),
        check_B002(case),
        check_B003(case),
        check_B004(case),
        check_B005(case, sensitive_amount_min=sensitive_amount_min),
        check_B006(case),
        check_B007(case, max_distance_blocking_km=max_distance_blocking_km),
    ]
    blocking = [r for r in results if r.violated]
    warnings = _compute_warnings(
        case,
        max_distance_warning_km=max_distance_warning_km,
        max_distance_blocking_km=max_distance_blocking_km,
        confidence_min=confidence_min,
    )
    return ComplianceReport(blocking=blocking, warnings=warnings)
