# Phase 2 — Cœur analytique (produire la valeur comme un É.A.)

**Dépend de :** Phase 1
**Débloque :** un rapport crédible (P3), la couverture métier (P4).
**Effort :** L–XL
**Objectif :** que le moteur produise réellement l'analyse de valeur d'un É.A. : grille d'ajustements, AMU raisonnée, approches coût/revenu sourcées. Couvre **A2, A3, A5, A6 (visibilité), A12 (unification calculs)**.

## Périmètre
**Inclus :** grille d'ajustements déterministe ; AMU réelle ; TGA marché + tables de coûts ; unification source de calcul ; visibilité des diagnostics sources.
**Exclus :** mise en forme du rapport (P3), nouveaux mandats (P4).

---

## Tâches

### T2.1 — Grille d'ajustements dans le moteur (A2) — *pièce maîtresse*
Aujourd'hui : moyenne pondérée des prix + ajustements saisis main. Cible : grille par comparable, par caractéristique, avec taux dérivés.
- `engine/valuation.py` (ou nouveau `engine/adjustments.py`) : calcul des ajustements par caractéristique (date/temps, superficie habitable, terrain, garage/stationnement, état, sous-sol, localisation) avec taux $/unité (paired sales ou taux paramétrables sourcés).
- Produire une **vraie grille** dans `calculs_approche_comparative.json` : prix vendu → ajustements ligne par ligne → prix ajusté → fourchette resserrée → valeur indiquée.
- Réutiliser/porter la logique des modules `src/lib/compute-adjustment-*.ts` (référence existante).
- **Fichiers :** `backend/engine/valuation.py` / `adjustments.py`, schéma `mvp/PIPELINE-IO-SCHEMAS/calculs_approche_comparative.schema.json`.
- **DoD :** l'artefact comparatif contient la grille complète (≥ 7 lignes d'ajustement, prix ajustés, fourchette) ; tests sur un dossier de référence.

### T2.2 — Unifier la source de calcul TS/Python (A12 calculs)
Les ~150 `compute-*.ts` (frontend) et `valuation.py` (backend) divergent.
- Décider la **source de vérité** : moteur Python (recommandé, car c'est lui qui alimente le rapport). Le frontend consomme les artefacts calculés, ne recalcule pas la valeur.
- Aligner les formules ; documenter le mapping ; déprécier les calculs frontend redondants (ou les garder en lecture seule d'affichage).
- **Fichiers :** `backend/engine/*`, `src/lib/compute-*` (audit d'usage), `docs/CALCULS-SOURCE-OF-TRUTH.md`.
- **DoD :** une seule logique produit la valeur ; le frontend affiche les artefacts moteur ; pas de double calcul de la valeur finale.

### T2.3 — AMU réelle (A3)
Remplacer le tampon `umpp_conclusion.json` (4 critères = True en dur).
- `engine/amu.py` : évaluer les 4 critères avec les données réelles —
  1. *légalement permis* : `zonage_urbanisme`, `zone_agricole` (CPTAQ), `patrimoine_culturel`, servitudes ;
  2. *physiquement possible* : superficie/forme terrain, services, contraintes (`zone_inondable`) ;
  3. *financièrement faisable* : signaux marché (conditionnel) ;
  4. *maximalement productif* : conclusion.
- Gérer terrain vacant vs amélioration existante (analyse A/B) ; conclusion pouvant **différer** de l'usage actuel.
- Brancher l'AMU sur le **choix des approches** (`approaches_for_case`).
- **Fichiers :** `backend/engine/amu.py`, `runtime.py` (blocs `umpp_conclusion.json` + `amu_analyse.md`), `valuation.py`.
- **DoD :** un cas zonage divergent → UMPP ≠ usage actuel justifié ; `conformite_zonage` reflète la donnée réelle ; tests par critère.

### T2.4 — Approche coût certifiable (A5 coût)
- Importeur de tables de coûts (Altus/Marshall Swift CSV, ou barème MEFQ base 1997 + 5 facteurs) → `engine/cost_tables.py`.
- Brancher dans `calculate_cost_approach` ; conserver le filigrane « VALEUR PROXY » tant qu'aucune table n'est chargée.
- **Fichiers :** `backend/engine/valuation.py`, `engine/cost_tables.py`, `backend/data/` (tables).
- **DoD :** avec tables chargées, l'approche coût n'affiche plus « proxy » ; sans tables, filigrane maintenu. Dépendance externe (accès Altus) suivie hors code.

### T2.5 — TGA / loyers de marché (A5 revenu)
- Dériver le TGA de transactions/loyers réels du secteur plutôt que des défauts (`_DEFAULT_CAP_RATE`, 35 %, 5 %).
- Signaler explicitement quand une valeur par défaut est utilisée (mention « à valider par l'É.A. »).
- **Fichiers :** `backend/engine/valuation.py`, `data_enrichment.py` (loyers SCHL conditionnels au locatif).
- **DoD :** un immeuble à revenus utilise un TGA sourcé ou marqué « défaut à valider » ; loyers SCHL injectés seulement si type locatif.

### T2.6 — Visibilité des diagnostics de sources (A6)
- Surfacer dans l'UI (panneau Marché / checkpoint 2) `source_coverage` / `source_diagnostics` : pourquoi 0 comparable, SIRF indisponible, ville non supportée, etc.
- **Fichiers :** `src/components/panels/MarchePanel.tsx` / `CheckpointComparablePanel.tsx`, `runtime-api.ts`.
- **DoD :** l'É.A. voit une explication claire quand le pool de comparables est vide ou partiel.

---

## Risques
- Données de taux d'ajustement : sans accès marché, les taux restent paramétrables/à valider — l'honnêteté du « à valider » est essentielle.
- Accès Altus incertain — prévoir saisie manuelle É.A. comme repli.

## Critère de done de la phase
Le moteur produit une grille d'ajustements réelle, une AMU raisonnée liée au choix d'approches, des approches coût/revenu sourcées ou explicitement marquées ; une seule source de calcul ; diagnostics visibles.
