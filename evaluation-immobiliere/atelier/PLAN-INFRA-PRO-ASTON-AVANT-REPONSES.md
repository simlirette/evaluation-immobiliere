# Plan infrastructure professionnelle avant reponses evaluateurs

## Objectif

Avancer le projet au maximum avant les reponses evaluateurs, sans inventer de
jugement metier. La cible est une infrastructure proche d'un runtime Aston:
orchestration claire, artefacts auditables, gates, traçabilite, file humaine,
securite documentaire et readiness reproductible.

## Phase 12 - Plan directeur et gouvernance runtime

Livrables:

- Plan de phases avant reponses.
- Regle explicite: aucune calibration metier inventee.
- Definition des artefacts de controle pre-reponses.

Critere done:

- Le plan existe dans `atelier/`.
- Les phases suivantes sont executables par scripts deterministes.

## Phase 13 - Manifest runtime scelle

Objectif:

- Produire un inventaire hashable des sorties runtime.
- Pouvoir prouver quels fichiers ont ete analyses ou envoyes.

Livrables:

- `runtime_manifest.json`
- `MANIFEST-RUNTIME-V0.md`
- hash SHA-256 par fichier et fingerprint global.

## Phase 14 - Gate readiness pre-reponses

Objectif:

- Avoir un statut operationnel unique avant envoi ou attente de reponses.

Livrables:

- `readiness_pre_reponses.json`
- `READINESS-PRE-REPONSES-V0.md`

Statuts:

- `PRET_A_RECEVOIR_REPONSES`
- `REPONSES_A_INTEGRER`
- `A_COMPLETER_AVANT_ENVOI`
- `A_CORRIGER`
- `A_CONTROLER`

## Phase 15 - File de revue humaine

Objectif:

- Transformer les signaux runtime en taches humaines explicites.

Livrables:

- `FILE-REVUE-HUMAINE-V0.csv`
- `FILE-REVUE-HUMAINE-V0.md`

Sources:

- warnings;
- blocages;
- erreurs de contrat;
- artefacts manquants;
- flags d'ingestion PDF;
- statuts runtime a confirmer.

## Phase 16 - Audit anonymisation pre-envoi

Objectif:

- Detecter les fuites evidentes avant partage ou revue.

Livrables:

- `anonymisation_audit.json`
- `RAPPORT-ANONYMISATION-V0.md`

Controles v0:

- courriels;
- telephones;
- codes postaux;
- adresses civiques probables;
- chemins locaux sensibles dans artefacts partageables.

## Phase 17 - Knowledge schema immobilier v0

Objectif:

- Preparer le futur equivalent Aston `knowledge.json`, sans le brancher tant
  que les retours evaluateurs ne sont pas connus.

Livrables prevus:

- schema YAML du dossier connaissance;
- profils par agent;
- mapping artefacts runtime -> knowledge.

## Phase 18 - Contrats de donnees v1 candidates

Objectif:

- Preparer les zones de contrats a modifier apres calibration.

Livrables prevus:

- liste des seuils et regles candidates;
- tests de regression attendus;
- matrice decision evaluateur -> changement contrat.

## Phase 19 - Runbook operations

Objectif:

- Rendre l'exploitation repetable par un humain non-developpeur.

Livrables prevus:

- sequence de commandes;
- criteres go/no-go;
- procedure de regeneration;
- procedure de correction.

## Phase 20 - Preparation integration Aston reelle

Objectif:

- Preparer le branchement futur vers un engine type Aston.

Livrables prevus:

- mapping sessions/events/persistence;
- specification SSE/API;
- definition de done pour agent_loop reel.

## Phase 21 - Knowledge snapshot reconstructible

Objectif:

- Generer un snapshot `knowledge` depuis les artefacts runtime sans remplacer
  les artefacts sources.

Livrables:

- `knowledge_snapshot.json`
- `KNOWLEDGE-SNAPSHOT-V0.md`

## Phase 22 - Orchestrateur pre-reponses

Objectif:

- Executer toute la chaine operationnelle pre-reponses en une commande.

Livrables:

- `outils/executer_pre_reponses_v0.py`
- `pre_reponses_run.json`
