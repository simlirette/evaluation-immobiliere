import type { Comparable } from '@/types'

export interface TimeAdjustmentRate {
  monthlyRatePct: number    // average implied % change per month
  annualRatePct: number     // annualized (monthlyRatePct × 12), 1 decimal
  basedOn: number           // number of comp pairs contributing to estimate
  /** 'élevée' ≥3 pairs, 'modérée' = 2, 'faible' = 1 */
  confidence: 'élevée' | 'modérée' | 'faible'
}

/**
 * Infers the implied monthly price appreciation rate from a set of comparables.
 * Uses the oldest comparable as baseline; computes rate for every other comp
 * with a different date, then averages.
 * Returns null when fewer than 2 comparables have valid sale_date and sale_price,
 * or when all dates are identical (no time span to measure).
 */
export function computeTimeAdjustmentRate(comps: Comparable[]): TimeAdjustmentRate | null {
  const valid = comps
    .filter(c => c.sale_date && c.sale_price && c.sale_price > 0)
    .map(c => ({ date: c.sale_date!, price: c.sale_price! }))
    .sort((a, b) => a.date.localeCompare(b.date))

  if (valid.length < 2) return null

  const baseline = valid[0]
  const pairs = valid.slice(1).filter(c => c.date !== baseline.date)

  if (pairs.length === 0) return null

  const rates = pairs.map(c => {
    const [by, bm, bd] = baseline.date.split('-').map(Number)
    const [cy, cm, cd] = c.date.split('-').map(Number)
    const months = (cy - by) * 12 + (cm - bm) + (cd - bd) / 30
    if (months <= 0) return null
    return ((c.price - baseline.price) / baseline.price / months) * 100
  }).filter((r): r is number => r !== null)

  if (rates.length === 0) return null

  const monthlyRatePct = rates.reduce((s, r) => s + r, 0) / rates.length
  const annualRatePct = Math.round(monthlyRatePct * 12 * 10) / 10
  const confidence: TimeAdjustmentRate['confidence'] =
    rates.length >= 3 ? 'élevée' : rates.length === 2 ? 'modérée' : 'faible'

  return {
    monthlyRatePct: Math.round(monthlyRatePct * 1000) / 1000,
    annualRatePct,
    basedOn: rates.length,
    confidence,
  }
}
