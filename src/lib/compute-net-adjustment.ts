import type { Adjustment } from '@/types'

export interface NetAdjustment {
  net: number       // algebraic sum of all adjustment fields
  netPct: number    // net / salePrice × 100 (can be negative)
  absPct: number    // |net| / salePrice × 100 (for threshold checks)
}

/**
 * Computes the net adjustment (sum of all adj fields) and its ratio to sale price.
 * Returns zero values when salePrice is 0 to avoid division errors.
 */
export function computeNetAdjustment(adj: Adjustment): NetAdjustment {
  const net = adj.surface_adj + adj.year_adj + adj.condition_adj + adj.garage_adj
  if (adj.salePrice === 0) return { net, netPct: 0, absPct: 0 }
  const netPct = (net / adj.salePrice) * 100
  return { net, netPct, absPct: Math.abs(netPct) }
}
