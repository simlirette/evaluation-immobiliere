import { describe, it, expect } from 'vitest'
import { filterDossiers } from './filter-dossiers'
import type { Dossier } from '@/types'

function d(address: string, property_type: string, neighborhood: string, status: Dossier['status']): Dossier {
  return { id: address, slug: address, address, property_type, neighborhood, status, updatedAt: '2026-01-01', pinned: false }
}

const DOSSIERS = [
  d('123 Rue Masson', 'Plex', 'Rosemont', 'en-cours'),
  d('456 Av. Papineau', 'Condo', 'Plateau', 'complet'),
  d('789 Bd. Rosemont', 'Maison', 'Outremont', 'brouillon'),
]

describe('filterDossiers', () => {
  it('returns all when search empty and status all', () => {
    expect(filterDossiers(DOSSIERS, '', 'all')).toHaveLength(3)
  })

  it('filters by address substring (case-insensitive)', () => {
    const result = filterDossiers(DOSSIERS, 'masson', 'all')
    expect(result).toHaveLength(1)
    expect(result[0].address).toBe('123 Rue Masson')
  })

  it('filters by property_type', () => {
    expect(filterDossiers(DOSSIERS, 'condo', 'all')).toHaveLength(1)
  })

  it('filters by neighborhood', () => {
    const result = filterDossiers(DOSSIERS, 'rosemont', 'all')
    // "Rue Masson" + "Rosemont" neighborhood → 2 matches
    expect(result).toHaveLength(2)
  })

  it('filters by status', () => {
    expect(filterDossiers(DOSSIERS, '', 'complet')).toHaveLength(1)
    expect(filterDossiers(DOSSIERS, '', 'brouillon')).toHaveLength(1)
    expect(filterDossiers(DOSSIERS, '', 'en-cours')).toHaveLength(1)
  })

  it('combines search and status filter', () => {
    expect(filterDossiers(DOSSIERS, 'Papineau', 'complet')).toHaveLength(1)
    expect(filterDossiers(DOSSIERS, 'Papineau', 'en-cours')).toHaveLength(0)
  })

  it('returns empty for no match', () => {
    expect(filterDossiers(DOSSIERS, 'zzz', 'all')).toHaveLength(0)
  })

  it('handles empty dossiers list', () => {
    expect(filterDossiers([], 'anything', 'all')).toHaveLength(0)
  })
})
