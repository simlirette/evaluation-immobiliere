# Architecture cible & plan de migration cloud — eval-immo

**Date :** 2026-05-31  
**Déclencheur :** ~200 évaluateurs actifs simultanés ou premier bureau > 10 É.A.

---

## 1. Architecture actuelle (Phase 5)

```
Frontend (Vercel/Next.js)
    │
    ▼ BFF Next.js API routes (/api/runtime/*)
    │
    ▼ Backend Python (Railway — simple process)
       runtime_sessions/    ← filesystem local (non partagé)
       backend/knowledge/   ← corpus RAG (statique)
    │
    ▼ Supabase (West US — Oregon)
       auth, dossiers, sessions, sirf_cache, knowledge_chunks, bureaux
```

**Limites actuelles :**
- `runtime_sessions/` est sur disque local Railway → non partageable entre instances
- Un seul process Python → pas de scale horizontal
- Supabase West US → latence ~80ms depuis Montréal (acceptable, < 150ms cible)

---

## 2. Architecture cible (~200 É.A.)

```
Frontend (Vercel — CDN edge)
    │
    ▼ Supabase Edge Functions (auth BFF)
    │
    ▼ Backend Python (Railway — auto-scale)
       sessions → Supabase Storage (partagé entre instances)
       knowledge → Supabase (déjà pgvector)
    │
    ▼ Supabase (région Canada si disponible sinon US-East)
```

**Changements principaux :**
1. `runtime_sessions/` → Supabase Storage (bucket `sessions`)
2. Scale horizontal automatique Railway (2-4 instances peak)
3. Supabase region upgrade → Canada (dès disponibilité) pour Loi 25

---

## 3. Résidence des données (Loi 25 art. 17)

| Composant | Localisation actuelle | Cible |
|---|---|---|
| Auth, dossiers, sessions | Supabase West US (Oregon) | Canada (dès dispo Supabase) |
| RAG knowledge_chunks | Supabase West US | Idem |
| runtime_sessions/ | Railway (US) | Supabase Storage (Canada) |
| Frontend | Vercel (CDN global) | Acceptable (statique) |

**Note :** Loi 25 art. 17 requiert consentement explicite ou encadrement contractuel pour transfert hors Québec. Supabase n'offre pas encore de région Canada (2026-05). Options :
- Attendre Supabase Canada
- Contrat DPA (Data Processing Agreement) avec Supabase + clause art. 17
- Migration vers Neon + Fly.io (Canada) si Supabase n'offre pas le Canada

---

## 4. Migration sessions filesystem → Supabase Storage

**Effort :** M (1-2 sprints)

**Plan :**
1. Créer bucket `runtime-sessions` dans Supabase Storage (RLS par evaluator_id/bureau_id)
2. Adapter `api.py` : remplacer `SESSIONS_DIR` / filesystem par calls Storage
3. Conserver filesystem comme repli local (dev)
4. Migration zéro-downtime : nouveau code lit Storage d'abord, filesystem en fallback

**Fichiers cibles :**
- `api.py` : `SESSIONS_DIR`, `create_session`, `load_session`, `save_session`
- `apicore/sessions.py` : abstraire via interface `ISessionStore`
- `supabase/migrations/009_sessions_storage.sql` : policies bucket

---

## 5. Seuil de déclenchement

| Seuil | Action |
|---|---|
| > 5 bureaux actifs | Appliquer migration sessions → Storage |
| > 50 É.A. simultanés | Scale horizontal Railway (2 instances) |
| > 200 É.A. ou data sensible entreprise | Contrat DPA Supabase + revue Loi 25 |
| Supabase Canada disponible | Migration région (1 semaine effort) |

---

## 6. Coûts estimés à l'échelle

| Composant | 10 É.A. | 100 É.A. | 200 É.A. |
|---|---|---|---|
| Railway (backend) | $5/mois | $20/mois | $40/mois |
| Supabase (DB + Storage) | $25/mois | $100/mois | $200/mois |
| Vercel (frontend) | $0 (free) | $20/mois | $40/mois |
| OpenAI (LLM/RAG) | ~$5/dossier | ~$3/dossier | ~$2/dossier |
