import type { Comparable } from '@/types'
import { isUsableComparable } from './comparable-validity'

const OEAQ_MINIMUM = 3

export interface ComparableMinimumCheck {
  pass: boolean
  count: number
  warning: string | null
}

/**
 * Verifies that the comparable set meets the OEAQ minimum count requirement
 * for the comparative approach (typically 3 comparable sales).
 */
export function checkComparableMinimum(comps: Comparable[]): ComparableMinimumCheck {
  const count = comps.filter(isUsableComparable).length
  const pass = count >= OEAQ_MINIMUM
  return {
    pass,
    count,
    warning: pass
      ? null
      : count === 0
        ? `Aucun comparable exploitable. L'approche comparative exige au minimum ${OEAQ_MINIMUM} ventes avec prix, date et source (OEAQ).`
        : `${count} comparable${count > 1 ? 's' : ''} exploitable${count > 1 ? 's' : ''} - minimum ${OEAQ_MINIMUM} requis par l'OEAQ pour l'approche comparative.`,
  }
}
