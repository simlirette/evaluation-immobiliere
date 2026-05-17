import type { Comparable } from '@/types'

export interface ComparableHabitatProfile {
  count: number
  min: number
  max: number
  mean: number
  median: number
  cv: number
  missingCount: number
}

export function computeComparableHabitatProfile(comps: Comparable[]): ComparableHabitatProfile | null {
  const valid = comps.map(c => c.hab_m2).filter((v): v is number => v !== null && v > 0)
  const missingCount = comps.length - valid.length

  if (valid.length < 2) return null

  const sorted = [...valid].sort((a, b) => a - b)
  const n = sorted.length
  const mean = valid.reduce((s, v) => s + v, 0) / n
  const median = n % 2 === 1
    ? sorted[Math.floor(n / 2)]
    : (sorted[n / 2 - 1] + sorted[n / 2]) / 2
  const variance = valid.reduce((s, v) => s + (v - mean) ** 2, 0) / n
  const cv = (Math.sqrt(variance) / mean) * 100

  return { count: n, min: sorted[0], max: sorted[n - 1], mean, median, cv, missingCount }
}
