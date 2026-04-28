# Scope MVP provisoire (v0)

## Objectif produit
Automatiser le travail de bureau d'un évaluateur immobilier (collecte, structuration, pré-analyse, brouillon de rapport), avec validation humaine obligatoire pour toute décision sensible.

## Cas d'usage inclus (IN)
- Mandat résidentiel standard (maison unifamiliale).
- Production d'un brouillon de rapport interne.
- Préparation des comparables et des justifications.
- Contrôles de complétude/conformité de base.

## Cas d'usage exclus (OUT)
- Signature professionnelle finale automatisée.
- Mandats commerciaux/industriels complexes.
- Avis de valeur sans données minimales.
- Décision finale de réconciliation sans évaluateur.

## Utilisateurs cibles
- Évaluateur agréé (principal)
- Analyste junior / adjoint (secondaire)

## Sorties MVP attendues
1. `fiche_bien_normalisee.json`
2. `comparables_proposes.json`
3. `journal_traçabilite.jsonl`
4. `brouillon_rapport.md`
5. `rapport_conformite.json`

## Critères de succès (v0)
- 30% de réduction du temps de préparation bureau (cible provisoire).
- 100% des conclusions liées à une source.
- 100% des dossiers avec statut final explicite (`BROUILLON`, `A_REVOIR`, `PRET_REVISION_FINALE`).

## Critères de rejet
- Sortie sans sources.
- Incohérences majeures non signalées.
- Aucun point de validation humaine pour ajustements sensibles.
