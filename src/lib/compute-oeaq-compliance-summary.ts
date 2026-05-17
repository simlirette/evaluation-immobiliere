import type { OEAQCheck } from './build-oeaq-checklist'
import type { GrossAdjustmentCeilingReport } from './compute-gross-adjustment-ceiling'
import type { AdjustmentBracketAnalysis } from './compute-adjustment-bracket-analysis'
import type { AdjustmentSymmetryResult } from './compute-adjustment-symmetry'

export interface OEAQComplianceSummary {
  passCount: number
  failCount: number
  /** 0–100 rounded score */
  score: number
  /** 'conforme' ≥80, 'attention' ≥50, 'non conforme' <50 */
  grade: 'conforme' | 'attention' | 'non conforme'
}

/**
 * Aggregates OEAQ compliance signals from multiple sources into a single summary.
 * Treats each signal as one pass/fail check with equal weight.
 *
 * Returns null when no checklist items provided.
 */
export function computeOEAQComplianceSummary(
  checklist: OEAQCheck[],
  ceilingReport: GrossAdjustmentCeilingReport | null,
  bracketResult: AdjustmentBracketAnalysis | null,
  symmetryResult: AdjustmentSymmetryResult | null,
): OEAQComplianceSummary | null {
  if (checklist.length === 0) return null

  const checks: boolean[] = checklist.map(c => c.pass)

  if (ceilingReport != null) checks.push(ceilingReport.compliant)
  if (bracketResult != null) checks.push(bracketResult.isBracketed)
  if (symmetryResult != null) checks.push(symmetryResult.overallSymmetric)

  const passCount = checks.filter(Boolean).length
  const failCount = checks.length - passCount
  const score = Math.round((passCount / checks.length) * 100)
  const grade: OEAQComplianceSummary['grade'] =
    score >= 80 ? 'conforme' : score >= 50 ? 'attention' : 'non conforme'

  return { passCount, failCount, score, grade }
}
