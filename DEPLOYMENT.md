# Déploiement — eval-immo

## Architecture

```
Vercel (Next.js)  ←→  Railway (Python backend)  ←→  Supabase (auth + DB)
       BFF /api/runtime/*      port $PORT (8080)
```

---

## Backend Python — Railway

### Variables d'environnement Railway

| Variable | Requis | Description |
|---|---|---|
| `PORT` | auto | Railway injecte automatiquement — ne pas définir |
| `OPENAI_API_KEY` | prod | Clé OpenAI pour les agents LLM. Sans elle : mode déterministe. |
| `OPENAI_MODEL` | non | Modèle à utiliser (défaut : `gpt-4o-mini`) |
| `EVAL_RUNTIME_API_TOKEN` | prod | Token partagé avec le BFF Next.js (32+ caractères aléatoires). Générer : `openssl rand -hex 32` |
| `EVAL_RUNTIME_ALLOWED_ORIGIN` | prod | URL exacte Vercel sans slash, ex : `https://eval-immo.vercel.app` |
| `SESSIONS_DIR` | volume | Chemin du volume Railway persistant, ex : `/data/sessions` |

### Volume persistant (obligatoire en prod)

Dans Railway → service backend → **Volumes** → Ajouter `/data/sessions`.  
Puis définir `SESSIONS_DIR=/data/sessions`.  
Sans volume, les sessions sont perdues à chaque redéploiement.

### Build

Le `Dockerfile` utilise `python:3.12-slim`. PyMuPDF >= 1.24 embarque ses propres binaires MuPDF mais requiert `libgomp1` (OpenMP) sur Linux — installé automatiquement par le Dockerfile.

### Healthcheck

Railway surveille `GET /health` (configuré dans `railway.json`).  
Réponse attendue : `{"status": "ok", "version": "2.0", "openai": true, "pymupdf": true}`.

---

## Frontend Next.js — Vercel

### Variables d'environnement Vercel

| Variable | Requis | Description |
|---|---|---|
| `RUNTIME_API_URL` | prod | URL publique du service Railway, ex : `https://eval-immo-backend.railway.app` |
| `RUNTIME_API_TOKEN` | prod | Même valeur que `EVAL_RUNTIME_API_TOKEN` côté Railway |
| `NEXT_PUBLIC_SUPABASE_URL` | prod | URL du projet Supabase, ex : `https://xxxx.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | prod | Clé anon Supabase (publique) |

> `RUNTIME_API_URL` et `RUNTIME_API_TOKEN` sont **server-only** — ne jamais les préfixer `NEXT_PUBLIC_`.

### Auth Supabase

Sans vraies credentials Supabase (ou avec les placeholders `<project-ref>`), le middleware passe en mode **passthrough** — aucune auth enforced. C'est voulu pour le dev local.

En prod, configurer les 2 variables `NEXT_PUBLIC_SUPABASE_*` active automatiquement la protection de toutes les routes sauf `/login`.

---

## Checklist de mise en production

- [ ] Railway : créer service depuis `/backend` (Dockerfile détecté automatiquement)
- [ ] Railway : configurer les 4 variables d'env backend (OPENAI_API_KEY, EVAL_RUNTIME_API_TOKEN, EVAL_RUNTIME_ALLOWED_ORIGIN, SESSIONS_DIR)
- [ ] Railway : ajouter volume `/data/sessions`
- [ ] Railway : vérifier que `GET /health` retourne 200 après deploy
- [ ] Vercel : configurer les 4 variables d'env frontend (RUNTIME_API_URL, RUNTIME_API_TOKEN, NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY)
- [ ] Vercel : vérifier que `/dossiers` redirige vers `/login` sans session
- [ ] Test end-to-end : créer un dossier, lancer pipeline, questionner un agent

---

## Dev local

```bash
# Terminal 1 — backend
cd backend
python api.py          # démarre sur :8796

# Terminal 2 — frontend
npm run dev            # démarre sur :3000
```

Copier `.env.example` → `.env.local` et ajuster les valeurs.  
Sans `OPENAI_API_KEY`, les agents retournent des réponses déterministes (mode hors-ligne fonctionnel).
