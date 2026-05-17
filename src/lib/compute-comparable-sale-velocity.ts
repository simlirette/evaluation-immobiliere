import type { Comparable } from '@/types'

export interface ComparableSaleVelocity {
  count: number
  spanMonths: number
  salesPerMonth: number
  annualizedRate: number
  signal: 'actif' | 'modéré' | 'lent'
}

export function computeComparableSaleVelocity(comps: Comparable[]): ComparableSaleVelocity | null {
  if (comps.length < 2) return null

  const dates = comps.map(c => new Date(c.sale_date).getTime())
  const minDate = Math.min(...dates)
  const maxDate = Math.max(...dates)

  const spanMs = maxDate - minDate
  const spanMonths = spanMs / (1000 * 60 * 60 * 24 * 30.4375)

  if (spanMonths === 0) return null

  const salesPerMonth = comps.length / spanMonths
  const annualizedRate = salesPerMonth * 12

  const signal: ComparableSaleVelocity['signal'] =
    salesPerMonth > 1 ? 'actif' : salesPerMonth >= 0.5 ? 'modéré' : 'lent'

  return { count: comps.length, spanMonths, salesPerMonth, annualizedRate, signal }
}
