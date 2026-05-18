import type { Comparable } from '@/types'

export interface SizeTierEntry {
  label: string
  minM2: number | null
  maxM2: number | null
  count: number
  avgPrice: number | null
}

export interface ComparableSizeTierDistribution {
  tiers: SizeTierEntry[]
  missingCount: number
}

const TIERS: Array<{ label: string; minM2: number | null; maxM2: number | null }> = [
  { label: '< 80 m²',     minM2: null, maxM2: 80  },
  { label: '80 – 120 m²', minM2: 80,   maxM2: 120 },
  { label: '120 – 160 m²',minM2: 120,  maxM2: 160 },
  { label: '> 160 m²',    minM2: 160,  maxM2: null },
]

export function computeComparableSizeTierDistribution(comps: Comparable[]): ComparableSizeTierDistribution | null {
  if (comps.length === 0) return null

  const missingCount = comps.filter(c => c.hab_m2 == null || c.hab_m2 <= 0).length
  const valid = comps.filter(c => c.hab_m2 != null && c.hab_m2 > 0)

  const tiers: SizeTierEntry[] = TIERS.map(t => {
    const matched = valid.filter(c => {
      const m = c.hab_m2!
      const aboveMin = t.minM2 === null || m >= t.minM2
      const belowMax = t.maxM2 === null || m < t.maxM2
      return aboveMin && belowMax
    })
    const avgPrice = matched.length > 0
      ? matched.reduce((s, c) => s + c.sale_price, 0) / matched.length
      : null
    return { ...t, count: matched.length, avgPrice }
  })

  return { tiers, missingCount }
}
