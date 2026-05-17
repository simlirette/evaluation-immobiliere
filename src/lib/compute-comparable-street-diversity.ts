import type { Comparable } from '@/types'

export interface ComparableStreetDiversity {
  uniqueCount: number
  totalCount: number
  concentrated: boolean
  streets: string[]
}

function extractStreet(address: string): string {
  // Strip leading digits/unit (e.g. "123 ", "123A ", "123-5 ") then take rest
  return address.replace(/^\d[\d\w-]*\s+/, '').trim().toLowerCase() || address.trim().toLowerCase()
}

export function computeComparableStreetDiversity(comps: Comparable[]): ComparableStreetDiversity | null {
  if (comps.length === 0) return null

  const streets = [...new Set(comps.map(c => extractStreet(c.address)).filter(Boolean))]

  return {
    uniqueCount: streets.length,
    totalCount: comps.length,
    concentrated: streets.length === 1,
    streets,
  }
}
