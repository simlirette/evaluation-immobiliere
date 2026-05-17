import type { Adjustment } from '@/types'

export interface AdjustmentTypeRatioEntry {
  type: 'surface' | 'year' | 'condition' | 'garage'
  label: string
  totalAbsolute: number
  pctOfGross: number
  /** True when this type accounts for > 50% of all gross adjustments */
  overReliance: boolean
}

export interface AdjustmentTypeRatioCheck {
  entries: AdjustmentTypeRatioEntry[]
  /** True when any single type is > 50% of gross — signals methodological over-reliance */
  hasOverReliance: boolean
  /** Type with highest pctOfGross among active types, null when grossTotal = 0 */
  dominantType: AdjustmentTypeRatioEntry['type'] | null
}

const LABELS: Record<AdjustmentTypeRatioEntry['type'], string> = {
  surface: 'Surface',
  year: 'Année',
  condition: 'État',
  garage: 'Garage',
}

const FIELD_MAP: Record<AdjustmentTypeRatioEntry['type'], keyof Adjustment> = {
  surface: 'surface_adj',
  year: 'year_adj',
  condition: 'condition_adj',
  garage: 'garage_adj',
}

/**
 * Computes what fraction of total gross adjustments each type accounts for.
 * Flags any type exceeding 50% as overReliance.
 *
 * Returns null when adjustments is empty or grossTotal is zero.
 */
export function computeAdjustmentTypeRatioCheck(
  adjs: Adjustment[],
): AdjustmentTypeRatioCheck | null {
  if (adjs.length === 0) return null

  const types: AdjustmentTypeRatioEntry['type'][] = ['surface', 'year', 'condition', 'garage']

  const grossTotal = adjs.reduce((sum, a) =>
    sum + Math.abs(a.surface_adj) + Math.abs(a.year_adj) + Math.abs(a.condition_adj) + Math.abs(a.garage_adj), 0)

  if (grossTotal === 0) return null

  const entries: AdjustmentTypeRatioEntry[] = types.map(type => {
    const field = FIELD_MAP[type]
    const totalAbsolute = adjs.reduce((s, a) => s + Math.abs(a[field] as number), 0)
    const pctOfGross = Math.round((totalAbsolute / grossTotal) * 1000) / 10
    return { type, label: LABELS[type], totalAbsolute, pctOfGross, overReliance: pctOfGross > 50 }
  })

  const active = entries.filter(e => e.totalAbsolute > 0)
  const dominantType = active.length > 0
    ? active.reduce((best, e) => e.pctOfGross > best.pctOfGross ? e : best).type
    : null

  return {
    entries,
    hasOverReliance: entries.some(e => e.overReliance),
    dominantType,
  }
}
