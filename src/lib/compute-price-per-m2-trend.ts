import type { Comparable } from '@/types'

export interface PricePerM2Trend {
  /** Number of comparables used (with hab_m2 and sale_date) */
  count: number
  /** Change in $/m² per calendar month (OLS slope) */
  slopePerMonth: number
  /** Coefficient of determination (0–1) — fit quality */
  r2: number
  /** 'rising' when slope > 50, 'falling' when slope < −50, 'stable' otherwise */
  direction: 'rising' | 'falling' | 'stable'
  /** True when r² ≥ 0.5 — trend is statistically meaningful */
  significant: boolean
}

/**
 * Fits a linear regression of price-per-m² vs sale date across comparables.
 * x = months since earliest sale_date, y = $/m².
 *
 * Returns null when fewer than 3 comparables have both hab_m2 and sale_date.
 */
export function computePricePerM2Trend(comps: Comparable[]): PricePerM2Trend | null {
  const valid = comps.filter(
    c => c.hab_m2 != null && c.hab_m2 > 0 && c.sale_price > 0 && c.sale_date,
  ) as (Comparable & { hab_m2: number; sale_date: string })[]

  if (valid.length < 3) return null

  const sorted = [...valid].sort((a, b) => a.sale_date.localeCompare(b.sale_date))
  const t0 = new Date(sorted[0].sale_date).getTime()
  const MS_PER_MONTH = 1000 * 60 * 60 * 24 * 30.4375

  const points = sorted.map(c => ({
    x: (new Date(c.sale_date).getTime() - t0) / MS_PER_MONTH,
    y: c.sale_price / c.hab_m2,
  }))

  const n = points.length
  const sumX = points.reduce((s, p) => s + p.x, 0)
  const sumY = points.reduce((s, p) => s + p.y, 0)
  const sumXY = points.reduce((s, p) => s + p.x * p.y, 0)
  const sumX2 = points.reduce((s, p) => s + p.x * p.x, 0)

  const denominator = n * sumX2 - sumX * sumX
  if (denominator === 0) return null

  const slope = (n * sumXY - sumX * sumY) / denominator
  const intercept = (sumY - slope * sumX) / n

  const meanY = sumY / n
  const ssTot = points.reduce((s, p) => s + (p.y - meanY) ** 2, 0)
  const ssRes = points.reduce((s, p) => s + (p.y - (intercept + slope * p.x)) ** 2, 0)
  const r2 = ssTot > 0 ? Math.round((1 - ssRes / ssTot) * 1000) / 1000 : 0
  const slopePerMonth = Math.round(slope * 10) / 10

  const direction: PricePerM2Trend['direction'] =
    slopePerMonth > 50 ? 'rising' : slopePerMonth < -50 ? 'falling' : 'stable'

  return { count: n, slopePerMonth, r2, direction, significant: r2 >= 0.5 }
}
