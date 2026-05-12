---
name: recherche-registre-cadastre
description: >
  Consulter le Registre foncier du Québec et les données cadastrales pour vérifier
  la propriété, les charges réelles et les droits affectant le bien.
type: recherche
agents:
  - data-facts
  - comps-market
sources:
  - registre_foncier
  - cadastre_renove
  - role_municipal
---

## Objectif

Obtenir les informations officielles sur le titre de propriété, les charges réelles (hypothèques, servitudes) et les données cadastrales du bien sujet et des comparables.

## Procédure

### 1. Recherche au Registre foncier

**Accès :** Registre foncier du Québec en ligne (MRNF) — `registrefoncier.gouv.qc.ca`

**Informations à extraire :**
- Numéro de lot (cadastre rénové) et description légale
- Actes inscrits par ordre chronologique inverse :
  - Acte de vente le plus récent (prix, date, parties)
  - Hypothèques actives (créancier, montant initial, date)
  - Servitudes (conventionnelles, légales, d'utilité publique)
  - Restrictions (clause de préemption, droit de superficie, emphytéose)
  - Avis de nouvelles adresses, corrections cadastrales

**Format matricule municipal :** `####-##-####-#-###` (17 caractères)

### 2. Données cadastrales

**Cadastre rénové (BDIMMO / MRNF) :**
- Superficie officielle du lot en m²
- Dimensions (façade × profondeur pour lots rectangulaires)
- Forme du lot (rectangulaire, irrégulier, d'angle, en drapeau)
- Mitoyenneté (lots adjacents)

**Attention aux écarts :**
- Superficie au rôle municipal ≠ superficie cadastrale si morcellement ou lotissement récent
- Toujours indiquer quelle source prime (cadastre rénové = officiel)

### 3. Rôle d'évaluation municipal

**Accès :** Portail de la municipalité concernée (ex. île-des-sœurs.ville.montreal.qc.ca)

**Données à extraire :**
- Matricule foncier (identifiant unique dans le rôle)
- Valeur imposable : terrain + bâtiment + total
- Description physique : type, superficie, nombre d'unités, année construction
- Année de dépôt du rôle et date de référence triennale
- Taux de taxation global (municipal + scolaire)

**Note LFM :** La valeur au rôle est établie à une date de référence du passé (ex. 2023-07-01 pour le rôle 2025–2027). Ne pas confondre valeur réelle LFM avec valeur marchande actuelle.

### 4. Utilisation pour les comparables

Pour chaque comparable retenu :
- Vérifier l'inscription de la vente au Registre foncier (acte de vente officiel)
- Confirmer que le prix déclaré correspond au prix payé (pas de prise en charge hypothécaire non déclarée)
- Identifier les transactions entre parties liées (même nom, même adresse)

## Sources officielles

| Source | URL / accès | Données |
|--------|------------|---------|
| Registre foncier | registrefoncier.gouv.qc.ca | Titres, hypothèques, servitudes |
| Cadastre rénové | bdimmo.gouv.qc.ca | Lots, superficies officielles |
| Portail Montréal | montreal.ca/evaluations | Rôle, taxes, description |
| Portail Québec | ville.quebec.qc.ca/evaluation | Rôle agglomération |
