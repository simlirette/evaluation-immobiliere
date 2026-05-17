import type { Comparable } from '@/types'

export type RecencyLabel = 'récent' | 'modéré' | 'daté'

export interface DateRecencyEntry {
  id: string
  comparableLabel: string
  monthsAgo: number
  recency: RecencyLabel
}

export interface ComparableDateRecencyProfile {
  entries: DateRecencyEntry[]
  recentCount: number
  moderateCount: number
  staleCount: number
  stalePct: number
}

function monthsAgo(saleDate: string): number {
  const sale = new Date(saleDate).getTime()
  const now = Date.now()
  return (now - sale) / (1000 * 60 * 60 * 24 * 30.4375)
}

function recencyLabel(months: number): RecencyLabel {
  return months <= 12 ? 'récent' : months <= 24 ? 'modéré' : 'daté'
}

export function computeComparableDateRecencyProfile(comps: Comparable[]): ComparableDateRecencyProfile | null {
  if (comps.length === 0) return null

  const entries: DateRecencyEntry[] = comps.map(c => {
    const months = monthsAgo(c.sale_date)
    return { id: c.id, comparableLabel: c.address || c.rank, monthsAgo: months, recency: recencyLabel(months) }
  })

  const recentCount = entries.filter(e => e.recency === 'récent').length
  const moderateCount = entries.filter(e => e.recency === 'modéré').length
  const staleCount = entries.filter(e => e.recency === 'daté').length
  const stalePct = Math.round((staleCount / entries.length) * 100)

  return { entries, recentCount, moderateCount, staleCount, stalePct }
}
