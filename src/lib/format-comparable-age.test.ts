import { describe, it, expect } from 'vitest'
import { formatComparableAge } from './format-comparable-age'

describe('formatComparableAge', () => {
  it('0 months → "ce mois-ci"', () => {
    expect(formatComparableAge(0)).toBe('ce mois-ci')
  })

  it('negative months → "ce mois-ci"', () => {
    expect(formatComparableAge(-3)).toBe('ce mois-ci')
  })

  it('1 month → "1 mois"', () => {
    expect(formatComparableAge(1)).toBe('1 mois')
  })

  it('11 months → "11 mois"', () => {
    expect(formatComparableAge(11)).toBe('11 mois')
  })

  it('12 months → "1 an"', () => {
    expect(formatComparableAge(12)).toBe('1 an')
  })

  it('13 months → "1 an 1 mois"', () => {
    expect(formatComparableAge(13)).toBe('1 an 1 mois')
  })

  it('23 months → "1 an 11 mois"', () => {
    expect(formatComparableAge(23)).toBe('1 an 11 mois')
  })

  it('24 months → "2 ans"', () => {
    expect(formatComparableAge(24)).toBe('2 ans')
  })

  it('36 months → "3 ans"', () => {
    expect(formatComparableAge(36)).toBe('3 ans')
  })

  it('37 months → "3 ans 1 mois"', () => {
    expect(formatComparableAge(37)).toBe('3 ans 1 mois')
  })
})
