import type { Comparable } from '@/types'

export interface ComparableCompleteness {
  comparableId: string
  /** Number of key fields present (0–5) */
  presentCount: number
  /** Total key fields checked */
  totalFields: number
  /** Percentage 0–100 */
  completenessPct: number
  /** Missing field names in French */
  missingFields: string[]
  /** 'complet' ≥80%, 'partiel' ≥50%, 'incomplet' <50% */
  grade: 'complet' | 'partiel' | 'incomplet'
}

const KEY_FIELDS: Array<{ key: keyof Comparable; label: string }> = [
  { key: 'hab_m2', label: 'Surface hab.' },
  { key: 'terrain_m2', label: 'Terrain' },
  { key: 'year_built', label: 'Année constr.' },
  { key: 'garage_type', label: 'Garage' },
  { key: 'sale_date', label: 'Date de vente' },
]

/**
 * Scores how complete each comparable's data profile is by checking
 * the presence of key descriptive fields.
 *
 * Returns an entry per comparable; empty array when input is empty.
 */
export function computeComparableCompleteness(comps: Comparable[]): ComparableCompleteness[] {
  return comps.map(c => {
    const missing = KEY_FIELDS.filter(f => !c[f.key]).map(f => f.label)
    const presentCount = KEY_FIELDS.length - missing.length
    const completenessPct = Math.round((presentCount / KEY_FIELDS.length) * 100)
    const grade: ComparableCompleteness['grade'] =
      completenessPct >= 80 ? 'complet' : completenessPct >= 50 ? 'partiel' : 'incomplet'

    return {
      comparableId: c.id,
      presentCount,
      totalFields: KEY_FIELDS.length,
      completenessPct,
      missingFields: missing,
      grade,
    }
  })
}
