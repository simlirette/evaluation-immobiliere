/**
 * @display-only — T2.2 CALCULS-SOURCE-OF-TRUTH.md
 * Ce calcul est pour l'affichage interactif uniquement.
 * La valeur finale du rapport provient du moteur Python (engine/valuation.py).
 * Ne pas utiliser ce résultat pour un rapport certifiable.
 */
import type { Adjustment } from '@/types'

export interface AdjustedPriceRangeNarrowing {
  rawRange: number
  adjustedRange: number
  narrowingPct: number
  narrowed: boolean
}

export function computeAdjustedPriceRangeNarrowing(adjs: Adjustment[]): AdjustedPriceRangeNarrowing | null {
  if (adjs.length < 2) return null

  const salePrices = adjs.map(a => a.salePrice)
  const adjustedPrices = adjs.map(a => a.adjusted)

  const rawRange = Math.max(...salePrices) - Math.min(...salePrices)
  const adjustedRange = Math.max(...adjustedPrices) - Math.min(...adjustedPrices)

  if (rawRange === 0) return null

  const narrowingPct = ((rawRange - adjustedRange) / rawRange) * 100

  return { rawRange, adjustedRange, narrowingPct, narrowed: adjustedRange < rawRange }
}
