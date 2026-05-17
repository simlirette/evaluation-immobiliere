import type { Adjustment } from '@/types'
import { computeNetAdjustment } from './compute-net-adjustment'
import { computeGrossAdjustment } from './compute-gross-adjustment'

function csvCell(value: string | number | null | undefined): string {
  if (value == null) return ''
  const str = String(value)
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return `"${str.replace(/"/g, '""')}"`
  }
  return str
}

function round1(n: number): number { return Math.round(n * 10) / 10 }

/**
 * Builds a UTF-8 CSV string from a set of adjustments.
 * Columns: label, salePrice, surface_adj, year_adj, condition_adj, garage_adj,
 *          net_adj_amt, net_adj_pct, gross_adj_pct, adjusted
 */
export function buildAdjustmentsCsv(adjs: Adjustment[]): string {
  const headers = [
    'Comparable', 'Prix vente ($)',
    'Adj. surface ($)', 'Adj. année ($)', 'Adj. condition ($)', 'Adj. garage ($)',
    'Net adj. ($)', 'Net adj. (%)', 'Brut adj. (%)', 'Prix ajusté ($)',
  ]
  const rows = adjs.map(a => {
    const { net, netPct } = computeNetAdjustment(a)
    const { grossPct } = computeGrossAdjustment(a)
    return [
      csvCell(a.comparableLabel),
      csvCell(a.salePrice),
      csvCell(a.surface_adj),
      csvCell(a.year_adj),
      csvCell(a.condition_adj),
      csvCell(a.garage_adj),
      csvCell(net),
      csvCell(round1(netPct)),
      csvCell(round1(grossPct)),
      csvCell(a.adjusted),
    ].join(',')
  })
  return [headers.join(','), ...rows].join('\n')
}
