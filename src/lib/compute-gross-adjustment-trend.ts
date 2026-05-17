import type { Comparable, Adjustment } from '@/types'
import { computeGrossAdjustment } from './compute-gross-adjustment'

export interface GrossAdjustmentTrend {
  count: number
  /** OLS slope: change in grossPct per month older the comp is */
  slopePerMonth: number
  /** Coefficient of determination (0–1) */
  r2: number
  /**
   * 'increasing' when slope > 0.5 pct/month — older comps need more adjustment
   * 'decreasing' when slope < -0.5 pct/month
   * 'stable' otherwise
   */
  direction: 'increasing' | 'decreasing' | 'stable'
  /** True when r² ≥ 0.4 — trend is worth noting */
  significant: boolean
}

/**
 * Fits a linear regression of gross adjustment % vs months-since-sale.
 * A significant positive slope suggests that time adjustments may be
 * underestimating the market appreciation needed for older comps.
 *
 * Returns null when fewer than 3 adjustment/comparable pairs with sale dates.
 */
export function computeGrossAdjustmentTrend(
  comps: Comparable[],
  adjs: Adjustment[],
): GrossAdjustmentTrend | null {
  const adjMap = new Map(adjs.map(a => [a.comparable_id, a]))
  const today = new Date()

  const points = comps
    .filter(c => adjMap.has(c.id) && c.sale_date)
    .map(c => {
      const adj = adjMap.get(c.id)!
      const { grossPct } = computeGrossAdjustment(adj)
      const sale = new Date(c.sale_date)
      const monthsAgo =
        (today.getFullYear() - sale.getFullYear()) * 12 +
        (today.getMonth() - sale.getMonth())
      return { x: Math.max(0, monthsAgo), y: grossPct }
    })

  if (points.length < 3) return null

  const n = points.length
  const sumX = points.reduce((s, p) => s + p.x, 0)
  const sumY = points.reduce((s, p) => s + p.y, 0)
  const sumXY = points.reduce((s, p) => s + p.x * p.y, 0)
  const sumX2 = points.reduce((s, p) => s + p.x * p.x, 0)

  const denom = n * sumX2 - sumX * sumX
  if (denom === 0) return null

  const slope = (n * sumXY - sumX * sumY) / denom
  const intercept = (sumY - slope * sumX) / n

  const meanY = sumY / n
  const ssTot = points.reduce((s, p) => s + (p.y - meanY) ** 2, 0)
  const ssRes = points.reduce((s, p) => s + (p.y - (intercept + slope * p.x)) ** 2, 0)
  const r2 = ssTot > 0 ? Math.round((1 - ssRes / ssTot) * 1000) / 1000 : 0
  const slopePerMonth = Math.round(slope * 100) / 100

  const direction: GrossAdjustmentTrend['direction'] =
    slopePerMonth > 0.2 ? 'increasing' : slopePerMonth < -0.2 ? 'decreasing' : 'stable'

  return { count: n, slopePerMonth, r2, direction, significant: r2 >= 0.4 }
}
