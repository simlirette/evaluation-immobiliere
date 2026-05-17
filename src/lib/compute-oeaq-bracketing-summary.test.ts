import { describe, it, expect } from 'vitest'
import { computeOEAQBracketingSummary } from './compute-oeaq-bracketing-summary'
import type { AdjustmentBracketAnalysis } from './compute-adjustment-bracket-analysis'
import type { ComparableSizeRange } from './compute-comparable-size-range'
import type { ReconciledValueBracket } from './compute-reconciled-value-bracket'

const passPrices: AdjustmentBracketAnalysis = { hasBelow: true, hasAbove: true, isBracketed: true, entries: [], nearestBelow: null, nearestAbove: null }
const failPrices: AdjustmentBracketAnalysis = { hasBelow: false, hasAbove: true, isBracketed: false, entries: [], nearestBelow: null, nearestAbove: null }

const passSize: ComparableSizeRange = { min: 80, max: 120, subjectHabM2: 100, bracketed: true, nearestBelow: null, nearestAbove: null, missingCount: 0 }
const failSize: ComparableSizeRange = { min: 110, max: 130, subjectHabM2: 100, bracketed: false, nearestBelow: null, nearestAbove: null, missingCount: 0 }

const passReconciled: ReconciledValueBracket = { min: 380000, max: 420000, reconciledValue: 400000, bracketed: true, deviationPct: 0 }
const failReconciled: ReconciledValueBracket = { min: 380000, max: 420000, reconciledValue: 500000, bracketed: false, deviationPct: 19 }

describe('computeOEAQBracketingSummary', () => {
  it('returns null when all inputs are null', () => {
    expect(computeOEAQBracketingSummary(null, null, null)).toBeNull()
  })

  it('allBracketed true when all available checks pass', () => {
    const r = computeOEAQBracketingSummary(passPrices, passSize, passReconciled)!
    expect(r.allBracketed).toBe(true)
    expect(r.failedChecks).toHaveLength(0)
  })

  it('allBracketed false when any check fails', () => {
    expect(computeOEAQBracketingSummary(failPrices, passSize, passReconciled)!.allBracketed).toBe(false)
  })

  it('availableChecks counts non-null inputs', () => {
    expect(computeOEAQBracketingSummary(passPrices, null, passReconciled)!.availableChecks).toBe(2)
    expect(computeOEAQBracketingSummary(passPrices, passSize, passReconciled)!.availableChecks).toBe(3)
  })

  it('passCount equals passing checks', () => {
    const r = computeOEAQBracketingSummary(passPrices, failSize, passReconciled)!
    expect(r.passCount).toBe(2)
  })

  it('failedChecks contains names of failed checks', () => {
    const r = computeOEAQBracketingSummary(failPrices, failSize, passReconciled)!
    expect(r.failedChecks).toHaveLength(2)
    expect(r.failedChecks.some(s => s.toLowerCase().includes('prix'))).toBe(true)
  })

  it('pricesBracketed null when pricesBracket input is null', () => {
    expect(computeOEAQBracketingSummary(null, passSize, passReconciled)!.pricesBracketed).toBeNull()
  })

  it('allBracketed true when only one check available and it passes', () => {
    expect(computeOEAQBracketingSummary(passPrices, null, null)!.allBracketed).toBe(true)
  })

  it('allBracketed false when only one check available and it fails', () => {
    expect(computeOEAQBracketingSummary(failPrices, null, null)!.allBracketed).toBe(false)
  })
})
