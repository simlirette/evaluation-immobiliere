import type { Comparable } from '@/types'

export interface FieldCoverageEntry {
  field: string
  label: string
  presentCount: number
  totalCount: number
  coveragePct: number
}

export interface ComparableFieldCoverage {
  fields: FieldCoverageEntry[]
  /** Mean coverage % across all 5 tracked fields (0–100) */
  overallScore: number
  /** Number of fields with coverage < 50% */
  sparseFieldCount: number
}

const FIELDS: Array<{ key: keyof Comparable; label: string }> = [
  { key: 'hab_m2', label: 'Surface hab.' },
  { key: 'terrain_m2', label: 'Terrain' },
  { key: 'year_built', label: 'Année const.' },
  { key: 'renovated_year', label: 'Année rénov.' },
  { key: 'garage_type', label: 'Type garage' },
]

/**
 * Measures what % of comparables have non-null data for each key property field.
 * Useful for identifying where the comp set has data gaps.
 *
 * Returns null when comparables array is empty.
 */
export function computeComparableFieldCoverage(
  comps: Comparable[],
): ComparableFieldCoverage | null {
  if (comps.length === 0) return null

  const n = comps.length
  const fields: FieldCoverageEntry[] = FIELDS.map(({ key, label }) => {
    const presentCount = comps.filter(c => c[key] != null).length
    const coveragePct = Math.round((presentCount / n) * 100)
    return { field: key as string, label, presentCount, totalCount: n, coveragePct }
  })

  const overallScore = Math.round(
    fields.reduce((s, f) => s + f.coveragePct, 0) / fields.length,
  )
  const sparseFieldCount = fields.filter(f => f.coveragePct < 50).length

  return { fields, overallScore, sparseFieldCount }
}
