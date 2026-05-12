---
name: analyse-reconciliation-valeur
description: >
  Reconciliation des indications de valeur des trois approches d'evaluation
  (comparaison, cout, revenu). Utiliser ce skill pour ponderer les resultats,
  attribuer les niveaux de confiance et conclure a la valeur finale.
type: analyse
agents:
  - valuation-draft
sources:
  - 01-mefq-manuel
  - 00-cuspap
  - 04-oeaq-normes
---

# Skill : Analyse — Réconciliation des valeurs

## 1. Rôle et contexte

Ce skill encode le processus de réconciliation des indications de valeur des trois approches. Utilisé par l'agent valuation-draft pour conclure à une valeur finale unique et motivée. La réconciliation n'est **pas une moyenne** — c'est une pondération raisonnée.

---

## 2. Connaissances encodées

### 2.1 Trois étapes MEFQ

1. Vérifier conformité des résultats avec données du marché
2. Revoir le processus d'évaluation de chaque méthode
3. Déterminer la valeur la plus pertinente

### 2.2 Niveaux de confiance

| Niveau | Données | Méthode | Poids |
|--------|---------|---------|-------|
| A | Abondantes et fiables | Bien adaptée | Élevé |
| B | Suffisantes avec limites | Adaptée avec réserves | Modéré |
| C | Limitées | Peu adaptée | Faible |

### 2.3 Pondération par type d'immeuble

| Type | Comparaison | Revenu | Coût |
|------|-------------|--------|------|
| Résidentiel unifamilial | A (prioritaire) | N/A | B (vérification) |
| Multirésidentiel 6+ | A-B | A-B | C |
| Commercial/industriel | B | A (prioritaire) | C |
| Immeuble spécial | C | N/A | A (seule méthode) |
| Terrain vacant | A (prioritaire) | C (résiduelle) | N/A |

### 2.4 Hiérarchie

Comparaison = preuve directe, méthode **prioritaire**. Écartée seulement si données insuffisantes ou immeuble atypique.

---

## 3. Méthodologie

### Étape 1 — Réception des indications

Recevoir les indications de valeur de chaque approche avec :
- Valeur indiquée
- Données utilisées (quantité, qualité)
- Ajustements appliqués
- Limites identifiées

### Étape 2 — Vérification de conformité

Pour chaque approche :
- Résultats cohérents avec le marché ?
- Indicateurs dans les fourchettes normales ?
- Anomalies ou résultats contre-intuitifs ?

### Étape 3 — Attribution des niveaux de confiance

Pour chaque approche, évaluer :
- Quantité et qualité des données
- Adéquation de la méthode au type d'immeuble
- Ampleur des ajustements
- Cohérence interne

### Étape 4 — Analyse convergence/divergence

- **Convergence** : résultats se renforcent → conclusion robuste
- **Divergence > 10-15 %** : expliquer pourquoi, justifier pondération
- Valeur finale dans la fourchette des indications (sauf justification exceptionnelle)

### Étape 5 — Conclusion motivée

- Valeur unique arrondie
- Pondération justifiée
- Divergences expliquées
- Approches non utilisées justifiées

---

## 4. Règles critiques

1. **JAMAIS** moyenner les indications — toujours pondérer selon fiabilité
2. **TOUJOURS** justifier la pondération retenue dans le rapport
3. **TOUJOURS** expliquer les divergences entre approches (> 10-15 %)
4. **TOUJOURS** justifier pourquoi une approche est écartée
5. La comparaison est prioritaire sauf données insuffisantes ou immeuble atypique
6. Le niveau de confiance (A/B/C) doit être attribué à chaque approche
7. La convergence renforce la conclusion — la documenter
8. La valeur finale doit être dans la fourchette des indications (sauf justification)
9. Le niveau de détail de la réconciliation dépend du type de rapport (complet/abrégé/MAJ)
10. Les indicateurs IAAO (COD, PRD, proportion médiane) sont consultatifs, pas contraignants

---

## 5. Checklist de qualité

- [ ] Chaque approche a un niveau de confiance attribué (A/B/C)
- [ ] La pondération est justifiée et documentée
- [ ] Les divergences entre approches sont expliquées
- [ ] Les approches non utilisées sont justifiées
- [ ] La valeur finale est dans la fourchette des indications
- [ ] Le processus de réconciliation est décrit selon le type de rapport
- [ ] La conclusion est une opinion motivée, pas une moyenne
- [ ] Le dossier de travail contient le raisonnement complet
