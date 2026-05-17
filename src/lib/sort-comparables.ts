import type { Comparable } from '@/types'
import { computePricePerM2 } from './comparable-utils'

export type ComparableSortKey = 'rank' | 'prix' | 'prix_m2' | 'date' | 'surface'

/**
 * Returns a new sorted array of comparables. Original array is not mutated.
 */
export function sortComparables(comps: Comparable[], key: ComparableSortKey): Comparable[] {
  const sorted = [...comps]
  switch (key) {
    case 'rank':
      return sorted.sort((a, b) => Number(a.rank) - Number(b.rank))
    case 'prix':
      return sorted.sort((a, b) => a.sale_price - b.sale_price)
    case 'prix_m2': {
      const pm2 = (c: Comparable) => computePricePerM2(c.sale_price, c.hab_m2) ?? Infinity
      return sorted.sort((a, b) => pm2(a) - pm2(b))
    }
    case 'date':
      return sorted.sort((a, b) => b.sale_date.localeCompare(a.sale_date))
    case 'surface': {
      const surf = (c: Comparable) => c.hab_m2 ?? 0
      return sorted.sort((a, b) => surf(b) - surf(a))
    }
  }
}
