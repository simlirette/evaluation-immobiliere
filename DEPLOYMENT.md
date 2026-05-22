# Déploiement — eval-immo

## Architecture

```
Vercel (Next.js)  ←→  Railway (Python backend)
       BFF /api/runtime/*      port $PORT
```

---

## Prérequis

- Compte [Railway](https://railway.app) (plan Hobby ou Pro)
- Compte [Vercel](https://vercel.com)
- Repo GitHub connecté aux deux plateformes
- `railway` CLI : `npm i -g @railway/cli` puis `railway login`

---

## 1. Backend Python — Railway

### 1.1 Créer le service

```bash
cd backend
railway init          # créer un nouveau projet Railway
railway up            # premier déploiement (détecte Dockerfile automatiquement)
```

Ou via l'UI : New Project → Deploy from GitHub → sélectionner le repo → **Root Directory : `backend`**.

### 1.2 Variables d'environnement Railway

Dans Railway → service → Variables, ajouter :

| Variable | Valeur |
|---|---|
| `OPENAI_API_KEY` | `sk-...` |
| `OPENAI_MODEL` | `gpt-4o-mini` (ou `gpt-4o`) |
| `APP_ENV` | `production` |
| `EVAL_RUNTIME_API_TOKEN` | générer : `openssl rand -hex 32` |
| `EVAL_RUNTIME_ALLOWED_ORIGIN` | URL Vercel exacte, ex : `https://eval-immo.vercel.app` |
| `SESSIONS_DIR` | `/data/sessions` |
| `DATA_CACHE_DIR` | `/data/data_cache` |

> `PORT` est injecté automatiquement par Railway — ne pas définir.

### 1.3 Volume persistant

Railway → service → **Volumes** → Add Volume :
- Mount path : `/data/sessions`
- Sans volume, les sessions sont perdues à chaque redéploiement.

Ajouter aussi un stockage persistant pour les sources publiques :
- Mount path : `/data/data_cache` si volume separe, ou monter `/data` et utiliser `/data/data_cache`.
- Prechauffer le cache MAMH avant usage reel : `python scripts/provision_mamh_cache.py --cache-dir /data/data_cache --all`.

### 1.4 Vérifier le healthcheck

Avant de publier l'URL Railway, executer le garde de readiness dans le service backend :

```bash
cd backend
APP_ENV=production python scripts/check_deploy_readiness.py --json
```

Le script retourne un code non-zero si une configuration critique manque.

```bash
curl https://<ton-service>.railway.app/health
# Liveness: retourne 200 et inclut "readiness" pour diagnostic.

curl https://<ton-service>.railway.app/readiness
# Readiness: retourne 200 si deployable, 503 si bloque par configuration critique.
```

---

## 2. Frontend Next.js — Vercel

### 2.1 Importer le projet

Vercel → Add New Project → Import Git Repository → sélectionner le repo.

- **Framework Preset** : Next.js (auto-détecté)
- **Root Directory** : `.` (racine du repo)
- **Build Command** : `npm run build` (défaut)

### 2.2 Variables d'environnement Vercel

Dans Vercel → Settings → Environment Variables :

| Variable | Valeur | Portée |
|---|---|---|
| `RUNTIME_API_URL` | URL Railway du backend, ex : `https://eval-immo-backend.railway.app` | Production |
| `RUNTIME_API_TOKEN` | Même valeur que `EVAL_RUNTIME_API_TOKEN` Railway | Production |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://<project-ref>.supabase.co` | All |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Clé anon Supabase | All |

> `RUNTIME_API_URL` et `RUNTIME_API_TOKEN` sont **server-only** — ne jamais préfixer `NEXT_PUBLIC_`.

### 2.3 Déployer

```bash
# Via CLI
npx vercel --prod

# Ou push sur main → déploiement automatique
git push origin main
```

---

## 3. Smoke test post-déploiement

```bash
BACKEND=https://<ton-service>.railway.app
FRONTEND=https://eval-immo.vercel.app
TOKEN=<EVAL_RUNTIME_API_TOKEN>

# 1. Readiness + health backend
curl $BACKEND/readiness
curl $BACKEND/health

# 2. App state via BFF (sans auth Supabase, le middleware passe en passthrough)
curl $FRONTEND/api/runtime/app/state

# 3. Créer un dossier de test
curl -X POST $BACKEND/app/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"address":"123 rue Test, Montréal","property_type":"condo","neighborhood":"Plateau","commanditaire":{"nom":"Test","organisation":"","fin_evaluation":"hypothecaire"}}'
```

---

## 4. Checklist complète

### Backend Railway
- [ ] Service créé depuis `/backend` (Dockerfile détecté)
- [ ] `OPENAI_API_KEY` configurée
- [ ] `EVAL_RUNTIME_API_TOKEN` générée (`openssl rand -hex 32`)
- [ ] `EVAL_RUNTIME_ALLOWED_ORIGIN` = URL Vercel exacte
- [ ] `SESSIONS_DIR=/data/sessions` configurée
- [ ] `DATA_CACHE_DIR=/data/data_cache` configurée
- [ ] Volume `/data/sessions` monté
- [ ] Volume/cache MAMH persistant monté et provisionné (`docs/MAMH-DATA-CACHE.md`)
- [ ] Smoke sources externes exécuté hors CI si réseau/identifiants disponibles (`docs/EXTERNAL-SOURCE-SMOKE.md`)
- [ ] `APP_ENV=production` configure.
- [ ] `python scripts/check_deploy_readiness.py --json` retourne `"ok": true`.
- [ ] `GET /readiness` retourne 200 et `GET /health` retourne 200.

### Frontend Vercel
- [ ] Projet importé depuis la racine du repo
- [ ] `RUNTIME_API_URL` = URL Railway
- [ ] `RUNTIME_API_TOKEN` = même valeur que `EVAL_RUNTIME_API_TOKEN`
- [ ] `NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY` configurées
- [ ] Build Vercel passe sans erreur
- [ ] `/api/runtime/app/state` retourne JSON (pas d'erreur 502)

### Test fonctionnel
- [ ] Créer un dossier → pipeline démarre
- [ ] Questionner Agent Dossier → réponse LLM reçue
- [ ] Générer paquet V1 → ZIP téléchargeable
- [ ] Acceptance dossier anonymisee executee avec un E.A. (`docs/EA-ACCEPTANCE.md`)

---

## Dev local

```bash
# Terminal 1 — backend
cd backend
python api.py          # démarre sur :8796

# Terminal 2 — frontend
npm run dev            # démarre sur :3000
```

Copier `.env.example` → `.env.local` et remplir `RUNTIME_API_URL=http://127.0.0.1:8796`.  
Sans `OPENAI_API_KEY`, les agents retournent des réponses déterministes.

---

## Notes techniques

- **Timeout BFF** : 120s pour `/app/create`, `/app/state`, `/app/package`, `/app/review/validate`. 30s pour les autres routes.
- **Streaming** : `/app/message/stream` utilise SSE — le body est pipé directement sans buffer ni timeout fixe.
- **Auth** : Si `NEXT_PUBLIC_SUPABASE_*` absent ou contient `<placeholder>`, le middleware passe en mode passthrough (pas d'auth). En prod avec vraies credentials, toutes les routes sauf `/login` sont protégées.
- **CORS** : `EVAL_RUNTIME_ALLOWED_ORIGIN` doit correspondre exactement à l'URL Vercel (sans slash final). En dev local, laisser `*`.
- **PyMuPDF** : Requiert `libgomp1` sur Linux — installé automatiquement par le `Dockerfile`.
- **Volume Railway** : Sans volume persistant, les sessions sont en mémoire uniquement et perdues au redémarrage.
- **Cache donnees publiques** : `DATA_CACHE_DIR` doit pointer vers un volume persistant. Le cache MAMH se provisionne avec `python scripts/provision_mamh_cache.py --cache-dir /data/data_cache --all`.
- **Smoke externes** : Infolot/MAMH/SIRF sont couverts par `backend/tests/test_live_external_sources.py`, désactivé par défaut. SIRF peut coûter de l'argent; activer seulement avec approbation.
