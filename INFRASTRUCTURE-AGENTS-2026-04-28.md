# Infrastructure des agents Aston — analyse complète

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Le moteur unifié (`src/engine/`)](#2-le-moteur-unifié-srcengine)
3. [Les quatre agents — vue comparative](#3-les-quatre-agents--vue-comparative)
4. [Agent Facts — analyse documentaire](#4-agent-facts--analyse-documentaire)
5. [Agent Research — recherche jurisprudentielle](#5-agent-research--recherche-jurisprudentielle)
6. [Agent AC Research — actions collectives](#6-agent-ac-research--actions-collectives)
7. [Agent Redaction — rédaction de documents](#7-agent-redaction--rédaction-de-documents)
8. [Sous-système d'outils](#8-sous-système-doutils)
9. [Pipeline RAG](#9-pipeline-rag)
10. [Pipeline de gestion de contexte](#10-pipeline-de-gestion-de-contexte)
11. [Vérification post-agent](#11-vérification-post-agent)
12. [Knowledge base — le mécanisme de handoff](#12-knowledge-base--le-mécanisme-de-handoff)
13. [Streaming SSE](#13-streaming-sse)
14. [Persistance](#14-persistance)
15. [Surface API](#15-surface-api)
16. [Hooks frontend](#16-hooks-frontend)
17. [Flow complet d'un dossier](#17-flow-complet-dun-dossier)

---

## 1. Vue d'ensemble

### 1.1 Idée centrale

Aston repose sur **une seule boucle d'agent** (`agent_loop()` dans `src/engine/loop.py`) qui exécute **tous** les agents. Chaque agent n'est qu'un `AgentConfig` (un dataclass de paramètres) qui décrit :

- les prompts système (statique + dynamique)
- les outils disponibles
- les budgets (itérations, tokens, fenêtre de contexte, wall-clock)
- des flags (thinking, long_cache, verification_checklist)

L'engine se charge du streaming, du caching prompt, de l'exécution concurrente d'outils, de la récupération d'erreurs, de la compaction de contexte, de la détection d'anti-loop et des nudges de continuation.

### 1.2 Architecture haut niveau

```
┌──────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
│   use-facts │ use-research │ use-ac-research │ use-redaction │
│        ↑              ↑              ↑              ↑         │
│        └──────────────┴──── SSE ─────┴──────────────┘         │
└────────────────────────────┬─────────────────────────────────┘
                             │ HTTP + SSE
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                    FastAPI (src/api.py)                      │
│   3 endpoints par agent : /session  /start  /stream          │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│              Engine unifié (src/engine/loop.py)              │
│                                                              │
│   ┌────────────────┐   ┌────────────┐   ┌──────────────┐    │
│   │  AgentConfig   │   │ AgentState │   │ task_bus     │    │
│   │  (paramètres)  │   │ (mutable)  │   │ (SSE events) │    │
│   └────────────────┘   └────────────┘   └──────────────┘    │
│                                                              │
│   pipelines: snip → compact → estimate → collapse →          │
│              summarize → restore → validate                  │
│                                                              │
│   per-turn: build_cached_system → API call →                 │
│             stop_reason branching → tool exec → continue     │
└────────────┬───────────────────────┬─────────────────────────┘
             │                       │
             ▼                       ▼
┌─────────────────────┐    ┌──────────────────────────────────┐
│  Anthropic API      │    │  Tools (concurrent ≤ 10)         │
│  (streaming)        │    │  general / legal / ac            │
└─────────────────────┘    └──────────┬───────────────────────┘
                                      │
                                      ▼
                       ┌──────────────────────────────────┐
                       │  RAG: pgvector + ZeroEntropy     │
                       │  Storage: filesystem / Azure     │
                       │  Persistence: PostgreSQL         │
                       └──────────────────────────────────┘
```

### 1.3 Les quatre agents

| Agent | Rôle | Output | Fichier de config |
|-------|------|--------|-------------------|
| **Facts** | Lit les fichiers du dossier, écrit le résumé des faits | `faits/resume-des-faits.md`, `faits/chronologie.md` | `src/agents/facts.py` |
| **Research** | Recherche jurisprudence + doctrine, écrit un mémo | `analyse-juridique/<memo>.md` | `src/agents/research.py` |
| **AC Research** | Recherche dans le registre des actions collectives | `analyse-juridique-ac/<memo>.md` | `src/agents/ac_research.py` |
| **Redaction** | Rédige un document HTML court-prêt | `procedures/<doc>.html` ou `redaction/<doc>.html` | `src/agents/redaction.py` |

Chaque agent **lit le knowledge base du dossier** (vue tailorisée), exécute sa boucle, **écrit un artefact**, et **déclenche une mise à jour asynchrone du knowledge** (sauf Redaction qui est terminal).

---

## 2. Le moteur unifié (`src/engine/`)

### 2.1 Composants

| Fichier | Rôle |
|---------|------|
| `loop.py` | La boucle principale `agent_loop()` |
| `config.py` | Dataclass `AgentConfig` — 60+ champs |
| `state.py` | Dataclass `AgentState` — compteurs, tokens, phase |
| `anti_loop.py` | Détection 3 appels d'outil identiques |
| `continuation.py` | Décide d'envoyer un nudge "continuez" |
| `recovery.py` | Escalade max_tokens, retry API, prompt-too-long |

### 2.2 `AgentConfig` — les paramètres

Champs critiques (`src/engine/config.py:18-62`) :

| Champ | Défaut | Rôle |
|-------|--------|------|
| `agent_type` | — | "facts", "research", "ac-research", "redaction" |
| `model` | "claude-sonnet-4-6" | Modèle LLM |
| `system_prompt_static` | str | Prompt statique injecté dans le system |
| `system_prompt_dynamic` | callable\|str | Résolu à chaque session (knowledge, mémos existants, draft status) |
| `tools` | dict[str, Tool] | Outils disponibles |
| `max_iterations` | 15 | Limite de tours |
| `max_tokens` | 8192 | Tokens max par appel API |
| `max_total_tokens` | 25 000 | Budget cumulé session |
| `window_size` | 8 | Messages récents à conserver après compaction |
| `thinking_enabled` | False | Active extended thinking |
| `thinking_budget_tokens` | 2000 | Budget thinking par tour |
| `long_cache` | False | Demande TTL cache 1h via beta header |
| `max_wall_clock_seconds` | None | Budget temps réel |
| `force_write_after_n_non_write_tools` | None | Seuil pour nudge "écrivez maintenant" |
| `verification_checklist` | None | Active le quality gate post-agent |
| `case_dir`, `case_id`, `tenant_id`, `user_id`, `session_id` | — | Contexte multi-tenant |

### 2.3 `AgentState` — l'état mutable

(`src/engine/state.py`)

- **Compteurs de boucle** : `turn_count`, `transition` (recovery/compaction/continuation)
- **Recovery** : `recovery_attempts`, `max_tokens_escalations`, `has_compacted`, `compaction_count`
- **Tokens** : `usage_input_tokens`, `usage_output_tokens`, `usage_cache_read_tokens`, `usage_cache_write_tokens`, `usage_thinking_tokens`, `token_budget_used`
- **Phase research** : `research_phase` (analyze/search/reading/writing/summary), `memo_nudge_attempts`
- **Nudges** : `finalize_nudge_sent`, `total_output_nudge_sent`, `force_write_nudge_sent`, `non_write_tool_count`
- **Lifecycle** : `wall_clock_started_at`, `messages: list[dict]`

`should_stop()` (`state.py:65-67`) : `turn_count >= max_iterations`.

### 2.4 Déroulé d'un tour de boucle

Pour chaque itération du `while not state.should_stop()` (`loop.py:344`) :

```
TOUR N
│
├─ 1. Incrémenter state.turn_count, _pop_transition()
│
├─ 2. Vérifier budgets
│   ├─ wall_clock : ok / finalize_now / hard_stop  (loop.py:107-123)
│   └─ output_tokens : ok / finalize_now / hard_stop  (loop.py:131-149)
│
├─ 3. Pipeline de gestion de contexte (loop.py:391-419)
│   ├─ snip_duplicate_reads()   → retire les read_file/get_decision_text redondants
│   ├─ compact_tool_results()   → tronque résultats anciens (800 chars max)
│   ├─ estimate_tokens()        → heuristique 4 chars = 1 token
│   ├─ Si over-budget OU transition="compaction" :
│   │   ├─ structured_summarize() → résumé Haiku 9 sections
│   │   ├─ collapse_old_messages() → garde les N derniers
│   │   └─ restore_critical_context() → réinjecte knowledge + artefacts récents
│   └─ validate_and_repair()    → réordonne user/assistant, strippe orphelins
│
├─ 4. Construction du system prompt caché (loop.py:326-341)
│   ├─ Date du jour injectée
│   ├─ system_prompt_static
│   ├─ await system_prompt_dynamic() (knowledge + mémos + draft status)
│   └─ build_cached_system() avec cache_control (épémère 5min ou 1h si long_cache)
│
├─ 5. Résolution thinking budget (loop.py:70-83)
│   └─ thinking_budget_per_turn(state, messages) ou défaut
│
├─ 6. Appel API streaming (loop.py:444-561)
│   ├─ AgentStreamRequest(model, system, messages, tools, thinking, ...)
│   ├─ Headers beta extended-cache-ttl si long_cache
│   ├─ Streaming des blocs : text_delta, tool_json_delta, content_block_stop
│   ├─ Détection phase research sur tool_use start (analyze/search/reading/writing)
│   ├─ Progressive HTML stream pour tool calls write_file (loop.py:1273-1298)
│   └─ stop_reason : end_turn / tool_use / max_tokens
│
├─ 7. Gestion des erreurs API (loop.py:563-584)
│   ├─ "prompt too long" → recover_prompt_too_long → transition="compaction" → CONTINUE
│   └─ LlmApiError → recover_api_error → backoff exp 2/4/8s → CONTINUE (max 3 tentatives)
│
├─ 8. Logging usage + accumulation tokens + emit usage SSE (loop.py:586-630)
│
├─ 9. Sanitize + persist assistant message (loop.py:635-652)
│   ├─ sanitize_output() → supprime emoji, em-dashes, exclamations
│   ├─ Emit message_commit
│   └─ store.add_message()
│
└─ 10. BRANCH sur stop_reason
    │
    ├─ "max_tokens" → recover_max_tokens (escalade 1.5×, max 3) + RESUME_MESSAGE → CONTINUE
    │
    ├─ "tool_use" :
    │   ├─ detect_loop() → si 3 calls identiques : nudge anti-loop, CONTINUE
    │   ├─ Filtrer via research_guard si applicable
    │   ├─ Forcer output_path pour write_file/edit_file en redaction
    │   ├─ execute_tools() en concurrent (≤ 10 parallèle, sémaphore)
    │   ├─ Émettre tool_start / tool_end / source_found / artifact_created
    │   ├─ Append tool_result blocks à state.messages
    │   ├─ Append nudges (force_write si force_write_after_n dépassé, iteration warning)
    │   └─ CONTINUE
    │
    └─ "end_turn" :
        ├─ should_continue() (≥90% budget, < 3 low-output) → nudge default → CONTINUE
        ├─ Research sans memo + 3+ tools → memo nudge → CONTINUE
        ├─ Phase transition writing → summary
        ├─ Verification (si checklist) :
        │   ├─ verify() retourne PASSE/ECHEC/PARTIEL + auto_fixable
        │   └─ Si should_auto_fix → append fix_msg → CONTINUE (max 2 cycles)
        └─ Sinon → emit done → RETURN

POST-LOOP (si turn_count atteint) :
├─ Si research sans artifact + 3+ tools → appel final write_file forcé
└─ Sinon → appel final text-only forcé
```

### 2.5 Anti-loop

(`src/engine/anti_loop.py:13-46`)

```python
def detect_loop(messages: list[dict], threshold: int = 3) -> bool:
    # Scan reverse, prend les 3 derniers tool_use des messages assistant
    # Compare (name, json.dumps(input, sort_keys=True))
    # Si tous identiques → True
```

Si déclenché : nudge `"[SYSTEME] Vous appelez {tool} de façon répétée. Changez d'approche."` injecté à `state.messages` **sans exécuter les outils**, puis `continue`.

### 2.6 Continuation

(`src/engine/continuation.py`)

Constantes :
- `CONTINUATION_THRESHOLD = 0.9` — continue si 90%+ du `max_tokens` consommés
- `LOW_OUTPUT_THRESHOLD = 500` — output < 500 tokens compte comme "faible"
- `MAX_LOW_OUTPUT_TURNS = 3` — stop après 3 tours faibles consécutifs

Trois variantes de nudges :
- `default` : `"[SYSTEME] Continuez."`
- `force_write` : "Le temps approche de sa limite. Écrivez immédiatement avec write_file. [CROCHETS] pour info manquante."
- `finalize_soft` : "Vous avez utilisé une large part du budget. Finalisez le brouillon maintenant."

### 2.7 Recovery

(`src/engine/recovery.py`)

| Mécanisme | Constantes | Action |
|-----------|------------|--------|
| Max tokens escalade | factor=1.5, max=3, ceiling=32768 | Escalade `current_max_tokens × 1.5`, append `RESUME_MESSAGE` |
| API error retry | max=3, backoff exp 2/4/8s | `recovery_attempts++`, sleep, retry |
| Prompt too long | — | `state.transition = "compaction"`, force compaction au prochain tour |

`RESUME_MESSAGE` (`recovery.py:20-28`) :
> "[SYSTEME] Vous avez atteint la limite de tokens en sortie. Reprenez EXACTEMENT où vous vous êtes arrêté. Pas d'excuses, pas de récapitulation, pas de recommencement."

### 2.8 Caching prompt

(`src/cache_utils.py`)

- **Standard** : `{"type": "ephemeral"}` → TTL 5 minutes (défaut Anthropic)
- **Long cache** : `{"type": "ephemeral", "ttl": "1h"}` si `config.long_cache=True`, header beta `extended-cache-ttl-2025-04-11`

`build_cached_system(*blocks, config)` met `cache_control` sur le **dernier bloc** (date + static + dynamic). Les outils peuvent aussi être cachés via `add_cache_to_tools()`.

Logging par tour : `tokens [agent] iter=N: input=X, output=Y, cache_write=Z, cache_read=W`.

### 2.9 Sanitization

(`src/sanitize.py:32-69`) — appliqué sur tout texte assistant avant `message_commit` et persistance :

1. Strip `<thinking>...</thinking>`
2. `—` (em dash) et `–` (en dash) et `--` → `, `
3. Emojis (regex Unicode) → supprimés
4. `!` → `.`
5. Cleanup : `..` → `.`, `  ` → ` `

**N'est pas appliqué** au contenu HTML des artefacts (sanitization HTML séparée via `bleach`).

---

## 3. Les quatre agents — vue comparative

| Aspect | Facts | Research | AC Research | Redaction |
|--------|-------|----------|-------------|-----------|
| **agent_type** | facts | research | ac-research | redaction |
| **max_iterations** | 20 | 12-28 (effort-based) | 15 | 12 |
| **max_tokens** | 16 384 | 8 192-16 384 | 8 192 | 16 384 |
| **window_size** | 8 | 10-16 | 8 | 12 |
| **max_total_tokens** | 20 000 | 25 000-70 000 | 25 000 | 30 000 |
| **thinking** | non | oui (par session) | oui (par session) | non |
| **system prompt** | statique seulement | statique + dynamic context | statique + dynamic context | statique + skill MD + dynamic context |
| **outils** | 6 (file system + cross_reference) | 11 (légaux) | 7 (AC) | 6 (file system + get_decision_text) |
| **silence rule** | doit produire texte avant chaque outil | aucun texte entre outils | 3 moments texte autorisés | 1 phrase max entre outils |
| **artifact dir** | `faits/` | `analyse-juridique/` | `analyse-juridique-ac/` | `procedures/` ou `redaction/` |
| **knowledge updated** | facts + identity + evidence | legal + strategy | (idem research) | aucune (terminal) |
| **knowledge lu** | identity | identity + facts | identity + facts | identity + facts + legal + strategy |

---

## 4. Agent Facts — analyse documentaire

### 4.1 Configuration

(`src/agents/facts.py:128-167`, profil `src/llm/profiles.py:53-63`)

```python
AgentConfig(
    agent_type="facts",
    system_prompt_static=_SYSTEM_PROMPT,  # ~120 lignes, purement statique
    tools={
        "list_files": ListFilesTool(),
        "read_file": ReadFileTool(),
        "write_file": WriteFileTool(),
        "edit_file": EditFileTool(),
        "search_files": SearchFilesTool(),
        "cross_reference_parties": CrossReferencePartiesTool(),
    },
    max_iterations=20,
    max_tokens=16_384,
    window_size=8,
    max_total_tokens=20_000,
    # thinking désactivé, pas de system_prompt_dynamic
)
```

### 4.2 Deux phases procédurales

**Phase 1 — Premier message** (`facts.py:53-58`) :

1. "Je prends connaissance du dossier." → `list_files()`
2. "J'ai lu les [N] documents. Je rédige le résumé." → `read_file()` × N
3. `write_file("faits/resume-des-faits.md", content)`
4. Synthèse brève (points saillants)

**Phase 2 — Messages suivants** (`facts.py:60-66`) :

- Le résumé existe déjà
- `read_file` sur l'artifact avant toute modification
- `edit_file` pour modifications chirurgicales
- **Pas** de `list_files` (les fichiers ont déjà été lus)
- `write_file("faits/chronologie.md", ...)` seulement si demandé

**Le prompt système est identique entre Phase 1 et Phase 2** ; le modèle déduit la phase du contexte (présence de l'artefact dans le knowledge ou les messages précédents).

### 4.3 Communication forcée

Particularité de Facts (contraire à Research) : **doit produire du texte avant chaque appel d'outil** (`facts.py:44-58`). C'est le seul agent où la règle est inversée.

### 4.4 Outputs

| Artifact | Quand |
|----------|-------|
| `faits/resume-des-faits.md` | Toujours en Phase 1 |
| `faits/chronologie.md` | Sur demande explicite du juriste |

Structure du résumé : Parties (table avec alias), Contexte, Faits établis, Faits contestés, Lacunes factuelles, Règle d'alias.

### 4.5 Side-effect : knowledge update

Après le `write_file`, le tool déclenche fire-and-forget (`src/tools/general/write_file.py:97-120`) :

```python
if "resume-des-faits" in path or "chronologie" in path:
    asyncio.create_task(update_knowledge_from_facts(...))
```

→ Voir [§12 Knowledge base](#12-knowledge-base--le-mécanisme-de-handoff).

---

## 5. Agent Research — recherche jurisprudentielle

### 5.1 Configuration

(`src/agents/research.py:336-415`, profil `src/llm/profiles.py:64-77`)

```python
AgentConfig(
    agent_type="research",
    system_prompt_static=_SYSTEM_PROMPT,        # ~240 lignes, 7 sections
    system_prompt_dynamic=lambda: _build_research_context(config),
    tools={
        # Légaux
        "search_caselaw": SearchCaselawTool(),
        "search_caselaw_keyword": SearchCaselawKeywordTool(),
        "get_decision_text": GetDecisionTextTool(),
        "find_decision_by_title": FindDecisionByTitleTool(),
        "check_decision_status": CheckDecisionStatusTool(),
        "search_private_legal_knowledge": SearchDoctrineTool(),
        "check_prescription": CheckPrescriptionTool(),
        "verify_citation": VerifyCitationTool(),
        "validate_document": ValidateDocumentTool(),
        "cross_reference_parties": CrossReferencePartiesTool(),
        # File system
        "list_files": ..., "read_file": ..., "write_file": ...,
    },
    max_iterations=12-28,           # selon effort
    max_tokens=8192-16384,
    window_size=10-16,
    max_total_tokens=25_000-70_000,
    thinking_enabled=True,
    thinking_budget_tokens=2000-6000,
    extra_tool_context={"allowed_courts": court_filters},  # optionnel
    research_plan=plan_dict,        # plan déterministe optionnel
)
```

### 5.2 Budgets adaptatifs (effort)

(`src/agents/research.py:34-89`)

L'effort est classé en **standard / expanded / deep** selon la longueur de la question et le nombre d'éléments listés :

| Effort | Trigger | max_iter | max_tok | window | total_tok | thinking |
|--------|---------|----------|---------|--------|-----------|----------|
| **standard** | défaut | 12 | 8192 | 10 | 25 000 | 2 000 |
| **expanded** | question > 450 chars OU 6+ items OU 3+ complex lanes | 20+ | 12 288+ | 14+ | 45 000+ | 4 000+ |
| **deep** | question > 1000 chars OU 10+ items OU 4+ complex lanes | 28+ | 16 384+ | 16+ | 70 000+ | 6 000+ |

### 5.3 Structure du system prompt

7 sections (`research.py:92-293`) :

1. **Mandat** — rechercher jurisprudence + doctrine, écrire mémo avec extraits verbatim
2. **Silence** — *aucun texte entre les appels d'outils*. Le panneau gauche affiche déjà les décisions consultées. Seul un message final 2-3 phrases après `write_file`. Violer = échec.
3. **Méthode** — 6 étapes : suivre le plan déterministe (si fourni), qualifier la question, doctrine privée optionnelle, deux voies (keyword + thématique), `get_decision_text` (un seul appel par décision), écrire le mémo
4. **Budget** — question simple : 3-4 recherches, 3-4 lectures, 1 mémo. Question complexe : couvrir le plan, plus de lectures, vérifier statuts. Si système nudge : écrire avec ce qui existe.
5. **Format du mémo** — titre, réponse directe (1-3 phrases), bloc par décision (titre + encadrement + blockquote verbatim [N] + portée), section "En résumé". 3-5 décisions au total. Aucun duplicata de [N], pas de mention "doctrine".
6. **Questions de suivi** — conversationnel, mise à jour du mémo (section "Mise à jour — AAAA-MM-JJ"), nouveau mémo (write_file avec nom différent, jamais d'écrasement)
7. **TONE_BLOCK** (injection depuis `tone.py`) — vouvoiement, pas d'emoji, pas de filler

### 5.4 Phases (5 phases SSE)

Les phases sont **détectées par l'engine** à partir du nom de l'outil appelé (`loop.py:376-389`), pas par le modèle :

| Phase | Trigger (premier appel) | Label SSE |
|-------|-------------------------|-----------|
| `analyze` | début de session | "Analyse de la question" |
| `search` | `search_caselaw` ou `search_caselaw_keyword` | "Recherche d'autorités" |
| `reading` | `get_decision_text` | "Lecture des décisions" |
| `writing` | `write_file` | "Rédaction du mémo" |
| `summary` | end_turn après `write_file` | "Synthèse" |

L'engine émet `phase_start` et `phase_complete` à chaque transition. Le frontend les rend dans une barre de progression.

### 5.5 Contexte dynamique injecté

(`research.py:300-329`)

```python
async def _build_research_context(config: AgentConfig) -> str:
    parts = []
    # 1. Knowledge base (~900 tokens)
    kb = await render_knowledge_for_agent(case_dir, "research", tenant_id)
    parts.append(f"## Contexte du dossier\n{kb}")

    # 2. Mémos existants
    memos = sorted((case_dir/"analyse-juridique").glob("*.md"))
    parts.append(f"## Memos de recherche existants\n" + "\n".join(f"- {m.name}" for m in memos))

    # 3. Plan déterministe (si fourni)
    parts.append(format_research_plan_for_prompt(config.research_plan))

    return "\n\n".join(parts)
```

### 5.6 Output

`analyse-juridique/<filename>.md` via `WriteFileTool` (général). Auto-versioning : `-v2`, `-v3` si déjà existant. **Append-only** (le tool refuse l'écrasement dans `analyse-juridique/`).

Side-effect : `update_knowledge_from_research(content)` fire-and-forget → enrichit `legal` et `strategy` du knowledge.

---

## 6. Agent AC Research — actions collectives

### 6.1 Configuration

(`src/agents/ac_research.py:150-203`, profil `profiles.py:78-91`)

```python
AgentConfig(
    agent_type="ac-research",
    system_prompt_static=_AC_SYSTEM_PROMPT,  # plus court que research
    system_prompt_dynamic=lambda: _build_ac_research_context(config),
    tools={
        "search_ac_registry": SearchAcRegistryTool(),
        "list_dossier_documents": ListDossierDocumentsTool(),
        "get_ac_document": GetAcDocumentTool(),
        "query_ac_dossiers": QueryAcDossiersTool(),
        "search_avocats": SearchAvocatsTool(),
        "write_file": WriteAcMemoTool(),     # nom identique pour réutiliser engine
        "read_artifact": ReadAcArtifactTool(),
    },
    max_iterations=15,
    window_size=8,
)
```

### 6.2 Différences clés avec Research

| Aspect | Research | AC Research |
|--------|----------|-------------|
| Corpus | jurisprudence_chunks + jurisprudence_decisions | ac_chunks + ac_decisions + ac_dossiers + ac_avocats |
| Outils | 11 légaux | 7 spécifiques AC |
| Court boost | oui (CSC ×1.30, QCCA ×1.25) | non |
| Treatment penalty | oui (REVERSED ×0.3) | non |
| Doctrine pré-chargée | non (`search_private_legal_knowledge` à la demande) | `ac_doctrine_knowledge.md` injecté dans le prompt |
| Sortie | `analyse-juridique/` | `analyse-juridique-ac/` |
| Silence rule | 1 message final | 3 moments texte (annonce + entre outils=vide + final) |
| Tool `write_file` | `WriteFileTool` (général) | `WriteAcMemoTool` (AC-spécifique avec storage backend abstraction) |

### 6.3 Outils AC

| Outil | Fonction |
|-------|----------|
| `search_ac_registry` | Recherche sémantique dans le corpus AC (zembed-1 + zerank-2) |
| `list_dossier_documents` | Liste les docs d'un dossier (no_dossier) |
| `get_ac_document` | Lit un document complet (cap 6000 chars) |
| `query_ac_dossiers` | Filtre/agrège les dossiers par sujet/district/étape (group_by possible) |
| `search_avocats` | Cherche les avocats par nom/cabinet/partie |
| `write_file` (`WriteAcMemoTool`) | Écrit un mémo dans `analyse-juridique-ac/` |
| `read_artifact` | Lit un mémo AC |

### 6.4 Storage backend

`WriteAcMemoTool` utilise une `StorageBackend` abstraction (`src/storage/`) :
- **Dev** : `FilesystemBackend` → `cases/<id>/analyse-juridique-ac/`
- **Prod** : `AzureBlobBackend` → blobs Azure (multi-tenant)

`ensure_within_tenant()` vérifie l'isolation des tenants.

---

## 7. Agent Redaction — rédaction de documents

### 7.1 Configuration

(`src/agents/redaction.py:336-377`, profil `profiles.py:92-102`)

```python
AgentConfig(
    agent_type="redaction",
    system_prompt_static=_SYSTEM_PROMPT_TEMPLATE.format(skill_content=...),
    system_prompt_dynamic=lambda: _build_redaction_context(config),
    tools={
        "list_files": ListFilesTool(),
        "read_file": ReadFileTool(),
        "write_file": WriteFileTool(),
        "edit_file": EditFileTool(),
        "search_files": SearchFilesTool(),
        "get_decision_text": GetDecisionTextTool(),  # SEULE exception : peut lire decision
    },
    max_iterations=12,            # strict, fixe
    max_tokens=16_384,
    window_size=12,
    max_total_tokens=30_000,
    # thinking_enabled=False (jamais)
)
```

**Pas d'outil `search_*`** — Redaction utilise **uniquement les mémos déjà écrits** dans `analyse-juridique/`. C'est un compositeur, pas un chercheur.

### 7.2 Le registre `DOCUMENT_TYPES`

(`src/agents/redaction.py:35-126`) — 17-18 types de documents :

| ID | Catégorie | Output path |
|----|-----------|-------------|
| `demande-introductive` | Procédure | `procedures/demande-introductive.html` |
| `mise-en-demeure` | Lettre | `redaction/mise-en-demeure.html` |
| `demande-irrecevabilite` | Procédure | `procedures/demande-irrecevabilite.html` |
| `avis-juridique` | Lettre | `redaction/avis-juridique.html` |
| `injonction` | Procédure | `procedures/demande-injonction.html` |
| `ordonnance-sauvegarde` | Procédure | `procedures/ordonnance-sauvegarde.html` |
| `defense` | Procédure | `procedures/defense.html` |
| `defense-action-collective` | Procédure | `procedures/defense-action-collective.html` |
| `pourvoi-controle-judiciaire` | Procédure | `procedures/pourvoi-controle-judiciaire.html` |
| `offre-de-reglement` | Lettre | `redaction/offre-de-reglement.html` |
| `declaration-abus` | Procédure | `procedures/declaration-abus.html` |
| `expose-defense` | Procédure | `procedures/expose-defense.html` |
| `plan-argumentation` | Procédure | `procedures/plan-argumentation.html` |
| `plaidoirie` | Procédure | `procedures/plaidoirie.html` |
| `nda` | Lettre | `redaction/nda.html` |
| `avis-fin-emploi` | Lettre | `redaction/avis-fin-emploi.html` |
| `appel-en-garantie` | Procédure | `procedures/appel-en-garantie.html` |
| `declaration-sous-serment` | Procédure | `procedures/declaration-sous-serment.html` |

Chaque type est mappé vers un répertoire `aston/skills/<skill_name>/` qui contient :
- `SKILL.md` — instructions de drafting (8-15 KB typique)
- `reference.docx` (optionnel) — template Word pour conversion pandoc

### 7.3 Injection du SKILL.md dans le prompt

Au moment de la création du `AgentConfig` (`src/services/redaction_service.py:209-218`) :

```python
skill_path = self._skills_dir / skill_name / "SKILL.md"
skill_content = skill_path.read_text(encoding="utf-8")
system_prompt = _SYSTEM_PROMPT_TEMPLATE.replace("{skill_content}", skill_content)
```

Le `SKILL.md` est **baked-in** dans le `system_prompt_static`. Il bénéficie du prompt caching standard (TTL 5 min) car il est dans le bloc final cache_control. **Taille typique** : 4 000-6 000 tokens.

### 7.4 reference.docx — export DOCX

(`src/services/artifact_service.py:248-328`)

Quand l'utilisateur exporte l'artefact, le service :

1. Sélectionne le `reference.docx` (cascade) :
   - `/skills/<skill_name>/reference.docx` (exact match)
   - Sinon `/skills/demande-introductive/reference.docx` (fallback procédure)
   - Sinon `/skills/mise-en-demeure/reference.docx` (fallback lettre)
   - Sinon `/skills/reference.docx` (global)
2. Convertit avec pandoc :
   ```bash
   pandoc file.html -o file.docx --reference-doc /path/reference.docx -Mtitle=
   ```
3. Le DOCX préserve marges, polices, en-têtes du cabinet.

### 7.5 Single-pass garanti

- `max_iterations=12` strict
- Prompt : "Appelez `write_file` ou `edit_file` tôt, au plus tard à l'itération 6"
- Prompt : "Un brouillon imparfait avec des [CROCHETS] bat un brouillon jamais écrit"
- Force-write nudge si 3+ outils non-write consécutifs (`engine/loop.py:169-199`)
- Iteration warning à `turn_count >= max-2` : "Il vous reste 1 itération. Arrêtez la recherche, finalisez maintenant"

### 7.6 Streaming HTML progressif

**Événements émis** par l'engine (`loop.py:540-555`) :

| Event | Quand |
|-------|-------|
| `artifact_streaming_start` | Le modèle commence à streamer le JSON du tool_use `write_file` (détection du pattern `"content":"`) |
| `artifact_delta` | Chunks HTML extraits du buffer JSON pendant le streaming |
| `artifact_streaming_done` | `content_block_stop` reçu pour le tool_use |
| `artifact_created` | Tool exécuté avec succès, fichier écrit |
| `artifact_updated` | `edit_file` exécuté |

Le frontend (`use-redaction.ts`) accumule `streamingHtml += data.content` et le binde à TinyMCE, donnant un rendu live du document en cours de rédaction.

### 7.7 Lettres vs procédures

| Aspect | Lettre (`mise-en-demeure`, `avis-juridique`, `nda`, `offre-de-reglement`, `avis-fin-emploi`) | Procédure (autres) |
|--------|---------------------------------------------------------------------------------------------|-------------------|
| En-tête | `<p>` avec mode service + date + adresse destinataire | `<table>` CANADA / QUÉBEC / DISTRICT / Parties / Titre |
| Numérotation | Pas de paragraphes numérotés | `<ol><li>` pour faits, moyens |
| Sections | `<p>` + `<strong>` + `<hr/>` | `<h2>` Les parties / Les faits / Les moyens |
| Formule d'ouverture | "Monsieur, Nous demeurons les procureurs..." | "AU SOUTIEN DE SA DEMANDE..., LA DEMANDERESSE EXPOSE..." |
| Clôture | "VEUILLEZ AGIR EN CONSÉQUENCE" + signature | "POUR CES MOTIFS, PLAISE À LA COUR :" + conclusions numérotées |

**La structure exacte est dans le SKILL.md** — le code Aston n'a pas de logique conditionnelle "letter vs procedure". L'agent applique le SKILL.

### 7.8 Contexte dynamique

(`src/agents/redaction.py:216-305`)

```python
async def _build_redaction_context(config) -> str:
    parts = []
    # 1. Knowledge (identity + facts + legal + strategy) ; fallback raw resume-des-faits.md
    parts.append(f"## Contexte: Résumé des faits\n\n{kb_or_raw}")

    # 2. TOUS les mémos de analyse-juridique/, capés à 6000 tokens chacun
    parts.append(f"## Mémos de recherche existants ({n})\n\n{joined_memos}")

    # 3. Statut du brouillon (existe ou non, tronqué à 10K chars)
    parts.append(f"## Brouillon actuel (`{output_path}`)\n{draft_text}")

    return "\n\n".join(parts)
```

**Important** : Redaction reçoit **tout le knowledge** (4 sections sur 4) + **tous les mémos** + **son draft actuel s'il existe**. C'est l'agent avec le contexte le plus riche.

---

## 8. Sous-système d'outils

### 8.1 Tool ABC

(`src/tools/base.py:1-23`)

```python
class Tool(ABC):
    name: str = ""              # ex: "search_caselaw"
    description: str = ""       # passé à Anthropic
    concurrent: bool = True     # paralleisable ?
    input_schema: dict = {}     # JSON Schema Anthropic

    @abstractmethod
    async def run(self, input_data: dict, context: dict) -> str:
        ...

    def to_anthropic_schema(self) -> dict:
        return {"name": self.name, "description": self.description, "input_schema": self.input_schema}
```

`context` contient `case_dir`, `case_id`, `tenant_id`, `user_id`, `session_id`, `query_cache`, `allowed_courts`, `storage_backend`, etc.

### 8.2 Executor concurrent

(`src/tools/executor.py:17-71`)

- Sémaphore global : **10 outils max en parallèle**
- Groupe les outils consécutifs par `concurrent` flag → batch
- Batch concurrent : `asyncio.gather(*tasks)` sous sémaphore
- Batch serial : exécution séquentielle si `concurrent=False`
- Résultats retournés dans l'ordre d'origine

### 8.3 Erreurs enrichies

(`src/tools/errors.py:1-66`)

| Exception | Enrichissement |
|-----------|----------------|
| `FileNotFoundError` | Liste les fichiers du parent + suggestion `list_files()` |
| `ValueError` (avec "old_text") | Suggestion `read_file()` d'abord pour voir le contenu exact |
| `PermissionError` | "Seuls les fichiers du dossier courant sont accessibles" |
| Autres | Format simple `{type}: {error}` |

Les erreurs sont passées au modèle via `tool_result` blocks avec `is_error=True` + metadata.

### 8.4 Catalogue des outils

#### Generaux (`tools/general/`)

| Outil | Rôle |
|-------|------|
| `list_files` | Liste les fichiers du `case_dir` |
| `read_file` | Lit un fichier (case ou processed) |
| `write_file` | Écrit dans le case (sanitize HTML si `.html`, side-effect knowledge update) |
| `edit_file` | Edit chirurgical (exact match puis fuzzy whitespace) |
| `search_files` | Regex search dans `.md/.txt/.html/.json` |

#### Légaux (`tools/legal/`)

| Outil | I/O |
|-------|------|
| `search_caselaw` | `query, k, search_type, court, date_from, date_to, domain, judge` → décisions formatées avec [N] |
| `search_caselaw_keyword` | `query, k, mode (phrase/all_terms/any_terms/article/citation_text), filtres` → mêmes résultats via FTS |
| `get_decision_text` | `source_file, question, k=8, full=False` → header + paragraphes pertinents (cap 6000 chars) |
| `find_decision_by_title` | `title, limit=10` → JSON `{results, count}` |
| `check_decision_status` | `neutral_citation` → traitement (REVERSED, FOLLOWED) + appeal chain |
| `search_private_legal_knowledge` | `query, k=3` → orientation interne (jamais cité dans le mémo) |
| `check_prescription` | `facts, claim_type` → délai + articles + point de départ (rules hardcodés) |
| `verify_citation` | `quote, citation` → VÉRIFIÉ / PARTIEL / ÉCHEC |
| `validate_document` | `content, doc_type` → rapport sections présentes + placeholders |
| `cross_reference_parties` | `name` → mentions du nom dans les fichiers du case |

#### Actions collectives (`tools/ac/`)

| Outil | I/O |
|-------|------|
| `search_ac_registry` | `query, k, doc_type, etape, district` → résultats sémantiques |
| `list_dossier_documents` | `dossier_no` → métadonnées + liste de docs |
| `get_ac_document` | `source_file, char_start, char_end` → texte (cap 6000 chars) |
| `query_ac_dossiers` | `sujet, district, etape, parties, group_by` → liste OU agrégat |
| `search_avocats` | `nom, cabinet, partie` → liste avocats |
| `write_file` (`WriteAcMemoTool`) | `path (ignoré), content, title, filename` → écrit dans `analyse-juridique-ac/` |
| `read_artifact` | `path` → contenu UTF-8 |

---

## 9. Pipeline RAG

(`src/rag/`)

### 9.1 Doctrine (`search_private_legal_knowledge`)

(`src/rag/doctrine.py:48-123`)

```
Query
  ↓ embed (zembed-1, cached singleton _embed_cache)
  ↓ pgvector ANN (doctrine_chunks, ann_k = max(k×5, 15))
  ↓ ZeroEntropy rerank (zerank-2, top_n=k)
  ↓ format compact (concepts + articles, sans source visible)
```

**Règle critique** : la doctrine n'est jamais citée dans le mémo. Elle sert uniquement d'orientation interne (concepts, articles à vérifier).

### 9.2 Jurisprudence (`search_caselaw`)

(`src/rag/jurisprudence.py:1261-1279` pour `search_jurisprudence_query`)

```
Query
  ↓ embed (zembed-1, cached)
  ↓ pgvector ANN (jurisprudence_chunks, k×4 candidates)
     WHERE court IN allowed_courts AND date_range AND domain AND judge
  ↓ ZeroEntropy rerank (zerank-2, top_n=k)
  ↓ Court authority boost
     CSC/SCC × 1.30
     QCCA   × 1.25
     QCCS   × 1.10
  ↓ Treatment penalty (citation_edges)
     REVERSED          × 0.3
     PARTIALLY_REVERSED × 0.7
  ↓ Deduplicate to decisions (keep highest scoring chunk per source_file)
  ↓ Format avec [N] + warnings traitement
```

Trois autres modes :
- `legislation_cited` — ANN sur l'article cité
- `citateur` — décisions citant une autorité donnée (via `citation_edges`)
- `definition` — définition de notion juridique

### 9.3 `get_decision_text` — retrieval paragraphe-level

(`jurisprudence.py:1621-1755`)

Quand l'agent demande à lire une décision :

1. Resolve `source_file` depuis citation
2. Charger texte complet (`jurisprudence_decisions` ou disque)
3. Parser paragraphes natifs `[N]` (skip indented/quoted)
4. **Embed batch** des paragraphes (pas de cache, sinon prohibitif)
5. Cosine similarity vs question
6. Top 20 par cosine
7. Rerank top 20 avec zerank-2 → top k
8. Expand context ± 1 paragraphe
9. Render en ordre lecteur avec `[...]` pour gaps
10. Hard cap **6000 chars**

Fallbacks : pas de paragraphes natifs → premiers 3000 chars. Embed fail → `extract_decision_excerpt` avec NOTE.

### 9.4 Cache RAG

(`src/rag/cache.py`)

- `_embed_cache: dict[str, list[float]]` — embeddings pgvector cachés en mémoire process
- `QueryCache` — résultats de recherche cachés (TTL 600s, clé MD5 sur `tool:query:k:extra`)
- `_treatment_cache: dict[str, dict]` — traitement de décisions, invalidé au restart

### 9.5 AC search

(`src/rag/ac_search.py`)

Pipeline identique à la jurisprudence (zembed-1 + zerank-2) **sans** court boost ni treatment penalty. Backend : `ac_chunks` (pgvector) + `ac_decisions` (texte complet) + `ac_dossiers` + `ac_avocats` (relationnel).

---

## 10. Pipeline de gestion de contexte

(`src/context/`)

Exécuté **avant chaque appel API** (`loop.py:391-419`).

### 10.1 `snip_duplicate_reads`

(`src/context/snip.py:19-114`)

- Cible : `read_file`, `get_decision_text`
- Clé : `read_file:{path}` ou `get_decision_text:{source}`
- Action : scan reverse, garde **uniquement le dernier** `(tool_use, tool_result)` pour chaque clé. Tous les autres sont supprimés.
- Retour : nouvelle liste de messages (pas de mutation in-place)

### 10.2 `compact_tool_results`

(`src/context/compaction.py:48`)

- `MAX_RESULT_CHARS = 800`
- `PRESERVE_LAST_N = 2` (résultats les plus récents intacts)
- Stratégie par outil :
  - `search_caselaw*`, `search_doctrine` → garde citations (regex `\d{4}\s+[A-Z]{2,6}\s+\d+`), scores, première phrase
  - `get_decision_text` → header (15 lignes) + numéros de paragraphes (max 30 lignes)
  - autres → 60% début + 30% fin + `[...]`

### 10.3 `estimate_tokens`

Heuristique simple : **4 caractères = 1 token**. Pas de tiktoken. Permet d'estimer si on dépasse `max_total_tokens`.

### 10.4 `collapse_old_messages`

(`src/context/collapse.py:11-36`)

```python
if len(messages) <= keep_recent:
    return messages

recent = messages[-keep_recent:]
return [summary_message] + recent if summary_message else recent
```

### 10.5 `structured_summarize`

(`src/context/summarizer.py`)

Modèle : `claude-haiku-4-5`. Format de sortie en **9 sections** :

1. MANDAT DU CLIENT
2. FAITS ETABLIS
3. RECHERCHE EFFECTUEE
4. DOCUMENTS REDIGES
5. DECISIONS LUES
6. ERREURS ET CORRECTIONS
7. INSTRUCTIONS DE L'UTILISATEUR (verbatim)
8. TRAVAIL EN COURS
9. PROCHAINE ETAPE

Retourne un `{"role": "user", "content": "[Résumé structuré...]\n\n{summary}"}`.

### 10.6 `restore_critical_context`

(`src/context/restore.py:28-82`)

Réinjecte trois catégories après collapse :

1. **Knowledge base** (si `knowledge_renderer` fourni) → `[Base de connaissances du dossier]\n\n{kb}`
2. **Artefacts récents** — top 3 fichiers récents dans `faits/`, `analyse-juridique/`, `redaction/`, `procedures/` (extensions `.md`, `.html`, `.txt`)
3. **Skill content** (redaction seulement) → `[Instructions de rédaction]\n\n{skill_content}`

### 10.7 `validate_and_repair`

(`src/persistence/validation.py:10-43`)

Garantit les invariants Anthropic message format :

- Alternance stricte `user/assistant/user/...`
- Pour deux `user` consécutifs → injecter `{"role": "assistant", "content": "[Suite.]"}`
- Pour deux `assistant` consécutifs → injecter `{"role": "user", "content": "[Suite de la conversation.]"}`
- `tool_use` orphelin (sans `tool_result` au tour suivant) → strip
- `tool_result` orphelin (sans `tool_use` au tour précédent) → strip
- Messages devenus vides après strip → supprimés
- Premier message doit être `user`

---

## 11. Vérification post-agent

(`src/verification/`)

### 11.1 Quand

Après `stop_reason == "end_turn"` avec texte non-vide, si `config.verification_checklist` activé (`loop.py:1018-1038`).

### 11.2 Checklists

(`src/verification/checklists.py:1-35`)

| Agent | Checks |
|-------|--------|
| **Facts** | dates_sourced, parties_consistent, no_unsourced_facts, chronology_ordered |
| **Research** | citation_format, quotes_verified, principles_attributed, question_answered, no_fabricated_citations |
| **Redaction** | sections_present, parties_match, dates_consistent, citations_sourced, html_valid, no_placeholders |

### 11.3 Verifier

Modèle : Haiku, prompt antagoniste qui force le détail. Retourne :

```json
{
    "verdict": "PASSE | ECHEC | PARTIEL",
    "score": "N/M",
    "checks": [{"check": "...", "status": "...", "detail": "...", "severity": "low|medium|high"}],
    "auto_fixable": true|false
}
```

### 11.4 Auto-fix

(`src/verification/auto_fix.py`)

- `MAX_FIX_CYCLES = 2` — limit auto-fix tentatives
- Skip si `auto_fixable == False`
- Skip si **n'importe quel** check échoué a `severity == "high"`
- Sinon : `build_fix_instructions(verdict)` → message `user` qui liste chaque problème + suggestion `edit_file`
- `state.transition = "verification_fix"`, `turn_count++`, `continue`

---

## 12. Knowledge base — le mécanisme de handoff

**C'est le cœur du handoff entre agents.** Au lieu de partager des fichiers bruts (~9 100 tokens), Aston compresse l'état du dossier dans un JSON structuré (~900 tokens) qui est rendu en markdown tailorisé pour chaque agent.

### 12.1 Schéma de `knowledge.json`

Stocké en JSONB dans `cases.knowledge` (Postgres) :

```json
{
    "identity": {
        "parties": [{"name", "role", "description"}],
        "nature": "...",
        "tribunal": "...",
        "prescription": {"type", "delai", "date_limite", "base"}
    },
    "facts": {
        "key_facts": [{"date", "assertion", "source", "disputed"}],
        "disputed_facts": [...]
    },
    "evidence": {
        "inventory": [{"piece", "file", "description", "probative_value"}],
        "gaps": [...]
    },
    "legal": {
        "framework": "2-3 phrases",
        "applicable_articles": [...],
        "holdings": [{"principle", "source", "relevance"}],
        "key_decisions": [...],
        "adverse_authority": [...]
    },
    "strategy": {
        "theory": "...",
        "strengths": [...],
        "weaknesses": [...],
        "recommended_approach": "...",
        "open_questions": [...]
    },
    "_meta": {"version", "updated_by", "last_updated"},
    "warnings": [{"severity", "message"}]
}
```

### 12.2 `update_knowledge_from_facts()`

(`src/knowledge/knowledge_base.py:147-212`)

**Déclenché** : après `write_file("faits/resume-des-faits.md")` ou `write_file("faits/chronologie.md")` via fire-and-forget `asyncio.create_task` (`src/tools/general/write_file.py:97-120`).

**Flow** :

1. Appel Haiku (profil `knowledge_facts`, max_tokens=4 000)
2. Prompt : "Tu es un extracteur de données juridiques" → retourne JSON avec `identity`, `facts` (max 10 faits), `evidence`
3. Parsing robuste (réparation trailing commas, fermeture brackets, fallback truncation)
4. Retry exponentiel (1s, 2s, 4s, max 3 tentatives)
5. UPDATE `cases.knowledge` SET `identity`, `facts`, `evidence`, `_meta.updated_by="facts"`, `_meta.last_updated=ISO`
6. **Side-effect imbriqué** : `asyncio.create_task(generate_research_suggestions(...))` → 1-3 questions de recherche essentielles stockées dans `research_suggestions`

### 12.3 `update_knowledge_from_research()`

(`src/knowledge/knowledge_base.py:215-260`)

**Déclenché** : après `write_file("analyse-juridique/<memo>.md")` ou `write_memo` AC.

**Flow** : identique à facts mais extrait `legal` + `strategy`. Met à jour `_meta.updated_by="research"`.

### 12.4 `render_knowledge_for_agent()`

(`src/knowledge/knowledge_base.py:267-379`)

```python
AGENT_CONTEXT_PROFILES = {
    "research":  ["identity", "facts"],
    "redaction": ["identity", "facts", "legal", "strategy"],
    "facts":     ["identity"],
}
```

Retourne un markdown formaté (~900 tokens) avec sections :
- `### Parties` (avec rôles)
- `### Nature du litige`
- `Tribunal compétent`, `Prescription`
- `### Faits clés` (avec dates, [CONTESTE] flag, sources)
- `### Faits contestés`
- `### Inventaire de preuve`, `### Lacunes`
- `### Cadre juridique`, `### Articles applicables`, `### Constats juridiques`, `### Autorité défavorable`
- `### Théorie de la cause`, `### Approche recommandée`, `### Risques`, `### Questions ouvertes`
- `### Avertissements`
- `### Documents complets (read_artifact si besoin)` — pointeurs vers les artefacts

### 12.5 Injection dans le system prompt

L'engine appelle `await config.system_prompt_dynamic()` à chaque tour (`loop.py:331-341`). Pour Research et Redaction, ce callable construit le contexte avec `render_knowledge_for_agent()` au sommet.

**Compression** : ~10× (900 tokens vs 9 100 tokens raw).

### 12.6 Flow de handoff

```
T0   Facts agent : write_file("faits/resume-des-faits.md")
T0+ε asyncio.create_task(update_knowledge_from_facts)
       ↓ Haiku extrait identity + facts + evidence
       ↓ UPDATE cases.knowledge
       ↓ asyncio.create_task(generate_research_suggestions)
         ↓ 1-3 questions stockées dans research_suggestions

T1   Research agent (utilisateur lance une question)
       ↓ _build_research_context()
       ↓ render_knowledge_for_agent("research") lit identity + facts
       ↓ injection dans system prompt dynamic
T1+  search_caselaw, get_decision_text, write_file
T1+ε asyncio.create_task(update_knowledge_from_research)
       ↓ Haiku extrait legal + strategy
       ↓ UPDATE cases.knowledge

T2   Redaction agent (utilisateur lance un document)
       ↓ _build_redaction_context()
       ↓ render_knowledge_for_agent("redaction") lit les 4 sections
       ↓ + tous les mémos dans analyse-juridique/ (capés à 6000 tok chacun)
       ↓ + draft actuel s'il existe
       ↓ injection dans system prompt dynamic
T2+  read_file, write_file (HTML), edit_file
       (terminal — pas de knowledge update)
```

**Garantie** : pas de race condition. Les knowledge updates sont fire-and-forget mais l'agent suivant lit le knowledge **au début de sa session** (au moment du build du contexte dynamique). Postgres JSONB garantit l'atomicité.

---

## 13. Streaming SSE

### 13.1 Event registry par agent

(`src/streaming/events.py`)

| Agent | Events émis |
|-------|-------------|
| **Facts** | `message_delta`, `message_commit`, `file_read`, `artifact_created`, `artifact_updated`, `done`, `error` |
| **Research** | `message_delta`, `message_commit`, `phase_start`, `phase_complete`, `source_found`, `artifact_created`, `research_plan`, `research_coverage`, `research_candidates`, `research_quality`, `tool_start`, `tool_end`, `usage`, `done`, `error` |
| **AC Research** | mêmes que Research (sauf phase_start/complete pas toujours émis) |
| **Redaction** | `message_delta`, `message_commit`, `message`, `artifact_created`, `artifact_updated`, `artifact_delta`, `artifact_streaming_start`, `artifact_streaming_done`, `done`, `error` |

### 13.2 Backend : task_bus

(`src/streaming/task_bus.py`)

Architecture **publisher/subscriber via Postgres LISTEN/NOTIFY** :

1. Engine émet `{"type": "message_delta", "data": {"content": "..."}}` via `await publish(task_id, event)`
2. `INSERT INTO task_events (task_id, event_type, data) VALUES (...)`
3. `SELECT pg_notify(channel, '')` réveille les subscribers
4. Events persistent **2h** (auto-cleanup via `start_retention_task()`)
5. **Reconnectable** : `Last-Event-ID` header → reprise depuis l'ID donné

### 13.3 Format SSE

Avec ID (events persistés) :
```
id: 42
event: message_delta
data: {"content": "..."}

```

Sans ID (events transitoires comme `done`/`error`) :
```
event: done
data: {}

```

### 13.4 Frontend SSE consumer

`AuthenticatedEventStream` (`frontend/src/lib/api.ts:32-141`) :
- Custom class (simule EventSource)
- Supporte header `Last-Event-ID`
- Reconnexion exponentielle (max 5 tentatives, backoff cap 8s)
- Ferme à `done` ou `error`

---

## 14. Persistance

### 14.1 PostgreSQL

| Table | Rôle |
|-------|------|
| `cases` | Dossiers (id, nom, partie, signals, delais, **knowledge JSONB**) |
| `messages` | Historique conversationnel (session_id, role, content JSONB, compacted bool) |
| `sessions` | Sessions d'agents (case_id, agent_type, doc_type, title, tenant_id) |
| `research_suggestions` | Questions auto-générées (case_id, question, rationale, status) |
| `task_registry` | Tasks live (task_id, agent_type, session_id, case_id) |
| `task_events` | Events SSE (id BIGSERIAL, task_id, event_type, data JSONB) |
| `users` | Utilisateurs (multi-tenant) |

### 14.2 Native Anthropic content blocks

`messages.content` (JSONB) stocke soit une string simple soit un array de blocks Anthropic :

```json
[
    {"type": "text", "text": "..."},
    {"type": "tool_use", "id": "call-abc", "name": "search_caselaw", "input": {...}},
    {"type": "tool_result", "tool_use_id": "call-abc", "content": "...", "is_error": false},
    {"type": "thinking", "thinking": "..."}
]
```

### 14.3 Compaction = soft delete

(`src/persistence/store.py:177-184`)

```sql
UPDATE messages SET compacted = TRUE WHERE id = ANY($1::text[])
```

`get_messages(session_id, include_compacted=False)` filtre `compacted = FALSE` par défaut. **Aucun hard-delete**, audit trail complet préservé.

### 14.4 Pools Postgres

(`src/app_db.py`, `src/corpus_db.py`)

- `app_database_url` : pool obligatoire (users, messages, sessions, tasks, cases, knowledge)
- `corpus_database_url` : pool optionnel read-only (jurisprudence, doctrine, AC chunks)
- Codec JSONB personnalisé pour round-trip dict/list

---

## 15. Surface API

(`src/api.py`) — toutes routes sous `/api/v1/`.

### 15.1 Pattern session + start + stream

Pour Research, AC Research, Redaction :

| Endpoint | Méthode | Rôle |
|----------|---------|------|
| `POST /cases/{id}/{agent}/sessions` | Crée une session persistée (génère `session_id`) |
| `POST /cases/{id}/{agent}` | Lance l'exécution (génère `task_id`, retourne immédiatement) |
| `GET /cases/{id}/{agent}/{task_id}` | SSE stream des events |

**Pourquoi 3 endpoints ?**

- **Session** = scope de persistance (historique conversationnel)
- **Task** = scope d'exécution (events live, timeout, cancellation)
- **Stream** = consumption (reconnectable, stateless, peut être servi par n'importe quel replica)

`task_registry.session_id → messages.session_id` lie les deux.

Facts est légèrement plus simple : un seul `POST /facts` (la session est implicite par case_id).

### 15.2 Endpoints complets

#### Cases
- `POST /cases` — créer
- `GET /cases` — lister
- `GET /cases/{id}` — lire
- `PATCH /cases/{id}` — mettre à jour
- `DELETE /cases/{id}` — supprimer

#### Files
- `POST /cases/{id}/files` — uploader (multipart, déclenche file_processor)
- `GET /cases/{id}/files` — lister
- `GET /cases/{id}/files/raw/{filename:path}` — télécharger
- `DELETE /cases/{id}/files/{filename}` — supprimer

#### Artifacts
- `GET /cases/{id}/artifacts` — lister
- `GET /cases/{id}/artifacts/{path:path}` — lire
- `PUT /cases/{id}/artifacts/{path:path}` — mettre à jour
- `PATCH /cases/{id}/artifacts/{path:path}` — renommer
- `DELETE /cases/{id}/artifacts/{path:path}` — supprimer
- `GET /cases/{id}/artifacts/{path:path}/export` — exporter DOCX (pandoc)

#### Facts
- `POST /cases/{id}/facts` → `{task_id}`
- `GET /cases/{id}/facts/{task_id}` → SSE

#### Research
- `POST /cases/{id}/research/sessions` → `{session_id, task_id, title}`
- `GET /cases/{id}/research/sessions` → `ResearchSession[]`
- `DELETE /cases/{id}/research/sessions/{session_id}`
- `POST /cases/{id}/research` → `{task_id}` (continuation)
- `GET /cases/{id}/research/{task_id}` → SSE
- `GET /cases/{id}/research/suggestions` → `ResearchSuggestion[]`
- `POST /cases/{id}/research/suggestions/{suggestion_id}/launch` → `{session_id, task_id, ...}`

#### AC Research
- `POST /cases/{id}/ac-research/sessions`
- `GET /cases/{id}/ac-research/sessions`
- `DELETE /cases/{id}/ac-research/sessions/{session_id}`
- `POST /cases/{id}/ac-research`
- `GET /cases/{id}/ac-research/{task_id}` → SSE

#### Redaction
- `POST /cases/{id}/redaction/sessions`
- `GET /cases/{id}/redaction/sessions`
- `DELETE /cases/{id}/redaction/sessions/{session_id}`
- `POST /cases/{id}/redaction/{doc_type}` → `{task_id}`
- `GET /cases/{id}/redaction/{doc_type}/{task_id}` → SSE

#### Conversations
- `GET /cases/{id}/conversations/{agent_type}` → `StoredMessage[]` (replay)

---

## 16. Hooks frontend

(`frontend/src/hooks/`)

### 16.1 `use-research.ts`

State :
- `messages`, `isRunning`
- `progress: ResearchProgress` — phases, sources, tools, currentPhase, usage live, plan, coverage, quality, candidates

Events handled :
```
phase_start, phase_complete, source_found, evaluation, iteration,
research_plan, research_coverage, research_candidates, research_quality,
message, message_delta, message_commit,
artifact_created, artifact_updated,
tool_start, tool_end, usage,
done, error
```

Rendu :
- **Phase progress bar** (5 phases : analyze/search/reading/writing/summary)
- **Decision cards** depuis `research_candidates` (citation, court, parties, paragraphs)
- **Activity journal** (`tool_start` → row "running", `tool_end` → "done"/"error" avec durée)
- **Token meter** depuis `usage`

### 16.2 `use-redaction.ts`

State :
- `streamingHtml` — accumulation live des `artifact_delta`
- `lastEditText`, `writingStatus`

Events handled :
```
message_delta, message_commit, message,
source_found,
artifact_created, artifact_updated,
artifact_delta, artifact_streaming_start, artifact_streaming_done,
done, error
```

Rendu progressif :
- `artifact_streaming_start` → `streamingHtml = ""`
- `artifact_delta` (×N) → `streamingHtml += data.content`
- `artifact_streaming_done` → finalize
- `streamingHtml` est binde à TinyMCE `.setContent()` pour rendu live HTML

### 16.3 `use-facts.ts`

State : messages simples + `writingStatus`. Pas de progress UI.

Events : `message_delta`, `message_commit`, `message`, `source_found`, `artifact_created`, `done`, `error`.

### 16.4 `use-ac-research.ts`

Réutilise `ResearchProgress`. Persistance localStorage : `aston:ac-research-progress:{sessionId}` (sauvegardé à `done`/`error`, rechargé au mount).

### 16.5 `use-streaming-text.ts`

Typewriter effect (60 FPS via `requestAnimationFrame`, `charsPerFrame=2`) pour révéler progressivement les SSE deltas accumulés.

### 16.6 Active task persistence

(`frontend/src/lib/active-tasks.ts`)

`sessionStorage` stocke `{kind, caseId, sessionId, taskId, userMessage, startedAt}`. Permet de reprendre un stream après reload du navigateur.

---

## 17. Flow complet d'un dossier

Voici le scénario type, de l'upload du premier document à la rédaction d'une procédure :

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. UPLOAD                                                       │
│    POST /cases (créer dossier)                                  │
│    POST /cases/{id}/files × N (PDF, DOCX, images)               │
│      → file_processor : PyMuPDF / Tesseract / python-docx      │
│      → processed/*.md écrits dans storage                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. FACTS AGENT                                                  │
│    POST /cases/{id}/facts                                       │
│    SSE : list_files → read_file × N → write_file (resume)      │
│      → fire-and-forget update_knowledge_from_facts              │
│        → Haiku extrait identity + facts + evidence              │
│        → UPDATE cases.knowledge                                 │
│        → fire-and-forget generate_research_suggestions          │
│          → 1-3 questions dans research_suggestions              │
│    Frontend : artifact_created → render le résumé              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. RESEARCH AGENT                                               │
│    GET /research/suggestions → liste les questions auto-générées│
│    POST /research/sessions {question}                           │
│    POST /research → {task_id}                                   │
│    GET /research/{task_id} → SSE                                │
│                                                                 │
│    Engine :                                                     │
│      _build_research_context()                                  │
│        → render_knowledge_for_agent("research")                 │
│           = identity + facts (~500 tok)                         │
│        → liste mémos existants                                  │
│        → plan déterministe (si fourni)                          │
│      → injection dans system prompt dynamic                     │
│                                                                 │
│    Boucle (12-28 iter selon effort) :                           │
│      analyze → search_caselaw / search_caselaw_keyword          │
│      → get_decision_text × 3-5                                  │
│      → write_file("analyse-juridique/<memo>.md")                │
│        → fire-and-forget update_knowledge_from_research         │
│          → Haiku extrait legal + strategy                       │
│          → UPDATE cases.knowledge                               │
│      → message final 2-3 phrases                                │
│                                                                 │
│    Frontend : phase progress + decision cards + journal        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. (optionnel) AC RESEARCH AGENT                                │
│    POST /ac-research/sessions {question}                        │
│    POST /ac-research → {task_id}                                │
│    GET /ac-research/{task_id} → SSE                             │
│                                                                 │
│    Boucle (15 iter) :                                           │
│      search_ac_registry / list_dossier_documents /              │
│      get_ac_document / query_ac_dossiers / search_avocats       │
│      → write_file("analyse-juridique-ac/<memo>.md")             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. REDACTION AGENT                                              │
│    POST /redaction/sessions {doc_type, title}                   │
│    POST /redaction/{doc_type} → {task_id}                       │
│    GET /redaction/{doc_type}/{task_id} → SSE                    │
│                                                                 │
│    Engine :                                                     │
│      _build_redaction_context()                                 │
│        → render_knowledge_for_agent("redaction")                │
│           = identity + facts + legal + strategy (~800 tok)      │
│        → TOUS les mémos analyse-juridique/ (cap 6000 tok chacun)│
│        → draft status (existe ou non)                           │
│      → SKILL.md du doc_type baked dans static prompt            │
│                                                                 │
│    Boucle (12 iter strict) :                                    │
│      read_file (mémos si stale) →                               │
│      write_file("procedures/<doc>.html")                        │
│        → SSE : artifact_streaming_start →                       │
│           artifact_delta × N (rendu live HTML dans TinyMCE) →   │
│           artifact_streaming_done →                             │
│           artifact_created                                      │
│      edit_file × 1-3 (corrections chirurgicales)                │
│      → message final                                            │
│                                                                 │
│    PAS de knowledge update (terminal)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. EXPORT                                                       │
│    GET /cases/{id}/artifacts/{path}/export                      │
│    → pandoc HTML → DOCX avec reference.docx (style cabinet)     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Annexes

### A. Conventions de nommage

- `agent_type` : "facts" | "research" | "ac-research" | "redaction"
- Output paths : sans slash initial, relatifs au case_dir
- Conversation key (persistance) : `session_id` pour Facts, `{agent_type}-{session_id}` pour les autres

### B. Variables d'environnement clés

| Var | Usage |
|-----|-------|
| `LLM_PROVIDER` | "anthropic" (seul supporté aujourd'hui) |
| `LLM_API_KEY` | Anthropic API |
| `LLM_MODEL` | défaut `claude-sonnet-4-6` |
| `APP_DATABASE_URL` | Postgres app (obligatoire) |
| `CORPUS_DATABASE_URL` | Postgres corpus (optionnel, read-only) |
| `ZEROENTROPY_API_KEY` | embeddings + reranking |
| `JURISPRUDENCE_DIR` | fallback markdown si DB absente |
| `AC_DIR`, `AC_DOSSIER_DB_PATH`, `AC_CHUNKS_TABLE` | activent AC Research |

### C. Fichiers critiques (référence rapide)

| Fichier | Rôle |
|---------|------|
| `src/engine/loop.py` | Boucle principale (~1300 lignes) |
| `src/engine/config.py` | Dataclass AgentConfig |
| `src/engine/state.py` | Dataclass AgentState |
| `src/agents/facts.py` | Config Facts |
| `src/agents/research.py` | Config Research + budgets effort + context builder |
| `src/agents/ac_research.py` | Config AC Research |
| `src/agents/redaction.py` | Config Redaction + DOCUMENT_TYPES + context builder |
| `src/agents/tone.py` | TONE_BLOCK partagé |
| `src/knowledge/knowledge_base.py` | Schéma + extracteurs Haiku + render_knowledge_for_agent |
| `src/knowledge/case_manager.py` | CRUD cases et knowledge |
| `src/services/redaction_service.py` | Charge SKILL.md depuis aston/skills/ |
| `src/services/artifact_service.py` | Export pandoc avec reference.docx |
| `src/rag/jurisprudence.py` | Pipeline RAG jurisprudence (court boost, treatment penalty, paragraph retrieval) |
| `src/rag/doctrine.py` | Pipeline RAG doctrine |
| `src/rag/ac_search.py` | Pipeline RAG AC |
| `src/streaming/events.py` | Registries d'events par agent |
| `src/streaming/task_bus.py` | Publisher/subscriber Postgres LISTEN/NOTIFY |
| `src/persistence/store.py` | Messages, sessions, research_suggestions |
| `src/persistence/validation.py` | validate_and_repair (alternance user/assistant, orphelins) |
| `src/api.py` | FastAPI app factory + tous endpoints |
| `frontend/src/hooks/use-research.ts` | Hook Research |
| `frontend/src/hooks/use-redaction.ts` | Hook Redaction |

### D. Forces de l'architecture

1. **Une seule boucle** pour 4 agents → cohérence de comportement, factorisation des fonctionnalités transversales (caching, recovery, compaction, anti-loop, continuation, sanitization)
2. **Knowledge base structurée** → handoff inter-agents en 900 tokens vs 9 100 raw (compression 10×)
3. **Async fire-and-forget** sur les knowledge updates → l'utilisateur ne voit jamais l'extraction Haiku
4. **SSE persistés en Postgres** → reconnectable, stateless, multi-replica
5. **Soft-delete via `compacted` flag** → audit trail complet
6. **3 endpoints (session/start/stream)** → séparation propre des responsabilités, idempotence, replay
7. **Tools concurrents** (≤ 10 sémaphore) → exploitation efficace du parallélisme RAG
8. **Pipeline RAG à 2 stages** (zembed-1 ANN + zerank-2 rerank) avec court boost et treatment penalty pour la jurisprudence

### E. Points de friction observables (non bloquants)

1. **Heuristique de comptage de tokens** (4 chars = 1 token) — peu précise pour le français accentué et le code, mais évite la dépendance à tiktoken
2. **`artifact_delta` partiellement implémenté** : `_try_progressive_stream` détecte le pattern `"content"` dans le buffer JSON mais l'extraction des chunks HTML n'est pas encore branchée sur les yields. Le rendu live TinyMCE dépend de cette implémentation côté frontend
3. **Les phases Research sont détectées par l'engine** depuis le nom de l'outil appelé, pas par le modèle. Si un agent appelle les outils dans un ordre non-canonique, les phases peuvent être confuses
4. **Knowledge updates fire-and-forget** sans feedback utilisateur : si l'extraction Haiku échoue silencieusement (après 3 retries), l'agent suivant verra un knowledge incomplet sans le savoir
5. **Pas de tiktoken** → estimation pessimiste qui peut déclencher des compactions inutiles

---

**Fin du rapport.**
