# Checklist orchestration runtime Aston (v0)

## Pre-conditions
- [x] Les 5 `AGENTCONFIG-*` existent et sont valides.
- [x] Les tools declares sont disponibles cote runtime Claude-style.
- [x] Le case directory est accessible en lecture/ecriture.

## Execution
- [x] Step 1 (data-facts) ecrit `fiche_bien.json`.
- [x] Step 2 (comps-market) ecrit `comparables_proposes.json`.
- [x] Step 3 (valuation-draft) ecrit les 3 approches + hypotheses.
- [x] Step 4 (compliance-qa) produit `statut_sortie.json`.
- [x] Step 5 (redaction) produit `brouillon_rapport.md`.

## Controles
- [x] Arret automatique si `A_REVOIR` bloquant.
- [x] Reprise manuelle possible via session persistante et surfaces de controller.
- [x] Events runtime visibles (`agent_session_start`, `tool_start`, `tool_end`, `agent_session_done`, etc.).
- [x] Metrics runtime capturees.

## Surfaces Claude Code adaptees
- [x] Runtime modes single-agent et pipeline Claude-style.
- [x] Agent manifest par role.
- [x] Prompts agents rendus avec sections static/dynamic/runtime contract.
- [x] Settings merge order compatible Claude Code.
- [x] Permissions, decisions, replay, updates et `additionalDirectories`.
- [x] Skills projet exposees comme prompt commands.
- [x] Slash commands, execution locale et historique.
- [x] Transcript Claude-style avec validation tool_use/tool_result.
- [x] Hooks, task state, handoffs et lineage artefacts.
- [x] Adaptateur modele opt-in `claude_live_data_facts_v0` expose via `/session/model-client`.
- [x] Adaptateur modele opt-in `claude_live_comps_market_v0` expose via `/session/model-client`.
- [x] Adaptateur modele opt-in `claude_live_valuation_draft_v0` expose via `/session/model-client`.
- [x] Adaptateur modele opt-in `claude_live_compliance_qa_v0` expose via `/session/model-client`.
- [x] Adaptateur modele opt-in `claude_live_redaction_v0` expose via `/session/model-client`.
- [x] Config provider modele redigee: `fake` est le seul provider executable par defaut, les providers reels restent bloques cote API/runtime.
- [x] Scaffold SDK Anthropic `anthropic_messages_v0` teste avec transport mock non-reseau; runtime API encore fake-only.
- [x] Boundary SDK reel `anthropic_sdk_transport_v0` ajoute: detection dependance optionnelle, lecture `ANTHROPIC_API_KEY` non persistee, flags explicites, timeout/retry et taxonomie d'erreurs testes avec SDK mock.
- [x] Diagnostics provider `/session/provider-diagnostics`: disponibilite SDK, guardrails manquants et config redigee sans construction client.
- [x] Runtime SDK Anthropic active uniquement avec flag operateur `EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME` + guardrails complets; tests avec factory SDK mock, aucun appel reseau live.
- [x] Boucle live `tool_use`/`tool_result`: tours bornes, execution via registre/permissions, preflight contrats artefacts, stop reasons explicites et surfaces `/session/model-client` + `/session/claude`.
- [x] Artefacts live declares adoptes sans overwrite deterministe, avec fallback deterministe pour sorties non produites.
- [x] Pipeline live `claude_live_pipeline_v0`: cinq agents, model client aggregate, live loop par agent, handoffs, permissions et transcript.
- [x] Reprise/replay live via `/session/live-replay`: validation transcript, replay permission, candidats retry et demandes `permission_state_ask_rule`.
- [x] Harness smoke provider reel hors CI: `outils/claude_live_provider_smoke_v0.py` + runbook, diagnostics-only par defaut et execution gatee par flags operateur.
- [x] Controller bundle `/session/claude` visible dans le cockpit produit.
