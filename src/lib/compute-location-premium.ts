/**
 * Computes how the subject property's reconciled value compares to the
 * local median home value (from census data).
 *
 * Returns null when either input is missing or median is zero.
 */
export interface LocationPremiumResult {
  delta: number
  deltaPct: number
  signal: 'prime' | 'aligné' | 'escompte'
}

export function computeLocationPremium(
  reconciledValue: number,
  medianHomeValue: number,
): LocationPremiumResult | null {
  if (!reconciledValue || !medianHomeValue || medianHomeValue === 0) return null

  const delta = reconciledValue - medianHomeValue
  const deltaPct = Math.round((delta / medianHomeValue) * 1000) / 10

  const signal: LocationPremiumResult['signal'] =
    deltaPct > 10 ? 'prime' : deltaPct < -10 ? 'escompte' : 'aligné'

  return { delta: Math.round(delta), deltaPct, signal }
}
