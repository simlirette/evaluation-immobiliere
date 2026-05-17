import type { Adjustment } from '@/types'

export type NetMagnitude = 'faible' | 'modéré' | 'fort'

export interface NetMagnitudeEntry {
  id: string
  comparableLabel: string
  netAdjPct: number
  magnitude: NetMagnitude
}

export interface AdjustmentNetMagnitudeProfile {
  entries: NetMagnitudeEntry[]
  countFaible: number
  countModéré: number
  countFort: number
}

function magnitudeLabel(pct: number): NetMagnitude {
  return pct < 5 ? 'faible' : pct <= 15 ? 'modéré' : 'fort'
}

export function computeAdjustmentNetMagnitudeProfile(adjs: Adjustment[]): AdjustmentNetMagnitudeProfile | null {
  if (adjs.length === 0) return null

  const entries: NetMagnitudeEntry[] = adjs.map(a => {
    const netAdjPct = (Math.abs(a.adjusted - a.salePrice) / a.salePrice) * 100
    return { id: a.id, comparableLabel: a.comparableLabel, netAdjPct, magnitude: magnitudeLabel(netAdjPct) }
  })

  return {
    entries,
    countFaible: entries.filter(e => e.magnitude === 'faible').length,
    countModéré: entries.filter(e => e.magnitude === 'modéré').length,
    countFort: entries.filter(e => e.magnitude === 'fort').length,
  }
}
