# Batch 5 — Commanditaire Form + LLM Conflict + Pipeline Gate

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-optimized:subagent-driven-development (recommended) or superpowers-optimized:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add commanditaire 2-step form, LLM conflict detection, and pipeline gate that blocks on detected conflicts.
**Architecture:** Backend pipeline gate reads `conflit_interets.json` after mandat-intake, raises `PipelineConflitError` if LLM flagged a conflict; api.py catches it and returns `status: CONFLIT_DETECTE`; frontend form adds commanditaire fields in step 2 and shows a red conflict banner when detected.
**Tech Stack:** Python (runtime.py, api.py, test_pure.py), TypeScript (runtime-api.ts, dossiers.ts, DossierPanel.tsx)
**Assumptions:**
- `case_subdir=True` always when called from `start_runtime()` (line 1183 api.py) — artifact paths use `case_dir / f"{step.name}.{artifact}"` pattern.
- `read_artifact_json_from_index` helper already exists in api.py (line 1421) — no new helper needed.
- No LLM in tests — `OPENAI_API_KEY` absent → `_enrich_artifact_llm` returns payload unchanged → `conflit_detecte` stays deterministic False unless manually set in payload.

---

## File Structure

| File | Action | What changes |
|---|---|---|
| `backend/engine/runtime.py` | Modify | `PipelineConflitError` class + `_LLM_TEXT_FIELD_BY_ARTIFACT` + `_build_enrichment_prompt` + `_enrich_artifact_llm` + `_artifact_payload` (lettre_mandat) + gate in `run_case_data` |
| `backend/api.py` | Modify | `load_case_from_body` + `app_start_demo` + `start_runtime` catch + `app_session_view` conflit exposition |
| `src/lib/runtime-api.ts` | Modify | `CreateRuntimeDossierInput` + `AppState.active.conflit` |
| `src/lib/supabase/queries/dossiers.ts` | Modify | Pass commanditaire through |
| `src/components/panels/DossierPanel.tsx` | Modify | 2-step `NewDossierForm` + conflict banner |
| `backend/tests/test_pure.py` | Modify | 5 new test classes |

---

### Task 1: Failing tests for backend behavior

**Files:**
- Modify: `backend/tests/test_pure.py`

**Security flag:** `none`

**Does NOT cover:** Tests that require LLM (CONFLIT_DETECTE via LLM) — tested deterministically by manually constructing the artifact with conflit_detecte: True.

- [x] **Step 1: Write failing tests**

Append to `backend/tests/test_pure.py`:

```python
# ── TestCommanditaireInCase ───────────────────────────────────────────────────

class TestCommanditaireInCase:
    def test_commanditaire_merged_from_body(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from api import load_case_from_body
        body = {
            "commanditaire": {
                "nom": "Banque Nationale",
                "organisation": "Financement immobilier",
                "fin_evaluation": "hypothecaire",
            }
        }
        case, _ = load_case_from_body(body)
        assert case["commanditaire"]["nom"] == "Banque Nationale"
        assert case["commanditaire"]["organisation"] == "Financement immobilier"
        assert case["commanditaire"]["fin_evaluation"] == "hypothecaire"

    def test_commanditaire_defaults_when_absent(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from api import load_case_from_body
        case, _ = load_case_from_body({})
        # commanditaire key absent — no crash, no injection
        assert "commanditaire" not in case or case.get("commanditaire") == {}

    def test_commanditaire_nom_default_placeholder(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from api import load_case_from_body
        body = {"commanditaire": {"nom": "", "fin_evaluation": "succession"}}
        case, _ = load_case_from_body(body)
        assert case["commanditaire"]["nom"] == "[COMMANDITAIRE]"


# ── TestLettreMandat_Commanditaire ────────────────────────────────────────────

class TestLettreMandat_Commanditaire:
    def test_lettre_mandat_uses_commanditaire_nom(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import RuntimeEngine
        engine = RuntimeEngine()
        case = {
            "dossier_id": "D-CMD-TEST",
            "type_bien": "residentiel_unifamilial",
            "date_reference": "2026-05-13",
            "mandat_type": "residentiel_standard",
            "format_rapport": "abrege",
            "commanditaire": {
                "nom": "Banque Nationale",
                "organisation": "Financement immobilier",
                "fin_evaluation": "hypothecaire",
            },
        }
        payload = engine._artifact_payload(
            "mandat-intake", "lettre_mandat.md", case, "BROUILLON", [], []
        )
        assert "[COMMANDITAIRE]" not in payload["_raw_md"]
        assert "Banque Nationale" in payload["_raw_md"]

    def test_lettre_mandat_placeholder_when_no_commanditaire(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import RuntimeEngine
        engine = RuntimeEngine()
        case = {
            "dossier_id": "D-CMD-TEST",
            "type_bien": "residentiel_unifamilial",
            "date_reference": "2026-05-13",
            "mandat_type": "residentiel_standard",
            "format_rapport": "abrege",
        }
        payload = engine._artifact_payload(
            "mandat-intake", "lettre_mandat.md", case, "BROUILLON", [], []
        )
        # Should still contain [COMMANDITAIRE] placeholder when missing
        assert "[COMMANDITAIRE]" in payload["_raw_md"]


# ── TestConflit_Deterministic_False ──────────────────────────────────────────

class TestConflit_Deterministic_False:
    def test_conflit_detecte_false_without_llm(self):
        """Without LLM (no OPENAI_API_KEY), conflit_detecte stays False."""
        import sys
        import os
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import RuntimeEngine
        original_key = os.environ.pop("OPENAI_API_KEY", None)
        try:
            engine = RuntimeEngine()
            case = {
                "dossier_id": "D-CONFLIT-TEST",
                "type_bien": "residentiel_unifamilial",
                "date_reference": "2026-05-13",
                "mandat_type": "residentiel_standard",
                "format_rapport": "abrege",
                "commanditaire": {"nom": "BNC", "organisation": "", "fin_evaluation": "hypothecaire"},
            }
            payload = engine._artifact_payload(
                "mandat-intake", "conflit_interets.json", case, "BROUILLON", [], []
            )
            assert payload["conflit_detecte"] is False
            assert payload["verification_completee"] is True
        finally:
            if original_key is not None:
                os.environ["OPENAI_API_KEY"] = original_key


# ── TestConflit_Gate_Blocks ───────────────────────────────────────────────────

class TestConflit_Gate_Blocks:
    def test_pipeline_raises_on_conflit_detecte(self, tmp_path):
        """run_case_data raises PipelineConflitError when conflit_detecte: True in artifact."""
        import sys
        import json
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import RuntimeEngine, PipelineConflitError, DEFAULT_STEPS

        engine = RuntimeEngine(steps=DEFAULT_STEPS[:1])  # mandat-intake only
        case = {
            "dossier_id": "D-GATE-TEST",
            "type_bien": "residentiel_unifamilial",
            "date_reference": "2026-05-13",
            "mandat_type": "residentiel_standard",
            "format_rapport": "abrege",
        }

        import pytest

        # Monkeypatch _artifact_payload to inject conflit_detecte: True for conflit_interets.json
        original_payload = engine._artifact_payload

        def patched_payload(step, artifact, case, status, blocking, warnings, valuation_values=None):
            p = original_payload(step, artifact, case, status, blocking, warnings, valuation_values)
            if step == "mandat-intake" and artifact == "conflit_interets.json":
                p["conflit_detecte"] = True
                p["conflit_motif"] = "Test: conflit injecte"
            return p

        engine._artifact_payload = patched_payload

        with pytest.raises(PipelineConflitError, match="Test: conflit injecte"):
            engine.run_case_data(case, tmp_path, source_fixture="test", case_stem="test", case_subdir=True)

    def test_pipeline_no_exception_when_conflit_false(self, tmp_path):
        """run_case_data runs normally when conflit_detecte: False."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import RuntimeEngine, DEFAULT_STEPS

        engine = RuntimeEngine(steps=DEFAULT_STEPS[:1])
        case = {
            "dossier_id": "D-GATE-OK-TEST",
            "type_bien": "residentiel_unifamilial",
            "date_reference": "2026-05-13",
            "mandat_type": "residentiel_standard",
            "format_rapport": "abrege",
        }
        result = engine.run_case_data(case, tmp_path, source_fixture="test", case_stem="test", case_subdir=True)
        assert result["dossier_id"] == "D-GATE-OK-TEST"


# ── TestConflit_ForceOverride ─────────────────────────────────────────────────

class TestConflit_ForceOverride:
    def test_force_conflit_continue_bypasses_gate(self, tmp_path):
        """force_conflit_continue: True lets pipeline continue despite conflit_detecte."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import RuntimeEngine, DEFAULT_STEPS

        engine = RuntimeEngine(steps=DEFAULT_STEPS[:1])
        case = {
            "dossier_id": "D-OVERRIDE-TEST",
            "type_bien": "residentiel_unifamilial",
            "date_reference": "2026-05-13",
            "mandat_type": "residentiel_standard",
            "format_rapport": "abrege",
            "force_conflit_continue": True,
        }

        original_payload = engine._artifact_payload

        def patched_payload(step, artifact, case, status, blocking, warnings, valuation_values=None):
            p = original_payload(step, artifact, case, status, blocking, warnings, valuation_values)
            if step == "mandat-intake" and artifact == "conflit_interets.json":
                p["conflit_detecte"] = True
                p["conflit_motif"] = "Test: conflit injecte"
            return p

        engine._artifact_payload = patched_payload

        # Should NOT raise — override is set
        result = engine.run_case_data(case, tmp_path, source_fixture="test", case_stem="test", case_subdir=True)
        assert result["dossier_id"] == "D-OVERRIDE-TEST"
```

- [x] **Step 2: Run tests — expect failures**

```bash
cd /c/Users/simon/eval-immo/backend && python -m pytest tests/test_pure.py::TestCommanditaireInCase tests/test_pure.py::TestLettreMandat_Commanditaire tests/test_pure.py::TestConflit_Deterministic_False tests/test_pure.py::TestConflit_Gate_Blocks tests/test_pure.py::TestConflit_ForceOverride -v 2>&1 | tail -30
```

Expected: Multiple FAILED — `load_case_from_body` not merging commanditaire, `PipelineConflitError` not importable, lettre_mandat using `[COMMANDITAIRE]` placeholder.

- [x] **Step 3: Commit tests**

```bash
cd /c/Users/simon/eval-immo && git add backend/tests/test_pure.py && git commit -m "test(batch5): add 10 failing tests for commanditaire + conflit gate"
```

---

### Task 2: runtime.py — PipelineConflitError + LLM conflit + lettre_mandat commanditaire

**Files:**
- Modify: `backend/engine/runtime.py`

**Security flag:** `none`

**Does NOT cover:** LLM-triggered conflit (no OPENAI_API_KEY in tests) — gate is tested via monkeypatching `_artifact_payload`.

- [ ] **Step 1: Add `PipelineConflitError` class**

After line 54 (the closing `}` of the `_STATUS_FROM_CONTRACTS` dict or any top-level dict before class `RuntimeEngine`), add the new exception class. Insert before the line `CONTRACTS_DATA_PATH = Path(...)` (line 57):

In `backend/engine/runtime.py`, find the section around line 55-57 and add:

```python
class PipelineConflitError(ValueError):
    """Raised when a conflict of interest is detected and the pipeline must stop."""
    pass
```

Insert this class definition after the top-level constants but before `CONTRACTS_DATA_PATH`. The exact insertion point: after the closing `}` of the dict at line 55, before `CONTRACTS_DATA_PATH` at line 57.

- [ ] **Step 2: Add `"conflit_interets.json": "analyse_conflit"` to `_LLM_TEXT_FIELD_BY_ARTIFACT`**

In `backend/engine/runtime.py`, find `_LLM_TEXT_FIELD_BY_ARTIFACT` (lines 60-75). Add the new entry after `"lettre_mandat.md": "_raw_md",`:

Replace:
```python
    "lettre_mandat.md": "_raw_md",
    # brouillon_rapport.md : géré par generate_brouillon_rapport — ne pas dupliquer
}
```

With:
```python
    "lettre_mandat.md": "_raw_md",
    "conflit_interets.json": "analyse_conflit",
    # brouillon_rapport.md : géré par generate_brouillon_rapport — ne pas dupliquer
}
```

- [ ] **Step 3: Add `_build_enrichment_prompt` block for `conflit_interets.json`**

In `backend/engine/runtime.py`, find the block for `lettre_mandat.md` in `_build_enrichment_prompt` (lines 301-315) and the `# Fallback générique` comment (line 317). Insert a new block BETWEEN the lettre_mandat block and the fallback.

Replace the closing of `lettre_mandat.md` block + fallback header:
```python
        "Ton professionnel, juridiction Quebec, references deontologiques OEAQ."
        )

    # Fallback générique
```

With:
```python
        "Ton professionnel, juridiction Quebec, references deontologiques OEAQ."
        )

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

    # Fallback générique
```

- [ ] **Step 4: Add `CONFLIT_DETECTE:` detection in `_enrich_artifact_llm`**

In `backend/engine/runtime.py`, find `_enrich_artifact_llm` (lines 332-379). The current successful return is:
```python
            result = (resp.choices[0].message.content or "").strip()
            if result:
                return {**payload, target_field: result}
```

Replace those two lines with:
```python
            result = (resp.choices[0].message.content or "").strip()
            if result:
                if artifact == "conflit_interets.json" and result.startswith("CONFLIT_DETECTE:"):
                    first_line = result.split("\n")[0]
                    motif = first_line.replace("CONFLIT_DETECTE:", "").strip()
                    return {**payload, target_field: result, "conflit_detecte": True, "conflit_motif": motif}
                return {**payload, target_field: result}
```

- [ ] **Step 5: Add `analyse_conflit` field to the deterministic `conflit_interets.json` payload**

In `backend/engine/runtime.py`, find `_artifact_payload` for `conflit_interets.json` (lines 538-543):
```python
        if step == "mandat-intake" and artifact == "conflit_interets.json":
            payload.update({
                "conflit_detecte": False,
                "verification_completee": True,
                "commentaire": "Aucun conflit d'interets detecte — verification V0 deterministe.",
            })
```

Replace with:
```python
        if step == "mandat-intake" and artifact == "conflit_interets.json":
            payload.update({
                "source_fixture": "",  # will be overwritten by run_case_data
                "conflit_detecte": False,
                "verification_completee": True,
                "commentaire": "Aucun conflit d'interets detecte — verification V0 deterministe.",
                "analyse_conflit": "",
            })
```

Wait — `source_fixture` is added by `run_case_data` after `_artifact_payload`. Don't add it here. Just add `"analyse_conflit": ""` as the LLM target field:

```python
        if step == "mandat-intake" and artifact == "conflit_interets.json":
            payload.update({
                "conflit_detecte": False,
                "verification_completee": True,
                "commentaire": "Aucun conflit d'interets detecte — verification V0 deterministe.",
                "analyse_conflit": "",
            })
```

- [ ] **Step 6: Update `lettre_mandat.md` payload to use `case["commanditaire"]`**

In `backend/engine/runtime.py`, find the `if step == "mandat-intake" and artifact == "lettre_mandat.md":` block (lines 545-569). Replace the entire block:

```python
        if step == "mandat-intake" and artifact == "lettre_mandat.md":
            type_bien = str(case.get("type_bien", "inconnu")).replace("_", " ")
            mandat_type = str(case.get("mandat_type", "residentiel_standard"))
            format_rapport = str(case.get("format_rapport", "abrege"))
            date_ref = case.get("date_reference", "—")
            dossier_id = case.get("dossier_id", "—")
            commanditaire = case.get("commanditaire", {})
            nom_cmd = str(commanditaire.get("nom", "[COMMANDITAIRE]")) if commanditaire else "[COMMANDITAIRE]"
            org_cmd = str(commanditaire.get("organisation", "")) if commanditaire else ""
            cmd_label = f"{nom_cmd} — {org_cmd}" if org_cmd else nom_cmd
            fin_eval = str(commanditaire.get("fin_evaluation", "non specifie")).replace("_", " ") if commanditaire else "non specifie"
            payload["_raw_md"] = (
                f"# Lettre de mandat\n\n"
                f"**Dossier :** {dossier_id}  \n"
                f"**Type de bien :** {type_bien}  \n"
                f"**Type de mandat :** {mandat_type}  \n"
                f"**Format du rapport :** {format_rapport}  \n"
                f"**Date de référence :** {date_ref}\n\n"
                f"## Identification du bien\n\n"
                f"Bien de type {type_bien} tel que décrit dans le dossier {dossier_id}.\n\n"
                f"## Identification du commanditaire\n\n"
                f"Commanditaire : {cmd_label}\n\n"
                f"## Type d'acte professionnel\n\n"
                f"Évaluation immobilière — rapport {format_rapport}.\n\n"
                f"## Fin d'évaluation\n\n"
                f"Mandat de type {mandat_type} — fin : {fin_eval}.\n\n"
                f"## Honoraires et conditions\n\n"
                f"À confirmer selon entente avec le commanditaire.\n\n"
                f"## Signatures\n\n"
                f"_Évaluateur agréé (É.A.) — signature requise_  \n"
                f"_Commanditaire — signature requise_\n"
            )
```

- [ ] **Step 7: Add gate in `run_case_data` after mandat-intake step**

In `backend/engine/runtime.py`, find `run_case_data` loop (around lines 680-748). After the inner `for artifact in step.writes:` loop and `self._record_event(events, audit_log_path, {"event": "step_done", ...})`, add the gate.

Find this exact sequence:
```python
            self._record_event(events, audit_log_path, {"event": "step_done", "step": step.name, "dossier_id": dossier_id})

            review_status = _status_from_contracts(has_blocking=True, has_warnings=bool(warnings))
```

Replace with:
```python
            self._record_event(events, audit_log_path, {"event": "step_done", "step": step.name, "dossier_id": dossier_id})

            # Gate conflit après mandat-intake
            if step.name == "mandat-intake":
                if case_subdir:
                    _conflit_path = case_dir / f"mandat-intake.conflit_interets.json"
                else:
                    _conflit_path = case_dir / f"{case_key}.mandat-intake.conflit_interets.json"
                if _conflit_path.exists():
                    _conflit = json.loads(_conflit_path.read_text(encoding="utf-8"))
                    if _conflit.get("conflit_detecte") and not case.get("force_conflit_continue"):
                        motif = _conflit.get("conflit_motif", "Conflit detecte par analyse mandat-intake")
                        raise PipelineConflitError(motif)

            review_status = _status_from_contracts(has_blocking=True, has_warnings=bool(warnings))
```

- [ ] **Step 8: Run the 5 new test classes**

```bash
cd /c/Users/simon/eval-immo/backend && python -m pytest tests/test_pure.py::TestCommanditaireInCase tests/test_pure.py::TestLettreMandat_Commanditaire tests/test_pure.py::TestConflit_Deterministic_False tests/test_pure.py::TestConflit_Gate_Blocks tests/test_pure.py::TestConflit_ForceOverride -v 2>&1 | tail -40
```

Expected: Most new tests PASS. `TestCommanditaireInCase` still FAILS (needs api.py change).

- [ ] **Step 9: Run existing 67 tests — verify no regression**

```bash
cd /c/Users/simon/eval-immo/backend && python -m pytest tests/test_pure.py -v 2>&1 | tail -20
```

Expected: 67 existing tests still PASS (new ones may still fail).

- [ ] **Step 10: Commit**

```bash
cd /c/Users/simon/eval-immo && git add backend/engine/runtime.py && git commit -m "feat(batch5): runtime.py — PipelineConflitError, LLM conflit prompt, gate, lettre_mandat commanditaire"
```

---

### Task 3: api.py — commanditaire injection + PipelineConflitError catch + conflit exposition

**Files:**
- Modify: `backend/api.py`

**Security flag:** `none`

**Does NOT cover:** Commanditaire validation against a real conflict registry — V0 is LLM heuristic only.

- [ ] **Step 1: Update import in api.py for PipelineConflitError**

In `backend/api.py`, find the line that imports from `engine.runtime`:

```bash
grep -n "from engine.runtime import" /c/Users/simon/eval-immo/backend/api.py
```

Find the import line (e.g., `from engine.runtime import RuntimeEngine`) and add `PipelineConflitError`:

Replace (exact line may vary — check with grep):
```python
from engine.runtime import RuntimeEngine
```

With:
```python
from engine.runtime import RuntimeEngine, PipelineConflitError
```

- [ ] **Step 2: Update `load_case_from_body()` to merge commanditaire**

In `backend/api.py`, find `load_case_from_body`. Locate where the fixture is loaded and case is built. Add commanditaire injection after the case dict is constructed. Find the function and add after the fixture loading:

```bash
grep -n "def load_case_from_body" /c/Users/simon/eval-immo/backend/api.py
```

Read the function body and add at the end, before the return statement:

```python
    # Injecter commanditaire dans le case si fourni dans le body
    if body.get("commanditaire") and isinstance(body["commanditaire"], dict):
        _cmd = body["commanditaire"]
        case["commanditaire"] = {
            "nom": str(_cmd.get("nom", "") or "[COMMANDITAIRE]") or "[COMMANDITAIRE]",
            "organisation": str(_cmd.get("organisation", "") or ""),
            "fin_evaluation": str(_cmd.get("fin_evaluation", "") or "non_specifie"),
        }

    return case, source_fixture
```

**Note:** The actual insertion depends on the current function structure. Read the function first with `grep -n` then insert at the correct location before `return case, source_fixture`.

- [ ] **Step 3: Update `app_start_demo()` to pass commanditaire**

In `backend/api.py`, find `app_start_demo` (line 915). Replace:

```python
def app_start_demo(body: dict) -> dict:
    fixture = str(body.get("fixture") or APP_DEFAULT_FIXTURE)
    started = start_runtime({"fixture": fixture, "strict_mode": True})
```

With:

```python
def app_start_demo(body: dict) -> dict:
    fixture = str(body.get("fixture") or APP_DEFAULT_FIXTURE)
    runtime_body: dict = {"fixture": fixture, "strict_mode": True}
    if body.get("commanditaire") and isinstance(body["commanditaire"], dict):
        runtime_body["commanditaire"] = body["commanditaire"]
    started = start_runtime(runtime_body)
```

- [ ] **Step 4: Catch `PipelineConflitError` in `start_runtime()`**

In `backend/api.py`, find the `result = engine.run_case_data(...)` call in `start_runtime()` (lines 1178-1184). Wrap it:

Replace:
```python
    result = engine.run_case_data(
        case,
        session_dir / "artifacts",
        source_fixture=source_fixture,
        case_stem=case_key,
        case_subdir=True,
    )
```

With:
```python
    try:
        result = engine.run_case_data(
            case,
            session_dir / "artifacts",
            source_fixture=source_fixture,
            case_stem=case_key,
            case_subdir=True,
        )
    except PipelineConflitError as _e:
        result = {
            "dossier_id": case.get("dossier_id", ""),
            "status": "CONFLIT_DETECTE",
            "blocking_failures": [f"CONFLIT: {_e}"],
            "warnings": [],
            "events": [],
            "artifact_dir": str(session_dir / "artifacts"),
        }
```

- [ ] **Step 5: Expose `conflit` in `app_session_view()`**

In `backend/api.py`, find `app_session_view` (line 815). After the line `summary = session_summary(session_id)`, add artifact_index loading:

After `summary = session_summary(session_id)` (first line of the function body), add:

```python
    _artifact_index = session_artifacts(session_id)
    _conflit_data = read_artifact_json_from_index(
        summary.get("session", {}), _artifact_index, "mandat-intake", "conflit_interets.json"
    )
```

Then, in the `return {` dict at the end of `app_session_view` (around line 845), add `"conflit"` field after `"mandat"`:

```python
        "conflit": {
            "detecte": bool(_conflit_data.get("conflit_detecte", False)),
            "motif": str(_conflit_data.get("conflit_motif", _conflit_data.get("commentaire", ""))),
        } if _conflit_data else None,
```

- [ ] **Step 6: Run new tests — all should pass now**

```bash
cd /c/Users/simon/eval-immo/backend && python -m pytest tests/test_pure.py::TestCommanditaireInCase tests/test_pure.py::TestLettreMandat_Commanditaire tests/test_pure.py::TestConflit_Deterministic_False tests/test_pure.py::TestConflit_Gate_Blocks tests/test_pure.py::TestConflit_ForceOverride -v 2>&1 | tail -40
```

Expected: All 10 new tests PASS.

- [ ] **Step 7: Run full test suite — all 72 tests pass**

```bash
cd /c/Users/simon/eval-immo/backend && python -m pytest tests/test_pure.py -v 2>&1 | tail -20
```

Expected: 72 tests PASS, 0 failed.

- [ ] **Step 8: Commit**

```bash
cd /c/Users/simon/eval-immo && git add backend/api.py && git commit -m "feat(batch5): api.py — commanditaire injection, PipelineConflitError catch, conflit exposition"
```

---

### Task 4: TypeScript — runtime-api.ts + dossiers.ts

**Files:**
- Modify: `src/lib/runtime-api.ts`
- Modify: `src/lib/supabase/queries/dossiers.ts`

**Security flag:** `none`

**Does NOT cover:** TypeScript type checking of commanditaire server response — server returns untyped JSON.

- [ ] **Step 1: Add `commanditaire` to `CreateRuntimeDossierInput` in runtime-api.ts**

In `src/lib/runtime-api.ts`, find (lines 57-61):

```typescript
export interface CreateRuntimeDossierInput {
  address: string
  property_type: string
  neighborhood: string
}
```

Replace with:

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

- [ ] **Step 2: Add `conflit` to `AppState.active` in runtime-api.ts**

In `src/lib/runtime-api.ts`, find the `mandat` field in `AppState.active` (lines 14-19):

```typescript
    mandat: {
      mandat_type: string
      format_rapport: string
      methodes_requises: string[]
      methode_preponderante: string
    } | null
```

Add `conflit` field directly after `mandat`:

```typescript
    mandat: {
      mandat_type: string
      format_rapport: string
      methodes_requises: string[]
      methode_preponderante: string
    } | null
    conflit: {
      detecte: boolean
      motif: string
    } | null
```

- [ ] **Step 3: Pass `commanditaire` in `createRuntimeDossier` POST body**

In `src/lib/runtime-api.ts`, find `createRuntimeDossier` (lines 116-129). Replace the body:

```typescript
export async function createRuntimeDossier(input: CreateRuntimeDossierInput): Promise<Dossier> {
  const payload = await runtimeJson<{ state: AppState }>('/app/demo', {
    method: 'POST',
    body: JSON.stringify({
      fixture: 'case_pilote_residentiel_standard.json',
      display_name: input.address,
      property_type: input.property_type,
      neighborhood: input.neighborhood,
    }),
  })
```

With:

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
    }),
  })
```

- [ ] **Step 4: No change needed in dossiers.ts**

`dossiers.ts` already re-exports `CreateDossierInput = CreateRuntimeDossierInput` (line 5) and passes `input` directly to `createRuntimeDossier(input)` (line 60). Adding `commanditaire` to `CreateRuntimeDossierInput` automatically flows through. No changes needed.

- [ ] **Step 5: Verify TypeScript compiles**

```bash
cd /c/Users/simon/eval-immo && npx tsc --noEmit 2>&1 | head -30
```

Expected: No errors (or only pre-existing unrelated errors).

- [ ] **Step 6: Commit**

```bash
cd /c/Users/simon/eval-immo && git add src/lib/runtime-api.ts && git commit -m "feat(batch5): runtime-api.ts — commanditaire in CreateRuntimeDossierInput, conflit in AppState"
```

---

### Task 5: DossierPanel.tsx — 2-step form + conflict banner

**Files:**
- Modify: `src/components/panels/DossierPanel.tsx`

**Security flag:** `none`

**Does NOT cover:** Step 1 field validation beyond `required` attribute; commanditaire org is optional by design.

- [ ] **Step 1: Convert `NewDossierForm` to 2-step form**

Replace the entire `NewDossierForm` function (lines 44-191) with:

```tsx
const FIN_EVAL_OPTIONS = [
  { value: 'hypothecaire', label: 'Hypothécaire / financement' },
  { value: 'succession', label: 'Succession / liquidation' },
  { value: 'litige', label: 'Litige judiciaire' },
  { value: 'assurance', label: 'Valeur assurable' },
  { value: 'commercial', label: 'Investissement commercial' },
  { value: 'expropriation', label: 'Expropriation' },
  { value: 'autre', label: 'Autre' },
]

function NewDossierForm() {
  const router = useRouter()
  const [formStep, setFormStep] = useState<1 | 2>(1)
  const [address, setAddress] = useState('Dossier pilote residentiel')
  const [propertyType, setPropertyType] = useState('Residentiel unifamilial')
  const [neighborhood, setNeighborhood] = useState('Zone anonymisee')
  const [cmdNom, setCmdNom] = useState('')
  const [cmdOrg, setCmdOrg] = useState('')
  const [cmdFin, setCmdFin] = useState('hypothecaire')
  const [loading, setLoading] = useState(false)
  const [stepIndex, setStepIndex] = useState(0)
  const [error, setError] = useState('')
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([])

  useEffect(() => {
    return () => timersRef.current.forEach(clearTimeout)
  }, [])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!address.trim() || !propertyType.trim() || !neighborhood.trim()) return
    if (!cmdNom.trim()) return
    setLoading(true)
    setStepIndex(0)
    setError('')

    LAUNCH_STEPS.forEach((step, i) => {
      if (i === 0) return
      const t = setTimeout(() => setStepIndex(i), step.delay)
      timersRef.current.push(t)
    })

    try {
      const dossier = await createDossier({
        address: address.trim(),
        property_type: propertyType.trim(),
        neighborhood: neighborhood.trim(),
        commanditaire: {
          nom: cmdNom.trim(),
          organisation: cmdOrg.trim(),
          fin_evaluation: cmdFin,
        },
      })
      router.push(`/dossier/${dossier.slug}?tab=dossier`)
    } catch (err) {
      timersRef.current.forEach(clearTimeout)
      timersRef.current = []
      setError(err instanceof Error ? err.message : 'Erreur lors de la creation du dossier.')
      setLoading(false)
    }
  }

  const inputStyle = {
    background: 'var(--input-bg)',
    border: '1px solid var(--input-border)',
  }

  const selectStyle = {
    background: 'var(--input-bg)',
    border: '1px solid var(--input-border)',
    appearance: 'none' as const,
    WebkitAppearance: 'none' as const,
  }

  return (
    <div className="w-full max-w-[520px] flex flex-col gap-6 pb-9">
      <div className="text-center">
        <div
          className="text-[20px] font-medium text-[#1a1916] tracking-[-.01em]"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          Nouveau dossier
        </div>
        <p className="mt-1 text-[13px] text-[#8a8780]">
          {formStep === 1
            ? 'Lance un dossier pilote dans le backend runtime et ouvre les agents AI.'
            : 'Identifiez le commanditaire du mandat.'}
        </p>
      </div>

      {error && (
        <div className="rounded-[10px] px-4 py-3 text-[13px] text-red-700 bg-red-50/80 border border-red-200/60">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex flex-col gap-3 py-2">
          <div className="w-full h-[3px] rounded-full overflow-hidden" style={{ background: 'var(--input-bg)' }}>
            <div
              className="h-full rounded-full transition-all duration-700 ease-out"
              style={{
                background: '#334155',
                width: `${Math.round(((stepIndex + 1) / LAUNCH_STEPS.length) * 100)}%`,
              }}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            {LAUNCH_STEPS.map((step, i) => (
              <div
                key={i}
                className="flex items-center gap-2 text-[13px] transition-opacity duration-300"
                style={{ opacity: i <= stepIndex ? 1 : 0.28 }}
              >
                <span style={{ color: i < stepIndex ? '#334155' : i === stepIndex ? '#334155' : '#b5b2ac' }}>
                  {i < stepIndex ? '✓' : i === stepIndex ? '›' : '·'}
                </span>
                <span style={{ color: i === stepIndex ? '#1a1916' : i < stepIndex ? '#8a8780' : '#b5b2ac' }}>
                  {step.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : formStep === 1 ? (
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-[12px] text-[#8a8780] font-medium">Nom du dossier</label>
            <input
              type="text"
              required
              value={address}
              onChange={e => setAddress(e.target.value)}
              className="w-full rounded-[10px] px-4 py-2.5 text-[14px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
              style={inputStyle}
            />
          </div>

          <div className="flex gap-3">
            <div className="flex flex-col gap-1.5 flex-1">
              <label className="text-[12px] text-[#8a8780] font-medium">Type</label>
              <input
                type="text"
                required
                value={propertyType}
                onChange={e => setPropertyType(e.target.value)}
                className="w-full rounded-[10px] px-4 py-2.5 text-[14px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
                style={inputStyle}
              />
            </div>
            <div className="flex flex-col gap-1.5 flex-1">
              <label className="text-[12px] text-[#8a8780] font-medium">Secteur</label>
              <input
                type="text"
                required
                value={neighborhood}
                onChange={e => setNeighborhood(e.target.value)}
                className="w-full rounded-[10px] px-4 py-2.5 text-[14px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
                style={inputStyle}
              />
            </div>
          </div>

          <button
            type="button"
            onClick={() => {
              if (address.trim() && propertyType.trim() && neighborhood.trim()) {
                setFormStep(2)
              }
            }}
            className="mt-1 w-full rounded-[10px] py-2.5 text-[14px] font-medium text-white transition-opacity hover:opacity-90 active:opacity-80"
            style={{ background: '#334155' }}
          >
            Suivant →
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-[12px] text-[#8a8780] font-medium">Nom du commanditaire <span className="text-red-500">*</span></label>
            <input
              type="text"
              required
              placeholder="ex. Banque Nationale"
              value={cmdNom}
              onChange={e => setCmdNom(e.target.value)}
              className="w-full rounded-[10px] px-4 py-2.5 text-[14px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
              style={inputStyle}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-[12px] text-[#8a8780] font-medium">Organisation <span className="text-[#b5b2ac]">(optionnel)</span></label>
            <input
              type="text"
              placeholder="ex. Financement immobilier"
              value={cmdOrg}
              onChange={e => setCmdOrg(e.target.value)}
              className="w-full rounded-[10px] px-4 py-2.5 text-[14px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
              style={inputStyle}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-[12px] text-[#8a8780] font-medium">Fin d&apos;évaluation</label>
            <select
              value={cmdFin}
              onChange={e => setCmdFin(e.target.value)}
              className="w-full rounded-[10px] px-4 py-2.5 text-[14px] text-[#1a1916] outline-none"
              style={selectStyle}
            >
              {FIN_EVAL_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div className="flex gap-2 mt-1">
            <button
              type="button"
              onClick={() => setFormStep(1)}
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
              Lancer le dossier
            </button>
          </div>
        </form>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Add conflict banner in `DossierPanel`**

In `src/components/panels/DossierPanel.tsx`, find the `DossierPanel` component. Add `conflit` to the state declarations alongside `mandat`:

After:
```tsx
  const [mandat, setMandat] = useState<MandatData>(null)
```

Add:
```tsx
  type ConflitData = { detecte: boolean; motif: string } | null
  const [conflit, setConflitData] = useState<ConflitData>(null)
```

In the `useEffect` that fetches app state, after `setMandat(appState.active?.mandat ?? null)`:

```tsx
      setConflitData(appState.active?.conflit ?? null)
```

In the JSX return, add the conflict banner BEFORE the chips AgentMessage (before `{chips.length > 0 && (`). Add:

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

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd /c/Users/simon/eval-immo && npx tsc --noEmit 2>&1 | head -30
```

Expected: No new errors.

- [ ] **Step 4: Commit**

```bash
cd /c/Users/simon/eval-immo && git add src/components/panels/DossierPanel.tsx && git commit -m "feat(batch5): DossierPanel — 2-step commanditaire form + conflict banner"
```

---

### Task 6: Final verification

**Files:**
- Test: `backend/tests/test_pure.py`

**Security flag:** `none`

**Does NOT cover:** End-to-end browser test of the 2-step form — no Playwright test exists for DossierPanel.

- [ ] **Step 1: Run full test suite**

```bash
cd /c/Users/simon/eval-immo/backend && python -m pytest tests/test_pure.py -v 2>&1
```

Expected: **72 tests PASS**, 0 failed.

Output should end with:
```
============================== 72 passed in ...s ==============================
```

- [ ] **Step 2: Verify new test classes are all represented**

```bash
cd /c/Users/simon/eval-immo/backend && python -m pytest tests/test_pure.py -v 2>&1 | grep -E "TestCommanditaire|TestLettreMandat_C|TestConflit"
```

Expected: 10 lines, all PASSED.

- [ ] **Step 3: TypeScript final check**

```bash
cd /c/Users/simon/eval-immo && npx tsc --noEmit 2>&1 | head -20
```

Expected: No new errors from Batch 5 changes.

- [ ] **Step 4: Update state.md**

Update `state.md` at project root:

```markdown
# State

## Current Goal
Batch 5 terminé. En attente review utilisateur avant Batch 6.

## Decisions
- Batch 5 livré : commanditaire 2-step form + LLM conflit + gate pipeline
- Roadmap : Batch 6 (ingestion-docs) → 7 (registre) → 8 (enrichissement) → 9 (frontend pipeline view) → 10 (admin-package PDF)

## Plan Status
- Batch 1 (AGENTCONFIG×5 + SKILL.md×20 + LLM enrichment): DONE ✓
- Batch 2 (classify_dossier + PLANS-MANDATS + PlanOrchestrator): DONE ✓
- Batch 3 (AMU agent + pipeline 5→6 + orchestrator wiring + build-eval-skill): DONE ✓
- Batch 4 (mandat-intake + FTA skill + frontend): DONE ✓
- Batch 5 (commanditaire form + LLM conflit + gate): DONE ✓
- Batch 6: plan NON encore écrit

## Evidence
- 72 tests pass
- Pipeline : mandat-intake(1) → data-facts(2) → amu-analyst(3) → comps-market(4) → valuation-draft(5) → compliance-qa(6) → redaction(7)
- Gate conflit actif après mandat-intake : PipelineConflitError → status CONFLIT_DETECTE

## Open Issues
- APIs Batch 7 (DLC, Centris, MRNF) — user travaille à les obtenir
```

- [ ] **Step 5: Commit state**

```bash
cd /c/Users/simon/eval-immo && git add state.md && git commit -m "chore: update state.md — Batch 5 complete, 72 tests pass"
```

---

## Self-Review

**Spec coverage:**
- ✓ Task 1: `conflit_interets.json` LLM field (`analyse_conflit`) — R1 covered in Task 2 Step 2
- ✓ Task 2: `_build_enrichment_prompt` for `conflit_interets.json` — R2 covered in Task 2 Step 3
- ✓ Task 3: `CONFLIT_DETECTE:` detection in `_enrich_artifact_llm` — R3 covered in Task 2 Step 4
- ✓ Task 4: `PipelineConflitError` + gate in `run_case_data` — R4 covered in Task 2 Steps 1+7
- ✓ Task 5: `lettre_mandat.md` uses real commanditaire nom — covered in Task 2 Step 6
- ✓ Task 6: `load_case_from_body` merges commanditaire — A2 covered in Task 3 Step 2
- ✓ Task 7: `app_start_demo` passes commanditaire — A1/A3 covered in Task 3 Steps 1+3
- ✓ Task 8: `start_runtime` catches `PipelineConflitError` — A3 covered in Task 3 Step 4
- ✓ Task 9: `app_session_view` exposes `conflit` — A4 covered in Task 3 Step 5
- ✓ Task 10: `CreateRuntimeDossierInput` + `AppState.active.conflit` — covered in Task 4
- ✓ Task 11: `NewDossierForm` 2-step — covered in Task 5 Step 1
- ✓ Task 12: Conflict banner in `DossierPanel` — covered in Task 5 Step 2
- ✓ All 5 test classes — covered in Task 1

**Type consistency:**
- `PipelineConflitError` defined in Task 2 Step 1, imported in Task 3 Step 1 — consistent.
- `conflit` field: Python dict `{"detecte": bool, "motif": str}` in Task 3 Step 5 matches TypeScript `{ detecte: boolean; motif: string } | null` in Task 4 Step 2.
- `commanditaire` dict shape consistent: `{nom, organisation, fin_evaluation}` used identically in Python (Task 2 Step 6, Task 3 Step 2) and TypeScript (Task 4 Step 1).

**Placeholder scan:** None found.
