import type { Comparable, Adjustment } from '@/types'

export interface PricePerM2Convergence {
  rawM2CV: number
  adjustedM2CV: number
  delta: number
  converged: boolean
}

function cv(values: number[]): number {
  const mean = values.reduce((s, v) => s + v, 0) / values.length
  if (mean === 0) return 0
  const variance = values.reduce((s, v) => s + (v - mean) ** 2, 0) / values.length
  return (Math.sqrt(variance) / mean) * 100
}

export function computePricePerM2Convergence(
  comps: Comparable[],
  adjs: Adjustment[],
): PricePerM2Convergence | null {
  const adjMap = new Map(adjs.map(a => [a.comparable_id, a]))

  const pairs = comps
    .map(c => {
      const adj = adjMap.get(c.id)
      if (!adj || !c.hab_m2 || c.hab_m2 <= 0) return null
      return { rawM2: c.sale_price / c.hab_m2, adjustedM2: adj.adjusted / c.hab_m2 }
    })
    .filter((p): p is NonNullable<typeof p> => p !== null)

  if (pairs.length < 2) return null

  const rawM2CV = cv(pairs.map(p => p.rawM2))
  const adjustedM2CV = cv(pairs.map(p => p.adjustedM2))
  const delta = adjustedM2CV - rawM2CV

  return { rawM2CV, adjustedM2CV, delta, converged: adjustedM2CV < rawM2CV }
}
