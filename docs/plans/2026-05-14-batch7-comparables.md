# Batch 7 — Comparables manuels Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-optimized:subagent-driven-development (recommended) or superpowers-optimized:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permettre la saisie manuelle de comparables candidats dans le wizard DossierPanel avant le lancement du pipeline.

**Architecture:** Les comparables saisis dans le frontend sont passés dans le POST `/app/demo`, propagés dans `runtime_body` par `app_start_demo`, puis mappés dans `case["comparables"]` via `load_case_from_body`. Le backend (`runtime.py` L624, `tools.py:search_comparables`) est déjà câblé — aucune modification. Seuls `api.py` (injection) et le frontend (wizard step 3 + types) changent.

**Tech Stack:** Python 3 (backend/api.py), TypeScript/React (Next.js frontend)

**Assumptions:**
- `case_nominal.json` fixture existe dans `backend/tests/fixtures/` — utilisée par défaut dans `load_case_from_body({})`. Requis pour les tests.
- Assumes `formStep` is `1 | 2` currently — will become `1 | 2 | 3`.
- Will NOT handle comparables entered when `body["case"]` is provided directly (inline case path) — only the fixture path used by `/app/demo`.

---

## File Structure

| Fichier | Rôle | Action |
|---------|------|--------|
| `backend/api.py` | Fonction pure `_map_comparable_input` + injection dans `load_case_from_body` + passthrough dans `app_start_demo` | Modify |
| `backend/tests/test_pure.py` | 6 tests: `TestMapComparableInput_Full`, `TestMapComparableInput_NullOptionals`, `TestLoadCaseBody_ComparablesInjected` | Modify |
| `src/types/index.ts` | Nouveau type `ComparableInput` | Modify |
| `src/lib/runtime-api.ts` | Étendre `CreateRuntimeDossierInput` + passer comparables dans POST | Modify |
| `src/components/panels/DossierPanel.tsx` | `formStep` 1\|2 → 1\|2\|3, state comparables, step 3 JSX | Modify |

---

## Wave Plan

- **Wave 1** (parallel): Task 1 (backend tests) + Task 3 (frontend types/API) — fichiers disjoints
- **Wave 2** (parallel): Task 2 (backend impl) + Task 4 (frontend UI) — fichiers disjoints
- **Wave 3** (sequential): Task 5 (vérification)

---

### Task 1: Backend tests (TDD — écrire avant l'implémentation)

**Files:**
- Modify: `backend/tests/test_pure.py`

**Security flag:** `none`

**Does NOT cover:** Tests pour `app_start_demo` (testé indirectement via `load_case_from_body`). Tests pour comparables avec `body["case"]` inline (non-goal).

- [ ] **Step 1: Ajouter les classes de test à la fin de `backend/tests/test_pure.py`**

```python
# ── TestMapComparableInput_Full ───────────────────────────────────────────────

class TestMapComparableInput_Full:
    def test_all_fields_mapped_correctly(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from api import _map_comparable_input
        row = {
            "id": "abc123",
            "adresse": "123 rue Example, Montréal",
            "date_vente": "2024-06-15",
            "prix_vente": 450000,
            "source_id": "CENTRIS-12345678",
            "source_type": "mls_centris",
            "type_propriete": "unifamiliale",
            "surface_hab": 145.0,
            "surface_terrain": 350.0,
            "annee_construction": 1985,
            "nb_logements": None,
            "conditions_vente": "normale",
            "notes": "Belle propriété",
        }
        result = _map_comparable_input(row)
        assert result["comparable_id"] == "CENTRIS-12345678"
        assert result["adresse"] == "123 rue Example, Montréal"
        assert result["date_vente"] == "2024-06-15"
        assert result["prix_vente"] == 450000.0
        assert result["source_id"] == "CENTRIS-12345678"
        assert result["source_type"] == "mls_centris"
        assert result["surface"] == {"value": 145.0, "unit": "m²"}
        assert result["surface_terrain"] == 350.0
        assert result["annee_construction"] == 1985
        assert result["nb_logements"] is None
        assert result["conditions_vente"] == "normale"
        assert result["notes"] == "Belle propriété"
        assert result["confidence"] == 0.80


# ── TestMapComparableInput_NullOptionals ──────────────────────────────────────

class TestMapComparableInput_NullOptionals:
    def test_surface_hab_none_returns_empty_surface_dict(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from api import _map_comparable_input
        row = {
            "surface_hab": None,
            "annee_construction": None,
            "surface_terrain": None,
            "nb_logements": None,
        }
        result = _map_comparable_input(row)
        assert result["surface"] == {}
        assert result["annee_construction"] is None
        assert result["surface_terrain"] is None
        assert result["nb_logements"] is None

    def test_missing_source_id_falls_back_to_id_field(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from api import _map_comparable_input
        row = {"id": "fallback-uuid", "source_id": ""}
        result = _map_comparable_input(row)
        assert result["comparable_id"] == "fallback-uuid"


# ── TestLoadCaseBody_ComparablesInjected ──────────────────────────────────────

class TestLoadCaseBody_ComparablesInjected:
    def test_comparables_mapped_from_body(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from api import load_case_from_body
        body = {
            "comparables": [
                {
                    "id": "c1",
                    "adresse": "456 rue Test",
                    "date_vente": "2024-03-01",
                    "prix_vente": 500000,
                    "source_id": "RF-2024-001",
                    "source_type": "registre_foncier",
                    "surface_hab": 120.0,
                    "surface_terrain": None,
                    "annee_construction": 1992,
                    "nb_logements": None,
                    "conditions_vente": "normale",
                    "notes": "",
                }
            ]
        }
        case, _ = load_case_from_body(body)
        assert len(case["comparables"]) == 1
        comp = case["comparables"][0]
        assert comp["source_id"] == "RF-2024-001"
        assert comp["surface"] == {"value": 120.0, "unit": "m²"}
        assert comp["confidence"] == 0.80

    def test_comparables_body_override_fixture_comparables(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from api import load_case_from_body
        body = {
            "comparables": [
                {
                    "id": "new1",
                    "source_id": "NEW-001",
                    "prix_vente": 300000,
                    "surface_hab": None,
                    "surface_terrain": None,
                    "annee_construction": None,
                    "nb_logements": None,
                }
            ]
        }
        case, _ = load_case_from_body(body)
        assert len(case["comparables"]) >= 1
        assert all(c["source_id"] == "NEW-001" for c in case["comparables"])

    def test_no_comparables_in_body_leaves_fixture_untouched(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from api import load_case_from_body
        case_a, _ = load_case_from_body({})
        fixture_comps = list(case_a.get("comparables", []))
        case_b, _ = load_case_from_body({})
        assert case_b.get("comparables", []) == fixture_comps
```

- [ ] **Step 2: Vérifier que les tests échouent (ImportError attendu — `_map_comparable_input` n'existe pas encore)**

Run: `cd backend && python -m pytest tests/test_pure.py::TestMapComparableInput_Full tests/test_pure.py::TestMapComparableInput_NullOptionals tests/test_pure.py::TestLoadCaseBody_ComparablesInjected -v 2>&1 | head -40`

Expected: FAIL — `ImportError: cannot import name '_map_comparable_input' from 'api'`

- [ ] **Step 3: Commit les tests**

```bash
git add backend/tests/test_pure.py
git commit -m "test(batch7): add failing tests for comparable input mapping and injection"
```

---

### Task 2: Backend implementation — `_map_comparable_input` + injection

**Files:**
- Modify: `backend/api.py`

**Security flag:** `none`

**Does NOT cover:** Validation de format `date_vente` (laissé au frontend). Injection de comparables quand `body["case"]` est fourni directement.

- [ ] **Step 1: Ajouter `_map_comparable_input` dans `backend/api.py` juste avant `load_case_from_body`**

Insérer avant la ligne `def load_case_from_body(body: dict) -> tuple[dict, str]:` :

```python
def _map_comparable_input(row: dict) -> dict:
    """Convertit un comparable saisi côté frontend au format attendu par tools.py:search_comparables."""
    surface_hab = row.get("surface_hab")
    return {
        "comparable_id": str(row.get("source_id") or row.get("id") or ""),
        "adresse": str(row.get("adresse") or ""),
        "date_vente": str(row.get("date_vente") or ""),
        "prix_vente": float(row.get("prix_vente") or 0),
        "source_id": str(row.get("source_id") or ""),
        "source_type": str(row.get("source_type") or "autre"),
        "surface": {"value": float(surface_hab), "unit": "m²"} if surface_hab else {},
        "surface_terrain": float(row["surface_terrain"]) if row.get("surface_terrain") else None,
        "annee_construction": int(row["annee_construction"]) if row.get("annee_construction") else None,
        "nb_logements": int(row["nb_logements"]) if row.get("nb_logements") else None,
        "conditions_vente": str(row.get("conditions_vente") or "normale"),
        "notes": str(row.get("notes") or ""),
        "confidence": 0.80,
    }
```

- [ ] **Step 2: Modifier `load_case_from_body` pour injecter les comparables du body**

Dans `load_case_from_body`, après le bloc d'injection `commanditaire` (après `return case, source_fixture` est atteint via le bloc `if body.get("commanditaire")`), ajouter juste avant `return case, source_fixture` :

```python
    # Injecter comparables dans le case si fournis dans le body
    if body.get("comparables") and isinstance(body["comparables"], list):
        case["comparables"] = [
            _map_comparable_input(r)
            for r in body["comparables"]
            if isinstance(r, dict)
        ]

    return case, source_fixture
```

Le bloc complet `load_case_from_body` devient :

```python
def load_case_from_body(body: dict) -> tuple[dict, str]:
    if "case" in body:
        return body["case"], body.get("source_fixture", "inline")

    fixture_name = body.get("fixture", "case_nominal.json")
    if Path(fixture_name).name != fixture_name:
        raise ValueError("fixture invalide")

    fixture_path = FIXTURES_DIR / fixture_name
    if not fixture_path.exists():
        raise FileNotFoundError(f"fixture introuvable: {fixture_name}")

    case = json.loads(fixture_path.read_text(encoding="utf-8"))
    source_fixture = fixture_name

    # Injecter commanditaire dans le case si fourni dans le body
    if body.get("commanditaire") and isinstance(body["commanditaire"], dict):
        _cmd = body["commanditaire"]
        case["commanditaire"] = {
            "nom": str(_cmd.get("nom", "") or "[COMMANDITAIRE]"),
            "organisation": str(_cmd.get("organisation", "") or ""),
            "fin_evaluation": str(_cmd.get("fin_evaluation", "") or "non_specifie"),
        }

    # Injecter comparables dans le case si fournis dans le body
    if body.get("comparables") and isinstance(body["comparables"], list):
        case["comparables"] = [
            _map_comparable_input(r)
            for r in body["comparables"]
            if isinstance(r, dict)
        ]

    return case, source_fixture
```

- [ ] **Step 3: Modifier `app_start_demo` pour passer les comparables dans `runtime_body`**

Dans `app_start_demo`, après le bloc `if body.get("commanditaire")`, ajouter :

```python
    if body.get("comparables") and isinstance(body["comparables"], list):
        runtime_body["comparables"] = body["comparables"]
```

Le bloc `app_start_demo` complet devient :

```python
def app_start_demo(body: dict) -> dict:
    fixture = str(body.get("fixture") or APP_DEFAULT_FIXTURE)
    runtime_body: dict = {"fixture": fixture, "strict_mode": True}
    if body.get("commanditaire") and isinstance(body["commanditaire"], dict):
        runtime_body["commanditaire"] = body["commanditaire"]
    if body.get("comparables") and isinstance(body["comparables"], list):
        runtime_body["comparables"] = body["comparables"]
    started = start_runtime(runtime_body)
    session_id = str(started.get("session", {}).get("session_id") or "")
    if session_id and any(body.get(key) for key in ("display_name", "property_type", "neighborhood")):
        session = require_session(session_id)
        session["app_display_name"] = str(body.get("display_name") or "").strip()
        session["app_property_type"] = str(body.get("property_type") or "").strip()
        session["app_neighborhood"] = str(body.get("neighborhood") or "").strip()
        save_session(session)
    state = app_state(session_id)
    return {"schema_version": "evaluateur_ai_app_demo_v1", "started": started, "state": state}
```

- [ ] **Step 4: Vérifier que les tests passent**

Run: `cd backend && python -m pytest tests/test_pure.py::TestMapComparableInput_Full tests/test_pure.py::TestMapComparableInput_NullOptionals tests/test_pure.py::TestLoadCaseBody_ComparablesInjected -v`

Expected: 6 tests PASS

- [ ] **Step 5: Vérifier que tous les tests existants passent toujours**

Run: `cd backend && python -m pytest tests/test_pure.py -v 2>&1 | tail -15`

Expected: 94+ tests PASS, 0 failures

- [ ] **Step 6: Commit**

```bash
git add backend/api.py
git commit -m "feat(batch7): add _map_comparable_input and inject comparables from POST body into case"
```

---

### Task 3: Frontend types + API

**Files:**
- Modify: `src/types/index.ts`
- Modify: `src/lib/runtime-api.ts`

**Security flag:** `none`

**Does NOT cover:** Validation côté frontend des champs (fait dans Task 4 via UI).

- [ ] **Step 1: Ajouter `ComparableInput` dans `src/types/index.ts`**

Ajouter après l'interface `Comparable` existante (après la ligne `}`  qui ferme `Comparable`) :

```typescript
export interface ComparableInput {
  id: string                        // UUID client-side (React key)
  adresse: string
  date_vente: string                // ISO: "2024-06-15"
  prix_vente: number
  source_id: string                 // ex: "CENTRIS-12345678" | "RF-2024-ABC"
  source_type: 'mls_centris' | 'registre_foncier' | 'dlc' | 'autre'
  type_propriete: string
  surface_hab: number | null        // m²
  surface_terrain: number | null    // m²
  annee_construction: number | null
  nb_logements: number | null
  conditions_vente: 'normale' | 'liee' | 'autre'
  notes: string
}
```

- [ ] **Step 2: Étendre `CreateRuntimeDossierInput` dans `src/lib/runtime-api.ts`**

Remplacer :

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

Par :

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
  comparables?: import('@/types').ComparableInput[]
}
```

- [ ] **Step 3: Passer les comparables dans le POST dans `createRuntimeDossier`**

Remplacer le `body: JSON.stringify({...})` dans `createRuntimeDossier` :

```typescript
export async function createRuntimeDossier(input: CreateRuntimeDossierInput): Promise<Dossier> {
  const payload = await runtimeJson<{ state: AppState }>('/app/demo', {
    method: 'POST',
    body: JSON.stringify({
      fixture: 'case_pilote_residentiel_standard.json',
      display_name: input.address,
      property_type: input.property_type,
      neighborhood: input.neighborhood,
      ...(input.commanditaire ? { commanditaire: input.commanditaire } : {}),
      ...(input.comparables && input.comparables.length > 0 ? { comparables: input.comparables } : {}),
    }),
  })
  const dossier = payload.state.active?.dossier
  if (!dossier) throw new Error('Aucun dossier runtime cree')
  return dossier
}
```

- [ ] **Step 4: Vérifier que TypeScript compile sans erreur**

Run: `cd .. && npx tsc --noEmit 2>&1 | head -20`

Expected: No errors (ou uniquement des erreurs préexistantes non liées à ce batch)

- [ ] **Step 5: Commit**

```bash
git add src/types/index.ts src/lib/runtime-api.ts
git commit -m "feat(batch7): add ComparableInput type and pass comparables in createRuntimeDossier POST"
```

---

### Task 4: Frontend UI — Step 3 wizard (comparables)

**Files:**
- Modify: `src/components/panels/DossierPanel.tsx`

**Security flag:** `none`

**Does NOT cover:** Réutilisation des comparables entre dossiers. Édition après lancement. Export/impression.

- [ ] **Step 1: Ajouter les imports nécessaires en haut du fichier**

Ajouter `ComparableInput` à l'import existant de `@/types` :

```typescript
import type { Document, FactChip, ComparableInput } from '@/types'
```

- [ ] **Step 2: Modifier `NewDossierForm` — ajouter état + helpers**

Dans `NewDossierForm`, après les déclarations d'état existantes (après `const timersRef`), ajouter :

```typescript
  const [formStep, setFormStep] = useState<1 | 2 | 3>(1)
  const [comparables, setComparables] = useState<ComparableInput[]>([])
  const [expandedId, setExpandedId] = useState<string | null>(null)

  function addComparable() {
    const id = Math.random().toString(36).slice(2, 10)
    setComparables(prev => [...prev, {
      id,
      adresse: '',
      date_vente: '',
      prix_vente: 0,
      source_id: '',
      source_type: 'mls_centris',
      type_propriete: '',
      surface_hab: null,
      surface_terrain: null,
      annee_construction: null,
      nb_logements: null,
      conditions_vente: 'normale',
      notes: '',
    }])
    setExpandedId(id)
  }

  function updateComp(id: string, field: keyof ComparableInput, value: string | number | null) {
    setComparables(prev => prev.map(c => c.id === id ? { ...c, [field]: value } : c))
  }

  function removeComp(id: string) {
    setComparables(prev => prev.filter(c => c.id !== id))
    if (expandedId === id) setExpandedId(null)
  }
```

Note: supprimer la déclaration existante de `formStep` si elle est déjà là sous la forme `useState<1 | 2>(1)` — la remplacer par `useState<1 | 2 | 3>(1)`.

- [ ] **Step 3: Modifier `handleSubmit` pour passer les comparables**

Dans `handleSubmit`, remplacer l'appel `createDossier({...})` par :

```typescript
      const dossier = await createDossier({
        address: address.trim(),
        property_type: propertyType.trim(),
        neighborhood: neighborhood.trim(),
        commanditaire: {
          nom: cmdNom.trim(),
          organisation: cmdOrg.trim(),
          fin_evaluation: cmdFin,
        },
        comparables: comparables.length > 0 ? comparables : undefined,
      })
```

- [ ] **Step 4: Modifier step 2 pour avancer vers step 3 au lieu de soumettre**

Dans le render de `NewDossierForm`, modifier la section step 2 (le `<form onSubmit={handleSubmit} ...>`) :

Changer `<form onSubmit={handleSubmit} ...>` → `<form onSubmit={e => { e.preventDefault(); if (cmdNom.trim()) { setError(''); setFormStep(3) } }} ...>`

Changer le bouton de soumission :

```tsx
            <button
              type="submit"
              className="flex-[2] rounded-[10px] py-2.5 text-[14px] font-medium text-white transition-opacity hover:opacity-90 active:opacity-80"
              style={{ background: '#334155' }}
            >
              Suivant →
            </button>
```

- [ ] **Step 5: Ajouter le render step 3 — remplacer la condition ternaire finale**

Trouver le pattern `formStep === 1 ? (...) : (...)` dans `NewDossierForm` et le transformer en `formStep === 1 ? (...) : formStep === 2 ? (...) : (...)`.

Le bloc step 3 complet à ajouter (après le bloc step 2, dans le ternaire) :

```tsx
      ) : (
        /* Step 3 — Comparables candidats */
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-3">
            {comparables.map(comp => (
              <div
                key={comp.id}
                className="rounded-[10px] overflow-hidden"
                style={{ border: '1px solid var(--input-border)' }}
              >
                {/* Card header — toujours visible */}
                <button
                  type="button"
                  onClick={() => setExpandedId(expandedId === comp.id ? null : comp.id)}
                  className="w-full flex items-center justify-between px-4 py-2.5 text-left"
                  style={{ background: 'var(--input-bg)' }}
                >
                  <span className="text-[13px] text-[#1a1916] truncate">
                    {comp.adresse || 'Comparable sans adresse'}{comp.prix_vente > 0 ? ` · ${comp.prix_vente.toLocaleString('fr-CA')} $` : ''}
                  </span>
                  <span className="text-[11px] text-[#8a8780] ml-2 shrink-0">{expandedId === comp.id ? '▲' : '▼'}</span>
                </button>

                {/* Card body — visible si expanded */}
                {expandedId === comp.id && (
                  <div className="flex flex-col gap-3 px-4 pb-4 pt-3" style={{ background: 'var(--input-bg)', borderTop: '1px solid var(--input-border)' }}>
                    <div className="flex flex-col gap-1.5">
                      <label className="text-[11px] text-[#8a8780] font-medium">Adresse</label>
                      <input type="text" value={comp.adresse} onChange={e => updateComp(comp.id, 'adresse', e.target.value)}
                        className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
                        style={inputStyle} placeholder="123 rue Example, Montréal" />
                    </div>

                    <div className="flex gap-3">
                      <div className="flex flex-col gap-1.5 flex-1">
                        <label className="text-[11px] text-[#8a8780] font-medium">Date de vente</label>
                        <input type="date" value={comp.date_vente} onChange={e => updateComp(comp.id, 'date_vente', e.target.value)}
                          className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none"
                          style={inputStyle} />
                      </div>
                      <div className="flex flex-col gap-1.5 flex-1">
                        <label className="text-[11px] text-[#8a8780] font-medium">Prix de vente ($)</label>
                        <input type="number" min="0" value={comp.prix_vente || ''} onChange={e => updateComp(comp.id, 'prix_vente', parseFloat(e.target.value) || 0)}
                          className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none"
                          style={inputStyle} placeholder="450000" />
                      </div>
                    </div>

                    <div className="flex gap-3">
                      <div className="flex flex-col gap-1.5 flex-1">
                        <label className="text-[11px] text-[#8a8780] font-medium">
                          Source ID <span className="text-[#b5b2ac]">(traçabilité OEAQ)</span>
                        </label>
                        <input type="text" value={comp.source_id} onChange={e => updateComp(comp.id, 'source_id', e.target.value)}
                          className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
                          style={inputStyle} placeholder="CENTRIS-12345678" />
                      </div>
                      <div className="flex flex-col gap-1.5 flex-1">
                        <label className="text-[11px] text-[#8a8780] font-medium">Source</label>
                        <select value={comp.source_type} onChange={e => updateComp(comp.id, 'source_type', e.target.value as ComparableInput['source_type'])}
                          className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none"
                          style={selectStyle}>
                          <option value="mls_centris">Centris / MLS</option>
                          <option value="registre_foncier">Registre foncier</option>
                          <option value="dlc">DLC</option>
                          <option value="autre">Autre</option>
                        </select>
                      </div>
                    </div>

                    <div className="flex gap-3">
                      <div className="flex flex-col gap-1.5 flex-1">
                        <label className="text-[11px] text-[#8a8780] font-medium">Type de propriété</label>
                        <input type="text" value={comp.type_propriete} onChange={e => updateComp(comp.id, 'type_propriete', e.target.value)}
                          className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
                          style={inputStyle} placeholder="Unifamiliale" />
                      </div>
                      <div className="flex flex-col gap-1.5 flex-1">
                        <label className="text-[11px] text-[#8a8780] font-medium">Conditions de vente</label>
                        <select value={comp.conditions_vente} onChange={e => updateComp(comp.id, 'conditions_vente', e.target.value as ComparableInput['conditions_vente'])}
                          className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none"
                          style={selectStyle}>
                          <option value="normale">Normale</option>
                          <option value="liee">Liée</option>
                          <option value="autre">Autre</option>
                        </select>
                      </div>
                    </div>

                    <div className="flex gap-3">
                      <div className="flex flex-col gap-1.5 flex-1">
                        <label className="text-[11px] text-[#8a8780] font-medium">Superficie hab. (m²)</label>
                        <input type="number" min="0" value={comp.surface_hab ?? ''} onChange={e => updateComp(comp.id, 'surface_hab', e.target.value ? parseFloat(e.target.value) : null)}
                          className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none"
                          style={inputStyle} placeholder="145" />
                      </div>
                      <div className="flex flex-col gap-1.5 flex-1">
                        <label className="text-[11px] text-[#8a8780] font-medium">Superficie terrain (m²)</label>
                        <input type="number" min="0" value={comp.surface_terrain ?? ''} onChange={e => updateComp(comp.id, 'surface_terrain', e.target.value ? parseFloat(e.target.value) : null)}
                          className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none"
                          style={inputStyle} placeholder="350" />
                      </div>
                    </div>

                    <div className="flex gap-3">
                      <div className="flex flex-col gap-1.5 flex-1">
                        <label className="text-[11px] text-[#8a8780] font-medium">Année construction</label>
                        <input type="number" min="1800" max="2099" value={comp.annee_construction ?? ''} onChange={e => updateComp(comp.id, 'annee_construction', e.target.value ? parseInt(e.target.value) : null)}
                          className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none"
                          style={inputStyle} placeholder="1985" />
                      </div>
                      <div className="flex flex-col gap-1.5 flex-1">
                        <label className="text-[11px] text-[#8a8780] font-medium">Nb logements <span className="text-[#b5b2ac]">(opt.)</span></label>
                        <input type="number" min="1" value={comp.nb_logements ?? ''} onChange={e => updateComp(comp.id, 'nb_logements', e.target.value ? parseInt(e.target.value) : null)}
                          className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none"
                          style={inputStyle} placeholder="1" />
                      </div>
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <label className="text-[11px] text-[#8a8780] font-medium">Notes</label>
                      <input type="text" value={comp.notes} onChange={e => updateComp(comp.id, 'notes', e.target.value)}
                        className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
                        style={inputStyle} placeholder="Particularités, ajustements prévus…" />
                    </div>

                    <button
                      type="button"
                      onClick={() => removeComp(comp.id)}
                      className="text-[12px] text-red-400 hover:text-red-600 text-left transition-colors"
                    >
                      Supprimer ce comparable
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>

          <button
            type="button"
            onClick={addComparable}
            className="w-full rounded-[10px] py-2.5 text-[14px] font-medium text-[#334155] transition-opacity hover:opacity-80"
            style={{ background: 'var(--input-bg)', border: '1px dashed var(--input-border)' }}
          >
            + Ajouter un comparable
          </button>

          {comparables.length === 0 && (
            <div className="rounded-[8px] px-3 py-2.5 text-[12px] text-[#8a8780]" style={{ background: 'var(--input-bg)', border: '1px solid var(--input-border)' }}>
              Aucun comparable — le rapport sera marqué <strong>A_REVOIR</strong> (CONF002). Vous pouvez continuer et corriger après.
            </div>
          )}

          <div className="flex gap-2 mt-1">
            <button
              type="button"
              onClick={() => { setError(''); setFormStep(2) }}
              className="flex-1 rounded-[10px] py-2.5 text-[14px] font-medium text-[#8a8780] transition-opacity hover:opacity-90 active:opacity-80"
              style={{ background: 'var(--input-bg)', border: '1px solid var(--input-border)' }}
            >
              ← Retour
            </button>
            <button
              type="submit"
              className="flex-[2] rounded-[10px] py-2.5 text-[14px] font-medium text-white transition-opacity hover:opacity-90 active:opacity-80"
              style={{ background: '#334155' }}
            >
              Lancer l&apos;évaluation
            </button>
          </div>
        </form>
```

- [ ] **Step 6: Vérifier que le build TypeScript passe**

Run: `npx tsc --noEmit 2>&1 | head -30`

Expected: 0 nouvelles erreurs

- [ ] **Step 7: Commit**

```bash
git add src/components/panels/DossierPanel.tsx
git commit -m "feat(batch7): add step 3 comparables grid to DossierPanel wizard"
```

---

### Task 5: Vérification finale

**Files:** Aucun (lecture seule)

**Security flag:** `none`

- [ ] **Step 1: Tous les tests backend passent**

Run: `cd backend && python -m pytest tests/test_pure.py -v 2>&1 | tail -20`

Expected: 100+ tests PASS (94 existants + 6 nouveaux), 0 failures

- [ ] **Step 2: Build frontend propre**

Run: `npx next build 2>&1 | tail -20`

Expected: `✓ Compiled successfully` ou équivalent, 0 erreurs TypeScript

- [ ] **Step 3: Vérifier les 6 nouveaux tests nommément**

Run: `cd backend && python -m pytest tests/test_pure.py::TestMapComparableInput_Full tests/test_pure.py::TestMapComparableInput_NullOptionals tests/test_pure.py::TestLoadCaseBody_ComparablesInjected -v`

Expected: 6/6 PASS

- [ ] **Step 4: Vérifier le flux de bout en bout (smoke test manuel)**

Dans le backend, vérifier que `_map_comparable_input` et l'injection sont cohérents avec `tools.py:search_comparables` en Python :

```python
cd backend
python3 -c "
from api import _map_comparable_input
from engine.tools import search_comparables

comp = _map_comparable_input({
    'id': 'test1',
    'adresse': '123 rue Test',
    'date_vente': '2024-06-01',
    'prix_vente': 500000,
    'source_id': 'CENTRIS-99999999',
    'source_type': 'mls_centris',
    'surface_hab': 130.0,
    'surface_terrain': 300.0,
    'annee_construction': 1990,
    'nb_logements': None,
    'conditions_vente': 'normale',
    'notes': '',
})
results = search_comparables([comp], max_items=1)
print('comparable_id:', results[0].comparable_id)
print('prix_vente:', results[0].prix_vente)
print('score:', results[0].score)
print('OK')
"
```

Expected: `comparable_id: CENTRIS-99999999`, `prix_vente: 500000.0`, `score: <float entre 0 et 1>`, `OK`

- [ ] **Step 5: Mettre à jour `state.md`**

```markdown
## Current Goal
Batch 7 terminé. Pipeline prêt pour saisie manuelle de comparables.

## Plan Status
- Batch 7 (comparables manuels): DONE ✓
```

- [ ] **Step 6: Commit final**

```bash
git add state.md
git commit -m "chore: batch7 done — manual comparables input wired end to end"
```
