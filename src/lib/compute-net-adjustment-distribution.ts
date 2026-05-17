import type { Adjustment } from '@/types'

export interface NetAdjustmentDistribution {
  /** Mean of (adjusted − salePrice) */
  mean: number
  stdDev: number
  /** CV of absolute net adjustments */
  cv: number
  min: number
  max: number
  /** Range: max − min */
  range: number
}

/**
 * Computes distribution statistics on the net adjustment amount (adjusted − salePrice)
 * across the comparable set. Complements direction balance with magnitude context.
 *
 * Returns null when fewer than 2 adjustments.
 */
export function computeNetAdjustmentDistribution(adjs: Adjustment[]): NetAdjustmentDistribution | null {
  if (adjs.length < 2) return null

  const nets = adjs.map(a => a.adjusted - a.salePrice)
  const mean = Math.round(nets.reduce((s, v) => s + v, 0) / nets.length)
  const variance = nets.reduce((s, v) => s + (v - mean) ** 2, 0) / nets.length
  const stdDev = Math.round(Math.sqrt(variance))
  const absNets = nets.map(Math.abs)
  const absMean = absNets.reduce((s, v) => s + v, 0) / absNets.length
  const cv = absMean > 0 ? Math.round(stdDev / absMean * 1000) / 10 : 0
  const sorted = [...nets].sort((a, b) => a - b)
  const min = sorted[0]
  const max = sorted[sorted.length - 1]

  return { mean, stdDev, cv, min, max, range: max - min }
}
