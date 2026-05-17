import type { Comparable, Adjustment, EnrichmentMarche } from '@/types'
import { computeComparableStats } from './compute-comparable-stats'
import { checkComparableMinimum } from './check-comparable-minimum'
import { computeMarketPriceTrend } from './compute-market-price-trend'
import { computeComparableQualityScore } from './compute-comparable-quality-score'
import { computePricePerM2Stats } from './compute-price-per-m2-stats'
import { computeTimeAdjustmentRate } from './compute-time-adjustment-rate'
import { computeComparableRanking } from './compute-comparable-ranking'
import { computeDataQualityReport } from './compute-data-quality-report'
import { computePricePerM2Distribution } from './compute-price-per-m2-distribution'

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
  adjustments?: Adjustment[],
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
    // Price trend
    const trend = computeMarketPriceTrend(comparables)
    const trendRow = trend
      ? `<tr><td style="color:#6a6763;">Tendance de prix annualisée</td><td style="font-weight:600;text-align:right;color:${trend.direction === 'hausse' ? '#1f7a5c' : trend.direction === 'baisse' ? '#b91c1c' : '#6a6763'};">${trend.annualizedPct > 0 ? '+' : ''}${fmt(trend.annualizedPct, 1)} %/an (${trend.direction})</td></tr>`
      : ''
    // $/m² stats
    const m2Stats = computePricePerM2Stats(comparables)
    const m2Row = m2Stats
      ? `<tr><td style="color:#6a6763;">Prix médian au m² (surface hab.)</td><td style="font-weight:600;text-align:right;">${fmt(m2Stats.median, 0)} $/m² <span style="font-weight:400;font-size:9pt;color:#8a8780;">(${fmt(m2Stats.min, 0)} – ${fmt(m2Stats.max, 0)})</span></td></tr>`
      : ''
    const timeRate = computeTimeAdjustmentRate(comparables)
    const timeRateRow = timeRate
      ? `<tr><td style="color:#6a6763;">Taux implicite d'appréciation</td><td style="font-weight:600;text-align:right;color:${timeRate.annualRatePct >= 0 ? '#1f7a5c' : '#b91c1c'};">${timeRate.annualRatePct >= 0 ? '+' : ''}${fmt(timeRate.annualRatePct, 1)} %/an <span style="font-weight:400;font-size:9pt;color:#8a8780;">— confiance ${timeRate.confidence}</span></td></tr>`
      : ''
    const m2Dist = computePricePerM2Distribution(comparables)
    const m2DistRow = m2Dist
      ? `<tr><td style="color:#6a6763;">Dispersion $/m² (CV)</td><td style="font-weight:600;text-align:right;">${fmt(m2Dist.cv, 1)} % <span style="font-weight:400;font-size:9pt;color:#8a8780;">(min ${fmt(m2Dist.min, 0)} – max ${fmt(m2Dist.max, 0)} $/m²)</span></td></tr>`
      : ''
    sections.push(`
      <h2>Synthèse des comparables</h2>
      <table><tbody>${statRows}${trendRow}${m2Row}${m2DistRow}${timeRateRow}</tbody></table>
      ${minCheck.warning ? `<p style="color:#b45309;font-size:10pt;">⚠ ${minCheck.warning}</p>` : ''}
    `)
  } else if (minCheck.warning) {
    sections.push(`<p style="color:#b45309;font-size:10pt;">⚠ ${minCheck.warning}</p>`)
  }

  // Comparables table
  if (comparables.length > 0) {
    const qualityScores = adjustments ? computeComparableQualityScore(comparables, adjustments) : []
    const qualityMap = new Map(qualityScores.map(q => [q.comparableId, q.label]))
    const ranking = adjustments ? computeComparableRanking(comparables, adjustments) : []
    const rankMap = new Map(ranking.map(r => [r.comparableId, r]))
    const rows = comparables.map(c => {
      const ql = qualityMap.get(c.id)
      const qlColor = ql === 'excellent' ? '#1f7a5c' : ql === 'bon' ? '#0369a1' : ql === 'acceptable' ? '#b45309' : ql === 'faible' ? '#b91c1c' : '#8a8780'
      const ranked = rankMap.get(c.id)
      const rankCell = ranked
        ? `<td style="text-align:right;font-size:9pt;color:${ranked.rank === 1 ? '#1f7a5c' : '#8a8780'};font-weight:${ranked.rank === 1 ? '700' : '400'};">#${ranked.rank}</td>`
        : '<td></td>'
      return `
      <tr>
        <td>${c.rank}</td>
        <td>${c.address}</td>
        <td style="text-align:right;">${fmtMoney(c.sale_price)}</td>
        <td style="text-align:right;">${c.date}</td>
        ${ql ? `<td style="color:${qlColor};font-size:9pt;font-weight:600;">${ql}</td>` : '<td></td>'}
        ${rankCell}
        <td style="color:#6a6763;font-size:10pt;">${c.meta}</td>
      </tr>
    `
    }).join('')
    sections.push(`
      <h2>${comparables.length} comparable${comparables.length !== 1 ? 's' : ''} retenus</h2>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Adresse</th>
            <th style="text-align:right;">Prix de vente</th>
            <th style="text-align:right;">Date</th>
            <th>Qualité</th>
            ${adjustments ? '<th style="text-align:right;">Rang</th>' : ''}
            <th>Notes</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    `)
  } else {
    sections.push('<p>Aucun comparable chargé.</p>')
  }

  // Data quality report
  if (comparables.length > 0) {
    const dqr = computeDataQualityReport(comparables, adjustments ?? [])
    if (dqr && dqr.grade !== 'bon') {
      const color = dqr.grade === 'faible' ? '#b91c1c' : '#b45309'
      const issueItems = dqr.issues.map(i => `<li>${i}</li>`).join('')
      sections.push(`
        <div style="background:${dqr.grade === 'faible' ? '#fef2f2' : '#fffbeb'};border:1pt solid ${dqr.grade === 'faible' ? '#fecaca' : '#fcd34d'};border-radius:4pt;padding:8pt 10pt;margin-top:8pt;">
          <p style="font-weight:600;color:${color};font-size:10pt;margin:0 0 4pt;">Qualité des données — ${dqr.grade}</p>
          <ul style="margin:0;padding-left:16pt;color:${color};font-size:9pt;">${issueItems}</ul>
        </div>
      `)
    }
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
