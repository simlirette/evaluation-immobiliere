# Analyse — Rédaction du rapport de conformité

> Synthèse exhaustive de la structure et du contenu du rapport de conformité généré par l'agent compliance-qa, incluant les non-conformités structurées, les recommandations correctives et les signaux de risque disciplinaire.

---

## 1. Objectif du rapport de conformité

Le rapport de conformité est le livrable de l'agent compliance-qa. Il documente le résultat de la vérification du dossier d'évaluation contre les 18 gates KQG, les normes CUSPAP/NPP et les signaux de risque disciplinaire.

**Le rapport de conformité n'est pas le rapport d'évaluation.** C'est un document interne de contrôle qualité destiné à :
- L'évaluateur agréé (pour validation humaine)
- L'agent redaction (pour intégrer les corrections)
- Le dossier de travail (pour traçabilité)

---

## 2. Structure du rapport de conformité

### 2.1 En-tête

| Champ | Contenu |
|-------|---------|
| Identifiant dossier | Numéro unique du mandat |
| Date de vérification | Date de génération du rapport |
| Version du rapport d'évaluation vérifié | Hash ou version du brouillon |
| Statut global | GO / NO_GO / CONDITIONNEL |

### 2.2 Section 1 — Résumé exécutif

- Statut global (GO/NO_GO/CONDITIONNEL)
- Nombre de gates P0 en FAIL
- Nombre de gates P1 en WARNING
- Nombre de signaux de risque disciplinaire
- Actions requises avant finalisation

### 2.3 Section 2 — Résultats par gate

Pour chaque gate KQG (001-018) :

| Champ | Contenu |
|-------|---------|
| ID du gate | KQG-001 à KQG-018 |
| Priorité | P0 / P1 / P2 |
| Domaine | Mandat, work-file, scope, etc. |
| Statut | PASS / FAIL / WARNING / N/A |
| Détail | Description de la vérification effectuée |
| Evidence | Référence aux éléments vérifiés |
| Non-conformité | Description précise si FAIL/WARNING |
| Recommandation | Action corrective recommandée |

### 2.4 Section 3 — Non-conformités détaillées

Pour chaque non-conformité identifiée :

| Champ | Contenu |
|-------|---------|
| Référence gate | KQG-XXX |
| Norme enfreinte | CUSPAP article, NPP norme/règle, Code déontologie article |
| Description | Ce qui manque ou ce qui est incorrect |
| Impact | Effet sur la validité du rapport |
| Sévérité | Critique / Élevée / Moyenne |
| Recommandation | Action corrective précise |
| Statut | Ouvert / En correction / Résolu |

### 2.5 Section 4 — Signaux de risque disciplinaire

Pour chaque signal détecté (KQG-017) :

| Champ | Contenu |
|-------|---------|
| Type de signal | Rapport incomplet, conclusion prédéterminée, etc. |
| Description | Détail du signal observé |
| Référence jurisprudence | Décision disciplinaire pertinente (Arès, Poulin, Turgeon) |
| Sévérité | Critique / Élevée |
| Action requise | Revue humaine obligatoire / Correction avant finalisation |

### 2.6 Section 5 — Vérification méthodologique

| Vérification | Statut |
|-------------|--------|
| Méthodes considérées (≥ 2 si pertinent) | PASS/FAIL |
| Méthode unique justifiée | PASS/FAIL/N/A |
| UMPP analysé et documenté | PASS/FAIL |
| Réconciliation documentée | PASS/FAIL |
| Ajustements justifiés et dérivés du marché | PASS/FAIL |
| Ventes antérieures du sujet analysées (< 3 ans) | PASS/FAIL |
| Données normalisées (revenus/dépenses) | PASS/FAIL/N/A |
| Format rapport approprié au mandat | PASS/FAIL |

### 2.7 Section 6 — Recommandations

Liste ordonnée par priorité :
1. Actions bloquantes (gates P0 en FAIL)
2. Actions importantes (gates P1 en WARNING)
3. Améliorations suggérées

### 2.8 Section 7 — Traçabilité

| Champ | Contenu |
|-------|---------|
| Gates vérifiés | 18/18 ou n/18 |
| Normes référencées | CUSPAP, NPP, Code déontologie |
| Sources de données vérifiées | Liste des sources cross-référencées |
| Validation humaine | Requise OUI/NON — statut |

---

## 3. Règles de rédaction

### 3.1 Ton et format

- Factuel et neutre — pas d'interprétation
- Structuré par gate — pas de prose narrative
- Chaque non-conformité = une entrée séparée
- Références précises (article, norme, règle, élément)
- Recommandations actionnables et spécifiques

### 3.2 Statut global

| Statut | Condition |
|--------|----------|
| **GO** | Tous les gates P0 en PASS, aucun signal critique |
| **CONDITIONNEL** | Gates P0 en PASS, mais gates P1 en WARNING nécessitant revue |
| **NO_GO** | Au moins un gate P0 en FAIL ou signal critique détecté |

### 3.3 Escalade

- Signal critique → revue humaine obligatoire avant toute action
- Non-conformité P0 → bloquer la chaîne de production
- Non-conformité P1 → signaler mais ne pas bloquer

---

## 4. Pièges et limites

- Le rapport de conformité ne remplace pas le jugement de l'évaluateur agréé
- Un statut GO ne signifie pas que l'évaluation est correcte — seulement que les exigences formelles sont satisfaites
- Les signaux de risque disciplinaire sont basés sur la jurisprudence disponible — d'autres risques peuvent exister
- Le rapport doit être conservé au dossier de travail (work-file) pour traçabilité
- La validation humaine est toujours requise — le statut automatique est indicatif seulement
