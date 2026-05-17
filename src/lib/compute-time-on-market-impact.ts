export interface TimeOnMarketImpact {
  /** Days on market */
  daysOnMarket: number
  /** 'rapide' ≤ 30d, 'normal' 31-90d, 'prolongé' 91-180d, 'très prolongé' > 180d */
  category: 'rapide' | 'normal' | 'prolongé' | 'très prolongé'
  /** Estimated value discount % (negative) due to extended time on market */
  estimatedDiscountPct: number
  /** Estimated dollar impact on a given property value */
  estimatedDiscountAmount: number | null
  /** Qualitative signal for appraisal note */
  signal: string
}

/**
 * Estimates the price impact of extended time on market.
 *
 * Based on industry research (CMHC, CREA):
 * - 0-30 days: no discount (active demand)
 * - 31-90 days: -1% (soft market signal)
 * - 91-180 days: -3% (price reduction pressure)
 * - > 180 days: -5% (significant stigma risk)
 *
 * Returns null when daysOnMarket < 0.
 */
export function computeTimeOnMarketImpact(
  daysOnMarket: number,
  propertyValue?: number,
): TimeOnMarketImpact | null {
  if (daysOnMarket < 0) return null

  let category: TimeOnMarketImpact['category']
  let estimatedDiscountPct: number
  let signal: string

  if (daysOnMarket <= 30) {
    category = 'rapide'
    estimatedDiscountPct = 0
    signal = 'Délai de vente rapide — aucune décote de délai applicable'
  } else if (daysOnMarket <= 90) {
    category = 'normal'
    estimatedDiscountPct = -1
    signal = 'Délai normal — légère décote possible (~1 %)'
  } else if (daysOnMarket <= 180) {
    category = 'prolongé'
    estimatedDiscountPct = -3
    signal = 'Délai prolongé — pression sur le prix, décote estimée ~3 %'
  } else {
    category = 'très prolongé'
    estimatedDiscountPct = -5
    signal = 'Délai très prolongé — risque de stigmatisation, décote estimée ~5 %'
  }

  const estimatedDiscountAmount = propertyValue != null && propertyValue > 0
    ? Math.round(propertyValue * estimatedDiscountPct / 100)
    : null

  return { daysOnMarket, category, estimatedDiscountPct, estimatedDiscountAmount, signal }
}
