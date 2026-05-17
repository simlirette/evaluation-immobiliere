export interface ListPriceRatio {
  /** salePrice / listPrice × 100 */
  ratioPct: number
  /** salePrice - listPrice */
  delta: number
  /** 'prime' ratio > 100%, 'équilibré' 97-100%, 'escompte' < 97% */
  regime: 'prime' | 'équilibré' | 'escompte'
  /** Human-readable signal */
  signal: string
}

/**
 * Computes the list-price-to-sale-price ratio.
 *
 * Returns null when listPrice ≤ 0 or salePrice ≤ 0.
 */
export function computeListPriceRatio(
  salePrice: number,
  listPrice: number,
): ListPriceRatio | null {
  if (salePrice <= 0 || listPrice <= 0) return null

  const ratioPct = Math.round((salePrice / listPrice) * 10000) / 100
  const delta = salePrice - listPrice

  const regime: ListPriceRatio['regime'] =
    ratioPct > 100 ? 'prime' : ratioPct >= 97 ? 'équilibré' : 'escompte'

  const signal =
    regime === 'prime'
      ? `Vente au-dessus du prix demandé (+${(ratioPct - 100).toFixed(1)} %) — marché de vendeurs`
      : regime === 'équilibré'
      ? `Vente proche du prix demandé (${(ratioPct - 100).toFixed(1)} %) — marché équilibré`
      : `Vente sous le prix demandé (${(ratioPct - 100).toFixed(1)} %) — négociation significative`

  return { ratioPct, delta, regime, signal }
}
