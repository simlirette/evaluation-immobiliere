import type { Adjustment } from '@/types'

export type YearImpactDirection = 'positive' | 'negative' | 'neutral'

export interface AdjustmentYearImpactSummary {
  totalImpact: number
  avgPerComp: number
  maxAbsId: string
  maxAbsValue: number
  dominantDirection: YearImpactDirection
}

export function computeAdjustmentYearImpactSummary(adjs: Adjustment[]): AdjustmentYearImpactSummary | null {
  if (adjs.length === 0) return null

  const totalImpact = adjs.reduce((s, a) => s + a.year_adj, 0)
  const avgPerComp = totalImpact / adjs.length

  const maxEntry = adjs.reduce(
    (best, a) => Math.abs(a.year_adj) > Math.abs(best.year_adj) ? a : best,
    adjs[0],
  )

  let dominantDirection: YearImpactDirection
  const positiveCount = adjs.filter(a => a.year_adj > 0).length
  const negativeCount = adjs.filter(a => a.year_adj < 0).length
  const zeroCount = adjs.filter(a => a.year_adj === 0).length

  if (positiveCount > negativeCount && positiveCount > zeroCount) dominantDirection = 'positive'
  else if (negativeCount > zeroCount) dominantDirection = 'negative'
  else dominantDirection = 'neutral'

  return {
    totalImpact,
    avgPerComp,
    maxAbsId: maxEntry.id,
    maxAbsValue: maxEntry.year_adj,
    dominantDirection,
  }
}
