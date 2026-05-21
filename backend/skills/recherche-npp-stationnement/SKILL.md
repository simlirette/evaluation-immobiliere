---
name: recherche-npp-stationnement
description: >
  Normes, methodologie et donnees pour l'evaluation d'immeubles de stationnement :
  stationnements interieurs (garages etages), stationnements de surface, cases
  individuelles en copropriete, et stationnements commerciaux. Utiliser ce skill
  pour tout mandat impliquant un terrain ou batiment dont la fonction principale
  ou complementaire est le stationnement.
type: recherche
agents:
  - data-facts
  - valuation-draft
  - compliance-qa
sources:
  - 04-oeaq-normes
  - 00-cuspap
  - 01-mefq-manuel
  - 16-droit-immobilier
dependencies:
  - recherche-mefq-methodologie
  - recherche-normes-professionnelles
---

# Skill : Recherche NPP — Evaluation de stationnements

## 1. Role et contexte

Ce skill encode les regles methodologiques et normatives applicables a l'evaluation d'immeubles de stationnement. Les stationnements constituent une categorie distincte en raison de :
- Leur nature hybride (terrain, batiment, exploitation)
- La predominance de l'approche revenu pour les stationnements exploites
- Les specificites des comparables ($/case, $/m2, taux d'occupation)
- L'impact de la reglementation de stationnement sur la valeur

Ta mission : fournir les cadres methodologiques precis pour les trois principaux types de mandats de stationnement.

---

## 2. Connaissances encodees

### 2.1 Typologie des immeubles de stationnement

| Type | Description | Methode privilegiee |
|------|------------|-------------------|
| **Terrain de stationnement de surface** | Terrain asphalte/pave, exploitation ou non | Comparaison (terrain) + revenu si exploite |
| **Garage etages (structure)** | Batiment multi-niveaux, cases couvertes | Revenu + cout + comparaison |
| **Garage souterrain** | Stationnement sous immeuble, cases vendues ou louees | Revenu + comparaison ($/case) |
| **Case individuelle en copropriete** | Fraction d'une copropriete, stationnement interieur | Comparaison ($/case) |
| **Stationnement commercial independant** | Exploitation commerciale, billetterie | Revenu (capitalisation revenus bruts) |
| **Stationnement de terrain vague** | Terrain non amenage, usage transitoire | Comparaison terrain (UMPP = potentiel futur) |

### 2.2 Methode du revenu — stationnements commerciaux

#### Indicateurs cles

| Indicateur | Definition | Source habituelle |
|-----------|-----------|------------------|
| **Taux d'occupation** | Nombre cases occupees / total cases | Operateur, observation |
| **Revenu brut/case/an** | Loyer annuel moyen par case | Comparables, operateurs |
| **Revenu mensuel moyen** | Abonnements + transactions / 12 | Rapports d'exploitation |
| **Mix abonnements/transactions** | % revenus abonnements vs a la piece | Operateur |
| **MRB (stationnement)** | Prix vente / Revenu brut annuel | Transactions comparables |
| **TGA (stationnement)** | RNE / Prix vente | Transactions comparables |

#### Formule application

```
RBP = Nombre cases × Revenu moyen/case/an
RBE = RBP × (1 - Taux inoccupation/vacance)
Frais exploitation = Administration + Entretien + Assurances + Taxes + Reserves
RNE = RBE - Frais exploitation
Valeur = RNE / TGA (ou RBP × MRB)
```

#### Frais d'exploitation typiques (stationnement)

| Poste | % du RBB approximatif |
|-------|----------------------|
| Administration/gestion | 8-15 % |
| Taxes foncieres | Variable (inscrites au role) |
| Assurances | 1-3 % |
| Entretien/reparations | 3-8 % |
| Services publics | 2-5 % |
| Securite | 3-7 % |
| Reserve remplacement | 3-5 % |

### 2.3 Methode de comparaison — indicateurs de valeur

| Indicateur | Application | Avantages |
|-----------|------------|---------|
| **$/case** | Cases individuelles, garages | Directement comparable |
| **$/m2 terrain** | Terrains de surface | Coherence avec terrains comparables |
| **$/place de stationnement/an** (loyer) | Calibrage approche revenu | Ancre dans le marche locatif |
| **Multiplicateur de revenu brut (MRB)** | Stationnements commerciaux | Simple, derive du marche |

### 2.4 Cases en copropriete

L'evaluation d'une **case de stationnement en copropriete** presente des particularites :

#### Statut juridique possible

| Statut | Nature | Impact evaluation |
|--------|--------|------------------|
| **Partie privative** (fraction distincte) | Inscrite separement au role, vendable independamment | Evaluation comme bien distinct |
| **Partie commune a usage exclusif** | Non inscrite separement, attachee a l'unite | Contribution a la valeur de la fraction |
| **Partie commune ordinaire** | Quote-part dans les parties communes | Incluse dans la valeur de la fraction, non separable |

#### Facteurs de valeur d'une case privative

- Localisation dans le garage (proche ascenseur, rez-de-chaussee vs niveau inferieur)
- Dimensions (standard, handicap, tandem)
- Acces independant ou passage obligatoire
- Securite du garage
- Frais de copropriete associes
- Transactions comparables de cases dans l'immeuble ou voisin

### 2.5 Reglementation et impact sur la valeur

| Facteur reglementaire | Impact potentiel |
|----------------------|-----------------|
| **Norme de stationnement minimum** | Surplus ou deficit de cases par rapport a la norme |
| **Zone ou le stationnement est reglemente** | Revenus limites ou eleves selon offre/demande locale |
| **Plan de mobilite urbaine** | Tendance a reduire les normes → impact sur valeur terrain |
| **Zonage transit-oriente (TOD)** | Reduction des normes de stationnement, valeur deprimee |
| **Tarification sur rue** | Concurrence directe pour stationnement de surface |
| **Accessibilite universelle** | Nombre minimum de cases adaptees obligatoires |

### 2.6 UMPP des terrains de stationnement

Pour un terrain de stationnement de surface en zone urbaine :
- L'UMPP peut etre le **developpement immobilier** (residentiel ou commercial) plutot que le stationnement
- Le stationnement peut etre un **usage transitoire** en attendant le developpement
- L'evaluateur doit analyser : zonage, potentiel de developpement, comparables terrains developpes, faisabilite financiere

**Usage courant vs UMPP** :
```
Si UMPP ≠ usage courant → valeur ≥ valeur selon usage courant
Le stationnement peut etre une charge si terrain vaut plus nu (sous-utilisation)
```

### 2.7 Regles NPP applicables

- **Norme 1, el. 11 (UMPP)** : Analyser obligatoirement si l'usage de stationnement est l'UMPP ou si un developpement serait plus profitable
- **Norme 1, el. 12 (methodes)** : Appliquer au moins deux methodes pour les stationnements commerciaux
- **NPP Norme 2** : Si rapport abrege, conditions d'utilisation doivent etre respectees — stationnements commerciaux complexes requierent generalement un narratif complet

---

## 3. Methodologie de recherche

### Etape 1 — Identifier le type de stationnement et l'usage

Determiner :
- Type physique (surface, structure, souterrain, case privative)
- Mode d'exploitation (commercial, residentiel, mixte, vacant)
- Statut juridique (pleine propriete, copropriete, bail)
- Localisation urbaine et contexte de mobilite

### Etape 2 — Collecter les donnees de revenus

- Obtenir les rapports d'exploitation (3 ans si disponibles)
- Identifier le mix revenus (abonnements, a la piece, locations commerciales)
- Obtenir les loyers des cases si stationnement residentiel
- Comparer avec les loyers/taux du marche local

### Etape 3 — Identifier les comparables

- Transactions de stationnements comparables (meme type, meme zone)
- Transactions de cases individuelles en copropriete si applicable
- Derivation des indicateurs de valeur ($/case, MRB, TGA)

### Etape 4 — Analyser l'UMPP

- Verifier le zonage et le potentiel de developpement
- Comparer la valeur selon usage stationnement vs developpement
- Conclure sur l'UMPP et son impact sur la valeur

### Etape 5 — Appliquer les methodes et reconcilier

- Appliquer methode revenu (si exploitation)
- Appliquer methode comparaison (transactions)
- Appliquer methode cout (si structure specifique)
- Reconcilier en privilegiant la methode la mieux documentee

---

## 4. Regles critiques

1. **TOUJOURS** analyser l'UMPP pour les terrains de stationnement de surface en zone urbanisee
2. **TOUJOURS** distinguer le statut juridique de la case (privative, commune usage exclusif, commune)
3. **TOUJOURS** normaliser les revenus d'exploitation (exclure les depenses de capital)
4. **JAMAIS** utiliser un MRB ou TGA derive d'un marche different (residentiel vs commercial)
5. **JAMAIS** omettre d'identifier le potentiel de developpement si le terrain est sous-utilise
6. En copropriete, verifier si la case est une fraction distincte inscrite au role ou partie commune
7. L'acces exclusif a une partie commune n'en fait pas une partie privative
8. Les tendances de mobilite urbaine (TOD, reduction normes) peuvent deprimer significativement la valeur des stationnements de surface
9. Toujours verifier la tarification sur rue a proximite (concurrence directe)
10. La methode du cout est rarement la methode principale pour un stationnement existant

---

## 5. Checklist de qualite

- [ ] Type de stationnement identifie (surface/structure/souterrain/case)
- [ ] Statut juridique de l'immeuble ou de la case verifie
- [ ] UMPP analyse et documente
- [ ] Revenus d'exploitation collectes et normalises (si exploitation)
- [ ] Frais d'exploitation normalises (excluant depenses de capital)
- [ ] Indicateurs de marche (TGA, MRB, $/case) derives de comparables
- [ ] Comparables de ventes identifies et analyses
- [ ] Reglementation de stationnement verifiee (normes, TOD)
- [ ] Au moins deux methodes appliquees ou le rejet justifie
- [ ] Reconciliation documentee avec justification du poids accorde
- [ ] Format de rapport adapte a la complexite du mandat
```

---