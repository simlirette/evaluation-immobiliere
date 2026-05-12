---
name: analyse-approche-cout
description: >
  Methodologie complete de l'approche par le cout pour l'evaluation
  immobiliere. Utiliser ce skill pour estimer le cout neuf, appliquer
  les facteurs de rajustement MEFQ et calculer la depreciation.
type: analyse
agents:
  - valuation-draft
sources:
  - 01-mefq-manuel
  - _legacy-unstructured
  - 00-cuspap
  - 04-oeaq-normes
---

# Skill : Analyse — Approche par le coût

## 1. Rôle et contexte

Ce skill encode la méthodologie complète de la méthode du coût. Utilisé par l'agent valuation-draft pour développer l'indication de valeur par le coût. Particulièrement pertinent pour les immeubles neufs, spéciaux, ou sans comparables/revenus.

---

## 2. Connaissances encodées

### 2.1 Formule fondamentale

**Valeur = Valeur du terrain + (Coût neuf ajusté − Dépréciation)**

### 2.2 Concepts de coût

| Concept | Usage |
|---------|-------|
| Substitution intégrale (remplacement) | **Standard MEFQ** — même utilité, matériaux contemporains |
| Reconstitution (reproduction) | Patrimoine, immeubles historiques, assurance |

### 2.3 Cinq barèmes MEFQ (date base : 1er juillet 1997)

| Barème | Application |
|--------|-------------|
| Résidentiel | Unifamilial, bifamilial |
| Multirésidentiel typique | 3+ logements standard |
| Multirésidentiel atypique | Conception non standard |
| Agricole | Bâtiments agricoles |
| Non résidentiel | Commercial, institutionnel, industriel |

### 2.4 Cinq facteurs de rajustement (application conjointe obligatoire)

**Coût ajusté = Coût base × F.temps × F.taxes × F.envergure × F.classe × F.économique**

| Facteur | Source | Facteurs temps 2025 |
|---------|--------|-------------------|
| Temps | Bulletin MAMH | Rés. 3,00 / Agri. 3,06 / Com. 2,76 / Ind. 2,52 / Inst. 3,06 |
| Taxes de vente | Bulletin MAMH | 1,06 à 1,15 selon type et valeur |
| Envergure | Bulletin MAMH | 1,05 à 1,35 selon superficie (non rés.) |
| Classe (1-9) | Bulletin MAMH | 0,60 à 1,30 (résidentiel) |
| Économique | **L'évaluateur** | Conditions du marché local |

### 2.5 Trois catégories de dépréciation

| Catégorie | Corrigible | Incorrigible |
|-----------|-----------|-------------|
| Détérioration physique | Peinture, toiture, fenêtres | Usure structurale |
| Désuétude fonctionnelle | SdB manquante, électrique | Hauteur plafond, suramelioration |
| Désuétude externe | — | Autoroute, fermeture employeur |

### 2.6 Techniques de dépréciation

| Technique | Formule | Usage |
|-----------|---------|-------|
| Âge/vie | Âge apparent / Vie économique | Standard, masse |
| Détaillée | Par composante | Complexe, litiges |
| Comparaison | Prix − terrain − coût neuf | Validation |

### 2.7 Bâtiments industriels

Segmentation : polyvalence d'usage (générale/limitée/unique), type de charpente (acier/béton/bois/mixte), localisation. Vocation unique = dépréciation plus rapide.

---

## 3. Méthodologie d'application

### Étape 1 — Évaluation du terrain

Évaluer le terrain séparément par :
1. Comparaison (principale) : prix de terrains similaires vendus
2. Allocation : proportion terrain/immeuble
3. Revenu résiduel : revenu net attribuable au terrain
4. Lotissement : analyse de développement

### Étape 2 — Estimation du coût neuf

1. Identifier le barème MEFQ applicable
2. Déterminer le coût de base unitaire
3. Multiplier par la superficie du bâtiment
4. Appliquer les 5 facteurs conjointement

### Étape 3 — Estimation de la dépr��ciation

1. Déterminer l'âge apparent et l'âge chronologique
2. Estimer la vie économique (selon type, charpente, localisation)
3. Calculer la dépréciation physique (technique âge/vie ou détaillée)
4. Identifier la désuétude fonctionnelle (corrigible et incorrigible)
5. Identifier la désuétude externe (généralement incorrigible)
6. Totaliser la dépr��ciation

### Étape 4 — Calcul de la valeur

Valeur = Terrain + (Coût neuf ajusté − Dépréciation totale)

### Étape 5 — Validation et documentation

1. Comparer avec les indications des autres méthodes
2. Vérifier la cohérence coût-valeur avec le marché
3. Documenter chaque composante et sa source
4. Indiquer le niveau de confiance (A/B/C)

---

## 4. Règles critiques

1. Les 5 facteurs de rajustement s'appliquent **conjointement** — jamais isolément
2. Ne pas mélanger les éditions de bulletins (2006 vs modernisée)
3. Le facteur économique est la **responsabilité de l'évaluateur**, pas du bulletin
4. **Toujours** consigner âge chronologique ET âge apparent
5. La désuétude externe est généralement incorrigible — ne pas l'ignorer
6. Le terrain est évalué **séparément** du bâtiment
7. Les barèmes MEFQ utilisent la substitution intégrale — inadaptés au patrimoine
8. Pour l'assurance : pas de déduction pour dépréciation (sauf clause contractuelle)
9. Le coût ne reflète pas nécessairement la valeur marchande — documenter l'écart
10. L'UMPP peut justifier que la méthode du coût ne soit pas la méthode de prédilection

---

## 5. Checklist de qualité

- [ ] Le terrain est évalué séparément avec méthode documentée
- [ ] Le barème MEFQ approprié est identifié
- [ ] Les 5 facteurs de rajustement sont appliqués conjointement
- [ ] L'édition du bulletin est cohérente (pas de mélange)
- [ ] Le facteur économique est établi par l'évaluateur
- [ ] L'âge chronologique ET l'âge apparent sont consignés
- [ ] Les trois catégories de dépréciation sont analysées (physique, fonctionnelle, externe)
- [ ] La technique de dépréciation est identifiée et justifiée
- [ ] Le calcul est documenté (terrain + coût neuf − dépréciation = valeur)
- [ ] Le niveau de confiance (A/B/C) est indiqué
- [ ] La cohérence coût-valeur avec le marché est vérifiée
