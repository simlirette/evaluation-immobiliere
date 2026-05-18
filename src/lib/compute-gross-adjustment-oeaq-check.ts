import type { Adjustment } from '@/types'

export interface GrossAdjustmentOEAQEntry {
  id: string
  comparableLabel: string
  grossPct: number
  violation: boolean
}

export interface GrossAdjustmentOEAQCheck {
  entries: GrossAdjustmentOEAQEntry[]
  violationCount: number
  compliant: boolean
}

export function computeGrossAdjustmentOEAQCheck(adjs: Adjustment[]): GrossAdjustmentOEAQCheck | null {
  if (adjs.length === 0) return null

  const entries: GrossAdjustmentOEAQEntry[] = adjs.map(a => {
    const gross = Math.abs(a.surface_adj) + Math.abs(a.year_adj) + Math.abs(a.condition_adj) + Math.abs(a.garage_adj)
    const grossPct = (gross / a.salePrice) * 100
    return { id: a.id, comparableLabel: a.comparableLabel, grossPct, violation: grossPct > 25 }
  })

  const violationCount = entries.filter(e => e.violation).length

  return { entries, violationCount, compliant: violationCount === 0 }
}
