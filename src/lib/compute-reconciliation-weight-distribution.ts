import type { Adjustment } from '@/types'

export interface ReconciliationWeightEntry {
  id: string
  comparableLabel: string
  grossPct: number
  weight: number
  weightPct: number
}

export interface ReconciliationWeightDistribution {
  entries: ReconciliationWeightEntry[]
  herfindahl: number
}

export function computeReconciliationWeightDistribution(adjs: Adjustment[]): ReconciliationWeightDistribution | null {
  if (adjs.length === 0) return null

  const rawWeights = adjs.map(a => {
    const gross = Math.abs(a.surface_adj) + Math.abs(a.year_adj) + Math.abs(a.condition_adj) + Math.abs(a.garage_adj)
    const grossPct = (gross / a.salePrice) * 100
    return { id: a.id, comparableLabel: a.comparableLabel, grossPct, weight: 1 / (grossPct + 1) }
  })

  const totalWeight = rawWeights.reduce((s, r) => s + r.weight, 0)

  const entries: ReconciliationWeightEntry[] = rawWeights.map(r => ({
    id: r.id,
    comparableLabel: r.comparableLabel,
    grossPct: r.grossPct,
    weight: r.weight,
    weightPct: (r.weight / totalWeight) * 100,
  }))

  const herfindahl = entries.reduce((s, e) => s + (e.weightPct / 100) ** 2, 0)

  return { entries, herfindahl }
}
