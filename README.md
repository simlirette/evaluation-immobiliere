# Eval Immo

Workbench d'evaluation immobiliere pour dossiers residentiels: frontend Next.js, BFF Next.js, runtime Python et artefacts auditables.

Le projet est utilisable en dev local avec fixtures anonymisees. Le lancement beta externe reste bloque tant que les variables de production, l'URL hebergee, le token runtime, les origines CORS strictes, les cles LLM et les donnees terrain E.A. ne sont pas finalises.

## Architecture

```text
eval-immo/
├── src/                       # Next.js 16 App Router, UI, BFF /api/runtime/*
├── backend/                   # Runtime Python, API locale sur 127.0.0.1:8796
├── backend/tests/             # Suite pytest backend
├── tests/fixtures/acceptance/ # Jeux anonymises pour acceptance E.A.
├── supabase/                  # Migrations et scaffolding auth
├── docs/                      # Docs historiques et procedures
└── _audit/2026-06-02/         # Analyse Codex et plan d'execution courant
```

- Frontend: Next.js 16, React 19, Tailwind v4, App Router, panneaux de dossier, workflow de revue et paquet exportable.
- BFF: routes Next.js `/api/runtime/*`; le navigateur n'appelle pas le runtime Python directement.
- Backend: runtime Python avec pipeline deterministe, modes agents, checkpoints, enrichissement, generation de rapport, packaging et readiness gates.
- Auth: Supabase SSR scaffolding. En production, les routes dossier doivent etre protegees par Supabase et le BFF doit transmettre le token runtime serveur.
- Stockage local: les sessions et caches sont ecrits sous `backend/runtime_sessions/` et `backend/data_cache/` par defaut.

## Demarrage Local

Prerequis:

- Node.js 22 recommande pour aligner la CI
- Python 3.12 recommande pour aligner la CI
- `pip install -r backend/requirements-dev.txt`

Frontend:

```bash
cp .env.example .env.local
npm install
npm run dev
```

Backend:

```bash
cd backend
pip install -r requirements-dev.txt
python api.py
```

Verifier le backend:

```bash
curl http://127.0.0.1:8796/health
```

URL dev:

- Frontend: `http://localhost:3000`
- Runtime Python: `http://127.0.0.1:8796`

## Variables D'environnement

| Variable | Cote | Description |
|---|---|---|
| `RUNTIME_API_URL` | Next.js serveur | URL interne du runtime Python. Dev: `http://127.0.0.1:8796`. |
| `RUNTIME_API_TOKEN` | Next.js serveur | Token transmis par le BFF au runtime. Requis en production. |
| `EVAL_RUNTIME_API_TOKEN` | Backend Python | Token attendu par le runtime. Doit correspondre a `RUNTIME_API_TOKEN`. |
| `APP_ENV` | Backend Python | Mettre `production` pour activer les validations strictes. |
| `EVAL_RUNTIME_ALLOWED_ORIGIN` | Backend Python | Origine Vercel exacte en production; ne pas garder `*`. |
| `SESSIONS_DIR` | Backend Python | Repertoire persistant des sessions runtime. |
| `DATA_CACHE_DIR` | Backend Python | Repertoire persistant des caches MAMH/Infolot/SIRF. |
| `OPENAI_API_KEY` | Backend Python | Active les modes LLM; sinon le mode deterministe reste disponible. |
| `OPENAI_MODEL` | Backend Python | Modele LLM cible. |
| `NEXT_PUBLIC_SUPABASE_URL` | Next.js client | Requis pour l'auth Supabase en production. |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Next.js client | Cle publique Supabase. |

Voir `.env.example` pour les valeurs et commentaires complets.

## Verification

Commandes principales:

```bash
npm run typecheck
npm run lint
npm test
npm run build
```

```bash
cd backend
pytest tests/ -v
```

Gates operationnelles utiles:

```bash
cd backend
python scripts/verifier_deploy_readiness.py --env nonprod --json
python scripts/verifier_beta_ea_readiness_v1.py --json
python scripts/run_ea_acceptance.py tests/fixtures/acceptance/ea_acceptance_anonymized_residential.json --json
```

Baseline verifiee par Codex le 2026-06-02 sur `origin/main`:

- Frontend: typecheck OK, lint OK avec deux avertissements mineurs avant correction, tests OK (`1188` tests), build OK avec avertissements Next.js avant correction.
- Backend: pytest OK (`961` passed, `3` skipped).
- Readiness non-prod: pret avec avertissements de configuration production.
- Beta E.A.: bloquee par configuration hebergee et secrets manquants.

## Statut Courant

| Surface | Statut |
|---|---|
| Workbench local | Utilisable avec fixtures anonymisees et runtime local. |
| Runtime backend | Suite backend verte; artefacts, revue, paquet et acceptance disponibles. |
| BFF runtime | En place via `/api/runtime/*`; evite l'exposition directe du runtime au navigateur. |
| Auth production | Scaffolding present; validation production encore a fermer avec Supabase reel. |
| Donnees externes | Caches et credentials reels a configurer avant beta. |
| Beta E.A. externe | Bloquee jusqu'a URL hebergee, secrets, CORS strict, OpenAI et dossiers terrain anonymises. |

## Analyse Et Plan

Le plan detaille de correction est dans [`_audit/2026-06-02/EXECUTION-PLAN.md`](_audit/2026-06-02/EXECUTION-PLAN.md).
Le plan d'amelioration du point de vue E.A. est dans [`_audit/2026-06-02/EA-IMPROVEMENT-PLAN.md`](_audit/2026-06-02/EA-IMPROVEMENT-PLAN.md).
Le gate operationnel avant partage du lien beta ferme est dans [`docs/CLOSED-BETA-LAUNCH.md`](docs/CLOSED-BETA-LAUNCH.md).

La ligne directrice:

1. Stabiliser la source de verite du repo et la hygiene build.
2. Eliminer les vulnerabilites critiques/hautes et ajouter un gate CI.
3. Fermer la configuration production: secrets, CORS, volumes, auth, monitoring.
4. Valider l'experience E.A. avec dossiers anonymises reels.
5. Lancer une beta fermee seulement apres acceptance, paquet audit complet et runbook support.

Chaque paquet V1 inclut maintenant:

- `professional_workfile_gate.json`
- `npp_compliance_matrix.json`
- `source_provenance.json`

## Limites Connues

- Les fixtures anonymisees ne remplacent pas encore des dossiers terrain signes par un E.A.
- La sortie est une assistance auditable, pas une certification automatique de valeur.
- Les sources publiques et SIRF doivent etre configurees, cachees et validees en environnement heberge.
- Les modes LLM dependent des cles et contrats operateur; le mode deterministe reste le fallback.
- Le lancement beta exige un environnement production strict, pas seulement les tests locaux.
