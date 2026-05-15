# Spec — Batch 5 : Commanditaire form + LLM conflit + gate pipeline

_Date : 2026-05-13 | Statut : Approuvé_

---

## Scope

**In scope :**
1. Formulaire 2 étapes dans `NewDossierForm` — Step 2 collecte nom commanditaire, organisation, fin d'évaluation
2. Propagation `commanditaire` dans `case` via `POST /app/demo` → `app_start_demo()` → `start_runtime()`
3. `lettre_mandat.md` utilise `case["commanditaire"]["nom"]` au lieu de `[COMMANDITAIRE]`
4. `conflit_interets.json` : LLM analyse les données du dossier, peut poser `conflit_detecte: true` + `analyse_conflit` (texte)
5. Gate pipeline dans `runtime.py` : si `conflit_detecte: true` après mandat-intake → `PipelineConflitError` → status `CONFLIT_DETECTE`
6. Override `case["force_conflit_continue"]: true` pour contournement documenté
7. `AppState.active.conflit` exposé par `app_session_view()`
8. `DossierPanel` affiche encadré rouge si `conflit.detecte: true`

**Non-goals (Batch 6+) :**
- Auto-fill commanditaire depuis documents uploadés (nécessite ingestion-documents)
- Base de données conflits réelle (V0 = heuristique LLM sur données dossier)
- Signature numérique lettre de mandat (Batch 10)
- UI de résolution conflit avec workflow de consentement (V0 = arrêt + motif)

---

## Architecture et data flow

### Flux commanditaire

```
NewDossierForm Step 2
  → POST /app/demo { commanditaire: {nom, organisation, fin_evaluation} }
  → app_start_demo() injecte dans start_runtime() body
  → load_case_from_body() merge dans case["commanditaire"]
  → mandat-intake _artifact_payload() lit case["commanditaire"]["nom"]
  → lettre_mandat.md contient le vrai nom au lieu de [COMMANDITAIRE]
```

### Flux conflit

```
runtime.py run_case_data()
  → mandat-intake step : _artifact_payload() → conflit_interets.json (déterministe V0)
  → _enrich_artifact_llm() → LLM analyse case + commanditaire → peut set conflit_detecte: true
  → [GATE] : lire conflit_interets.json écrit sur disque
      si conflit_detecte: true ET force_conflit_continue absent → raise PipelineConflitError
      sinon → continuer pipeline normalement
```

### Flux frontend conflit

```
app_session_view() lit conflit_interets.json depuis artifact_index
  → "conflit": {"detecte": bool, "motif": str} | null dans la réponse
AppState.active.conflit → DossierPanel affiche encadré rouge si detecte: true
```

---

## Interfaces / contrats

### `conflit_interets.json` — V1 (LLM-enrichi)

```json
{
  "dossier_id": "...",
  "step": "mandat-intake",
  "artifact": "conflit_interets.json",
  "source_fixture": "...",
  "conflit_detecte": false,
  "verification_completee": true,
  "commentaire": "Aucun conflit d'intérêts détecté.",
  "analyse_conflit": "Texte LLM — analyse des parties, commanditaire, relation évaluateur."
}
```

`analyse_conflit` est le champ enrichi par LLM (pattern `_LLM_TEXT_FIELD_BY_ARTIFACT`). `conflit_detecte` reste déterministe en fallback (false) si LLM absent. Si LLM active et détecte anomalie → le LLM doit retourner un texte commençant par `CONFLIT_DETECTE:` pour déclencher le gate.

### `case["commanditaire"]`

```python
{
    "nom": "Banque Nationale du Canada",      # str, requis
    "organisation": "Financement immobilier", # str, optionnel
    "fin_evaluation": "hypothecaire",         # str, valeurs: hypothecaire|succession|litige|assurance|commercial|expropriation|autre
}
```

### `AppState.active.conflit` (TypeScript)

```typescript
conflit: {
  detecte: boolean
  motif: string
} | null
```

### `_LLM_TEXT_FIELD_BY_ARTIFACT` — nouvel entrée

```python
"conflit_interets.json": "analyse_conflit",
```

### `_build_enrichment_prompt` — bloc `conflit_interets.json`

Le prompt demande au LLM d'analyser les données disponibles (commanditaire, parties du dossier, type de bien) et de détecter d'éventuels conflits d'intérêts. Si conflit détecté, le LLM commence sa réponse par `CONFLIT_DETECTE: <motif court>`. Sinon, réponse normale.

Après l'appel LLM dans `_enrich_artifact_llm()` : si `analyse_conflit` commence par `CONFLIT_DETECTE:`, setter `conflit_detecte: True` et extraire le motif dans `conflit_motif`.

---

## Composants à créer/modifier

| Fichier | Action | Notes |
|---|---|---|
| `src/components/panels/DossierPanel.tsx` | Modifier | `NewDossierForm` → 2 étapes |
| `src/lib/runtime-api.ts` | Modifier | `CreateRuntimeDossierInput` + `commanditaire` ; `AppState.active.conflit` |
| `src/lib/supabase/queries/dossiers.ts` | Modifier | Passer `commanditaire` à `createRuntimeDossier()` |
| `backend/api.py` | Modifier | `app_start_demo()` + `app_session_view()` |
| `backend/engine/runtime.py` | Modifier | 4 changements (voir ci-dessous) |
| `backend/tests/test_pure.py` | Modifier | Tests commanditaire + gate + conflit |

---

## Détail des changements `runtime.py` (4 emplacements)

### R1 — `_LLM_TEXT_FIELD_BY_ARTIFACT`

```python
"conflit_interets.json": "analyse_conflit",
```

### R2 — `_build_enrichment_prompt` pour `conflit_interets.json`

Insérer avant le fallback générique :

```python
if artifact == "conflit_interets.json":
    commanditaire = case.get("commanditaire", {})
    nom_cmd = str(commanditaire.get("nom", "[COMMANDITAIRE]"))
    org_cmd = str(commanditaire.get("organisation", ""))
    fin_eval = str(commanditaire.get("fin_evaluation", "non specifie"))
    return base + (
        f"VÉRIFICATION CONFLIT D'INTÉRÊTS :\n"
        f"Commanditaire : {nom_cmd} | Organisation : {org_cmd} | Fin : {fin_eval}\n"
        f"Type de bien : {type_bien} | Zone : {case.get('zone', '—')}\n\n"
        "Tu es un expert en déontologie de l'évaluation immobilière OEAQ. "
        "Analyse s'il existe un conflit d'intérêts potentiel entre l'évaluateur et le commanditaire/les parties. "
        "Critères OEAQ : lien financier, familial, ou professionnel avec une partie; mandat conditionnel à une valeur; "
        "intérêt direct dans la propriété. "
        "Si tu détectes un conflit réel ou potentiel, commence ta réponse EXACTEMENT par : "
        "'CONFLIT_DETECTE: <motif court en 1 ligne>' puis développe l'analyse. "
        "Si aucun conflit : rédige une analyse courte confirmant l'absence de conflit apparent."
    )
```

### R3 — `_enrich_artifact_llm` — détection `CONFLIT_DETECTE:`

Après l'appel LLM, si l'artifact est `conflit_interets.json` et que le résultat commence par `CONFLIT_DETECTE:` :

```python
if artifact == "conflit_interets.json" and result.startswith("CONFLIT_DETECTE:"):
    first_line = result.split("\n")[0]
    motif = first_line.replace("CONFLIT_DETECTE:", "").strip()
    return {**payload, "analyse_conflit": result, "conflit_detecte": True, "conflit_motif": motif}
```

### R4 — Gate dans `run_case_data()` après step mandat-intake

Après l'écriture des artifacts du step mandat-intake, lire `conflit_interets.json` depuis le répertoire d'artifacts. Si `conflit_detecte: True` et `case.get("force_conflit_continue")` absent :

```python
# Gate conflit après mandat-intake
if step.name == "mandat-intake":
    conflit_path = artifact_dir / case_stem / "conflit_interets.json"
    if conflit_path.exists():
        _conflit = json.loads(conflit_path.read_text(encoding="utf-8"))
        if _conflit.get("conflit_detecte") and not case.get("force_conflit_continue"):
            motif = _conflit.get("conflit_motif", "Conflit detecte par analyse mandat-intake")
            raise PipelineConflitError(motif)
```

Nouvelle exception dans `runtime.py` :

```python
class PipelineConflitError(ValueError):
    pass
```

Dans `start_runtime()` (api.py), catcher `PipelineConflitError` et retourner un résultat avec `status: "CONFLIT_DETECTE"`.

---

## Changements `api.py`

### A1 — `app_start_demo()` : injecter commanditaire

```python
def app_start_demo(body: dict) -> dict:
    fixture = str(body.get("fixture") or APP_DEFAULT_FIXTURE)
    runtime_body: dict = {"fixture": fixture, "strict_mode": True}
    # Injecter commanditaire dans le body start_runtime si fourni
    if body.get("commanditaire"):
        runtime_body["commanditaire"] = body["commanditaire"]
    started = start_runtime(runtime_body)
    ...
```

### A2 — `load_case_from_body()` : merger commanditaire dans case

```python
if body.get("commanditaire") and isinstance(body["commanditaire"], dict):
    case["commanditaire"] = {
        "nom": str(body["commanditaire"].get("nom", "[COMMANDITAIRE]")),
        "organisation": str(body["commanditaire"].get("organisation", "")),
        "fin_evaluation": str(body["commanditaire"].get("fin_evaluation", "non_specifie")),
    }
```

### A3 — `start_runtime()` : catcher `PipelineConflitError`

```python
from engine.runtime import RuntimeEngine, PipelineConflitError
...
try:
    result = engine.run_case_data(...)
except PipelineConflitError as e:
    result = {
        "status": "CONFLIT_DETECTE",
        "dossier_id": case.get("dossier_id", ""),
        "blocking_failures": [f"CONFLIT: {e}"],
        "warnings": [],
        "events": [],
        "artifact_dir": str(session_dir / "artifacts"),
    }
```

### A4 — `app_session_view()` : exposer `conflit`

```python
# Lire conflit_interets.json depuis artifact_index si présent
_conflit_artifact = artifact_index.get("conflit_interets.json")  # path
_conflit_data = read_json_dict(_conflit_artifact) if _conflit_artifact and Path(_conflit_artifact).exists() else {}
...
"conflit": {
    "detecte": bool(_conflit_data.get("conflit_detecte", False)),
    "motif": str(_conflit_data.get("conflit_motif", _conflit_data.get("commentaire", ""))),
} if _conflit_data else None,
```

---

## Changements `_artifact_payload` — commanditaire dans `lettre_mandat.md`

Dans le bloc `if step == "mandat-intake" and artifact == "lettre_mandat.md":`, remplacer le placeholder :

```python
commanditaire = case.get("commanditaire", {})
nom_cmd = str(commanditaire.get("nom", "[COMMANDITAIRE]"))
org_cmd = str(commanditaire.get("organisation", ""))
cmd_label = f"{nom_cmd} — {org_cmd}" if org_cmd else nom_cmd
fin_eval = str(commanditaire.get("fin_evaluation", "non_specifie")).replace("_", " ")
```

Utiliser `cmd_label` et `fin_eval` dans le `_raw_md` au lieu des placeholders.

---

## Changements frontend

### `src/lib/runtime-api.ts`

Ajouter `commanditaire` dans `CreateRuntimeDossierInput` :

```typescript
export interface CreateRuntimeDossierInput {
  address: string
  property_type: string
  neighborhood: string
  commanditaire?: {
    nom: string
    organisation: string
    fin_evaluation: string
  }
}
```

Ajouter `conflit` dans `AppState.active` :

```typescript
conflit: {
  detecte: boolean
  motif: string
} | null
```

### `src/lib/supabase/queries/dossiers.ts`

Passer `commanditaire` dans `createRuntimeDossier(input)` → body du POST `/app/demo`.

### `src/components/panels/DossierPanel.tsx` — `NewDossierForm`

`NewDossierForm` devient une form à 2 étapes :
- `step: 1 | 2` dans le state local
- Étape 1 : champs existants (nom dossier, type, secteur) + bouton "Suivant →"
- Étape 2 : Nom commanditaire (required), Organisation (optional), Fin d'évaluation (select) + bouton "Lancer le dossier"
- `handleSubmit` ne se déclenche qu'à l'étape 2

FIN_EVALUATION_OPTIONS :
```typescript
const FIN_EVAL_OPTIONS = [
  { value: 'hypothecaire', label: 'Hypothécaire / financement' },
  { value: 'succession', label: 'Succession / liquidation' },
  { value: 'litige', label: 'Litige judiciaire' },
  { value: 'assurance', label: 'Valeur assurable' },
  { value: 'commercial', label: 'Investissement commercial' },
  { value: 'expropriation', label: 'Expropriation' },
  { value: 'autre', label: 'Autre' },
]
```

Encadré conflit dans `DossierPanel` : si `AppState.active.conflit?.detecte`, afficher avant les chips :

```tsx
{conflit?.detecte && (
  <AgentMessage agentName="Agent Mandat">
    <div className="rounded-[8px] px-3 py-2 text-[12px] text-red-700 bg-red-50/80 border border-red-200/60">
      {'Conflit d\u2019int\u00e9r\u00eats d\u00e9tect\u00e9\u00a0\u2014 pipeline arr\u00eat\u00e9'}
      {conflit.motif && <div className="mt-1 opacity-80">{conflit.motif}</div>}
    </div>
  </AgentMessage>
)}
```

---

## Stratégie de tests

- `TestCommanditaireInCase` — `load_case_from_body()` merge correctement les 3 champs
- `TestLettreMandat_Commanditaire` — `_artifact_payload("mandat-intake", "lettre_mandat.md", case_with_cmd)` ne contient plus `[COMMANDITAIRE]`
- `TestConflit_Gate_Blocks` — pipeline lève `PipelineConflitError` si `conflit_detecte: True` dans artifact
- `TestConflit_ForceOverride` — `force_conflit_continue: True` dans case → pipeline continue malgré conflit
- `TestConflit_Deterministic_False` — sans LLM, `conflit_detecte` reste `False` (régression Batch 4)
- Tous les 67 tests existants doivent passer sans modification

---

## Failure modes documentés

1. **Faux positif LLM → évaluateur bloqué** — `force_conflit_continue: true` permet override documenté. Motif affiché dans UI. *(Minor)*
2. **Commanditaire absent sur re-run session** — `[COMMANDITAIRE]` placeholder en fallback dans `lettre_mandat.md`. Pas de crash. *(Minor)*
3. **`conflit_interets.json` absent de l'artifact_index** — `app_session_view()` retourne `conflit: null`. Frontend condition `{conflit?.detecte && ...}` gère le cas. *(Minor)*
4. **`PipelineConflitError` non catchée dans `start_runtime()`** — Si catch manquant, le pipeline explose avec 500. Mitigé : import explicite et catch en Task 4 backend. *(Critical → mitigé par le plan)*
