import { describe, it, expect } from 'vitest'
import { formatRelativeDate } from './format-date'

const NOW = new Date(2026, 4, 16) // 2026-05-16

describe('formatRelativeDate', () => {
  it('returns Aujourd\'hui for today', () => {
    expect(formatRelativeDate('2026-05-16', NOW)).toBe("Aujourd'hui")
  })

  it('returns Hier for yesterday', () => {
    expect(formatRelativeDate('2026-05-15', NOW)).toBe('Hier')
  })

  it('returns N jours for 2-6 days ago', () => {
    expect(formatRelativeDate('2026-05-14', NOW)).toBe('il y a 2 jours')
    expect(formatRelativeDate('2026-05-10', NOW)).toBe('il y a 6 jours')
  })

  it('returns 1 semaine for 7-13 days ago', () => {
    expect(formatRelativeDate('2026-05-09', NOW)).toBe('il y a 1 semaine')
    expect(formatRelativeDate('2026-05-03', NOW)).toBe('il y a 1 semaine')
  })

  it('returns N semaines for 14-29 days ago', () => {
    expect(formatRelativeDate('2026-05-02', NOW)).toBe('il y a 2 semaines')
    expect(formatRelativeDate('2026-04-17', NOW)).toBe('il y a 4 semaines')
  })

  it('returns absolute label for same year', () => {
    expect(formatRelativeDate('2026-03-01', NOW)).toBe('1 mar')
    expect(formatRelativeDate('2026-01-15', NOW)).toBe('15 jan')
  })

  it('returns absolute label with year for previous year', () => {
    expect(formatRelativeDate('2025-12-31', NOW)).toBe('31 déc 2025')
    expect(formatRelativeDate('2024-06-10', NOW)).toBe('10 juin 2024')
  })

  it('uses system date when now not provided', () => {
    // Just verify it doesn't throw
    expect(() => formatRelativeDate('2026-01-01')).not.toThrow()
  })
})
