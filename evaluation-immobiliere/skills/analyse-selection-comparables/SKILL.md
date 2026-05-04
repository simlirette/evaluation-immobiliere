---
name: analyse-selection-comparables
description: >
  Selection, scoring et justification des comparables pour la methode de
  comparaison. Utiliser ce skill pour filtrer, classer et documenter les
  ventes comparables selon les criteres MEFQ, CUSPAP/NPP et IAAO.
type: analyse
agents:
  - comps-market
sources:
  - 01-mefq-manuel
  - 15-methodes-internationaux
  - 00-cuspap
  - 04-oeaq-normes
---

# Skill : Analyse — Sélection des comparables

## 1. Rôle et contexte

Ce skill encode le processus complet de sélection, scoring et justification des comparables pour la méthode de comparaison directe. Il est utilisé par l'agent comps-market pour constituer l'ensemble des ventes comparables qui alimenteront l'analyse de valeur.

---

## 2. Connaissances encodées

### 2.1 Stratification MEFQ — 5 niveaux

| Niveau | Filtre |
|--------|--------|
| 1. Parc sous étude | Totalité des immeubles |
| 2. Parc cible | Même type/usage (CUBF) |
| 3. Territoire d'observation | Zone géographique homogène |
| 4. Segment | Sous-ensemble homogène |
| 5. Immeuble type | Référence de comparaison |

**Seuils minimaux** : 15 % des immeubles du segment vendus OU 30 observations minimum.

### 2.2 Critères de sélection (par priorité)

1. **Localisation** — facteur le plus déterminant (éliminatoire)
2. **Type d'usage** — CUBF compatible (éliminatoire)
3. **Date de vente** — < 1 an préféré, < 3 ans acceptable (éliminatoire)
4. **Superficie** — terrain et bâtiment comparables
5. **Âge et état** — époque et entretien similaires
6. **Qualité construction** — classe A-E similaire
7. **Nombre d'unités** — pour immeubles à revenus
8. **Caractéristiques physiques** — configuration, services, dépendances

### 2.3 Ventes à exclure

| Vente | Disposition |
|-------|-----------|
| Forcée par ordonnance judiciaire | **TOUJOURS exclure** |
| Entre personnes liées | Exclure sauf marché ouvert + prix typique |
| Gouvernementale | Exclure sauf recherche approfondie |
| Institution financière (vendeur) | Exclure sauf > 20 % du marché |
| Succession | Exclure sauf exposition marché normale |
| Organisme caritatif/religieux/éducatif | Exclure |
| Titre douteux | Exclure |
| Biens meubles > 10 % (résidentiel) | Exclure |
| Biens meubles > 25 % (commercial) | Exclure |

### 2.4 Ordre des ajustements

1. **Transactionnels** (financement, frais clôture, taxes impayées)
2. **Condition du bien** (biens meubles, baux, réparations)
3. **Temporels** (date de vente → date d'évaluation)
4. **Localisation** (différences géographiques)
5. **Caractéristiques physiques** (terrain, bâtiment, aménagements)

### 2.5 Limites des ajustements

- Total des ajustements : ne devrait pas excéder 25-30 % du prix
- Ajustement individuel majeur (> 15 %) : justification documentée requise
- Plus d'ajustements = moins de fiabilité du comparable

### 2.6 Indicateurs IAAO

| Indicateur | Seuil |
|-----------|-------|
| COD | ≤ 15 % résidentiel, ≤ 20 % commercial |
| PRD | 0,98 à 1,03 |
| Proportion médiane | 0,95 à 1,05 |

---

## 3. Méthodologie de sélection

### Étape 1 — Filtrage par catégorie

1. Identifier le CUBF du sujet
2. Filtrer les ventes avec CUBF identique ou compatible
3. Exclure les catégories incompatibles

### Étape 2 — Filtrage géographique

1. Définir le territoire d'observation (marché homogène)
2. Si insuffisant, élargir progressivement
3. Documenter le territoire retenu et sa justification

### Étape 3 — Filtrage temporel

1. Priorité : ventes < 1 an
2. Acceptable : ventes < 3 ans avec ajustement temporel
3. CUSPAP exige l'analyse de toute vente du sujet dans les 3 dernières années

### Étape 4 — Scoring de similarité

Pour chaque vente restante, scorer selon :
- Proximité géographique (poids élevé)
- Similarité de superficie (poids moyen-élevé)
- Similarité d'âge et d'état (poids moyen)
- Similarité de qualité de construction (poids moyen)
- Similarité de caractéristiques spéciales (poids faible-moyen)

### Étape 5 — Vérification

1. Vérifier les conditions de transaction de chaque comparable retenu
2. Identifier les ventes nécessitant des ajustements
3. Exclure les ventes échouant aux tests de validité (avec code de raison)

### Étape 6 — Sélection finale et documentation

1. Retenir les N meilleurs comparables
2. Documenter pour chaque comparable : identification, source, conditions vérifiées, score, ajustements, indicateur de valeur
3. Justifier le choix dans le rapport

---

## 4. Règles critiques

1. **TOUJOURS** vérifier les conditions de transaction avant d'utiliser un comparable
2. **TOUJOURS** documenter les raisons d'exclusion des ventes écartées
3. **TOUJOURS** justifier le choix des comparables dans le rapport
4. **JAMAIS** sélectionner uniquement par proximité géographique
5. **JAMAIS** utiliser une vente forcée comme comparable
6. **JAMAIS** appliquer des ajustements arbitraires non dérivés du marché
7. **JAMAIS** ignorer les ventes antérieures du sujet (< 3 ans — CUSPAP)
8. Les ajustements doivent être dans l'ordre prescrit (transactionnel → temporel → localisation → physique)
9. Si seuils minimaux non atteints (15 % ou 30 obs.), élargir le segment avant de conclure
10. Le biais de sélection (retenir seulement les comparables confirmant une valeur préconçue) est une faute professionnelle

---

## 5. Checklist de qualité

- [ ] Le CUBF du sujet est identifié et les comparables sont de catégorie compatible
- [ ] Le territoire d'observation est défini et justifié
- [ ] Les seuils minimaux de représentativité sont atteints (15 % ou 30 obs.)
- [ ] Les conditions de transaction de chaque comparable sont vérifiées
- [ ] Les ventes invalides sont exclues avec code de raison documenté
- [ ] Les ajustements sont appliqués dans l'ordre prescrit
- [ ] Le total des ajustements ne dépasse pas 25-30 % du prix par comparable
- [ ] Les ventes antérieures du sujet (< 3 ans) sont analysées
- [ ] Les indicateurs de valeur sont calculés et réconciliés
- [ ] La documentation est complète (identification, source, conditions, score, ajustements)
- [ ] La justification du choix est incluse dans le rapport
- [ ] Le dossier est structuré pour conservation (7 ans CUSPAP)
