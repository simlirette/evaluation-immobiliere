import type { Comparable, EnrichmentMarche } from '@/types'
import { computeComparableStats } from './compute-comparable-stats'
import { checkComparableMinimum } from './check-comparable-minimum'

function fmt(n: number | null | undefined, digits = 1): string {
  if (n == null) return '—'
  return new Intl.NumberFormat('fr-CA', { maximumFractionDigits: digits }).format(n)
}

function fmtMoney(n: number | null | undefined): string {
  if (n == null) return '—'
  return new Intl.NumberFormat('fr-CA', { style: 'currency', currency: 'CAD', maximumFractionDigits: 0 })
    .format(n).replace('CA', '').trim()
}

/**
 * Builds print-friendly HTML for the Marché panel (comparables + market context).
 * Intended for use with printWindow().
 */
export function buildMarcheHtml(
  comparables: Comparable[],
  marche: EnrichmentMarche | null,
  address?: string,
): string {
  const sections: string[] = []
  const today = new Date().toLocaleDateString('fr-CA', { year: 'numeric', month: 'long', day: 'numeric' })

  // Header
  sections.push(`
    <h1>Rapport de marché — comparables</h1>
    <p style="color:#8a8780;font-size:11pt;margin-bottom:4pt;">
      ${address ?? 'Dossier'} &mdash; ${today}
    </p>
    <hr style="border:none;border-top:1pt solid #ddd;margin:10pt 0;">
  `)

  // Score marché
  if (marche?.score_marche != null) {
    const score = marche.score_marche
    const color = score >= 7 ? '#1f7a5c' : score >= 5 ? '#b45309' : '#b91c1c'
    sections.push(`
      <h2>Score de marché</h2>
      <p>
        <strong style="font-size:16pt;color:${color};">${fmt(score, 1)}&nbsp;/&nbsp;10</strong>
        ${marche.tension_locative ? `&nbsp;&mdash;&nbsp;<em>${marche.tension_locative}</em>` : ''}
      </p>
      ${marche.marche_interpretation ? `<p style="color:#4a4743;">${marche.marche_interpretation}</p>` : ''}
    `)
  }

  // Comparable set stats summary
  const stats = computeComparableStats(comparables)
  const minCheck = checkComparableMinimum(comparables)
  if (stats) {
    const statRows = [
      ['Nombre de comparables', String(stats.count)],
      ['Fourchette de prix', `${fmtMoney(stats.priceMin)} – ${fmtMoney(stats.priceMax)}`],
      ['Période des ventes', `${stats.dateMin.slice(0, 4)}${stats.dateMin.slice(0, 4) !== stats.dateMax.slice(0, 4) ? ` – ${stats.dateMax.slice(0, 4)}` : ''}`],
      ...(stats.priceM2Min !== null && stats.priceM2Max !== null
        ? [['Fourchette $/m²', `${fmt(stats.priceM2Min, 0)} – ${fmt(stats.priceM2Max, 0)} $/m²`]]
        : []),
    ].map(([label, val]) => `
      <tr>
        <td style="color:#6a6763;">${label}</td>
        <td style="font-weight:600;text-align:right;">${val}</td>
      </tr>
    `).join('')
    sections.push(`
      <h2>Synthèse des comparables</h2>
      <table><tbody>${statRows}</tbody></table>
      ${minCheck.warning ? `<p style="color:#b45309;font-size:10pt;">⚠ ${minCheck.warning}</p>` : ''}
    `)
  } else if (minCheck.warning) {
    sections.push(`<p style="color:#b45309;font-size:10pt;">⚠ ${minCheck.warning}</p>`)
  }

  // Comparables table
  if (comparables.length > 0) {
    const rows = comparables.map(c => `
      <tr>
        <td>${c.rank}</td>
        <td>${c.address}</td>
        <td style="text-align:right;">${fmtMoney(c.sale_price)}</td>
        <td style="text-align:right;">${c.date}</td>
        <td style="color:#6a6763;font-size:10pt;">${c.meta}</td>
      </tr>
    `).join('')
    sections.push(`
      <h2>${comparables.length} comparable${comparables.length !== 1 ? 's' : ''} retenus</h2>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Adresse</th>
            <th style="text-align:right;">Prix de vente</th>
            <th style="text-align:right;">Date</th>
            <th>Notes</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    `)
  } else {
    sections.push('<p>Aucun comparable chargé.</p>')
  }

  // Market context chips
  const chips: Array<[string, string]> = []
  if (marche?.taux_inoccupation_pct != null) chips.push(['Inoccupation', `${fmt(marche.taux_inoccupation_pct)} %`])
  if (marche?.nhpi_variation_pct != null) chips.push(['NHPI variation', `${marche.nhpi_variation_pct >= 0 ? '+' : ''}${fmt(marche.nhpi_variation_pct)} %/an`])
  if (marche?.taux_hypo_5ans_pct != null) chips.push(['Taux hypo 5 ans', `${fmt(marche.taux_hypo_5ans_pct)} %`])
  if (marche?.taux_directeur_pct != null) chips.push(['Taux directeur', `${fmt(marche.taux_directeur_pct)} %`])
  if (marche?.taux_chomage_pct != null) chips.push(['Chômage CMA', `${fmt(marche.taux_chomage_pct)} %`])
  if (marche?.mises_en_chantier_12m != null) chips.push(['Mises en chantier', `${fmt(marche.mises_en_chantier_12m, 0)}/an`])
  if (marche?.taux_absorption_pct != null) chips.push(['Taux absorption', `${fmt(marche.taux_absorption_pct)} %`])
  if (marche?.ipc_variation_logement_pct != null) chips.push(['IPC logement', `${marche.ipc_variation_logement_pct >= 0 ? '+' : ''}${fmt(marche.ipc_variation_logement_pct)} %/an`])

  if (chips.length > 0) {
    const rows = chips.map(([label, val]) => `
      <tr>
        <td style="color:#6a6763;">${label}</td>
        <td style="font-weight:600;text-align:right;">${val}</td>
      </tr>
    `).join('')
    sections.push(`
      <h2>Contexte de marché</h2>
      <table>
        <tbody>${rows}</tbody>
      </table>
    `)
  }

  return sections.join('\n')
}
