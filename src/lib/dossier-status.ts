import type { DossierStatus } from '@/types'

const CYCLE: DossierStatus[] = ['brouillon', 'en-cours', 'complet']

/**
 * Returns the next status in the cycle: brouillon → en-cours → complet → brouillon
 */
export function nextDossierStatus(current: DossierStatus): DossierStatus {
  const i = CYCLE.indexOf(current)
  return CYCLE[(i + 1) % CYCLE.length]
}

/**
 * Returns the previous status in the cycle (for undo-style revert).
 */
export function prevDossierStatus(current: DossierStatus): DossierStatus {
  const i = CYCLE.indexOf(current)
  return CYCLE[(i - 1 + CYCLE.length) % CYCLE.length]
}
