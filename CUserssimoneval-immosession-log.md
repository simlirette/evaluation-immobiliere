
## 2026-05-15 [saved]
Goal: Batch 8b livré + Batch 9 design — live view pipeline + UX polish
Decisions:
- Batch 8b: export base64 JSON (pas binaire) — BFF proxy corrompt binaire ; _generate_docx/_generate_html module isolé.
- Batch 9: usePipelinePolling hook (polling 2s /app/state) — zéro changement backend, steps déjà dans AppState.
- Batch 9: DragHandle custom (mousemove/mouseup) pour resize rapport panel — pas de lib externe, localStorage persist.
- Batch 9: PanelSkeleton remplace PanelLoader — animate-pulse Tailwind, prépare test É.A. end-to-end.
Rejected:
- WeasyPrint PDF backend — dépendances GTK/Cairo Windows, trop fragile.
- SSE pour live view — polling 2s suffisant, zéro infra supplémentaire.
Open:
- Pipeline jamais testé bout-en-bout — qualité É.A. inconnue.
- Rôle d'évaluation foncière municipal (auto-fill) — Batch 10+.
