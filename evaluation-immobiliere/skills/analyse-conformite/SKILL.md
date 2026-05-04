---
name: analyse-conformite
description: >
  Verification de conformite d'un dossier d'evaluation immobiliere contre
  les normes CUSPAP 2026, NPP OEAQ, Code de deontologie et les 18 gates
  KQG. Utiliser ce skill pour valider la conformite avant finalisation.
type: analyse
agents:
  - compliance-qa
sources:
  - 00-cuspap
  - 04-oeaq-normes
  - 05-oeaq-reglements
  - 09-jurisprudence-discipline
---

# Skill : Analyse — Conformité

## 1. Rôle et contexte

Ce skill encode le processus complet de vérification de conformité. Utilisé par l'agent compliance-qa pour valider chaque dossier contre toutes les portes de qualité avant finalisation. **Aucune conformité CUSPAP/OEAQ ne peut être déclarée sans validation humaine par un évaluateur agréé.**

---

## 2. Connaissances encodées

### 2.1 Les 12 gates P0 (bloquants)

| Gate | Domaine | Vérification clé |
|------|---------|-----------------|
| KQG-001 | Mandat | Client, utilisateurs, usage, but, définition valeur, dates |
| KQG-002 | Work-file | Manifest avant signature, rétention 7 ans |
| KQG-003 | Scope/inspection | Inspection documentée, limites, sources, fiabilité |
| KQG-004 | IA/AVM | Pas de conclusion finale basée uniquement sur IA. Validation humaine |
| KQG-005 | Hypothèses/réserves | Type, impact, source, justification. Écarts directives = consentement |
| KQG-006 | Certification | Signature évaluateur, pas de signature automatique |
| KQG-007 | Indépendance | Questionnaire conflit, divulgation, consentement |
| KQG-008 | Confidentialité | Destinataires autorisés, consentement photos |
| KQG-009 | Consentement | Client informé, changement scope = nouveau consentement |
| KQG-010 | Tiers essentiels | Déclaration rôle, étendue, compétence |
| KQG-011 | Méthodologie | ≥ 2 méthodes considérées ou justification méthode unique |
| KQG-012 | Réconciliation | Revue processus, droits, date, raisonnement → valeur finale |

### 2.2 Les 5 gates P1 (importants)

| Gate | Vérification clé |
|------|-----------------|
| KQG-013 | Examen/revue : complétude, données, méthodes, conclusions |
| KQG-014 | Donnée municipale ≠ conclusion valeur marchande sans analyse |
| KQG-015 | Module municipal séparé du workflow privé |
| KQG-016 | Proportion médiane : ventes admissibles vs privées |
| KQG-017 | Signaux disciplinaires : rapport incomplet, conclusion prédéterminée, incohérence |

### 2.3 Signaux de risque disciplinaire

| Signal | Sévérité | Action |
|--------|----------|--------|
| Rapport incomplet | Élevée | Bloquer P0 |
| Conclusion prédéterminée | Critique | Bloquer P0 |
| Méthode rejetée sans justification | Élevée | Flag P1 |
| UMPP non analysé | Élevée | Flag P1 |
| Évaluations contradictoires | Critique | Bloquer P0 |
| Signature rapport tiers | Critique | Bloquer P0 |
| Non-visite ancienne | Élevée | Flag P1 |

### 2.4 Couches normatives

| Couche | Prévalence |
|--------|-----------|
| Lois provinciales (LFM, CCQ, C. prof.) | Absolue |
| CUSPAP 2026 + NPP OEAQ | Obligatoire pour membres |
| IAAO, IPMS | Consultatif seulement |

---

## 3. Méthodologie de vérification

### Étape 1 — Vérification P0 (bloquants)

Pour chaque gate P0, vérifier la présence et la complétude de l'evidence attendue :
1. KQG-001 : mandat complet ?
2. KQG-002 : work-file manifest existe ?
3. KQG-003 : inspection documentée ?
4. KQG-004 : sorties IA validées par humain ?
5. KQG-005 : hypothèses et réserves documentées ?
6. KQG-006 : certification signée ?
7. KQG-007 : conflit vérifié ?
8. KQG-008 : confidentialité respectée ?
9. KQG-009 : consentement client obtenu ?
10. KQG-010 : tiers déclarés ?
11. KQG-011 : méthodologie justifiée ?
12. KQG-012 : réconciliation documentée ?

**Si un gate P0 échoue → BLOQUER la finalisation.**

### Étape 2 — Vérification P1 (importants)

Pour chaque gate P1, vérifier et signaler :
13. KQG-013 : processus de revue documenté ?
14. KQG-014 : données municipales étiquetées ?
15. KQG-015 : module municipal séparé ?
16. KQG-016 : proportion médiane correcte ?
17. KQG-017 : signaux disciplinaires détectés ?

**Si un gate P1 échoue → SIGNALER pour revue humaine.**

### Étape 3 — Vérification P2 (spécialisés)

18. KQG-018 : profil spécialisé séparé si assurance/expropriation/fonds ?

### Étape 4 — Rapport de conformité

Produire un rapport structuré avec :
- Statut de chaque gate (PASS/FAIL/WARNING)
- Détail des non-conformités
- Recommandations correctives
- Signaux de risque disciplinaire

---

## 4. Règles critiques

1. **TOUT gate P0 en FAIL → BLOQUER** la finalisation du rapport
2. **TOUT gate P1 en FAIL → REVUE HUMAINE** obligatoire
3. **JAMAIS** déclarer la conformité CUSPAP/OEAQ sans validation humaine
4. **JAMAIS** ignorer un signal de risque disciplinaire
5. Les règles coercitives NPP sont **absolues** — aucune dérogation
6. Les règles directives NPP sont modifiables avec consentement client et explication
7. Les standards IAAO sont **consultatifs** — ne jamais les traiter comme obligations
8. Le work-file doit exister **avant** l'émission du rapport (pas après)
9. Aucune signature automatique permise
10. Aucune conclusion basée uniquement sur IA/AVM

---

## 5. Checklist de qualité

- [ ] Les 12 gates P0 sont vérifiés (PASS/FAIL)
- [ ] Les 5 gates P1 sont vérifiés (PASS/WARNING)
- [ ] Le gate P2 est vérifié si applicable
- [ ] Les signaux de risque disciplinaire sont scannés
- [ ] Le rapport de conformité est produit
- [ ] Les non-conformités sont documentées avec recommandations
- [ ] Le statut global est déterminé (GO/NO_GO)
- [ ] La validation humaine est requise avant déclaration de conformité
