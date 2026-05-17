import type { Adjustment } from '@/types'

export interface AdjustmentMagnitudeEntry {
  type: 'surface' | 'year' | 'condition' | 'garage'
  label: string
  /** Number of comps with a non-zero adjustment for this type */
  nonZeroCount: number
  /** nonZeroCount / total comps × 100 */
  pctOfComps: number
  /** Average absolute value among non-zero adjustments */
  avgAbsolute: number
  /** Largest absolute value seen for this type */
  maxAbsolute: number
}

export interface AdjustmentMagnitudeProfile {
  entries: AdjustmentMagnitudeEntry[]
  /** Type with the largest avgAbsolute */
  dominantType: AdjustmentMagnitudeEntry['type'] | null
}

const LABELS: Record<string, string> = {
  surface: 'Surface',
  year: 'Année',
  condition: 'État',
  garage: 'Garage',
}

/**
 * Profiles the magnitude of each adjustment type across the comparable set.
 * Reveals which types dominate and how broadly they're applied.
 *
 * Returns null when no adjustments provided.
 */
export function computeAdjustmentMagnitudeProfile(adjs: Adjustment[]): AdjustmentMagnitudeProfile | null {
  if (adjs.length === 0) return null

  const types = ['surface', 'year', 'condition', 'garage'] as const
  const fieldMap: Record<string, keyof Adjustment> = {
    surface: 'surface_adj',
    year: 'year_adj',
    condition: 'condition_adj',
    garage: 'garage_adj',
  }

  const entries: AdjustmentMagnitudeEntry[] = types.map(type => {
    const field = fieldMap[type] as keyof Adjustment
    const values = adjs.map(a => Math.abs(a[field] as number))
    const nonZero = values.filter(v => v > 0)
    const nonZeroCount = nonZero.length
    const pctOfComps = Math.round((nonZeroCount / adjs.length) * 1000) / 10
    const avgAbsolute = nonZeroCount > 0
      ? Math.round(nonZero.reduce((s, v) => s + v, 0) / nonZeroCount)
      : 0
    const maxAbsolute = nonZeroCount > 0 ? Math.max(...nonZero) : 0
    return { type, label: LABELS[type], nonZeroCount, pctOfComps, avgAbsolute, maxAbsolute }
  })

  const active = entries.filter(e => e.nonZeroCount > 0)
  const dominantType = active.length > 0
    ? active.reduce((best, e) => e.avgAbsolute > best.avgAbsolute ? e : best).type
    : null

  return { entries, dominantType }
}
