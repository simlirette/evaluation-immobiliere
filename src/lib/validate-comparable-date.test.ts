import { describe, it, expect } from 'vitest'
import { validateComparableDate } from './validate-comparable-date'

const TODAY = new Date('2026-05-17')

describe('validateComparableDate', () => {
  it('recent sale (6 months) → not stale', () => {
    const result = validateComparableDate('2025-11-17', TODAY)
    expect(result.stale).toBe(false)
    expect(result.warning).toBeNull()
    expect(result.ageMonths).toBe(6)
  })

  it('sale exactly 36 months → not stale', () => {
    const result = validateComparableDate('2023-05-17', TODAY)
    expect(result.stale).toBe(false)
  })

  it('sale 37 months ago → stale', () => {
    const result = validateComparableDate('2023-04-17', TODAY)
    expect(result.stale).toBe(true)
    expect(result.warning).not.toBeNull()
  })

  it('very old sale → stale with age in warning', () => {
    const result = validateComparableDate('2020-01-01', TODAY)
    expect(result.stale).toBe(true)
    expect(result.warning).toContain('mois')
    expect(result.ageMonths).toBeGreaterThan(36)
  })

  it('warning mentions OEAQ threshold', () => {
    const result = validateComparableDate('2022-01-01', TODAY)
    expect(result.warning).toContain('OEAQ')
    expect(result.warning).toContain('36')
  })

  it('sale today → ageMonths 0, not stale', () => {
    const result = validateComparableDate('2026-05-17', TODAY)
    expect(result.ageMonths).toBe(0)
    expect(result.stale).toBe(false)
  })

  it('returns ageMonths as integer', () => {
    const result = validateComparableDate('2025-05-17', TODAY)
    expect(Number.isInteger(result.ageMonths)).toBe(true)
  })

  it('12-month-old sale → ageMonths ~12, not stale', () => {
    const result = validateComparableDate('2025-05-17', TODAY)
    expect(result.ageMonths).toBe(12)
    expect(result.stale).toBe(false)
  })
})
