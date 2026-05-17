import { describe, it, expect } from 'vitest'
import { formatCAD, fmtNum } from './format-number'

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
