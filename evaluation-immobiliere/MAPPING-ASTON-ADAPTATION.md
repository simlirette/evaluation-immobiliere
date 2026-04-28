# Mapping explicite — Aston -> Évaluation immobilière

## Réponse courte
Oui: tout ce qui a été construit jusqu'ici sert à l'adaptation de l'infrastructure Aston vers un MVP d'évaluation immobilière.

## Ce qui est déjà fait pour l'adaptation

### 1) Orchestration multi-agents adaptée au métier
- Contrats d'agents définis pour le flux évaluation immobilière (`intake`, `data_facts`, `comps_market`, `valuation_draft`, `compliance_qa`, `redaction`).
- Schémas I/O inter-agents pour faire circuler des artefacts compatibles entre étapes.

### 2) Gouvernance et conformité du domaine
- Règles bloquantes / warnings alignées sur une logique de conformité et validation humaine.
- Checklist conformité et spécification de traçabilité.

### 3) Outils de simulation exécutable
- Fixtures métier (cas nominal + cas d'erreur).
- Runner dry-run qui applique les règles et produit des rapports par cas.
- Résumé global automatique (indicateurs de conformité et causes d'échec).

## Ce qui reste à faire pour terminer l'adaptation
1. Connecter des sources de données réelles (ou anonymisées) du domaine immobilier.
2. Remplacer les heuristiques simplifiées par des règles métier validées par évaluateurs.
3. Brancher ce pipeline sur l'engine Aston réel (loop, tool-calls, persistance).
4. Faire valider les sorties par des évaluateurs sur des dossiers pilotes.

## Conclusion
On a complété la fondation "MVP exécutable" de l'adaptation. Ce n'est pas encore le produit final branché en production, mais c'est bien la trajectoire d'adaptation Aston -> évaluation immobilière.
