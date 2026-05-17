import { describe, it, expect } from 'vitest'
import { computeListPriceRatio } from './compute-list-price-ratio'

describe('computeListPriceRatio', () => {
  it('returns null for invalid inputs', () => {
    expect(computeListPriceRatio(0, 400000)).toBeNull()
    expect(computeListPriceRatio(400000, 0)).toBeNull()
    expect(computeListPriceRatio(-1, 400000)).toBeNull()
  })

  it('ratioPct 100 when sale equals list', () => {
    const r = computeListPriceRatio(400000, 400000)!
    expect(r.ratioPct).toBe(100)
  })

  it('ratioPct > 100 when sale above list', () => {
    // 420000/400000 = 105%
    const r = computeListPriceRatio(420000, 400000)!
    expect(r.ratioPct).toBe(105)
  })

  it('ratioPct < 100 when sale below list', () => {
    // 380000/400000 = 95%
    const r = computeListPriceRatio(380000, 400000)!
    expect(r.ratioPct).toBe(95)
  })

  it('regime prime when ratioPct > 100', () => {
    expect(computeListPriceRatio(410000, 400000)!.regime).toBe('prime')
  })

  it('regime équilibré when 97 <= ratioPct <= 100', () => {
    expect(computeListPriceRatio(400000, 400000)!.regime).toBe('équilibré')
    // 97% exactly: 388000/400000 = 97%
    expect(computeListPriceRatio(388000, 400000)!.regime).toBe('équilibré')
  })

  it('regime escompte when ratioPct < 97', () => {
    // 384000/400000 = 96%
    expect(computeListPriceRatio(384000, 400000)!.regime).toBe('escompte')
  })

  it('delta is salePrice - listPrice', () => {
    const r = computeListPriceRatio(420000, 400000)!
    expect(r.delta).toBe(20000)
    const r2 = computeListPriceRatio(380000, 400000)!
    expect(r2.delta).toBe(-20000)
  })

  it('signal contains relevant label', () => {
    expect(computeListPriceRatio(420000, 400000)!.signal).toContain('au-dessus')
    expect(computeListPriceRatio(400000, 400000)!.signal).toContain('proche')
    expect(computeListPriceRatio(380000, 400000)!.signal).toContain('sous')
  })
})
