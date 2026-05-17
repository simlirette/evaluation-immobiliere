import { describe, it, expect } from 'vitest'
import { sortDossiers } from './sort-dossiers'
import type { Dossier } from '@/types'

function makeDossier(overrides: Partial<Dossier>): Dossier {
  return {
    id: 'slug-1', slug: 'slug-1', address: 'Addr', property_type: 'Plex',
    neighborhood: 'Rosemont', status: 'brouillon', updatedAt: '2026-01-01', pinned: false,
    ...overrides,
  }
}

const A = makeDossier({ id: 'a', slug: 'a', address: 'Alpha', updatedAt: '2026-05-01' })
const B = makeDossier({ id: 'b', slug: 'b', address: 'Bravo', updatedAt: '2026-05-10' })
const C = makeDossier({ id: 'c', slug: 'c', address: 'Charlie', updatedAt: '2026-03-01' })

describe('sortDossiers', () => {
  it('recent: newest updatedAt first', () => {
    const result = sortDossiers([A, B, C], 'recent')
    expect(result.map(d => d.slug)).toEqual(['b', 'a', 'c'])
  })

  it('oldest: oldest updatedAt first', () => {
    const result = sortDossiers([A, B, C], 'oldest')
    expect(result.map(d => d.slug)).toEqual(['c', 'a', 'b'])
  })

  it('az: alphabetical ascending', () => {
    const result = sortDossiers([C, A, B], 'az')
    expect(result.map(d => d.address)).toEqual(['Alpha', 'Bravo', 'Charlie'])
  })

  it('za: alphabetical descending', () => {
    const result = sortDossiers([A, C, B], 'za')
    expect(result.map(d => d.address)).toEqual(['Charlie', 'Bravo', 'Alpha'])
  })

  it('does not mutate the input array', () => {
    const input = [B, A, C]
    sortDossiers(input, 'az')
    expect(input.map(d => d.slug)).toEqual(['b', 'a', 'c'])
  })

  it('handles empty array', () => {
    expect(sortDossiers([], 'recent')).toEqual([])
  })

  it('handles single element', () => {
    expect(sortDossiers([A], 'za')).toEqual([A])
  })
})
