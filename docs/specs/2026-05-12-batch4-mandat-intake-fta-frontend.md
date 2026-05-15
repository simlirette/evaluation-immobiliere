# Spec — Batch 4 : mandat-intake agent + analyse-approche-fta + frontend Plan de mandat

_Date : 2026-05-12 | Statut : Approuvé_

---

## Scope

**In scope :**
1. `redaction-lettre-mandat` skill + `analyse-approche-fta` skill (via build-eval-skill)
2. `AGENTCONFIG-MANDAT-INTAKE-V0.yaml` — nouvel agent step 0
3. Pipeline 6→7 steps (mandat-intake en position 0)
4. `lettre_mandat.md` + `conflit_interets.json` — nouveaux artefacts pipeline
5. Persistance des champs plan (mandat_type, format_rapport, methodes_requises) dans la session
6. Section "Plan de mandat" dans DossierPanel frontend

**Non-goals (Batch 5) :**
- UI de saisie du commanditaire avant lancement pipeline (V0 déterministe)
- Signature numérique lettre de mandat
- Gate bloquant sur conflit d'intérêts (V0 = `conflit_detecte: false` déterministe)
- Agent `mandat-intake` avec vrai appel LLM — V0 déterministe comme AMU

---

## Architecture et data flow

### Pipeline après Batch 4

```
mandat-intake(1) → data-facts(2) → amu-analyst(3) → comps-market(4) → valuation-draft(5) → compliance-qa(6) → redaction(7)
```

### Flux mandat-intake

```
case → [mandat-intake] → lettre_mandat.md (enrichi LLM)
                       → conflit_interets.json (V0 deterministe)
                              ↓
                 lettre_mandat.md lu par redaction (section mandant du rapport)
```

### Flux mandat fields → frontend

```
start_runtime(): enrich_case() → case[mandat_type, format_rapport, methodes_requises]
                               → session["mandat_*"] = case["mandat_*"]
                               → write_json(session.json)

app_session_view() lit session.json → retourne "mandat": {...}
AppState.active.mandat → DossierPanel affiche section "Plan de mandat"
```

---

## Interfaces / contrats

### `conflit_interets.json` (step mandat-intake, writes)

```json
{
  "dossier_id": "...",
  "step": "mandat-intake",
  "artifact": "conflit_interets.json",
  "source_fixture": "...",
  "conflit_detecte": false,
  "verification_completee": true,
  "commentaire": "Aucun conflit d'intérêts détecté — vérification V0 déterministe."
}
```

### `lettre_mandat.md` (step mandat-intake, writes)

Artefact MD — `_raw_md` field, enrichi par LLM. Contenu : identification bien, commanditaire, type acte professionnel, type rapport, fin d'évaluation, date référence, honoraires (placeholder), date livraison prévue.

### `session.mandat_*` (api.py, persisted in session.json)

Après `enrich_case()` dans `start_runtime()` :
```python
session["mandat_type"] = case.get("mandat_type")
session["format_rapport"] = case.get("format_rapport")
session["methodes_requises"] = case.get("methodes_requises", [])
session["methode_preponderante"] = case.get("methode_preponderante")
```

### `AppState.active.mandat` (TypeScript)

```typescript
mandat: {
  mandat_type: string
  format_rapport: string
  methodes_requises: string[]
  methode_preponderante: string
} | null
```

---

## Composants à créer/modifier

| Fichier | Action | Notes |
|---|---|---|
| `backend/skills/redaction-lettre-mandat/SKILL.md` | Créer | Via build-eval-skill methodology |
| `backend/skills/redaction-lettre-mandat/analysis.md` | Créer | §6.3 workflow, 10 éléments obligatoires |
| `backend/skills/analyse-approche-fta/SKILL.md` | Créer | Via build-eval-skill methodology |
| `backend/skills/analyse-approche-fta/analysis.md` | Créer | §9.7 workflow, DCF/FTA complet |
| `backend/integration/AGENTCONFIG-MANDAT-INTAKE-V0.yaml` | Créer | Nouvel agent step 0 |
| `backend/engine/skills.py` | Modifier | `mandat-intake` dans DEFAULT_SKILLS_BY_AGENT ; `analyse-approche-fta` dans `valuation-draft` |
| `backend/engine/runtime.py` | Modifier | 5 changements (voir ci-dessous) |
| `backend/integration/PIPELINE-RUNTIME-ASTON-V0.yaml` | Modifier | Renumber 1-7, insérer step 1 |
| `backend/api.py` | Modifier | Persister mandat_* dans session + exposer dans app_session_view() |
| `src/lib/runtime-api.ts` | Modifier | Ajouter `mandat` dans AppState.active |
| `src/components/panels/DossierPanel.tsx` | Modifier | Section "Plan de mandat" |
| `backend/tests/test_pure.py` | Modifier | Tests mandat-intake + pipeline 7 steps |

---

## Détail des changements runtime.py (5 emplacements)

### 5a — `_LLM_TEXT_FIELD_BY_ARTIFACT`

```python
"lettre_mandat.md": "_raw_md",   # ajouter après amu_analyse.md
```

### 5b — `REQUIRED_FIELDS_BY_ARTIFACT`

```python
"conflit_interets.json": ["dossier_id", "step", "artifact", "source_fixture", "conflit_detecte"],
```

### 5c — `DEFAULT_STEPS`

Insérer en index 0 :
```python
RuntimeStep(
    "mandat-intake",
    ["dossier_input"],
    ["lettre_mandat.md", "conflit_interets.json"],
    _skills_for_agent("mandat-intake"),
    "AGENTCONFIG-MANDAT-INTAKE-V0.yaml"
),
```
`redaction` reads mis à jour pour inclure `lettre_mandat.md`.

### 5d — `_artifact_payload` pour mandat-intake

```python
if step == "mandat-intake" and artifact == "conflit_interets.json":
    payload.update({
        "conflit_detecte": False,
        "verification_completee": True,
        "commentaire": "Aucun conflit d'interets detecte — verification V0 deterministe.",
    })

if step == "mandat-intake" and artifact == "lettre_mandat.md":
    type_bien = str(case.get("type_bien", "inconnu")).replace("_", " ")
    mandat_type = str(case.get("mandat_type", "residentiel_standard"))
    format_rapport = str(case.get("format_rapport", "abrege"))
    date_ref = case.get("date_reference", "—")
    dossier_id = case.get("dossier_id", "—")
    payload["_raw_md"] = (
        f"# Lettre de mandat\n\n"
        f"**Dossier :** {dossier_id}  \n"
        f"**Type de bien :** {type_bien}  \n"
        f"**Type de mandat :** {mandat_type}  \n"
        f"**Format du rapport :** {format_rapport}  \n"
        f"**Date de référence :** {date_ref}\n\n"
        f"## Identification du bien\n\n"
        f"Bien de type {type_bien} tel que décrit dans le dossier {dossier_id}.\n\n"
        f"## Type d'acte professionnel\n\n"
        f"Évaluation immobilière — rapport {format_rapport}.\n\n"
        f"## Fin d'évaluation\n\n"
        f"Mandat de type {mandat_type}.\n\n"
        f"## Honoraires et conditions\n\n"
        f"À confirmer selon entente avec le commanditaire.\n\n"
        f"## Signatures\n\n"
        f"_Évaluateur agréé (É.A.) — signature requise_  \n"
        f"_Commanditaire — signature requise_\n"
    )
```

### 5e — `_build_enrichment_prompt` pour lettre_mandat.md

```python
if artifact == "lettre_mandat.md":
    mandat_type = str(case.get("mandat_type", "residentiel_standard"))
    format_rapport = str(case.get("format_rapport", "abrege"))
    methodes = case.get("methodes_requises", [])
    return base + (
        f"MANDAT :\n"
        f"Type de bien : {type_bien} | Mandat : {mandat_type} | Format rapport : {format_rapport}\n"
        f"Methodes requises : {methodes}\n\n"
        "Redige la lettre de mandat professionnelle en Markdown conforme au Code de deontologie OEAQ. "
        "Structure obligatoire : identification du bien, identification du commanditaire (laisser [COMMANDITAIRE] si absent), "
        "type d'acte professionnel, type de rapport, fin d'evaluation, date de reference, "
        "etendue de l'inspection, hypotheses et limitations prealables, honoraires ([A CONFIRMER]), "
        "date de livraison prevue ([A CONFIRMER]), lignes de signature. "
        "Ton professionnel, juridiction Quebec, references deontologiques OEAQ."
    )
```

---

## Changements api.py

### Persistance des champs plan dans la session

Dans `start_runtime()`, après le bloc `try/except enrich_case` et avant `session_dir = Path(...)` :

```python
    # Persister les champs plan dans la session pour exposition frontend
    for _field in ("mandat_type", "format_rapport", "methodes_requises", "methode_preponderante"):
        if case.get(_field) is not None:
            session[_field] = case[_field]
    write_json(Path(session["session_dir"]) / "session.json", session)
```

### Exposition dans app_session_view()

Dans la dict retournée par `app_session_view()`, ajouter la clé `"mandat"` :

```python
"mandat": {
    "mandat_type": session.get("mandat_type"),
    "format_rapport": session.get("format_rapport"),
    "methodes_requises": session.get("methodes_requises", []),
    "methode_preponderante": session.get("methode_preponderante"),
} if session.get("mandat_type") else None,
```

---

## Changements frontend

### `src/lib/runtime-api.ts`

Dans l'interface `AppState`, dans le bloc `active`, ajouter :

```typescript
mandat: {
  mandat_type: string
  format_rapport: string
  methodes_requises: string[]
  methode_preponderante: string
} | null
```

### `src/components/panels/DossierPanel.tsx`

Récupérer `mandat` depuis `AppState.active`. Ajouter une section dans le render principal (après les chips, avant les documents) :

```tsx
{mandat && (
  <AgentMessage agentName="Agent Mandat">
    {'Plan de mandat'}
    <div className="flex flex-wrap gap-1.5 mt-2.5">
      <Chip label={`Mandat\u00a0: ${mandat.mandat_type.replace(/_/g, '\u00a0')}`} highlight />
      <Chip label={`Format\u00a0: ${mandat.format_rapport.replace(/_/g, '\u00a0')}`} highlight />
      {mandat.methodes_requises.map((m, i) => (
        <Chip key={i} label={m.replace(/_/g, '\u00a0')} />
      ))}
    </div>
  </AgentMessage>
)}
```

`mandat` est chargé via `fetchAppState(dossierId)` dans le useEffect existant.

---

## Stratégie de tests

- `TestMandatIntakeDeterministic` — `conflit_interets.json` champs + `lettre_mandat.md` `_raw_md` présent
- `TestPipelineStepCount` (mise à jour) — DEFAULT_STEPS a 7 étapes, `mandat-intake` en index 0
- `TestDefaultSkillsByAgent` (mise à jour) — `mandat-intake` présent, `analyse-approche-fta` dans `valuation-draft`
- Tous les tests existants (59) doivent passer sans modification

---

## Failure modes documentés

1. **`write_json` session avant `session_dir` résolu** → le bloc de persistance mandat doit être placé **après** que `session["session_dir"]` est garanti (il est défini dans `create_session()`, avant `start_runtime()`). Mitigation : le chemin est résolu dès l'entrée de `start_runtime()`.
2. **Frontend crash si `mandat: null`** → la section est conditionnellement rendue (`{mandat && ...}`). Si l'ancien pipeline tourne sans mandat_type, rien ne s'affiche — pas de crash.
3. **Tests pipeline hardcodés à 6** → `TestPipelineStepCount` mis à jour dans le même commit que `DEFAULT_STEPS`. Les 59 tests existants ne hardcodent pas le nombre de steps à 6 (vérifier avant Task 5).
