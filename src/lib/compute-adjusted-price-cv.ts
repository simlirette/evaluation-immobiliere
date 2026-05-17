import type { Adjustment } from '@/types'

export interface AdjustedPriceCV {
  rawCV: number
  adjustedCV: number
  delta: number
  homogenized: boolean
}

function cv(values: number[]): number {
  const mean = values.reduce((s, v) => s + v, 0) / values.length
  const variance = values.reduce((s, v) => s + (v - mean) ** 2, 0) / values.length
  return (Math.sqrt(variance) / mean) * 100
}

export function computeAdjustedPriceCV(adjs: Adjustment[]): AdjustedPriceCV | null {
  if (adjs.length < 2) return null

  const rawCV = cv(adjs.map(a => a.salePrice))
  const adjustedCV = cv(adjs.map(a => a.adjusted))
  const delta = adjustedCV - rawCV

  return { rawCV, adjustedCV, delta, homogenized: adjustedCV < rawCV }
}
