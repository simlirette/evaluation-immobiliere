import type { Comparable } from '@/types'

export interface PricePerM2Panel {
  count: number
  min: number
  max: number
  mean: number
  median: number
  stdDev: number
  cv: number
}

export function computePricePerM2Panel(comps: Comparable[]): PricePerM2Panel | null {
  const valid = comps.filter(c => c.hab_m2 != null && c.hab_m2 > 0)
  if (valid.length < 2) return null

  const ppm2s = valid.map(c => c.sale_price / c.hab_m2!)
  const sorted = [...ppm2s].sort((a, b) => a - b)
  const n = sorted.length
  const mean = ppm2s.reduce((s, v) => s + v, 0) / n
  const median = n % 2 === 1
    ? sorted[Math.floor(n / 2)]
    : (sorted[n / 2 - 1] + sorted[n / 2]) / 2
  const variance = ppm2s.reduce((s, v) => s + (v - mean) ** 2, 0) / n
  const stdDev = Math.sqrt(variance)
  const cv = mean > 0 ? (stdDev / mean) * 100 : 0

  return { count: n, min: sorted[0], max: sorted[n - 1], mean, median, stdDev, cv }
}
