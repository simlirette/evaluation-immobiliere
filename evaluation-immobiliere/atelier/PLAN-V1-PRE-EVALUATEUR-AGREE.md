# Plan V1 pre-evaluateur agree

_As-of date: 2026-05-04 (UTC)_

## Objectif

Finaliser une V1 demonstrable et credible avant consultation d'un evaluateur immobilier agree.

Cette V1 ne pretend pas etre validee terrain reel. Elle doit etre assez complete pour montrer le produit, le raisonnement, les artefacts, les limites et le workflow cible afin que l'evaluateur puisse reviser quelque chose de concret.

## Positionnement

- Cible produit: **V1_PRE_EVALUATEUR**
- Decision courante: **PRET_SEANCE_REVUE_EVALUATEUR_AGREE**
- Production reelle: **bloquee**
- Validation terrain Phase H: **post-V1**
- Reponses evaluateurs: **non requises pour finir la V1**, requises seulement pour calibration/homologation metier reelle.

## Plan par phase

| Phase | Role dans la V1 pre-evaluateur | Statut cible V1 | A faire maintenant | Bloque V1 | Bloque prod reelle |
|---|---|---|---|---|---|
| A - Cadrage | Garder la vision et le perimetre clairs | TERMINE | Mettre a jour les decisions recentes | non | non |
| B - Contrats | Prouver les entrees/sorties et schemas | TERMINE | Conserver compatibilite CI | non | non |
| C - Runtime | Produire un dossier exemple complet | PRET_DEMO | Conserver la demo E2E lisible et reproductible | non | oui |
| D - API/persistence | Donner une surface produit coherente | PRET_DEMO | Conserver endpoints/session/artefacts utiles a la demo | non | oui |
| E - UI evaluateur | Presenter le workflow concret | PRET_DEMO | Presenter revue, artefacts, corrections et decisions | non | oui |
| F - Securite/gouvernance | Montrer que les donnees sensibles sont traitees serieusement | PRET_DEMO | Garder anonymisation, retention, audit, RBAC documentes | non | oui |
| G - Perf/fiabilite/cout | Montrer les limites et budgets | GO_CONDITIONNEL | Fermer ou documenter SLO manquants | non | oui |
| H - Revue evaluateur/terrain | Calibration apres V1 | HANDOFF_PRET | Tenir la seance avec le handoff versionne, sans reponse inventee | non | oui |
| I - CI/CD | Prouver que la V1 est regenerable | PRET_STAGING | Garder gates verts et statut phases en CI | non | non |
| J - Preprod | Simuler homologation sans prod | PROD_BLOQUEE | Garder dress rehearsal et ecarts ouverts visibles | non | oui |
| K - Canary | Planifier sans ouvrir prod | PROD_BLOQUEE | Conserver plan canary bloque | non | oui |
| L - Hypercare | Preparer support futur | PREPARE_PROD_BLOQUEE | Conserver playbook incident/backlog | non | oui |

## Livrables V1 a produire avant revue evaluateur

1. Demo E2E sur dossier exemple anonymise ou synthetique representatif.
2. Rapport d'evaluation exemple complet avec sources, comparables, calculs, reserves et statut final.
3. UI/API utilisable pour inspecter session, artefacts, warnings, blocages et corrections.
4. Paquet de revue evaluateur: rapport, questions, grille de decision, matrice d'ecarts.
5. Note de limites: ce qui est simule, ce qui est theorique, ce qui attend la revue metier.
6. Gate `STATUT-PHASES-PROJET-V1` vert avec production reelle bloquee.

Le paquet versionne est produit dans `atelier/PAQUET-V1-PRE-EVALUATEUR/` par `generer_paquet_v1_pre_evaluateur.py`. Il est regenere en CI et bloque le statut global si les fichiers ou signaux machine-readable divergent.

Le handoff de seance est produit par `generer_handoff_revue_evaluateur_v1.py`. Il transforme le paquet en brief, ordre du jour, checklist et manifest de point d'arret avant integration de vraies reponses evaluateur.

## Criteres done V1 pre-evaluateur

- Le projet se lance et produit une preuve E2E reproductible.
- Les artefacts metier sont lisibles par un evaluateur.
- Les statuts `PRET_REVISION_FINALE`, `BROUILLON`, `A_REVOIR` sont expliques.
- Les limites terrain sont explicites et non maquillees.
- Aucune donnee sensible ou reponse evaluateur inventee n'est requise.
- La production reelle reste bloquee tant que Phase H n'est pas faite.

## Suite apres V1

Une fois la V1 presentable:

1. Revue avec evaluateur immobilier agree.
2. Collecte de commentaires sur workflow, statuts, comparables, seuils et rapport.
3. Transformation des retours en backlog V2.
4. Eventuelle campagne Phase H reelle avec dossiers anonymises et reponses signees.
