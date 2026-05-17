import type { Comparable } from '@/types'

export interface DuplicatePair {
  idA: string
  idB: string
  reason: 'same-address' | 'same-price-date'
}

function normalizeAddress(addr: string): string {
  return addr.toLowerCase().replace(/\s+/g, ' ').trim()
}

/**
 * Detects potential duplicate comparables in a set.
 * A duplicate is flagged when two comparables share the same normalized address
 * OR share both the same sale price and sale date (different source, same transaction).
 * Returns all detected pairs — evaluator decides which to remove.
 */
export function detectDuplicateComparables(comps: Comparable[]): DuplicatePair[] {
  const pairs: DuplicatePair[] = []
  for (let i = 0; i < comps.length; i++) {
    for (let j = i + 1; j < comps.length; j++) {
      const a = comps[i]
      const b = comps[j]
      if (normalizeAddress(a.address) === normalizeAddress(b.address)) {
        pairs.push({ idA: a.id, idB: b.id, reason: 'same-address' })
      } else if (a.sale_price === b.sale_price && a.sale_date === b.sale_date) {
        pairs.push({ idA: a.id, idB: b.id, reason: 'same-price-date' })
      }
    }
  }
  return pairs
}
