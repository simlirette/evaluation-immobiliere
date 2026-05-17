import type { Dossier } from '@/types'

export type SortKey = 'recent' | 'oldest' | 'az' | 'za'

export function sortDossiers(dossiers: Dossier[], sort: SortKey): Dossier[] {
  return [...dossiers].sort((a, b) => {
    if (sort === 'az') return a.address.localeCompare(b.address, 'fr')
    if (sort === 'za') return b.address.localeCompare(a.address, 'fr')
    if (sort === 'oldest') return a.updatedAt.localeCompare(b.updatedAt)
    return b.updatedAt.localeCompare(a.updatedAt) // recent first (default)
  })
}
