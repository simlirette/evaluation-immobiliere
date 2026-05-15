# Spec — Batch 3 : AMU agent + PlanOrchestrator wiring + build-eval-skill

_Date : 2026-05-12 | Statut : Approuvé_

---

## Scope

**In scope :**
1. `build-eval-skill` — meta-skill Claude Code adapté du Jules build-legal-skill pour créer les backend skills eval-immo
2. `analyse-amu` skill + `analysis.md` (créé avec build-eval-skill)
3. `AGENTCONFIG-AMU-ANALYST-V0.yaml` — nouvel agent
4. Insertion `amu-analyst` dans le pipeline (step 2, renumber 1→6)
5. Wire `PlanOrchestrator.enrich_case()` dans `start_runtime()` (api.py)
6. `amu_analyse.md` ajouté à `_LLM_TEXT_FIELD_BY_ARTIFACT` pour enrichissement LLM

**Non-goals (remis à Batch 4) :**
- `redaction-lettre-mandat` skill
- `analyse-approche-fta` (DCF commercial complexe)
- Modification frontend (surfacer `mandat_type`)
- Logique AMU LLM avancée (V0 déterministe + enrichissement optionnel)

---

## Architecture et data flow

### Pipeline après Batch 3

```
data-facts(1) → amu-analyst(2) → comps-market(3) → valuation-draft(4) → compliance-qa(5) → redaction(6)
```

### Flux AMU

```
fiche_bien.json + type_bien/zone → [amu-analyst] → umpp_conclusion.json + amu_analyse.md
                                                            ↓
                                              comps-market lit umpp_conclusion.json
                                              redaction lit amu_analyse.md
```

---

## Interfaces / contrats

### `umpp_conclusion.json` (step amu-analyst, writes)

```json
{
  "dossier_id": "...",
  "step": "amu-analyst",
  "artifact": "umpp_conclusion.json",
  "source_fixture": "...",
  "umpp": {
    "usage_retenu": "residentiel_unifamilial",
    "usage_actuel": "residentiel_unifamilial",
    "conformite_zonage": true,
    "criteres": {
      "physiquement_possible": true,
      "legalement_permis": true,
      "financierement_faisable": true,
      "maximalement_productif": true
    },
    "conclusion": "L'usage actuel constitue le meilleur usage du bien.",
    "umpp_differe_usage_actuel": false
  },
  "confidence": 0.8
}
```

### `amu_analyse.md` (step amu-analyst, writes)

Narrative MD — 4 critères OEAQ documentés, conclusion UMPP, enrichi par LLM.

---

## Composants à créer/modifier

| Fichier | Action | Notes |
|---|---|---|
| `.claude/skills/build-eval-skill/SKILL.md` | Créer | Meta-skill adapté Jules → eval-immo |
| `backend/skills/analyse-amu/SKILL.md` | Créer | Via build-eval-skill |
| `backend/skills/analyse-amu/analysis.md` | Créer | Via build-eval-skill |
| `backend/integration/AGENTCONFIG-AMU-ANALYST-V0.yaml` | Créer | Nouvel agent |
| `backend/integration/PIPELINE-RUNTIME-ASTON-V0.yaml` | Modifier | Renumber 1→6, ajouter step 2 |
| `backend/engine/skills.py` | Modifier | Ajouter `amu-analyst` dans `DEFAULT_SKILLS_BY_AGENT` |
| `backend/engine/runtime.py` | Modifier | DEFAULT_STEPS + _artifact_payload + _LLM_TEXT_FIELD |
| `backend/api.py` | Modifier | `start_runtime()` — enrich_case wrappé try/except |
| `backend/tests/test_pure.py` | Modifier | Tests AMU déterministe |

---

## build-eval-skill vs Jules build-legal-skill

| Aspect | Jules | eval-immo |
|---|---|---|
| Output format | HTML (TinyMCE) | Markdown |
| Doctrine source | `/Users/emmanuel/PROJETS/...` | `docs/workflow-evaluateur-agree.md` + `backend/skills/*/analysis.md` |
| Reference format | `reference.html` | Pas nécessaire |
| Registration | `DOCUMENT_TYPES` backend+frontend | `DEFAULT_SKILLS_BY_AGENT` dans skills.py |
| Produits | SKILL.md + analysis.md + reference.html | SKILL.md + analysis.md |
| Domaine | Droit civil québécois | Évaluation immobilière OEAQ/CUSPAP/NPP |

---

## Failure modes documentés

1. **Tests cassés par step AMU** → `_artifact_payload` gère amu-analyst avec fallback sur `type_bien` absent. Mitigation : déterministe par défaut, crash impossible.
2. **Renumbering YAML** → vérifier que le parser accepte step 2 inséré. Aucun test ne hard-code le nombre de steps à 5.
3. **enrich_case priority** → `{**plan_fields, **case}` : `case` gagne toujours sur les champs plan. Wrappé try/except → non-bloquant.

---

## Stratégie de tests

- `TestAmuDeterministic` — umpp_conclusion.json produit par _artifact_payload, résidentiel standard, terrain
- `TestPipelineStepCount` — DEFAULT_STEPS a 6 étapes, amu-analyst en position 2
- `TestOrchestatorWiring` — start_runtime enrichit le case (testé via mock, pas en intégration)
- Tous tests existants (52) doivent passer sans modification
