import type { Comparable } from '@/types'

export interface PriceIndexationEntry {
  comparableId: string
  comparableLabel: string
  originalPrice: number
  indexedPrice: number
  monthsAdjusted: number
  adjustmentPct: number
}

/**
 * Reindexes each comparable's sale price to today using a linear monthly appreciation rate.
 * Linear (not compound) adjustment, consistent with the ≤24-month time-adjustment policy.
 *
 * Returns empty array when comparables array is empty.
 */
export function computePriceIndexation(
  comparables: Comparable[],
  monthlyRatePct: number,
): PriceIndexationEntry[] {
  if (comparables.length === 0) return []

  const today = new Date()

  return comparables.map(c => {
    const saleDate = new Date(c.sale_date)
    const monthsAdjusted = Math.max(
      0,
      (today.getFullYear() - saleDate.getFullYear()) * 12
        + (today.getMonth() - saleDate.getMonth()),
    )

    const adjustmentFactor = (monthlyRatePct * monthsAdjusted) / 100
    const indexedPrice = Math.round(c.sale_price * (1 + adjustmentFactor))
    const adjustmentPct = Math.round(adjustmentFactor * 1000) / 10

    return {
      comparableId: c.id,
      comparableLabel: c.address,
      originalPrice: c.sale_price,
      indexedPrice,
      monthsAdjusted,
      adjustmentPct,
    }
  })
}
