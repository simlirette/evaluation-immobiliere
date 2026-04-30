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

## Phase 27 - Cockpit UI ops

Objectif:

- Lire les endpoints ops depuis une page interne.
- Visualiser readiness, risques, contrats infra et file humaine.

Livrables:

- `ui/ops_cockpit.html`
- routes `/ops/ui` et `/ops/cockpit`

## Phase 28 - Durcissement API ops

Objectif:

- Tester les endpoints HTTP reels et les erreurs de rapport absent/inconnu.

Livrables:

- tests HTTP sur `/ops`, `/ops/readiness`, `/ops/review_queue`,
  `/ops/pre-response-run`.

## Phase 29 - Verrou anti-concurrence

Objectif:

- Eviter deux executions pre-reponses simultanees.

Livrables:

- lock file `pre_reponses.lock`
- expiration configurable
- reponse API `409` si execution deja active

## Phase 30 - Simulation calibration controlee

Objectif:

- Prouver le flux post-reponses avec des donnees fictives de test seulement.

Livrables:

- `tests/fixtures/calibration_evaluateurs_simulee.csv`
- tests de backlog P0/P2 et de confirmation de blocage

## Phase 31 - Telemetrie execution pre-reponses

Objectif:

- Rendre chaque run pre-reponses auditable en temps d'execution.
- Identifier rapidement l'etape fautive en cas d'arret.

Livrables:

- timestamps debut/fin du run
- durees par etape
- `steps_count`
- `failed_step`

## Phase 32 - Delta runtime pre-reponses

Objectif:

- Comparer la qualite courante au dernier run registre.
- Detecter une regression avant envoi ou attente de reponses.

Livrables:

- `runtime_delta_report.json`
- `RAPPORT-DELTA-RUNTIME-V0.md`
- statut `STABLE`, `A_CONTROLER` ou `OBSERVATION_INITIALE`

## Phase 33 - Manifeste handoff ops

Objectif:

- Inventorier les rapports et traces qui composent le paquet operationnel.
- Distinguer les fichiers requis des rapports optionnels.

Livrables:

- `ops_handoff_manifest.json`
- `OPS-HANDOFF-MANIFEST-V0.md`

## Phase 34 - Exposition ops et contrats v1

Objectif:

- Exposer delta et handoff dans l'API/cockpit ops.
- Valider leur presence dans les contrats infra.

Livrables:

- endpoints `/ops/delta` et `/ops/handoff`
- cockpit ops enrichi
- contrats infra et tests mis a jour

## Phase 35 - Schemas contrats v1

Objectif:

- Declarer les contrats ops critiques en JSON Schema.
- Valider les rapports runtime sans dependance externe.

Livrables:

- `schemas/ops/*.schema.json`
- `schema_validation_report.json`
- `RAPPORT-SCHEMAS-OPS-V0.md`

## Phase 36 - Ops doctor

Objectif:

- Donner un diagnostic exploitation unique.
- Fournir des exit codes stables pour scripts et CI.

Livrables:

- `ops_doctor_report.json`
- `OPS-DOCTOR-V0.md`
- exit codes `0=OK`, `1=A_CONTROLER`, `2=A_CORRIGER`

## Phase 37 - Gate paquet evaluateurs

Objectif:

- Controler le paquet evaluateurs avant envoi.
- Verifier fichiers requis, en-tetes CSV, anonymisation et absence de fuites evidentes.

Livrables:

- `paquet_evaluateurs_gate.json`
- `PAQUET-EVALUATEURS-GATE-V0.md`
