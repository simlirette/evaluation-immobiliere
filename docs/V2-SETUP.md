# V2 Setup — Required Manual Steps

## 1. Run the Supabase migration

In the Supabase dashboard → SQL Editor, run the contents of:

```
supabase/migrations/001_v3_schema.sql
```

This creates: `dossiers`, `user_dossier_pins`, `property_facts`, `documents`,
`comparables`, `adjustments`, and the `dossier-documents` storage bucket.

Only needed once per Supabase project.

## 2. Enable LLM agent responses

Add to your local environment file and Railway environment variables:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini   # optional, this is the default
```

Without this key, agent chat falls back to deterministic template responses.
The code in `backend/api.py` handles both cases automatically — no code change needed.

## 3. Create the first user

Supabase dashboard → Authentication → Users → Invite user.

The login page at `/login` is invite-only (no public signup).
Middleware now enforces auth on all routes — unauthenticated requests redirect to `/login`.

## 4. Deploy

### Backend — Railway
```
SESSIONS_DIR=/data/runtime_sessions
OPENAI_API_KEY=sk-...
EVAL_RUNTIME_API_TOKEN=<random-secret>
```

### Frontend — Vercel
```
NEXT_PUBLIC_SUPABASE_URL=https://<project>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon-key>
RUNTIME_API_URL=https://<railway-app>.railway.app
RUNTIME_API_TOKEN=<same-secret-as-backend>
```

## Architecture (V2 hybrid)

```
Browser → Next.js (Vercel)
  ├── Auth:            Supabase (sessions, RLS, invite-only)
  ├── Dossier list:    Supabase DB (dossiers table, per-user RLS)
  ├── Pins:            Supabase DB (user_dossier_pins table)
  └── Dossier data:    Railway runtime API (facts, comps, report, agents)
```

## What changed in V2

| Feature | Before | After |
|---------|--------|-------|
| Auth guard | Middleware passed all requests | Redirects to /login if no session |
| Dossier list | Runtime JSON files + localStorage | Supabase `dossiers` table |
| Pins | localStorage | Supabase `user_dossier_pins` |
| Agent chat | Deterministic template | Real LLM (when OPENAI_API_KEY set) |
| Sign-out | Already worked | Already worked |
