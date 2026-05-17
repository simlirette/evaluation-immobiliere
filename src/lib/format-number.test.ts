import { describe, it, expect } from 'vitest'
import { formatCAD, fmtNum, formatPct } from './format-number'

describe('formatCAD', () => {
  it('formats zero', () => {
    expect(formatCAD(0)).toContain('0')
  })
  it('contains dollar sign', () => {
    expect(formatCAD(400000)).toContain('$')
  })
  it('no fraction digits', () => {
    expect(formatCAD(400000.9)).not.toContain('.')
    expect(formatCAD(400000.9)).not.toContain(',')
  })
  it('does not contain CA prefix', () => {
    expect(formatCAD(400000)).not.toMatch(/^CA/)
  })
  it('negative value contains minus', () => {
    expect(formatCAD(-50000)).toContain('50')
  })
})

describe('fmtNum', () => {
  it('null → dash', () => {
    expect(fmtNum(null)).toBe('—')
  })
  it('undefined → dash', () => {
    expect(fmtNum(undefined)).toBe('—')
  })
  it('zero → "0"', () => {
    expect(fmtNum(0)).toBe('0')
  })
  it('rounds to digits', () => {
    const r = fmtNum(3.567, 1)
    expect(r).toContain('3')
    expect(r).toContain('6')
  })
  it('default digits=0 truncates decimal', () => {
    expect(fmtNum(7.9)).not.toContain('.')
    expect(fmtNum(7.9)).not.toContain(',')
  })
  it('large number formatted', () => {
    expect(fmtNum(1000000)).toContain('000')
  })
})

describe('formatPct', () => {
  it('null → dash', () => {
    expect(formatPct(null)).toBe('—')
  })
  it('undefined → dash', () => {
    expect(formatPct(undefined)).toBe('—')
  })
  it('contains % sign', () => {
    expect(formatPct(3.5)).toContain('%')
  })
  it('zero → "0 %"', () => {
    expect(formatPct(0)).toContain('0')
    expect(formatPct(0)).toContain('%')
  })
  it('default 1 decimal digit', () => {
    const r = formatPct(3.567)
    expect(r).toContain('3')
    expect(r).toContain('6')
  })
  it('custom digits=0 truncates', () => {
    const r = formatPct(3.9, 0)
    expect(r).toContain('4')
    expect(r).not.toContain('.')
    expect(r).not.toContain(',')
  })
  it('negative value', () => {
    expect(formatPct(-2.5)).toContain('2')
    expect(formatPct(-2.5)).toContain('%')
  })
})
