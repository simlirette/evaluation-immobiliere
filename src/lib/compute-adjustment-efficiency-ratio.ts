import type { Adjustment } from '@/types'

export interface AdjustmentEfficiencyEntry {
  id: string
  comparableLabel: string
  netAdj: number
  grossAdj: number
  efficiency: number
}

export interface AdjustmentEfficiencyRatio {
  entries: AdjustmentEfficiencyEntry[]
  mean: number
  min: number
  max: number
}

export function computeAdjustmentEfficiencyRatio(adjs: Adjustment[]): AdjustmentEfficiencyRatio | null {
  if (adjs.length === 0) return null

  const entries: AdjustmentEfficiencyEntry[] = []

  for (const a of adjs) {
    const netAdj = a.surface_adj + a.year_adj + a.condition_adj + a.garage_adj
    const grossAdj = Math.abs(a.surface_adj) + Math.abs(a.year_adj) + Math.abs(a.condition_adj) + Math.abs(a.garage_adj)
    const efficiency = grossAdj === 0 ? 0 : Math.abs(netAdj) / grossAdj
    entries.push({ id: a.id, comparableLabel: a.comparableLabel, netAdj, grossAdj, efficiency })
  }

  const efficiencies = entries.map(e => e.efficiency)
  const mean = efficiencies.reduce((s, v) => s + v, 0) / efficiencies.length
  const min = Math.min(...efficiencies)
  const max = Math.max(...efficiencies)

  return { entries, mean, min, max }
}
