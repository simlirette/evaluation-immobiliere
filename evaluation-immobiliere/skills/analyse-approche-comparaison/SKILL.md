---
name: analyse-approche-comparaison
description: >
  Methodologie complete de l'approche par comparaison directe pour
  l'evaluation immobiliere. Utiliser ce skill pour appliquer la technique
  des prix de vente rajustes ou la modelisation statistique.
type: analyse
agents:
  - valuation-draft
sources:
  - 01-mefq-manuel
  - 00-cuspap
  - 04-oeaq-normes
  - 15-methodes-internationaux
---

# Skill : Analyse — Approche par comparaison

## 1. Rôle et contexte

Ce skill encode la méthodologie complète de la méthode de comparaison directe. Utilisé par l'agent valuation-draft pour développer l'indication de valeur par comparaison. La comparaison est la méthode **prioritaire** — écartée uniquement si données insuffisantes ou immeuble trop atypique.

---

## 2. Connaissances encodées

### 2.1 Méthodologie en 10 étapes MEFQ

1. Définir le parc sous étude
2. Délimiter le parc cible (CUBF)
3. Délimiter le territoire d'observation (marché homogène)
4. Constituer le segment (sous-ensemble homogène)
5. Sélectionner les ventes comparables
6. Vérifier et analyser les ventes
7. Ajuster les prix de vente
8. Calculer les indicateurs de valeur
9. Réconcilier les indicateurs
10. Conclure à la valeur

### 2.2 Deux techniques

| Technique | Application | Avantages |
|-----------|-------------|-----------|
| Prix de vente rajustés | Évaluation unitaire, petits échantillons | Preuve directe, transparence |
| Régression multiple | Évaluation de masse, grands échantillons | Traitement simultané variables, mesure fiabilité |

### 2.3 Ordre des ajustements

1. **Transactionnels** (financement, frais clôture, taxes)
2. **Condition du bien** (meubles, baux, réparations)
3. **Temporels** (date vente → date évaluation)
4. **Localisation** (différences géographiques)
5. **Caractéristiques physiques** (terrain, bâtiment)

### 2.4 Limites des ajustements

- Total : ≤ 25-30 % du prix du comparable
- Individuel majeur (> 15 %) : justification documentée
- Ajustements dérivés du marché, pas subjectifs

### 2.5 Réconciliation

- Pondérer selon fiabilité et similarité (pas une moyenne arithmétique)
- Le comparable le plus similaire reçoit le poids le plus élevé
- Niveaux de confiance MEFQ : A (données abondantes), B (suffisantes), C (limitées)

---

## 3. Méthodologie d'application

### Étape 1 — Réception des comparables

Recevoir les comparables sélectionnés et vérifiés par l'agent comps-market. Vérifier que :
- Les conditions de transaction sont documentées
- Les ajustements transactionnels sont déjà appliqués
- Les fiches comparables sont complètes

### Étape 2 — Ajustements de comparaison

Pour chaque comparable, ajuster séquentiellement :
1. Temporel : facteur de marché entre date de vente et date d'évaluation
2. Localisation : différences de quartier, voisinage, accès, nuisances
3. Physiques : superficie, âge, qualité, état, aménagements, dépendances

### Étape 3 — Calcul des indicateurs

Calculer les unités de comparaison pertinentes :
- Résidentiel : $/pi² bâtiment, prix ajusté global
- Multirésidentiel : $/porte, MRB
- Commercial : $/pi² bâtiment, TGA
- Terrain : $/pi² terrain

### Étape 4 — Réconciliation

1. Analyser la dispersion des indicateurs
2. Identifier les aberrations et les expliquer
3. Pondérer selon similarité et fiabilité
4. Conclure à la valeur — opinion motivée

### Étape 5 — Documentation

Rédiger la section de comparaison du rapport :
- Description de chaque comparable
- Grille d'ajustements avec justification
- Indicateurs de valeur
- Réconciliation et conclusion

---

## 4. Règles critiques

1. La comparaison est la méthode **prioritaire** sauf données insuffisantes ou immeuble atypique
2. Les ajustements suivent l'ordre prescrit (transactionnel → condition → temporel → localisation → physique)
3. La réconciliation est une **pondération raisonnée**, jamais une moyenne arithmétique
4. Chaque ajustement doit être dérivé du marché et documenté
5. Les ventes antérieures du sujet (< 3 ans) doivent être analysées (CUSPAP)
6. Le biais de confirmation est une faute — ne pas retenir seulement les comparables qui confirment
7. Les seuils d'ajustement (25-30 % total, 15 % individuel) sont des guides de fiabilité
8. Le niveau de confiance (A/B/C) doit être indiqué pour cette approche

---

## 5. Checklist de qualité

- [ ] Les comparables reçus sont vérifiés et documentés
- [ ] Les ajustements sont appliqués dans l'ordre prescrit
- [ ] Chaque ajustement est justifié et dérivé du marché
- [ ] Le total des ajustements par comparable est raisonnable (≤ 25-30 %)
- [ ] Les indicateurs de valeur sont calculés et cohérents
- [ ] La réconciliation est une pondération raisonnée (pas une moyenne)
- [ ] Les ventes antérieures du sujet (< 3 ans) sont analysées
- [ ] Le niveau de confiance (A/B/C) est indiqué
- [ ] La section du rapport est complète (comparables, grille, réconciliation)
- [ ] Aucun biais de confirmation dans la sélection
