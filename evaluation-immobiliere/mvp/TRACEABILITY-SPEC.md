# Traceability spec v0

## Principe directeur
Aucune conclusion sans preuve: chaque valeur, ajustement ou affirmation doit être traçable vers une source explicite.

## Format du journal (JSONL)
Chaque ligne représente un événement:

```json
{
  "task_id": "comps_market",
  "artifact": "comparables_proposes.json",
  "field": "prix_vente_ajuste",
  "value": 512000,
  "source_id": "src_2026_001",
  "confidence": 0.84,
  "human_decision": "approved",
  "rationale": "Ajustement localisation validé",
  "timestamp_utc": "2026-04-28T20:00:00Z"
}
```

## Règles obligatoires
1. `source_id` est obligatoire pour chaque conclusion.
2. `human_decision` est obligatoire pour chaque ajustement sensible.
3. Toute modification d'un calcul doit produire un nouvel événement.
4. Les événements doivent être horodatés en UTC.

## Contrôles de validité
- Rejeter une sortie si un champ critique est sans source.
- Rejeter une sortie si `human_decision` est absent sur un ajustement sensible.
- Signaler (warning) toute confiance < 0.60.
