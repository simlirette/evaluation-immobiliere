import type { Comparable } from '@/types'

export interface ComparablePriceTrendByDate {
  slope: number
  r2: number
  direction: 'hausse' | 'baisse' | 'stable'
  count: number
}

export function computeComparablePriceTrendByDate(comps: Comparable[]): ComparablePriceTrendByDate | null {
  if (comps.length < 2) return null

  const sorted = [...comps].sort((a, b) => a.sale_date.localeCompare(b.sale_date))
  const t0 = new Date(sorted[0].sale_date).getTime()
  const MS_PER_MONTH = 1000 * 60 * 60 * 24 * 30.4375

  const xs = sorted.map(c => (new Date(c.sale_date).getTime() - t0) / MS_PER_MONTH)
  const ys = sorted.map(c => c.sale_price)
  const n = xs.length

  const meanX = xs.reduce((s, v) => s + v, 0) / n
  const meanY = ys.reduce((s, v) => s + v, 0) / n

  let ssXY = 0, ssXX = 0, ssYY = 0
  for (let i = 0; i < n; i++) {
    const dx = xs[i] - meanX
    const dy = ys[i] - meanY
    ssXY += dx * dy
    ssXX += dx * dx
    ssYY += dy * dy
  }

  if (ssXX === 0) return null

  const slope = ssXY / ssXX
  const r2 = ssYY === 0 ? 1 : (ssXY * ssXY) / (ssXX * ssYY)
  const direction: 'hausse' | 'baisse' | 'stable' =
    slope > 0 ? 'hausse' : slope < 0 ? 'baisse' : 'stable'

  return { slope, r2, direction, count: n }
}
