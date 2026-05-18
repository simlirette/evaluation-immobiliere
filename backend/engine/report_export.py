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


def _generate_pdf(md_text: str, dossier_id: str) -> bytes:
    """Convertit le markdown en PDF via PyMuPDF fitz.Story (sans dépendances externes)."""
    import fitz  # type: ignore
    import markdown as md_lib  # type: ignore

    body = md_lib.markdown(md_text, extensions=["tables", "fenced_code"])
    html = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><style>
body {{ font-family: serif; font-size: 11pt; line-height: 1.65; color: #1a1916; margin: 0; padding: 0; }}
.watermark {{ background: #fff3cd; border: 1.5px solid #b8860b; border-radius: 4px;
    padding: 8px 14px; margin-bottom: 20px; font-size: 9pt; font-weight: bold; color: #856404; }}
h1 {{ font-size: 17pt; font-weight: bold; margin: 0 0 10px; }}
h2 {{ font-size: 13pt; font-weight: bold; margin: 22px 0 8px;
    border-bottom: 1px solid #e5e2dc; padding-bottom: 4px; }}
h3 {{ font-size: 11pt; font-weight: bold; margin: 14px 0 5px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 9pt; margin: 10px 0; }}
th {{ text-align: left; padding: 5px 8px; background: #f5f3ef;
    font-weight: bold; border: 1px solid #ccc; }}
td {{ padding: 4px 8px; border: 1px solid #ccc; vertical-align: top; }}
ul, ol {{ padding-left: 20px; margin: 6px 0; }}
li {{ margin: 2px 0; }}
blockquote {{ margin: 10px 0; padding: 6px 12px; border-left: 3px solid #ffc107;
    background: #fffbf0; font-size: 9pt; color: #856404; }}
</style></head>
<body>
<div class="watermark">&#9888; BROUILLON NON CERTIFIÉ — Ce document doit être révisé et signé
par un évaluateur agréé (É.A.) avant toute diffusion.</div>
{body}
</body></html>"""

    buf = io.BytesIO()
    story = fitz.Story(html=html)
    writer = fitz.DocumentWriter(buf)
    mediabox = fitz.paper_rect("a4")
    where = mediabox + (71, 71, -71, -71)  # ~2.5 cm margins
    more = True
    while more:
        device = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(device)
        writer.end_page()
    writer.close()
    return buf.getvalue()


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
