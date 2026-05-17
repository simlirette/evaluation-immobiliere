import type { Comparable } from '@/types'

export interface GarageTypeGroup {
  type: string
  count: number
  pct: number
}

export interface GarageTypeDistribution {
  groups: GarageTypeGroup[]
  /** Type with the highest count, null when all missing or tied */
  dominantType: string | null
  /** True when more than one distinct non-null garage type exists in the set */
  hasGarageConflict: boolean
  /** Comps with null garage_type */
  missingCount: number
}

/**
 * Groups comparables by garage_type and identifies methodological risk
 * when multiple garage types are present (adjustments may treat them differently).
 *
 * Returns null when no comparables provided.
 */
export function computeGarageTypeDistribution(comps: Comparable[]): GarageTypeDistribution | null {
  if (comps.length === 0) return null

  const missingCount = comps.filter(c => c.garage_type == null).length
  const withType = comps.filter(c => c.garage_type != null)

  const counts = new Map<string, number>()
  for (const c of withType) {
    const t = c.garage_type!
    counts.set(t, (counts.get(t) ?? 0) + 1)
  }

  const groups: GarageTypeGroup[] = [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([type, count]) => ({
      type,
      count,
      pct: Math.round((count / comps.length) * 1000) / 10,
    }))

  const dominantType = groups.length === 1
    ? groups[0].type
    : groups.length > 1 && groups[0].count > groups[1].count
      ? groups[0].type
      : null

  return {
    groups,
    dominantType,
    hasGarageConflict: groups.length > 1,
    missingCount,
  }
}
