import { describe, it, expect } from 'vitest'
import { computeOEAQComplianceSummary } from './compute-oeaq-compliance-summary'
import type { OEAQCheck } from './build-oeaq-checklist'
import type { GrossAdjustmentCeilingReport } from './compute-gross-adjustment-ceiling'
import type { AdjustmentBracketAnalysis } from './compute-adjustment-bracket-analysis'
import type { AdjustmentSymmetryResult } from './compute-adjustment-symmetry'

function mkCheck(id: string, pass: boolean): OEAQCheck {
  return { id, rule: `Rule ${id}`, pass, message: null }
}

const allPass: OEAQCheck[] = [mkCheck('a', true), mkCheck('b', true), mkCheck('c', true)]
const mixed: OEAQCheck[] = [mkCheck('a', true), mkCheck('b', false), mkCheck('c', true)]

const passCeiling: GrossAdjustmentCeilingReport = { entries: [], violationCount: 0, compliant: true, avgTotalGrossPct: 5 }
const failCeiling: GrossAdjustmentCeilingReport = { entries: [], violationCount: 1, compliant: false, avgTotalGrossPct: 30 }

const passBracket = { hasBelow: true, hasAbove: true, isBracketed: true, entries: [], nearestBelow: null, nearestAbove: null } as AdjustmentBracketAnalysis
const failBracket = { hasBelow: false, hasAbove: true, isBracketed: false, entries: [], nearestBelow: null, nearestAbove: null } as AdjustmentBracketAnalysis

const passSymmetry = { surface: { mean: 0, stdDev: 0, cv: 0, symmetric: true }, year: { mean: 0, stdDev: 0, cv: 0, symmetric: true }, condition: { mean: 0, stdDev: 0, cv: 0, symmetric: true }, garage: { mean: 0, stdDev: 0, cv: 0, symmetric: true }, asymmetricCount: 0, overallSymmetric: true } as AdjustmentSymmetryResult

describe('computeOEAQComplianceSummary', () => {
  it('returns null for empty checklist', () => {
    expect(computeOEAQComplianceSummary([], null, null, null)).toBeNull()
  })

  it('passCount and failCount sum to total checks', () => {
    const r = computeOEAQComplianceSummary(mixed, null, null, null)!
    expect(r.passCount + r.failCount).toBe(mixed.length)
  })

  it('score 100 when all pass', () => {
    expect(computeOEAQComplianceSummary(allPass, null, null, null)!.score).toBe(100)
  })

  it('score 0 when all fail', () => {
    const allFail = [mkCheck('a', false), mkCheck('b', false)]
    expect(computeOEAQComplianceSummary(allFail, null, null, null)!.score).toBe(0)
  })

  it('grade conforme when score >= 80', () => {
    expect(computeOEAQComplianceSummary(allPass, null, null, null)!.grade).toBe('conforme')
  })

  it('grade non conforme when score < 50', () => {
    const mostFail = [mkCheck('a', false), mkCheck('b', false), mkCheck('c', false), mkCheck('d', true)]
    expect(computeOEAQComplianceSummary(mostFail, null, null, null)!.grade).toBe('non conforme')
  })

  it('incorporates ceiling report as extra check', () => {
    // 3 pass + failCeiling → 3/4 = 75% → attention
    const r = computeOEAQComplianceSummary(allPass, failCeiling, null, null)!
    expect(r.failCount).toBe(1)
    expect(r.score).toBe(75)
  })

  it('incorporates bracket result as extra check', () => {
    // 3 pass + failBracket → 3/4 = 75%
    const r = computeOEAQComplianceSummary(allPass, null, failBracket, null)!
    expect(r.failCount).toBe(1)
  })

  it('incorporates symmetry as extra check', () => {
    // 3 pass + passCeiling + passBracket + passSymmetry → 6/6 = 100
    const r = computeOEAQComplianceSummary(allPass, passCeiling, passBracket, passSymmetry)!
    expect(r.score).toBe(100)
    expect(r.failCount).toBe(0)
  })
})
