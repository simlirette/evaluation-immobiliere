# Cadrage documentaire minimal (v0)

## 1) Contexte
Copilote d'évaluation immobilière pour accélérer le travail de bureau sur mandats résidentiels standards, avec validation humaine obligatoire sur décisions sensibles.

## 2) Objectif
Stabiliser la chaîne de preuve `sources -> facts -> comparables -> calculs -> conformité -> brouillon` avant extension fonctionnelle.

## 3) Contraintes
- Conformité OEAQ/NPP et auditabilité complète.
- Pas de signature professionnelle automatisée.
- Sorties bloquées en cas d'écarts critiques.

## 4) Frontière IA vs humain (v0)
- IA propose: extraction, pré-structuration, comparables, calculs préparatoires, brouillon.
- Humain valide: hypothèses sensibles, ajustements significatifs, conclusion de valeur, statut final exportable.

## 5) Artefacts obligatoires
1. `fiche_bien_normalisee.json`
2. `comparables_proposes.json`
3. `trace_calcul_valeur.json`
4. `rapport_conformite.json`
5. `journal_tracabilite.jsonl`

## 6) Critères d'entrée minimum d'un dossier
- Adresse et type de mandat renseignés.
- Date de référence renseignée.
- Au moins 1 source exploitable.

## 7) Critères de sortie minimum
- Chaque conclusion chiffrée reliée à au moins une source.
- Règles blocking conformité: 0 échec.
- Validation humaine complétée sur points sensibles.
