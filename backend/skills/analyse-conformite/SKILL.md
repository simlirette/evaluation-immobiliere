---
name: analyse-conformite
description: >
  Analyser la conformité d'un dossier d'évaluation aux normes OEAQ, aux règles
  contractuelles du pipeline et aux exigences légales applicables au type de mandat.
type: analyse
agents:
  - compliance-qa
sources:
  - npp_oeaq_2025
  - code_deontologie_c26
  - contrats_donnees
---

## Objectif

Identifier et classifier tous les défauts de conformité, évaluer leur impact sur la fiabilité du rapport et formuler des recommandations correctives.

## Niveaux de conformité

### Bloquant (B) — Le rapport ne peut pas être émis

Ces défauts compromettent l'objectivité ou la fiabilité fondamentale du rapport.

| Code | Condition bloquante | Vérification |
|------|-------------------|-------------|
| B001 | Données essentielles manquantes (dossier_id, date_référence, adresse) | `case.get('dossier_id') and case.get('date_reference')` |
| B002 | Comparable ou ajustement sans `source_id` | Tous les comparables et ajustements ont un source_id |
| B003 | Date de vente d'un comparable > date de référence | `date_vente <= date_reference` pour chaque comparable |
| B004 | Incohérence d'unités entre sujet et comparables | Même unité dans tous les `surface.unit` |
| B005 | Ajustement ≥ 25 000 $ sans `validation_humaine: true` | Vérifier chaque ajustement |
| B006 | < 3 comparables pour évaluation résidentielle | `len(comparables_retenus) >= 3` |
| B007 | Approche de capitalisation avec TGA non extrait du marché (W005 escaladé) | Vérifier source TGA |
| STRICT | Sortie refusée si comparable sans source (mode strict) | Uniquement en production |

### Avertissement (W) — Qualité réduite mais acceptable avec justification

| Code | Condition | Impact |
|------|----------|--------|
| W001 | Niveau de confiance < 60% | Fiabilité globale réduite |
| W002 | Comparable à > 30 km sans justification | Marché différent possible |
| W003 | Hypothèse corroborée par une seule source | Risque si source erronée |
| W004 | Ajustements bruts cumulatifs > 30% (un comparable) | Comparaison douteuse |
| W005 | TGA non extrait de transactions vérifiées | Valeur revenu approximative |
| W006 | Dernière vente du sujet > 10 ans | Historique de valeur limité |

## Processus d'analyse

### Étape 1 — Vérification des données essentielles

```python
# Pseudo-code de vérification
checks = {
    'dossier_id': bool(case.get('dossier_id')),
    'date_reference': bool(case.get('date_reference')),
    'adresse': bool(case.get('adresse') or case.get('adresse_anonymisee')),
    'type_bien': bool(case.get('type_bien')),
    'surface': bool(case.get('surface')),
}
```

### Étape 2 — Vérification des sources

Pour chaque comparable et ajustement :
- Présence du champ `source_id` → B002 si absent
- Le `source_id` pointe vers une entrée dans `source_index.json` → CONF003 si absent

### Étape 3 — Cohérence temporelle

- `date_reference` ≤ date du jour → B001 si future
- `date_vente` de chaque comparable ≤ `date_reference` → B003 si vente future
- Écart entre comparable le plus ancien et date_reference → W002 si > 36 mois

### Étape 4 — Cohérence des calculs

- Unités identiques sujet/comparables → B004 si mélangées
- TGA dans plage [2.5%, 10%] pour immeubles résidentiels → W005 si hors plage
- Écart inter-approches ≤ 35% → CONF007 si dépassé

### Étape 5 — Règles spécifiques au type de mandat

- Mandat municipal/contestation : `date_reference` = date triennale du rôle → LFM001
- Mandat fiscal (JVM) : définition LIR art. 69(1) citée → OEAQ004
- Condo indivise : décote d'indivision documentée → OEAQ005
- Expropriation partielle : méthode avant-après présente → OEAQ006

## Format de sortie

```json
{
  "status": "A_REVOIR",
  "blocking_failures": ["B002: comparable[0] sans source_id"],
  "warnings": ["W003: hypothèse non corroborée par ≥ 2 sources"],
  "conformite_score": 0.72,
  "conformite_detail": {
    "donnees_essentielles": "OK",
    "tracabilite_sources": "FAIL",
    "coherence_temporelle": "OK",
    "coherence_calculs": "OK",
    "regles_specifiques_mandat": "OK"
  }
}
```
