# Batch 8a — Rapport éditeur Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-optimized:subagent-driven-development (recommended) or superpowers-optimized:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Afficher, éditer et sauvegarder le brouillon de rapport dans un éditeur TipTap WYSIWYG depuis le panneau Rapport, avec régénération LLM améliorée (CUSPAP, formes abrégée/complète).

**Architecture:** `report.preview` (contenu `brouillon_rapport.md`) est déjà dans AppState via `dossier_review_summary()`. `RapportPanel` passe le texte à `RapportDoc`, qui branche sur `RapportEditor` (TipTap) si le texte est présent. L'éditeur convertit MD→HTML à l'import (marked) et HTML→MD à la sauvegarde (turndown). Deux nouveaux endpoints backend: `POST /app/report` (save) et `POST /app/report/generate` (régénération LLM avec format).

**Tech Stack:** Python 3.11 (backend), Next.js/React/TypeScript (frontend), TipTap v2, marked v12, turndown v7, pytest

**Assumptions:**
- Assumes `dossierId` côté frontend = `session_id` côté backend — ne fonctionnera pas si les IDs divergent.
- Assumes `find_artifact_record(session, "redaction", "brouillon_rapport.md")` retourne un enregistrement avec un `path` valide — ne fonctionnera pas si le pipeline n'a pas encore produit cet artefact.
- Assumes TipTap v2.10+ — l'API `StarterKit` et les extensions table sont stables; à revalider si version majeure change.
- Assumes `marked@12` retourne `string` synchrone depuis `marked.parse()` — ne fonctionnera pas si mode async activé.

---

## File Structure

| Fichier | Action | Responsabilité |
|---------|--------|----------------|
| `backend/engine/runtime.py` | Modify | `_build_rapport_prompt_v2`, `_RAPPORT_SYSTEM_PROMPT_ABREGE`, `_RAPPORT_SYSTEM_PROMPT_COMPLET`, `_RAPPORT_MAX_TOKENS` 4000, `generate_brouillon_rapport(format=)`, `_generate_rapport_llm(format=)` |
| `backend/api.py` | Modify | `app_save_rapport(body)`, `app_generate_rapport(body)`, routing `/app/report` + `/app/report/generate` |
| `backend/tests/test_pure.py` | Modify | 5 nouvelles classes de test |
| `src/lib/runtime-api.ts` | Modify | `saveRapport()`, `generateRapport()` |
| `src/components/shared/RapportEditor.tsx` | Create | TipTap editor WYSIWYG avec toolbar, save, generate |
| `src/components/shared/RapportDoc.tsx` | Modify | Prop `reportText?`, branche vers `RapportEditor` si présent |
| `src/components/panels/RapportPanel.tsx` | Modify | `reportText` dans `RapportState`, handlers save/generate, passe à `RapportDoc` |
| `package.json` | Modify | Ajouter TipTap + marked + turndown deps |

---

## Wave Plan

- **Wave 1:** Task 1 (tests TDD) + Task 4 (frontend API types) — fichiers disjoints
- **Wave 2:** Task 2 (runtime.py) + Task 7 (npm deps) — fichiers disjoints
- **Wave 3:** Task 3 (api.py endpoints, après Task 2) + Task 5 (RapportEditor, après Task 7) — parallèle
- **Wave 4:** Task 6 (wiring RapportDoc+Panel, après Tasks 3+4+5)
- **Wave 5:** Task 8 (vérification finale)

---

### Task 1: Backend tests (TDD)

**Files:**
- Test: `backend/tests/test_pure.py`

**Security flag:** `none`

**Does NOT cover:** Tests pour `app_save_rapport` avec vrai session (I/O) — nécessite tmp_path, couvert séparément ci-dessous. Ne teste pas le comportement avec OPENAI_API_KEY réelle (mock suffisant).

- [ ] **Step 1: Add failing tests**

Ajouter à la fin de `backend/tests/test_pure.py`:

```python
# ── TestBuildRapportPromptV2 ───────────────────────────────────────────────────

class TestBuildRapportPromptV2_IncludesCommanditaire:
    def test_commanditaire_nom_in_prompt(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import _build_rapport_prompt_v2
        case = {
            "dossier_id": "D-TEST",
            "commanditaire": {
                "nom": "Jean Tremblay",
                "organisation": "Banque XYZ",
                "fin_evaluation": "hypothecaire",
            },
            "date_reference": "2026-05-15",
            "type_bien": "residentiel_unifamilial",
            "zone": "R-1",
            "surface": {"value": 120, "unit": "m²"},
            "comparables": [],
        }
        prompt = _build_rapport_prompt_v2(case, "abrege", {}, "BROUILLON", [], [])
        assert "Jean Tremblay" in prompt

    def test_commanditaire_organisation_in_prompt(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import _build_rapport_prompt_v2
        case = {
            "commanditaire": {"nom": "Marie Côté", "organisation": "Caisse Pop", "fin_evaluation": "succession"},
        }
        prompt = _build_rapport_prompt_v2(case, "abrege", {}, "BROUILLON", [], [])
        assert "Caisse Pop" in prompt


class TestBuildRapportPromptV2_FormatAbrege:
    def test_format_abrege_label_in_prompt(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import _build_rapport_prompt_v2
        case = {"dossier_id": "D-TEST"}
        prompt = _build_rapport_prompt_v2(case, "abrege", {}, "BROUILLON", [], [])
        assert "abrege" in prompt.lower() or "abrégé" in prompt.lower()

    def test_format_abrege_not_complet(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import _build_rapport_prompt_v2
        case = {"dossier_id": "D-TEST"}
        prompt = _build_rapport_prompt_v2(case, "abrege", {}, "BROUILLON", [], [])
        assert "narratif complet" not in prompt.lower()


class TestBuildRapportPromptV2_FormatComplet:
    def test_format_complet_label_in_prompt(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import _build_rapport_prompt_v2
        case = {"dossier_id": "D-TEST"}
        prompt = _build_rapport_prompt_v2(case, "complet", {}, "BROUILLON", [], [])
        assert "complet" in prompt.lower() or "narratif" in prompt.lower()


class TestGenerateRapportFallbackNoCle:
    def test_returns_deterministic_string_without_api_key(self, monkeypatch):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import generate_brouillon_rapport
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        case = {
            "dossier_id": "D-TEST",
            "type_bien": "residentiel_unifamilial",
            "zone": "R-1",
            "date_reference": "2026-05-15",
            "surface": {"value": 120, "unit": "m²"},
            "comparables": [],
        }
        result = generate_brouillon_rapport(case, {}, "BROUILLON", [], [], format="abrege")
        assert isinstance(result, str)
        assert len(result) > 100
        assert "BROUILLON" in result

    def test_complet_format_also_returns_string(self, monkeypatch):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import generate_brouillon_rapport
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        case = {"dossier_id": "D-TEST", "type_bien": "immeuble_revenus"}
        result = generate_brouillon_rapport(case, {}, "BROUILLON", [], [], format="complet")
        assert isinstance(result, str)
        assert len(result) > 100


class TestSaveRapportContent:
    def test_writes_content_to_artifact_file(self, tmp_path, monkeypatch):
        """app_save_rapport écrase le fichier brouillon_rapport.md dans la session."""
        import sys, json
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        import api as api_module
        monkeypatch.setattr(api_module, "SESSIONS_DIR", tmp_path)

        session_id = "test-session-abc"
        session_dir = tmp_path / session_id
        session_dir.mkdir()
        artifacts_dir = session_dir / "artifacts" / "D-TEST"
        artifacts_dir.mkdir(parents=True)
        rapport_path = artifacts_dir / "redaction.brouillon_rapport.md"
        rapport_path.write_text("# Brouillon original\n", encoding="utf-8")

        artifact_index = {
            "artifacts": [
                {
                    "step": "redaction",
                    "artifact": "brouillon_rapport.md",
                    "event_id": "evt_001",
                    "path": str(rapport_path),
                }
            ]
        }
        (session_dir / "artifact_index.json").write_text(
            json.dumps(artifact_index), encoding="utf-8"
        )
        session_data = {
            "session_id": session_id,
            "session_dir": str(session_dir),
        }
        (session_dir / "session.json").write_text(
            json.dumps(session_data), encoding="utf-8"
        )

        result = api_module.app_save_rapport(
            {"session_id": session_id, "content": "# Contenu modifié\n\nTexte édité."}
        )
        assert result["ok"] is True
        assert rapport_path.read_text(encoding="utf-8") == "# Contenu modifié\n\nTexte édité."
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd C:\Users\simon\eval-immo\backend && python -m pytest tests/test_pure.py -k "TestBuildRapportPromptV2 or TestGenerateRapportFallbackNoCle or TestSaveRapportContent" -v 2>&1 | tail -25
```

Expected: FAIL — `ImportError: cannot import name '_build_rapport_prompt_v2'` et `AttributeError: module 'api' has no attribute 'app_save_rapport'`

- [ ] **Step 3: Commit placeholder (tests only)**

```bash
cd C:\Users\simon\eval-immo && git add backend/tests/test_pure.py && git commit -m "test(batch8a): TDD tests for rapport prompt v2, save endpoint, generate fallback"
```

---

### Task 2: Backend — Improved rapport generation (runtime.py)

**Files:**
- Modify: `backend/engine/runtime.py`

**Security flag:** `none`

**Does NOT cover:** Appel OpenAI avec vraie clé (testé end-to-end séparément). Ne modifie pas `_generate_rapport_deterministic` (conservé tel quel).

- [ ] **Step 1: Replace RAPPORT constants and improve functions**

Dans `backend/engine/runtime.py`, remplacer les lignes 1029-1048 (de `_RAPPORT_MAX_TOKENS = 2000` jusqu'à la fin de `_RAPPORT_SYSTEM_PROMPT`) par :

```python
_RAPPORT_MAX_TOKENS = 4000

_RAPPORT_SYSTEM_PROMPT_ABREGE = (
    "Tu es un expert en rédaction de rapports d'évaluation immobilière au Québec, conforme aux normes OEAQ/CUSPAP 2026.\n\n"
    "Génère un RAPPORT ABRÉGÉ (formulaire) professionnel en Markdown. Format cible : 5-6 pages, "
    "tous les 16 éléments obligatoires CUSPAP présents.\n\n"
    "STRUCTURE OBLIGATOIRE (rapport abrégé) :\n"
    "1. Identification — dossier, mandant, propriétaire, conclusion de valeur, but et fin\n"
    "2. Généralités — secteur, marché, données municipales, zonage\n"
    "3. Description — terrain, UMPP (analyse brève), bâtiment (généralités, composantes, finition)\n"
    "4. Approches de valeur — méthode du coût et/ou de comparaison (3-5 comparables avec ajustements)\n"
    "5. Réconciliation et attestation — jugement pondéré (jamais une moyenne), valeur en chiffres ET lettres\n"
    "6. Réserves et hypothèses — clauses standards OEAQ\n\n"
    "RÈGLES ABSOLUES :\n"
    "- BROUILLON NON CERTIFIÉ bien visible en tête\n"
    "- N'invente aucune donnée non fournie dans le prompt\n"
    "- Valeur finale en chiffres ET en lettres (ex: 475 000 $ (quatre cent soixante-quinze mille dollars))\n"
    "- Réconciliation = jugement professionnel pondéré, jamais une moyenne arithmétique\n"
    "- La méthode du coût ne peut servir aux fins d'assurance\n"
    "- Justifier tout rejet de méthode (élément 10 CUSPAP)\n"
    "- Langue : français canadien professionnel\n"
    "- Format : Markdown avec titres numérotés, tableaux pour comparables et ajustements\n"
)

_RAPPORT_SYSTEM_PROMPT_COMPLET = (
    "Tu es un expert en rédaction de rapports d'évaluation immobilière au Québec, conforme aux normes OEAQ/CUSPAP 2026.\n\n"
    "Génère un RAPPORT NARRATIF COMPLET en Markdown. Format cible : 15+ sections, "
    "tous les 16 éléments obligatoires CUSPAP.\n\n"
    "STRUCTURE OBLIGATOIRE (15 sections) :\n"
    "0. Lettre de transmission — client, objet, conclusion (chiffres + lettres), référence OEAQ\n"
    "1. Page titre — titre, adresse, référence, date\n"
    "2. Table des matières\n"
    "3. Identification de l'immeuble (éléments 1-5) — adresse, cadastre, droits évalués, but/fin, définition valeur, date référence, historique\n"
    "4. Étendue du travail (élément 6) — visite, collecte, recherches, analyses, vérifications\n"
    "5. Réserves et hypothèses (élément 7) — 11 clauses standard OEAQ + extraordinaires si applicable\n"
    "6. Informations générales — ville, secteur, marché, données municipales, zonage, infrastructures\n"
    "7. Description de l'immeuble (éléments 1, 8) — terrain, UMPP (élément 9), bâtiment (généralités, composantes, finition)\n"
    "8. Évaluation et analyse (éléments 10, 11) — présentation des 3 méthodes, justification retenues/rejetées\n"
    "9. Méthode du coût — terrain (comparables $/m²), coût neuf, dépréciations, conclusion\n"
    "10. Méthode de comparaison — tableau comparables, fiches détaillées, ajustements, taux, conclusion\n"
    "11. Méthode du revenu — RBP, vacance, RBE, frais, RNE, TGA, capitalisation, conclusion ou justification non-application\n"
    "12. Réconciliation (élément 13) — résultats, analyse chaque indication, méthode prépondérante, valeur finale\n"
    "13. Attestation (élément 12) — 7 déclarations OEAQ, inspection, conclusion chiffres+lettres, [SIGNATURE É.A.]\n"
    "14. Extrait NPP — éléments applicables\n"
    "15. Annexes (élément 16) — liste pièces jointes\n\n"
    "RÈGLES ABSOLUES :\n"
    "- BROUILLON NON CERTIFIÉ bien visible en tête ET à l'attestation\n"
    "- N'invente aucune donnée non fournie dans le prompt\n"
    "- Valeur finale en chiffres ET en lettres\n"
    "- Réconciliation = jugement professionnel pondéré, jamais une moyenne arithmétique\n"
    "- Attestation avec les 7 déclarations OEAQ (à signer par l'É.A.)\n"
    "- Justifier tout rejet de méthode (élément 10)\n"
    "- Langue : français canadien professionnel\n"
    "- Format : Markdown structuré avec titres numérotés\n"
)
```

- [ ] **Step 2: Replace `_build_rapport_prompt` with `_build_rapport_prompt_v2`**

Remplacer la fonction `_build_rapport_prompt` (lignes 1055-1092) par :

```python
def _build_rapport_prompt_v2(
    case: dict,
    format: str,
    valuation_values: dict,
    status: str,
    blocking: list,
    warnings: list,
) -> str:
    """Construit le prompt utilisateur enrichi pour la génération du rapport."""
    surface = case.get("surface", {})
    surface_str = (
        f"{surface.get('value', '—')} {surface.get('unit', 'm²')}"
        if isinstance(surface, dict)
        else str(surface or "—")
    )
    cmd = case.get("commanditaire", {}) if isinstance(case.get("commanditaire"), dict) else {}
    format_label = (
        "Rapport abrégé (formulaire)"
        if format == "abrege"
        else "Rapport narratif complet 15 sections CUSPAP"
    )
    comp_lines = []
    for i, c in enumerate(case.get("comparables", [])[:5], 1):
        price = c.get("prix_vente") or c.get("sale_price")
        price_str = _fmt_cad(float(price)) if price else "—"
        score = c.get("score", "—")
        score_str = f"{float(score):.2f}" if isinstance(score, (int, float)) else str(score)
        comp_lines.append(
            f"  {i}. source={c.get('source_id', '—')} | adresse={c.get('adresse', '—')} | "
            f"prix={price_str} | date={c.get('date_vente', '—')} | score={score_str}"
        )
    approach_lines = []
    labels = {
        "approche_comparative": "Approche comparative",
        "approche_cout": "Approche par le coût",
        "approche_revenu": "Approche par le revenu",
    }
    for key, label in labels.items():
        if key in valuation_values:
            approach_lines.append(f"  - {label} : {_fmt_cad(valuation_values[key])}")
    lines = [
        f"FORMAT: {format} — {format_label}",
        f"DOSSIER: {case.get('dossier_id', '—')}",
        f"COMMANDITAIRE: {cmd.get('nom', '—')} — {cmd.get('organisation', '—')}",
        f"FIN ÉVALUATION: {cmd.get('fin_evaluation', '—')}",
        f"TYPE MANDAT: {case.get('mandat_type', case.get('type_bien', '—'))}",
        f"DATE RÉFÉRENCE: {case.get('date_reference', '—')}",
        "",
        "IDENTIFICATION:",
        f"  Adresse: {case.get('adresse', case.get('display_name', '—'))}",
        f"  Type de bien: {case.get('type_bien', '—')}",
        f"  Zone / secteur: {case.get('zone', '—')}",
        f"  Surface habitable: {surface_str}",
        f"  Surface terrain: {case.get('surface_terrain', '—')} m²",
        f"  Année construction: {case.get('annee_construction', '—')}",
        f"  Nb logements: {case.get('nb_logements', '—')}",
        "",
        f"APPROCHES DE VALEUR ({len(approach_lines)}):",
        *approach_lines,
        "",
        f"COMPARABLES RETENUS ({len(case.get('comparables', []))}):",
        *comp_lines,
        "",
        f"STATUT CONFORMITÉ: {status}",
    ]
    if blocking:
        lines += [f"BLOCAGES ({len(blocking)}): " + "; ".join(str(b) for b in blocking[:3])]
    if warnings:
        lines += [f"AVERTISSEMENTS ({len(warnings)}): " + "; ".join(str(w) for w in warnings[:3])]
    hypotheses = case.get("hypotheses_explicites") or case.get("hypotheses", [])
    if hypotheses and isinstance(hypotheses, list):
        lines += ["", f"HYPOTHÈSES ({len(hypotheses)}):"]
        for h in hypotheses[:3]:
            lines.append(f"  - {h}")
    return "\n".join(lines)
```

- [ ] **Step 3: Update `_generate_rapport_llm` signature**

Remplacer la fonction `_generate_rapport_llm` (lignes 1095-1113) par :

```python
def _generate_rapport_llm(prompt: str, format: str = "abrege") -> str | None:
    """Appelle OpenAI pour générer le rapport. Retourne None si indisponible."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return None
    try:
        import openai as _openai  # type: ignore
        client = _openai.OpenAI(api_key=api_key)
        system_prompt = (
            _RAPPORT_SYSTEM_PROMPT_COMPLET if format == "complet" else _RAPPORT_SYSTEM_PROMPT_ABREGE
        )
        resp = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            max_tokens=_RAPPORT_MAX_TOKENS,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content or None
    except Exception:
        return None
```

- [ ] **Step 4: Update `generate_brouillon_rapport` signature**

Remplacer la fonction `generate_brouillon_rapport` (lignes 1225-1235) par :

```python
def generate_brouillon_rapport(
    case: dict,
    valuation_values: dict,
    status: str,
    blocking: list,
    warnings: list,
    format: str = "abrege",
) -> str:
    """Génère le brouillon de rapport : LLM si disponible, sinon template déterministe."""
    prompt = _build_rapport_prompt_v2(case, format, valuation_values, status, blocking, warnings)
    llm_text = _generate_rapport_llm(prompt, format)
    if llm_text:
        disclaimer = (
            "> **BROUILLON NON CERTIFIÉ** — Produit par assistant IA.\n"
            "> Validation et signature d'un évaluateur agréé requises avant toute diffusion.\n\n---\n\n"
        )
        return disclaimer + llm_text
    return _generate_rapport_deterministic(case, valuation_values, status, blocking, warnings)
```

- [ ] **Step 5: Run failing tests to verify they now pass**

```bash
cd C:\Users\simon\eval-immo\backend && python -m pytest tests/test_pure.py -k "TestBuildRapportPromptV2 or TestGenerateRapportFallbackNoCle" -v 2>&1 | tail -20
```

Expected: PASS — 6 tests passing. `TestSaveRapportContent` still fails (needs Task 3).

- [ ] **Step 6: Run all tests**

```bash
cd C:\Users\simon\eval-immo\backend && python -m pytest tests/test_pure.py -v 2>&1 | tail -10
```

Expected: 106+ PASS, 0 failures (100 existants + 6 nouveaux prompt tests)

- [ ] **Step 7: Commit**

```bash
cd C:\Users\simon\eval-immo && git add backend/engine/runtime.py && git commit -m "feat(batch8a): improved rapport LLM prompt v2, CUSPAP system prompts abrege/complet, max_tokens 4000"
```

---

### Task 3: Backend — Save and generate endpoints (api.py)

**Files:**
- Modify: `backend/api.py`

**Security flag:** `none`

**Does NOT cover:** Authentification/autorisation pour les endpoints (utilise le même pattern `_require_permission("runtime_write")` que les autres endpoints). Ne valide pas le contenu Markdown (anti-XSS non nécessaire côté backend pur).

- [ ] **Step 1: Add `app_save_rapport` and `app_generate_rapport` functions**

Dans `backend/api.py`, ajouter après `app_upload_document` (chercher `def app_upload_document`) :

```python
def app_save_rapport(body: dict) -> dict:
    """Écrase le contenu de brouillon_rapport.md dans la session."""
    session_id = str(body.get("session_id", "")).strip()
    content = str(body.get("content", "")).strip()
    if not session_id:
        raise ValueError("session_id requis")
    if not content:
        raise ValueError("content requis")
    session = require_session(session_id)
    artifact = find_artifact_record(session, "redaction", "brouillon_rapport.md")
    if not artifact:
        raise FileNotFoundError("brouillon_rapport.md introuvable dans la session")
    _, artifact_path = resolve_session_artifact(
        session, event_id=str(artifact.get("event_id") or "")
    )
    artifact_path.write_text(content, encoding="utf-8")
    return {"ok": True, "session_id": session_id}


def app_generate_rapport(body: dict) -> dict:
    """Régénère brouillon_rapport.md via LLM (ou fallback déterministe), sauvegarde et retourne le contenu."""
    from engine.runtime import generate_brouillon_rapport
    session_id = str(body.get("session_id", "")).strip()
    format_param = str(body.get("format", "abrege")).strip()
    if not session_id:
        raise ValueError("session_id requis")
    if format_param not in {"abrege", "complet"}:
        raise ValueError("format doit être 'abrege' ou 'complet'")
    session = require_session(session_id)
    dossier = dossier_review_summary(session_id)
    # Lire le case input depuis la session
    session_dir = Path(str(session.get("session_dir", "")))
    dossier_id = str(session.get("dossier_id", "") or dossier.get("dossier_id", ""))
    case_input_path = session_dir / f"{dossier_id}.input.json"
    if not case_input_path.exists():
        raise FileNotFoundError(f"case input introuvable: {case_input_path.name}")
    case = json.loads(case_input_path.read_text(encoding="utf-8"))
    valuation_values = dossier.get("valuation", {}).get("values", {}) or {}
    compliance = dossier.get("compliance", {}) or {}
    status = str(compliance.get("status", "BROUILLON") or "BROUILLON")
    blocking = list(compliance.get("blocking_failures", []) or [])
    warnings = list(compliance.get("warnings", []) or [])
    rapport_md = generate_brouillon_rapport(
        case, valuation_values, status, blocking, warnings, format=format_param
    )
    # Sauvegarder dans la session
    artifact = find_artifact_record(session, "redaction", "brouillon_rapport.md")
    if artifact:
        _, artifact_path = resolve_session_artifact(
            session, event_id=str(artifact.get("event_id") or "")
        )
        artifact_path.write_text(rapport_md, encoding="utf-8")
    return {"ok": True, "content": rapport_md, "session_id": session_id, "format": format_param}
```

- [ ] **Step 2: Add routing for new endpoints**

Dans `do_POST`, avant la ligne `self._send_json(404, {"error": "route introuvable"})` à la fin du bloc POST (chercher cette ligne dans `do_POST`), ajouter :

```python
            if self.path == "/app/report":
                if not self._require_permission("runtime_write"):
                    return
                self._send_json(200, app_save_rapport(body))
                return
            if self.path == "/app/report/generate":
                if not self._require_permission("runtime_write"):
                    return
                self._send_json(200, app_generate_rapport(body))
                return
```

- [ ] **Step 3: Run all backend tests including TestSaveRapportContent**

```bash
cd C:\Users\simon\eval-immo\backend && python -m pytest tests/test_pure.py -v 2>&1 | tail -15
```

Expected: 108+ PASS, 0 failures (tous les tests batch8a maintenant verts)

- [ ] **Step 4: Commit**

```bash
cd C:\Users\simon\eval-immo && git add backend/api.py && git commit -m "feat(batch8a): POST /app/report (save) and POST /app/report/generate endpoints"
```

---

### Task 4: Frontend API types (runtime-api.ts)

**Files:**
- Modify: `src/lib/runtime-api.ts`

**Security flag:** `none`

**Does NOT cover:** Gestion des erreurs réseau au-delà du `runtimeJson` existant (pattern établi).

- [ ] **Step 1: Add `saveRapport` and `generateRapport` functions**

Dans `src/lib/runtime-api.ts`, ajouter avant la dernière ligne (ou à la fin du fichier) :

```typescript
export async function saveRapport(sessionId: string, content: string): Promise<void> {
  await runtimeJson<{ ok: boolean }>('/app/report', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, content }),
  })
}

export async function generateRapport(
  sessionId: string,
  format: 'abrege' | 'complet'
): Promise<string> {
  const result = await runtimeJson<{ ok: boolean; content: string }>('/app/report/generate', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, format }),
  })
  return result.content
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd C:\Users\simon\eval-immo && npx tsc --noEmit 2>&1 | head -10
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
cd C:\Users\simon\eval-immo && git add src/lib/runtime-api.ts && git commit -m "feat(batch8a): saveRapport() and generateRapport() API functions"
```

---

### Task 5: Frontend — RapportEditor component (new file)

**Files:**
- Create: `src/components/shared/RapportEditor.tsx`

**Security flag:** `none`

**Does NOT cover:** Édition des tableaux comparables inline dans TipTap (TipTap table extensions gèrent le rendu mais l'édition fine des cellules est manuelle). Sauvegarde automatique (auto-save) — save est explicite via bouton.

- [ ] **Step 1: Install npm dependencies**

```bash
cd C:\Users\simon\eval-immo && npm install @tiptap/react @tiptap/pm @tiptap/starter-kit @tiptap/extension-table @tiptap/extension-table-row @tiptap/extension-table-cell @tiptap/extension-table-header marked turndown turndown-plugin-gfm && npm install -D @types/turndown
```

Expected: package.json mis à jour, node_modules installés sans erreur.

- [ ] **Step 2: Add turndown-plugin-gfm type declaration**

Créer `src/types/turndown-plugin-gfm.d.ts` :

```typescript
declare module 'turndown-plugin-gfm' {
  import TurndownService from 'turndown'
  export function gfm(service: TurndownService): void
  export function tables(service: TurndownService): void
  export function strikethrough(service: TurndownService): void
}
```

- [ ] **Step 3: Create RapportEditor component**

Créer `src/components/shared/RapportEditor.tsx` :

```typescript
'use client'

import { useEffect, useState, useCallback } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Table from '@tiptap/extension-table'
import TableRow from '@tiptap/extension-table-row'
import TableCell from '@tiptap/extension-table-cell'
import TableHeader from '@tiptap/extension-table-header'
import { marked } from 'marked'
import TurndownService from 'turndown'
import { gfm } from 'turndown-plugin-gfm'

const td = new TurndownService({
  headingStyle: 'atx',
  codeBlockStyle: 'fenced',
  bulletListMarker: '-',
})
td.use(gfm)

interface Props {
  initialMarkdown: string
  onSave: (markdown: string) => Promise<void>
  onGenerate: (format: 'abrege' | 'complet') => Promise<void>
}

function ToolbarButton({
  onClick,
  active,
  title,
  children,
}: {
  onClick: () => void
  active: boolean
  title: string
  children: React.ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      className={`w-7 h-7 rounded-[6px] text-[12px] flex items-center justify-center transition-colors ${
        active
          ? 'bg-[#1a1916] text-white'
          : 'text-[#5a5854] hover:bg-black/[.06]'
      }`}
    >
      {children}
    </button>
  )
}

export default function RapportEditor({ initialMarkdown, onSave, onGenerate }: Props) {
  const [isEdited, setIsEdited] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [toast, setToast] = useState('')

  const editor = useEditor({
    extensions: [
      StarterKit,
      Table.configure({ resizable: false }),
      TableRow,
      TableCell,
      TableHeader,
    ],
    content: '',
    onUpdate: () => setIsEdited(true),
    editorProps: {
      attributes: {
        class: 'focus:outline-none min-h-[200px]',
      },
    },
  })

  useEffect(() => {
    if (!editor || !initialMarkdown) return
    const html = String(marked.parse(initialMarkdown))
    editor.commands.setContent(html, false)
    setIsEdited(false)
  }, [editor, initialMarkdown])

  const handleSave = useCallback(async () => {
    if (!editor || isSaving) return
    setIsSaving(true)
    try {
      const markdown = td.turndown(editor.getHTML())
      await onSave(markdown)
      setIsEdited(false)
      setToast('Rapport sauvegardé')
      setTimeout(() => setToast(''), 2000)
    } finally {
      setIsSaving(false)
    }
  }, [editor, isSaving, onSave])

  const handleGenerate = useCallback(
    async (format: 'abrege' | 'complet') => {
      const label = format === 'complet' ? 'forme complète (15 sections)' : 'forme abrégée'
      if (!confirm(`La régénération remplacera le contenu actuel (${label}). Continuer ?`)) return
      setIsGenerating(true)
      try {
        await onGenerate(format)
        setIsEdited(false)
      } finally {
        setIsGenerating(false)
      }
    },
    [onGenerate]
  )

  if (!editor) return null

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* Toolbar */}
      <div
        className="flex items-center gap-1 px-3 py-2 border-b border-black/[.06] flex-shrink-0"
        style={{ background: 'rgba(255,255,255,.70)' }}
      >
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleBold().run()}
          active={editor.isActive('bold')}
          title="Gras"
        >
          <strong>B</strong>
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleItalic().run()}
          active={editor.isActive('italic')}
          title="Italique"
        >
          <em>I</em>
        </ToolbarButton>
        <div className="w-px h-4 bg-black/[.10] mx-1" />
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          active={editor.isActive('heading', { level: 2 })}
          title="Titre 2"
        >
          H2
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
          active={editor.isActive('heading', { level: 3 })}
          title="Titre 3"
        >
          H3
        </ToolbarButton>
        <div className="w-px h-4 bg-black/[.10] mx-1" />
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          active={editor.isActive('bulletList')}
          title="Liste à puces"
        >
          ≡
        </ToolbarButton>
        <div className="flex-1" />
        {toast && (
          <span className="text-[11px] text-emerald-600 mr-2 transition-opacity">{toast}</span>
        )}
        <button
          type="button"
          onClick={handleSave}
          disabled={!isEdited || isSaving}
          className="rounded-full px-3 py-1.5 text-[12px] bg-[#334155] text-white disabled:opacity-40 transition-opacity"
        >
          {isSaving ? 'Sauvegarde...' : 'Sauvegarder ✓'}
        </button>
      </div>

      {/* Editor content */}
      <div className="flex-1 overflow-y-auto px-8 py-5 scroll-fade">
        <div className="text-[13px] leading-[1.75] text-[#1a1916] [&_h1]:text-[18px] [&_h1]:font-semibold [&_h1]:mb-2 [&_h2]:text-[15px] [&_h2]:font-semibold [&_h2]:mt-5 [&_h2]:mb-1.5 [&_h3]:text-[13px] [&_h3]:font-medium [&_h3]:mt-3 [&_h3]:mb-1 [&_table]:w-full [&_table]:text-[12px] [&_table]:border-collapse [&_th]:text-left [&_th]:px-2 [&_th]:py-1.5 [&_th]:font-medium [&_th]:bg-black/[.025] [&_td]:px-2 [&_td]:py-1.5 [&_td]:border-t [&_td]:border-black/[.05] [&_blockquote]:border-l-2 [&_blockquote]:border-amber-400 [&_blockquote]:pl-3 [&_blockquote]:text-[12px] [&_blockquote]:text-amber-800 [&_blockquote]:bg-amber-50/60 [&_blockquote]:rounded-r-[4px] [&_blockquote]:py-1">
          <EditorContent editor={editor} />
        </div>
      </div>

      {/* Footer */}
      <div
        className="flex items-center gap-2 px-4 py-2.5 border-t border-black/[.06] flex-shrink-0"
        style={{ background: 'rgba(255,255,255,.60)' }}
      >
        <span className="text-[11px] text-[#b5b2ac] mr-1">Régénérer :</span>
        <button
          type="button"
          onClick={() => handleGenerate('abrege')}
          disabled={isGenerating}
          className="rounded-full px-3 py-1.5 text-[11px] bg-black/[.05] text-[#5a5854] hover:bg-black/[.09] disabled:opacity-40 transition-colors"
        >
          {isGenerating ? 'Génération...' : 'Forme abrégée'}
        </button>
        <button
          type="button"
          onClick={() => handleGenerate('complet')}
          disabled={isGenerating}
          className="rounded-full px-3 py-1.5 text-[11px] bg-[#1f7a5c]/10 text-[#1f7a5c] border border-[#1f7a5c]/20 hover:bg-[#1f7a5c]/20 disabled:opacity-40 transition-colors"
        >
          {isGenerating ? 'Génération...' : 'Forme complète →'}
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd C:\Users\simon\eval-immo && npx tsc --noEmit 2>&1 | head -15
```

Expected: No errors from RapportEditor.tsx or turndown-plugin-gfm.d.ts.

- [ ] **Step 5: Commit**

```bash
cd C:\Users\simon\eval-immo && git add src/components/shared/RapportEditor.tsx src/types/turndown-plugin-gfm.d.ts package.json package-lock.json && git commit -m "feat(batch8a): RapportEditor TipTap WYSIWYG component with save/generate"
```

---

### Task 6: Frontend wiring — RapportDoc + RapportPanel

**Files:**
- Modify: `src/components/shared/RapportDoc.tsx`
- Modify: `src/components/panels/RapportPanel.tsx`

**Security flag:** `none`

**Does NOT cover:** Affichage du texte `reportText` dans la vue non-split (hors split view RapportDoc). La vue split est la seule entrée pour l'éditeur TipTap.

- [ ] **Step 1: Update RapportDoc to accept reportText and branch to RapportEditor**

Dans `src/components/shared/RapportDoc.tsx`, modifier l'interface Props et le composant :

Ajouter à l'import en tête du fichier :
```typescript
import RapportEditor from '@/components/shared/RapportEditor'
```

Ajouter dans l'interface `Props` (après `onClose: () => void`) :
```typescript
  reportText?: string
  onSave?: (markdown: string) => Promise<void>
  onGenerate?: (format: 'abrege' | 'complet') => Promise<void>
```

Dans le composant `RapportDoc`, ajouter les nouveaux paramètres destructurés et un branchement conditionnel. Remplacer le début de la fonction `export default function RapportDoc({` jusqu'à (et incluant) le `return (` initial par :

```typescript
export default function RapportDoc({
  address,
  valeur,
  comparables,
  adjustments,
  factChips,
  valuationValues,
  complianceStatus,
  blockingFailures,
  warnings,
  onClose,
  reportText,
  onSave,
  onGenerate,
}: Props) {
  const today = new Date().toLocaleDateString('fr-CA', { year: 'numeric', month: 'long', day: 'numeric' })
  const approaches = Object.entries(valuationValues).filter(([, v]) => v > 0)

  // Bouton fermer réutilisé dans les deux branches
  const closeButton = (
    <div className="absolute top-3 right-8 z-10">
      <button
        onClick={onClose}
        className="w-7 h-7 rounded-[7px] flex items-center justify-center bg-transparent border-none cursor-pointer text-[#b5b2ac] hover:text-[#1a1916] hover:bg-black/[.06] transition-colors"
        title="Fermer"
      >
        <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
            d="M20 4L13 11M17 11H13V7M4 20L11 13M7 13H11V17"/>
        </svg>
      </button>
    </div>
  )

  // Si texte brouillon disponible → éditeur TipTap
  if (reportText) {
    return (
      <div className="flex flex-col flex-1 relative overflow-hidden">
        {closeButton}
        <div className="pt-8 flex flex-col flex-1 overflow-hidden">
          <RapportEditor
            initialMarkdown={reportText}
            onSave={onSave ?? (async () => {})}
            onGenerate={onGenerate ?? (async () => {})}
          />
        </div>
      </div>
    )
  }

  // Fallback : vue structurée (tables statiques)
  return (
    <div className="flex flex-col flex-1 relative overflow-hidden">
      {closeButton}
```

Puis supprimer l'ancien bloc `<div className="absolute top-3 right-8 z-10">...</div>` (le close button original, maintenant dupliqué dans `closeButton`).

- [ ] **Step 2: Update RapportPanel to load reportText and wire handlers**

Dans `src/components/panels/RapportPanel.tsx` :

**2a.** Ajouter les imports en haut du fichier :
```typescript
import { saveRapport, generateRapport } from '@/lib/runtime-api'
```

**2b.** Ajouter `reportText: string` dans l'interface `RapportState` (après `valuationValues: Record<string, number>`):
```typescript
  reportText: string
```

**2c.** Dans la fonction `reload()`, ajouter `reportText` à l'objet passé à `setState` (après `valuationValues` ligne) :
```typescript
      reportText: app.active?.report.preview ?? '',
```

**2d.** Ajouter les handlers après `handlePackage()` :
```typescript
  async function handleSaveReport(content: string) {
    if (!dossierId) return
    await saveRapport(dossierId, content)
  }

  async function handleGenerateReport(format: 'abrege' | 'complet') {
    if (!dossierId) return
    const newContent = await generateRapport(dossierId, format)
    setState(prev => prev ? { ...prev, reportText: newContent } : prev)
  }
```

**2e.** Dans le JSX, passer les nouvelles props à `<RapportDoc>` (après `onClose={() => setSplit(false)}`) :
```typescript
              reportText={state.reportText}
              onSave={handleSaveReport}
              onGenerate={handleGenerateReport}
```

- [ ] **Step 3: Verify TypeScript compiles clean**

```bash
cd C:\Users\simon\eval-immo && npx tsc --noEmit 2>&1 | head -15
```

Expected: No errors.

- [ ] **Step 4: Build**

```bash
cd C:\Users\simon\eval-immo && npx next build 2>&1 | tail -20
```

Expected: Build succeeds, 0 errors.

- [ ] **Step 5: Commit**

```bash
cd C:\Users\simon\eval-immo && git add src/components/shared/RapportDoc.tsx src/components/panels/RapportPanel.tsx && git commit -m "feat(batch8a): wire RapportEditor into RapportDoc split view, connect save/generate handlers"
```

---

### Task 7: npm deps (already covered in Task 5 Step 1)

> **Note:** Les dépendances npm sont installées dans Task 5 Step 1. Cette tâche est un rappel pour les waves parallèles — Task 7 = Task 5 Step 1 exécuté en avance si Task 5 n'est pas encore commencée.

Si Task 5 n'a pas encore été exécutée, lancer uniquement :

```bash
cd C:\Users\simon\eval-immo && npm install @tiptap/react @tiptap/pm @tiptap/starter-kit @tiptap/extension-table @tiptap/extension-table-row @tiptap/extension-table-cell @tiptap/extension-table-header marked turndown turndown-plugin-gfm && npm install -D @types/turndown
```

---

### Task 8: Vérification finale

**Files:**
- Test: tous
- Update: `state.md`

**Security flag:** `none`

- [ ] **Step 1: Run all backend tests**

```bash
cd C:\Users\simon\eval-immo\backend && python -m pytest tests/test_pure.py -v 2>&1 | tail -15
```

Expected: 108+ tests PASS, 0 failures.

- [ ] **Step 2: Frontend build**

```bash
cd C:\Users\simon\eval-immo && npx next build 2>&1 | tail -20
```

Expected: Build succeeds, 0 TypeScript errors.

- [ ] **Step 3: Smoke test — backend rapport functions**

```bash
cd C:\Users\simon\eval-immo\backend && python -c "
from engine.runtime import _build_rapport_prompt_v2, generate_brouillon_rapport, _RAPPORT_MAX_TOKENS

# Test prompt v2 includes commanditaire
case = {
    'dossier_id': 'D-TEST',
    'commanditaire': {'nom': 'Jean Dupont', 'organisation': 'Banque Test', 'fin_evaluation': 'hypothecaire'},
    'type_bien': 'residentiel_unifamilial',
    'zone': 'R-1',
    'date_reference': '2026-05-15',
    'surface': {'value': 120, 'unit': 'm2'},
    'comparables': [],
}
prompt = _build_rapport_prompt_v2(case, 'abrege', {}, 'BROUILLON', [], [])
assert 'Jean Dupont' in prompt, 'commanditaire manquant dans prompt'
assert 'abrege' in prompt.lower() or 'abr' in prompt.lower()
print('prompt v2 OK — commanditaire inclus')

# Test max_tokens
assert _RAPPORT_MAX_TOKENS == 4000, f'max_tokens: {_RAPPORT_MAX_TOKENS}'
print(f'max_tokens OK: {_RAPPORT_MAX_TOKENS}')

# Test fallback sans clé
import os
os.environ.pop('OPENAI_API_KEY', None)
result = generate_brouillon_rapport(case, {}, 'BROUILLON', [], [], format='abrege')
assert 'BROUILLON' in result and len(result) > 100
print('fallback déterministe OK')
print('SMOKE TEST PASSED')
"
```

Expected: `SMOKE TEST PASSED`

- [ ] **Step 4: Update state.md**

Dans `state.md`, mettre à jour :
- `Plan Status` : `Batch 8a (rapport éditeur TipTap + LLM quality): DONE ✓`
- `Evidence` : `108+ tests pass`
- `Current Goal` : `Batch 8a DONE. Prêt pour Batch 8b (export Word/PDF + versioning) ou Batch 9.`

- [ ] **Step 5: Commit**

```bash
cd C:\Users\simon\eval-immo && git add state.md && git commit -m "chore(batch8a): mark complete, 108+ tests pass, TipTap editor live"
```

---

## Self-Review

**1. Spec coverage:**
- ✅ `report.preview` → `RapportEditor` (Task 6)
- ✅ TipTap WYSIWYG StarterKit + Tables (Task 5)
- ✅ marked import + turndown export (Task 5)
- ✅ Save `POST /app/report` (Task 3 + 6)
- ✅ Régénérer forme abrégée / complète (Task 3 + 5)
- ✅ `_RAPPORT_SYSTEM_PROMPT_ABREGE` + `_COMPLET` (Task 2)
- ✅ `_build_rapport_prompt_v2` avec commanditaire (Task 2)
- ✅ `_RAPPORT_MAX_TOKENS` 4000 (Task 2)
- ✅ Toolbar Bold/Italic/H2/H3/List (Task 5)
- ✅ isEdited, isSaving, toast (Task 5)
- ✅ Confirm dialog avant régénération (Task 5)
- ✅ Fallback structured view si no `reportText` (Task 6)
- ✅ npm deps (Task 5)
- ✅ Tests TDD (Task 1)

**2. Placeholder scan:** Aucun TBD/TODO dans les implémentations.

**3. Type consistency:**
- `saveRapport(sessionId: string, content: string)` → `POST /app/report` body `{session_id, content}` ✅
- `generateRapport(sessionId: string, format: 'abrege' | 'complet')` → `POST /app/report/generate` ✅
- `RapportEditor` props `{ initialMarkdown, onSave, onGenerate }` → utilisés dans RapportDoc ✅
- `RapportState.reportText: string` → `state.reportText` passé à `RapportDoc.reportText` ✅

**4. Scope-reduction scan:** Aucun "basic/simple/v1/placeholder" non sanctionné.
