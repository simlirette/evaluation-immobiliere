import type { Adjustment } from '@/types'

export interface ZeroRateEntry {
  type: 'surface' | 'year' | 'condition' | 'garage'
  label: string
  zeroCount: number
  zeroPct: number
}

export interface AdjustmentZeroRateByType {
  entries: ZeroRateEntry[]
  unusedTypes: string[]
  universalTypes: string[]
}

const TYPE_LABELS: Record<string, string> = {
  surface: 'Surface',
  year: 'Année',
  condition: 'État',
  garage: 'Garage',
}

export function computeAdjustmentZeroRateByType(adjs: Adjustment[]): AdjustmentZeroRateByType | null {
  if (adjs.length === 0) return null

  const types = ['surface', 'year', 'condition', 'garage'] as const
  const entries: ZeroRateEntry[] = types.map(type => {
    const key = `${type}_adj` as keyof typeof adjs[0]
    const zeroCount = adjs.filter(a => a[key] === 0).length
    const zeroPct = Math.round((zeroCount / adjs.length) * 100)
    return { type, label: TYPE_LABELS[type], zeroCount, zeroPct }
  })

  const unusedTypes = entries.filter(e => e.zeroPct === 100).map(e => e.label)
  const universalTypes = entries.filter(e => e.zeroPct === 0).map(e => e.label)

  return { entries, unusedTypes, universalTypes }
}
