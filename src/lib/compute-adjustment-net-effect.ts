import type { Adjustment } from '@/types'

export interface AdjustmentNetEffect {
  comparableId: string
  comparableLabel: string
  salePrice: number
  /** Sum of all adjustments in dollars */
  totalAdjustment: number
  /** totalAdjustment / salePrice × 100 */
  netPct: number
  /** 'positif' when totalAdjustment > 0, 'négatif' < 0, 'neutre' === 0 */
  direction: 'positif' | 'négatif' | 'neutre'
  /** Magnitude relative to sale price: 'fort' |netPct| ≥ 10%, 'modéré' ≥ 5%, 'faible' < 5% */
  magnitude: 'fort' | 'modéré' | 'faible'
}

/**
 * Computes the net effect of all adjustments for each comparable.
 * Returns [] when no adjustments provided.
 */
export function computeAdjustmentNetEffect(adjs: Adjustment[]): AdjustmentNetEffect[] {
  if (adjs.length === 0) return []
  return adjs.map(a => {
    const totalAdjustment = a.adjusted - a.salePrice
    const netPct = a.salePrice > 0 ? Math.round((totalAdjustment / a.salePrice) * 1000) / 10 : 0
    const absNetPct = Math.abs(netPct)
    const direction: AdjustmentNetEffect['direction'] =
      totalAdjustment > 0 ? 'positif' : totalAdjustment < 0 ? 'négatif' : 'neutre'
    const magnitude: AdjustmentNetEffect['magnitude'] =
      absNetPct >= 10 ? 'fort' : absNetPct >= 5 ? 'modéré' : 'faible'
    return {
      comparableId: a.comparable_id,
      comparableLabel: a.comparableLabel,
      salePrice: a.salePrice,
      totalAdjustment,
      netPct,
      direction,
      magnitude,
    }
  })
}
