import type { Adjustment } from '@/types'

export interface AdjustmentDirectionBalance {
  /** Comps where net adjustment is positive (adjusted > salePrice) */
  upCount: number
  /** Comps where net adjustment is negative (adjusted < salePrice) */
  downCount: number
  /** Comps with zero net adjustment */
  neutralCount: number
  upPct: number
  downPct: number
  /** 'upward' when >70% positive, 'downward' when >70% negative, else 'balanced' */
  direction: 'upward' | 'downward' | 'balanced'
  balanced: boolean
}

/**
 * Checks whether adjustments lean predominantly positive or negative.
 * A skew > 70% in one direction is a potential appraisal bias flag.
 *
 * Returns null when no adjustments provided.
 */
export function computeAdjustmentDirectionBalance(adjs: Adjustment[]): AdjustmentDirectionBalance | null {
  if (adjs.length === 0) return null

  let upCount = 0
  let downCount = 0
  let neutralCount = 0

  for (const a of adjs) {
    const net = a.adjusted - a.salePrice
    if (net > 0) upCount++
    else if (net < 0) downCount++
    else neutralCount++
  }

  const nonNeutral = upCount + downCount
  const upPct = nonNeutral > 0 ? Math.round((upCount / adjs.length) * 1000) / 10 : 0
  const downPct = nonNeutral > 0 ? Math.round((downCount / adjs.length) * 1000) / 10 : 0

  const direction: AdjustmentDirectionBalance['direction'] =
    upPct > 70 ? 'upward' : downPct > 70 ? 'downward' : 'balanced'

  return { upCount, downCount, neutralCount, upPct, downPct, direction, balanced: direction === 'balanced' }
}
