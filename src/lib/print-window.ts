/**
 * Opens a temporary print window with the given HTML content and triggers print.
 * The window closes itself after the print dialog is dismissed.
 */
export function printWindow(bodyHtml: string, title = 'Rapport évaluation'): void {
  const win = window.open('', '_blank', 'width=900,height=700')
  if (!win) return

  win.document.write(`<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>${title}</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 12pt;
    line-height: 1.75;
    color: #1a1916;
    padding: 32mm 25mm;
    max-width: 900px;
    margin: 0 auto;
  }
  h1 { font-size: 16pt; font-weight: 700; margin-bottom: 6pt; }
  h2 { font-size: 13pt; font-weight: 600; margin-top: 18pt; margin-bottom: 6pt; border-bottom: 1pt solid #ddd; padding-bottom: 3pt; }
  h3 { font-size: 11pt; font-weight: 600; margin-top: 12pt; margin-bottom: 4pt; }
  p { margin-bottom: 9pt; }
  ul, ol { margin: 6pt 0 9pt 18pt; }
  li { margin-bottom: 3pt; }
  table { width: 100%; border-collapse: collapse; margin: 9pt 0; font-size: 10pt; }
  th { background: #f5f3f0; font-weight: 600; text-align: left; padding: 5pt 8pt; border: 0.5pt solid #ccc; }
  td { padding: 4pt 8pt; border: 0.5pt solid #ddd; vertical-align: top; }
  blockquote { border-left: 3pt solid #d97706; padding: 6pt 12pt; background: #fffbeb; margin: 9pt 0; font-size: 10pt; color: #92400e; border-radius: 2pt; }
  .watermark { color: #bbb; font-size: 9pt; text-align: center; margin-top: 24pt; padding-top: 12pt; border-top: 0.5pt solid #eee; font-style: italic; font-family: sans-serif; }
  @media print {
    body { padding: 0; }
    @page { margin: 20mm 18mm; }
    h2 { page-break-after: avoid; }
    table { page-break-inside: avoid; }
  }
</style>
</head>
<body>
${bodyHtml}
<div class="watermark">Document brouillon — non certifié — validation par évaluateur agréé requise</div>
</body>
</html>`)
  win.document.close()
  win.onload = () => { win.print(); win.onafterprint = () => win.close() }
}
