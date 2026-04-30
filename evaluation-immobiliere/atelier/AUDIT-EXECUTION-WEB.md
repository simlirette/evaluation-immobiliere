# AUDIT EXECUTION WEB — evaluation-immobiliere (2026-04-30)

## Synthèse opérationnelle
- Le repo est **déjà exécutable en mode v0 web/local léger**: API runtime (`api.py`), UI ops (`ui/ops_cockpit.html`, `ui/pilote_api.html`), outils CLI et nombreux tests. Références: `README.md`, `api.py`, `outils/lancer_api_v0.py`.
- La base documentaire A→L existe mais reste souvent **macro**: plusieurs sous-plans n’embarquent pas encore de critères d’acceptation mesurables, owners explicites et dépendances techniques vérifiables. Références: `atelier/PLAN-DIRECTEUR-COMPLET-V1.md`, `atelier/sous-plans/PHASE-*-SOUS-PLAN.md`.
- Bloquant principal de mise en prod: absence de branchement complet à un runtime Aston réel + persistance/streaming prod + sécurité/CI-CD/homologation opérables. Références: `atelier/PLAN-DIRECTEUR-COMPLET-V1.md`, `integration/README-INTEGRATION.md`.

## Ce qui est prêt immédiatement (web-efficient)
1. **Démonstration runtime v0** via API + fixtures.
2. **Validation automatisée** (tests unitaires/intégration runtime/ops multiples).
3. **Artefacts de traçabilité** (JSONL audit, reports runtime, schemas ops).
4. **Matière atelier évaluateurs** (questionnaire, templates CSV, scripts compilation/priorisation).

## Flous / zones non actionnables détectés
- Sous-plans A→L homogènes mais trop génériques sur:
  - commandes exactes à lancer;
  - seuils quantifiés Go/No-Go;
  - matrice risques→owner;
  - dépendances runtime réel (Aston session lifecycle, streaming, persistence).
- Plusieurs phases mentionnent des livrables V1 non présents dans le repo (normal), sans kit d’exécution standardisé.

## Gaps bloquants mise en prod
- **C1** Runtime Aston réel non branché end-to-end (critique).
- **C2** Persistance session/events/artefacts robuste non finalisée (critique).
- **C3** Connecteurs data/OCR/comparables “prod-ready” non prouvés (critique).
- **C4** RBAC/secrets/chiffrement/rétention/audit d’accès non formalisés en contrôles exécutables (critique).
- **C5** Homologation terrain évaluateurs non signée (majeur).

## Go/No-Go web (ce qui est faisable maintenant)
### Go immédiat
- Produire backlog exécutable P0/P1/P2.
- Préparer kits A→L normalisés avec acceptance tests.
- Préparer checklist handoff terminal (tests lourds/local infra).
- Préparer readiness client (preuves minimales).

### No-Go immédiat (à valider en session terminal)
- Preuve de performance réelle multi-dossiers.
- Validation sécurité opérationnelle complète.
- Déploiement/staging/prod et stratégie rollback testée.

## Décisions prises
- Basculer la planification en **artefacts d’exécution** plutôt qu’en descriptions macro.
- Prioriser les actions qui augmentent la “démontrabilité” client sans dépendre d’un runtime local lourd.
- Définir les éléments manquants avec hypothèses explicites et statut **à valider**.

## Questions ouvertes
1. Quel est l’environnement Aston cible exact (SDK/runtime contract final)? **À valider**.
2. Quelles sources data externes seront autorisées en prod (comparables, cadastre, OCR)? **À valider**.
3. Quels seuils métier signés déclenchent Go commercial (écarts tolérés, taux correction)? **À valider**.
4. Quel modèle d’hébergement/sécurité est imposé côté client final? **À valider**.
