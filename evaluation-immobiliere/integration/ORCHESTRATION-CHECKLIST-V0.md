# Checklist orchestration runtime Aston (v0)

## Pré-conditions
- [ ] Les 5 `AGENTCONFIG-*` existent et sont valides.
- [ ] Les tools déclarés sont disponibles côté Aston.
- [ ] Le case directory est accessible en lecture/écriture.

## Exécution
- [ ] Step 1 (data-facts) écrit `fiche_bien.json`.
- [ ] Step 2 (comps-market) écrit `comparables_proposes.json`.
- [ ] Step 3 (valuation-draft) écrit les 3 approches + hypothèses.
- [ ] Step 4 (compliance-qa) produit `statut_sortie.json`.
- [ ] Step 5 (redaction) produit `brouillon_rapport.md`.

## Contrôles
- [ ] Arrêt automatique si `A_REVOIR` bloquant.
- [ ] Reprise manuelle possible après correction.
- [ ] Events runtime visibles (`step_start`, `step_done`, etc.).
- [ ] Metrics runtime capturées.
