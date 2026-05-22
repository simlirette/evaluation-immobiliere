from __future__ import annotations

import unicodedata
from datetime import date
from typing import Any

from engine.tools import is_usable_comparable, run_calculation, search_comparables


_COMPARATIVE_ONLY = {
    "terrain", "lot", "terrain_vacant", "lot_vacant", "terrain_developpement",
    "terrain_agricole",
}
_RESIDENTIAL_COST = {
    "unifamiliale", "unifamilial", "maison", "cottage", "bungalow", "condo",
    "condominium", "jumele", "jumel", "jumel detache", "residentiel_unifamilial",
    "residentiel_rural",
}
_MULTI_REVENUE = {
    "duplex", "triplex", "quadruplex", "quintuplex", "plex",
    "residentiel_multifamilial",
}
_INCOME_TYPES = {
    "immeuble_revenus", "immeuble_locatif", "multilogement", "multiresidentiel",
    "grand_multiresidentiel", "commercial_revenus", "commercial_generateur",
}
_COST_TYPES = _RESIDENTIAL_COST | {
    "commercial", "bureau", "bureaux", "magasin", "commerce", "centre_commercial",
    "local_commercial", "institutionnel", "industriel", "entrepot", "manufacture",
    "usine", "parc_industriel",
}

_DEFAULT_COST_PER_M2 = {
    "residential": 2400.0,
    "multifamily": 2600.0,
    "commercial": 3000.0,
    "industrial": 2200.0,
}
_DEFAULT_CAP_RATE = {
    "duplex": 0.050,
    "triplex": 0.0525,
    "quadruplex": 0.055,
    "multifamily": 0.0575,
    "commercial": 0.065,
    "industrial": 0.0675,
    "default": 0.060,
}

_INSUFFICIENT_COMPARABLES_WARNING = (
    "AUCUN COMPARABLE DISPONIBLE - valeur calculee nulle. "
    "Importer et confirmer des comparables avant de generer le rapport."
)
_INSUFFICIENT_COST_WARNING = (
    "DONNEES COUT INSUFFISANTES - fournir au minimum une superficie batiment "
    "et un cout unitaire ou cout neuf total verifiable."
)
_INSUFFICIENT_INCOME_WARNING = (
    "DONNEES REVENU INSUFFISANTES - fournir revenus, depenses et taux de "
    "capitalisation, ou une projection FTA complete."
)


def applicable_approaches(type_bien: str) -> list[str]:
    """Return default valuation approaches for a property type.

    The mandate plan may override these defaults through case["methodes_requises"].
    """
    t = _normalize_type(type_bien)
    if t in _COMPARATIVE_ONLY:
        return ["approche_comparative"]
    if t in _INCOME_TYPES:
        return ["approche_revenu", "approche_comparative"]
    if t in _MULTI_REVENUE:
        return ["approche_comparative", "approche_revenu"]
    if t in _COST_TYPES:
        return ["approche_comparative", "approche_cout"]
    return ["approche_comparative"]


def approaches_for_case(case: dict) -> list[str]:
    """Return valuation approaches required by the case or inferred by type."""
    explicit = case.get("methodes_requises")
    if isinstance(explicit, list):
        seen: set[str] = set()
        ordered: list[str] = []
        for approach in explicit:
            approach_id = str(approach or "").strip()
            if approach_id in {
                "approche_comparative",
                "approche_cout",
                "approche_revenu",
            } and approach_id not in seen:
                seen.add(approach_id)
                ordered.append(approach_id)
        if ordered:
            return ordered
    mandat_type = _normalize_type(case.get("mandat_type"))
    if mandat_type == "assurance":
        return ["approche_cout"]
    return applicable_approaches(str(case.get("type_bien") or ""))


def calculate_valuation_trace(case: dict, approach: str) -> dict[str, object]:
    """Calculate one valuation approach with an auditable deterministic trace."""
    if approach == "approche_comparative":
        return _calculate_comparative_approach(case)
    if approach == "approche_cout":
        return calculate_cost_approach(case)
    if approach == "approche_revenu":
        if _has_fta_inputs(case):
            return calculate_fta_approach(case)
        return calculate_income_approach(case)
    raise ValueError(f"approche inconnue: {approach}")


def calculate_all_valuation_traces(
    case: dict,
    type_bien: str = "",
) -> dict[str, dict[str, object]]:
    """Calculate traces for required/default approaches; mark others not applicable."""
    case_for_selection = dict(case)
    if type_bien:
        case_for_selection["type_bien"] = type_bien
        case_for_selection.pop("methodes_requises", None)
    applicable = set(approaches_for_case(case_for_selection))
    not_applicable: dict[str, object] = {
        "applicable": False,
        "value": None,
        "input_count": 0,
        "calculation_status": "NOT_APPLICABLE",
    }

    return {
        "approche_comparative": (
            calculate_valuation_trace(case, "approche_comparative")
            if "approche_comparative" in applicable
            else {**not_applicable, "approach": "approche_comparative"}
        ),
        "approche_cout": (
            calculate_valuation_trace(case, "approche_cout")
            if "approche_cout" in applicable
            else {**not_applicable, "approach": "approche_cout"}
        ),
        "approche_revenu": (
            calculate_valuation_trace(case, "approche_revenu")
            if "approche_revenu" in applicable
            else {**not_applicable, "approach": "approche_revenu"}
        ),
    }


def calculate_cost_approach(case: dict) -> dict[str, object]:
    """Replacement cost less depreciation plus land value."""
    ref = _as_dict(case.get("couts_reference"))
    type_bien = _normalize_type(case.get("type_bien"))
    surface_m2 = _surface_m2(case)
    total_cost_new_explicit = _first_float(ref, ["cout_neuf_total", "cout_remplacement_total"])
    unit_cost_m2 = _cost_unit_m2(case, ref, type_bien)
    inputs_used: list[str] = []
    warnings: list[str] = []

    if total_cost_new_explicit > 0:
        cost_base = total_cost_new_explicit
        inputs_used.append("cout_neuf_total")
    elif surface_m2 > 0 and unit_cost_m2 > 0:
        cost_base = surface_m2 * unit_cost_m2
        inputs_used.extend(["surface_m2", "cout_unitaire_m2"])
    else:
        return {
            "approach": "approche_cout",
            "method": "replacement_cost_less_depreciation_v1",
            "value": None,
            "input_count": 0,
            "calculation_status": "INSUFFICIENT_COST_DATA",
            "trace": {
                "surface_m2": round(surface_m2, 2) if surface_m2 else None,
                "cout_unitaire_m2": unit_cost_m2 or None,
                "required_inputs": ["surface_m2", "cout_unitaire_m2 ou cout_neuf_total"],
            },
            "AVERTISSEMENT": _INSUFFICIENT_COST_WARNING,
        }

    factors = _cost_factors(ref, type_bien)
    factor_product = 1.0
    for value in factors.values():
        factor_product *= value
    cost_new = cost_base * factor_product
    depreciation_pct = _depreciation_pct(case)
    inputs_used.append("depreciation_pct")

    is_insurance = _is_insurance_mandate(case)
    if is_insurance:
        depreciated_building = cost_new
        depreciation_amount = 0.0
        land_value = 0.0
        method = "replacement_cost_insurance_v1"
        calculation_status = "OK"
    else:
        depreciation_amount = cost_new * depreciation_pct / 100.0
        depreciated_building = max(cost_new - depreciation_amount, 0.0)
        land_value, land_source = _land_value(case, ref)
        if land_value > 0:
            inputs_used.append(land_source)
            calculation_status = "OK"
        else:
            warnings.append("valeur_terrain_absente")
            calculation_status = "PARTIAL_MISSING_LAND_VALUE"
        method = "replacement_cost_less_depreciation_v1"

    value = depreciated_building + land_value
    result: dict[str, object] = {
        "approach": "approche_cout",
        "method": method,
        "value": round(value, 2),
        "input_count": len(set(inputs_used)),
        "calculation_status": calculation_status,
        "trace": {
            "surface_m2": round(surface_m2, 2) if surface_m2 else None,
            "cout_base": round(cost_base, 2),
            "cout_unitaire_m2": round(unit_cost_m2, 2) if unit_cost_m2 else None,
            "facteurs": factors,
            "facteur_total": round(factor_product, 6),
            "cout_neuf": round(cost_new, 2),
            "taux_depreciation_pct": round(depreciation_pct, 2),
            "depreciation": round(depreciation_amount, 2),
            "valeur_batiment_depreciee": round(depreciated_building, 2),
            "valeur_terrain": round(land_value, 2),
            "mandat_assurance": is_insurance,
            "warnings": warnings,
            "calculation_policy": [
                "Valeur cout = terrain + cout neuf ajuste moins depreciation.",
                "Mandat assurance: le terrain et la depreciation sont exclus; cout de remplacement neuf.",
                "Les facteurs explicites fournis au dossier priment les valeurs par defaut.",
            ],
        },
    }
    if warnings:
        result["AVERTISSEMENT"] = "Approche cout partielle: " + ", ".join(warnings)
    return result


def calculate_income_approach(case: dict) -> dict[str, object]:
    """Direct capitalization of stabilized net operating income."""
    income = _income_inputs(case)
    if income["noi"] <= 0 or income["cap_rate"] <= 0 or not income["has_revenue"]:
        return {
            "approach": "approche_revenu",
            "method": "direct_capitalization_v1",
            "value": None,
            "input_count": int(income["input_count"]),
            "calculation_status": "INSUFFICIENT_INCOME_DATA",
            "trace": income,
            "AVERTISSEMENT": _INSUFFICIENT_INCOME_WARNING,
        }

    value = income["noi"] / income["cap_rate"]
    return {
        "approach": "approche_revenu",
        "method": "direct_capitalization_v1",
        "value": round(value, 2),
        "input_count": int(income["input_count"]),
        "calculation_status": "OK",
        "trace": {
            **income,
            "value_formula": "RNE / taux_capitalisation",
            "calculation_policy": [
                "RBP moins vacance = RBE.",
                "RBE moins depenses = RNE.",
                "Valeur par capitalisation directe = RNE / TGA.",
            ],
        },
    }


def calculate_fta_approach(case: dict) -> dict[str, object]:
    """Discounted cash-flow / FTA model used inside the income approach."""
    cfg = _fta_config(case)
    flows = _fta_cash_flows(cfg)
    discount_rate = _rate(
        _first_float(cfg, ["taux_actualisation_pct", "discount_rate_pct", "taux_escompte_pct"])
    )
    exit_cap_rate = _rate(
        _first_float(cfg, ["taux_capitalisation_sortie_pct", "exit_cap_rate_pct", "exit_cap_pct"])
    )
    terminal_growth = _rate(
        _first_float(cfg, ["croissance_terminale_pct", "terminal_growth_pct", "croissance_terminal_pct"])
    )

    if not flows or discount_rate <= 0 or exit_cap_rate <= 0:
        return {
            "approach": "approche_revenu",
            "method": "fta_dcf_v1",
            "value": None,
            "input_count": len(flows),
            "calculation_status": "INSUFFICIENT_FTA_DATA",
            "trace": {
                "cash_flows": flows,
                "taux_actualisation": discount_rate,
                "taux_capitalisation_sortie": exit_cap_rate,
                "required_inputs": [
                    "flux annuels ou rne_initial",
                    "taux_actualisation_pct",
                    "taux_capitalisation_sortie_pct",
                ],
            },
            "AVERTISSEMENT": _INSUFFICIENT_INCOME_WARNING,
        }

    discounted_flows: list[dict[str, float | int]] = []
    pv_flows = 0.0
    for idx, noi in enumerate(flows, 1):
        discount_factor = 1.0 / ((1.0 + discount_rate) ** idx)
        present_value = noi * discount_factor
        pv_flows += present_value
        discounted_flows.append({
            "year": idx,
            "rne": round(noi, 2),
            "discount_factor": round(discount_factor, 6),
            "present_value": round(present_value, 2),
        })

    terminal_noi = flows[-1] * (1.0 + terminal_growth)
    terminal_value = terminal_noi / exit_cap_rate
    terminal_discount_factor = 1.0 / ((1.0 + discount_rate) ** len(flows))
    pv_terminal = terminal_value * terminal_discount_factor
    value = pv_flows + pv_terminal

    return {
        "approach": "approche_revenu",
        "method": "fta_dcf_v1",
        "value": round(value, 2),
        "input_count": len(flows) + 2,
        "calculation_status": "OK",
        "trace": {
            "projection_years": len(flows),
            "cash_flows": discounted_flows,
            "taux_actualisation": round(discount_rate, 6),
            "taux_capitalisation_sortie": round(exit_cap_rate, 6),
            "croissance_terminale": round(terminal_growth, 6),
            "terminal_noi": round(terminal_noi, 2),
            "terminal_value": round(terminal_value, 2),
            "terminal_discount_factor": round(terminal_discount_factor, 6),
            "pv_cash_flows": round(pv_flows, 2),
            "pv_terminal": round(pv_terminal, 2),
            "value_formula": "somme VP(RNE annuels) + VP(valeur terminale)",
            "calculation_policy": [
                "FTA utilise les flux RNE explicites ou une projection depuis RNE initial.",
                "Valeur terminale = RNE(N+1) / taux de sortie.",
                "Chaque flux et la valeur terminale sont actualises au taux fourni.",
            ],
        },
    }


def _calculate_comparative_approach(case: dict) -> dict[str, object]:
    raw_pool = [c for c in case.get("comparables", []) if isinstance(c, dict)]
    comparables = [
        c.__dict__
        for c in search_comparables(
            raw_pool,
            max_items=5,
            subject=case,
            date_reference=case.get("date_reference"),
        )
    ]
    prices = [
        _to_float(c.get("prix_vente"))
        for c in comparables
        if _to_float(c.get("prix_vente")) > 0
    ]
    weights = [
        max(_to_float(c.get("score")), 0.01)
        for c in comparables
        if _to_float(c.get("prix_vente")) > 0
    ]
    adjustment_total = sum(
        _to_float(a.get("montant"))
        for a in case.get("ajustements", [])
        if isinstance(a, dict) and a.get("validation_humaine", False) is True
    )
    invalid_comparable_count = sum(1 for c in raw_pool if not is_usable_comparable(c))
    base_value = run_calculation(prices, method="weighted_mean", weights=weights)
    value = round(base_value + adjustment_total, 2) if prices else 0.0
    result: dict[str, object] = {
        "approach": "approche_comparative",
        "method": "weighted_mean_score_v1",
        "value": value,
        "input_count": len(prices),
        "calculation_status": "OK" if prices else "INSUFFICIENT_COMPARABLES",
        "excluded_comparable_count": invalid_comparable_count,
        "trace": {
            "base_value": round(base_value, 2) if prices else 0.0,
            "adjustment_total_validated": round(adjustment_total, 2),
            "selected_comparables": comparables,
            "weights_used": [round(weight, 4) for weight in weights],
            "calculation_policy": [
                "Les comparables sans source_id sont exclus avant calcul.",
                "Les comparables sans prix de vente positif ou date_vente ISO valide sont exclus avant calcul.",
                "L'approche comparative utilise une moyenne ponderee par score explicable.",
                "Seuls les ajustements avec validation_humaine=true sont appliques.",
            ],
        },
    }
    if not prices:
        result["AVERTISSEMENT"] = _INSUFFICIENT_COMPARABLES_WARNING
    return result


def _income_inputs(case: dict) -> dict[str, Any]:
    source = _as_dict(case.get("revenus_depenses"))
    market = _as_dict(case.get("marche_locatif"))
    input_count = 0
    notes: list[str] = []

    potential_revenue = _first_float(source, [
        "revenu_brut_potentiel",
        "revenus_bruts_potentiels",
        "rbp",
        "revenu_brut_annuel",
        "revenus_annuels",
        "revenu_annuel",
        "gross_potential_income",
    ])
    if potential_revenue > 0:
        input_count += 1
    else:
        monthly_rent = _first_float(source, ["loyer_mensuel_total", "loyer_total_mensuel"])
        if monthly_rent <= 0:
            monthly_rent = _first_float(market, ["loyer_moyen_total", "loyer_median_total"])
        units = _to_float(case.get("nb_logements") or source.get("nb_logements"), 1.0)
        if monthly_rent > 0:
            potential_revenue = monthly_rent * max(units, 1.0) * 12.0
            input_count += 1
            notes.append("revenu_brut_projete_depuis_loyer_mensuel")

    effective_revenue = _first_float(source, [
        "revenu_brut_effectif",
        "rbe",
        "effective_gross_income",
    ])
    vacancy_pct = _first_float(source, ["taux_vacance_pct", "vacance_pct"])
    if vacancy_pct <= 0:
        vacancy_pct = _first_float(_as_dict(case.get("taux_inoccupation")), ["taux_total_pct"])
    if vacancy_pct <= 0:
        vacancy_pct = 5.0
        notes.append("taux_vacance_defaut_5pct")
    else:
        input_count += 1

    if effective_revenue <= 0 and potential_revenue > 0:
        effective_revenue = potential_revenue * (1.0 - _pct(vacancy_pct))

    expenses_total = _expenses_total(source)
    expense_ratio_pct = _first_float(source, ["ratio_depenses_pct", "expense_ratio_pct"])
    if expenses_total > 0:
        input_count += 1
    elif effective_revenue > 0:
        if expense_ratio_pct <= 0:
            expense_ratio_pct = 35.0
            notes.append("ratio_depenses_defaut_35pct")
        expenses_total = effective_revenue * _pct(expense_ratio_pct)

    noi = _first_float(source, [
        "revenu_net_exploitation",
        "rne",
        "noi",
        "net_operating_income",
    ])
    if noi > 0:
        input_count += 1
    elif effective_revenue > 0:
        noi = effective_revenue - expenses_total

    cap_rate_pct = _first_float(source, [
        "taux_capitalisation_pct",
        "tga_pct",
        "cap_rate_pct",
        "taux_global_actualisation_pct",
    ])
    if cap_rate_pct > 0:
        input_count += 1
    else:
        cap_rate_pct = _default_cap_rate_pct(case)
        notes.append("taux_capitalisation_defaut_par_type")

    return {
        "revenu_brut_potentiel": round(potential_revenue, 2) if potential_revenue else 0.0,
        "taux_vacance_pct": round(vacancy_pct, 2),
        "revenu_brut_effectif": round(effective_revenue, 2) if effective_revenue else 0.0,
        "depenses_exploitation": round(expenses_total, 2) if expenses_total else 0.0,
        "ratio_depenses_pct": round(expense_ratio_pct, 2) if expense_ratio_pct else None,
        "rne": round(noi, 2) if noi else 0.0,
        "taux_capitalisation_pct": round(cap_rate_pct, 3),
        "cap_rate": _rate(cap_rate_pct),
        "noi": noi,
        "has_revenue": potential_revenue > 0 or effective_revenue > 0 or noi > 0,
        "input_count": input_count,
        "notes": notes,
    }


def _expenses_total(source: dict[str, Any]) -> float:
    total = _first_float(source, [
        "depenses_exploitation",
        "depenses_totales",
        "total_depenses",
        "operating_expenses",
    ])
    if total > 0:
        return total
    depenses = source.get("depenses")
    if isinstance(depenses, dict):
        return sum(_to_float(v) for v in depenses.values())
    if isinstance(depenses, list):
        return sum(_to_float(item.get("montant")) for item in depenses if isinstance(item, dict))
    return 0.0


def _has_fta_inputs(case: dict) -> bool:
    cfg = _fta_config(case)
    return bool(cfg)


def _fta_config(case: dict) -> dict[str, Any]:
    for key in ("fta", "flux_tresorerie", "dcf", "projection_fta"):
        value = case.get(key)
        if isinstance(value, dict) and value:
            return value
    rd = _as_dict(case.get("revenus_depenses"))
    for key in ("fta", "flux_tresorerie", "dcf", "projection_fta"):
        value = rd.get(key)
        if isinstance(value, dict) and value:
            return value
    return {}


def _fta_cash_flows(cfg: dict[str, Any]) -> list[float]:
    for key in ("flux", "cash_flows", "rne_annuels"):
        raw_flows = cfg.get(key)
        flows = _parse_flows(raw_flows)
        if flows:
            return flows

    initial_noi = _first_float(cfg, [
        "rne_initial",
        "noi_initial",
        "revenu_net_initial",
        "annee_1_rne",
    ])
    years = int(_first_float(cfg, ["projection_years", "duree_projection_ans", "horizon_ans"]) or 0)
    growth_pct = _first_float(cfg, ["croissance_rne_pct", "croissance_revenus_pct", "noi_growth_pct"])
    if initial_noi <= 0 or years <= 0:
        return []
    years = max(1, min(years, 30))
    return [initial_noi * ((1.0 + _pct(growth_pct)) ** idx) for idx in range(years)]


def _parse_flows(raw_flows: Any) -> list[float]:
    if not isinstance(raw_flows, list):
        return []
    flows: list[float] = []
    for item in raw_flows:
        if isinstance(item, dict):
            value = _first_float(item, ["rne", "noi", "cash_flow", "flux_net"])
        else:
            value = _to_float(item)
        if value > 0:
            flows.append(value)
    return flows


def _surface_m2(case: dict) -> float:
    for key in ("surface_habitable", "superficie_batiment_m2", "hab_m2"):
        value = _to_float(case.get(key))
        if value > 0:
            return value
    role = _as_dict(case.get("role_municipal"))
    for key in ("superficie_batiment_m2", "surface_habitable"):
        value = _to_float(role.get(key))
        if value > 0:
            return value

    surface = case.get("surface")
    if isinstance(surface, dict):
        value = _to_float(surface.get("value"))
        unit = _normalize_type(surface.get("unit"))
        if value <= 0:
            return 0.0
        if unit in {"pi2", "pi", "ft2", "sqft", "pied2", "pieds2"}:
            return value * 0.09290304
        return value
    return _to_float(surface)


def _cost_unit_m2(case: dict, ref: dict[str, Any], type_bien: str) -> float:
    unit_m2 = _first_float(ref, [
        "cout_unitaire_m2",
        "cout_neuf_m2",
        "cout_base_m2",
        "cout_remplacement_m2",
        "replacement_cost_m2",
    ])
    if unit_m2 > 0:
        return unit_m2
    unit_pi2 = _first_float(ref, ["cout_unitaire_pi2", "cout_neuf_pi2", "replacement_cost_sqft"])
    if unit_pi2 > 0:
        return unit_pi2 / 0.09290304
    if ref.get("allow_default_cost_reference") is True:
        return _DEFAULT_COST_PER_M2[_cost_family(type_bien)]
    return 0.0


def _cost_factors(ref: dict[str, Any], type_bien: str) -> dict[str, float]:
    raw_factors = _as_dict(ref.get("facteurs") or ref.get("factors"))
    defaults = {
        "temps": 1.0,
        "taxes": 1.0,
        "envergure": 1.0,
        "classe": 1.0,
        "economique": 1.0,
    }
    if raw_factors:
        return {
            key: max(_to_float(raw_factors.get(key), default), 0.0)
            for key, default in defaults.items()
        }

    family = _cost_family(type_bien)
    if family == "residential":
        defaults["temps"] = _to_float(ref.get("facteur_temps"), 1.0)
        defaults["taxes"] = _to_float(ref.get("facteur_taxes"), 1.0)
    elif family == "commercial":
        defaults["envergure"] = _to_float(ref.get("facteur_envergure"), 1.0)
    return defaults


def _depreciation_pct(case: dict) -> float:
    ref = _as_dict(case.get("couts_reference"))
    explicit = _first_float(ref, ["taux_depreciation_pct", "depreciation_pct"])
    if explicit <= 0:
        explicit = _first_float(case, ["taux_depreciation_pct", "depreciation_pct"])
    if explicit <= 0:
        vetuste = _as_dict(case.get("vetuste_batiment"))
        explicit = _first_float(vetuste, ["taux_depreciation_pct", "depreciation_pct"])
    if explicit > 0:
        return min(max(explicit, 0.0), 95.0)

    year = int(_first_float(case, ["annee_construction", "year_built"]) or 0)
    if year <= 0:
        role = _as_dict(case.get("role_municipal"))
        year = int(_first_float(role, ["annee_construction", "year_built"]) or 0)
    if year <= 0:
        return 0.0
    ref_year = _reference_year(case)
    age = max(ref_year - year, 0)
    economic_life = _first_float(ref, ["vie_economique_ans", "economic_life_years"]) or 80.0
    return min(max(age / economic_life * 100.0, 0.0), 80.0)


def _land_value(case: dict, ref: dict[str, Any]) -> tuple[float, str]:
    value = _first_float(ref, ["valeur_terrain", "land_value", "site_value"])
    if value > 0:
        return value, "valeur_terrain"
    role = _as_dict(case.get("role_municipal"))
    value = _first_float(role, ["valeur_terrain", "land_value", "site_value"])
    if value > 0:
        return value, "role_municipal.valeur_terrain"
    unit = _first_float(ref, ["valeur_terrain_m2", "land_value_m2"])
    area = _land_area_m2(case)
    if unit > 0 and area > 0:
        return unit * area, "valeur_terrain_m2"
    return 0.0, "valeur_terrain_absente"


def _land_area_m2(case: dict) -> float:
    for key in ("terrain_m2", "superficie_terrain_m2", "surface_terrain"):
        value = _to_float(case.get(key))
        if value > 0:
            return value
    role = _as_dict(case.get("role_municipal"))
    return _first_float(role, ["superficie_terrain_m2", "surface_terrain"])


def _default_cap_rate_pct(case: dict) -> float:
    t = _normalize_type(case.get("type_bien"))
    if t in {"duplex"}:
        return _DEFAULT_CAP_RATE["duplex"] * 100.0
    if t in {"triplex"}:
        return _DEFAULT_CAP_RATE["triplex"] * 100.0
    if t in {"quadruplex", "quintuplex", "plex", "residentiel_multifamilial"}:
        return _DEFAULT_CAP_RATE["quadruplex"] * 100.0
    if t in _INCOME_TYPES:
        return _DEFAULT_CAP_RATE["multifamily"] * 100.0
    if t in {"commercial", "bureau", "commerce", "centre_commercial", "local_commercial"}:
        return _DEFAULT_CAP_RATE["commercial"] * 100.0
    if t in {"industriel", "entrepot", "manufacture", "usine"}:
        return _DEFAULT_CAP_RATE["industrial"] * 100.0
    return _DEFAULT_CAP_RATE["default"] * 100.0


def _cost_family(type_bien: str) -> str:
    if type_bien in _INCOME_TYPES or type_bien in _MULTI_REVENUE:
        return "multifamily"
    if type_bien in {"commercial", "bureau", "bureaux", "commerce", "magasin", "centre_commercial", "local_commercial", "institutionnel"}:
        return "commercial"
    if type_bien in {"industriel", "entrepot", "manufacture", "usine", "parc_industriel"}:
        return "industrial"
    return "residential"


def _is_insurance_mandate(case: dict) -> bool:
    mandat = _normalize_type(case.get("mandat_type"))
    purpose = _normalize_type(case.get("but_evaluation") or case.get("fin_evaluation"))
    cmd = _as_dict(case.get("commanditaire"))
    cmd_purpose = _normalize_type(cmd.get("fin_evaluation"))
    return "assurance" in {mandat, purpose, cmd_purpose} or "assurance" in purpose or "assurance" in cmd_purpose


def _reference_year(case: dict) -> int:
    ref = str(case.get("date_reference") or "")
    try:
        return date.fromisoformat(ref[:10]).year
    except ValueError:
        return date.today().year


def _first_float(mapping: dict[str, Any], keys: list[str]) -> float:
    for key in keys:
        value = _to_float(mapping.get(key))
        if value > 0:
            return value
    return 0.0


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _pct(value: float) -> float:
    return max(value, 0.0) / 100.0


def _rate(value: float) -> float:
    if value <= 0:
        return 0.0
    return value / 100.0 if value > 1 else value


def _to_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_type(value: object) -> str:
    text = str(value or "").lower().strip()
    nfkd = unicodedata.normalize("NFKD", text)
    normalized = "".join(c for c in nfkd if not unicodedata.combining(c))
    return normalized.replace("-", "_").replace(" ", "_")
