from __future__ import annotations

from engine.tools import run_calculation, search_comparables


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
    return {
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


def calculate_all_valuation_traces(case: dict) -> dict[str, dict[str, object]]:
    return {
        "approche_comparative": calculate_valuation_trace(case, "approche_comparative"),
        "approche_cout": calculate_valuation_trace(case, "approche_cout"),
        "approche_revenu": calculate_valuation_trace(case, "approche_revenu"),
    }
