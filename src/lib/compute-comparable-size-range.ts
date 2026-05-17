import type { Comparable } from '@/types'

export interface ComparableSizeRangeEntry {
  comparableId: string
  hab_m2: number
}

export interface ComparableSizeRange {
  min: number
  max: number
  subjectHabM2: number
  /** True when subjectHabM2 is within [min, max] of comp hab_m2 values */
  bracketed: boolean
  /** Closest comp with hab_m2 < subjectHabM2, or null */
  nearestBelow: ComparableSizeRangeEntry | null
  /** Closest comp with hab_m2 > subjectHabM2, or null */
  nearestAbove: ComparableSizeRangeEntry | null
  /** Number of comps excluded due to null hab_m2 */
  missingCount: number
}

/**
 * Checks whether a subject's living area is bracketed by the comp set.
 * OEAQ size-bracketing: at least one comp should be smaller and one larger.
 *
 * Returns null when subjectHabM2 is null/zero or fewer than 2 comps have hab_m2.
 */
export function computeComparableSizeRange(
  comps: Comparable[],
  subjectHabM2: number | null,
): ComparableSizeRange | null {
  if (!subjectHabM2 || subjectHabM2 <= 0) return null

  const valid = comps.filter(c => c.hab_m2 != null && c.hab_m2 > 0) as (Comparable & { hab_m2: number })[]
  const missingCount = comps.length - valid.length

  if (valid.length < 2) return null

  const sorted = [...valid].sort((a, b) => a.hab_m2 - b.hab_m2)
  const min = sorted[0].hab_m2
  const max = sorted[sorted.length - 1].hab_m2
  const bracketed = subjectHabM2 >= min && subjectHabM2 <= max

  const below = sorted.filter(c => c.hab_m2 < subjectHabM2)
  const above = sorted.filter(c => c.hab_m2 > subjectHabM2)

  const nearestBelow = below.length > 0
    ? { comparableId: below[below.length - 1].id, hab_m2: below[below.length - 1].hab_m2 }
    : null
  const nearestAbove = above.length > 0
    ? { comparableId: above[0].id, hab_m2: above[0].hab_m2 }
    : null

  return { min, max, subjectHabM2, bracketed, nearestBelow, nearestAbove, missingCount }
}
