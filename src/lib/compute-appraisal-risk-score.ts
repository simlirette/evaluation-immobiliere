import type { Comparable, Adjustment } from '@/types'
import { buildOEAQChecklist } from './build-oeaq-checklist'
import { computeAdjustmentConsistency } from './compute-adjustment-consistency'
import { computeSensitivityAnalysis } from './compute-sensitivity-analysis'
import { computeDataQualityReport } from './compute-data-quality-report'
import { detectOutlierComparables } from './detect-outlier-comparables'

export interface AppraisalRiskScore {
  /** 0 = no risk, 100 = maximum risk */
  score: number
  /** 'faible' score < 30, 'modéré' 30–59, 'élevé' ≥ 60 */
  riskLevel: 'faible' | 'modéré' | 'élevé'
  /** Human-readable factors driving the risk score */
  factors: string[]
}

/**
 * Computes a composite appraisal risk score from 4 signals:
 * 1. OEAQ non-compliance (25 pts max): each failing rule = 8 pts
 * 2. Data quality (25 pts max): faible=25, acceptable=12, bon=0
 * 3. Adjustment consistency (25 pts max): each inconsistent type = 10 pts
 * 4. Sensitivity (25 pts max): each influential comp = 8 pts
 *
 * Returns null when no adjustments provided.
 */
export function computeAppraisalRiskScore(
  adjs: Adjustment[],
  comps: Comparable[],
): AppraisalRiskScore | null {
  if (adjs.length === 0) return null

  let score = 0
  const factors: string[] = []

  // 1. OEAQ compliance
  const oeaqChecks = buildOEAQChecklist(comps, adjs)
  const failCount = oeaqChecks.filter(c => !c.pass).length
  if (failCount > 0) {
    const pts = Math.min(25, failCount * 8)
    score += pts
    factors.push(`${failCount} règle${failCount > 1 ? 's' : ''} OEAQ non conforme${failCount > 1 ? 's' : ''}`)
  }

  // 2. Data quality
  const dqr = comps.length > 0 ? computeDataQualityReport(comps, adjs) : null
  if (dqr) {
    if (dqr.grade === 'faible') {
      score += 25
      factors.push('qualité des données faible')
    } else if (dqr.grade === 'acceptable') {
      score += 12
      factors.push('qualité des données acceptable')
    }
  }

  // 3. Adjustment consistency
  if (adjs.length >= 2) {
    const consistency = computeAdjustmentConsistency(adjs)
    const inconsistentCount = consistency.filter(c => !c.consistent).length
    if (inconsistentCount > 0) {
      const pts = Math.min(25, inconsistentCount * 10)
      score += pts
      factors.push(`ajustements incohérents sur ${inconsistentCount} type${inconsistentCount > 1 ? 's' : ''}`)
    }
  }

  // 4. Sensitivity (influential comparables)
  if (adjs.length >= 3) {
    const sensitivity = computeSensitivityAnalysis(adjs)
    if (sensitivity) {
      const influentialCount = sensitivity.entries.filter(e => e.influential).length
      if (influentialCount > 0) {
        const pts = Math.min(25, influentialCount * 8)
        score += pts
        factors.push(`${influentialCount} comparable${influentialCount > 1 ? 's' : ''} très influent${influentialCount > 1 ? 's' : ''}`)
      }
    }
  }

  // Outliers as a minor additive factor (not a primary signal)
  const outliers = detectOutlierComparables(adjs).filter(o => o.isOutlier)
  if (outliers.length > 0) {
    const pts = Math.min(10, outliers.length * 4)
    score = Math.min(100, score + pts)
    factors.push(`${outliers.length} valeur${outliers.length > 1 ? 's' : ''} indiquée${outliers.length > 1 ? 's' : ''} atypique${outliers.length > 1 ? 's' : ''}`)
  }

  score = Math.min(100, score)
  const riskLevel: AppraisalRiskScore['riskLevel'] =
    score < 30 ? 'faible' : score < 60 ? 'modéré' : 'élevé'

  return { score, riskLevel, factors }
}
