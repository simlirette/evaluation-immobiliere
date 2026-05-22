import type { Adjustment } from '@/types'

export interface GrossAdjustment {
  gross: number     // sum of absolute values of all adjustment fields
  grossPct: number  // gross / salePrice × 100 (always ≥ 0)
}

/**
 * Computes the gross adjustment (sum of |each adj field|) and its ratio to sale price.
 * Gross adjustment measures total adjustment magnitude regardless of sign cancellation.
 * OEAQ reliability concern threshold: grossPct > 40.
 * Returns zero percentages when salePrice is not positive to avoid division errors.
 */
export function computeGrossAdjustment(adj: Adjustment): GrossAdjustment {
  const gross =
    Math.abs(adj.surface_adj) +
    Math.abs(adj.year_adj) +
    Math.abs(adj.condition_adj) +
    Math.abs(adj.garage_adj)
  if (!Number.isFinite(adj.salePrice) || adj.salePrice <= 0) return { gross, grossPct: 0 }
  return { gross, grossPct: (gross / adj.salePrice) * 100 }
}
