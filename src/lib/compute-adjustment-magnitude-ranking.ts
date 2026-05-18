import type { Adjustment } from '@/types'

export type AdjustmentType = 'surface' | 'year' | 'condition' | 'garage'

export interface AdjustmentMagnitudeEntry {
  type: AdjustmentType
  totalAbsolute: number
  avgAbsolute: number
  rank: number
}

export interface AdjustmentMagnitudeRanking {
  entries: AdjustmentMagnitudeEntry[]
}

export function computeAdjustmentMagnitudeRanking(adjs: Adjustment[]): AdjustmentMagnitudeRanking | null {
  if (adjs.length === 0) return null

  const types: AdjustmentType[] = ['surface', 'year', 'condition', 'garage']
  const keyMap: Record<AdjustmentType, keyof Adjustment> = {
    surface: 'surface_adj',
    year: 'year_adj',
    condition: 'condition_adj',
    garage: 'garage_adj',
  }

  const unsorted = types.map(type => {
    const key = keyMap[type]
    const totalAbsolute = adjs.reduce((s, a) => s + Math.abs(a[key] as number), 0)
    const avgAbsolute = totalAbsolute / adjs.length
    return { type, totalAbsolute, avgAbsolute, rank: 0 }
  })

  unsorted.sort((a, b) => b.totalAbsolute - a.totalAbsolute)
  unsorted.forEach((e, i) => { e.rank = i + 1 })

  return { entries: unsorted }
}
