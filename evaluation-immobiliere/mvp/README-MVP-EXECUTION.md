# MVP execution - point de depart concret

## Ce qui est pret maintenant

- Contrats d'agents v0: `AGENT-CONTRACTS-V0.yaml`
- Checklist conformite v0: `CHECKLIST-CONFORMITE-V0.md`
- Regles conformite: `RULES-CONFORMITE-V0.yaml`
- Pipeline runtime: `../integration/PIPELINE-RUNTIME-ASTON-V0.yaml`
- Moteur runtime: `../engine/runtime.py`
- API locale minimale: `../api.py`

## Commandes CLI

```bash
python evaluation-immobiliere/outils/prioriser_mvp.py
python evaluation-immobiliere/outils/valider_fixtures_v0.py
python evaluation-immobiliere/outils/valider_fixtures_v0.py --input evaluation-immobiliere/tests/fixtures/template_dossier_anonymise.json --strict --report-out evaluation-immobiliere/atelier/RAPPORT-VALIDATION-DOSSIER-PILOTE.md
python evaluation-immobiliere/outils/verifier_coherence_runtime_v0.py
python evaluation-immobiliere/outils/simuler_runtime_engine_v0.py
python evaluation-immobiliere/outils/analyser_integrite_runtime_v0.py
```

## Commandes API

```bash
python evaluation-immobiliere/outils/lancer_api_v0.py
python evaluation-immobiliere/outils/demo_api_v0.py --fixture case_nominal.json
```

## Critere de demo interne

La demo est exploitable si:

- le check de coherence passe;
- la simulation produit `runtime_summary.json`;
- les artefacts sont classes par dossier dans `tests/runtime/case_*`;
- l'API cree une session et retourne un statut de dossier;
- le flux `/stream` expose les evenements runtime.

## Prochaine etape operationnelle

1. Transformer un dossier reel anonymise en fixture JSON.
2. Lancer ce dossier via `/start`.
3. Faire relire `rapport_non_conformites.json`, `statut_sortie.json` et `brouillon_rapport.md` par un evaluateur.
4. Ajouter les ecarts au backlog MVP v1.
