# evaluation-immobiliere

Ce dossier regroupe les artefacts de demarrage et le runtime v0 du projet **evaluation-immobiliere**.

## Ce qui est disponible

- Cadrage metier et atelier evaluateurs dans `atelier/`
- Contrats MVP, schemas, regles et checklist dans `mvp/`
- Configs d'agents et pipeline dans `integration/`
- Moteur local dans `engine/`
- Outils CLI dans `outils/`
- Fixtures et rapports de verification dans `tests/`
- API locale minimale dans `api.py`
- Collecte et compilation des reponses evaluateurs dans `atelier/`

## Commandes utiles

```bash
python evaluation-immobiliere/outils/verifier_coherence_runtime_v0.py
python evaluation-immobiliere/outils/simuler_runtime_engine_v0.py
python evaluation-immobiliere/outils/analyser_integrite_runtime_v0.py
python evaluation-immobiliere/outils/compiler_reponses_evaluateurs.py
python evaluation-immobiliere/outils/prioriser_mvp.py
python -m unittest evaluation-immobiliere/tests/test_tools_v0.py evaluation-immobiliere/tests/test_runtime_v0.py
```

## API runtime v0

L'API locale expose le runtime sans UI complete:

```bash
python evaluation-immobiliere/outils/lancer_api_v0.py
```

Endpoints:

- `POST /session`
- `POST /start`
- `GET /stream?session_id=<id>`
- `GET /health`

Demo depuis un autre terminal:

```bash
python evaluation-immobiliere/outils/demo_api_v0.py --fixture case_nominal.json
```

## Prochaine etape logique

Brancher 2-3 dossiers anonymises reels sur le runtime/API, puis comparer les sorties avec une revue evaluateur.
