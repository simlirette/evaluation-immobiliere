---
name: analyse-approche-revenu
description: >
  Methodologie complete de l'approche par le revenu pour l'evaluation
  immobiliere. Utiliser ce skill pour appliquer le MRB, la capitalisation
  directe, les flux monetaires actualises ou la technique residuelle.
type: analyse
agents:
  - valuation-draft
sources:
  - 01-mefq-manuel
  - 23-baux-logement-revenu
  - 00-cuspap
  - 04-oeaq-normes
---

# Skill : Analyse — Approche par le revenu

## 1. Rôle et contexte

Ce skill encode la méthodologie de la méthode du revenu. Utilisé par l'agent valuation-draft pour les immeubles à revenus. Quatre techniques : MRB, capitalisation directe (TGA), flux monétaires actualisés, technique résiduelle.

---

## 2. Connaissances encodées

### 2.1 Quatre techniques

| Technique | Formule | Usage |
|-----------|---------|-------|
| MRB | Valeur = RBP × MRB | Estimation rapide, petits immeubles |
| Capitalisation directe | Valeur = RNE / TGA | Standard, immeubles stabilisés |
| Flux monétaires actualisés | VA des RNE + réversion | Complexe, baux long terme, transition |
| Résiduelle | Isole terrain ou bâtiment | Analyse composante |

### 2.2 Processus capitalisation directe

RBP (loyers marché × 12) → − provision inoccupation → RBE → − frais exploitation normalisés → RNE → / TGA → **Valeur**

### 2.3 Normalisation obligatoire

**Revenus** : loyers du marché (pas contractuels), ajuster faveur/estimés, inclure autres revenus.

**Dépenses** — Inclure : taxes, assurances, entretien, administration, services publics, réserve remplacement. **Exclure** : capital, amortissement hypothécaire, impôts sur le revenu.

### 2.4 TGA — Dérivation du marché

TGA = RNE comparable / Prix de vente comparable. Facteurs : risque, qualité, localisation, financement, âge, baux.

**Relation MRB/TGA** : MRB ≈ 1 / (TGA × (1 − ratio dépenses) × (1 − taux inoccupation))

### 2.5 Baux commerciaux

| Type | Dépenses payées par |
|------|-------------------|
| Brut | Locateur |
| Net | Locataire (certaines) |
| Triple net | Locataire (taxes, assurances, entretien) |
| Pourcentage | Base + % chiffre d'affaires |

### 2.6 Ratios typiques dépenses/RBE

- Multirés. petit (6-12 log.) : 35-45 %
- Multirés. moyen (12-50 log.) : 40-50 %
- Commercial : variable selon bail

---

## 3. Méthodologie d'application

### Étape 1 — Collecte des données locatives

Recevoir les données de l'agent data-facts / recherche-baux-revenus :
- Baux, loyers, services, taux d'inoccupation, dépenses

### Étape 2 — Normalisation

1. Normaliser les loyers au marché
2. Calculer RBP (tous logements au loyer du marché × 12)
3. Appliquer provision inoccupation/mauvaises créances (taux marché)
4. Calculer RBE
5. Normaliser les dépenses (exclure capital, hypothèque, impôts)
6. Calculer RNE

### Étape 3 — Sélection de la technique

| Situation | Technique recommandée |
|-----------|---------------------|
| Petit multirés., données limitées | MRB |
| Immeuble stabilisé, données suffisantes | Capitalisation directe (TGA) |
| Baux long terme, propriété en transition | Flux monétaires actualisés |
| Analyse composante (terrain ou bâtiment) | Résiduelle |

### Étape 4 — Application

**MRB** : dériver le MRB des comparables → Valeur = RBP × MRB
**TGA** : dériver le TGA des comparables → Valeur = RNE / TGA
**FMA** : projeter RNE sur 5-10 ans → actualiser + réversion
**Résiduelle** : attribuer rendement à composante connue → capitaliser résidu

### Étape 5 — Documentation

Rédiger la section revenu du rapport avec calculs détaillés, sources des données, justification des taux.

---

## 4. Règles critiques

1. **TOUJOURS** normaliser loyers ET dépenses avant application
2. **TOUJOURS** exclure dépenses de capital, amortissement hypothécaire et impôts sur le revenu
3. **TOUJOURS** dériver TGA et MRB du marché (pas d'hypothèses arbitraires)
4. **JAMAIS** confondre loyer contractuel et loyer du marché
5. **JAMAIS** utiliser le taux d'inoccupation historique de l'immeuble comme taux du marché
6. Un petit changement de TGA produit un grand changement de valeur — justifier soigneusement
7. Le ratio dépenses/RBE doit être vérifié par rapport au marché du segment
8. Les baux commerciaux (net vs brut) affectent directement le calcul — ajuster
9. La réserve de remplacement est obligatoire même si non documentée par le propriétaire
10. Le niveau de confiance (A/B/C) doit être indiqué pour cette approche

---

## 5. Checklist de qualité

- [ ] Les loyers sont normalisés au marché (pas contractuels)
- [ ] La provision inoccupation utilise le taux du marché local
- [ ] Les dépenses sont normalisées (excluant capital, hypothèque, impôts)
- [ ] La réserve de remplacement est incluse
- [ ] Le TGA ou MRB est dérivé de comparables du marché
- [ ] La technique est appropriée à la situation (MRB, TGA, FMA, résiduelle)
- [ ] Les calculs sont détaillés et documentés
- [ ] Les sources des données locatives sont citées
- [ ] Le ratio dépenses/RBE est cohérent avec le marché
- [ ] Le niveau de confiance (A/B/C) est indiqué
