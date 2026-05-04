---
name: recherche-jurisprudence-discipline
description: >
  Decisions disciplinaires de l'OEAQ, infractions sanctionnees et signaux
  de risque pour la conformite en evaluation immobiliere. Utiliser ce skill
  pour identifier les erreurs professionnelles a eviter et les regles de
  prevention derivees de la jurisprudence.
type: recherche
agents:
  - compliance-qa
sources:
  - 09-jurisprudence-discipline
---

# Skill : Recherche jurisprudence disciplinaire

## 1. Rôle et contexte

Ce skill encode les décisions disciplinaires de l'OEAQ et les signaux de risque pour la conformité. Utilisé par l'agent compliance-qa pour identifier les erreurs à prévenir et valider la conformité des rapports.

---

## 2. Connaissances encodées

### 2.1 Typologie des infractions sanctionnées

| Catégorie | Infractions | Sanction typique |
|-----------|------------|-----------------|
| **Méthodologique** | Erreur méthode coût/comparaison, omission UMPP, omission justifier rejet méthode, analyse marché incomplète | 4 500 $/chef |
| **Rapport** | Format inapproprié, informations essentielles manquantes, omission options client | 4 500 $ ou réprimande |
| **Indépendance** | Signature rapport tiers, évaluations contradictoires, tiers définit mandat, non-visite après 7 ans | 10 000 $ + limitation |
| **Entrave syndic** | Défaut répondre dans les plus brefs délais | Variable |

### 2.2 Signaux de risque — 10 règles de prévention

1. Appliquer les 3 méthodes ou **justifier explicitement le rejet**
2. **Toujours analyser l'UMPP** — indiquer usage actuel vs UMPP
3. Choisir le **format de rapport approprié** (pas toujours abrégé)
4. Procéder à une **visite récente** (7 ans = insuffisant)
5. **Signer uniquement ses propres rapports**
6. Maintenir **l'indépendance** — pas d'évaluations contradictoires sans justification
7. **Répondre au syndic rapidement**
8. **Documenter complètement** les informations essentielles
9. **Convenir soi-même du mandat** — pas de délégation à un tiers
10. **Connaissance complète des faits** avant de conclure

### 2.3 Dispositions clés

| Article | Source | Infraction |
|---------|--------|-----------|
| Art. 4 | Code déontologie | Non-conformité normes de pratique |
| Art. 9 | Code déontologie | Indépendance professionnelle |
| Art. 17(1)(2)(3) | Code déontologie | Conflits d'intérêts, indépendance |
| Art. 40-41 | Code déontologie | Connaissance des faits, signature |
| Art. 69 | Code déontologie | Répondre au syndic |
| Art. 59.2 | C. prof. | Indépendance professionnelle |

### 2.4 Décisions de référence

- **Arès (2024-2025)** : erreurs méthodologiques + rapport → 2 × 4 500 $
- **Poulin (2024)** : signature rapport tiers + non-visite → 10 000 $ + réprimande + limitation 12 mois
- **Turgeon (2025)** : évaluations contradictoires (210k vs 240k, 6 mois, 0 modification) → indépendance

### 2.5 Objectifs de la sanction (*Pigeon c. Daigneault*)

1. Protection du public (prioritaire)
2. Dissuasion de récidiver
3. Exemplarité
4. Droit d'exercer

---

## 3. Méthodologie de vérification

### Étape 1 — Identification des risques

Scanner le dossier d'évaluation pour les signaux de risque :
- Méthode rejetée sans justification ?
- UMPP non analysé ?
- Format de rapport approprié au mandat ?
- Visite récente effectuée ?
- Indépendance documentée ?

### Étape 2 — Validation contre la jurisprudence

Comparer les pratiques observées avec les infractions sanctionnées :
- Les erreurs méthodologiques identifiées dans les décisions sont-elles présentes ?
- Les exigences de rapport sont-elles respectées ?
- L'indépendance est-elle préservée ?

### Étape 3 — Documentation des risques

Documenter tout signal de risque identifié avec :
- Description du risque
- Référence à la décision disciplinaire pertinente
- Recommandation corrective

---

## 4. Règles critiques

1. **TOUJOURS** vérifier que le rejet d'une méthode est justifié dans le rapport
2. **TOUJOURS** vérifier que l'UMPP est analysé et documenté
3. **TOUJOURS** vérifier que le format de rapport est approprié au mandat
4. **TOUJOURS** vérifier qu'une visite récente a été effectuée
5. **JAMAIS** ignorer un signal de contradiction (évaluations divergentes sans justification)
6. **JAMAIS** accepter un rapport signé par un non-préparateur
7. La jurisprudence est spécifique au contexte — ne pas généraliser sans nuance
8. Les facteurs atténuants (plaidoyer, absence antécédents, expérience) réduisent la sanction
9. Les sanctions augmentent avec la répétition et l'atteinte à l'indépendance

---

## 5. Checklist de qualité

- [ ] Les trois méthodes sont appliquées ou leur rejet est justifié
- [ ] L'UMPP est analysé et documenté
- [ ] Le format de rapport est approprié au mandat
- [ ] Une visite récente est documentée
- [ ] L'indépendance est préservée et documentée
- [ ] Le mandat est convenu directement avec le client
- [ ] Les informations essentielles sont dans le rapport
- [ ] Aucune contradiction non justifiée avec des évaluations antérieures
- [ ] Le rapport est signé par son préparateur
- [ ] Les signaux de risque disciplinaire sont documentés
