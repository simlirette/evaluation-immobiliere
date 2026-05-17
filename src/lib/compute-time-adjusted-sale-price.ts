/**
 * Computes the time-adjusted sale price for a single comparable,
 * applying the implied monthly appreciation rate to bring the price
 * to a reference date (default: today).
 *
 * Uses linear interpolation (not compounding) — standard for short-period
 * appraisal time adjustments (≤ 24 months).
 * Returns null when saleDate is missing, salePrice ≤ 0, or monthsElapsed ≤ 0.
 */
export function computeTimeAdjustedSalePrice(
  saleDate: string,
  salePrice: number,
  monthlyRatePct: number,
  refDate?: Date,
): { adjustedPrice: number; monthsElapsed: number; adjustmentPct: number } | null {
  if (!saleDate || salePrice <= 0) return null

  const ref = refDate ?? new Date()
  const [ry, rm, rd] = [ref.getFullYear(), ref.getMonth() + 1, ref.getDate()]
  const parts = saleDate.split('-').map(Number)
  const [by, bm, bd] = parts

  const monthsElapsed = (ry - by) * 12 + (rm - bm) + (rd - bd) / 30
  if (monthsElapsed <= 0) return null

  const adjustedPrice = Math.round(salePrice * (1 + (monthlyRatePct / 100) * monthsElapsed))
  const adjustmentPct = Math.round(((adjustedPrice - salePrice) / salePrice) * 1000) / 10

  return {
    adjustedPrice,
    monthsElapsed: Math.round(monthsElapsed * 10) / 10,
    adjustmentPct,
  }
}
