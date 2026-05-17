import type { Comparable } from '@/types'

/**
 * Filters comparables by address substring (case-insensitive, accent-insensitive).
 * Empty or whitespace-only query returns the full array unchanged.
 */
export function filterComparablesByQuery(comps: Comparable[], query: string): Comparable[] {
  const q = query.trim().toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
  if (!q) return comps
  return comps.filter(c => {
    const addr = c.address.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    return addr.includes(q)
  })
}
