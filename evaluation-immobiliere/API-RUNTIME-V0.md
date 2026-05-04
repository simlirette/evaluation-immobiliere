# API runtime v0

Objectif: permettre une execution locale du pipeline sans UI complete, avec session persistante, artefacts par dossier et flux d'evenements consultable.

## Lancer le serveur

```bash
python evaluation-immobiliere/outils/lancer_api_v0.py --host 127.0.0.1 --port 8787
```

Le serveur utilise uniquement la bibliotheque standard Python.

Interface locale:

```text
http://127.0.0.1:8787/product
http://127.0.0.1:8787/ui
http://127.0.0.1:8787/review/ui
```

Endpoints:

- `GET /ui`
- `GET /fixtures`
- `GET /health`
- `GET /product/summary`
- `POST /product/demo`
- `POST /session`
- `POST /start`
- `GET /session/summary?session_id=<id>`
- `GET /status?session_id=<id>`
- `GET /artifacts?session_id=<id>`
- `GET /artifact?session_id=<id>&event_id=<event_id>`
- `GET /stream?session_id=<id>`
- `POST /review`
- `POST /resume`

## Creer une session

```bash
curl -X POST http://127.0.0.1:8787/session ^
  -H "Content-Type: application/json" ^
  -d "{\"strict_mode\": true}"
```

Reponse:

```json
{
  "session_id": "...",
  "strict_mode": true,
  "status": "CREATED",
  "events_url": "/stream?session_id=..."
}
```

## Demarrer une execution depuis une fixture

```bash
curl -X POST http://127.0.0.1:8787/start ^
  -H "Content-Type: application/json" ^
  -d "{\"session_id\":\"<id>\",\"fixture\":\"case_nominal.json\"}"
```

Sans `session_id`, `/start` cree une session automatiquement.

## Demarrer une execution inline

```json
{
  "case": {
    "dossier_id": "D-PILOTE-001",
    "date_reference": "2026-04-28",
    "comparables": [
      {
        "comparable_id": "C1",
        "prix_vente": 500000,
        "source_id": "SRC-1"
      }
    ],
    "ajustements": [
      {
        "ajustement_id": "A1",
        "montant": 10000,
        "source_id": "SRC-1",
        "validation_humaine": true
      }
    ],
    "confidence": 0.85
  }
}
```

## Lire les evenements SSE

```bash
curl http://127.0.0.1:8787/stream?session_id=<id>
```

Evenements exposes:

- `step_start`
- `artifact_written`
- `step_done`
- `warning_detected`
- `blocking_detected`
- `schema_invalid`

## Relire une session et ses artefacts

```bash
curl http://127.0.0.1:8787/session/summary?session_id=<id>
curl http://127.0.0.1:8787/artifact?session_id=<id>^&event_id=<event_id>
```

`/artifact` refuse les chemins hors repertoire de session et renvoie seulement
un apercu texte/JSON plafonne a 64 KiB pour garder l'UI exploitable sans exposer
de lecture arbitraire du disque.

## Persistance locale

Les sessions API sont ecrites dans:

```text
evaluation-immobiliere/runtime_sessions/<session_id>/
```

Ce dossier est ignore par Git. Les simulations CLI continuent d'ecrire leurs artefacts reproductibles dans `evaluation-immobiliere/tests/runtime/`.
