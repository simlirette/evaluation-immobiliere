# Runbook operations pre-reponses

## Sequence nominale

```bash
python evaluation-immobiliere/outils/executer_dossiers_pilotes_reels_v0.py
python evaluation-immobiliere/outils/calibrer_reponses_evaluateurs_v0.py
python evaluation-immobiliere/outils/generer_file_revue_humaine_v0.py
python evaluation-immobiliere/outils/auditer_anonymisation_v0.py
python evaluation-immobiliere/outils/generer_manifest_runtime_v0.py
python evaluation-immobiliere/outils/generer_knowledge_snapshot_v0.py
python evaluation-immobiliere/outils/generer_manifest_runtime_v0.py
python evaluation-immobiliere/outils/verifier_readiness_pre_reponses_v0.py
python -m unittest discover -s evaluation-immobiliere/tests -p "test_*.py"
```

Equivalent en une commande:

```bash
python evaluation-immobiliere/outils/executer_pre_reponses_v0.py
```

## Statut attendu avant reponses

Sans dossiers reels anonymises actifs:

- `pre_reponses_run.json`: `OK: True`, 20 etapes OK
- `READINESS-PRE-REPONSES-V0.md`: `EN_ATTENTE_ENTREES_TERRAIN_REELLES`
- `OPS-HANDOFF-MANIFEST-V0.md`: `EN_ATTENTE_ENTREES_TERRAIN_REELLES`
- `RAPPORT-CONTRATS-INFRA-V0.md`: `EN_ATTENTE_ENTREES_TERRAIN_REELLES`, 0 manquant bloquant
- `RAPPORT-SCHEMAS-OPS-V0.md`: `EN_ATTENTE_ENTREES_TERRAIN_REELLES`, 0 invalide bloquant
- `PAQUET-EVALUATEURS-GATE-V0.md`: `EN_ATTENTE_ENTREES_TERRAIN_REELLES`
- `OPS-DOCTOR-V0.md`: `EN_ATTENTE_ENTREES_TERRAIN_REELLES`

Avec dossiers reels anonymises actifs et runtime execute:

- `RAPPORT-CALIBRATION-EVALUATEURS-V0.md`: `PRET_A_RECEVOIR_REPONSES`
- `READINESS-PRE-REPONSES-V0.md`: `PRET_A_RECEVOIR_REPONSES`
- `RAPPORT-ANONYMISATION-V0.md`: `OK`
- `RAPPORT-DELTA-RUNTIME-V0.md`: `STABLE` ou `OBSERVATION_INITIALE`
- `OPS-HANDOFF-MANIFEST-V0.md`: `PRET_A_TRANSMETTRE`
- `RAPPORT-SCHEMAS-OPS-V0.md`: `OK`
- `PAQUET-EVALUATEURS-GATE-V0.md`: `PRET_A_ENVOYER`
- `OPS-DOCTOR-V0.md`: `OK`
- tests locaux: tous verts

## Cockpit ops

Demarrer l'API locale puis ouvrir:

```bash
python evaluation-immobiliere/outils/lancer_api_v0.py
```

URL:

```text
http://127.0.0.1:8787/ops/ui
```

Endpoints utiles:

- `/ops/delta`
- `/ops/handoff`
- `/ops/schema_validation`
- `/ops/package_gate`
- `/ops/doctor`
- `/ops/infra_contracts`
- `/ops/review_queue`

## Go / no-go

Go:

- paquet evaluateurs `PRET_A_ENVOYER`;
- aucun finding anonymisation;
- manifest runtime present;
- file de revue humaine generee;
- calibration vide ou valide.

Attente controlee:

- `EN_ATTENTE_ENTREES_TERRAIN_REELLES` sur readiness, handoff, schemas, paquet et ops doctor;
- aucun manquant bloquant dans les rapports infra/schema;
- aucune reponse evaluateur inventee;
- `runtime_pilotes_reels/` reste ignore par Git.

No-go:

- erreur de structure calibration;
- finding anonymisation;
- absence de manifest;
- paquet evaluateurs absent;
- tests locaux rouges.

## Correction

1. Corriger l'artefact ou le CSV source.
2. Regenerer les rapports dans la sequence nominale.
3. Verifier que le fingerprint runtime change seulement si les artefacts ont
   vraiment change.
