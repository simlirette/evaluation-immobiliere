import { describe, it, expect } from 'vitest'
import { formatListCount } from './format-list-count'

describe('formatListCount', () => {
  it('total 0 → null', () => {
    expect(formatListCount(0, 0)).toBeNull()
  })

  it('unfiltered singular', () => {
    expect(formatListCount(1, 1)).toBe('1 comparable')
  })

  it('unfiltered plural', () => {
    expect(formatListCount(5, 5)).toBe('5 comparables')
  })

  it('filtered shows X / N', () => {
    expect(formatListCount(2, 5)).toBe('2 / 5 comparables')
  })

  it('filtered singular total', () => {
    expect(formatListCount(0, 1)).toBe('0 / 1 comparable')
  })

  it('custom noun', () => {
    expect(formatListCount(3, 3, 'dossier')).toBe('3 dossiers')
  })

  it('custom noun filtered', () => {
    expect(formatListCount(1, 4, 'dossier')).toBe('1 / 4 dossiers')
  })

  it('zero visible with total > 0', () => {
    expect(formatListCount(0, 5)).toBe('0 / 5 comparables')
  })
})
