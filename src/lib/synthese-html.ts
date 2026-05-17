import type { Enrichment } from '@/types'

function fmtMoney(n: number | null | undefined): string {
  if (n == null) return '—'
  return new Intl.NumberFormat('fr-CA', {
    style: 'currency', currency: 'CAD', maximumFractionDigits: 0,
  }).format(n).replace('CA', '').trim()
}

function fmt(n: number | null | undefined, digits = 1): string {
  if (n == null) return '—'
  return new Intl.NumberFormat('fr-CA', { maximumFractionDigits: digits }).format(n)
}

const ALERTE_LABELS: Record<string, string> = {
  critique: 'CRITIQUE',
  attention: 'ATTENTION',
  info: 'INFO',
}

const GRADE_LABELS: Record<string, string> = {
  A: '#1f7a5c',
  B: '#0369a1',
  C: '#b45309',
  D: '#c2410c',
  F: '#b91c1c',
}

/**
 * Builds a print-friendly HTML string for the Synthèse panel.
 * Intended for use with printWindow().
 */
export function buildSyntheseHtml(enrichment: Enrichment, address?: string): string {
  const sections: string[] = []
  const today = new Date().toLocaleDateString('fr-CA', { year: 'numeric', month: 'long', day: 'numeric' })

  // Header
  sections.push(`
    <h1>Synthèse d'évaluation</h1>
    <p style="color:#8a8780;font-size:11pt;margin-bottom:4pt;">
      ${address ?? 'Dossier'} &mdash; ${today}
    </p>
    <hr style="border:none;border-top:1pt solid #ddd;margin:10pt 0;">
  `)

  // Score global
  if (enrichment.score_global) {
    const sg = enrichment.score_global
    const color = GRADE_LABELS[sg.grade] ?? '#555'
    sections.push(`
      <h2>Score global</h2>
      <table>
        <tr>
          <td style="width:60pt;font-size:40pt;font-weight:700;color:${color};vertical-align:middle;text-align:center;">
            ${sg.grade}
          </td>
          <td style="vertical-align:middle;padding-left:12pt;">
            <div style="font-size:18pt;font-weight:600;color:#1a1916;">${fmt(sg.score, 2)} / 10</div>
            <div style="font-size:11pt;color:#4a4743;margin-top:4pt;">${sg.recommandation}</div>
          </td>
        </tr>
      </table>
    `)
  }

  // Alertes
  if (enrichment.alertes && enrichment.alertes.liste.length > 0) {
    const rows = enrichment.alertes.liste.map(a => {
      const nivel = ALERTE_LABELS[a.niveau] ?? a.niveau.toUpperCase()
      const color = a.niveau === 'critique' ? '#b91c1c' : a.niveau === 'attention' ? '#b45309' : '#0369a1'
      return `
        <tr>
          <td style="width:70pt;font-size:9pt;font-weight:700;color:${color};vertical-align:top;padding:4pt 8pt;">
            ${nivel}
          </td>
          <td style="vertical-align:top;padding:4pt 8pt;">
            <div style="font-size:9pt;color:#6a6763;text-transform:capitalize;">${a.categorie.replace(/_/g, ' ')}</div>
            <div style="font-size:11pt;color:#1a1916;">${a.message}</div>
          </td>
        </tr>
      `
    }).join('')
    sections.push(`<h2>Alertes</h2><table>${rows}</table>`)
  }

  // Scores
  const scoreRows: string[] = []
  const addScore = (label: string, score: number | null | undefined, sub?: string | null) => {
    if (score == null) return
    const color = score >= 7 ? '#1f7a5c' : score >= 5 ? '#b45309' : '#b91c1c'
    scoreRows.push(`
      <tr>
        <td style="padding:4pt 8pt;font-size:11pt;color:#1a1916;">${label}</td>
        <td style="padding:4pt 8pt;font-size:11pt;font-weight:600;color:${color};">${fmt(score, 1)} / 10</td>
        <td style="padding:4pt 8pt;font-size:10pt;color:#6a6763;">${sub ?? ''}</td>
      </tr>
    `)
  }
  addScore('Investissement', enrichment.score_investissement?.score, enrichment.score_investissement?.recommandation)
  addScore('Marché', enrichment.marche?.score_marche, enrichment.marche?.marche_interpretation ?? enrichment.marche?.tension_locative)
  addScore('Qualité de vie', enrichment.indice_qualite_vie?.score, enrichment.indice_qualite_vie?.interpretation)
  addScore('Risque', enrichment.score_risque?.score, enrichment.score_risque?.categorie)
  if (scoreRows.length > 0) {
    sections.push(`<h2>Scores composites</h2><table><thead><tr><th>Indicateur</th><th>Score</th><th>Interprétation</th></tr></thead><tbody>${scoreRows.join('')}</tbody></table>`)
  }

  // Valeurs clés
  const kvRows: string[] = []
  if (enrichment.valeur_indicative) {
    kvRows.push(`<tr><td>Valeur indicative</td><td>${fmtMoney(enrichment.valeur_indicative.valeur)}</td><td>${enrichment.valeur_indicative.fiabilite}</td></tr>`)
  }
  if (enrichment.rendement_locatif) {
    kvRows.push(`<tr><td>Rendement locatif brut</td><td>${fmt(enrichment.rendement_locatif.taux_brut_pct, 2)} %</td><td>Net estimé : ${fmt(enrichment.rendement_locatif.taux_net_pct, 2)} %</td></tr>`)
  }
  if (enrichment.taxes_municipales) {
    kvRows.push(`<tr><td>Taxes municipales</td><td>${fmtMoney(enrichment.taxes_municipales.annuel)}/an</td><td>${fmt(enrichment.taxes_municipales.taux_pct, 3)} %</td></tr>`)
  }
  if (enrichment.ratio_prix_loyer) {
    kvRows.push(`<tr><td>Ratio prix/loyer</td><td>${fmt(enrichment.ratio_prix_loyer.ratio, 1)}×</td><td>${enrichment.ratio_prix_loyer.signal}</td></tr>`)
  }
  if (enrichment.vetuste_batiment) {
    kvRows.push(`<tr><td>Vétusté du bâtiment</td><td>${enrichment.vetuste_batiment.age_ans} ans</td><td>${enrichment.vetuste_batiment.categorie}</td></tr>`)
  }
  if (enrichment.cout_renovation) {
    const r = enrichment.cout_renovation
    kvRows.push(`<tr><td>Rénovation estimée</td><td>${fmtMoney(r.cout_min)}–${fmtMoney(r.cout_max)}</td><td>${r.type_travaux}</td></tr>`)
  }
  if (kvRows.length > 0) {
    sections.push(`<h2>Métriques clés</h2><table><thead><tr><th>Indicateur</th><th>Valeur</th><th>Note</th></tr></thead><tbody>${kvRows.join('')}</tbody></table>`)
  }

  // Projection
  if (enrichment.projection_valeur) {
    const pv = enrichment.projection_valeur
    sections.push(`
      <h2>Projection de valeur (scénario de base)</h2>
      <p style="font-size:10pt;color:#6a6763;">
        Base : <strong>${fmtMoney(pv.valeur_base)}</strong> &mdash; Taux : ${fmt(pv.taux_base_pct, 2)} %/an
      </p>
      <table>
        <thead><tr><th>Horizon</th><th>Valeur projetée</th></tr></thead>
        <tbody>
          <tr><td>1 an</td><td>${fmtMoney(pv.an1)}</td></tr>
          <tr><td>3 ans</td><td>${fmtMoney(pv.an3)}</td></tr>
          <tr><td>5 ans</td><td>${fmtMoney(pv.an5)}</td></tr>
        </tbody>
      </table>
    `)
  }

  return sections.join('\n')
}
