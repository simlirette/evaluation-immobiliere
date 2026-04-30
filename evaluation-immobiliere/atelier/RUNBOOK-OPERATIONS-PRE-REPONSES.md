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

- `RAPPORT-CALIBRATION-EVALUATEURS-V0.md`: `PRET_A_RECEVOIR_REPONSES`
- `READINESS-PRE-REPONSES-V0.md`: `PRET_A_RECEVOIR_REPONSES`
- `RAPPORT-ANONYMISATION-V0.md`: `OK`
- tests locaux: tous verts

## Go / no-go

Go:

- paquet evaluateurs `PRET_A_ENVOYER`;
- aucun finding anonymisation;
- manifest runtime present;
- file de revue humaine generee;
- calibration vide ou valide.

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
