import type { Comparable } from '@/types'
import { computePricePerM2 } from './comparable-utils'

function csvCell(value: string | number | null | undefined): string {
  if (value == null) return ''
  const str = String(value)
  // Wrap in quotes if contains comma, quote, or newline
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return `"${str.replace(/"/g, '""')}"`
  }
  return str
}

/**
 * Builds a UTF-8 CSV string from a set of comparables.
 * Columns: rank, address, sale_price, sale_date, hab_m2, terrain_m2, year_built, price_per_m2
 */
export function buildComparablesCsv(comps: Comparable[]): string {
  const headers = ['#', 'Adresse', 'Prix de vente ($)', 'Date de vente', 'Surface hab. (m²)', 'Terrain (m²)', 'Année construction', 'Prix/m² ($)']
  const rows = comps.map(c => {
    const perM2 = computePricePerM2(c.sale_price, c.hab_m2)
    return [
      csvCell(c.rank),
      csvCell(c.address),
      csvCell(c.sale_price),
      csvCell(c.sale_date),
      csvCell(c.hab_m2),
      csvCell(c.terrain_m2),
      csvCell(c.year_built),
      csvCell(perM2 != null ? Math.round(perM2) : null),
    ].join(',')
  })
  return [headers.join(','), ...rows].join('\n')
}
