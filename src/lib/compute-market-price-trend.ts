import type { Comparable } from '@/types'

export interface MarketPriceTrend {
  earliestDate: string     // ISO date of oldest comparable
  latestDate: string       // ISO date of most recent comparable
  earliestPrice: number
  latestPrice: number
  periodMonths: number
  variationPct: number     // total % change from earliest to latest (1 decimal)
  annualizedPct: number    // annualized % change (1 decimal)
  direction: 'hausse' | 'baisse' | 'stable'
}

/**
 * Computes price trend from a set of comparables using the two most temporally
 * extreme comps (oldest and newest by sale_date). Returns null when fewer than
 * 2 comparables have a valid sale_date and sale_price.
 */
export function computeMarketPriceTrend(comps: Comparable[]): MarketPriceTrend | null {
  const valid = comps
    .filter(c => c.sale_date && c.sale_price && c.sale_price > 0)
    .map(c => ({ date: c.sale_date!, price: c.sale_price! }))
    .sort((a, b) => a.date.localeCompare(b.date))

  if (valid.length < 2) return null

  const earliest = valid[0]
  const latest = valid[valid.length - 1]

  if (earliest.date === latest.date) return null

  const [ey, em, ed] = earliest.date.split('-').map(Number)
  const [ly, lm, ld] = latest.date.split('-').map(Number)
  const periodMonths = (ly - ey) * 12 + (lm - em) + (ld - ed) / 30

  if (periodMonths <= 0) return null

  const variationPct = Math.round(((latest.price - earliest.price) / earliest.price) * 1000) / 10
  const annualizedPct = Math.round((variationPct / (periodMonths / 12)) * 10) / 10

  const direction: MarketPriceTrend['direction'] =
    variationPct > 1 ? 'hausse' : variationPct < -1 ? 'baisse' : 'stable'

  return {
    earliestDate: earliest.date,
    latestDate: latest.date,
    earliestPrice: earliest.price,
    latestPrice: latest.price,
    periodMonths: Math.round(periodMonths),
    variationPct,
    annualizedPct,
    direction,
  }
}
