import type { Comparable } from '@/types'
import { computePricePerM2 } from './comparable-utils'

export interface PricePerM2Stats {
  count: number        // comps with hab_m2 data
  min: number
  max: number
  median: number
  avg: number
  spread: number       // max - min
}

/**
 * Computes aggregate $/m² statistics from a set of comparables.
 * Only includes comparables that have both sale_price and hab_m2.
 * Returns null when fewer than 2 valid comparables.
 */
export function computePricePerM2Stats(comps: Comparable[]): PricePerM2Stats | null {
  const values = comps
    .map(c => computePricePerM2(c.sale_price, c.hab_m2))
    .filter((v): v is number => v !== null)

  if (values.length < 2) return null

  const sorted = [...values].sort((a, b) => a - b)
  const min = sorted[0]
  const max = sorted[sorted.length - 1]
  const avg = Math.round(values.reduce((s, v) => s + v, 0) / values.length)
  const mid = Math.floor(sorted.length / 2)
  const median = sorted.length % 2 === 0
    ? Math.round((sorted[mid - 1] + sorted[mid]) / 2)
    : sorted[mid]

  return { count: values.length, min, max, median, avg, spread: max - min }
}
