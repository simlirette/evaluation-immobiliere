from __future__ import annotations

from engine.tools import run_calculation, search_comparables

# ── S9 — Approches conditionnelles + watermark proxy ─────────────────────────

_PROXY_WARNING = (
    "VALEUR PROXY — {method}(prix_comparables). "
    "Non certifiable OEAQ. "
    "Remplacer par calcul Altus/Marshall Swift avant livraison."
)

# Correspondances type_bien → famille pour applicable_approaches
_FAMILLE_COMPARATIVE_SEULE = {
    "unifamiliale", "maison", "cottage", "jumelé", "jumele",
    "jumelé détaché", "jumele detache", "terrain", "lot",
    "residentiel_unifamilial", "residentiel_rural",
}
_FAMILLE_REVENU = {
    "immeuble_revenus", "duplex", "triplex", "quadruplex",
    "multilogement", "commercial", "bureau",
}


def applicable_approaches(type_bien: str) -> list[str]:
    """Retourne les approches applicables au type de bien (plan S9 2026-05-20).

    Unifamiliale / terrain → comparative uniquement.
    Immeuble à revenus / commercial → comparative + revenu.
    Approche coût toujours proxy (données Altus absentes) → non incluse par défaut.
    """
    t = str(type_bien or "").lower().strip()
    # Normalisation simple des accents
    t_norm = t.replace("é", "e").replace("è", "e").replace("ê", "e")
    if t in _FAMILLE_COMPARATIVE_SEULE or t_norm in _FAMILLE_COMPARATIVE_SEULE:
        return ["approche_comparative"]
    if t in _FAMILLE_REVENU or t_norm in _FAMILLE_REVENU:
        return ["approche_comparative", "approche_revenu"]
    # Défaut OEAQ résidentiel : comparative uniquement
    return ["approche_comparative"]


def calculate_valuation_trace(case: dict, approach: str) -> dict[str, object]:
    """Calcule une approche de valeur en Python deterministe avec trace auditable."""
    comparables = [c.__dict__ for c in search_comparables(case.get("comparables", []), max_items=5, subject=case, date_reference=case.get("date_reference"))]
    prices = [float(c["prix_vente"]) for c in comparables if c.get("prix_vente")]
    weights = [max(float(c.get("score", 0)), 0.01) for c in comparables if c.get("prix_vente")]
    adjustment_total = sum(float(a.get("montant", 0) or 0) for a in case.get("ajustements", []) if a.get("validation_humaine", False))

    if approach == "approche_comparative":
        method = "weighted_mean_score_v0"
        base_value = run_calculation(prices, method="weighted_mean", weights=weights)
    elif approach == "approche_cout":
        method = "proxy_mean_cost_v0"
        base_value = run_calculation(prices, method="mean")
    elif approach == "approche_revenu":
        method = "proxy_median_income_v0"
        base_value = run_calculation(prices, method="median")
    else:
        raise ValueError(f"approche inconnue: {approach}")

    value = round(base_value + adjustment_total, 2) if prices else 0.0
    result: dict[str, object] = {
        "approach": approach,
        "method": method,
        "value": value,
        "input_count": len(prices),
        "trace": {
            "base_value": round(base_value, 2) if prices else 0.0,
            "adjustment_total_validated": round(adjustment_total, 2),
            "selected_comparables": comparables,
            "weights_used": [round(weight, 4) for weight in weights],
            "calculation_policy": [
                "Les comparables sans source_id sont exclus avant calcul.",
                "L'approche comparative utilise une moyenne ponderee par score explicable.",
                "Les approches cout/revenu restent des proxys v0 tant que les tables metier ne sont pas calibrees.",
                "Seuls les ajustements avec validation_humaine=true sont appliques.",
            ],
        },
    }
    # Watermark proxy obligatoire pour cout et revenu (S9)
    if approach in ("approche_cout", "approche_revenu"):
        result["AVERTISSEMENT"] = _PROXY_WARNING.format(method=method)
    return result


def calculate_all_valuation_traces(
    case: dict,
    type_bien: str = "",
) -> dict[str, dict[str, object]]:
    """Calcule les traces pour les approches applicables au type de bien.

    Unifamiliale → approche_comparative uniquement.
    Immeuble à revenus / commercial → comparative + revenu.
    Approches non applicables → {"applicable": False, "value": None}.
    """
    t = type_bien or str(case.get("type_bien") or "")
    applicable = applicable_approaches(t)

    _NOT_APPLICABLE: dict[str, object] = {"applicable": False, "value": None, "input_count": 0}

    return {
        "approche_comparative": calculate_valuation_trace(case, "approche_comparative"),
        "approche_cout": (
            calculate_valuation_trace(case, "approche_cout")
            if "approche_cout" in applicable
            else {**_NOT_APPLICABLE, "approach": "approche_cout"}
        ),
        "approche_revenu": (
            calculate_valuation_trace(case, "approche_revenu")
            if "approche_revenu" in applicable
            else {**_NOT_APPLICABLE, "approach": "approche_revenu"}
        ),
    }
