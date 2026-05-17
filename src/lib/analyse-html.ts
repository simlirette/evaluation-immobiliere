import type { Comparable, Adjustment, EnrichmentFinancier } from '@/types'
import { buildOEAQChecklist } from './build-oeaq-checklist'
import { computeSubjectContext } from './compute-subject-context'
import { computeMedianIndicatedValue } from './compute-median-indicated-value'
import { detectOutlierComparables } from './detect-outlier-comparables'

function fmtMoney(n: number): string {
  return new Intl.NumberFormat('fr-CA', {
    style: 'currency', currency: 'CAD', maximumFractionDigits: 0,
  }).format(n).replace('CA', '').trim()
}

function fmtAdj(n: number): string {
  const prefix = n > 0 ? '+' : ''
  return `${prefix}${fmtMoney(n)}`
}

function fmt(n: number | null | undefined, digits = 1): string {
  if (n == null) return '—'
  return new Intl.NumberFormat('fr-CA', { maximumFractionDigits: digits }).format(n)
}

const STATUS_LABELS: Record<string, string> = {
  A_VALIDER_PAR_EVALUATEUR_AGREE: 'À valider — évaluateur agréé requis',
  VALIDE: 'Validé en revue interne',
  A_CORRIGER: 'À corriger',
  PRET_REVUE: 'Prêt pour revue',
  ASSISTANCE_DOSSIER_ACTIVE: 'Assistance active',
}

/**
 * Builds print-friendly HTML for the Analyse panel (adjustments table + financial context).
 * Intended for use with printWindow().
 */
export function buildAnalyseHtml(
  adjustments: Adjustment[],
  conclusion: number | null,
  status: string,
  financier: EnrichmentFinancier | null,
  address?: string,
  comparables?: Comparable[],
): string {
  const sections: string[] = []
  const today = new Date().toLocaleDateString('fr-CA', { year: 'numeric', month: 'long', day: 'numeric' })
  const statusLabel = STATUS_LABELS[status] ?? status.replace(/_/g, ' ')

  // Header
  sections.push(`
    <h1>Analyse — ajustements de valeur</h1>
    <p style="color:#8a8780;font-size:11pt;margin-bottom:4pt;">
      ${address ?? 'Dossier'} &mdash; ${today}
    </p>
    <hr style="border:none;border-top:1pt solid #ddd;margin:10pt 0;">
  `)

  // Conclusion
  if (conclusion !== null) {
    const ctx = adjustments.length > 0 ? computeSubjectContext(conclusion, adjustments) : null
    const median = computeMedianIndicatedValue(adjustments)
    const contextNote = ctx
      ? ctx.withinRange
        ? `Conclusion dans la fourchette des valeurs indiquées${Math.abs(ctx.deviationFromMedianPct) >= 1 ? ` (${ctx.deviationFromMedianPct > 0 ? '+' : ''}${fmt(ctx.deviationFromMedianPct)} % vs médiane${median != null ? '&nbsp;' + fmtMoney(median) : ''})` : ', en ligne avec la médiane'}.`
        : `⚠ Conclusion hors de la fourchette des valeurs indiquées (${ctx.deviationFromMedianPct > 0 ? '+' : ''}${fmt(ctx.deviationFromMedianPct)} % vs médiane${median != null ? '&nbsp;' + fmtMoney(median) : ''}) — justification requise.`
      : null
    sections.push(`
      <h2>Conclusion de valeur proposée</h2>
      <p style="font-size:20pt;font-weight:700;color:#1a1916;">${fmtMoney(conclusion)}</p>
      <p style="font-size:10pt;color:#6a6763;">Statut&nbsp;: ${statusLabel}</p>
      ${contextNote ? `<p style="font-size:10pt;color:${ctx?.withinRange ? '#6a6763' : '#b45309'};">${contextNote}</p>` : ''}
      <blockquote>À titre indicatif uniquement — validation et signature par un évaluateur agréé requises avant toute diffusion.</blockquote>
    `)
  }

  // Adjustments table
  if (adjustments.length > 0) {
    const outliers = detectOutlierComparables(adjustments)
    const outlierMap = new Map(outliers.map(o => [o.id, o]))
    const rows = adjustments.map(a => {
      const outlier = outlierMap.get(a.id)
      const adjustedCell = outlier?.isOutlier
        ? `<td style="text-align:right;font-weight:700;">${fmtMoney(a.adjusted)}<br><span style="font-size:8pt;font-weight:400;color:#b45309;">${outlier.deviationFromMedianPct > 0 ? '+' : ''}${fmt(outlier.deviationFromMedianPct)} % vs méd.</span></td>`
        : `<td style="text-align:right;font-weight:700;">${fmtMoney(a.adjusted)}</td>`
      return `
      <tr>
        <td>${a.comparableLabel}</td>
        <td style="text-align:right;">${fmtMoney(a.salePrice)}</td>
        <td style="text-align:right;color:${a.surface_adj >= 0 ? '#1f7a5c' : '#b91c1c'};">${fmtAdj(a.surface_adj)}</td>
        <td style="text-align:right;color:${a.year_adj >= 0 ? '#1f7a5c' : '#b91c1c'};">${fmtAdj(a.year_adj)}</td>
        <td style="text-align:right;color:${a.condition_adj >= 0 ? '#1f7a5c' : '#b91c1c'};">${fmtAdj(a.condition_adj)}</td>
        ${adjustedCell}
      </tr>
    `
    }).join('')
    const outlierCount = outliers.filter(o => o.isOutlier).length
    const outlierNote = outlierCount > 0
      ? `<p style="font-size:9pt;color:#b45309;margin-top:6pt;">⚠ ${outlierCount} valeur${outlierCount !== 1 ? 's' : ''} indiquée${outlierCount !== 1 ? 's' : ''} atypique${outlierCount !== 1 ? 's' : ''} (écart &gt; 15 % vs médiane) — à examiner avant réconciliation.</p>`
      : ''
    sections.push(`
      <h2>Trace d'ajustements (${adjustments.length} comparable${adjustments.length !== 1 ? 's' : ''})</h2>
      <table>
        <thead>
          <tr>
            <th>Comparable</th>
            <th style="text-align:right;">Prix vente</th>
            <th style="text-align:right;">Adj. surface</th>
            <th style="text-align:right;">Adj. année</th>
            <th style="text-align:right;">Adj. état</th>
            <th style="text-align:right;">Ajusté</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
      ${outlierNote}
    `)
  }

  // Financial context
  if (financier) {
    const rows: Array<[string, string, string?]> = []
    if (financier.total_mensuel != null) rows.push(['Coût mensuel total estimé', fmtMoney(financier.total_mensuel)])
    if (financier.versement_hypo_mensuel != null) rows.push(['Dont versement hypothécaire', fmtMoney(financier.versement_hypo_mensuel)])
    if (financier.ratio_revenu_pct != null) rows.push(['Ratio coûts / revenu médian', `${fmt(financier.ratio_revenu_pct)} %`, financier.interpretation_couts ?? undefined])
    if (financier.versement_mensuel_estime != null) rows.push(['Mensualité estimée (25 ans, 20 % MDP)', fmtMoney(financier.versement_mensuel_estime)])
    if (financier.ratio_mensualite_revenu_pct != null) rows.push(['Ratio mensualité / revenu médian', `${fmt(financier.ratio_mensualite_revenu_pct)} %`, financier.seuil_propriete ?? undefined])
    if (financier.revenu_median_menage != null) rows.push(['Revenu médian ménage CMA (2021)', fmtMoney(financier.revenu_median_menage)])
    if (financier.ratio_dette_revenu_pct != null) {
      const trend = financier.variation_dette_revenu_pct != null
        ? `${financier.variation_dette_revenu_pct >= 0 ? '+' : ''}${fmt(financier.variation_dette_revenu_pct)} %/an`
        : undefined
      rows.push(['Ratio dette / revenu (Canada)', `${fmt(financier.ratio_dette_revenu_pct)} %`, trend])
    }
    if (rows.length > 0) {
      const tableRows = rows.map(([label, value, sub]) => `
        <tr>
          <td style="color:#6a6763;">${label}</td>
          <td style="text-align:right;font-weight:600;">${value}${sub ? `<br><span style="font-size:9pt;font-weight:400;color:#8a8780;">${sub}</span>` : ''}</td>
        </tr>
      `).join('')
      sections.push(`<h2>Contexte financier</h2><table><tbody>${tableRows}</tbody></table>`)
    }
  }

  // OEAQ compliance checklist
  if (comparables && comparables.length > 0) {
    const checks = buildOEAQChecklist(comparables, adjustments)
    const checkRows = checks.map(c => `
      <tr>
        <td style="color:${c.pass ? '#1f7a5c' : '#b45309'};font-weight:600;white-space:nowrap;">${c.pass ? '✓' : '⚠'}</td>
        <td style="color:#1a1916;">${c.rule}</td>
        <td style="color:${c.pass ? '#6a6763' : '#b45309'};font-size:9pt;">${c.message ?? ''}</td>
      </tr>
    `).join('')
    sections.push(`
      <h2>Conformité OEAQ</h2>
      <table>
        <thead><tr><th></th><th>Règle</th><th>Note</th></tr></thead>
        <tbody>${checkRows}</tbody>
      </table>
    `)
  }

  return sections.join('\n')
}
