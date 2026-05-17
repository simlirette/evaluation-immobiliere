import type { Adjustment } from '@/types'
import { computeGrossAdjustment } from './compute-gross-adjustment'

export interface ReconciledValue {
  value: number
  /** weight per comparable id — higher = more reliable (lower gross adj) */
  weights: Record<string, number>
  /** 'forte' when max weight ≥ 2× min; 'modérée' otherwise */
  confidence: 'forte' | 'modérée'
}

/**
 * Weighted reconciliation: weight = 1 / (grossPct + 1).
 * Comparables with smaller gross adjustments are considered more reliable.
 * Returns null when adjustments is empty.
 */
export function computeReconciledValue(adjs: Adjustment[]): ReconciledValue | null {
  if (adjs.length === 0) return null

  const rawWeights = adjs.map(a => {
    const { grossPct } = computeGrossAdjustment(a)
    return 1 / (grossPct + 1)
  })

  const totalWeight = rawWeights.reduce((s, w) => s + w, 0)

  const value = Math.round(
    adjs.reduce((sum, a, i) => sum + a.adjusted * (rawWeights[i] / totalWeight), 0),
  )

  const weights: Record<string, number> = {}
  adjs.forEach((a, i) => {
    weights[a.id] = Math.round((rawWeights[i] / totalWeight) * 1000) / 10
  })

  const max = Math.max(...rawWeights)
  const min = Math.min(...rawWeights)
  const confidence: ReconciledValue['confidence'] = max >= 2 * min ? 'forte' : 'modérée'

  return { value, weights, confidence }
}
