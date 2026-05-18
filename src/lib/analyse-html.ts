import type { Comparable, Adjustment, EnrichmentFinancier } from '@/types'
import { buildOEAQChecklist } from './build-oeaq-checklist'
import { computeSubjectContext } from './compute-subject-context'
import { computeMedianIndicatedValue } from './compute-median-indicated-value'
import { detectOutlierComparables } from './detect-outlier-comparables'
import { computeAdjustmentProfile } from './compute-adjustment-profile'
import { computeReconciledValue } from './compute-reconciled-value'
import { computeAdjustmentConsistency } from './compute-adjustment-consistency'
import { computeTimeAdjustmentRate } from './compute-time-adjustment-rate'
import { computeAdjustedPriceStats } from './compute-adjusted-price-stats'
import { computeSensitivityAnalysis } from './compute-sensitivity-analysis'
import { computeComparableRanking } from './compute-comparable-ranking'
import { computeValuationConclusion } from './compute-valuation-conclusion'
import { computeDataQualityReport } from './compute-data-quality-report'
import { computeMarketPositioning } from './compute-market-positioning'
import { computeAdjustmentNetEffect } from './compute-adjustment-net-effect'
import { computeHoldingCostEstimate } from './compute-holding-cost-estimate'
import { computeAppraisalRiskScore } from './compute-appraisal-risk-score'
import { computeNeighborhoodComparability } from './compute-neighborhood-comparability'
import { computeAdjustmentBracketAnalysis } from './compute-adjustment-bracket-analysis'
import { computeGrossAdjustmentCeiling } from './compute-gross-adjustment-ceiling'
import { computeValueRangeConfidence } from './compute-value-range-confidence'
import { computeAdjustmentWeightedMedian } from './compute-adjustment-weighted-median'
import { computeAdjustmentSymmetry } from './compute-adjustment-symmetry'
import { computeLocationPremium } from './compute-location-premium'
import { computeComparableVintageAnalysis } from './compute-comparable-vintage-analysis'
import { computeValuePerM2Conclusion } from './compute-value-per-m2-conclusion'
import { computeAdjustmentDirectionBalance } from './compute-adjustment-direction-balance'
import { computeAdjustmentMagnitudeProfile } from './compute-adjustment-magnitude-profile'
import { computeAdjustmentConvergence } from './compute-adjustment-convergence'
import { computeNetAdjustmentDistribution } from './compute-net-adjustment-distribution'
import { computeOEAQComplianceSummary } from './compute-oeaq-compliance-summary'
import { computeAdjustmentTypeRatioCheck } from './compute-adjustment-type-ratio-check'
import { computeReconciledValueBracket } from './compute-reconciled-value-bracket'
import { computeReconciliationConcentration } from './compute-reconciliation-concentration'
import { computeAdjustmentOutlierByType } from './compute-adjustment-outlier-by-type'
import { computeOEAQBracketingSummary } from './compute-oeaq-bracketing-summary'
import { computeWeightedAdjustedMean } from './compute-weighted-adjusted-mean'
import { computeGrossAdjustmentTrend } from './compute-gross-adjustment-trend'
import { computeAdjustmentSummaryByComp } from './compute-adjustment-summary-by-comp'
import { computeAdjustmentCoverageByType } from './compute-adjustment-coverage-by-type'
import { computeTimeAdjustmentImpact } from './compute-time-adjustment-impact'
import { computeGrossToNetRatio } from './compute-gross-to-net-ratio'
import { computeAdjustmentLineItemStats } from './compute-adjustment-line-item-stats'
import { computeNetAdjustmentRangeCheck } from './compute-net-adjustment-range-check'
import { computeAdjustmentExplainedVariance } from './compute-adjustment-explained-variance'
import { computeAdjustedPriceCV } from './compute-adjusted-price-cv'
import { computeNetAdjustmentSignBias } from './compute-net-adjustment-sign-bias'
import { computeGrossAdjustmentDistribution } from './compute-gross-adjustment-distribution'
import { computeAdjustmentZeroRateByType } from './compute-adjustment-zero-rate-by-type'
import { computePricePerM2Convergence } from './compute-price-per-m2-convergence'
import { computeAdjustmentDominantTypeByComp } from './compute-adjustment-dominant-type-by-comp'
import { computeSalePriceResidual } from './compute-sale-price-residual'
import { computeMedianAdjustedPrice } from './compute-median-adjusted-price'
import { computeValueIndicatorRange } from './compute-value-indicator-range'
import { computeAdjustmentNetMagnitudeProfile } from './compute-adjustment-net-magnitude-profile'
import { computeAdjustmentConditionBias } from './compute-adjustment-condition-bias'
import { computeAdjustmentGarageImpact } from './compute-adjustment-garage-impact'
import { computeAdjustedPriceZScore } from './compute-adjusted-price-z-score'
import { computeAdjustmentYearImpactSummary } from './compute-adjustment-year-impact-summary'
import { computePanelAdjustmentBalance } from './compute-panel-adjustment-balance'
import { computeAdjustmentSurfaceImpact } from './compute-adjustment-surface-impact'
import { computeAdjustedPriceRangeNarrowing } from './compute-adjusted-price-range-narrowing'
import { computeAdjustmentNetPctHistogram } from './compute-adjustment-net-pct-histogram'
import { computeGrossAdjustmentOEAQCheck } from './compute-gross-adjustment-oeaq-check'
import { computeAdjustmentMagnitudeRanking } from './compute-adjustment-magnitude-ranking'
import { computeReconciliationWeightDistribution } from './compute-reconciliation-weight-distribution'
import { computeAdjustmentNetPerCompSummary } from './compute-adjustment-net-per-comp-summary'
import { computeAdjustmentEfficiencyRatio } from './compute-adjustment-efficiency-ratio'

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
  subjectHabM2?: number | null,
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

  // Valuation conclusion (structured summary)
  const valuationConclusion = adjustments.length > 0
    ? computeValuationConclusion(adjustments, comparables ?? [])
    : null
  if (valuationConclusion) {
    const reliabilityColor = valuationConclusion.reliability === 'élevée' ? '#1f7a5c'
      : valuationConclusion.reliability === 'modérée' ? '#b45309' : '#b91c1c'
    const vcRows = [
      ['Valeur réconciliée', `<strong>${fmtMoney(valuationConclusion.reconciledValue)}</strong>`],
      ['Intervalle ±1σ', `${fmtMoney(valuationConclusion.confidenceRange.low)} – ${fmtMoney(valuationConclusion.confidenceRange.high)}`],
      ['Dispersion (CV)', `${fmt(valuationConclusion.cv, 1)} %`],
      ['Fiabilité globale', `<strong style="color:${reliabilityColor};">${valuationConclusion.reliability}</strong>`],
      ...(valuationConclusion.oeaqWarnings > 0 ? [['Alertes OEAQ', `<span style="color:#b45309;">${valuationConclusion.oeaqWarnings} avertissement${valuationConclusion.oeaqWarnings > 1 ? 's' : ''}</span>`]] : []),
      ...(valuationConclusion.hasTimeAdjustment && valuationConclusion.annualTimeRatePct !== null ? [[`Taux temporel`, `<span style="color:${valuationConclusion.annualTimeRatePct >= 0 ? '#1f7a5c' : '#b91c1c'};">${valuationConclusion.annualTimeRatePct >= 0 ? '+' : ''}${fmt(valuationConclusion.annualTimeRatePct, 1)} %/an</span>`]] : []),
      ...((() => { const nc = comparables && comparables.length > 0 ? computeNeighborhoodComparability(comparables, adjustments) : null; return nc ? [[`Comparabilité voisinage`, `<span style="color:${nc.strength === 'forte' ? '#1f7a5c' : nc.strength === 'modérée' ? '#b45309' : '#b91c1c'};">${nc.strength} (${nc.score}/100)</span>`]] : [] })()),
      ...((() => { const vrc = conclusion !== null && adjustments.length >= 2 ? computeValueRangeConfidence(adjustments, conclusion) : null; return vrc ? [[`Intervalle confiance (±1σ)`, `${fmtMoney(vrc.band1Sigma.low)} – ${fmtMoney(vrc.band1Sigma.high)}<br><span style="font-size:8pt;font-weight:400;color:#8a8780;">confiance conclusion&nbsp;: <strong style="color:${vrc.conclusionConfidence === 'haute' ? '#1f7a5c' : vrc.conclusionConfidence === 'modérée' ? '#b45309' : '#b91c1c'};">${vrc.conclusionConfidence}</strong></span>`]] : [] })()),
      ...((() => { const wm = adjustments.length >= 2 ? computeAdjustmentWeightedMedian(adjustments) : null; return wm && Math.abs(wm.deltaPct) >= 0.5 ? [[`Médiane pondérée`, `${fmtMoney(wm.weightedMedian)} <span style="font-size:8pt;font-weight:400;color:#8a8780;">(${wm.deltaPct > 0 ? '+' : ''}${fmt(wm.deltaPct, 1)} % vs médiane simple)</span>`]] : [] })()),
      ...((() => { const wam = adjustments.length >= 2 ? computeWeightedAdjustedMean(adjustments) : null; if (!wam || Math.abs(wam.deltaVsSimplePct) < 0.5) return []; const color = wam.deltaVsSimplePct > 0 ? '#1f7a5c' : '#b91c1c'; return [[`Moyenne pondérée vs simple`, `<span style="color:${color};">${fmtMoney(wam.weightedMean)}</span> <span style="font-size:8pt;font-weight:400;color:#8a8780;">(${wam.deltaVsSimplePct > 0 ? '+' : ''}${fmt(wam.deltaVsSimplePct, 1)} % vs ${fmtMoney(wam.simpleMean)})</span>`]] })()),
      ...((() => { const lp = financier?.valeur_mediane_logement != null ? computeLocationPremium(valuationConclusion.reconciledValue, financier.valeur_mediane_logement) : null; if (!lp) return []; const color = lp.signal === 'prime' ? '#b45309' : lp.signal === 'escompte' ? '#0369a1' : '#1f7a5c'; return [[`Prime de localisation`, `<span style="color:${color};font-weight:600;">${lp.signal}</span> <span style="font-size:8pt;font-weight:400;color:#8a8780;">(${lp.deltaPct > 0 ? '+' : ''}${fmt(lp.deltaPct, 1)} % vs médiane&nbsp;${fmtMoney(financier!.valeur_mediane_logement!)})</span>`]] })()),
      ...((() => { const db = adjustments.length >= 2 ? computeAdjustmentDirectionBalance(adjustments) : null; if (!db || db.balanced) return []; const color = '#b45309'; const dirLabel = db.direction === 'upward' ? 'positifs' : 'négatifs'; const dirPct = db.direction === 'upward' ? db.upPct : db.downPct; return [[`Biais d'ajustement`, `<span style="color:${color};">${fmt(dirPct, 0)} % ${dirLabel}</span> <span style="font-size:8pt;font-weight:400;color:#8a8780;">(${db.upCount}↑ ${db.downCount}↓ ${db.neutralCount}=)</span>`]] })()),
      ...((() => { const vm = subjectHabM2 != null && subjectHabM2 > 0 ? computeValuePerM2Conclusion(valuationConclusion.reconciledValue, subjectHabM2, comparables ?? []) : null; if (!vm) return []; const color = vm.signal === 'haut' ? '#b45309' : vm.signal === 'bas' ? '#0369a1' : '#1f7a5c'; const vsNote = vm.vsMedianPct != null ? ` <span style="font-size:8pt;font-weight:400;color:#8a8780;">(${vm.vsMedianPct > 0 ? '+' : ''}${fmt(vm.vsMedianPct, 1)} % vs médiane comparables ${vm.medianCompM2 != null ? fmt(vm.medianCompM2, 0) + ' $/m²' : ''})</span>` : ''; return [[`Valeur au m² (sujet)`, `<span style="color:${color};font-weight:600;">${fmt(vm.pricePerM2, 0)} $/m²${vm.signal ? ` — ${vm.signal}` : ''}</span>${vsNote}`]] })()),
      ...((() => { const conv = adjustments.length >= 3 ? computeAdjustmentConvergence(adjustments) : null; if (!conv) return []; const color = conv.converged ? '#1f7a5c' : '#b45309'; const sign = conv.convergencePct > 0 ? '+' : ''; return [[`Convergence des ajustements`, `<span style="color:${color};font-weight:600;">${conv.converged ? 'convergente' : 'divergente'}</span> <span style="font-size:8pt;font-weight:400;color:#8a8780;">(CV brut ${fmt(conv.rawCv, 1)} % → ajusté ${fmt(conv.adjustedCv, 1)} %, ${sign}${fmt(conv.convergencePct, 1)} %)</span>`]] })()),
      ...((() => { const ti = adjustments.length > 0 ? computeTimeAdjustmentImpact(adjustments) : null; if (!ti || ti.avgYearAdjPctOfGross == null) return []; const color = ti.timeAdjustmentDominant ? '#b45309' : '#6a6763'; return [[`Impact ajustement temporel`, `<span style="color:${color};font-weight:${ti.timeAdjustmentDominant ? '600' : '400'};">${fmt(ti.avgYearAdjPctOfGross, 1)} % du brut (moy.)</span>${ti.timeAdjustmentDominant ? ' <span style="font-size:8pt;color:#b45309;">⚠ dominant</span>' : ''}`]] })()),
      ...((() => { const gnr = adjustments.length > 0 ? computeGrossToNetRatio(adjustments) : null; if (!gnr || gnr.avgRatio == null || gnr.avgRatio <= 1.5) return []; const color = gnr.avgRatio > 3 ? '#b91c1c' : '#b45309'; return [[`Annulation des ajustements`, `<span style="color:${color};font-weight:600;">ratio ${fmt(gnr.avgRatio, 2)}</span> <span style="font-size:8pt;font-weight:400;color:#8a8780;">(${gnr.highCancellationIds.length} comp. en forte annulation)</span>`]] })()),
    ].map(([label, val]) => `<tr><td style="color:#6a6763;">${label}</td><td style="text-align:right;">${val}</td></tr>`).join('')
    sections.push(`
      <h2>Conclusion structurée</h2>
      <table><tbody>${vcRows}</tbody></table>
    `)
  }

  // Appraisal risk score
  if (adjustments.length > 0) {
    const risk = computeAppraisalRiskScore(adjustments, comparables ?? [])
    if (risk) {
      const riskColor = risk.riskLevel === 'faible' ? '#1f7a5c'
        : risk.riskLevel === 'modéré' ? '#b45309' : '#b91c1c'
      const factorsHtml = risk.factors.length > 0
        ? `<span style="font-size:9pt;color:#8a8780;"> — ${risk.factors.join(' · ')}</span>`
        : ''
      sections.push(`
        <p style="font-size:10pt;margin-top:4pt;">
          Risque dossier&nbsp;:
          <strong style="color:${riskColor};">${risk.riskLevel} (${risk.score}/100)</strong>
          ${factorsHtml}
        </p>
      `)
    }
  }

  // Data quality
  if (comparables && comparables.length > 0) {
    const dqr = computeDataQualityReport(comparables, adjustments)
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

  // Dispersion stats
  const priceStats = adjustments.length >= 2 ? computeAdjustedPriceStats(adjustments) : null

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
      ${priceStats ? `<p style="font-size:10pt;color:#6a6763;">Dispersion des valeurs indiquées&nbsp;: CV&nbsp;<strong>${fmt(priceStats.cv, 1)} %</strong> — cohésion ${priceStats.cohesion}</p>` : ''}
      ${(() => {
        const bracket = adjustments.length > 0 ? computeAdjustmentBracketAnalysis(adjustments, conclusion) : null
        if (!bracket) return ''
        return bracket.isBracketed
          ? `<p style="font-size:10pt;color:#1f7a5c;">Encadrement OEAQ&nbsp;: ✓ conclusion encadrée par les valeurs indiquées.</p>`
          : `<p style="font-size:10pt;color:#b45309;">⚠ Encadrement OEAQ&nbsp;: conclusion non encadrée${!bracket.hasBelow ? ' (aucun comparable en-dessous)' : ' (aucun comparable au-dessus)'} — justification requise.</p>`
      })()}
      <blockquote>À titre indicatif uniquement — validation et signature par un évaluateur agréé requises avant toute diffusion.</blockquote>
    `)
  }

  // Market positioning
  if (conclusion !== null && adjustments.length > 0) {
    const pos = computeMarketPositioning(conclusion, adjustments)
    if (pos) {
      const posColor = pos.position === 'bas' ? '#0369a1'
        : pos.position === 'haut' ? '#b45309' : '#1f7a5c'
      const nearLines: string[] = []
      if (pos.nearestBelow) nearLines.push(`comparable le plus proche en-dessous&nbsp;: <strong>${pos.nearestBelow.label}</strong> (−${fmtMoney(pos.nearestBelow.delta)})`)
      if (pos.nearestAbove) nearLines.push(`comparable le plus proche au-dessus&nbsp;: <strong>${pos.nearestAbove.label}</strong> (+${fmtMoney(pos.nearestAbove.delta)})`)
      sections.push(`
        <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
          Positionnement de la conclusion&nbsp;: <strong style="color:${posColor};">${pos.position}</strong>
          (rang percentile&nbsp;: ${pos.percentileRank}&nbsp;%,
          ${pos.countBelow}&nbsp;comp. en-dessous, ${pos.countAbove}&nbsp;au-dessus sur ${pos.total})
          ${nearLines.length > 0 ? `<br><span style="font-size:9pt;">` + nearLines.join(' · ') + `</span>` : ''}
        </p>
      `)
    }
  }

  // Adjustments table
  if (adjustments.length > 0) {
    const outliers = detectOutlierComparables(adjustments)
    const outlierMap = new Map(outliers.map(o => [o.id, o]))
    const reconciledWeights = adjustments.length > 1 ? (computeReconciledValue(adjustments)?.weights ?? {}) : {}
    const netEffects = computeAdjustmentNetEffect(adjustments)
    const netEffectMap = new Map(netEffects.map(e => [e.comparableId, e]))
    const rows = adjustments.map(a => {
      const outlier = outlierMap.get(a.id)
      const weightPct = reconciledWeights[a.id]
      const netEffect = netEffectMap.get(a.comparable_id)
      const subLines: string[] = []
      if (outlier?.isOutlier) subLines.push(`<span style="font-size:8pt;font-weight:400;color:#b45309;">${outlier.deviationFromMedianPct > 0 ? '+' : ''}${fmt(outlier.deviationFromMedianPct)} % vs méd.</span>`)
      if (weightPct != null) subLines.push(`<span style="font-size:8pt;font-weight:400;color:#8a8780;">poids ${weightPct} %</span>`)
      if (netEffect && netEffect.direction !== 'neutre') {
        const netColor = netEffect.direction === 'positif' ? '#1f7a5c' : '#b91c1c'
        subLines.push(`<span style="font-size:8pt;font-weight:400;color:${netColor};">net ${netEffect.netPct > 0 ? '+' : ''}${fmt(netEffect.netPct, 1)} % (${netEffect.magnitude})</span>`)
      }
      const adjustedCell = `<td style="text-align:right;font-weight:700;">${fmtMoney(a.adjusted)}${subLines.length > 0 ? '<br>' + subLines.join('<br>') : ''}</td>`
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

    // Gross adjustment ceiling report
    const ceilingReport = computeGrossAdjustmentCeiling(adjustments)
    if (ceilingReport && !ceilingReport.compliant) {
      const violRows = ceilingReport.entries.filter(e => e.hasViolation).map(e => {
        const lineFail = e.exceedsLineCeiling ? `<span style="color:#b91c1c;">ligne max ${e.maxLinePct} %</span>` : ''
        const totalFail = e.exceedsTotalCeiling ? `<span style="color:#b45309;">total ${e.totalGrossPct} %</span>` : ''
        const fails = [lineFail, totalFail].filter(Boolean).join(', ')
        return `<tr><td style="color:#6a6763;">${e.comparableLabel}</td><td style="text-align:right;">${fails}</td></tr>`
      }).join('')
      sections.push(`
        <div style="background:#fef2f2;border:1pt solid #fecaca;border-radius:4pt;padding:8pt 10pt;margin-top:8pt;">
          <p style="font-weight:600;color:#b91c1c;font-size:10pt;margin:0 0 4pt;">⚠ Plafonds OEAQ dépassés (${ceilingReport.violationCount} comparable${ceilingReport.violationCount > 1 ? 's' : ''})</p>
          <p style="font-size:9pt;color:#b91c1c;margin:0 0 4pt;">Ligne &gt; 15 % ou total brut &gt; 25 % — justification obligatoire</p>
          <table style="margin:0;"><tbody>${violRows}</tbody></table>
        </div>
      `)
    }

    // Adjustment profile
    const profile = computeAdjustmentProfile(adjustments)
    if (profile && profile.grossTotal > 0) {
      const active = profile.types.filter(t => t.totalAbsolute > 0)
      const profileRows = active.map(t => {
        const color = t.direction === 'positive' ? '#1f7a5c' : t.direction === 'negative' ? '#b91c1c' : '#8a8780'
        const avgStr = `${t.avgPerComp >= 0 ? '+' : ''}${fmtMoney(t.avgPerComp)}`
        return `<tr>
          <td style="color:#6a6763;">${t.label}</td>
          <td style="text-align:right;color:${color};font-weight:600;">${t.pctOfGrossTotal}%</td>
          <td style="text-align:right;color:${color};">${avgStr} / comp.</td>
        </tr>`
      }).join('')
      sections.push(`
        <h2>Répartition des ajustements</h2>
        <table><tbody>${profileRows}</tbody></table>
      `)
    }

    // B147: adjustment coverage by type
    const coverage = computeAdjustmentCoverageByType(adjustments)
    if (coverage) {
      const unusedNote = coverage.unusedTypes.length > 0
        ? ` · non utilisés&nbsp;: ${coverage.unusedTypes.map(t => ({ surface: 'Surface', year: 'Année', condition: 'État', garage: 'Garage' })[t]).join(', ')}`
        : ''
      const universalNote = coverage.universalTypes.length > 0
        ? `Universels (≥ 80 %)&nbsp;: ${coverage.universalTypes.map(t => ({ surface: 'Surface', year: 'Année', condition: 'État', garage: 'Garage' })[t]).join(', ')}. `
        : ''
      sections.push(`
        <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
          ${universalNote}Couverture par type&nbsp;: ${coverage.entries.filter(e => e.coveragePct > 0).map(e => `${e.label} ${e.coveragePct} %`).join(' · ')}${unusedNote}
        </p>
      `)
    }

    // B132: adjustment type ratio check (over-reliance flag)
    const ratioCheck = computeAdjustmentTypeRatioCheck(adjustments)
    if (ratioCheck?.hasOverReliance) {
      const overType = ratioCheck.entries.find(e => e.overReliance)
      if (overType) {
        sections.push(`
          <div style="background:#fffbeb;border:1pt solid #fcd34d;border-radius:4pt;padding:8pt 10pt;margin-top:6pt;">
            <p style="font-weight:600;color:#b45309;font-size:10pt;margin:0 0 2pt;">⚠ Dépendance excessive — ${overType.label}</p>
            <p style="font-size:9pt;color:#b45309;margin:0;">${overType.label} représente <strong>${overType.pctOfGross} %</strong> de l'ajustement brut total — justifier la prédominance de ce facteur.</p>
          </div>
        `)
      }
    }

    // B124: adjustment magnitude profile
    const magnitudeProfile = computeAdjustmentMagnitudeProfile(adjustments)
    if (magnitudeProfile) {
      const activeEntries = magnitudeProfile.entries.filter(e => e.nonZeroCount > 0)
      if (activeEntries.length > 0) {
        const magRows = activeEntries.map(e => {
          const isDominant = e.type === magnitudeProfile.dominantType
          return `<tr>
            <td style="color:#6a6763;${isDominant ? 'font-weight:600;' : ''}">${e.label}</td>
            <td style="text-align:right;">${e.nonZeroCount}/${adjustments.length} comp. (${fmt(e.pctOfComps, 0)} %)</td>
            <td style="text-align:right;font-weight:600;">${fmtMoney(e.avgAbsolute)} moy.</td>
            <td style="text-align:right;font-size:9pt;color:#8a8780;">max ${fmtMoney(e.maxAbsolute)}</td>
          </tr>`
        }).join('')
        sections.push(`
          <h2>Magnitude des ajustements</h2>
          <table>
            <thead><tr><th>Type</th><th style="text-align:right;">Fréquence</th><th style="text-align:right;">Moyenne</th><th style="text-align:right;">Maximum</th></tr></thead>
            <tbody>${magRows}</tbody>
          </table>
        `)
      }
    }

    // Reconciled value
    const reconciled = computeReconciledValue(adjustments)
    if (reconciled && adjustments.length > 1) {
      sections.push(`
        <p style="font-size:11pt;color:#6a6763;margin-top:6pt;">
          Valeur réconciliée (pondérée — adj. brut)&nbsp;:
          <strong style="color:#1a1916;">${fmtMoney(reconciled.value)}</strong>
          <span style="font-size:9pt;"> — confiance ${reconciled.confidence}</span>
        </p>
      `)
    }

    // B137: reconciliation concentration
    if (adjustments.length >= 2) {
      const concentration = computeReconciliationConcentration(adjustments)
      if (concentration?.concentrated) {
        const maxAdj = adjustments.find(a => a.id === concentration.maxWeightId)
        const label = maxAdj?.comparableLabel ?? concentration.maxWeightId
        sections.push(`
          <div style="background:#fffbeb;border:1pt solid #fcd34d;border-radius:4pt;padding:8pt 10pt;margin-top:6pt;">
            <p style="font-weight:600;color:#b45309;font-size:10pt;margin:0 0 2pt;">⚠ Concentration de la réconciliation</p>
            <p style="font-size:9pt;color:#b45309;margin:0;"><strong>${label}</strong> porte <strong>${concentration.maxWeightPct} %</strong> du poids total (HHI ${fmt(concentration.hhi, 3)}) — résultat sensible à ce seul comparable.</p>
          </div>
        `)
      }
    }

    // B133: reconciled value bracket
    if (reconciled && adjustments.length > 1) {
      const rvBracket = computeReconciledValueBracket(adjustments, reconciled.value)
      if (rvBracket && !rvBracket.bracketed) {
        sections.push(`
          <p style="font-size:10pt;color:#b45309;margin-top:4pt;">
            ⚠ Valeur réconciliée hors de la fourchette des valeurs indiquées
            (${fmtMoney(rvBracket.min)} – ${fmtMoney(rvBracket.max)},
            écart ${fmt(rvBracket.deviationPct, 1)} %) — réviser la pondération.
          </p>
        `)
      }
    }

    // Consistency warnings
    if (adjustments.length >= 2) {
      const consistencyChecks = computeAdjustmentConsistency(adjustments)
      const inconsistent = consistencyChecks.filter(c => !c.consistent)
      if (inconsistent.length > 0) {
        const warningItems = inconsistent.map(c => `<li>${c.warning}</li>`).join('')
        sections.push(`
          <div style="background:#fffbeb;border:1pt solid #fcd34d;border-radius:4pt;padding:8pt 10pt;margin-top:8pt;">
            <p style="font-weight:600;color:#b45309;font-size:10pt;margin:0 0 4pt;">⚠ Cohérence des ajustements</p>
            <ul style="margin:0;padding-left:16pt;color:#b45309;font-size:9pt;">${warningItems}</ul>
          </div>
        `)
      }
    }

    // Adjustment symmetry
    if (adjustments.length >= 3) {
      const symmetry = computeAdjustmentSymmetry(adjustments)
      if (symmetry && !symmetry.overallSymmetric) {
        const typeNames: Record<string, string> = { surface: 'Surface', year: 'Année', condition: 'État', garage: 'Garage' }
        const asymTypes = Object.entries(symmetry)
          .filter(([k, v]) => ['surface','year','condition','garage'].includes(k) && typeof v === 'object' && !(v as {symmetric: boolean}).symmetric && (v as {mean: number}).mean !== 0)
          .map(([k]) => typeNames[k] ?? k)
        if (asymTypes.length > 0) {
          sections.push(`
            <div style="background:#fffbeb;border:1pt solid #fcd34d;border-radius:4pt;padding:8pt 10pt;margin-top:8pt;">
              <p style="font-weight:600;color:#b45309;font-size:10pt;margin:0 0 4pt;">⚠ Symétrie des ajustements</p>
              <p style="font-size:9pt;color:#b45309;margin:0;">Variation élevée (CV > 50 %) détectée pour&nbsp;: ${asymTypes.join(', ')} — application non homogène entre comparables.</p>
            </div>
          `)
        }
      }
    }

    // B139: adjustment outlier by type
    if (adjustments.length >= 3) {
      const adjOutliers = computeAdjustmentOutlierByType(adjustments)
      if (adjOutliers?.hasOutliers) {
        const typeLabels: Record<string, string> = { surface: 'Surface', year: 'Année', condition: 'État', garage: 'Garage' }
        const flagged = (['surface', 'year', 'condition', 'garage'] as const)
          .filter(k => adjOutliers[k].outlierIds.length > 0)
          .map(k => {
            const t = adjOutliers[k]
            const ids = t.outlierIds.join(', ')
            return `${typeLabels[k]}: ${ids} (moy. ${fmtMoney(t.mean)}, σ ${fmtMoney(t.stdDev)})`
          })
        if (flagged.length > 0) {
          sections.push(`
            <div style="background:#fffbeb;border:1pt solid #fcd34d;border-radius:4pt;padding:8pt 10pt;margin-top:8pt;">
              <p style="font-weight:600;color:#b45309;font-size:10pt;margin:0 0 4pt;">⚠ Ajustements atypiques par type (&gt; 2σ)</p>
              <ul style="margin:0;padding-left:16pt;color:#b45309;font-size:9pt;">${flagged.map(f => `<li>${f}</li>`).join('')}</ul>
            </div>
          `)
        }
      }
    }

    // Sensitivity analysis
    if (adjustments.length >= 3) {
      const sensitivity = computeSensitivityAnalysis(adjustments)
      if (sensitivity) {
        const sensRows = sensitivity.entries.map(e => {
          const color = e.influential ? '#b45309' : '#6a6763'
          const sign = e.deltaPct > 0 ? '+' : ''
          return `<tr>
            <td style="color:#6a6763;">Sans ${e.comparableLabel}</td>
            <td style="text-align:right;font-weight:600;">${fmtMoney(e.reconciledWithout)}</td>
            <td style="text-align:right;color:${color};">${sign}${fmt(e.deltaPct, 1)} %${e.influential ? ' ⚠' : ''}</td>
          </tr>`
        }).join('')
        sections.push(`
          <h2>Sensibilité de la réconciliation</h2>
          <table>
            <thead><tr><th>Exclusion</th><th style="text-align:right;">Réconcilié</th><th style="text-align:right;">Écart</th></tr></thead>
            <tbody>${sensRows}</tbody>
          </table>
        `)
      }
    }

    // Vintage analysis
    if (comparables && comparables.length > 0) {
      const vintage = computeComparableVintageAnalysis(comparables)
      if (vintage && vintage.vintageBias) {
        sections.push(`
          <div style="background:#fffbeb;border:1pt solid #fcd34d;border-radius:4pt;padding:8pt 10pt;margin-top:8pt;">
            <p style="font-weight:600;color:#b45309;font-size:10pt;margin:0 0 4pt;">⚠ Biais de millésime</p>
            <p style="font-size:9pt;color:#b45309;margin:0;">Aucun comparable dans un rayon de ±20 ans autour de l'immeuble sujet${vintage.subjectDecade ? ` (${vintage.subjectDecade})` : ''} — représentativité du parc à justifier.</p>
          </div>
        `)
      }
    }

    // Time adjustment rate note
    if (comparables && comparables.length >= 2) {
      const timeRate = computeTimeAdjustmentRate(comparables)
      if (timeRate) {
        const color = timeRate.annualRatePct >= 0 ? '#1f7a5c' : '#b91c1c'
        sections.push(`
          <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
            Taux implicite d'appréciation (${timeRate.basedOn}&nbsp;paire${timeRate.basedOn !== 1 ? 's' : ''})&nbsp;:
            <strong style="color:${color};">${timeRate.annualRatePct >= 0 ? '+' : ''}${fmt(timeRate.annualRatePct, 1)}&nbsp;%/an</strong>
            <span style="font-size:9pt;color:#8a8780;">— confiance ${timeRate.confidence}</span>
          </p>
        `)
      }

      // B144: gross adjustment trend vs age
      if (comparables.length >= 3) {
        const adjTrend = computeGrossAdjustmentTrend(comparables, adjustments)
        if (adjTrend?.significant && adjTrend.direction !== 'stable') {
          const color = adjTrend.direction === 'increasing' ? '#b45309' : '#0369a1'
          const sign = adjTrend.slopePerMonth > 0 ? '+' : ''
          sections.push(`
            <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
              Tendance ajustements bruts&nbsp;:
              <span style="color:${color};font-weight:600;">${adjTrend.direction === 'increasing' ? '↑ croissants avec l\'ancienneté' : '↓ décroissants avec l\'ancienneté'}</span>
              <span style="font-size:9pt;color:#8a8780;"> (${sign}${fmt(adjTrend.slopePerMonth, 2)} %/mois, R²=${fmt(adjTrend.r2, 2)})</span>
            </p>
          `)
        }
      }
    }
  }

  // Comparable ranking (needs both comparables and adjustments)
  if (comparables && comparables.length > 0 && adjustments.length > 0) {
    const ranking = computeComparableRanking(comparables, adjustments)
    if (ranking.length > 0) {
      const rankRows = ranking.map(r => `<tr>
        <td style="font-weight:600;color:${r.rank === 1 ? '#1f7a5c' : '#6a6763'};">#${r.rank}</td>
        <td>${r.comparableLabel}</td>
        <td style="text-align:right;">${fmt(r.qualityScore, 1)}/10</td>
        <td style="text-align:right;color:${r.isOutlier ? '#b45309' : '#6a6763'};">${r.isOutlier ? '⚠ atypique' : `${r.weightPct} %`}</td>
      </tr>`).join('')
      sections.push(`
        <h2>Classement des comparables</h2>
        <table>
          <thead><tr><th>#</th><th>Comparable</th><th style="text-align:right;">Qualité</th><th style="text-align:right;">Poids</th></tr></thead>
          <tbody>${rankRows}</tbody>
        </table>
      `)
    }
  }

  // B145: adjustment summary by comparable
  if (adjustments.length > 0) {
    const summaries = computeAdjustmentSummaryByComp(adjustments)
    if (summaries.length > 0) {
      const sumRows = summaries.map(s => {
        const dirColor = s.direction === 'upward' ? '#1f7a5c' : s.direction === 'downward' ? '#b91c1c' : '#8a8780'
        const grossColor = s.grossPct > 25 ? '#b91c1c' : s.grossPct > 15 ? '#b45309' : '#6a6763'
        return `<tr>
          <td>${s.comparableLabel}</td>
          <td style="text-align:right;color:${grossColor};font-weight:600;">${fmt(s.grossPct, 1)} %</td>
          <td style="text-align:right;color:${dirColor};font-weight:600;">${s.netPct > 0 ? '+' : ''}${fmt(s.netPct, 1)} %</td>
          <td style="text-align:right;font-size:9pt;color:${dirColor};">${fmtAdj(s.netAmount)}</td>
          <td style="text-align:right;font-size:9pt;color:#8a8780;">${s.magnitude}</td>
        </tr>`
      }).join('')
      sections.push(`
        <h2>Sommaire par comparable</h2>
        <table>
          <thead><tr><th>Comparable</th><th style="text-align:right;">Brut %</th><th style="text-align:right;">Net %</th><th style="text-align:right;">Net $</th><th style="text-align:right;">Magnitude</th></tr></thead>
          <tbody>${sumRows}</tbody>
        </table>
      `)
    }
  }

  // B152: adjustment line item stats
  if (adjustments.length > 0) {
    const lineItemStats = computeAdjustmentLineItemStats(adjustments)
    if (lineItemStats) {
      const typeLabels: Record<string, string> = { surface: 'Surface', year: 'Année', condition: 'État', garage: 'Garage' }
      const statRows = (['surface', 'year', 'condition', 'garage'] as const).map(k => {
        const s = lineItemStats[k]
        const signMin = s.min > 0 ? '+' : ''
        const signMax = s.max > 0 ? '+' : ''
        const signMean = s.mean > 0 ? '+' : ''
        return `<tr>
          <td style="color:#6a6763;">${typeLabels[k]}</td>
          <td style="text-align:right;font-size:9pt;">${signMin}${fmtAdj(s.min)}</td>
          <td style="text-align:right;font-size:9pt;">${signMax}${fmtAdj(s.max)}</td>
          <td style="text-align:right;font-size:9pt;font-weight:600;">${signMean}${fmtAdj(s.mean)}</td>
          <td style="text-align:right;font-size:9pt;">${s.mean > 0 ? '+' : ''}${fmtAdj(s.median)}</td>
        </tr>`
      }).join('')
      sections.push(`
        <h2>Ajustements par poste</h2>
        <table>
          <thead><tr><th>Poste</th><th style="text-align:right;">Min</th><th style="text-align:right;">Max</th><th style="text-align:right;">Moy.</th><th style="text-align:right;">Méd.</th></tr></thead>
          <tbody>${statRows}</tbody>
        </table>
      `)
    }
  }

  // B153: net adjustment range check (OEAQ: |net adj| ≤ 15% of sale price)
  if (adjustments.length > 0) {
    const rangeCheck = computeNetAdjustmentRangeCheck(adjustments)
    if (rangeCheck && !rangeCheck.compliant) {
      const violators = rangeCheck.entries.filter(e => e.violation)
      const violatorItems = violators.map(e =>
        `<li>${e.comparableLabel}&nbsp;: ${fmt(e.netAdjPct, 1)} % (${e.netAdj > 0 ? '+' : ''}${fmtAdj(e.netAdj)})</li>`
      ).join('')
      sections.push(`
        <div style="background:#fffbeb;border:1pt solid #fcd34d;border-radius:4pt;padding:8pt 10pt;margin-top:8pt;">
          <p style="font-weight:600;color:#b45309;font-size:10pt;margin:0 0 4pt;">⚠ Ajustement net &gt; 15 % du prix de vente (OEAQ)</p>
          <ul style="margin:0;padding-left:16pt;color:#b45309;font-size:9pt;">${violatorItems}</ul>
        </div>
      `)
    }
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
    // Holding cost estimate (when we have a conclusion price; use 5.5% as market proxy rate)
    if (conclusion !== null) {
      const holdingEst = computeHoldingCostEstimate(conclusion, 20, 5.5, 25)
      if (holdingEst) {
        rows.push(['Coût détention estimé (5 ans, 20 % MDP, taux 5,5 %)', fmtMoney(holdingEst.totalHoldingCost), `${fmtMoney(holdingEst.monthlyTotal)}/mois`])
      }
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

    // B128: OEAQ compliance summary score
    if (adjustments.length > 0) {
      const ceiling = computeGrossAdjustmentCeiling(adjustments)
      const bracket = conclusion != null ? computeAdjustmentBracketAnalysis(adjustments, conclusion) : null
      const symmetry = adjustments.length >= 3 ? computeAdjustmentSymmetry(adjustments) : null
      const summary = computeOEAQComplianceSummary(checks, ceiling, bracket, symmetry)
      if (summary) {
        const gradeColor = summary.grade === 'conforme' ? '#1f7a5c' : summary.grade === 'attention' ? '#b45309' : '#b91c1c'
        sections.push(`
          <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
            Score de conformité OEAQ&nbsp;:
            <strong style="color:${gradeColor};">${summary.grade} (${summary.score}/100)</strong>
            <span style="font-size:9pt;color:#8a8780;"> — ${summary.passCount} critères satisfaits, ${summary.failCount} à corriger</span>
          </p>
        `)
      }

      // B140: OEAQ bracketing summary
      const sizeRangeForBracket = null  // subject size not available in this context
      const rvBracketForCheck = (() => {
        const reconciled = computeReconciledValue(adjustments)
        return reconciled && adjustments.length > 1 ? computeReconciledValueBracket(adjustments, reconciled.value) : null
      })()
      const bracketSummary = computeOEAQBracketingSummary(bracket, sizeRangeForBracket, rvBracketForCheck)
      if (bracketSummary) {
        const allColor = bracketSummary.allBracketed ? '#1f7a5c' : '#b45309'
        const checks3 = [
          bracketSummary.pricesBracketed !== null ? `Prix&nbsp;: ${bracketSummary.pricesBracketed ? '✓' : '⚠'}` : null,
          bracketSummary.sizeBracketed !== null ? `Surface&nbsp;: ${bracketSummary.sizeBracketed ? '✓' : '⚠'}` : null,
          bracketSummary.reconciledBracketed !== null ? `Réconcilié&nbsp;: ${bracketSummary.reconciledBracketed ? '✓' : '⚠'}` : null,
        ].filter(Boolean).join(' · ')
        sections.push(`
          <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
            Encadrement global OEAQ&nbsp;:
            <strong style="color:${allColor};">${bracketSummary.allBracketed ? '✓ tous les critères satisfaits' : `⚠ ${bracketSummary.failedChecks.length} critère${bracketSummary.failedChecks.length > 1 ? 's' : ''} non respecté${bracketSummary.failedChecks.length > 1 ? 's' : ''}`}</strong>
            <span style="font-size:9pt;color:#8a8780;"> — ${checks3}</span>
          </p>
        `)
      }
    }
  }

  // B155: adjustment explained variance
  if (adjustments.length >= 2) {
    const explVar = computeAdjustmentExplainedVariance(adjustments)
    if (explVar) {
      const color = explVar.interpretation === 'forte' ? '#1f7a5c' : explVar.interpretation === 'aucune' ? '#b91c1c' : explVar.interpretation === 'faible' ? '#b45309' : '#6a6763'
      const sign = explVar.varianceReductionPct > 0 ? '' : ''
      sections.push(`
        <p style="font-size:10pt;color:#6a6763;margin-top:6pt;">
          Réduction de variance par les ajustements&nbsp;:
          <strong style="color:${color};">${explVar.interpretation} (${fmt(explVar.varianceReductionPct, 1)} %)</strong>
          <span style="font-size:9pt;color:#8a8780;"> — var. brute ${fmtMoney(Math.sqrt(explVar.saleVariance))}σ → ajustée ${fmtMoney(Math.sqrt(explVar.adjustedVariance))}σ</span>
        </p>
      `)
    }
  }

  // B156: adjusted price CV vs raw CV
  if (adjustments.length >= 2) {
    const adjCV = computeAdjustedPriceCV(adjustments)
    if (adjCV) {
      const color = adjCV.homogenized ? '#1f7a5c' : '#b45309'
      const sign = adjCV.delta > 0 ? '+' : ''
      sections.push(`
        <p style="font-size:10pt;color:#6a6763;margin-top:6pt;">
          CV brut vs ajusté&nbsp;:
          <strong style="color:${color};">${fmt(adjCV.rawCV, 1)} % → ${fmt(adjCV.adjustedCV, 1)} % (${sign}${fmt(adjCV.delta, 1)} pp)</strong>
          <span style="font-size:9pt;color:#8a8780;"> — ${adjCV.homogenized ? 'ajustements ont homogénéisé le panel' : 'ajustements ont augmenté la dispersion'}</span>
        </p>
      `)
    }
  }

  // B158: net adjustment sign bias
  if (adjustments.length >= 2) {
    const signBias = computeNetAdjustmentSignBias(adjustments)
    if (signBias && signBias.biased) {
      const dirLabel: Record<string, string> = { upward: 'à la hausse', downward: 'à la baisse', neutral: 'neutres' }
      sections.push(`
        <p style="font-size:10pt;color:#b45309;margin-top:4pt;">
          ⚠ Biais directionnel des ajustements nets&nbsp;:
          <strong>${fmt(signBias.dominancePct, 0)} % ${dirLabel[signBias.dominantDirection]}</strong>
          <span style="font-size:9pt;color:#8a8780;"> (↑ ${signBias.countUpward} · ↓ ${signBias.countDownward} · ≈ ${signBias.countNeutral})</span>
        </p>
      `)
    }
  }

  // B159: gross adjustment distribution
  if (adjustments.length >= 2) {
    const grossDist = computeGrossAdjustmentDistribution(adjustments)
    if (grossDist) {
      sections.push(`
        <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
          Distribution des ajustements bruts&nbsp;:
          <strong>${fmt(grossDist.min, 1)} % – ${fmt(grossDist.max, 1)} %</strong>
          <span style="font-size:9pt;color:#8a8780;"> — moy. ${fmt(grossDist.mean, 1)} % · méd. ${fmt(grossDist.median, 1)} % · CV ${fmt(grossDist.cv, 0)} %</span>
        </p>
      `)
    }
  }

  // B160: zero rate by type
  if (adjustments.length > 0) {
    const zeroRate = computeAdjustmentZeroRateByType(adjustments)
    if (zeroRate && zeroRate.unusedTypes.length > 0) {
      sections.push(`
        <p style="font-size:10pt;color:#8a8780;margin-top:4pt;">
          Postes non utilisés&nbsp;: <strong>${zeroRate.unusedTypes.join(', ')}</strong>
          ${zeroRate.universalTypes.length > 0 ? `· universels&nbsp;: <strong>${zeroRate.universalTypes.join(', ')}</strong>` : ''}
        </p>
      `)
    }
  }

  // B161: $/m² convergence
  if (comparables && comparables.length >= 2 && adjustments.length >= 2) {
    const m2conv = computePricePerM2Convergence(comparables, adjustments)
    if (m2conv) {
      const color = m2conv.converged ? '#1f7a5c' : '#b45309'
      const sign = m2conv.delta > 0 ? '+' : ''
      sections.push(`
        <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
          Convergence $/m²&nbsp;:
          <strong style="color:${color};">${m2conv.converged ? '✓ homogénéisé' : '⚠ divergence'}</strong>
          <span style="font-size:9pt;color:#8a8780;"> — CV brut ${fmt(m2conv.rawM2CV, 1)} % → ajusté ${fmt(m2conv.adjustedM2CV, 1)} % (${sign}${fmt(m2conv.delta, 1)} pp)</span>
        </p>
      `)
    }
  }

  // B162: dominant type by comp
  if (adjustments.length > 0) {
    const domType = computeAdjustmentDominantTypeByComp(adjustments)
    if (domType && domType.mostCommonDominantType !== 'none') {
      const typeLabels: Record<string, string> = { surface: 'Surface', year: 'Année', condition: 'État', garage: 'Garage' }
      const label = typeLabels[domType.mostCommonDominantType] ?? domType.mostCommonDominantType
      sections.push(`
        <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
          Poste dominant&nbsp;: <strong>${label}</strong>
          <span style="font-size:9pt;color:#8a8780;"> — facteur principal pour la majorité des comparables</span>
        </p>
      `)
    }
  }

  // B163: sale price residuals vs reconciled value
  if (adjustments.length > 0 && conclusion !== null) {
    const residuals = computeSalePriceResidual(adjustments, conclusion)
    if (residuals && residuals.largeResidualIds.length > 0) {
      const items = residuals.entries
        .filter(e => e.large)
        .map(e => `<li>${e.comparableLabel}&nbsp;: ${fmt(e.residualPct, 1)} % (${fmtAdj(e.residualAmt)})</li>`)
        .join('')
      sections.push(`
        <div style="background:#fffbeb;border:1pt solid #fcd34d;border-radius:4pt;padding:8pt 10pt;margin-top:8pt;">
          <p style="font-weight:600;color:#b45309;font-size:10pt;margin:0 0 4pt;">⚠ Écarts importants vs valeur réconciliée (&gt; 5 %)</p>
          <ul style="margin:0;padding-left:16pt;color:#b45309;font-size:9pt;">${items}</ul>
        </div>
      `)
    }
  }

  // B165: median adjusted price vs reconciled value
  if (adjustments.length >= 2 && conclusion !== null) {
    const medAdj = computeMedianAdjustedPrice(adjustments, conclusion)
    if (medAdj && Math.abs(medAdj.deltaPct) >= 1) {
      const color = medAdj.deltaPct > 0 ? '#b45309' : '#0369a1'
      const sign = medAdj.delta > 0 ? '+' : ''
      sections.push(`
        <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
          Médiane ajustée&nbsp;: <strong>${fmtMoney(medAdj.median)}</strong>
          <span style="font-size:9pt;color:${color};"> — réconcilié ${sign}${fmt(medAdj.deltaPct, 1)} % vs médiane (${sign}${fmtMoney(medAdj.delta)})</span>
        </p>
      `)
    }
  }

  // B166: value indicator range (IQR of adjusted prices)
  if (adjustments.length >= 4) {
    const vir = computeValueIndicatorRange(adjustments)
    if (vir) {
      sections.push(`
        <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
          Fourchette indicative (IQR)&nbsp;:
          <strong>${fmtMoney(vir.q1)} – ${fmtMoney(vir.q3)}</strong>
          <span style="font-size:9pt;color:#8a8780;"> — IQR ${fmtMoney(vir.iqr)} · ${fmt(vir.iqrPct, 1)} % de la médiane · centre ${fmtMoney(vir.midpoint)}</span>
        </p>
      `)
    }
  }

  // B167: net magnitude profile
  if (adjustments.length > 0) {
    const magProfile = computeAdjustmentNetMagnitudeProfile(adjustments)
    if (magProfile && magProfile.countFort > 0) {
      sections.push(`
        <p style="font-size:10pt;color:#b45309;margin-top:4pt;">
          ⚠ Magnitude des ajustements nets&nbsp;: <strong>${magProfile.countFort} fort${magProfile.countFort > 1 ? 's' : ''}</strong>
          <span style="font-size:9pt;color:#8a8780;"> · ${magProfile.countModéré} modéré${magProfile.countModéré !== 1 ? 's' : ''} · ${magProfile.countFaible} faible${magProfile.countFaible !== 1 ? 's' : ''}</span>
        </p>
      `)
    }
  }

  // B169: condition adjustment bias
  if (adjustments.length > 0) {
    const condBias = computeAdjustmentConditionBias(adjustments)
    if (condBias && condBias.avgWhenApplied !== null) {
      const dirLabel: Record<string, string> = { positive: 'à la hausse', negative: 'à la baisse', neutral: 'neutre' }
      const color = condBias.dominantDirection === 'positive' ? '#1f7a5c' : condBias.dominantDirection === 'negative' ? '#b91c1c' : '#6a6763'
      sections.push(`
        <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
          Ajustement état&nbsp;:
          <strong style="color:${color};">${dirLabel[condBias.dominantDirection]}</strong>
          <span style="font-size:9pt;color:#8a8780;"> — ↑ ${condBias.countPositive} · ↓ ${condBias.countNegative} · ≈ ${condBias.countZero} · moy. appliqué ${fmtAdj(condBias.avgWhenApplied)}</span>
        </p>
      `)
    }
  }

  // B171: garage adjustment impact
  if (adjustments.length > 0) {
    const garageImpact = computeAdjustmentGarageImpact(adjustments)
    if (garageImpact && garageImpact.avgWhenApplied !== null) {
      const dirLabel: Record<string, string> = { positive: 'à la hausse', negative: 'à la baisse', neutral: 'neutre' }
      const color = garageImpact.dominantDirection === 'positive' ? '#1f7a5c' : garageImpact.dominantDirection === 'negative' ? '#b91c1c' : '#6a6763'
      sections.push(`
        <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
          Ajustement garage&nbsp;:
          <strong style="color:${color};">${dirLabel[garageImpact.dominantDirection]}</strong>
          <span style="font-size:9pt;color:#8a8780;"> — ↑ ${garageImpact.countPositive} · ↓ ${garageImpact.countNegative} · ≈ ${garageImpact.countZero} · moy. appliqué ${fmtAdj(garageImpact.avgWhenApplied)}</span>
        </p>
      `)
    }
  }

  // B172: adjusted price z-score outliers
  if (adjustments.length >= 3) {
    const zScores = computeAdjustedPriceZScore(adjustments)
    if (zScores && zScores.outlierIds.length > 0) {
      const outlierLabels = zScores.entries.filter(e => e.outlier).map(e => `${e.comparableLabel} (z=${fmt(e.zScore, 2)})`).join(', ')
      sections.push(`
        <div style="background:#fffbeb;border:1pt solid #fcd34d;border-radius:4pt;padding:8pt 10pt;margin-top:8pt;">
          <p style="font-weight:600;color:#b45309;font-size:10pt;margin:0 0 4pt;">⚠ Prix ajustés atypiques (|z| &gt; 2)</p>
          <p style="font-size:9pt;color:#b45309;margin:0;">${outlierLabels}</p>
        </div>
      `)
    }
  }

  // B174: year adjustment impact summary
  if (adjustments.length > 0) {
    const yearImpact = computeAdjustmentYearImpactSummary(adjustments)
    if (yearImpact && yearImpact.totalImpact !== 0) {
      const color = yearImpact.totalImpact > 0 ? '#1f7a5c' : '#b91c1c'
      const sign = yearImpact.totalImpact > 0 ? '+' : ''
      sections.push(`
        <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
          Impact temporel total&nbsp;:
          <strong style="color:${color};">${sign}${fmtMoney(yearImpact.totalImpact)}</strong>
          <span style="font-size:9pt;color:#8a8780;"> — moy. ${sign}${fmtAdj(yearImpact.avgPerComp)}/comp. · max ${fmtAdj(yearImpact.maxAbsValue)}</span>
        </p>
      `)
    }
  }

  // B175: panel adjustment balance
  if (adjustments.length > 0) {
    const balance = computePanelAdjustmentBalance(adjustments)
    if (balance) {
      const color = balance.netBalance > 0 ? '#1f7a5c' : balance.netBalance < 0 ? '#b91c1c' : '#6a6763'
      const sign = balance.netBalance > 0 ? '+' : ''
      sections.push(`
        <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
          Balance des ajustements&nbsp;:
          <strong style="color:${color};">${sign}${fmtMoney(balance.netBalance)}</strong>
          <span style="font-size:9pt;color:#8a8780;"> — ↑ ${fmtMoney(balance.totalPositive)} · ↓ ${fmtMoney(balance.totalNegative)} · solde ${sign}${fmt(balance.balancePct, 1)} %</span>
        </p>
      `)
    }
  }

  // B176: surface adjustment impact
  if (adjustments.length > 0) {
    const surfaceImpact = computeAdjustmentSurfaceImpact(adjustments)
    if (surfaceImpact && surfaceImpact.avgWhenApplied !== null) {
      const dirLabel: Record<string, string> = { positive: 'à la hausse', negative: 'à la baisse', neutral: 'neutre' }
      const color = surfaceImpact.dominantDirection === 'positive' ? '#1f7a5c' : surfaceImpact.dominantDirection === 'negative' ? '#b91c1c' : '#6a6763'
      sections.push(`
        <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
          Ajustement surface&nbsp;:
          <strong style="color:${color};">${dirLabel[surfaceImpact.dominantDirection]}</strong>
          <span style="font-size:9pt;color:#8a8780;"> — ↑ ${surfaceImpact.countPositive} · ↓ ${surfaceImpact.countNegative} · ≈ ${surfaceImpact.countZero} · moy. appliqué ${fmtAdj(surfaceImpact.avgWhenApplied)}</span>
        </p>
      `)
    }
  }

  // B178: adjusted price range narrowing
  if (adjustments.length >= 2) {
    const narrowing = computeAdjustedPriceRangeNarrowing(adjustments)
    if (narrowing) {
      const color = narrowing.narrowed ? '#1f7a5c' : '#b45309'
      const sign = narrowing.narrowingPct > 0 ? '' : ''
      sections.push(`
        <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
          Resserrement de la fourchette&nbsp;:
          <strong style="color:${color};">${narrowing.narrowed ? '✓' : '⚠'} ${fmt(narrowing.narrowingPct, 1)} %</strong>
          <span style="font-size:9pt;color:#8a8780;"> — brute ${fmtMoney(narrowing.rawRange)} → ajustée ${fmtMoney(narrowing.adjustedRange)}</span>
        </p>
      `)
    }
  }

  // B180: net pct histogram
  if (adjustments.length >= 3) {
    const histogram = computeAdjustmentNetPctHistogram(adjustments)
    if (histogram) {
      const nonEmpty = histogram.buckets.filter(b => b.count > 0)
      if (nonEmpty.length > 1) {
        const bars = nonEmpty.map(b => `${b.label}&nbsp;(${b.count})`).join(' · ')
        sections.push(`
          <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
            Distribution des ajustements nets&nbsp;(%)&nbsp;: <span style="font-size:9pt;">${bars}</span>
          </p>
        `)
      }
    }
  }

  // B181: gross adjustment OEAQ check (≤25%)
  if (adjustments.length > 0) {
    const oeaqGross = computeGrossAdjustmentOEAQCheck(adjustments)
    if (oeaqGross) {
      const color = oeaqGross.compliant ? '#1f7a5c' : '#b91c1c'
      const note = oeaqGross.compliant
        ? 'Tous les comparables respectent le plafond brut de 25 %.'
        : `${oeaqGross.violationCount} comparable(s) dépassent le plafond brut de 25 %.`
      sections.push(`
        <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
          Plafond brut OEAQ (25 %)&nbsp;: <strong style="color:${color};">${oeaqGross.compliant ? '✓ Conforme' : '⚠ Non conforme'}</strong>
          <span style="font-size:9pt;color:#8a8780;"> — ${note}</span>
        </p>
      `)
    }
  }

  // B183: adjustment magnitude ranking
  if (adjustments.length > 0) {
    const ranking = computeAdjustmentMagnitudeRanking(adjustments)
    if (ranking) {
      const topTwo = ranking.entries.slice(0, 2).map(e => `${e.type} (${fmtMoney(e.totalAbsolute)})`).join(', ')
      sections.push(`
        <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
          Types d'ajustement dominants&nbsp;: <strong>${topTwo}</strong>
          <span style="font-size:9pt;color:#8a8780;"> — par magnitude absolue cumulée</span>
        </p>
      `)
    }
  }

  // B184: reconciliation weight distribution
  if (adjustments.length > 0) {
    const weights = computeReconciliationWeightDistribution(adjustments)
    if (weights) {
      const topComp = weights.entries.reduce((a, b) => a.weightPct > b.weightPct ? a : b)
      const concentration = weights.herfindahl > 0.5 ? 'concentrée' : weights.herfindahl > 0.33 ? 'modérée' : 'équilibrée'
      sections.push(`
        <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
          Pondération de la réconciliation&nbsp;: <strong>${topComp.comparableLabel}</strong> ${fmt(topComp.weightPct, 0)} %
          <span style="font-size:9pt;color:#8a8780;"> — concentration ${concentration} (H = ${fmt(weights.herfindahl, 2)})</span>
        </p>
      `)
    }
  }

  // B187: net adj per comp summary (sorted by magnitude)
  if (adjustments.length > 0) {
    const netSummary = computeAdjustmentNetPerCompSummary(adjustments)
    if (netSummary) {
      const top = netSummary.entries[0]
      const color = top.direction === 'positive' ? '#1f7a5c' : top.direction === 'negative' ? '#b91c1c' : '#6a6763'
      const sign = top.netAdj >= 0 ? '+' : ''
      sections.push(`
        <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
          Ajustement net max&nbsp;: <strong style="color:${color};">${top.comparableLabel} ${sign}${fmtMoney(top.netAdj)}</strong>
          <span style="font-size:9pt;color:#8a8780;"> (${sign}${fmt(top.netPct, 1)} %)</span>
        </p>
      `)
    }
  }

  // B189: adjustment efficiency ratio
  if (adjustments.length > 0) {
    const efficiency = computeAdjustmentEfficiencyRatio(adjustments)
    if (efficiency) {
      const pct = Math.round(efficiency.mean * 100)
      const label = efficiency.mean >= 0.7 ? 'forte' : efficiency.mean >= 0.4 ? 'modérée' : 'faible'
      const color = efficiency.mean >= 0.7 ? '#1f7a5c' : efficiency.mean >= 0.4 ? '#b45309' : '#b91c1c'
      sections.push(`
        <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
          Efficacité des ajustements&nbsp;: <strong style="color:${color};">${pct} % (${label})</strong>
          <span style="font-size:9pt;color:#8a8780;"> — ratio |net|/brut moy. sur le panel</span>
        </p>
      `)
    }
  }

  // B127: net adjustment distribution
  if (adjustments.length >= 2) {
    const netDist = computeNetAdjustmentDistribution(adjustments)
    if (netDist) {
      const meanColor = netDist.mean > 0 ? '#1f7a5c' : netDist.mean < 0 ? '#b91c1c' : '#6a6763'
      sections.push(`
        <p style="font-size:10pt;color:#6a6763;margin-top:6pt;">
          Distribution des ajustements nets&nbsp;:
          moy. <strong style="color:${meanColor};">${netDist.mean >= 0 ? '+' : ''}${fmtMoney(netDist.mean)}</strong>,
          écart-type ${fmtMoney(netDist.stdDev)},
          fourchette ${fmtMoney(netDist.min)} – ${fmtMoney(netDist.max)}
          <span style="font-size:9pt;color:#8a8780;">(CV ${fmt(netDist.cv, 1)} %)</span>
        </p>
      `)
    }
  }

  return sections.join('\n')
}
