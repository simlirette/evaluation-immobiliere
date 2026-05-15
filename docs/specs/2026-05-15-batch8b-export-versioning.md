# Batch 8b — Export livrable + Versioning rapport

## Scope

**In scope :**
- Export .docx depuis `brouillon_rapport.md` — `python-docx` + parser MD custom
- Export HTML imprimable (aperçu PDF navigateur) — `markdown` lib + template CSS print A4
- Watermark "BROUILLON NON CERTIFIÉ" toujours injecté dans les deux formats ; l'É.A. l'enlève manuellement avant certification
- Versioning Supabase (frontend only) : 1ère version auto + versions manuelles sur demande
- UI historique dans RapportPanel : liste, restauration locale, renommage inline

**Non-goals :**
- WeasyPrint / génération PDF native backend (dépendances Windows)
- Export PDF pixel-perfect (Word + Ctrl+P navigateur = suffisant V0)
- Auto-save de version à chaque sauvegarde (stockage inutile)
- Versioning dans le backend Python (pas de supabase-py)
- Historique diff / track changes entre versions

---

## Architecture

### Flux export

```
RapportEditor toolbar
  └─ [⬇ .docx]  → exportRapport(sessionId, 'docx')
                   → POST /app/report/export {session_id, format: 'docx'}
                   → lit brouillon_rapport.md artifact
                   → _generate_docx(md_text, dossier_id) → bytes
                   → Content-Disposition: attachment; filename="rapport-{dossier_id}.docx"
                   → frontend: blob download

  └─ [🖨 PDF]   → exportRapport(sessionId, 'html')
                   → POST /app/report/export {session_id, format: 'html'}
                   → _generate_html(md_text, dossier_id) → HTML string
                   → Content-Type: text/html; charset=utf-8
                   → frontend: window.open(blobURL, '_blank')
```

### Flux versioning

```
RapportPanel.reload()
  └─ si report.preview non vide ET aucune version dans Supabase pour session_id
       → insert version initiale (is_initial=true, label="Génération initiale")

RapportEditor toolbar
  └─ [📌 Sauv. version]
       → confirm label auto ("Manuelle YYYY-MM-DD HH:MM")
       → insert Supabase rapport_versions
       → si count >= 6: toast "Quota atteint (5 versions + initiale)"

RapportPanel header
  └─ "Historique (N)" → <RapportVersionHistory> slide-in
       └─ liste triée DESC created_at
       └─ [Restaurer] → editor.setContent(html) local (pas de save auto)
       └─ [Renommer] → inline edit → update Supabase label
```

---

## Nouveaux endpoints backend

### `POST /app/report/export`
```
Body:  { "session_id": "...", "format": "docx" | "html" }
Auth:  _require_permission("runtime_write")
Steps:
  1. require_session(session_id)
  2. find_artifact_record(session, "redaction", "brouillon_rapport.md")
  3. lire contenu markdown
  4. si format == "docx" → _generate_docx(md, dossier_id) → bytes
     si format == "html" → _generate_html(md, dossier_id) → str.encode("utf-8")
  5. _send_bytes(data, content_type, filename)
Returns: binary file
Errors:  404 si artifact manquant, 400 si format invalide
```

### Helper `_send_bytes`
Ajouter dans la classe handler api.py :
```python
def _send_bytes(self, data: bytes, content_type: str, filename: str) -> None:
    self.send_response(200)
    self.send_header("Content-Type", content_type)
    self.send_header("Content-Length", str(len(data)))
    self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
    self._send_cors_headers()
    self.end_headers()
    self._write_access_audit(200)
    self.wfile.write(data)
```

---

## Génération .docx — `_generate_docx(md_text, dossier_id)`

Parser markdown ligne par ligne avec `python-docx` :

| Markdown | python-docx |
|----------|-------------|
| `# Titre` | `Heading 1` |
| `## Titre` | `Heading 2` |
| `### Titre` | `Heading 3` |
| `> blockquote` | style Normal, fond gris, italic |
| `**bold**` / `*italic*` | runs avec bold/italic |
| `- item` | List Bullet |
| `\| col \| col \|` | Table (1 ligne header) |
| texte normal | Normal |

Watermark injecté en premier paragraphe :
```
⚠ BROUILLON NON CERTIFIÉ — Ce document doit être révisé et signé par un évaluateur agréé 
(É.A.) avant toute diffusion. Supprimer ce paragraphe avant certification.
```

Style watermark : rouge, gras, encadré, Normal style.

---

## Génération HTML — `_generate_html(md_text, dossier_id)`

```python
import markdown as md_lib

def _generate_html(md_text: str, dossier_id: str) -> str:
    body = md_lib.markdown(md_text, extensions=["tables", "fenced_code"])
    watermark = '<div class="watermark">⚠ BROUILLON NON CERTIFIÉ — ...</div>'
    return HTML_PRINT_TEMPLATE.format(
        title=f"Rapport — {dossier_id}",
        watermark=watermark,
        body=body,
    )
```

`HTML_PRINT_TEMPLATE` : HTML complet avec `<style>` inline, `@media print` A4, police Cormorant Garamond (Google Fonts), marges 2.5cm, page-break avant H1.

---

## Schéma Supabase

```sql
create table rapport_versions (
  id uuid primary key default gen_random_uuid(),
  session_id text not null,
  dossier_id text not null,
  content text not null,
  format text not null default 'abrege',
  label text not null,
  is_initial boolean not null default false,
  created_at timestamptz default now()
);

alter table rapport_versions enable row level security;

create policy "authenticated users manage versions"
  on rapport_versions for all
  using (auth.role() = 'authenticated');

create index on rapport_versions (session_id, created_at desc);
```

**Quota** : max 6 versions par `session_id` (1 initiale `is_initial=true` + 5 manuelles). Vérification côté frontend avant insert.

---

## Modifications fichiers

| Fichier | Type | Description |
|---------|------|-------------|
| `backend/engine/report_export.py` | Créer | `_generate_docx()`, `_generate_html()`, `HTML_PRINT_TEMPLATE` |
| `backend/api.py` | Modifier | `app_export_rapport()`, `_send_bytes()`, routing `/app/report/export` |
| `backend/requirements.txt` | Modifier | Ajouter `python-docx>=1.1`, `markdown>=3.6` |
| `backend/tests/test_pure.py` | Modifier | `TestGenerateDocx_*`, `TestGenerateHtml_*`, `TestExportRapport_*` |
| `src/lib/runtime-api.ts` | Modifier | `exportRapport(sessionId, format): Promise<Blob>` |
| `src/lib/rapport-versions.ts` | Créer | `saveVersion()`, `loadVersions()`, `renameVersion()`, `restoreVersion()` — appels Supabase JS |
| `src/components/shared/RapportVersionHistory.tsx` | Créer | Liste versions + restaurer + renommer |
| `src/components/shared/RapportEditor.tsx` | Modifier | Boutons ⬇ .docx, 🖨 PDF, 📌 Sauv. version dans toolbar |
| `src/components/panels/RapportPanel.tsx` | Modifier | Auto-save version initiale, bouton "Historique (N)", passage props à RapportEditor |

---

## Dépendances npm (aucune nouvelle)
Supabase JS déjà installé (auth existant). Pas de nouveau package npm.

---

## Tests backend

| Classe | Vérifie |
|--------|---------|
| `TestGenerateDocx_ContainsWatermark` | Watermark présent dans le .docx généré |
| `TestGenerateDocx_HeadingsRendered` | `## Titre` → Heading 2 dans le document |
| `TestGenerateHtml_ContainsWatermark` | Watermark div présent dans HTML |
| `TestGenerateHtml_TablesRendered` | Tableaux markdown présents dans HTML |
| `TestExportRapport_DocxEndpoint` | POST /app/report/export format=docx → 200 + Content-Disposition |
| `TestExportRapport_HtmlEndpoint` | POST /app/report/export format=html → 200 + text/html |
| `TestExportRapport_InvalidFormat` | format=pdf → 400 |

---

## Failure modes et mitigations

| Mode | Sévérité | Mitigation |
|------|----------|------------|
| `python-docx` table markdown malformée → exception | Mineur | `try/except` par ligne, ligne problématique → paragraphe plain text |
| Insert Supabase version échoue (réseau/quota) | **Critique** | `try/catch` frontend, toast "Version non sauvegardée", save principal non bloqué |
| HTML print rendu différent Chrome vs Firefox | Mineur | CSS `@media print` standardisé, testé Chrome/Edge (V0 suffisant) |
| Session sans brouillon_rapport.md artifact | Mineur | Backend 404 clair, frontend toast "Export indisponible" |
| Quota 6 versions dépassé | Mineur | Frontend vérifie count avant insert, toast explicatif |
