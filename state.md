# State — eval-immo

_Updated: 2026-06-01 | HEAD: 0c2ad0c (master)_

## Frontend — État final session UI

Tous les fixes déployés sur https://eval-immo.vercel.app

### Layout conversation (style Claude)
- Messages + ChatInput dans même max-w-[900px] mx-auto
- Stepper dans grid 1fr/300px → aligné avec colonne conversation
- Dégradé bas sous messages, ChatInput fixe
- Liquid glass topbar (backdrop-blur)

### ChatInput redesigné
- rounded-[18px], paper-hi, border subtile
- Textarea auto-resize
- Layout 2 rangées (texte haut, boutons bas)
- w-full (pas de max-w propre)

### Autres fixes
- Sidebar layout, stepper style, dark mode toggle
- Modèles cards, Archives click, counts faux retirés
- Paramètres/Aide layout, icons engrenage/?

## Prochain — Loading streaming agents

Backend prêt : llm_assistant_stream dans api.py.
Frontend : implémenter SSE/streaming dans useAgentChat hook.
Pattern : tokens arrivent en temps réel, curseur clignotant (▊).
