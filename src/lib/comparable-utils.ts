/**
 * Computes price per square metre from sale price and habitable area.
 * Returns null if habM2 is null, zero, or negative.
 */
export function computePricePerM2(salePrice: number, habM2: number | null): number | null {
  if (!habM2 || habM2 <= 0) return null
  return Math.round(salePrice / habM2)
}

/**
 * Formats a price-per-m² value as a localized string with the $/m² suffix.
 */
export function formatPricePerM2(perM2: number): string {
  return `${new Intl.NumberFormat('fr-CA', { maximumFractionDigits: 0 }).format(perM2)} $/m²`
}
