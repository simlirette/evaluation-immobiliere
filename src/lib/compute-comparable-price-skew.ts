import type { Comparable } from '@/types'

export interface ComparablePriceSkew {
  count: number
  mean: number
  median: number
  stdDev: number
  /** (mean − median) / stdDev. Positive = right skew (high outliers), negative = left skew */
  skew: number
  /** 'symétrique' when |skew| < 0.5, 'asymétrie positive' or 'asymétrie négative' otherwise */
  interpretation: 'symétrique' | 'asymétrie positive' | 'asymétrie négative'
}

/**
 * Measures skewness of the sale price distribution across comparables.
 * Uses the non-parametric Bowley skew: (mean − median) / stdDev.
 * Positive skew → high-price outliers pulling the mean up; negative → low-price outliers.
 *
 * Returns null when fewer than 3 comparables.
 */
export function computeComparablePriceSkew(comps: Comparable[]): ComparablePriceSkew | null {
  if (comps.length < 3) return null

  const prices = comps.map(c => c.sale_price)
  const n = prices.length
  const sorted = [...prices].sort((a, b) => a - b)

  const mean = Math.round(prices.reduce((s, v) => s + v, 0) / n)
  const median = n % 2 === 0
    ? Math.round((sorted[n / 2 - 1] + sorted[n / 2]) / 2)
    : sorted[Math.floor(n / 2)]
  const variance = prices.reduce((s, v) => s + (v - mean) ** 2, 0) / n
  const stdDev = Math.round(Math.sqrt(variance))

  const skew = stdDev > 0 ? Math.round(((mean - median) / stdDev) * 100) / 100 : 0
  const interpretation: ComparablePriceSkew['interpretation'] =
    skew > 0.5 ? 'asymétrie positive' : skew < -0.5 ? 'asymétrie négative' : 'symétrique'

  return { count: n, mean, median, stdDev, skew, interpretation }
}
