import type { Comparable, Adjustment, EnrichmentMarche } from '@/types'
import { computePriceIndexation } from './compute-price-indexation'
import { computeLotSizeAnalysis } from './compute-lot-size-analysis'
import { computeRenovationProfile } from './compute-renovation-profile'
import { computeComparableDateSpread } from './compute-comparable-date-spread'
import { computeGarageTypeDistribution } from './compute-garage-type-distribution'
import { computeBuildingAgeStats } from './compute-building-age-stats'
import { computeTimeAdjustedPriceRange } from './compute-time-adjusted-price-range'
import { computeComparablePriceQuartiles } from './compute-comparable-price-quartiles'
import { computePricePerM2Outliers } from './compute-price-per-m2-outliers'
import { computeComparableSimilarityScore } from './compute-comparable-similarity-score'
import { computeComparableStats } from './compute-comparable-stats'
import { checkComparableMinimum } from './check-comparable-minimum'
import { computeMarketPriceTrend } from './compute-market-price-trend'
import { computeComparableQualityScore } from './compute-comparable-quality-score'
import { computePricePerM2Stats } from './compute-price-per-m2-stats'
import { computeTimeAdjustmentRate } from './compute-time-adjustment-rate'
import { computeComparableRanking } from './compute-comparable-ranking'
import { computeDataQualityReport } from './compute-data-quality-report'
import { computePricePerM2Distribution } from './compute-price-per-m2-distribution'
import { computeSalesPressureIndex } from './compute-sales-pressure-index'
import { computeComparableSizeRange } from './compute-comparable-size-range'
import { computeComparableSelectionSummary } from './compute-comparable-selection-summary'
import { computePricePerM2Trend } from './compute-price-per-m2-trend'
import { computeComparablePriceSkew } from './compute-comparable-price-skew'
import { computePriceIndexationSummary } from './compute-price-indexation-summary'
import { computeSalePricePerTerrainM2 } from './compute-sale-price-per-terrain-m2'
import { computeComparableFieldCoverage } from './compute-comparable-field-coverage'
import { computeComparableRepresentativeness } from './compute-comparable-representativeness'
import { computeComparableAgeDiversityScore } from './compute-comparable-age-diversity-score'
import { computeReconciledValue } from './compute-reconciled-value'
import { computeSalePriceCV } from './compute-sale-price-cv'
import { computeComparableSaleVelocity } from './compute-comparable-sale-velocity'
import { computeComparableDateRecencyProfile } from './compute-comparable-date-recency-profile'
import { computeComparableHabitatProfile } from './compute-comparable-habitat-profile'
import { computeComparableStreetDiversity } from './compute-comparable-street-diversity'
import { computeComparableDataCompleteness } from './compute-comparable-data-completeness'

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
  subject?: { hab_m2?: number | null; year_built?: number | null },
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
    // B148: age diversity score
    const ageDiversity = computeComparableAgeDiversityScore(comparables)
    const ageDiversityRow = ageDiversity
      ? (() => {
          const color = ageDiversity.diversity === 'élevée' ? '#1f7a5c' : ageDiversity.diversity === 'faible' ? '#b45309' : '#6a6763'
          return `<tr><td style="color:#6a6763;">Diversité des millésimes</td><td style="font-weight:600;text-align:right;color:${color};">${ageDiversity.diversity} (${ageDiversity.decadeCount} décennie${ageDiversity.decadeCount > 1 ? 's' : ''}) <span style="font-weight:400;font-size:9pt;color:#8a8780;">${ageDiversity.minYear} – ${ageDiversity.maxYear}, étendue ${ageDiversity.range} ans</span></td></tr>`
        })()
      : ''
    // B142: $/terrain m²
    const terrainM2 = computeSalePricePerTerrainM2(comparables)
    const terrainM2Row = terrainM2
      ? `<tr><td style="color:#6a6763;">Prix médian au m² terrain</td><td style="font-weight:600;text-align:right;">${fmt(terrainM2.median, 0)} $/m² <span style="font-weight:400;font-size:9pt;color:#8a8780;">(${fmt(terrainM2.min, 0)} – ${fmt(terrainM2.max, 0)}${terrainM2.missingCount > 0 ? ` · ${terrainM2.missingCount} sans données` : ''})</span></td></tr>`
      : ''
    // B131: subject size range bracket
    const sizeRange = subject?.hab_m2 != null ? computeComparableSizeRange(comparables, subject.hab_m2) : null
    const sizeRangeRow = sizeRange
      ? (() => {
          const color = sizeRange.bracketed ? '#1f7a5c' : '#b45309'
          const bracketNote = sizeRange.bracketed
            ? `✓ encadré`
            : `⚠ hors fourchette (${fmt(sizeRange.subjectHabM2, 0)} m²)`
          return `<tr><td style="color:#6a6763;">Surface sujet vs comparables</td><td style="font-weight:600;text-align:right;color:${color};">${bracketNote} <span style="font-weight:400;font-size:9pt;color:#8a8780;">(comp. : ${fmt(sizeRange.min, 0)} – ${fmt(sizeRange.max, 0)} m²)</span></td></tr>`
        })()
      : ''
    // B136: price skew
    const priceSkew = computeComparablePriceSkew(comparables)
    const priceSkewRow = priceSkew && priceSkew.interpretation !== 'symétrique'
      ? (() => {
          const color = priceSkew.skew > 0.5 ? '#b45309' : '#0369a1'
          return `<tr><td style="color:#6a6763;">Asymétrie des prix</td><td style="font-weight:600;text-align:right;color:${color};">${priceSkew.interpretation} <span style="font-weight:400;font-size:9pt;color:#8a8780;">(skew ${priceSkew.skew > 0 ? '+' : ''}${fmt(priceSkew.skew, 2)}, moy. ${fmtMoney(priceSkew.mean)} vs méd. ${fmtMoney(priceSkew.median)})</span></td></tr>`
        })()
      : ''
    // B164: habitat profile
    const habitatProfile = computeComparableHabitatProfile(comparables)
    const habitatRow = habitatProfile
      ? `<tr><td style="color:#6a6763;">Surface hab. médiane</td><td style="font-weight:600;text-align:right;">${fmt(habitatProfile.median, 0)} m² <span style="font-weight:400;font-size:9pt;color:#8a8780;">(${fmt(habitatProfile.min, 0)} – ${fmt(habitatProfile.max, 0)}${habitatProfile.missingCount > 0 ? ` · ${habitatProfile.missingCount} sans données` : ''} · CV ${fmt(habitatProfile.cv, 1)} %)</span></td></tr>`
      : ''
    // B151: sale price CV
    const salePriceCV = computeSalePriceCV(comparables)
    const salePriceCVRow = salePriceCV
      ? (() => {
          const color = salePriceCV.cohesion === 'homogène' ? '#1f7a5c' : salePriceCV.cohesion === 'hétérogène' ? '#b91c1c' : '#b45309'
          return `<tr><td style="color:#6a6763;">Homogénéité des prix (CV)</td><td style="font-weight:600;text-align:right;color:${color};">${salePriceCV.cohesion} <span style="font-weight:400;font-size:9pt;color:#8a8780;">(CV ${fmt(salePriceCV.cv, 1)} % · σ ${fmtMoney(salePriceCV.stdDev)})</span></td></tr>`
        })()
      : ''
    // B135: $/m² trend
    const ppm2Trend = computePricePerM2Trend(comparables)
    const ppm2TrendRow = ppm2Trend
      ? (() => {
          const color = ppm2Trend.direction === 'rising' ? '#1f7a5c' : ppm2Trend.direction === 'falling' ? '#b91c1c' : '#6a6763'
          const sigNote = ppm2Trend.significant ? ` <span style="font-size:9pt;color:#8a8780;">(R²=${fmt(ppm2Trend.r2, 2)})</span>` : ` <span style="font-size:9pt;color:#8a8780;">(non significatif, R²=${fmt(ppm2Trend.r2, 2)})</span>`
          const sign = ppm2Trend.slopePerMonth > 0 ? '+' : ''
          return `<tr><td style="color:#6a6763;">Tendance $/m² (régression)</td><td style="font-weight:600;text-align:right;color:${color};">${ppm2Trend.direction} ${sign}${fmt(ppm2Trend.slopePerMonth, 0)} $/m²/mois${sigNote}</td></tr>`
        })()
      : ''
    // B122: building age
    const ageStats = computeBuildingAgeStats(comparables)
    const ageStatsRow = ageStats
      ? `<tr><td style="color:#6a6763;">Âge médian à la vente</td><td style="font-weight:600;text-align:right;">${ageStats.median} ans <span style="font-weight:400;font-size:9pt;color:#8a8780;">(${ageStats.min} – ${ageStats.max}${ageStats.missingCount > 0 ? ` · ${ageStats.missingCount} sans données` : ''})</span></td></tr>`
      : ''
    // B125: price quartiles
    const quartiles = computeComparablePriceQuartiles(comparables)
    const quartilesRow = quartiles
      ? (() => {
          const outlierNote = quartiles.outlierIds.length > 0
            ? ` · <span style="color:#b45309;">${quartiles.outlierIds.length} hors-norme IQR</span>`
            : ''
          return `<tr><td style="color:#6a6763;">Quartiles de prix</td><td style="font-weight:600;text-align:right;font-size:9pt;">${fmtMoney(quartiles.q1)} / ${fmtMoney(quartiles.q2)} / ${fmtMoney(quartiles.q3)} <span style="font-weight:400;color:#8a8780;">IQR ${fmtMoney(quartiles.iqr)}${outlierNote}</span></td></tr>`
        })()
      : ''
    // B129: $/m² outliers
    const m2Outliers = computePricePerM2Outliers(comparables)
    const m2OutliersRow = m2Outliers
      ? (() => {
          const outlierNote = m2Outliers.outlierIds.length > 0
            ? ` · <span style="color:#b45309;">${m2Outliers.outlierIds.length} hors-norme $/m²</span>`
            : ''
          return `<tr><td style="color:#6a6763;">Quartiles $/m² (IQR)</td><td style="font-weight:600;text-align:right;font-size:9pt;">${fmt(m2Outliers.q1, 0)} / ${fmt(m2Outliers.median, 0)} / ${fmt(m2Outliers.q3, 0)} $/m² <span style="font-weight:400;color:#8a8780;">IQR ${fmt(m2Outliers.iqr, 0)}${outlierNote}</span></td></tr>`
        })()
      : ''
    // B116: lot size
    const lotSize = computeLotSizeAnalysis(comparables)
    const lotSizeRow = lotSize
      ? `<tr><td style="color:#6a6763;">Terrain médian (m²)</td><td style="font-weight:600;text-align:right;">${fmt(lotSize.median, 0)} m² <span style="font-weight:400;font-size:9pt;color:#8a8780;">(${fmt(lotSize.min, 0)} – ${fmt(lotSize.max, 0)}${lotSize.missingCount > 0 ? ` · ${lotSize.missingCount} sans données` : ''})</span></td></tr>`
      : ''
    // B119: date spread
    const dateSpread = computeComparableDateSpread(comparables)
    const dateSpreadRow = dateSpread
      ? (() => {
          const color = dateSpread.recencyScore === 'récent' ? '#1f7a5c' : dateSpread.recencyScore === 'daté' ? '#b91c1c' : '#b45309'
          return `<tr><td style="color:#6a6763;">Étendue temporelle</td><td style="font-weight:600;text-align:right;">${dateSpread.spanMonths} mois <span style="font-weight:400;font-size:9pt;color:${color};">— ${dateSpread.recencyScore} (${dateSpread.staleCount} daté${dateSpread.staleCount !== 1 ? 's' : ''}, ${dateSpread.recent12mCount} récent${dateSpread.recent12mCount !== 1 ? 's' : ''})</span></td></tr>`
        })()
      : ''
    sections.push(`
      <h2>Synthèse des comparables</h2>
      <table><tbody>${statRows}${trendRow}${m2Row}${m2DistRow}${priceSkewRow}${salePriceCVRow}${timeRateRow}${ppm2TrendRow}${terrainM2Row}${habitatRow}${lotSizeRow}${sizeRangeRow}${dateSpreadRow}${ageStatsRow}${ageDiversityRow}${quartilesRow}${m2OutliersRow}</tbody></table>
      ${minCheck.warning ? `<p style="color:#b45309;font-size:10pt;">⚠ ${minCheck.warning}</p>` : ''}
    `)

    // B146: subject value representativeness vs raw comp prices
    if (adjustments && adjustments.length >= 2) {
      const reconciledResult = computeReconciledValue(adjustments)
      if (reconciledResult) {
        const rep = computeComparableRepresentativeness(comparables, reconciledResult.value)
        if (rep && !rep.withinRange) {
          const side = rep.subjectValue < rep.compMin ? 'en-dessous' : 'au-dessus'
          sections.push(`
            <p style="font-size:10pt;color:#b45309;margin-top:4pt;">
              ⚠ Valeur réconciliée (${fmtMoney(rep.subjectValue)}) ${side} des prix bruts des comparables (${fmtMoney(rep.compMin)} – ${fmtMoney(rep.compMax)}, écart ${fmt(rep.deviationPct, 1)} %) — représentativité limitée.
            </p>
          `)
        }
      }
    }

    // Indexed prices sub-table when time rate is available
    if (timeRate && comparables.length > 0) {
      const indexed = computePriceIndexation(comparables, timeRate.monthlyRatePct)
      if (indexed.length > 0) {
        const indexedRows = indexed.map(e => {
          const color = e.adjustmentPct > 0 ? '#1f7a5c' : e.adjustmentPct < 0 ? '#b91c1c' : '#8a8780'
          const sign = e.adjustmentPct > 0 ? '+' : ''
          return `<tr>
            <td style="color:#6a6763;">${e.comparableLabel}</td>
            <td style="text-align:right;">${fmtMoney(e.originalPrice)}</td>
            <td style="text-align:right;color:${color};font-weight:600;">${fmtMoney(e.indexedPrice)}</td>
            <td style="text-align:right;font-size:9pt;color:${color};">${sign}${fmt(e.adjustmentPct, 1)} % (${e.monthsAdjusted} mois)</td>
          </tr>`
        }).join('')
        sections.push(`
          <h2>Prix réindexés à aujourd'hui</h2>
          <p style="font-size:9pt;color:#8a8780;margin:0 0 4pt;">Taux mensuel implicite&nbsp;: ${timeRate.monthlyRatePct >= 0 ? '+' : ''}${fmt(timeRate.monthlyRatePct, 2)} %/mois (linéaire) — confiance ${timeRate.confidence}</p>
          <table>
            <thead>
              <tr>
                <th>Comparable</th>
                <th style="text-align:right;">Prix original</th>
                <th style="text-align:right;">Prix réindexé</th>
                <th style="text-align:right;">Ajustement</th>
              </tr>
            </thead>
            <tbody>${indexedRows}</tbody>
          </table>
        `)
        // B138: indexation summary
        const idxSummary = computePriceIndexationSummary(indexed)
        if (idxSummary && Math.abs(idxSummary.avgAdjPct) >= 0.5) {
          const color = idxSummary.totalAdded > 0 ? '#1f7a5c' : '#b91c1c'
          const sign = idxSummary.totalAdded > 0 ? '+' : ''
          sections.push(`
            <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
              Réindexation totale&nbsp;:
              <strong style="color:${color};">${sign}${fmtMoney(idxSummary.totalAdded)}</strong>
              <span style="font-size:9pt;color:#8a8780;"> — moy. ${idxSummary.avgAdjPct > 0 ? '+' : ''}${fmt(idxSummary.avgAdjPct, 1)} %/comp. · plus ajusté&nbsp;: ${idxSummary.mostAdjustedId} (${idxSummary.mostAdjustedPct} %)</span>
            </p>
          `)
        }
        // B123: time-adjusted price range (compare to raw range)
        const rawPrices = comparables.map(c => c.sale_price).sort((a, b) => a - b)
        const rawRange = rawPrices[rawPrices.length - 1] - rawPrices[0]
        const adjRange = computeTimeAdjustedPriceRange(comparables, timeRate.monthlyRatePct)
        if (adjRange && rawRange > 0) {
          const pctChange = Math.round(((adjRange.range - rawRange) / rawRange) * 1000) / 10
          const color = pctChange < 0 ? '#1f7a5c' : pctChange > 0 ? '#b45309' : '#8a8780'
          sections.push(`
            <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
              Fourchette après réindexation temporelle&nbsp;:
              <strong>${fmtMoney(adjRange.min)} – ${fmtMoney(adjRange.max)}</strong>
              <span style="font-size:9pt;color:${color};"> (${pctChange > 0 ? '+' : ''}${fmt(pctChange, 1)} % vs fourchette brute)</span>
            </p>
          `)
        }
      }
    }
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
    // B117: renovation profile note
    const renovationProfile = computeRenovationProfile(comparables)
    if (renovationProfile && renovationProfile.renovatedCount > 0) {
      const recentNote = renovationProfile.recentlyRenovatedIds.length > 0
        ? ` · ${renovationProfile.recentlyRenovatedIds.length} rénové${renovationProfile.recentlyRenovatedIds.length > 1 ? 's' : ''} récemment (≤ 10 ans)`
        : ''
      const ageNote = renovationProfile.avgRenovationAge != null
        ? ` · âge moyen rénovation : ${renovationProfile.avgRenovationAge} ans`
        : ''
      sections.push(`
        <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
          Rénovations&nbsp;: <strong>${renovationProfile.renovatedCount}/${comparables.length}</strong>
          (${fmt(renovationProfile.renovatedPct, 0)} %)${ageNote}${recentNote}
        </p>
      `)
    }
    // B134: comparable selection summary (quality + similarity aggregate)
    if (adjustments) {
      const qualityScoresForSummary = computeComparableQualityScore(comparables, adjustments)
      const simScoresForSummary = subject ? computeComparableSimilarityScore(comparables, subject) : null
      const selSummary = computeComparableSelectionSummary(qualityScoresForSummary, simScoresForSummary)
      if (selSummary) {
        const color = selSummary.recommendation === 'forte' ? '#1f7a5c' : selSummary.recommendation === 'faible' ? '#b91c1c' : '#b45309'
        const simNote = selSummary.avgSimilarityScore != null
          ? ` · similarité moy. ${selSummary.avgSimilarityScore}/100`
          : ''
        const lowNote = selSummary.lowQualityCount > 0
          ? ` · ${selSummary.lowQualityCount} comp. faible qualité`
          : ''
        sections.push(`
          <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
            Sélection des comparables&nbsp;:
            <strong style="color:${color};">${selSummary.recommendation}</strong>
            <span style="font-size:9pt;color:#8a8780;"> — qualité moy. ${fmt(selSummary.avgQualityScore, 1)}/10${simNote}${lowNote}</span>
          </p>
        `)
      }
    }
    // B168: street diversity
    if (comparables.length > 0) {
      const streetDiv = computeComparableStreetDiversity(comparables)
      if (streetDiv && streetDiv.concentrated) {
        sections.push(`
          <p style="font-size:10pt;color:#b45309;margin-top:4pt;">
            ⚠ Concentration géographique&nbsp;: tous les comparables sur la même rue
            <span style="font-size:9pt;color:#8a8780;"> (${streetDiv.streets[0]})</span>
          </p>
        `)
      }
    }
    // B157: date recency profile
    if (comparables.length > 0) {
      const recency = computeComparableDateRecencyProfile(comparables)
      if (recency && recency.staleCount > 0) {
        const color = recency.stalePct >= 50 ? '#b91c1c' : '#b45309'
        sections.push(`
          <p style="font-size:10pt;color:${color};margin-top:4pt;">
            ⚠ ${recency.staleCount} comparable${recency.staleCount > 1 ? 's' : ''} daté${recency.staleCount > 1 ? 's' : ''} (&gt; 24 mois) — ${recency.stalePct} % du panel
            <span style="font-size:9pt;color:#8a8780;"> · ${recency.recentCount} récent${recency.recentCount !== 1 ? 's' : ''} · ${recency.moderateCount} modéré${recency.moderateCount !== 1 ? 's' : ''}</span>
          </p>
        `)
      }
    }
    // B154: comparable sale velocity
    if (comparables.length >= 2) {
      const velocity = computeComparableSaleVelocity(comparables)
      if (velocity) {
        const color = velocity.signal === 'actif' ? '#1f7a5c' : velocity.signal === 'lent' ? '#b45309' : '#6a6763'
        sections.push(`
          <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
            Vélocité des ventes&nbsp;:
            <strong style="color:${color};">${velocity.signal}</strong>
            <span style="font-size:9pt;color:#8a8780;"> — ${fmt(velocity.salesPerMonth, 2)} vente${velocity.salesPerMonth !== 1 ? 's' : ''}/mois · ${fmt(velocity.annualizedRate, 1)}/an · sur ${fmt(velocity.spanMonths, 0)} mois</span>
          </p>
        `)
      }
    }
    // B121: garage type distribution
    const garageDist = computeGarageTypeDistribution(comparables)
    if (garageDist && garageDist.groups.length > 0) {
      const conflictNote = garageDist.hasGarageConflict
        ? ` <span style="color:#b45309;">· types mixtes — cohérence des ajustements garage à vérifier</span>`
        : ''
      const groupStr = garageDist.groups.map(g => `${g.type} (${g.count})`).join(', ')
      sections.push(`
        <p style="font-size:10pt;color:#6a6763;margin-top:4pt;">
          Types de garage&nbsp;: <strong>${groupStr}</strong>${conflictNote}
        </p>
      `)
    }
    // B130: similarity scores when subject profile available
    if (subject) {
      const simScores = computeComparableSimilarityScore(comparables, subject)
      if (simScores && simScores.length > 0) {
        const simRows = [...simScores]
          .sort((a, b) => b.score - a.score)
          .map(e => {
            const color = e.score >= 70 ? '#1f7a5c' : e.score >= 40 ? '#b45309' : '#b91c1c'
            const sizeNote = e.sizeDiffPct != null ? `${fmt(e.sizeDiffPct, 0)} % surf.` : ''
            const ageNote = e.ageDiff != null ? `${e.ageDiff} an(s)` : ''
            const notes = [sizeNote, ageNote].filter(Boolean).join(', ')
            return `<tr>
              <td>${e.comparableLabel}</td>
              <td style="text-align:right;font-weight:600;color:${color};">${e.score}/100</td>
              <td style="text-align:right;font-size:9pt;color:#8a8780;">${notes}</td>
            </tr>`
          }).join('')
        sections.push(`
          <h2>Similarité avec le sujet</h2>
          <table>
            <thead><tr><th>Comparable</th><th style="text-align:right;">Score</th><th style="text-align:right;">Écarts</th></tr></thead>
            <tbody>${simRows}</tbody>
          </table>
        `)
      }
    }
  } else {
    sections.push('<p>Aucun comparable chargé.</p>')
  }

  // B170: per-comp data completeness
  if (comparables.length > 0) {
    const completeness = computeComparableDataCompleteness(comparables)
    if (completeness && completeness.sparseCount > 0) {
      const sparseLabels = completeness.entries
        .filter(e => e.score < 3)
        .map(e => `${e.comparableLabel} (${e.score}/5)`)
        .join(', ')
      sections.push(`
        <p style="font-size:10pt;color:#b45309;margin-top:4pt;">
          ⚠ Données insuffisantes (${completeness.sparseCount} comp.&nbsp;&lt; 3/5 champs)&nbsp;: <strong>${sparseLabels}</strong>
          <span style="font-size:9pt;color:#8a8780;"> — score moy. ${fmt(completeness.avgScore, 1)}/5 · ${completeness.fullCount} complet${completeness.fullCount !== 1 ? 's' : ''}</span>
        </p>
      `)
    }
  }

  // B143: field coverage summary
  if (comparables.length > 0) {
    const fieldCov = computeComparableFieldCoverage(comparables)
    if (fieldCov && fieldCov.sparseFieldCount > 0) {
      const sparseFields = fieldCov.fields
        .filter(f => f.coveragePct < 50)
        .map(f => `${f.label} (${f.coveragePct} %)`)
        .join(', ')
      sections.push(`
        <p style="font-size:10pt;color:#b45309;margin-top:4pt;">
          ⚠ Données manquantes&nbsp;: <strong>${sparseFields}</strong>
          <span style="font-size:9pt;color:#8a8780;"> — couverture globale ${fieldCov.overallScore} %</span>
        </p>
      `)
    }
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

  if (chips.length > 0 || marche != null) {
    const pressureIndex = marche ? computeSalesPressureIndex(marche) : null
    const pressureRow = pressureIndex
      ? `<tr><td style="color:#6a6763;">Pression du marché</td><td style="font-weight:600;text-align:right;color:${pressureIndex.regime === 'vendeur' ? '#b45309' : pressureIndex.regime === 'acheteur' ? '#0369a1' : '#1f7a5c'};">${pressureIndex.regime} (indice ${pressureIndex.index}/100)</td></tr>`
      : ''
    const rows = chips.map(([label, val]) => `
      <tr>
        <td style="color:#6a6763;">${label}</td>
        <td style="font-weight:600;text-align:right;">${val}</td>
      </tr>
    `).join('')
    if (chips.length > 0 || pressureRow) {
      sections.push(`
        <h2>Contexte de marché</h2>
        <table>
          <tbody>${pressureRow}${rows}</tbody>
        </table>
      `)
    }
  }

  return sections.join('\n')
}
