import type { Comparable } from '@/types'

export interface GarageTypeCount {
  type: string
  count: number
}

export interface ComparableGarageProfile {
  total: number
  missingCount: number
  typeCounts: GarageTypeCount[]
}

export function computeComparableGarageProfile(comps: Comparable[]): ComparableGarageProfile | null {
  if (comps.length === 0) return null

  const missingCount = comps.filter(c => c.garage_type == null).length
  const withGarage = comps.filter(c => c.garage_type != null)

  const counts = new Map<string, number>()
  for (const c of withGarage) {
    const key = c.garage_type!
    counts.set(key, (counts.get(key) ?? 0) + 1)
  }

  const typeCounts: GarageTypeCount[] = Array.from(counts.entries())
    .map(([type, count]) => ({ type, count }))
    .sort((a, b) => b.count - a.count)

  return { total: comps.length, missingCount, typeCounts }
}
