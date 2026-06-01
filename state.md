# State — eval-immo

_Updated: 2026-05-31 | HEAD: 29d6ae2 (master)_

## Current Goal

Session corrections UI — espace de travail agrandi, fixes déployés.

## Derniers fixes (29d6ae2)

- max-w-[640px] retiré de DossierPanel, MarchePanel, AnalysePanel, RapportPanel
  → contenu full-width (~820px vs 640px avant)
- ChatInput fixe au bas sur tous les onglets avec agents (Dossier, Marché, Analyse, Rapport)
- Side cards 340→300px, padding px-10→px-8
- overflow-hidden sur onglets avec ChatInput

## Fix #3 en attente

- Loading streaming token-by-token (backend prêt : llm_assistant_stream)
