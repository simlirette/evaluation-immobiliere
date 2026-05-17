import type { AdjustmentBracketAnalysis } from './compute-adjustment-bracket-analysis'
import type { ComparableSizeRange } from './compute-comparable-size-range'
import type { ReconciledValueBracket } from './compute-reconciled-value-bracket'

export interface OEAQBracketingSummary {
  /** Adjusted prices bracket the subject value (from AdjustmentBracketAnalysis) — null when check unavailable */
  pricesBracketed: boolean | null
  /** Subject hab_m² is within the comp size range (from ComparableSizeRange) — null when check unavailable */
  sizeBracketed: boolean | null
  /** Reconciled value falls within adjusted price range (from ReconciledValueBracket) — null when check unavailable */
  reconciledBracketed: boolean | null
  /** True only when all available checks pass */
  allBracketed: boolean
  /** Number of checks that were available (non-null inputs) */
  availableChecks: number
  /** Number of checks that passed */
  passCount: number
  /** Names of checks that failed */
  failedChecks: string[]
}

/**
 * Aggregates the three OEAQ bracketing requirements into a single summary.
 * Returns null when all three inputs are null (no bracketing data available).
 */
export function computeOEAQBracketingSummary(
  pricesBracket: AdjustmentBracketAnalysis | null,
  sizeRange: ComparableSizeRange | null,
  reconciledBracket: ReconciledValueBracket | null,
): OEAQBracketingSummary | null {
  if (!pricesBracket && !sizeRange && !reconciledBracket) return null

  const pricesBracketed = pricesBracket ? pricesBracket.isBracketed : null
  const sizeBracketed = sizeRange ? sizeRange.bracketed : null
  const reconciledBracketed = reconciledBracket ? reconciledBracket.bracketed : null

  const checks: Array<{ name: string; result: boolean | null }> = [
    { name: 'Prix (encadrement comparables)', result: pricesBracketed },
    { name: 'Surface (encadrement dimensionnel)', result: sizeBracketed },
    { name: 'Valeur réconciliée (dans la fourchette)', result: reconciledBracketed },
  ]

  const available = checks.filter(c => c.result !== null)
  const failed = available.filter(c => c.result === false)
  const passed = available.filter(c => c.result === true)

  return {
    pricesBracketed,
    sizeBracketed,
    reconciledBracketed,
    allBracketed: available.length > 0 && failed.length === 0,
    availableChecks: available.length,
    passCount: passed.length,
    failedChecks: failed.map(c => c.name),
  }
}
