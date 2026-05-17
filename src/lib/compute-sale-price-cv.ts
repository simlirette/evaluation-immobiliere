import type { Comparable } from '@/types'

export interface SalePriceCV {
  count: number
  mean: number
  stdDev: number
  cv: number
  cohesion: 'homogène' | 'modérée' | 'hétérogène'
}

export function computeSalePriceCV(comps: Comparable[]): SalePriceCV | null {
  if (comps.length < 2) return null

  const prices = comps.map(c => c.sale_price)
  const count = prices.length
  const mean = prices.reduce((s, p) => s + p, 0) / count
  const variance = prices.reduce((s, p) => s + (p - mean) ** 2, 0) / count
  const stdDev = Math.sqrt(variance)
  const cv = (stdDev / mean) * 100

  const cohesion: SalePriceCV['cohesion'] =
    cv < 10 ? 'homogène' : cv <= 20 ? 'modérée' : 'hétérogène'

  return { count, mean, stdDev, cv, cohesion }
}
