import type { Adjustment } from '@/types'

export interface AdjustmentExplainedVariance {
  saleVariance: number
  adjustedVariance: number
  varianceReductionPct: number
  interpretation: 'forte' | 'modérée' | 'faible' | 'aucune'
}

function variance(values: number[]): number {
  const mean = values.reduce((s, v) => s + v, 0) / values.length
  return values.reduce((s, v) => s + (v - mean) ** 2, 0) / values.length
}

export function computeAdjustmentExplainedVariance(adjs: Adjustment[]): AdjustmentExplainedVariance | null {
  if (adjs.length < 2) return null

  const saleVariance = variance(adjs.map(a => a.salePrice))
  const adjustedVariance = variance(adjs.map(a => a.adjusted))

  if (saleVariance === 0) return null

  const varianceReductionPct = ((saleVariance - adjustedVariance) / saleVariance) * 100

  const interpretation: AdjustmentExplainedVariance['interpretation'] =
    varianceReductionPct >= 50 ? 'forte'
    : varianceReductionPct >= 20 ? 'modérée'
    : varianceReductionPct > 0 ? 'faible'
    : 'aucune'

  return { saleVariance, adjustedVariance, varianceReductionPct, interpretation }
}
