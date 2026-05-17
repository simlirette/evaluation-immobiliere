import type { Comparable } from '@/types'

export type VintageDecade = 'pre-1950' | '1950–1979' | '1980–1999' | '2000–2019' | '2020+'

export interface VintageGroup {
  decade: VintageDecade
  count: number
  comparableIds: string[]
}

export interface ComparableVintageAnalysis {
  groups: VintageGroup[]
  /** Decade label of the subject property, or null if year not provided */
  subjectDecade: VintageDecade | null
  /**
   * True when subject year_built has no comparable within ±20 years,
   * suggesting the vintage is under-represented in the comp set.
   */
  vintageBias: boolean
  /** IDs of comparables with null year_built */
  missingYearIds: string[]
}

function toDecade(year: number): VintageDecade {
  if (year < 1950) return 'pre-1950'
  if (year < 1980) return '1950–1979'
  if (year < 2000) return '1980–1999'
  if (year < 2020) return '2000–2019'
  return '2020+'
}

const ALL_DECADES: VintageDecade[] = ['pre-1950', '1950–1979', '1980–1999', '2000–2019', '2020+']

/**
 * Groups comparables by construction decade and optionally flags vintage bias
 * when the subject property has no comparable within ±20 years.
 *
 * Returns null when no comparables provided.
 */
export function computeComparableVintageAnalysis(
  comparables: Comparable[],
  subjectYearBuilt?: number | null,
): ComparableVintageAnalysis | null {
  if (comparables.length === 0) return null

  const missingYearIds = comparables.filter(c => c.year_built == null).map(c => c.id)

  // Build decade groups
  const groupMap = new Map<VintageDecade, string[]>(ALL_DECADES.map(d => [d, []]))
  for (const c of comparables) {
    if (c.year_built != null) {
      groupMap.get(toDecade(c.year_built))!.push(c.id)
    }
  }

  const groups: VintageGroup[] = ALL_DECADES.map(decade => ({
    decade,
    count: groupMap.get(decade)!.length,
    comparableIds: groupMap.get(decade)!,
  }))

  // Subject decade
  const subjectDecade = subjectYearBuilt != null ? toDecade(subjectYearBuilt) : null

  // Vintage bias: no comparable within ±20 years of subject
  let vintageBias = false
  if (subjectYearBuilt != null) {
    const compsWithYear = comparables.filter(c => c.year_built != null)
    if (compsWithYear.length > 0) {
      const hasNeighbor = compsWithYear.some(
        c => Math.abs(c.year_built! - subjectYearBuilt) <= 20,
      )
      vintageBias = !hasNeighbor
    }
  }

  return { groups, subjectDecade, vintageBias, missingYearIds }
}
