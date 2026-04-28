# Test plan v0

## Objectif
Valider que la chaîne MVP produit une sortie complète, traçable et révisable par un évaluateur.

## Cas de tests minimum

### T01 — Dossier nominal (simple)
- Entrée complète, données cohérentes.
- Attendu: statut `BROUILLON` ou `PRET_REVISION_FINALE`.

### T02 — Dossier avec source manquante
- Une conclusion sans `source_id`.
- Attendu: échec bloquant, statut `A_REVOIR`.

### T03 — Ajustement sensible sans validation
- Ajustement montant élevé sans `human_decision`.
- Attendu: échec bloquant, statut `A_REVOIR`.

### T04 — Unité incohérente
- Mélange m2/pi2 sans conversion.
- Attendu: échec bloquant, statut `A_REVOIR`.

### T05 — Données faibles mais complètes
- Sources présentes, confiance basse sur plusieurs champs.
- Attendu: warnings + statut `BROUILLON`.

## Critères d'acceptation globaux
- 100% des tests bloquants détectés.
- 100% des sorties avec statut final valide.
- 100% des conclusions liées à une source.
- 100% des ajustements sensibles avec validation humaine explicite.

## Exécution (manuelle v0)
1. Préparer 5 fixtures (JSON/YAML).
2. Exécuter pipeline dry-run.
3. Vérifier les rapports de conformité et journal de traçabilité.
4. Documenter les écarts.
