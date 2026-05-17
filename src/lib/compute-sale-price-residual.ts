import type { Adjustment } from '@/types'

export interface SalePriceResidualEntry {
  id: string
  comparableLabel: string
  adjustedPrice: number
  residualAmt: number
  residualPct: number
  large: boolean
}

export interface SalePriceResidual {
  entries: SalePriceResidualEntry[]
  stdDevResidual: number
  largeResidualIds: string[]
}

const LARGE_THRESHOLD = 5 // percent

export function computeSalePriceResidual(adjs: Adjustment[], reconciledValue: number): SalePriceResidual | null {
  if (adjs.length === 0 || reconciledValue <= 0) return null

  const entries: SalePriceResidualEntry[] = adjs.map(a => {
    const residualAmt = Math.abs(a.adjusted - reconciledValue)
    const residualPct = (residualAmt / reconciledValue) * 100
    return { id: a.id, comparableLabel: a.comparableLabel, adjustedPrice: a.adjusted, residualAmt, residualPct, large: residualPct > LARGE_THRESHOLD }
  })

  const mean = entries.reduce((s, e) => s + e.residualPct, 0) / entries.length
  const variance = entries.reduce((s, e) => s + (e.residualPct - mean) ** 2, 0) / entries.length
  const stdDevResidual = Math.sqrt(variance)
  const largeResidualIds = entries.filter(e => e.large).map(e => e.id)

  return { entries, stdDevResidual, largeResidualIds }
}
