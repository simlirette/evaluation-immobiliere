import type { Comparable } from '@/types'

export interface PriceAnomalyEntry {
  id: string
  comparableLabel: string
  actualPricePerM2: number
  panelMedianPricePerM2: number
  deviationPct: number
  isAnomaly: boolean
}

export interface ComparablePriceAnomaly {
  entries: PriceAnomalyEntry[]
  anomalyIds: string[]
  panelMedianPricePerM2: number
}

const ANOMALY_THRESHOLD = 25 // percent

export function computeComparablePriceAnomaly(comps: Comparable[]): ComparablePriceAnomaly | null {
  const valid = comps.filter(c => c.hab_m2 != null && c.hab_m2 > 0)
  if (valid.length < 2) return null

  const ppm2s = valid.map(c => c.sale_price / c.hab_m2!)
  const sorted = [...ppm2s].sort((a, b) => a - b)
  const n = sorted.length
  const panelMedianPricePerM2 = n % 2 === 1
    ? sorted[Math.floor(n / 2)]
    : (sorted[n / 2 - 1] + sorted[n / 2]) / 2

  const entries: PriceAnomalyEntry[] = valid.map((c, i) => {
    const actualPricePerM2 = ppm2s[i]
    const deviationPct = Math.abs(actualPricePerM2 - panelMedianPricePerM2) / panelMedianPricePerM2 * 100
    return {
      id: c.id,
      comparableLabel: c.address || c.rank,
      actualPricePerM2,
      panelMedianPricePerM2,
      deviationPct,
      isAnomaly: deviationPct > ANOMALY_THRESHOLD,
    }
  })

  return { entries, anomalyIds: entries.filter(e => e.isAnomaly).map(e => e.id), panelMedianPricePerM2 }
}
