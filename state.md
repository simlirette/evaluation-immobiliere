# State — eval-immo

_Updated: 2026-05-31 | HEAD: f2a3727 (master)_

## Current Goal

Prod live + bugs UI corrigés. Prochaine : E.A. bêta.

## Fixes récents (cette session)

- Sidebar layout : .sidebar.open ~ .main-content { margin-left: 260px } (06f89bf)
- Double input : AgentChat flottant non branché supprimé (f2a3727)
- Tokens Railway-Vercel synchronisés (blissful-reverence = Python backend)
- Migration 009 profiles ea fields appliquée prod

## État prod

- Frontend : https://eval-immo.vercel.app (Vercel)
- Backend : https://blissful-reverence-production-ef1d.up.railway.app (Railway Python)
- DB : vsarxgbzwxludarjhrnf.supabase.co (13 tables + 8745 RAG chunks)

## Prochaines étapes

1. E.A. bêta — tester avec un vrai dossier
2. Onboarding / inscription E.A.
3. Stripe facturation (metering deja en place)
