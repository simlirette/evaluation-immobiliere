# Plan directeur complet post-merge `85555aa` (2026-04-30)

## 1) État actuel complet du projet

## 1.1 Niveau de maturité

Le projet dispose d'une base **runtime v0 opérationnelle** avec:
- moteur local (`engine/`) ;
- API locale (`api.py`) ;
- cockpit ops HTML ;
- jeux de fixtures et cas runtime ;
- rapports d'intégrité, qualité, delta et handoff ;
- gates ops et tests automatiques.

## 1.2 Ce qui est déjà en place (synthèse)

### A. Chaîne fonctionnelle d'évaluation
- Pipeline d'agents métier documenté (`integration/PIPELINE-RUNTIME-ASTON-V0.yaml`).
- Artefacts de sortie structurés pour les approches comparative/coût/revenu.
- Contrats de sortie, checklist conformité, règles v0.

### B. Industrialisation technique v0
- Manifest runtime, registry runtime, delta runtime, handoff ops.
- Vérifications de cohérence/intégrité/contrats/schemas.
- Verrou anti-concurrence pré-réponses.
- Ops doctor et gates de paquet évaluateurs.

### C. Qualité et preuve
- Suite de tests étendue (`tests/test_*`).
- Cas nominal + cas dégradés (source manquante, incohérences unités, faible confiance, etc.).
- Traçabilité par audits JSONL, source index, rapports markdown/json.

### D. Intégration Aston préparée mais partielle
- Mapping d'outils Aston documenté.
- Cible persistence/streaming décrite.
- Agent configs YAML définis.
- Architecture cible annoncée comme adaptation directe Aston.

## 1.3 Limites actuelles (constat)

- Runtime encore majoritairement **simulateur local guidé par fixtures**, pas branché de bout en bout à un engine Aston réel.
- Connexions réelles de données externes (comparables, registres, OCR robuste) non finalisées.
- Persistance sessionnelle Aston-like (sessions live + événements stream + stockage central) seulement spécifiée.
- UI métier complète d'exploitation évaluateur (pas seulement cockpit ops) à compléter.
- Déploiement production, sécurité opérationnelle avancée et SLO/SLA non finalisés.

---

## 2) Comparaison avec infrastructure Aston (écart structuré)

## 2.1 Équivalents déjà couverts

1. **Orchestration par étapes agentisées**: couverte au niveau design/runtime local.
2. **Artefacts structurés et auditables**: largement couverts.
3. **Quality gates/contrats/schemas**: couverts avec plusieurs contrôles.
4. **Préparation persistence/streaming**: spécification disponible.

## 2.2 Équivalents manquants ou incomplets

1. **Agent loop Aston réel** (session lifecycle, retries/budgets natifs).
2. **Streaming live consommable UI produit** (événements utilisateur temps réel en conditions réelles).
3. **Persistance centrale robuste** (sessions/artifacts/audit/events/knowledge) avec migrations et reprise.
4. **Tooling runtime branché réel** (OCR prod, connecteurs comparables, registres, cadastre, etc.).
5. **Sécurité et conformité production** (IAM, secrets, chiffrement, rétention, journal d'accès).
6. **Ops production** (monitoring, alerting, runbooks incident, backup/restore, PRA).
7. **CI/CD complète + environnements** (dev/staging/prod, promotion contrôlée).
8. **Validation métier finale terrain** (calibration évaluateurs consolidée, acceptance formelle).

---

## 3) Points équivalents manquants (backlog cible Aston)

## 3.1 Priorité P0 (bloquants avant “outil pro complet”)

- Brancher l'exécution sur boucle Aston réelle.
- Mettre en place persistence sessionnelle et event stream robustes.
- Brancher outils réels d'extraction/acquisition de données.
- Couvrir la sécurité prod minimale (secrets, auth, audit accès).
- Obtenir benchmark de qualité métier sur dossiers réels validés.

## 3.2 Priorité P1 (professionnalisation)

- Cockpit évaluateur complet (revue, correction, validation, historique).
- CI/CD avec quality gates bloquants et promotion environnementale.
- Observabilité avancée (SLO, alertes, corrélation run/session/artefact).
- Contrôles coûts/performance (latence, coût token, coût data provider).

## 3.3 Priorité P2 (scale & optimisation)

- Optimisations de throughput multi-dossiers.
- Stratégie cache/réexécution incrémentale.
- Hardening haute disponibilité et reprise sinistre.
- Automatisation analytique post-déploiement (drift qualité, drift sources).

---

## 4) Plan exhaustif par phases (jusqu'au déploiement)

## Phase A — Baseline et cadrage d'exécution (1 semaine)
- Geler baseline post-merge `85555aa`.
- Produire matrice “existant vs Aston cible” versionnée.
- Définir KPI de réussite par domaine: métier, technique, ops, sécurité.

## Phase B — Contrats d'intégration Aston réels (1 à 2 semaines)
- Transformer les spécifications existantes en contrats exécutables (session/events/artifacts).
- Définir précisément erreurs/retries/timeouts/idempotence.
- Versionner les contrats et tests de compatibilité.

## Phase C — Branchement engine réel & outils runtime (2 à 4 semaines)
- Brancher `AgentConfig` immobiliers dans la boucle Aston réelle.
- Connecter outils réels: lecture documents, OCR, écriture artefacts, audit append-only.
- Valider exécution d'un dossier réel de bout en bout en environnement dev.

## Phase D — Persistance, streaming et API produit (2 à 3 semaines)
- Implémenter stockage sessions/artefacts/events/knowledge snapshots.
- Exposer endpoints session/start/stream/artefacts/review.
- Garantir reprise sur incident (resume run) et cohérence event sourcing.

## Phase E — Interface évaluateur professionnelle (2 à 4 semaines)
- Étendre du cockpit ops vers une UI évaluateur complète.
- Workflow: file de revue, justification, corrections, validation finale.
- Journaliser toutes décisions humaines (trace légale/opérationnelle).

## Phase F — Sécurité, conformité, gouvernance (2 à 3 semaines)
- IAM RBAC, gestion secrets, chiffrement transit/repos.
- Politique de logs sensibles/anonymisation/rétention.
- Contrôles conformité réglementaire et auditabilité formelle.

## Phase G — Performance, fiabilité, coût (2 à 3 semaines)
- Bench latence/capacité/coût sur lots de dossiers.
- Optimiser prompts, cache, parallélisation contrôlée.
- Mettre SLO/SLA + alertes + budget coût.

## Phase H — Validation métier terrain & calibration finale (2 à 6 semaines)
- Exécuter campagne dossiers réels multi-profils.
- Consolider retours évaluateurs et calibrer règles/pondérations.
- Clore écarts critiques avec seuils d'acceptation signés.

## Phase I — Industrialisation CI/CD et environnements (1 à 2 semaines)
- Pipelines CI: tests, contrats, sécurité, perf smoke.
- Pipeline CD: dev -> staging -> prod avec approbations.
- Stratégie rollback/versioning/compatibilité données.

## Phase J — Pré-production et homologation (1 à 2 semaines)
- Dress rehearsal complet (charge, incidents simulés, recovery).
- Homologation sécurité + exploitation + métier.
- Go/No-Go documenté avec plan de mitigation.

## Phase K — Déploiement production (semaine de release)
- Déploiement progressif (canary/périmètre restreint).
- Monitoring renforcé J+0/J+7/J+30.
- Comité quotidien de stabilisation.

## Phase L — Hypercare et amélioration continue (2 à 4 semaines)
- Traitement prioritaire incidents/retours utilisateurs.
- Ajustements rapides des seuils non critiques.
- Passage en mode run standard avec roadmap v2.

---

## 5) Définition de “complet, professionnel, performant”

Le projet atteint la cible quand les conditions suivantes sont réunies:

1. **Complet**: flux dossier réel de l'entrée à un rapport validé évaluateur, avec traçabilité intégrale.
2. **Professionnel**: sécurité, conformité, exploitation et gouvernance prouvées.
3. **Performant**: SLO respectés, coût maîtrisé, stabilité opérationnelle en production.
4. **Déployé**: CI/CD, monitoring, runbooks, rollback et support post-release actifs.

---

## 6) Préparation de la prochaine session (sous-plans)

Prochaine session recommandée:
- prendre chaque phase A -> L ;
- produire un sous-plan standardisé: objectifs, tâches atomiques, dépendances, risques, critères done, livrables, estimation ;
- sortir un backlog exécutable priorisé (P0/P1/P2) avec ordre strict de réalisation.

Format cible du sous-plan (à répliquer pour chaque phase):
1. Objectif phase
2. Pré-requis
3. Tâches détaillées
4. Livrables
5. Tests/validation
6. Risques + mitigation
7. Critères de done
8. Estimation charge/délai
