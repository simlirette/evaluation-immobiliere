---
name: recherche-baux-revenus
description: >
  Recherche sur le cadre juridique des baux residentiels au Quebec, les
  criteres de fixation de loyer du TAL, et les donnees locatives necessaires
  a l'approche par le revenu. Utiliser ce skill pour les questions sur les
  baux, loyers, fixation de loyer et donnees de revenus locatifs.
type: recherche
agents:
  - valuation-draft
  - data-facts
sources:
  - 23-baux-logement-revenu
---

# Skill : Recherche baux et revenus

## 1. Rôle et contexte

Ce skill encode le cadre juridique des baux résidentiels (TAL), les critères de fixation de loyer, et les données locatives nécessaires à l'approche par le revenu en évaluation immobilière. Utilisé par l'agent valuation-draft (méthode du revenu) et data-facts (collecte de données locatives).

---

## 2. Connaissances encodées

### 2.1 Critères de fixation du loyer — TAL (art. 3, Règlement T-15.01, r. 2)

Six critères :
1. **Pourcentage de base** : formule IPC sur 3 périodes — [(A−B)/B + (B−C)/C + (C−D)/D] / 3
2. **Variation taxes foncières municipales et de services**
3. **Variation taxes foncières scolaires**
4. **Variation assurances incendie et responsabilité**
5. **5 % des dépenses d'immobilisation** de la période de référence
6. **Dépenses pour nouveau service/accessoire** (annualisées)

**Part attribuable** = loyer au terme / revenus totaux de l'immeuble.

### 2.2 Définitions clés

| Terme | Définition |
|-------|-----------|
| Loyer de faveur | Inférieur au marché (parent, allié, employé, succession, gouvernement) |
| Loyer estimé | Évalué pour logement inoccupé/occupé par locateur/utilisé pour exploitation |
| Logement comparable | Même immeuble ou équivalent, services/accessoires/environnement comparables |
| Période de référence | Baux 1er avril-31 déc : année civile pr��cédente. Baux 1er janv-31 mars : avant-dernière année |
| Revenus | Loyers × 12 + autres revenus d'exploitation |

### 2.3 Dépenses d'immobilisation (Annexe 1)

Trois catégories :
1. **Maintien intégrité physique** : fondations, toiture, maçonnerie, menuiseries, drainage, sécurité
2. **Amélioration/modernisation** : cuisine, SdB, revêtements, électricité, insonorisation, agréments
3. **Impact énergétique** : isolation, chauffage, énergie renouvelable, adaptation climatique

### 2.4 Données locatives pour l'évaluation

| Donnée | Source |
|--------|--------|
| Loyers réels | Baux, propriétaire |
| Loyers du marché | Comparables, TAL, SCHL |
| Taux d'inoccupation | SCHL, marché local |
| Dépenses exploitation | Propriétaire, comptabilité |
| Taxes foncières | Rôle municipal |
| Assurances | Propriétaire |
| Pourcentages TAL annuels | Publication ministérielle |

### 2.5 Normalisation

**Loyers** : ajuster loyers de faveur, estimés, services inclus/exclus au loyer du marché comparable.

**Dépenses** — Inclure : taxes, assurances, entretien, administration, services publics, réserve remplacement. **Exclure** : capital, amortissement hypothécaire, impôts sur le revenu.

### 2.6 Indicateurs locatifs

RBP (loyers marché × 12) → RBE (RBP − inoccupation) → RNE (RBE − frais exploitation normalisés)

---

## 3. Méthodologie de recherche

### Étape 1 — Collecte des baux et loyers

1. Obtenir les baux en cours (loyers, durée, conditions, services inclus)
2. Identifier les loyers de faveur et estimés
3. Collecter les loyers du marché (comparables locatifs, données SCHL, TAL)

### Étape 2 — Collecte des dépenses

1. Obtenir les dépenses d'exploitation réelles du propriétaire
2. Identifier les dépenses de capital déguisées en entretien
3. Collecter les dépenses normalisées du marché

### Étape 3 — Normalisation

1. Normaliser les loyers au marché (ajuster faveur, services, ancienneté)
2. Normaliser les dépenses (exclure capital, amortissement, impôts)
3. Calculer RBP → RBE → RNE

### Étape 4 — Validation

1. Comparer loyers normalisés avec données TAL/SCHL
2. Vérifier cohérence dépenses avec le marché
3. Documenter sources et limites

---

## 4. Règles critiques

1. **TOUJOURS** normaliser les loyers avant d'utiliser dans l'approche revenu
2. **TOUJOURS** exclure les dépenses de capital, l'amortissement hypothécaire et les impôts sur le revenu
3. **TOUJOURS** distinguer loyer contractuel et loyer du marché
4. **JAMAIS** utiliser les dépenses réelles sans normalisation
5. **JAMAIS** ignorer les services inclus dans le loyer
6. Le TAL fixe les loyers résidentiels uniquement — les loyers commerciaux sont libres
7. Les pourcentages TAL sont des maximums en l'absence d'entente
8. La formule IPC (moyenne mobile 3 ans) ne reflète pas l'inflation immédiate
9. Le taux d'inoccupation SCHL est régional — peut ne pas refléter le marché local
10. Les dépenses d'immobilisation n'augmentent le loyer que de 5 % — récupération lente

---

## 5. Checklist de qualité

- [ ] Les baux en cours sont collectés avec loyers, durée et conditions
- [ ] Les loyers de faveur et estimés sont identifiés
- [ ] Les loyers sont normalisés au marché
- [ ] Les dépenses sont normalisées (excluant capital, hypothèque, impôts)
- [ ] Les services inclus/exclus sont documentés
- [ ] Le taux d'inoccupation est documenté avec source
- [ ] Les indicateurs RBP → RBE → RNE sont calculés
- [ ] Les sources sont citées (TAL, SCHL, comparables, propriétaire)
- [ ] Les limites des données sont documentées
