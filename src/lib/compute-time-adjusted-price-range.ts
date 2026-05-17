import type { Comparable } from '@/types'
import { computePriceIndexation } from './compute-price-indexation'

export interface TimeAdjustedPriceRange {
  min: number
  max: number
  median: number
  /** max − min */
  range: number
  count: number
}

/**
 * Applies linear time indexation to all comparable sale prices and returns
 * the resulting price range statistics. Useful for comparing the spread
 * before and after temporal normalization.
 *
 * Returns null when fewer than 2 comparables or monthlyRatePct is 0.
 */
export function computeTimeAdjustedPriceRange(
  comps: Comparable[],
  monthlyRatePct: number,
): TimeAdjustedPriceRange | null {
  if (comps.length < 2 || monthlyRatePct === 0) return null

  const indexed = computePriceIndexation(comps, monthlyRatePct)
  const prices = indexed.map(e => e.indexedPrice).sort((a, b) => a - b)

  const min = prices[0]
  const max = prices[prices.length - 1]
  const mid = Math.floor(prices.length / 2)
  const median = prices.length % 2 === 0
    ? Math.round((prices[mid - 1] + prices[mid]) / 2)
    : prices[mid]

  return { min, max, median, range: max - min, count: prices.length }
}
