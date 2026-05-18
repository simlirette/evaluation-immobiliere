import type { Adjustment } from '@/types'

export interface NetPctBucket {
  label: string
  min: number | null
  max: number | null
  count: number
}

export interface AdjustmentNetPctHistogram {
  buckets: NetPctBucket[]
}

const BANDS: Array<{ label: string; min: number | null; max: number | null }> = [
  { label: '< −15 %',    min: null,  max: -15 },
  { label: '−15 → −10 %', min: -15,   max: -10 },
  { label: '−10 → −5 %',  min: -10,   max: -5  },
  { label: '−5 → 0 %',    min: -5,    max: 0   },
  { label: '0 → 5 %',     min: 0,     max: 5   },
  { label: '5 → 10 %',    min: 5,     max: 10  },
  { label: '10 → 15 %',   min: 10,    max: 15  },
  { label: '> 15 %',      min: 15,    max: null },
]

function bandFor(pct: number): number {
  for (let i = 0; i < BANDS.length; i++) {
    const { min, max } = BANDS[i]
    const aboveMin = min === null || pct >= min
    const belowMax = max === null || pct < max
    if (aboveMin && belowMax) return i
  }
  return BANDS.length - 1
}

export function computeAdjustmentNetPctHistogram(adjs: Adjustment[]): AdjustmentNetPctHistogram | null {
  if (adjs.length === 0) return null

  const counts = new Array(BANDS.length).fill(0)
  for (const a of adjs) {
    const netPct = ((a.adjusted - a.salePrice) / a.salePrice) * 100
    counts[bandFor(netPct)]++
  }

  const buckets: NetPctBucket[] = BANDS.map((b, i) => ({ ...b, count: counts[i] }))
  return { buckets }
}
