import type { Comparable } from '@/types'

export function hasPositiveSalePrice(comp: Comparable): boolean {
  return Number.isFinite(comp.sale_price) && comp.sale_price > 0
}

export function hasComparableSource(comp: Comparable): boolean {
  return String(comp.source_id || comp.meta || '').trim().length > 0
}

export function hasIsoSaleDate(comp: Comparable): boolean {
  const text = String(comp.sale_date || '').trim()
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(text)
  if (!match) return false
  const year = Number(match[1])
  const month = Number(match[2])
  const day = Number(match[3])
  const parsed = new Date(Date.UTC(year, month - 1, day))
  return parsed.getUTCFullYear() === year
    && parsed.getUTCMonth() === month - 1
    && parsed.getUTCDate() === day
}

export function isUsableComparable(comp: Comparable): boolean {
  return hasPositiveSalePrice(comp) && hasComparableSource(comp) && hasIsoSaleDate(comp)
}

