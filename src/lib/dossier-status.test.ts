import { describe, it, expect } from 'vitest'
import { nextDossierStatus, prevDossierStatus } from './dossier-status'

describe('nextDossierStatus', () => {
  it('brouillon → en-cours', () => {
    expect(nextDossierStatus('brouillon')).toBe('en-cours')
  })
  it('en-cours → complet', () => {
    expect(nextDossierStatus('en-cours')).toBe('complet')
  })
  it('complet wraps to brouillon', () => {
    expect(nextDossierStatus('complet')).toBe('brouillon')
  })
  it('full cycle returns to origin', () => {
    const s0 = 'brouillon'
    const s1 = nextDossierStatus(s0)
    const s2 = nextDossierStatus(s1)
    const s3 = nextDossierStatus(s2)
    expect(s3).toBe(s0)
  })
})

describe('prevDossierStatus', () => {
  it('en-cours → brouillon', () => {
    expect(prevDossierStatus('en-cours')).toBe('brouillon')
  })
  it('complet → en-cours', () => {
    expect(prevDossierStatus('complet')).toBe('en-cours')
  })
  it('brouillon wraps to complet', () => {
    expect(prevDossierStatus('brouillon')).toBe('complet')
  })
})
