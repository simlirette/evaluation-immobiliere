---
name: redaction-rapport-conformite
description: >
  Generation du rapport de conformite structure documentant les resultats
  de verification des 18 gates KQG, les non-conformites et les signaux
  de risque disciplinaire. Utiliser ce skill pour produire le livrable
  de l'agent compliance-qa.
type: redaction
agents:
  - compliance-qa
sources:
  - 00-cuspap
  - 04-oeaq-normes
  - 09-jurisprudence-discipline
---

# Skill : Rédaction — Rapport de conformité

## 1. Rôle et contexte

Ce skill encode la structure et les règles de rédaction du rapport de conformité, livrable de l'agent compliance-qa. **Ce rapport n'est pas le rapport d'évaluation.** C'est un document interne de contrôle qualité destiné à l'évaluateur agréé, à l'agent rédaction et au dossier de travail.

---

## 2. Connaissances encodées

### 2.1 Structure du rapport (7 sections)

**En-tête** :
- Identifiant dossier (numéro mandat)
- Date de vérification
- Version du brouillon vérifié (hash ou version)
- Statut global : GO / NO_GO / CONDITIONNEL

**Section 1 — Résumé exécutif** :
- Statut global
- Nombre de gates P0 en FAIL
- Nombre de gates P1 en WARNING
- Nombre de signaux de risque disciplinaire
- Actions requises avant finalisation

**Section 2 — Résultats par gate** :
Pour chaque gate KQG-001 à KQG-018 :
- ID, priorité (P0/P1/P2), domaine
- Statut : PASS / FAIL / WARNING / N/A
- Détail de la vérification effectuée
- Evidence (éléments vérifiés)
- Non-conformité (si FAIL/WARNING)
- Recommandation corrective

**Section 3 — Non-conformités détaillées** :
Pour chaque non-conformité :
- Référence gate (KQG-XXX)
- Norme enfreinte (CUSPAP article, NPP norme/règle, Code déontologie article)
- Description (ce qui manque ou est incorrect)
- Impact sur la validité du rapport
- Sévérité : Critique / Élevée / Moyenne
- Recommandation corrective précise
- Statut : Ouvert / En correction / Résolu

**Section 4 — Signaux de risque disciplinaire** :
Pour chaque signal détecté :
- Type (rapport incomplet, conclusion prédéterminée, etc.)
- Description du signal observé
- Référence jurisprudence (Arès, Poulin, Turgeon)
- Sévérité : Critique / Élevée
- Action requise (revue humaine / correction avant finalisation)

**Section 5 — Vérification méthodologique** :
- Méthodes considérées (≥ 2 si pertinent)
- Méthode unique justifiée
- UMPP analysé et documenté
- Réconciliation documentée
- Ajustements justifiés et dérivés du marché
- Ventes antérieures du sujet analysées (< 3 ans)
- Données normalisées (revenus/dépenses)
- Format rapport approprié au mandat

**Section 6 — Recommandations** :
Liste ordonnée par priorité :
1. Actions bloquantes (gates P0 en FAIL)
2. Actions importantes (gates P1 en WARNING)
3. Améliorations suggérées

**Section 7 — Traçabilité** :
- Gates vérifiés (n/18)
- Normes référencées
- Sources de données vérifiées
- Validation humaine requise OUI/NON — statut

### 2.2 Logique de statut global

| Statut | Condition |
|--------|----------|
| **GO** | Tous gates P0 en PASS, aucun signal critique |
| **CONDITIONNEL** | Gates P0 en PASS, mais gates P1 en WARNING nécessitant revue |
| **NO_GO** | Au moins un gate P0 en FAIL ou signal critique détecté |

### 2.3 Échelle de sévérité

| Sévérité | Définition | Action |
|----------|-----------|--------|
| **Critique** | Violation P0 ou signal disciplinaire grave | Bloquer — revue humaine obligatoire |
| **Élevée** | Violation P1 ou lacune majeure | Signaler — correction recommandée |
| **Moyenne** | Lacune mineure ou amélioration possible | Documenter — amélioration suggérée |

---

## 3. Méthodologie de rédaction

### Étape 1 — Collecter les résultats

Récupérer les résultats de vérification des 18 gates KQG produits par le skill analyse-conformite.

### Étape 2 — Rédiger l'en-tête

Déterminer le statut global selon la logique GO/NO_GO/CONDITIONNEL.

### Étape 3 — Rédiger le résumé exécutif

Compiler les compteurs (P0 FAIL, P1 WARNING, signaux) et lister les actions requises.

### Étape 4 — Détailler les résultats par gate

Pour chaque gate, rédiger une entrée structurée avec statut, détail, evidence, non-conformité et recommandation.

### Étape 5 — Documenter les non-conformités

Pour chaque FAIL/WARNING, créer une entrée détaillée avec norme enfreinte, impact, sévérité et recommandation actionnable.

### Étape 6 — Documenter les signaux disciplinaires

Pour chaque signal détecté, référencer la jurisprudence pertinente et préciser l'action requise.

### Étape 7 — Compléter vérification méthodologique, recommandations et traçabilité

Remplir les sections 5, 6 et 7 du rapport.

---

## 4. Règles critiques

1. **Ton factuel et neutre** — pas d'interprétation, pas de prose narrative
2. **Structuré par gate** — chaque non-conformité = une entrée séparée
3. **Références précises** — article, norme, règle, élément spécifique
4. **Recommandations actionnables** — dire exactement quoi corriger
5. **TOUT gate P0 en FAIL → statut NO_GO** obligatoirement
6. **Signal critique → revue humaine obligatoire** avant toute action
7. **JAMAIS** déclarer la conformité CUSPAP/OEAQ — le rapport est indicatif, la validation humaine est toujours requise
8. **Conserver au dossier de travail** — le rapport fait partie du work-file
9. **Vérifier les 18 gates** — aucun gate ne peut être omis (N/A est acceptable, omission non)
10. **Un statut GO ne signifie pas que l'évaluation est correcte** — seulement que les exigences formelles sont satisfaites

---

## 5. Checklist de qualité

- [ ] Les 7 sections du rapport sont présentes
- [ ] Le statut global est cohérent avec les résultats des gates
- [ ] Chaque gate a un statut (PASS/FAIL/WARNING/N/A)
- [ ] Chaque non-conformité a une norme enfreinte identifiée
- [ ] Chaque recommandation est actionnable et spécifique
- [ ] Les signaux disciplinaires sont documentés avec jurisprudence
- [ ] La traçabilité indique 18/18 gates vérifiés
- [ ] La validation humaine est marquée comme requise
- [ ] Le rapport est conservé au dossier de travail
