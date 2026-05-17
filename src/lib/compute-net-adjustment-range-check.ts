import type { Adjustment } from '@/types'

export interface NetAdjustmentRangeEntry {
  id: string
  comparableLabel: string
  netAdj: number
  netAdjPct: number
  violation: boolean
}

export interface NetAdjustmentRangeCheck {
  entries: NetAdjustmentRangeEntry[]
  violationCount: number
  compliant: boolean
}

const NET_THRESHOLD = 15 // percent

export function computeNetAdjustmentRangeCheck(adjs: Adjustment[]): NetAdjustmentRangeCheck | null {
  if (adjs.length === 0) return null

  const entries: NetAdjustmentRangeEntry[] = adjs.map(a => {
    const netAdj = a.adjusted - a.salePrice
    const netAdjPct = (Math.abs(netAdj) / a.salePrice) * 100
    return {
      id: a.id,
      comparableLabel: a.comparableLabel,
      netAdj,
      netAdjPct,
      violation: netAdjPct > NET_THRESHOLD,
    }
  })

  const violationCount = entries.filter(e => e.violation).length
  return { entries, violationCount, compliant: violationCount === 0 }
}
