# Intégration — adaptation directe d'Aston

Ce dossier contient les artefacts d'adaptation **directe** de l'infrastructure Aston vers l'évaluation immobilière.
On conserve le cœur Aston et on remplace principalement les modules métier.

## Artefacts disponibles
- `AGENTCONFIG-DATA-FACTS-V0.yaml`
- `AGENTCONFIG-COMPS-MARKET-V0.yaml`
- `AGENTCONFIG-VALUATION-DRAFT-V0.yaml`
- `AGENTCONFIG-COMPLIANCE-QA-V0.yaml`
- `AGENTCONFIG-REDACTION-V0.yaml`
- `TOOL-MAPPING-ASTON-V0.md`
- `PIPELINE-RUNTIME-ASTON-V0.yaml`
- `ORCHESTRATION-CHECKLIST-V0.md`
- `CLAUDE-CODE-ADAPTATION-V0.md`
- `CLAUDE-LIVE-PROVIDER-SMOKE-RUNBOOK.md`
- `AGENT-SKILLS-MATRIX.md`
- `AGENT-ARTIFACT-CONTRACTS-V0.json`

## Principe d'intégration
- Garder la structure Aston (engine/orchestration/events).
- Adapter seulement les briques métier immobilières (prompts/tools/rules/outputs).
- Limiter les modifications infra au strict nécessaire.
- Declarer les skills projet par agent dans `skills_allowed`, puis les exposer via le runtime sans charger toute la connaissance dans chaque etape.
- Verifier les artefacts metier produits par chaque agent avec `outils/verifier_contrats_artefacts_agents_v0.py`.
- Adapter les surfaces Claude Code agent par agent: settings, permissions, commands, skills, tools, prompts, transcript, hooks, tasks, handoffs et controller.
- Garder la compatibilite avec `permissions.additionalDirectories` pour rattacher `C:\Users\simon\claude-code-project` au contexte permissionnel local quand requis.
- Introduire les agents live uniquement via des modes opt-in qui reutilisent les contrats Claude-style existants: `claude_live_data_facts_v0`, `claude_live_comps_market_v0`, `claude_live_valuation_draft_v0`, `claude_live_compliance_qa_v0`, puis `claude_live_redaction_v0`.
- Garder le provider modele en mode `fake` par defaut; toute option provider est redigee et les providers reels restent bloques cote API/runtime.
- Exercer le scaffold Anthropic avec transport mock non-reseau et garder le transport SDK reel derriere les guardrails explicites: dependance Anthropic optionnelle, `ANTHROPIC_API_KEY`, `allow_network`, `enable_sdk_execution`, timeout/retry et taxonomie d'erreurs.
- Exposer les diagnostics provider via `/session/provider-diagnostics` avant tout run reel; l'execution Anthropic runtime exige aussi le flag operateur `EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME`.
- Executer les `tool_use` live via le registre eval-immo existant avec `tool_result`, tours bornes, stop reasons explicites et preflight contrat artefact avant tout `write_file`.
- Adopter les artefacts live declares quand le modele les ecrit correctement, avec fallback deterministe seulement pour les artefacts non produits.
- Exposer `/session/live-replay` pour reprise operateur: validation transcript, replay permissions, demandes `ask` et candidats retry.
- Garder les vrais smoke providers hors CI via `outils/claude_live_provider_smoke_v0.py`; le mode par defaut est diagnostics-only et `--execute` exige les flags operateur.

## Ordre d'intégration recommandé
1. data-facts
2. comps-market
3. valuation-draft
4. compliance-qa
5. redaction
