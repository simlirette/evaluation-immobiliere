import type { Adjustment } from '@/types'
import { computeGrossAdjustment } from './compute-gross-adjustment'

export interface ReconciledValue {
  value: number
  /** weight per comparable id - higher = more reliable (lower gross adj) */
  weights: Record<string, number>
  /** 'forte' when max weight >= 2x min; 'moderee' otherwise */
  confidence: 'forte' | 'modérée'
}

export function isUsableAdjustment(adj: Adjustment): boolean {
  return Number.isFinite(adj.salePrice)
    && adj.salePrice > 0
    && Number.isFinite(adj.adjusted)
    && adj.adjusted > 0
}

/**
 * Weighted reconciliation: weight = 1 / (grossPct + 1).
 * Comparables with smaller gross adjustments are considered more reliable.
 * Returns null when no adjustment row has a positive sale and adjusted price.
 */
export function computeReconciledValue(adjs: Adjustment[]): ReconciledValue | null {
  const usableAdjs = adjs.filter(isUsableAdjustment)
  if (usableAdjs.length === 0) return null

  const rawWeights = usableAdjs.map(a => {
    const { grossPct } = computeGrossAdjustment(a)
    return 1 / (grossPct + 1)
  })

  const totalWeight = rawWeights.reduce((s, w) => s + w, 0)
  if (totalWeight <= 0) return null

  const value = Math.round(
    usableAdjs.reduce((sum, a, i) => sum + a.adjusted * (rawWeights[i] / totalWeight), 0),
  )

  const weights: Record<string, number> = {}
  usableAdjs.forEach((a, i) => {
    weights[a.id] = Math.round((rawWeights[i] / totalWeight) * 1000) / 10
  })

  const max = Math.max(...rawWeights)
  const min = Math.min(...rawWeights)
  const confidence: ReconciledValue['confidence'] = max >= 2 * min ? 'forte' : 'modérée'

  return { value, weights, confidence }
}
