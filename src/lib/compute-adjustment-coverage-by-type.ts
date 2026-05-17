import type { Adjustment } from '@/types'

export interface AdjustmentCoverageEntry {
  type: 'surface' | 'year' | 'condition' | 'garage'
  label: string
  /** Number of comps with a non-zero adjustment for this type */
  nonZeroCount: number
  /** nonZeroCount / total comps × 100 */
  coveragePct: number
  /** Mean absolute value of adjustment when non-zero (0 when nonZeroCount = 0) */
  avgAbsWhenApplied: number
}

export interface AdjustmentCoverageByType {
  entries: AdjustmentCoverageEntry[]
  /** Types applied to ≥ 80% of comparables */
  universalTypes: AdjustmentCoverageEntry['type'][]
  /** Types never applied (coveragePct = 0) */
  unusedTypes: AdjustmentCoverageEntry['type'][]
}

const LABELS: Record<AdjustmentCoverageEntry['type'], string> = {
  surface: 'Surface',
  year: 'Année',
  condition: 'État',
  garage: 'Garage',
}

type AdjField = 'surface_adj' | 'year_adj' | 'condition_adj' | 'garage_adj'

const FIELD_MAP: Record<AdjustmentCoverageEntry['type'], AdjField> = {
  surface: 'surface_adj',
  year: 'year_adj',
  condition: 'condition_adj',
  garage: 'garage_adj',
}

/**
 * For each adjustment type, computes what fraction of comparables received
 * a non-zero adjustment and the average magnitude when applied.
 *
 * Returns null when adjustments is empty.
 */
export function computeAdjustmentCoverageByType(
  adjs: Adjustment[],
): AdjustmentCoverageByType | null {
  if (adjs.length === 0) return null

  const types: AdjustmentCoverageEntry['type'][] = ['surface', 'year', 'condition', 'garage']

  const entries: AdjustmentCoverageEntry[] = types.map(type => {
    const field = FIELD_MAP[type]
    const values = adjs.map(a => a[field] as number)
    const nonZeroValues = values.filter(v => v !== 0)
    const nonZeroCount = nonZeroValues.length
    const coveragePct = Math.round((nonZeroCount / adjs.length) * 100)
    const avgAbsWhenApplied = nonZeroCount > 0
      ? Math.round(nonZeroValues.reduce((s, v) => s + Math.abs(v), 0) / nonZeroCount)
      : 0

    return { type, label: LABELS[type], nonZeroCount, coveragePct, avgAbsWhenApplied }
  })

  return {
    entries,
    universalTypes: entries.filter(e => e.coveragePct >= 80).map(e => e.type),
    unusedTypes: entries.filter(e => e.coveragePct === 0).map(e => e.type),
  }
}
