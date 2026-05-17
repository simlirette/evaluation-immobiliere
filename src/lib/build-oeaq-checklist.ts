import type { Comparable, Adjustment } from '@/types'
import { checkComparableMinimum } from './check-comparable-minimum'
import { validateComparableDate } from './validate-comparable-date'
import { computeNetAdjustment } from './compute-net-adjustment'
import { computeGrossAdjustment } from './compute-gross-adjustment'

export interface OEAQCheck {
  id: string
  rule: string
  pass: boolean
  message: string | null
}

/**
 * Aggregates all OEAQ compliance checks into a unified checklist.
 * Each check is advisory — the evaluator retains professional judgment.
 */
export function buildOEAQChecklist(
  comps: Comparable[],
  adjustments: Adjustment[],
  today: Date = new Date()
): OEAQCheck[] {
  const checks: OEAQCheck[] = []

  // 1. Minimum comparable count
  const minCheck = checkComparableMinimum(comps)
  checks.push({
    id: 'min-comparables',
    rule: 'Nombre minimal de comparables (≥ 3)',
    pass: minCheck.pass,
    message: minCheck.warning,
  })

  // 2. Stale comparable dates (> 36 months)
  const staleComps = comps.filter(c => validateComparableDate(c.sale_date, today).stale)
  checks.push({
    id: 'stale-dates',
    rule: 'Récence des ventes (≤ 36 mois)',
    pass: staleComps.length === 0,
    message: staleComps.length > 0
      ? `${staleComps.length} vente${staleComps.length > 1 ? 's' : ''} de plus de 36 mois — justification requise (OEAQ).`
      : null,
  })

  // 3. Net adjustment magnitude (> 25% = reliability concern)
  const largeAdjs = adjustments.filter(a => computeNetAdjustment(a).absPct > 25)
  checks.push({
    id: 'adjustment-magnitude',
    rule: 'Amplitude des ajustements nets (≤ 25 %)',
    pass: largeAdjs.length === 0,
    message: largeAdjs.length > 0
      ? `${largeAdjs.length} comparable${largeAdjs.length > 1 ? 's' : ''} avec ajustement net > 25 % — fiabilité réduite.`
      : null,
  })

  // 4. Gross adjustment magnitude (> 40% = reliability concern)
  const largeGrossAdjs = adjustments.filter(a => computeGrossAdjustment(a).grossPct > 40)
  checks.push({
    id: 'gross-adjustment',
    rule: 'Amplitude des ajustements bruts (≤ 40 %)',
    pass: largeGrossAdjs.length === 0,
    message: largeGrossAdjs.length > 0
      ? `${largeGrossAdjs.length} comparable${largeGrossAdjs.length > 1 ? 's' : ''} avec ajustement brut > 40 % — justification requise (OEAQ).`
      : null,
  })

  return checks
}
