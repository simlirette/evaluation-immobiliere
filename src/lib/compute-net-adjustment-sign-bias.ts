import type { Adjustment } from '@/types'

export type BiasDirection = 'upward' | 'downward' | 'neutral'

export interface NetAdjustmentSignBias {
  countUpward: number
  countDownward: number
  countNeutral: number
  dominantDirection: BiasDirection
  dominancePct: number
  biased: boolean
}

const NEUTRAL_THRESHOLD = 0.01 // 1% of salePrice
const BIAS_THRESHOLD = 70      // percent

export function computeNetAdjustmentSignBias(adjs: Adjustment[]): NetAdjustmentSignBias | null {
  if (adjs.length === 0) return null

  let countUpward = 0
  let countDownward = 0
  let countNeutral = 0

  for (const a of adjs) {
    const netAdj = a.adjusted - a.salePrice
    const netPct = Math.abs(netAdj) / a.salePrice
    if (netPct < NEUTRAL_THRESHOLD) {
      countNeutral++
    } else if (netAdj > 0) {
      countUpward++
    } else {
      countDownward++
    }
  }

  const total = adjs.length
  const upPct = (countUpward / total) * 100
  const downPct = (countDownward / total) * 100
  const neutralPct = (countNeutral / total) * 100

  let dominantDirection: BiasDirection
  let dominancePct: number
  if (countUpward >= countDownward && countUpward >= countNeutral) {
    dominantDirection = 'upward'
    dominancePct = upPct
  } else if (countDownward >= countNeutral) {
    dominantDirection = 'downward'
    dominancePct = downPct
  } else {
    dominantDirection = 'neutral'
    dominancePct = neutralPct
  }

  return { countUpward, countDownward, countNeutral, dominantDirection, dominancePct, biased: dominancePct >= BIAS_THRESHOLD }
}
