# State — eval-immo

_Updated: 2026-05-31 | HEAD: 8df43aa (master)_

## Current Goal

Session corrections UI — 10/11 fixes appliqués. Loading agent a discuter.

## Fixes déployés (8df43aa)

- #1 Ligne sous toolbar retirée + scroll-fade-top
- #2 Stepper : fond seul, plus de underline bleu
- #4 Counts faux retirés (Bibliothèque 348, Archives 142)
- #5 Modèles cards : layout colonne lisible
- #6 Archives : clic ouvre /dossier/[id]
- #7 Apparence : toggle Clair/Sombre
- #8 Paramètres : icône engrenage
- #9/11 Paramètres/Aide layout : retiré flex-direction:column de .main-content
- #10 Aide : icône ?

## Fix en attente

- #3 Loading agents : streaming token-by-token (llm_assistant_stream déjà en backend)
  ou typing dots — décision utilisateur requise

## État prod

- eval-immo.vercel.app
- blissful-reverence-production-ef1d.up.railway.app
- Supabase prod 13 tables + 8745 RAG chunks
