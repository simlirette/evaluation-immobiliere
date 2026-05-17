import type { Adjustment } from '@/types'

export type AdjType = 'surface' | 'year' | 'condition' | 'garage' | 'none'

export interface DominantTypeEntry {
  id: string
  comparableLabel: string
  dominantType: AdjType
  dominantValue: number
}

export interface AdjustmentDominantTypeByComp {
  entries: DominantTypeEntry[]
  mostCommonDominantType: AdjType
}

export function computeAdjustmentDominantTypeByComp(adjs: Adjustment[]): AdjustmentDominantTypeByComp | null {
  if (adjs.length === 0) return null

  const entries: DominantTypeEntry[] = adjs.map(a => {
    const candidates: Array<[AdjType, number]> = [
      ['surface', Math.abs(a.surface_adj)],
      ['year', Math.abs(a.year_adj)],
      ['condition', Math.abs(a.condition_adj)],
      ['garage', Math.abs(a.garage_adj)],
    ]
    const max = candidates.reduce((best, cur) => cur[1] > best[1] ? cur : best, ['none' as AdjType, 0])
    const dominantType: AdjType = max[1] === 0 ? 'none' : max[0] as AdjType
    return { id: a.id, comparableLabel: a.comparableLabel, dominantType, dominantValue: max[1] }
  })

  const counts = new Map<AdjType, number>()
  for (const e of entries) counts.set(e.dominantType, (counts.get(e.dominantType) ?? 0) + 1)
  const mostCommonDominantType = [...counts.entries()].reduce(
    (best, cur) => cur[1] > best[1] ? cur : best,
    ['none' as AdjType, 0],
  )[0] as AdjType

  return { entries, mostCommonDominantType }
}
