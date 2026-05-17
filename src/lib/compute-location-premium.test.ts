import { describe, it, expect } from 'vitest'
import { computeLocationPremium } from './compute-location-premium'

describe('computeLocationPremium', () => {
  it('returns null when medianHomeValue is 0', () => {
    expect(computeLocationPremium(500000, 0)).toBeNull()
  })

  it('returns null when reconciledValue is 0', () => {
    expect(computeLocationPremium(0, 400000)).toBeNull()
  })

  it('signal is prime when reconciledValue > 10% above median', () => {
    // 550000 vs 500000 = +10% → exactly 10%, so aligné (not strictly > 10)
    expect(computeLocationPremium(551000, 500000)!.signal).toBe('prime')
  })

  it('signal is aligné when within ±10%', () => {
    expect(computeLocationPremium(500000, 500000)!.signal).toBe('aligné')
    expect(computeLocationPremium(550000, 500000)!.signal).toBe('aligné') // exactly +10%
    expect(computeLocationPremium(450000, 500000)!.signal).toBe('aligné') // exactly -10%
  })

  it('signal is escompte when reconciledValue < 10% below median', () => {
    expect(computeLocationPremium(449000, 500000)!.signal).toBe('escompte')
  })

  it('delta is reconciledValue minus medianHomeValue', () => {
    const r = computeLocationPremium(600000, 500000)!
    expect(r.delta).toBe(100000)
  })

  it('deltaPct is rounded to 1 decimal', () => {
    // 600000 / 500000 - 1 = 20%
    const r = computeLocationPremium(600000, 500000)!
    expect(r.deltaPct).toBe(20)
  })

  it('negative deltaPct for escompte case', () => {
    const r = computeLocationPremium(400000, 500000)!
    expect(r.deltaPct).toBe(-20)
    expect(r.delta).toBe(-100000)
  })

  it('deltaPct rounds correctly', () => {
    // 333333 / 300000 = 11.111% → 11.1
    const r = computeLocationPremium(333333, 300000)!
    expect(r.deltaPct).toBeCloseTo(11.1, 0)
  })
})
