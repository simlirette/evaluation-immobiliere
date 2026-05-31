# Phase 4 — Couverture métier (toutes les tâches d'un É.A.)

**Dépend de :** Phases 2 et 3
**Débloque :** la promesse « exécuter toutes les tâches d'un É.A. » au-delà du résidentiel standard.
**Effort :** XL (livrer par vagues)
**Objectif :** opérationnaliser dans le moteur les mandats et types de biens documentés dans `workflow-evaluateur-agree.md` mais non codés. Couvre **A4** (mandats + types de biens) et **A6** (sources étendues) et l'assistant agissant (tool calling étendu).

## Périmètre
**Inclus :** routing étendu, dates rétrospectives, définitions de valeur (JVM/valeur réelle), méthode avant-après, valeur de liquidation, types de biens spécialisés, outils assistant d'action.
**Exclus :** multi-bureau (P5).

---

## Vague 4A — Mandats à date/définition de valeur particulière (priorité haute)

### T4.1 — Date d'évaluation rétrospective (succession, donation, litige)
- Gérer une `date_reference` **rétrospective** imposée : toutes les données de marché doivent être ≤ cette date ; bloquer/filtrer les comparables postérieurs (déjà B003) ; sourcer des données d'époque.
- **Fichiers :** `orchestrator.py` (classify), `valuation.py`, `compliance.py`, `data_enrichment.py` (données historiques).
- **DoD :** un mandat succession à date passée n'utilise que des données contemporaines ; rapport justifie la date retenue.

### T4.2 — Définitions de valeur fiscale (JVM) et municipale (valeur réelle)
- JVM (LIR) pour succession/donation/roulement ; « valeur réelle » (art. 42 LFM) + **date de référence triennale** pour contestation de rôle.
- Adapter la définition de valeur, le type de rapport et les mentions normatives selon le mandat.
- **Fichiers :** `PLANS-MANDATS-V0.yaml` (nouveaux plans), `orchestrator.py`, gabarits de rapport, templates lettre.
- **DoD :** mandats `succession`, `donation`, `contestation_role` routés et produits avec la bonne définition de valeur + date.

### T4.3 — Expropriation (méthode avant-après)
- Évaluer propriété entière (avant) − résidu (après) + préjudices accessoires ; dépréciation par contiguïté.
- **Fichiers :** `engine/valuation.py` (`calculate_expropriation`), plan mandat, gabarit dédié.
- **DoD :** un cas d'expropriation partielle produit indemnité = avant − résidu + préjudices.

### T4.4 — Liquidation / vente forcée
- Valeur de liquidation ordonnée/forcée = valeur marchande − décote justifiée et documentée.
- **Fichiers :** `valuation.py`, plan mandat, gabarit.
- **DoD :** un mandat liquidation produit une valeur avec décote quantifiée et justifiée.

---

## Vague 4B — Types de biens (par ordre de demande)

### T4.5 — Immeubles à revenus 7+ / commercial / industriel (approfondir)
- Normalisation revenus/dépenses complète (RBP→RBE→RNE), baux, vacance historique, provision pour remplacement ; $/pi² commercial ; coût pour bâtiments spéciaux.
- **DoD :** rapport revenus/commercial avec analyse financière complète.

### T4.6 — Biens spécialisés (going concern & contraintes)
- RPA (composante immobilière vs achalandage, certification MSSS), hôtel (FF&E, RevPAR), station-service (Phase I/II contamination), copropriété indivise (décote illiquidité + convention), patrimonial (prime/décote), agricole (CPTAQ, $/hectare).
- Chaque type : règles d'approche + mentions/hypothèses obligatoires + données spécifiques.
- **DoD :** au moins RPA, indivise, patrimonial, agricole opérationnels (les autres documentés/jalonnés).

---

## Vague 4C — Assistant qui agit (constat assistant)

### T4.7 — Outils d'action pour l'assistant
- Au-delà de `fetch_artifact`/`search_knowledge` : `search_comparables`, `run_calculation`, `rerun_step(checkpoint)` (sous gate humain).
- Permet à l'É.A. d'ordonner « relance les comparables avec ce critère » au lieu de seulement poser des questions.
- **Fichiers :** `api.py` (outils + boucle tool-calling), gates checkpoint respectés.
- **DoD :** l'É.A. peut, via le chat, déclencher une ré-exécution d'étape qui repasse par le checkpoint.

---

## Sources étendues (A6)
- JLR API (si partenariat), multi-source comparables ; robustesse SIRF (détection de casse DOM, alertes).
- **DoD :** repli propre si une source tombe ; ajout d'une source documenté.

## Critère de done de la phase
Les mandats succession/donation/contestation LFM/expropriation/liquidation sont exécutés correctement ; immeubles à revenus + commercial complets ; principaux biens spécialisés couverts ; l'assistant peut déclencher des actions sous gate.
