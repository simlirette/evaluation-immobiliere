import type { Adjustment } from '@/types'

export interface ValueRangeConfidence {
  /** Mean of adjusted prices */
  mean: number
  /** Median of adjusted prices */
  median: number
  /** ±1 standard deviation band */
  band1Sigma: { low: number; high: number }
  /** ±1.5 standard deviation band */
  band15Sigma: { low: number; high: number }
  /** Conclusion's distance from mean as % */
  deviationFromMeanPct: number
  /** 'haute' within ±1σ, 'modérée' within ±1.5σ, 'faible' outside */
  conclusionConfidence: 'haute' | 'modérée' | 'faible'
  /** Whether conclusion is within the min–max range of adjusted prices */
  withinRange: boolean
}

/**
 * Computes value range confidence bands (±1σ, ±1.5σ) and assesses
 * where a proposed conclusion falls within the adjusted price distribution.
 *
 * Returns null when fewer than 2 adjustments or conclusion ≤ 0.
 */
export function computeValueRangeConfidence(
  adjs: Adjustment[],
  conclusion: number,
): ValueRangeConfidence | null {
  if (adjs.length < 2 || conclusion <= 0) return null

  const prices = adjs.map(a => a.adjusted)
  const n = prices.length
  const mean = Math.round(prices.reduce((s, v) => s + v, 0) / n)
  const sorted = [...prices].sort((a, b) => a - b)
  const median = n % 2 === 0
    ? Math.round((sorted[n / 2 - 1] + sorted[n / 2]) / 2)
    : sorted[Math.floor(n / 2)]
  const variance = prices.reduce((s, v) => s + (v - mean) ** 2, 0) / n
  const sigma = Math.round(Math.sqrt(variance))

  const band1Sigma = { low: Math.round(mean - sigma), high: Math.round(mean + sigma) }
  const band15Sigma = { low: Math.round(mean - sigma * 1.5), high: Math.round(mean + sigma * 1.5) }

  const deviationFromMeanPct = mean > 0 ? Math.round(((conclusion - mean) / mean) * 1000) / 10 : 0

  const withinRange = conclusion >= sorted[0] && conclusion <= sorted[n - 1]

  const within1Sigma = conclusion >= band1Sigma.low && conclusion <= band1Sigma.high
  const within15Sigma = conclusion >= band15Sigma.low && conclusion <= band15Sigma.high

  const conclusionConfidence: ValueRangeConfidence['conclusionConfidence'] =
    within1Sigma ? 'haute' : within15Sigma ? 'modérée' : 'faible'

  return { mean, median, band1Sigma, band15Sigma, deviationFromMeanPct, conclusionConfidence, withinRange }
}
