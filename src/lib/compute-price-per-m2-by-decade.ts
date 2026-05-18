import type { Comparable } from '@/types'

export interface PricePerM2ByDecadeEntry {
  decade: number
  count: number
  avgPpm2: number
}

export interface PricePerM2ByDecade {
  entries: PricePerM2ByDecadeEntry[]
}

export function computePricePerM2ByDecade(comps: Comparable[]): PricePerM2ByDecade | null {
  const valid = comps.filter(c => c.year_built != null && c.hab_m2 != null && c.hab_m2 > 0)
  if (valid.length === 0) return null

  const buckets = new Map<number, number[]>()
  for (const c of valid) {
    const decade = Math.floor(c.year_built! / 10) * 10
    const ppm2 = c.sale_price / c.hab_m2!
    const existing = buckets.get(decade) ?? []
    existing.push(ppm2)
    buckets.set(decade, existing)
  }

  const entries: PricePerM2ByDecadeEntry[] = [...buckets.entries()]
    .sort(([a], [b]) => a - b)
    .map(([decade, ppm2s]) => ({
      decade,
      count: ppm2s.length,
      avgPpm2: ppm2s.reduce((s, v) => s + v, 0) / ppm2s.length,
    }))

  return { entries }
}
