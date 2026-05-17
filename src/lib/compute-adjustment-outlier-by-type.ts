import type { Adjustment } from '@/types'

export interface AdjustmentTypeOutliers {
  mean: number
  stdDev: number
  /** Ids of comparables where |value − mean| > 2 × stdDev for this type */
  outlierIds: string[]
}

export interface AdjustmentOutlierByType {
  surface: AdjustmentTypeOutliers
  year: AdjustmentTypeOutliers
  condition: AdjustmentTypeOutliers
  garage: AdjustmentTypeOutliers
  /** True when at least one type has at least one outlier */
  hasOutliers: boolean
}

type AdjField = 'surface_adj' | 'year_adj' | 'condition_adj' | 'garage_adj'

const FIELD_MAP: Record<keyof Omit<AdjustmentOutlierByType, 'hasOutliers'>, AdjField> = {
  surface: 'surface_adj',
  year: 'year_adj',
  condition: 'condition_adj',
  garage: 'garage_adj',
}

/**
 * For each adjustment type, identifies comparables whose value for that type
 * deviates more than 2 standard deviations from the per-type mean.
 * Signals inconsistent application of a specific adjustment factor.
 *
 * Returns null when fewer than 3 adjustments.
 */
export function computeAdjustmentOutlierByType(
  adjs: Adjustment[],
): AdjustmentOutlierByType | null {
  if (adjs.length < 3) return null

  function analyzeType(field: AdjField): AdjustmentTypeOutliers {
    const values = adjs.map(a => a[field] as number)
    const mean = values.reduce((s, v) => s + v, 0) / values.length
    const variance = values.reduce((s, v) => s + (v - mean) ** 2, 0) / values.length
    const stdDev = Math.sqrt(variance)

    const outlierIds = stdDev > 0
      ? adjs.filter((a, i) => Math.abs(values[i] - mean) > 2 * stdDev).map(a => a.comparable_id)
      : []

    return {
      mean: Math.round(mean),
      stdDev: Math.round(stdDev),
      outlierIds,
    }
  }

  const types = Object.fromEntries(
    (Object.entries(FIELD_MAP) as [keyof typeof FIELD_MAP, AdjField][]).map(
      ([key, field]) => [key, analyzeType(field)],
    ),
  ) as Omit<AdjustmentOutlierByType, 'hasOutliers'>

  const hasOutliers = Object.values(types).some(t => t.outlierIds.length > 0)

  return { ...types, hasOutliers }
}
