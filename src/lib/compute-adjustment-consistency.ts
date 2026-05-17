import type { Adjustment } from '@/types'

export interface AdjustmentConsistencyCheck {
  type: 'surface' | 'year' | 'condition' | 'garage'
  label: string
  consistent: boolean   // all non-zero values share the same direction
  positiveCount: number
  negativeCount: number
  zeroCount: number
  warning: string | null
}

const LABELS: Record<string, string> = {
  surface: 'Surface', year: 'Année', condition: 'État', garage: 'Garage',
}

const FIELD_MAP: Record<string, keyof Adjustment> = {
  surface: 'surface_adj', year: 'year_adj', condition: 'condition_adj', garage: 'garage_adj',
}

/**
 * Checks directional consistency of each adjustment type across all comparables.
 * An inconsistency (mixed + and - for the same type) may indicate a methodological error.
 * Types where all values are zero are marked consistent with no warning.
 * Returns empty array when fewer than 2 adjustments.
 */
export function computeAdjustmentConsistency(
  adjs: Adjustment[],
): AdjustmentConsistencyCheck[] {
  if (adjs.length < 2) return []

  const types = ['surface', 'year', 'condition', 'garage'] as const

  return types.map(type => {
    const values = adjs.map(a => a[FIELD_MAP[type]] as number)
    const positiveCount = values.filter(v => v > 0).length
    const negativeCount = values.filter(v => v < 0).length
    const zeroCount = values.filter(v => v === 0).length

    const nonZero = positiveCount + negativeCount
    const consistent = nonZero === 0 || positiveCount === 0 || negativeCount === 0

    const warning = consistent ? null
      : `Adj. ${LABELS[type].toLowerCase()} : directions mixtes (${positiveCount}↑ / ${negativeCount}↓) — vérifier la cohérence méthodologique.`

    return { type, label: LABELS[type], consistent, positiveCount, negativeCount, zeroCount, warning }
  })
}
