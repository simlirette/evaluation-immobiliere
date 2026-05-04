---
name: redaction-analyse-marche
description: >
  Redaction des sections d'analyse de marche dans le rapport d'evaluation
  immobiliere. Utiliser ce skill pour generer les descriptions de secteur,
  les etudes de marche et les donnees municipales contextuelles.
type: redaction
agents:
  - redaction
sources:
  - 01-mefq-manuel
  - 10-rapports-precedents-firme
  - 12-fournisseurs-donnees
---

# Skill : Rédaction — Analyse de marché

## 1. Rôle et contexte

Ce skill encode la structure et les règles de rédaction des sections d'analyse de marché dans le rapport d'évaluation. L'analyse de marché contextualise la propriété évaluée et justifie les paramètres retenus dans les méthodes d'évaluation (ajustements, TGA, UMPP).

---

## 2. Connaissances encodées

### 2.1 Composantes de l'analyse de marché

| Composante | Contenu |
|-----------|---------|
| **Description ville** | Population, économie, services, positionnement régional, attraits, qualité de vie |
| **Secteur immédiat** | Localisation, âge quartier, type dominant, tendance, offre/demande, conformité, services |
| **Marché local** | Délai vente, type marché (acheteurs/vendeurs), variation prix (terrain, loyer, construction, taux), tendances court/moyen terme |
| **Données municipales** | Matricule, rôle triennal, date marché, évaluation (terrain/bâtisse), taxes, proportion médiane, zonage |
| **Infrastructures** | Services publics (aqueduc, égout, gaz), rues (asphalte, trottoirs) |

### 2.2 Sources de données

| Source | Données |
|--------|---------|
| Rôle d'évaluation | Valeurs, mutations, caractéristiques |
| BPD / JLR | Transactions, prix déclarés |
| MLS / Centris | Inscriptions, prix demandés, délais |
| ISQ | Démographie, emploi, IPC |
| SCHL | Mises en chantier, taux vacance, loyers |
| Municipalité | Zonage, permis, urbanisme |

### 2.3 Indicateurs par segment

**Résidentiel** : ventes, prix médian, délai vente, ratio prix/demandé, vacance, loyers, mises en chantier

**Commercial/bureaux** : inventaire pi², taux inoccupation (classe A/B/C), loyer brut/net, absorption, TGA

**Industriel** : inventaire pi², inoccupation, loyer $/pi², ventes $/pi²

**Terrain** : prix $/m², volume transactions, tendance, disponibilité

### 2.4 Note sur les données municipales

Le rôle d'évaluation foncière sert à la taxation. Valeurs établies au 1er juillet de l'année précédant le dépôt du rôle. Triennal. L'évaluateur municipal inclut l'ensemble des droits (faisceau). La proportion médiane mesure l'écart entre prix courants et valeurs au rôle — pas un facteur d'ajustement direct.

---

## 3. Méthodologie de rédaction

### Étape 1 — Collecter les données

Rassembler données municipales, transactions récentes, statistiques marché, descriptions secteur.

### Étape 2 — Rédiger la description de la ville

Portrait factuel centré sur les éléments pertinents à la valeur immobilière.

### Étape 3 — Rédiger la description du secteur

Localisation, caractéristiques du quartier, facteurs favorables/défavorables, proximité services.

### Étape 4 — Rédiger l'analyse du marché local

Indicateurs de marché, offre/demande, tendances des prix, délais de vente.

### Étape 5 — Documenter les données municipales

Rôle d'évaluation, taxes, zonage, proportion médiane, avec note explicative.

### Étape 6 — Lier l'analyse aux méthodes

S'assurer que l'analyse alimente directement l'UMPP, les ajustements, le TGA et la réconciliation.

---

## 4. Règles critiques

1. **Factuel et vérifiable** — sources identifiées, données datées
2. **Pertinent au segment** — indicateurs adaptés au type de propriété
3. **Échelle appropriée** — quartier pour le secteur, ville/région pour les tendances
4. **Données actuelles** — moins de 12 mois pour les indicateurs de marché
5. **Distinction faits/opinions** — qualifier les prévisions comme estimations
6. **Données municipales ≠ valeur marchande** — toujours le mentionner
7. **La proportion médiane n'est pas un facteur d'ajustement direct**
8. **L'analyse doit servir les méthodes** — pas de données décoratives
9. **Tableaux pour les comparatifs** — structurer les données
10. **Sources en note** — identification de la provenance des données

---

## 5. Checklist de qualité

- [ ] Description de la ville pertinente et factuelle
- [ ] Secteur immédiat décrit (localisation, type, tendance, services)
- [ ] Marché local documenté (offre/demande, délais, tendances)
- [ ] Données municipales complètes (rôle, taxes, zonage, médiane)
- [ ] Note explicative sur le rôle d'évaluation incluse
- [ ] Sources de données identifiées
- [ ] Indicateurs adaptés au segment de propriété
- [ ] Données de moins de 12 mois
- [ ] Analyse liée aux méthodes d'évaluation (UMPP, ajustements, TGA)
- [ ] Pas de confusion données municipales / valeur marchande
