import type { Comparable } from '@/types'

export interface ComparableDateSpread {
  /** Earliest and latest sale dates (ISO strings) */
  minDate: string
  maxDate: string
  /** Total span in calendar months between earliest and latest sale */
  spanMonths: number
  /** Comps sold within the last 12 months */
  recent12mCount: number
  /** Comps sold more than 24 months ago */
  staleCount: number
  /** 'récent' ≥75% within 12mo; 'daté' ≥50% stale; else 'mixte' */
  recencyScore: 'récent' | 'mixte' | 'daté'
}

/**
 * Analyses the temporal spread of a comparable set.
 * Returns null when fewer than 2 comparables provided.
 */
export function computeComparableDateSpread(comps: Comparable[]): ComparableDateSpread | null {
  if (comps.length < 2) return null

  const today = new Date()
  const dates = comps.map(c => new Date(c.sale_date))
  const sorted = [...dates].sort((a, b) => a.getTime() - b.getTime())

  const minDate = sorted[0].toISOString().slice(0, 10)
  const maxDate = sorted[sorted.length - 1].toISOString().slice(0, 10)

  const earliest = sorted[0]
  const latest = sorted[sorted.length - 1]
  const spanMonths =
    (latest.getFullYear() - earliest.getFullYear()) * 12
    + (latest.getMonth() - earliest.getMonth())

  const monthsAgo = (d: Date) =>
    (today.getFullYear() - d.getFullYear()) * 12
    + (today.getMonth() - d.getMonth())

  const recent12mCount = dates.filter(d => monthsAgo(d) <= 12).length
  const staleCount = dates.filter(d => monthsAgo(d) > 24).length

  const stalePct = staleCount / comps.length
  const recentPct = recent12mCount / comps.length
  const recencyScore: ComparableDateSpread['recencyScore'] =
    recentPct >= 0.75 ? 'récent' : stalePct >= 0.5 ? 'daté' : 'mixte'

  return { minDate, maxDate, spanMonths, recent12mCount, staleCount, recencyScore }
}
