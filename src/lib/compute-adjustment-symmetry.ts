import type { Adjustment } from '@/types'

export interface AdjustmentSymmetryResult {
  /** Per adjustment type: mean, stdDev, coefficientOfVariation of the raw adjustment amounts */
  surface: { mean: number; stdDev: number; cv: number; symmetric: boolean }
  year: { mean: number; stdDev: number; cv: number; symmetric: boolean }
  condition: { mean: number; stdDev: number; cv: number; symmetric: boolean }
  garage: { mean: number; stdDev: number; cv: number; symmetric: boolean }
  /** Number of types with CV > 50% (high variation = asymmetric methodology) */
  asymmetricCount: number
  /** True when all active types have CV ≤ 50% */
  overallSymmetric: boolean
}

function stats(values: number[]): { mean: number; stdDev: number; cv: number; symmetric: boolean } {
  const active = values.filter(v => v !== 0)
  if (active.length < 2) return { mean: 0, stdDev: 0, cv: 0, symmetric: true }
  const mean = active.reduce((s, v) => s + v, 0) / active.length
  const variance = active.reduce((s, v) => s + (v - mean) ** 2, 0) / active.length
  const stdDev = Math.round(Math.sqrt(variance))
  const cv = mean !== 0 ? Math.round(Math.abs(stdDev / mean) * 1000) / 10 : 0
  return { mean: Math.round(mean), stdDev, cv, symmetric: cv <= 50 }
}

/**
 * Measures the consistency (symmetry) of each adjustment type across comparables.
 * High CV (> 50%) for a given type suggests the adjustment amounts are not being
 * applied consistently, which is a methodological red flag.
 *
 * Returns null when fewer than 3 adjustments (need enough variation to be meaningful).
 */
export function computeAdjustmentSymmetry(adjs: Adjustment[]): AdjustmentSymmetryResult | null {
  if (adjs.length < 3) return null

  const surface = stats(adjs.map(a => a.surface_adj))
  const year = stats(adjs.map(a => a.year_adj))
  const condition = stats(adjs.map(a => a.condition_adj))
  const garage = stats(adjs.map(a => a.garage_adj))

  const types = [surface, year, condition, garage]
  const asymmetricCount = types.filter(t => !t.symmetric && t.mean !== 0).length
  const overallSymmetric = asymmetricCount === 0

  return { surface, year, condition, garage, asymmetricCount, overallSymmetric }
}
