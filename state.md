# State — eval-immo

_Updated: 2026-06-01 | HEAD: 9244184 (master)_

## Current Goal

Session corrections UI — layout Claude répliqué.

## Derniers fixes

- Pattern Claude : messages + ChatInput dans même max-w-[760px] mx-auto → alignement parfait
- Stepper aligné avec max-w-[760px] mx-auto
- Dégradé bas : contenu s'estompe avant input (comme Claude desktop)
- Fix TS : gradient/ChatInput dans colonne centrée (MarchePanel, AnalysePanel)

## Fix #3 en attente

- Loading streaming token-by-token (backend prêt : llm_assistant_stream)
