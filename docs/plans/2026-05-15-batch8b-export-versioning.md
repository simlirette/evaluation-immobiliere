# Batch 8b — Export livrable + Versioning rapport Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-optimized:subagent-driven-development (recommended) or superpowers-optimized:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permettre l'export .docx et HTML/PDF du rapport depuis RapportEditor, et sauvegarder des versions dans Supabase avec historique consultable.

**Architecture:** Le backend génère .docx (python-docx) et HTML (markdown lib) encodés en base64 JSON via `POST /app/report/export` — pas de changement au proxy BFF. Le versioning est 100% frontend : insert/query Supabase JS après chaque action de sauvegarde manuelle, version initiale auto-insérée à la première ouverture. `RapportEditor` reçoit `sessionId`, `dossierId`, `onSaveVersion` pour les boutons export/version ; `RapportPanel` orchestre le tout.

**Tech Stack:** Python 3.11 + python-docx 1.1 + markdown 3.6 (backend) ; Next.js/TypeScript + Supabase JS (frontend)

**Assumptions:**
- Assumes la table `rapport_versions` existe dans Supabase — ne fonctionnera pas si la migration SQL n'a pas été exécutée. Exécuter le SQL de la spec avant l'implémentation.
- Assumes `dossierId` prop de `RapportPanel` est utilisé comme `session_id` côté backend (pattern établi en Batch 8a).
- Assumes `app.active?.dossier.id` contient le `dossier_id` réel (pour libellé fichier et colonne Supabase).
- Assumes python-docx 1.1 — `from docx import Document` est le bon import ; will NOT work with python-docx 0.x.
- Assumes `marked.parse()` retourne `string` synchrone (Batch 8a déjà validé).

---

## File Structure

| Fichier | Action | Responsabilité |
|---------|--------|----------------|
| `backend/engine/report_export.py` | Créer | `_generate_docx`, `_generate_html`, `HTML_PRINT_TEMPLATE` — module isolé, aucune dépendance sur runtime.py |
| `backend/api.py` | Modifier | `app_export_rapport(body)`, routing `POST /app/report/export` |
| `backend/requirements.txt` | Modifier | Ajouter `python-docx>=1.1`, `markdown>=3.6` |
| `backend/tests/test_pure.py` | Modifier | 7 nouvelles classes de test |
| `src/lib/runtime-api.ts` | Modifier | `exportRapport(sessionId, format): Promise<{filename, blob}>` |
| `src/lib/rapport-versions.ts` | Créer | `saveVersion`, `loadVersions`, `renameVersion` — Supabase JS |
| `src/components/shared/RapportVersionHistory.tsx` | Créer | Liste versions + restaurer + renommer inline |
| `src/components/shared/RapportEditor.tsx` | Modifier | Props `sessionId`, `dossierId`, `onSaveVersion` ; boutons ⬇.docx, 🖨PDF, 📌Sauv.version |
| `src/components/shared/RapportDoc.tsx` | Modifier | Threader `sessionId`, `dossierId`, `onSaveVersion` de RapportPanel vers RapportEditor |
| `src/components/panels/RapportPanel.tsx` | Modifier | `versionCount` dans state, handlers save/restore, toggle historique, passe props à RapportDoc |

---

## Wave Plan

- **Wave 1:** Task 1 (TDD tests) + Task 4 (runtime-api.ts) — fichiers disjoints
- **Wave 2:** Task 2 (report_export.py + requirements.txt) + Task 5 (rapport-versions.ts) — après Task 1
- **Wave 3:** Task 3 (api.py endpoint) + Task 6 (RapportVersionHistory) — après Tasks 2+5 respectivement
- **Wave 4:** Task 7 (RapportEditor + RapportDoc) + Task 8 (RapportPanel) — après Tasks 3+4+6
- **Wave 5:** Task 9 (vérification finale)

---

### Task 1: Backend TDD tests

**Files:**
- Test: `backend/tests/test_pure.py`

**Security flag:** `none`

**Does NOT cover:** Tests d'intégration HTTP live (utilise `app_export_rapport` directement comme les autres tests batch8a).

- [ ] **Step 1: Append 7 new test classes to test_pure.py**

Ajouter à la fin de `backend/tests/test_pure.py` :

```python
# ── Batch 8b — Export rapport ────────────────────────────────────────────────

class TestGenerateDocx_ContainsWatermark:
    def test_watermark_in_generated_docx(self):
        import sys, io
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.report_export import _generate_docx
        from docx import Document
        data = _generate_docx("## Identification\n\nTestDocument", "D-TEST")
        assert isinstance(data, bytes) and len(data) > 0
        doc = Document(io.BytesIO(data))
        all_text = " ".join(p.text for p in doc.paragraphs)
        assert "BROUILLON NON CERTIFIÉ" in all_text


class TestGenerateDocx_HeadingsRendered:
    def test_h2_becomes_heading2(self):
        import sys, io
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.report_export import _generate_docx
        from docx import Document
        data = _generate_docx("## Section principale\n\nTexte normal.", "D-TEST")
        doc = Document(io.BytesIO(data))
        heading_styles = [p.style.name for p in doc.paragraphs]
        assert "Heading 2" in heading_styles


class TestGenerateHtml_ContainsWatermark:
    def test_watermark_div_present(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.report_export import _generate_html
        html = _generate_html("## Test\n\nContenu.", "D-TEST")
        assert isinstance(html, str)
        assert "BROUILLON NON CERTIFIÉ" in html


class TestGenerateHtml_TablesRendered:
    def test_markdown_table_becomes_html_table(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.report_export import _generate_html
        md = "| Col A | Col B |\n|-------|-------|\n| val1  | val2  |"
        html = _generate_html(md, "D-TEST")
        assert "<table" in html.lower()
        assert "val1" in html


class TestExportRapport_DocxEndpoint:
    def test_docx_export_returns_base64_with_correct_fields(self, tmp_path, monkeypatch):
        import sys, json, base64
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        import api as api_module
        monkeypatch.setattr(api_module, "SESSIONS_DIR", tmp_path)

        session_id = "test-export-docx"
        session_dir = tmp_path / session_id
        session_dir.mkdir()
        artifacts_dir = session_dir / "artifacts" / "D-EXPORT"
        artifacts_dir.mkdir(parents=True)
        rapport_path = artifacts_dir / "redaction.brouillon_rapport.md"
        rapport_path.write_text("## Rapport\n\nContenu test.", encoding="utf-8")
        artifact_index = {"artifacts": [{"step": "redaction", "artifact": "brouillon_rapport.md",
                                          "event_id": "evt_001", "path": str(rapport_path)}]}
        (session_dir / "artifact_index.json").write_text(json.dumps(artifact_index), encoding="utf-8")
        (session_dir / "session.json").write_text(
            json.dumps({"session_id": session_id, "session_dir": str(session_dir), "dossier_id": "D-EXPORT"}),
            encoding="utf-8")

        result = api_module.app_export_rapport({"session_id": session_id, "format": "docx"})
        assert result["ok"] is True
        assert result["content_type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert result["filename"] == "rapport-D-EXPORT.docx"
        data = base64.b64decode(result["data"])
        assert len(data) > 100  # valid docx has content


class TestExportRapport_HtmlEndpoint:
    def test_html_export_returns_html_string_with_watermark(self, tmp_path, monkeypatch):
        import sys, json
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        import api as api_module
        monkeypatch.setattr(api_module, "SESSIONS_DIR", tmp_path)

        session_id = "test-export-html"
        session_dir = tmp_path / session_id
        session_dir.mkdir()
        artifacts_dir = session_dir / "artifacts" / "D-HTML"
        artifacts_dir.mkdir(parents=True)
        rapport_path = artifacts_dir / "redaction.brouillon_rapport.md"
        rapport_path.write_text("## Test\n\nContenu.", encoding="utf-8")
        artifact_index = {"artifacts": [{"step": "redaction", "artifact": "brouillon_rapport.md",
                                          "event_id": "evt_001", "path": str(rapport_path)}]}
        (session_dir / "artifact_index.json").write_text(json.dumps(artifact_index), encoding="utf-8")
        (session_dir / "session.json").write_text(
            json.dumps({"session_id": session_id, "session_dir": str(session_dir), "dossier_id": "D-HTML"}),
            encoding="utf-8")

        result = api_module.app_export_rapport({"session_id": session_id, "format": "html"})
        assert result["ok"] is True
        assert result["content_type"] == "text/html; charset=utf-8"
        assert "BROUILLON NON CERTIFIÉ" in result["data"]
        assert "<table" in result["data"].lower() or "Test" in result["data"]


class TestExportRapport_InvalidFormat:
    def test_format_pdf_raises_value_error(self, tmp_path, monkeypatch):
        import sys, json, pytest
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        import api as api_module
        monkeypatch.setattr(api_module, "SESSIONS_DIR", tmp_path)

        session_id = "test-invalid-fmt"
        session_dir = tmp_path / session_id
        session_dir.mkdir()
        (session_dir / "session.json").write_text(
            json.dumps({"session_id": session_id, "session_dir": str(session_dir)}),
            encoding="utf-8")

        with pytest.raises(ValueError, match="format"):
            api_module.app_export_rapport({"session_id": session_id, "format": "pdf"})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd C:\Users\simon\eval-immo\backend && python -m pytest tests/test_pure.py -k "TestGenerateDocx or TestGenerateHtml or TestExportRapport" -v 2>&1 | tail -20
```

Expected: FAIL — `ModuleNotFoundError: No module named 'engine.report_export'`

- [ ] **Step 3: Commit**

```bash
cd C:\Users\simon\eval-immo && git add backend/tests/test_pure.py && git commit -m "test(batch8b): TDD tests for docx/html export and export endpoint"
```

---

### Task 2: Backend — report_export.py + requirements.txt

**Files:**
- Create: `backend/engine/report_export.py`
- Modify: `backend/requirements.txt`

**Security flag:** `none`

**Does NOT cover:** Tables avec cellules fusionnées — fallback plain text si parsing échoue. Mise en page avancée (sauts de page forcés entre sections) — non requis V0.

- [ ] **Step 1: Update requirements.txt**

Ajouter à la fin de `backend/requirements.txt` :

```
python-docx>=1.1
markdown>=3.6
```

- [ ] **Step 2: Install new dependencies**

```bash
cd C:\Users\simon\eval-immo\backend && pip install "python-docx>=1.1" "markdown>=3.6"
```

- [ ] **Step 3: Create backend/engine/report_export.py**

```python
"""
Export du rapport d'évaluation : génération .docx et HTML imprimable.
Aucune dépendance sur runtime.py — module isolé.
"""
from __future__ import annotations

import io
import re


HTML_PRINT_TEMPLATE = """\
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; }}
  body {{
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 12pt;
    line-height: 1.65;
    color: #1a1916;
    max-width: 780px;
    margin: 0 auto;
    padding: 2.5cm;
  }}
  .watermark {{
    background: #fff3cd;
    border: 1.5px solid #ffc107;
    border-radius: 4px;
    padding: 8px 14px;
    margin-bottom: 24px;
    font-size: 10pt;
    font-weight: 600;
    color: #856404;
  }}
  h1 {{ font-size: 18pt; font-weight: 600; margin: 0 0 8px; }}
  h2 {{ font-size: 14pt; font-weight: 600; margin: 28px 0 8px;
        border-bottom: 1px solid #e5e2dc; padding-bottom: 4px; }}
  h3 {{ font-size: 12pt; font-weight: 600; margin: 18px 0 6px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 10pt; margin: 12px 0; }}
  th {{ text-align: left; padding: 6px 10px; background: #f5f3ef;
        font-weight: 600; border: 1px solid #ddd9d2; }}
  td {{ padding: 5px 10px; border: 1px solid #ddd9d2; vertical-align: top; }}
  blockquote {{ margin: 12px 0; padding: 8px 14px; border-left: 3px solid #ffc107;
                background: #fffbf0; font-size: 10pt; color: #856404; }}
  ul, ol {{ padding-left: 22px; margin: 8px 0; }}
  li {{ margin: 3px 0; }}
  @media print {{
    @page {{ size: A4; margin: 2.5cm; }}
    body {{ padding: 0; max-width: none; }}
    table {{ page-break-inside: avoid; }}
  }}
</style>
</head>
<body>
<div class="watermark">&#9888; BROUILLON NON CERTIFIÉ — Ce document doit être révisé et signé
par un évaluateur agréé (É.A.) avant toute diffusion.
Supprimer cet avertissement avant certification.</div>
{body}
</body>
</html>
"""


def _generate_html(md_text: str, dossier_id: str) -> str:
    """Convertit le markdown en HTML imprimable avec CSS A4 et watermark."""
    import markdown as md_lib  # type: ignore
    body = md_lib.markdown(md_text, extensions=["tables", "fenced_code"])
    return HTML_PRINT_TEMPLATE.format(
        title=f"Rapport d'évaluation — {dossier_id}",
        body=body,
    )


def _parse_inline(text: str) -> list[tuple[str, bool, bool]]:
    """Retourne liste de (texte, bold, italic) depuis markdown inline."""
    parts: list[tuple[str, bool, bool]] = []
    pattern = re.compile(r"\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*(.+?)\*|([^*]+)")
    for m in pattern.finditer(text):
        if m.group(1):
            parts.append((m.group(1), True, True))
        elif m.group(2):
            parts.append((m.group(2), True, False))
        elif m.group(3):
            parts.append((m.group(3), False, True))
        elif m.group(4):
            parts.append((m.group(4), False, False))
    return parts


def _add_inline_paragraph(doc: object, text: str, style: str = "Normal") -> object:  # type: ignore
    """Ajoute un paragraphe avec runs gras/italique inline."""
    p = doc.add_paragraph(style=style)  # type: ignore[attr-defined]
    for chunk, bold, italic in _parse_inline(text):
        run = p.add_run(chunk)
        run.bold = bold
        run.italic = italic
    return p


def _generate_docx(md_text: str, dossier_id: str) -> bytes:
    """Convertit le markdown en fichier .docx (python-docx)."""
    from docx import Document  # type: ignore
    from docx.shared import Cm, RGBColor  # type: ignore

    doc = Document()

    # Marges 2.5cm
    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    # Watermark — paragraphe rouge gras en tête
    wm = doc.add_paragraph()
    run = wm.add_run(
        "\u26a0 BROUILLON NON CERTIFIÉ — Ce document doit être révisé et signé par un "
        "évaluateur agréé (É.A.) avant toute diffusion. "
        "Supprimer ce paragraphe avant certification."
    )
    run.bold = True
    run.font.color.rgb = RGBColor(0xDC, 0x26, 0x26)
    doc.add_paragraph()  # espace après watermark

    lines = md_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]

        # Heading 1 (# mais pas ##)
        if re.match(r"^# [^#]", line):
            doc.add_heading(line[2:].strip(), level=1)
            i += 1
            continue

        # Heading 2 (## mais pas ###)
        if re.match(r"^## [^#]", line):
            doc.add_heading(line[3:].strip(), level=2)
            i += 1
            continue

        # Heading 3
        if re.match(r"^### ", line):
            doc.add_heading(line[4:].strip(), level=3)
            i += 1
            continue

        # Blockquote
        if line.startswith("> "):
            p = doc.add_paragraph(style="Normal")
            run = p.add_run(line[2:].strip())
            run.italic = True
            run.font.color.rgb = RGBColor(0x85, 0x64, 0x04)
            i += 1
            continue

        # Bullet list
        if line.startswith("- ") or line.startswith("* "):
            _add_inline_paragraph(doc, line[2:].strip(), style="List Bullet")
            i += 1
            continue

        # Table (lignes commençant par |)
        if line.startswith("|"):
            table_lines: list[str] = []
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i])
                i += 1
            # Exclure la ligne de séparation |---|---|
            data_rows = [l for l in table_lines if not re.match(r"^\|[\s\-:|]+\|", l)]
            if not data_rows:
                continue
            try:
                parsed = [[c.strip() for c in row.strip("|").split("|")] for row in data_rows]
                max_cols = max(len(r) for r in parsed)
                table = doc.add_table(rows=len(parsed), cols=max_cols)
                table.style = "Table Grid"
                for row_idx, row_data in enumerate(parsed):
                    for col_idx in range(max_cols):
                        cell_text = row_data[col_idx] if col_idx < len(row_data) else ""
                        cell = table.cell(row_idx, col_idx)
                        cell.text = cell_text
                        if row_idx == 0:
                            for r in cell.paragraphs[0].runs:
                                r.bold = True
            except Exception:
                # Fallback plain text si table malformée
                for l in data_rows:
                    doc.add_paragraph(l.strip("|").replace("|", "  "), style="Normal")
            doc.add_paragraph()
            continue

        # Ligne vide
        if not line.strip():
            i += 1
            continue

        # Paragraphe normal avec inline bold/italic
        _add_inline_paragraph(doc, line, style="Normal")
        i += 1

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
```

- [ ] **Step 4: Run TDD tests to verify they pass**

```bash
cd C:\Users\simon\eval-immo\backend && python -m pytest tests/test_pure.py -k "TestGenerateDocx or TestGenerateHtml" -v 2>&1 | tail -15
```

Expected: 4 tests PASS. `TestExportRapport_*` still fail (needs Task 3).

- [ ] **Step 5: Run full suite**

```bash
cd C:\Users\simon\eval-immo\backend && python -m pytest tests/test_pure.py -v 2>&1 | tail -5
```

Expected: 108 PASS (7 nouveaux en attente), 0 failures.

- [ ] **Step 6: Commit**

```bash
cd C:\Users\simon\eval-immo && git add backend/engine/report_export.py backend/requirements.txt && git commit -m "feat(batch8b): report_export module — _generate_docx, _generate_html, HTML_PRINT_TEMPLATE"
```

---

### Task 3: Backend — export endpoint (api.py)

**Files:**
- Modify: `backend/api.py`

**Security flag:** `none`

**Does NOT cover:** Authentification de l'export (utilise `_require_permission("runtime_write")` comme les autres endpoints). Le .docx est retourné base64 JSON — pas de streaming binaire (proxy BFF utilise `res.text()`).

- [ ] **Step 1: Add app_export_rapport function**

Dans `backend/api.py`, ajouter après `app_generate_rapport` (chercher la fin de cette fonction) :

```python
def app_export_rapport(body: dict) -> dict:
    """Génère l'export du rapport en .docx ou HTML (base64 JSON)."""
    import base64
    from engine.report_export import _generate_docx, _generate_html

    session_id = str(body.get("session_id", "")).strip()
    format_param = str(body.get("format", "")).strip()
    if not session_id:
        raise ValueError("session_id requis")
    if format_param not in {"docx", "html"}:
        raise ValueError("format doit être 'docx' ou 'html'")

    session = require_session(session_id)
    artifact = find_artifact_record(session, "redaction", "brouillon_rapport.md")
    if not artifact:
        raise FileNotFoundError("brouillon_rapport.md introuvable dans la session")
    _, artifact_path = resolve_session_artifact(
        session, event_id=str(artifact.get("event_id") or "")
    )
    md_text = artifact_path.read_text(encoding="utf-8")
    dossier_id = str(session.get("dossier_id", "rapport"))

    if format_param == "docx":
        data = _generate_docx(md_text, dossier_id)
        return {
            "ok": True,
            "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "filename": f"rapport-{dossier_id}.docx",
            "data": base64.b64encode(data).decode("ascii"),
        }
    # format == "html"
    html = _generate_html(md_text, dossier_id)
    return {
        "ok": True,
        "content_type": "text/html; charset=utf-8",
        "filename": f"rapport-{dossier_id}.html",
        "data": html,
    }
```

- [ ] **Step 2: Add routing in do_POST**

Dans `do_POST`, avant `self._send_json(404, {"error": "route introuvable"})` (dernière ligne du bloc POST), ajouter :

```python
            if self.path == "/app/report/export":
                if not self._require_permission("runtime_write"):
                    return
                self._send_json(200, app_export_rapport(body))
                return
```

- [ ] **Step 3: Run all backend tests**

```bash
cd C:\Users\simon\eval-immo\backend && python -m pytest tests/test_pure.py -v 2>&1 | tail -10
```

Expected: **115 PASS, 0 failures** (108 existants + 7 nouveaux batch8b).

- [ ] **Step 4: Commit**

```bash
cd C:\Users\simon\eval-immo && git add backend/api.py && git commit -m "feat(batch8b): POST /app/report/export endpoint — docx (base64) and html formats"
```

---

### Task 4: Frontend API — exportRapport (runtime-api.ts)

**Files:**
- Modify: `src/lib/runtime-api.ts`

**Security flag:** `none`

**Does NOT cover:** Gestion erreur réseau au-delà de `runtimeJson` (pattern établi). Pas de progress indicator pour les gros fichiers.

- [ ] **Step 1: Add exportRapport function**

À la fin de `src/lib/runtime-api.ts`, ajouter :

```typescript
export async function exportRapport(
  sessionId: string,
  format: 'docx' | 'html'
): Promise<{ filename: string; blob: Blob }> {
  const result = await runtimeJson<{
    ok: boolean
    content_type: string
    filename: string
    data: string
  }>('/app/report/export', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, format }),
  })

  let blob: Blob
  if (format === 'docx') {
    // data est base64 — décoder en bytes
    const binary = atob(result.data)
    const bytes = new Uint8Array(binary.length)
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i)
    }
    blob = new Blob([bytes], { type: result.content_type })
  } else {
    blob = new Blob([result.data], { type: result.content_type })
  }

  return { filename: result.filename, blob }
}
```

- [ ] **Step 2: Verify TypeScript**

```bash
cd C:\Users\simon\eval-immo && npx tsc --noEmit 2>&1 | head -10
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
cd C:\Users\simon\eval-immo && git add src/lib/runtime-api.ts && git commit -m "feat(batch8b): exportRapport() — base64 decode docx, blob html"
```

---

### Task 5: Frontend versioning lib — rapport-versions.ts

**Files:**
- Create: `src/lib/rapport-versions.ts`

**Security flag:** `security` — accès Supabase avec credentials ANON_KEY ; la table utilise RLS `auth.role() = 'authenticated'`.

**Does NOT cover:** Pagination des versions (limite hard à 6 côté query). Gestion offline — si Supabase inaccessible, les fonctions lèvent une erreur que l'appelant doit try/catch.

- [ ] **Step 1: Create src/lib/rapport-versions.ts**

```typescript
import { createClient } from '@/lib/supabase/client'

export interface RapportVersion {
  id: string
  session_id: string
  dossier_id: string
  content: string
  format: string
  label: string
  is_initial: boolean
  created_at: string
}

/**
 * Insère une nouvelle version. Lance si Supabase inaccessible ou quota dépassé côté DB.
 * L'appelant doit try/catch pour ne pas bloquer le save principal.
 */
export async function saveVersion(
  sessionId: string,
  dossierId: string,
  content: string,
  format: string,
  label: string,
  isInitial: boolean
): Promise<void> {
  const supabase = createClient()
  const { error } = await supabase.from('rapport_versions').insert({
    session_id: sessionId,
    dossier_id: dossierId,
    content,
    format,
    label,
    is_initial: isInitial,
  })
  if (error) throw new Error(`saveVersion: ${error.message}`)
}

/**
 * Charge les 6 versions les plus récentes pour une session.
 * Triées DESC par created_at (la plus récente en premier).
 */
export async function loadVersions(sessionId: string): Promise<RapportVersion[]> {
  const supabase = createClient()
  const { data, error } = await supabase
    .from('rapport_versions')
    .select('*')
    .eq('session_id', sessionId)
    .order('created_at', { ascending: false })
    .limit(6)
  if (error) throw new Error(`loadVersions: ${error.message}`)
  return (data ?? []) as RapportVersion[]
}

/**
 * Renomme une version existante.
 */
export async function renameVersion(id: string, label: string): Promise<void> {
  const supabase = createClient()
  const { error } = await supabase
    .from('rapport_versions')
    .update({ label })
    .eq('id', id)
  if (error) throw new Error(`renameVersion: ${error.message}`)
}
```

- [ ] **Step 2: Verify TypeScript**

```bash
cd C:\Users\simon\eval-immo && npx tsc --noEmit 2>&1 | head -10
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
cd C:\Users\simon\eval-immo && git add src/lib/rapport-versions.ts && git commit -m "feat(batch8b): rapport-versions.ts — saveVersion, loadVersions, renameVersion (Supabase)"
```

---

### Task 6: Frontend — RapportVersionHistory component

**Files:**
- Create: `src/components/shared/RapportVersionHistory.tsx`

**Security flag:** `none`

**Does NOT cover:** Suppression de versions. Affichage du diff entre versions. Pagination (max 6 versions par session).

- [ ] **Step 1: Create src/components/shared/RapportVersionHistory.tsx**

```typescript
'use client'

import { useEffect, useState, useCallback } from 'react'
import { loadVersions, renameVersion, type RapportVersion } from '@/lib/rapport-versions'

interface Props {
  sessionId: string
  onRestore: (content: string) => void
}

function timeAgo(isoDate: string): string {
  const diff = Date.now() - new Date(isoDate).getTime()
  const mins = Math.floor(diff / 60_000)
  if (mins < 1) return "À l'instant"
  if (mins < 60) return `il y a ${mins} min`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `il y a ${hrs}h`
  return new Date(isoDate).toLocaleDateString('fr-CA', { month: 'short', day: 'numeric' })
}

export default function RapportVersionHistory({ sessionId, onRestore }: Props) {
  const [versions, setVersions] = useState<RapportVersion[]>([])
  const [loading, setLoading] = useState(true)
  const [renamingId, setRenamingId] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const v = await loadVersions(sessionId)
      setVersions(v)
    } catch {
      // Supabase non configuré ou erreur réseau — afficher vide
    } finally {
      setLoading(false)
    }
  }, [sessionId])

  useEffect(() => { load() }, [load])

  async function handleRename(id: string) {
    if (!renameValue.trim()) {
      setRenamingId(null)
      return
    }
    const newLabel = renameValue.trim()
    // Optimistic update
    setVersions(prev => prev.map(v => v.id === id ? { ...v, label: newLabel } : v))
    setRenamingId(null)
    try {
      await renameVersion(id, newLabel)
    } catch {
      // Revert on failure
      load()
    }
  }

  if (loading) {
    return <div className="px-4 py-3 text-[11px] text-[#b5b2ac]">Chargement…</div>
  }

  if (versions.length === 0) {
    return <div className="px-4 py-3 text-[11px] text-[#b5b2ac]">Aucune version sauvegardée.</div>
  }

  return (
    <div className="flex flex-col">
      {versions.map(v => (
        <div
          key={v.id}
          className="flex items-center gap-2 px-4 py-2 hover:bg-black/[.03] group border-b border-black/[.04] last:border-0"
        >
          <div className="flex flex-col flex-1 min-w-0">
            {renamingId === v.id ? (
              <input
                autoFocus
                value={renameValue}
                onChange={e => setRenameValue(e.target.value)}
                onBlur={() => handleRename(v.id)}
                onKeyDown={e => {
                  if (e.key === 'Enter') handleRename(v.id)
                  if (e.key === 'Escape') setRenamingId(null)
                }}
                className="text-[12px] text-[#1a1916] bg-transparent border-b border-[#334155] outline-none w-full pb-0.5"
              />
            ) : (
              <span className="text-[12px] text-[#1a1916] truncate">{v.label}</span>
            )}
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="text-[10px] text-[#b5b2ac]">{timeAgo(v.created_at)}</span>
              {v.is_initial && (
                <span className="text-[9px] bg-[#1f7a5c]/10 text-[#1f7a5c] rounded px-1 py-0.5 font-medium">
                  initiale
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
            <button
              type="button"
              onClick={() => { setRenamingId(v.id); setRenameValue(v.label) }}
              className="text-[10px] text-[#b5b2ac] hover:text-[#5a5854] px-1.5 py-1 rounded"
              title="Renommer"
            >
              ✎
            </button>
            <button
              type="button"
              onClick={() => onRestore(v.content)}
              className="text-[10px] bg-[#334155] text-white rounded-full px-2.5 py-1 hover:bg-[#1e293b] transition-colors"
            >
              Restaurer
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
```

- [ ] **Step 2: Verify TypeScript**

```bash
cd C:\Users\simon\eval-immo && npx tsc --noEmit 2>&1 | head -10
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
cd C:\Users\simon\eval-immo && git add src/components/shared/RapportVersionHistory.tsx && git commit -m "feat(batch8b): RapportVersionHistory component — list, restore, rename inline"
```

---

### Task 7: Frontend — RapportEditor + RapportDoc new props

**Files:**
- Modify: `src/components/shared/RapportEditor.tsx`
- Modify: `src/components/shared/RapportDoc.tsx`

**Security flag:** `none`

**Does NOT cover:** Export depuis la vue structurée (fallback sans reportText) — boutons export uniquement dans l'éditeur TipTap.

- [ ] **Step 1: Update RapportEditor.tsx**

Lire le fichier, puis effectuer ces changements :

**1a. Ajouter import** après les imports existants :
```typescript
import { exportRapport } from '@/lib/runtime-api'
```

**1b. Mettre à jour l'interface Props** (remplacer l'existante) :
```typescript
interface Props {
  initialMarkdown: string
  sessionId: string
  dossierId: string
  onSave: (markdown: string) => Promise<void>
  onGenerate: (format: 'abrege' | 'complet') => Promise<void>
  onSaveVersion: (markdown: string) => Promise<void>
}
```

**1c. Mettre à jour la destructuration** de la fonction `export default function RapportEditor(...)` :
```typescript
export default function RapportEditor({ initialMarkdown, sessionId, dossierId, onSave, onGenerate, onSaveVersion }: Props) {
```

**1d. Ajouter `isExporting` state** après les états existants :
```typescript
  const [isExporting, setIsExporting] = useState(false)
```

**1e. Ajouter `handleExport` callback** après `handleGenerate` :
```typescript
  const handleExport = useCallback(
    async (format: 'docx' | 'html') => {
      if (isExporting) return
      setIsExporting(true)
      try {
        const { filename, blob } = await exportRapport(sessionId, format)
        if (format === 'docx') {
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = filename
          document.body.appendChild(a)
          a.click()
          document.body.removeChild(a)
          URL.revokeObjectURL(url)
        } else {
          const url = URL.createObjectURL(blob)
          window.open(url, '_blank')
          setTimeout(() => URL.revokeObjectURL(url), 10_000)
        }
      } finally {
        setIsExporting(false)
      }
    },
    [isExporting, sessionId]
  )
```

**1f. Ajouter `handleSaveVersion` callback** après `handleExport` :
```typescript
  const handleSaveVersion = useCallback(async () => {
    if (!editor) return
    const markdown = td.turndown(editor.getHTML())
    await onSaveVersion(markdown)
  }, [editor, onSaveVersion])
```

**1g. Mettre à jour le JSX de la toolbar** — remplacer le `<div className="flex-1" />` jusqu'au bouton Sauvegarder existant par :

```tsx
        <div className="flex-1" />
        {toast && (
          <span className="text-[11px] text-emerald-600 mr-2 transition-opacity">{toast}</span>
        )}
        <div className="w-px h-4 bg-black/[.10] mx-1" />
        <button
          type="button"
          onClick={() => handleExport('docx')}
          disabled={isExporting}
          title="Télécharger .docx"
          className="rounded-full px-2.5 py-1.5 text-[11px] bg-black/[.05] text-[#5a5854] hover:bg-black/[.09] disabled:opacity-40 transition-colors"
        >
          {isExporting ? '…' : '⬇ .docx'}
        </button>
        <button
          type="button"
          onClick={() => handleExport('html')}
          disabled={isExporting}
          title="Aperçu PDF (imprimer depuis le navigateur)"
          className="rounded-full px-2.5 py-1.5 text-[11px] bg-black/[.05] text-[#5a5854] hover:bg-black/[.09] disabled:opacity-40 transition-colors"
        >
          {isExporting ? '…' : '🖨 PDF'}
        </button>
        <button
          type="button"
          onClick={handleSaveVersion}
          title="Sauvegarder comme nouvelle version"
          className="rounded-full px-2.5 py-1.5 text-[11px] bg-black/[.05] text-[#5a5854] hover:bg-black/[.09] transition-colors"
        >
          📌 Sauv. version
        </button>
        <div className="w-px h-4 bg-black/[.10] mx-1" />
        <button
          type="button"
          onClick={handleSave}
          disabled={!isEdited || isSaving}
          className="rounded-full px-3 py-1.5 text-[12px] bg-[#334155] text-white disabled:opacity-40 transition-opacity"
        >
          {isSaving ? 'Sauvegarde...' : 'Sauvegarder ✓'}
        </button>
```

- [ ] **Step 2: Update RapportDoc.tsx — thread new props**

Lire `src/components/shared/RapportDoc.tsx`, puis :

**2a. Ajouter à l'interface Props** (après `onGenerate`) :
```typescript
  sessionId?: string
  dossierId?: string
  onSaveVersion?: (markdown: string) => Promise<void>
```

**2b. Destructurer les nouveaux props** dans la signature de fonction.

**2c. Passer les nouveaux props à `<RapportEditor>`** dans la branche `if (reportText)` :
```tsx
          <RapportEditor
            initialMarkdown={reportText}
            sessionId={sessionId ?? ''}
            dossierId={dossierId ?? ''}
            onSave={onSave ?? (async () => {})}
            onGenerate={onGenerate ?? (async () => {})}
            onSaveVersion={onSaveVersion ?? (async () => {})}
          />
```

- [ ] **Step 3: Verify TypeScript**

```bash
cd C:\Users\simon\eval-immo && npx tsc --noEmit 2>&1 | head -15
```

Expected: No errors.

- [ ] **Step 4: Commit**

```bash
cd C:\Users\simon\eval-immo && git add src/components/shared/RapportEditor.tsx src/components/shared/RapportDoc.tsx && git commit -m "feat(batch8b): RapportEditor export/version buttons; RapportDoc threads sessionId+dossierId+onSaveVersion"
```

---

### Task 8: Frontend — RapportPanel wiring

**Files:**
- Modify: `src/components/panels/RapportPanel.tsx`

**Security flag:** `none`

**Does NOT cover:** Affichage du compteur de versions en temps réel si une autre session sauvegarde en parallèle (pas de sync realtime, reload manuel suffit pour V0).

- [ ] **Step 1: Update RapportPanel.tsx**

Lire le fichier complet, puis effectuer ces changements :

**1a. Ajouter imports** (après les imports existants) :
```typescript
import { marked } from 'marked'
import { saveVersion, loadVersions } from '@/lib/rapport-versions'
import RapportVersionHistory from '@/components/shared/RapportVersionHistory'
```

**1b. Ajouter `versionCount: number` et `dossierId: string` à `RapportState`** (après `complianceStatus`) :
```typescript
  versionCount: number
  realDossierId: string
```

**1c. Ajouter `showHistory` state** après les états existants :
```typescript
  const [showHistory, setShowHistory] = useState(false)
```

**1d. Mettre à jour `reload()`** — ajouter dans le bloc `setState({...})` après `complianceStatus` :
```typescript
      versionCount: 0,  // sera peuplé après
      realDossierId: app.active?.dossier.id ?? dossierId ?? '',
```

Et après l'appel `setState`, ajouter la logique de version initiale :
```typescript
    // Auto-save version initiale si aucune version n'existe
    const preview = app.active?.report.preview ?? ''
    if (preview && dossierId) {
      try {
        const versions = await loadVersions(dossierId)
        setState(prev => prev ? { ...prev, versionCount: versions.length } : prev)
        if (versions.length === 0) {
          const realId = app.active?.dossier.id ?? dossierId
          await saveVersion(
            dossierId,
            realId,
            preview,
            app.active?.mandat?.format_rapport ?? 'abrege',
            'Génération initiale',
            true
          )
          setState(prev => prev ? { ...prev, versionCount: 1 } : prev)
        }
      } catch {
        // Supabase non configuré — silencieux
      }
    }
```

**1e. Ajouter `handleSaveVersion` handler** après `handleGenerateReport` :
```typescript
  async function handleSaveVersion(markdown: string) {
    if (!dossierId || !state) return
    if (state.versionCount >= 6) {
      alert('Quota atteint : 5 versions manuelles + 1 initiale maximum. Aucune nouvelle version sauvegardée.')
      return
    }
    const now = new Date()
    const label = `Manuelle ${now.toLocaleDateString('fr-CA')} ${now.toLocaleTimeString('fr-CA', { hour: '2-digit', minute: '2-digit' })}`
    try {
      await saveVersion(dossierId, state.realDossierId, markdown, 'abrege', label, false)
      setState(prev => prev ? { ...prev, versionCount: prev.versionCount + 1 } : prev)
    } catch {
      alert('Version non sauvegardée — vérifier la connexion Supabase.')
    }
  }
```

**1f. Ajouter `handleRestoreVersion` handler** après `handleSaveVersion` :
```typescript
  function handleRestoreVersion(content: string) {
    setState(prev => prev ? { ...prev, reportText: content } : prev)
    setShowHistory(false)
  }
```

**1g. Ajouter le bouton Historique dans le JSX** — dans le bloc `<AgentMessage>`, après `<RapportArtifact .../>` :
```tsx
            {split && (
              <button
                type="button"
                onClick={() => setShowHistory(s => !s)}
                className="mt-2 rounded-full px-3 py-1.5 text-[11px] bg-black/[.05] text-[#5a5854] hover:bg-black/[.09] transition-colors"
              >
                {showHistory ? 'Fermer historique' : `Historique (${state.versionCount})`}
              </button>
            )}
            {showHistory && dossierId && (
              <div className="mt-2 rounded-[10px] border border-black/[.07] overflow-hidden">
                <RapportVersionHistory
                  sessionId={dossierId}
                  onRestore={handleRestoreVersion}
                />
              </div>
            )}
```

**1h. Passer les nouveaux props à `<RapportDoc>`** — ajouter après `onGenerate={handleGenerateReport}` :
```tsx
          sessionId={dossierId ?? ''}
          dossierId={state.realDossierId}
          onSaveVersion={handleSaveVersion}
```

- [ ] **Step 2: Verify TypeScript**

```bash
cd C:\Users\simon\eval-immo && npx tsc --noEmit 2>&1 | head -15
```

Expected: No errors.

- [ ] **Step 3: Build**

```bash
cd C:\Users\simon\eval-immo && npx next build 2>&1 | tail -20
```

Expected: Build succeeds, 0 errors.

- [ ] **Step 4: Commit**

```bash
cd C:\Users\simon\eval-immo && git add src/components/panels/RapportPanel.tsx && git commit -m "feat(batch8b): RapportPanel — version auto-save, historique toggle, restore, save version handler"
```

---

### Task 9: Vérification finale

**Files:**
- Update: `state.md`

**Security flag:** `none`

- [ ] **Step 1: Run all backend tests**

```bash
cd C:\Users\simon\eval-immo\backend && python -m pytest tests/test_pure.py -v 2>&1 | tail -10
```

Expected: **115 PASS, 0 failures**.

- [ ] **Step 2: Frontend build**

```bash
cd C:\Users\simon\eval-immo && npx next build 2>&1 | tail -15
```

Expected: Build succeeds, 0 TypeScript errors.

- [ ] **Step 3: Backend smoke test**

```bash
cd C:\Users\simon\eval-immo\backend && python -c "
from engine.report_export import _generate_docx, _generate_html

md = '## Identification\n\nAdresse: 123 rue Test\n\n| Col A | Col B |\n|-------|-------|\n| val1  | val2  |'

# Test HTML
html = _generate_html(md, 'D-TEST')
assert 'BROUILLON NON CERTIFIÉ' in html
assert '<table' in html.lower()
print('HTML OK — watermark + table present')

# Test docx
data = _generate_docx(md, 'D-TEST')
assert len(data) > 100
import io
from docx import Document
doc = Document(io.BytesIO(data))
texts = [p.text for p in doc.paragraphs]
assert any('BROUILLON' in t for t in texts)
headings = [p.style.name for p in doc.paragraphs]
assert 'Heading 2' in headings
print('DOCX OK — watermark + heading + bytes valid')
print('SMOKE TEST PASSED')
"
```

Expected: `SMOKE TEST PASSED`

- [ ] **Step 4: Update state.md**

Mettre à jour `state.md` :
- `Current Goal` → `Batch 8b DONE. Prêt pour Batch 9 (pipeline live view) ou présentation É.A.`
- `Plan Status` → ajouter `- Batch 8b (export docx/html + versioning Supabase): DONE ✓`
- `Evidence` → `115 tests pass`
- `Open Issues` → retirer "Supabase SQL migration", ajouter si besoin

- [ ] **Step 5: Commit**

```bash
cd C:\Users\simon\eval-immo && git add state.md && git commit -m "chore(batch8b): mark complete, 115 tests pass, export + versioning live"
```

---

## Self-Review

**1. Spec coverage :**
- ✅ Export .docx — `_generate_docx` + `app_export_rapport` + `exportRapport()` + bouton ⬇ .docx (Tasks 2+3+4+7)
- ✅ Export HTML/PDF — `_generate_html` + `app_export_rapport` + bouton 🖨 PDF (Tasks 2+3+4+7)
- ✅ Watermark toujours injecté dans .docx et HTML (Task 2)
- ✅ Versioning Supabase — `rapport-versions.ts` + auto-save initial dans reload() (Tasks 5+8)
- ✅ Max 6 versions (1 initiale + 5 manuelles) — vérifié dans `handleSaveVersion` (Task 8)
- ✅ Bouton 📌 Sauv. version — dans toolbar RapportEditor, passe markdown à `onSaveVersion` (Tasks 7+8)
- ✅ Historique UI — `RapportVersionHistory` + toggle dans RapportPanel (Tasks 6+8)
- ✅ Restauration — `handleRestoreVersion` → `setState({reportText})` → `useEffect` recharge éditeur (Task 8)
- ✅ Renommage inline — `handleRename` dans RapportVersionHistory (Task 6)
- ✅ Auto-label date/heure (Task 8 — `handleSaveVersion`)
- ✅ Tests TDD (Task 1 + 2 + 3)

**2. Placeholder scan :** Aucun TBD/TODO détecté.

**3. Type consistency :**
- `RapportVersion.session_id / dossier_id / content / format / label / is_initial / created_at` — défini Task 5, utilisé Tasks 6+8 ✅
- `exportRapport(sessionId, format) → {filename, blob}` — défini Task 4, utilisé Task 7 ✅
- `onSaveVersion: (markdown: string) => Promise<void>` — défini Task 7 (RapportEditor Props), passé Task 7 (RapportDoc), câblé Task 8 ✅
- `realDossierId: string` dans RapportState — défini Task 8, utilisé dans handleSaveVersion Task 8 ✅

**4. Scope-reduction scan :** Aucune réduction de scope non sanctionnée détectée.
