import type { Adjustment } from '@/types'

export interface AdjustmentTypeProfile {
  type: 'surface' | 'year' | 'condition' | 'garage'
  label: string
  totalAbsolute: number      // sum of |adj| across all comps
  netTotal: number           // sum of adj (signed)
  avgPerComp: number         // netTotal / count (rounded)
  pctOfGrossTotal: number    // totalAbsolute / grossTotal * 100 (1 decimal)
  direction: 'positive' | 'negative' | 'neutral'
}

export interface AdjustmentProfile {
  types: AdjustmentTypeProfile[]
  /** type key with highest totalAbsolute, null when all adjustments are zero */
  dominantType: AdjustmentTypeProfile['type'] | null
  grossTotal: number  // sum of all |adj| across all types and comps
}

const LABELS: Record<AdjustmentTypeProfile['type'], string> = {
  surface: 'Surface',
  year: 'Année',
  condition: 'État',
  garage: 'Garage',
}

/**
 * Breaks down adjustments by type: surface, year, condition, garage.
 * Returns null when adjustments is empty.
 */
export function computeAdjustmentProfile(adjs: Adjustment[]): AdjustmentProfile | null {
  if (adjs.length === 0) return null

  const keys: AdjustmentTypeProfile['type'][] = ['surface', 'year', 'condition', 'garage']
  const fieldMap: Record<AdjustmentTypeProfile['type'], keyof Adjustment> = {
    surface: 'surface_adj',
    year: 'year_adj',
    condition: 'condition_adj',
    garage: 'garage_adj',
  }

  const grossTotal = adjs.reduce((sum, a) =>
    sum + Math.abs(a.surface_adj) + Math.abs(a.year_adj) + Math.abs(a.condition_adj) + Math.abs(a.garage_adj), 0)

  const types: AdjustmentTypeProfile[] = keys.map(type => {
    const field = fieldMap[type]
    const values = adjs.map(a => a[field] as number)
    const totalAbsolute = values.reduce((s, v) => s + Math.abs(v), 0)
    const netTotal = values.reduce((s, v) => s + v, 0)
    const avgPerComp = Math.round(netTotal / adjs.length)
    const pctOfGrossTotal = grossTotal > 0
      ? Math.round((totalAbsolute / grossTotal) * 1000) / 10
      : 0
    const direction: AdjustmentTypeProfile['direction'] =
      netTotal > 0 ? 'positive' : netTotal < 0 ? 'negative' : 'neutral'

    return { type, label: LABELS[type], totalAbsolute, netTotal, avgPerComp, pctOfGrossTotal, direction }
  })

  const nonZero = types.filter(t => t.totalAbsolute > 0)
  const dominantType = nonZero.length > 0
    ? nonZero.reduce((best, t) => t.totalAbsolute > best.totalAbsolute ? t : best).type
    : null

  return { types, dominantType, grossTotal }
}
