# Source de vérité des calculs — eval-immo

**Date :** 2026-05-31  
**Décision :** Moteur Python = source de vérité unique pour toute valeur engageante.

---

## Principe

**Le moteur Python (`backend/engine/`) produit les valeurs.  
Le frontend (`src/lib/compute-*.ts`) affiche et analyse, il ne recalcule pas la valeur finale.**

Toute divergence entre frontend et backend est résolue en faveur du backend.

---

## Source de vérité : moteur Python

| Calcul | Module Python | Artefact produit |
|---|---|---|
| Valeur comparative (grille 7 lignes/comp) | `engine/adjustments.py` | `calculs_approche_comparative.json` |
| Valeur par le coût | `engine/valuation.py::calculate_cost_approach` | `calculs_approche_cout.json` |
| Valeur par le revenu (RBP→RBE→RNE/TGA) | `engine/valuation.py::calculate_income_approach` | `calculs_approche_revenu.json` |
| Valeur expropriation avant-après | `engine/valuation.py::calculate_expropriation` | dans `calculs_approche_comparative.json` |
| Valeur liquidation (VM - décote) | `engine/valuation.py::calculate_liquidation_value` | idem |
| AMU / UMPP (4 critères) | `engine/amu.py::evaluate_amu` | `umpp_conclusion.json` |
| Conformité B001-B008 | `engine/compliance.py::run_compliance` | `rapport_non_conformites.json` |
| Conflit d'intérêts | `engine/compliance.py::check_conflit_interets` | `conflit_interets.json` |
| Grille d'ajustements finale (rapport) | `engine/adjustments.py::compute_adjustment_grid` | dans `brouillon_rapport.md` |

**Ces valeurs sont CERTIFIANTES** — elles apparaissent dans le rapport signé par l'É.A.

---

## Rôle du frontend (affichage + analytics uniquement)

Les 112 fichiers `src/lib/compute-*.ts` font de l'**analyse UI** sur les artefacts reçus du backend. Ils ne produisent pas de valeur certifiante.

### Catégories

| Catégorie | Fichiers exemples | Rôle |
|---|---|---|
| **Statistiques comparables** | `compute-comparable-price-quartiles.ts`, `compute-comparable-completeness.ts` | Afficher la qualité du pool pour l'É.A. |
| **Analyse ajustements** | `compute-adjustment-profile.ts`, `compute-adjustment-garage-impact.ts` | Visualiser la distribution des ajustements |
| **Prix ajustés** | `compute-adjusted-price-stats.ts`, `compute-adjusted-price-cv.ts` | Stats descriptives sur les prix reçus du backend |
| **Qualité données** | `compute-data-quality-report.ts`, `compute-comparable-field-coverage.ts` | Indicateurs de complétude pour l'É.A. |
| **Marché** | `compute-market-price-trend.ts`, `compute-sales-pressure-index.ts` | Contexte marché (display only) |

**Ces calculs ne modifient JAMAIS le dossier** — ils sont recalculés à chaque rendu React.

---

## Règle de décision

```
if (valeur engagée dans le rapport) → Python uniquement
if (indicateur UI / analytics) → TypeScript OK
if (doute) → Python
```

---

## Migration prévue

- Les `compute-adjustment-*.ts` **dupliquent partiellement** la logique Python de `engine/adjustments.py`.
  → Constat A12 : à terme, le frontend consomme la grille calculée par Python (déjà le cas pour le rapport).
  → Les TS files restent pour l'**affichage interactif** (valeurs en temps réel pendant la saisie).
  → **Pas de suppression** — garder pour l'UX, mais ne pas les utiliser pour le rapport.

---

## Invariant

> Aucun calcul TypeScript frontend ne peut donner une valeur différente de celle du rapport.  
> Si l'É.A. voit une valeur à l'écran, elle doit être cohérente avec `calculs_approche_comparative.json`.
