import { describe, it, expect } from 'vitest'
import { computePricePerM2, formatPricePerM2 } from './comparable-utils'

describe('computePricePerM2', () => {
  it('normal case', () => {
    expect(computePricePerM2(420000, 120)).toBe(3500)
  })
  it('rounds to integer', () => {
    expect(computePricePerM2(100000, 3)).toBe(33333)
  })
  it('null hab_m2 → null', () => {
    expect(computePricePerM2(420000, null)).toBeNull()
  })
  it('zero hab_m2 → null', () => {
    expect(computePricePerM2(420000, 0)).toBeNull()
  })
  it('negative hab_m2 → null', () => {
    expect(computePricePerM2(420000, -10)).toBeNull()
  })
  it('zero price → 0', () => {
    expect(computePricePerM2(0, 100)).toBe(0)
  })
})

describe('formatPricePerM2', () => {
  it('includes $/m² suffix', () => {
    expect(formatPricePerM2(3500)).toContain('$/m²')
  })
  it('formats number', () => {
    const result = formatPricePerM2(3500)
    expect(result).toContain('3')
    expect(result).toContain('500')
  })
})
