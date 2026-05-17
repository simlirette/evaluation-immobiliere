import { describe, it, expect } from 'vitest'
import { computeDossierStats } from './dossier-stats'
import type { Dossier } from '@/types'

function d(status: Dossier['status']): Dossier {
  return { id: 's', slug: 's', address: 'A', property_type: 'P', neighborhood: 'N', status, updatedAt: '2026-01-01', pinned: false }
}

describe('computeDossierStats', () => {
  it('returns zeros for empty list', () => {
    expect(computeDossierStats([])).toEqual({ total: 0, complet: 0, en_cours: 0, brouillon: 0 })
  })

  it('counts each status correctly', () => {
    const dossiers = [d('complet'), d('complet'), d('en-cours'), d('brouillon')]
    expect(computeDossierStats(dossiers)).toEqual({ total: 4, complet: 2, en_cours: 1, brouillon: 1 })
  })

  it('total equals sum of statuses', () => {
    const dossiers = [d('brouillon'), d('en-cours'), d('complet')]
    const stats = computeDossierStats(dossiers)
    expect(stats.total).toBe(stats.complet + stats.en_cours + stats.brouillon)
  })

  it('handles all same status', () => {
    const dossiers = [d('en-cours'), d('en-cours'), d('en-cours')]
    expect(computeDossierStats(dossiers)).toEqual({ total: 3, complet: 0, en_cours: 3, brouillon: 0 })
  })
})
