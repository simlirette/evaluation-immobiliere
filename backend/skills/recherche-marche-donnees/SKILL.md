---
name: recherche-marche-donnees
description: >
  Recherche et extraction des donnees de marche immobilier, facteurs de
  rajustement au cout de base (MEFQ), verification et ajustement des ventes
  (IAAO), et standards internationaux de mesure (IPMS). Utiliser ce skill
  pour toute question sur les sources de donnees de marche, les facteurs
  de rajustement et la validation des transactions.
type: recherche
agents:
  - comps-market
  - data-facts
sources:
  - _legacy-unstructured
  - 15-methodes-internationaux
  - 12-fournisseurs-donnees
---

# Skill : Recherche marché et données

## 1. Rôle et contexte

Ce skill encode la connaissance sur les sources de données de marché immobilier au Québec, le système de facteurs de rajustement au coût de base du MEFQ, les standards IAAO de vérification et ajustement des ventes, et les standards internationaux de mesure IPMS. Il alimente principalement l'agent comps-market (sélection de comparables, analyse de marché) et l'agent data-facts (collecte de données).

---

## 2. Connaissances encodées

### 2.1 Sources de données de marché

| Source | Type | Accès |
|--------|------|-------|
| Registre foncier du Québec | Transactions, prix, hypothèques, transferts | Payant |
| Statistiques Registre foncier | 4 indicateurs mensuels (ventes, transferts, hypothèques, difficultés) | Gratuit |
| Rôles d'évaluation municipaux | Valeur foncière, CUBF, superficie, année | Variable |
| Données Québec | Données ouvertes, rôles, statistiques | Gratuit (CC 4.0) |
| JLR | Données transactionnelles enrichies | Abonnement |
| Centris / APCIQ | Ventes résidentielles MLS | Abonnement |

### 2.2 Facteurs de rajustement au coût de base — Système MEFQ

**Règle critique** : aucun facteur ne peut être utilisé isolément ni appliqué à un coût autre que ceux des barèmes MEFQ.

**Cinq catégories** :

| Catégorie | Ce qu'il rajuste | Qui l'établit |
|-----------|-----------------|--------------|
| Temps | Évolution des coûts de construction | Bulletin MAMH |
| Taxes de vente | Composante TPS/TVQ | Bulletin MAMH |
| Envergure | Taille du bâtiment | Bulletin MAMH |
| Classe | Qualité de construction (1 à 9) | Bulletin MAMH |
| Économique | Conditions économiques locales | **L'évaluateur** |

**Facteurs de temps 2025** :

| Usage | Facteur |
|-------|---------|
| Résidentiel | 3,00 |
| Multirésidentiel typique | 2,80 |
| Agricole | 3,06 |
| Commercial | 2,76 |
| Industriel | 2,52 |
| Institutionnel | 3,06 |

**Facteurs de classe 2025** (résidentiel) : Classe 1=1,30 / 2=1,15 / 3=1,10 / 4-5=1,00 / 6=0,85 / 7=0,75 / 8=0,65 / 9=0,60

### 2.3 Vérification des ventes — Standard IAAO

**Principe** : toutes les ventes sont candidates valides sauf preuve documentée du contraire. Vérification dans les 3 mois.

**Ventes généralement invalides** :
- Ventes forcées par ordonnance judiciaire (JAMAIS valides)
- Ventes entre personnes liées
- Ventes gouvernementales
- Ventes d'institutions caritatives/religieuses/éducatives
- Ventes d'institutions financières (acheteur ou vendeur)
- Ventes pour succession
- Ventes de titre douteux

**Exception** : ventes d'institutions financières comme vendeur potentiellement valides si > 20 % du marché.

### 2.4 Ajustements au prix de vente — Ordre IAAO

1. **Ajustements transactionnels** (prix → valeur marchande à la date de vente)
   - Frais clôture acheteur payés par vendeur → soustraire
   - Taxes impayées payées par acheteur → ajouter
   - Financement hors marché → VA de la différence de paiements
   - Commission payée par acheteur → ajouter (sinon aucun ajustement)

2. **Ajustements condition du bien** (isoler le bien immobilier)
   - Biens meubles → soustraire (seuil : > 10 % résidentiel, > 25 % commercial → exclure)
   - Baux long terme hors marché (≥ 3 ans) → VA différence loyers contractuels vs marché
   - Allocation réparations → soustraire si non réparé à la date d'évaluation

3. **Ajustements temporels** (date de vente → date d'analyse)

### 2.5 Indicateurs IAAO

| Indicateur | Seuil acceptable |
|-----------|-----------------|
| COD | ≤ 15 % résidentiel, ≤ 20 % commercial |
| PRD | 0,98 à 1,03 |
| Proportion médiane | 0,95 à 1,05 |

### 2.6 Standards IPMS — Mesure des bâtiments

6 standards (IPMS 1 à 4.2) couvrant mesures externes/internes, bâtiment entier/occupation exclusive, incluant/excluant murs et colonnes. Standard ouvert, 88 organisations membres. Applicable tous types de bâtiments.

---

## 3. Méthodologie de recherche

### Étape 1 — Identification des sources

1. Identifier les sources disponibles pour le marché visé (publiques et privées)
2. Documenter les conditions d'accès, licences, limites de chaque source
3. Prioriser : registre foncier → rôle municipal → données ouvertes → sources privées

### Étape 2 — Extraction des transactions

1. Extraire les transactions pertinentes (période, localisation, type de bien)
2. Constituer un fichier de ventes avec informations complètes
3. Inclure : prix, date, parties, financement, conditions, caractéristiques du bien

### Étape 3 — Vérification

1. Vérifier chaque vente (conditions de transaction, intérêt transféré, financement)
2. Exclure les ventes non représentatives avec code de raison documenté
3. Identifier les ratios atypiques (< 50 %, > 150 %) pour investigation
4. Délai recommandé : dans les 3 mois suivant la vente

### Étape 4 — Ajustement

1. Appliquer les ajustements dans l'ordre IAAO (transactionnels → condition → temporels)
2. Pour méthode du coût : appliquer les 5 facteurs MEFQ conjointement
3. Documenter chaque ajustement et sa justification

### Étape 5 — Validation croisée

1. Comparer données de ventes avec valeurs au rôle
2. Vérifier cohérence entre sources
3. Contextualiser avec statistiques régionales

---

## 4. Règles critiques

1. **NE JAMAIS** utiliser un facteur MEFQ isolément — les 5 facteurs s'appliquent conjointement
2. **NE JAMAIS** mélanger les éditions de bulletins (2006 vs modernisée)
3. **NE JAMAIS** exclure une vente sans code de raison documenté
4. **NE JAMAIS** inclure les ventes forcées par ordonnance judiciaire
5. **NE JAMAIS** appliquer les seuils IAAO comme des normes contraignantes — ils sont consultatifs
6. **TOUJOURS** documenter la provenance de chaque donnée de marché
7. **TOUJOURS** vérifier si le prix inscrit au registre reflète la considération réelle
8. **TOUJOURS** appliquer les ajustements dans l'ordre prescrit
9. Le facteur économique est la responsabilité de l'évaluateur, pas du bulletin MAMH
10. La règle du premier droit à l'acte sous-estime le volume réel — ne pas extrapoler directement

---

## 5. Checklist de qualité

- [ ] Les sources de données sont identifiées avec conditions d'accès et limites
- [ ] Les transactions extraites couvrent la période et localisation pertinentes
- [ ] Chaque vente a été vérifiée selon les critères IAAO
- [ ] Les ventes invalides sont exclues avec code de raison documenté
- [ ] Les ajustements sont appliqués dans l'ordre prescrit
- [ ] Les facteurs MEFQ sont appliqués conjointement (jamais isolément)
- [ ] L'édition des bulletins est cohérente (pas de mélange 2006/modernisée)
- [ ] Le facteur économique est établi par l'évaluateur
- [ ] Les données sont croisées entre sources pour cohérence
- [ ] Les statistiques régionales sont contextualisées (attention Région 10)
- [ ] Les seuils IAAO sont utilisés comme guides, non comme obligations
- [ ] Les limites des données sont documentées
