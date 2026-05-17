import type { Comparable } from '@/types'

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
  const count = comps.length
  const pass = count >= OEAQ_MINIMUM
  return {
    pass,
    count,
    warning: pass
      ? null
      : count === 0
        ? `Aucun comparable retenu. L\u2019approche comparative exige au minimum ${OEAQ_MINIMUM} ventes (OEAQ).`
        : `${count} comparable${count > 1 ? 's' : ''} retenu${count > 1 ? 's' : ''} — minimum ${OEAQ_MINIMUM} requis par l\u2019OEAQ pour l\u2019approche comparative.`,
  }
}
