import type { Comparable } from '@/types'
import { computePricePerM2 } from './comparable-utils'

export interface ComparableStats {
  count: number
  priceMin: number
  priceMax: number
  dateMin: string   // YYYY-MM-DD — earliest sale
  dateMax: string   // YYYY-MM-DD — most recent sale
  priceM2Min: number | null  // null when any comp lacks hab_m2
  priceM2Max: number | null
}

/**
 * Computes aggregate statistics for a set of comparables.
 * Returns null for empty input.
 */
export function computeComparableStats(comps: Comparable[]): ComparableStats | null {
  if (comps.length === 0) return null

  const prices = comps.map(c => c.sale_price)
  const dates  = comps.map(c => c.sale_date).sort()

  const perM2Values = comps
    .map(c => computePricePerM2(c.sale_price, c.hab_m2))
    .filter((v): v is number => v !== null)

  return {
    count:    comps.length,
    priceMin: Math.min(...prices),
    priceMax: Math.max(...prices),
    dateMin:  dates[0],
    dateMax:  dates[dates.length - 1],
    priceM2Min: perM2Values.length === comps.length ? Math.min(...perM2Values) : null,
    priceM2Max: perM2Values.length === comps.length ? Math.max(...perM2Values) : null,
  }
}
