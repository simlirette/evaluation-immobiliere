# Éval Immo

Workbench d'évaluation immobilière. Frontend Next.js + runtime Python (pipeline déterministe, artéfacts auditables).

## Architecture

```
eval-immo/
├── src/              # Next.js 16 frontend (App Router)
├── backend/          # Python runtime API (FastAPI/Flask, port 8796)
├── supabase/         # Migrations historiques (auth scaffolding)
└── docs/             # Audit + plans de complétion
```

- **Frontend** — Next.js 16, Tailwind v4, Cormorant Garamond + Inter, Liquid Glass design system.
- **Backend** — Python runtime exposé sur `http://127.0.0.1:8796`. Orchestre le pipeline d'évaluation, écrit des artéfacts auditables, expose les agents via `/app/*`.
- **Pas de requêtes Supabase directes en V1** — `src/lib/supabase/queries/*` sont des shims au-dessus du runtime API.

## Démarrage local

### Prérequis

- Node.js 20+
- Python 3.11+ (`pip install -r backend/requirements.txt`)

### Frontend

```bash
cp .env.example .env.local
# Remplir NEXT_PUBLIC_RUNTIME_API_URL si le runtime tourne sur un port différent
npm install
npm run dev        # http://localhost:3000
```

### Backend (runtime)

```bash
cd backend
pip install -r requirements.txt
python api.py      # http://127.0.0.1:8796
```

Vérifier : `curl http://127.0.0.1:8796/health` → `{"status":"ok"}`

## Variables d'environnement

| Variable | Où | Description |
|---|---|---|
| `NEXT_PUBLIC_RUNTIME_API_URL` | Frontend | URL du runtime (défaut `http://127.0.0.1:8796`) |
| `RUNTIME_API_URL` | Serveur (BFF, à venir) | URL interne du runtime pour le proxy Next.js |
| `RUNTIME_API_TOKEN` | Backend | Token d'authentification (optionnel en dev local) |
| `NEXT_PUBLIC_SUPABASE_URL` | Frontend | URL Supabase (auth scaffolding, non actif en V1) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Frontend | Clé Supabase (non actif en V1) |

Voir `.env.example` pour les valeurs par défaut.

## Déploiement

- **Frontend** — Vercel. Branch de déploiement : `main`. Env vars dans Vercel Dashboard.
- **Backend** — Railway. `railway.json` à la racine de `backend/`. Start command : `python api.py`.

En production, `NEXT_PUBLIC_RUNTIME_API_URL` doit pointer vers le service Railway (ex. `https://eval-immo-runtime.railway.app`). Ne pas exposer le runtime directement sans token.

## Statut V1

| Couche | Complétude |
|---|---|
| UI shell desktop | ~70% |
| Runtime pipeline | ~65% |
| Persistance / lifecycle dossiers | ~30% |
| Auth / sécurité | ~25% |
| Tests / CI | ~10% |

Voir `docs/project-audit-2026-05-08.md` pour l'audit complet et `docs/superpowers-optimized/plans/2026-05-08-project-completion-sessions.md` pour le plan de complétion.

## Limitations connues (V1)

- Création de dossier = fixture pilote (`case_pilote_residentiel_standard.json`), pas de données réelles.
- Delete/pin non persistants.
- Upload document = local UI seulement, pas d'ingestion runtime.
- Middleware auth désactivé — routes non protégées.
- Pas de proxy BFF — le browser appelle le runtime directement (non déployable en prod sans correction Session 2).
