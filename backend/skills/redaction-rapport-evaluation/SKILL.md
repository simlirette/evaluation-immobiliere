---
name: redaction-rapport-evaluation
description: >
  Redaction du rapport d'evaluation immobiliere complet conforme aux normes
  CUSPAP 2026 et NPP OEAQ. Utiliser ce skill pour generer le rapport final
  selon le format appropriate au mandat (narratif complet, abrege, mise a jour).
type: redaction
agents:
  - redaction
sources:
  - 00-cuspap
  - 04-oeaq-normes
  - 10-rapports-precedents-firme
---

# Skill : Rédaction — Rapport d'évaluation immobilière

## 1. Rôle et contexte

Ce skill encode la structure, le contenu et les règles de rédaction du rapport d'évaluation immobilière. L'agent rédaction l'utilise pour générer le rapport final à partir des données produites par les agents en amont (data-facts, comps-market, valuation-draft). **Le rapport doit être conforme aux 16 éléments obligatoires CUSPAP/NPP et le format doit être approprié au mandat.**

---

## 2. Connaissances encodées

### 2.1 Trois formats de rapport

| Format | Quand l'utiliser |
|--------|-----------------|
| **Narratif complet** | Immeubles complexes, commerciaux, terrains développement, mandats institutionnels |
| **Abrégé (formulaire)** | Résidentiel standard, prêt hypothécaire simple |
| **Mise à jour** | Actualisation d'une évaluation antérieure |

Le choix du format inapproprié est sanctionnable (Arès, chef 1e — Règle 2.2 Norme 2).

### 2.2 Structure — Rapport narratif complet (15 sections)

0. **Lettre de transmission** — client, objet, conclusion (chiffres + lettres), signature É.A.
1. **Page titre** — titre, adresse, référence, date
2. **Table des matières** — numérotée avec pagination
3. **Identification de l'immeuble** (éléments 1-5) — adresse, cadastre, droits évalués, but/fin, définition valeur, date, historique
4. **Étendue du travail** (élément 6) — visite, collecte, recherches, analyses, vérifications
5. **Réserves et hypothèses** (élément 7) — 11 clauses standard + extraordinaires si applicable
6. **Informations générales** — ville, secteur, marché, données municipales, zonage, infrastructures
7. **Description de l'immeuble** (éléments 1, 8) — terrain, UMPP (élément 9), bâtiment (généralités, composantes, finition), observations
8. **Évaluation et analyse** (éléments 10, 11) — présentation des 3 méthodes, justification retenues/rejetées
9. **Méthode du coût** — terrain (comparables $/m²), coût neuf, dépréciations, améliorations, conclusion
10. **Méthode de comparaison** — tableau comparables, fiches détaillées, ajustements, taux, conclusion
11. **Méthode du revenu** — RBP, vacance, RBE, frais, RNE, TGA, capitalisation, conclusion (ou justification non-application)
12. **Réconciliation** (élément 13) — résultats, analyse chaque indication, méthode prépondérante, valeur finale
13. **Attestation** (élément 12) — 7 déclarations, inspection, conclusion chiffres+lettres, signature, numéro membre
14. **Extrait NPP** — éléments applicables
15. **Annexes** (élément 16) — certificat localisation, zonage, photos, plans, comparables, qualifications

### 2.3 Structure — Rapport abrégé formulaire

| Page | Contenu |
|------|---------|
| 1 | Identification, mandant, propriétaire, conclusion, but |
| 2 | Généralités, secteur, marché, données municipales |
| 3 | Terrain, UMPP, bâtiment (généralités, composantes, finition) |
| 4 | Méthode du coût, méthode de comparaison (3-5 comparables) |
| 5 | Réconciliation, attestation, signature |
| 6 | Réserves et hypothèses, extrait NPP |
| + | Photos |

### 2.4 Les 16 éléments obligatoires (CUSPAP / NPP Règle 2.3)

1. Identification physique et légale
2. Droits évalués
3. But et fin
4. Définition de la valeur
5. Date d'évaluation
6. Étendue du travail
7. Réserves et hypothèses
8. Description de l'immeuble
9. UMPP
10. Rejet d'une méthode (justifié)
11. Approches et analyse
12. Attestation signée et datée
13. Réconciliation
14. Information sur l'inspection
15. Hypothèses extraordinaires
16. Pièces jointes

### 2.5 Attestation — 7 déclarations obligatoires

1. Faits vrais et exacts
2. Analyses/opinions neutres, objectives, propres
3. Aucun intérêt ni parti pris
4. Conformité normes OEAQ
5. Rémunération non liée à la conclusion
6. Inspection conforme aux normes (≠ inspection en bâtiment)
7. Aide professionnelle déclarée

### 2.6 Réconciliation — Règles

- PAS une moyenne des méthodes — jugement pondéré
- Méthode prépondérante justifiée
- Comparaison = preuve directe, généralement prépondérante pour résidentiel
- Coût = preuve indirecte, valeur maximum (substitution)
- Revenu = attitude investisseur, prépondérante pour immeubles locatifs

---

## 3. Méthodologie de rédaction

### Étape 1 — Déterminer le format

Évaluer le mandat et choisir narratif complet, abrégé ou mise à jour.

### Étape 2 — Assembler la lettre de transmission

Rédiger avec conclusion en chiffres + lettres, référence normes OEAQ.

### Étape 3 — Rédiger les sections d'identification

Éléments 1-7 : identification, droits, but, définition, date, étendue, réserves.

### Étape 4 — Rédiger la description

Éléments 8-9 : informations générales, description immeuble, UMPP.

### Étape 5 — Rédiger les sections méthodologiques

Éléments 10-11 : chaque méthode utilisée avec données, analyses, conclusions. Justifier tout rejet.

### Étape 6 — Rédiger la réconciliation

Élément 13 : résultats, analyse, pondération, valeur finale.

### Étape 7 — Rédiger l'attestation

Élément 12 : 7 déclarations, conclusion chiffres+lettres, signature.

### Étape 8 — Assembler les annexes

Élément 16 : tous documents de support.

---

## 4. Règles critiques

1. **TOUJOURS** inclure les 16 éléments obligatoires selon le format choisi
2. **TOUJOURS** justifier le rejet d'une méthode (élément 10, règle 2.3)
3. **TOUJOURS** analyser et documenter l'UMPP (même si conclusion = usage actuel)
4. **TOUJOURS** exprimer la valeur finale en chiffres ET en lettres
5. **TOUJOURS** inclure l'attestation signée avec les 7 déclarations
6. **JAMAIS** utiliser un format abrégé quand le mandat exige un narratif complet
7. **JAMAIS** présenter la réconciliation comme une moyenne arithmétique
8. **JAMAIS** omettre les réserves et hypothèses
9. La méthode du coût ne peut EN AUCUN CAS servir aux fins d'assurance
10. Le rapport doit être compréhensible et non trompeur (Norme 2 NPP)
11. Les hypothèses extraordinaires doivent être rappelées à chaque conclusion de valeur
12. La signature doit être celle de l'évaluateur qui a fait les analyses

---

## 5. Checklist de qualité

- [ ] Format de rapport approprié au mandat
- [ ] Les 16 éléments obligatoires sont présents
- [ ] Lettre de transmission avec conclusion en chiffres et lettres
- [ ] UMPP analysé et documenté
- [ ] Rejet de méthode justifié (élément 10)
- [ ] Réconciliation = jugement pondéré (pas une moyenne)
- [ ] Attestation complète (7 déclarations, signature, date, numéro membre)
- [ ] Réserves et hypothèses de base incluses
- [ ] Valeur finale en chiffres ET en lettres
- [ ] Données municipales documentées
- [ ] Photos et annexes incluses
- [ ] Aucune mention d'usage aux fins d'assurance pour la méthode du coût
