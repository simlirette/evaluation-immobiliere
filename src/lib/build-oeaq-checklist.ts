import type { Comparable, Adjustment } from '@/types'
import { checkComparableMinimum } from './check-comparable-minimum'
import { validateComparableDate } from './validate-comparable-date'
import { computeNetAdjustment } from './compute-net-adjustment'
import { computeGrossAdjustment } from './compute-gross-adjustment'
import { hasIsoSaleDate, isUsableComparable } from './comparable-validity'
import { isUsableAdjustment } from './compute-reconciled-value'

export interface OEAQCheck {
  id: string
  rule: string
  pass: boolean
  message: string | null
}

/**
 * Aggregates all OEAQ compliance checks into a unified checklist.
 * Each check is advisory: the evaluator retains professional judgment.
 */
export function buildOEAQChecklist(
  comps: Comparable[],
  adjustments: Adjustment[],
  today: Date = new Date()
): OEAQCheck[] {
  const checks: OEAQCheck[] = []

  const minCheck = checkComparableMinimum(comps)
  checks.push({
    id: 'min-comparables',
    rule: 'Nombre minimal de comparables (>= 3)',
    pass: minCheck.pass,
    message: minCheck.warning,
  })

  const invalidComps = comps.filter(c => !isUsableComparable(c))
  checks.push({
    id: 'comparable-inputs',
    rule: 'Prix, date et source des comparables',
    pass: invalidComps.length === 0,
    message: invalidComps.length > 0
      ? `${invalidComps.length} comparable${invalidComps.length > 1 ? 's' : ''} sans prix positif, date ISO ou source_id - correction requise avant certification.`
      : null,
  })

  const staleComps = comps.filter(c => hasIsoSaleDate(c) && validateComparableDate(c.sale_date, today).stale)
  checks.push({
    id: 'stale-dates',
    rule: 'Récence des ventes (<= 36 mois)',
    pass: staleComps.length === 0,
    message: staleComps.length > 0
      ? `${staleComps.length} vente${staleComps.length > 1 ? 's' : ''} de plus de 36 mois - justification requise (OEAQ).`
      : null,
  })

  const usableAdjustments = adjustments.filter(isUsableAdjustment)
  const invalidAdjustments = adjustments.filter(a => !isUsableAdjustment(a))
  checks.push({
    id: 'adjustment-inputs',
    rule: 'Prix ajustes exploitables',
    pass: invalidAdjustments.length === 0,
    message: invalidAdjustments.length > 0
      ? `${invalidAdjustments.length} ajustement${invalidAdjustments.length > 1 ? 's' : ''} sans prix de vente ou valeur ajustee positive.`
      : null,
  })

  const largeAdjs = usableAdjustments.filter(a => computeNetAdjustment(a).absPct > 25)
  checks.push({
    id: 'adjustment-magnitude',
    rule: 'Amplitude des ajustements nets (<= 25 %)',
    pass: largeAdjs.length === 0,
    message: largeAdjs.length > 0
      ? `${largeAdjs.length} comparable${largeAdjs.length > 1 ? 's' : ''} avec ajustement net > 25 % - fiabilite reduite.`
      : null,
  })

  const largeGrossAdjs = usableAdjustments.filter(a => computeGrossAdjustment(a).grossPct > 40)
  checks.push({
    id: 'gross-adjustment',
    rule: 'Amplitude des ajustements bruts (<= 40 %)',
    pass: largeGrossAdjs.length === 0,
    message: largeGrossAdjs.length > 0
      ? `${largeGrossAdjs.length} comparable${largeGrossAdjs.length > 1 ? 's' : ''} avec ajustement brut > 40 % - justification requise (OEAQ).`
      : null,
  })

  return checks
}
