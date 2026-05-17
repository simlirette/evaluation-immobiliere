import type { Comparable } from '@/types'

export interface DataCompletenessEntry {
  id: string
  comparableLabel: string
  score: number   // out of 5
  missingFields: string[]
}

export interface ComparableDataCompleteness {
  entries: DataCompletenessEntry[]
  avgScore: number
  fullCount: number    // score = 5
  sparseCount: number  // score < 3
}

const FIELDS: Array<{ key: keyof Comparable; label: string }> = [
  { key: 'hab_m2', label: 'Surface hab.' },
  { key: 'terrain_m2', label: 'Terrain' },
  { key: 'year_built', label: 'Année construction' },
  { key: 'renovated_year', label: 'Année rénovation' },
  { key: 'garage_type', label: 'Type garage' },
]

export function computeComparableDataCompleteness(comps: Comparable[]): ComparableDataCompleteness | null {
  if (comps.length === 0) return null

  const entries: DataCompletenessEntry[] = comps.map(c => {
    const missingFields = FIELDS.filter(f => c[f.key] == null).map(f => f.label)
    return { id: c.id, comparableLabel: c.address || c.rank, score: FIELDS.length - missingFields.length, missingFields }
  })

  const avgScore = entries.reduce((s, e) => s + e.score, 0) / entries.length

  return {
    entries,
    avgScore,
    fullCount: entries.filter(e => e.score === 5).length,
    sparseCount: entries.filter(e => e.score < 3).length,
  }
}
