import type { Dossier, DossierStatus } from '@/types'

export type StatusFilter = 'all' | DossierStatus

export function filterDossiers(
  dossiers: Dossier[],
  search: string,
  statusFilter: StatusFilter,
): Dossier[] {
  const q = search.toLowerCase().trim()
  return dossiers.filter(d => {
    const matchSearch =
      !q ||
      d.address.toLowerCase().includes(q) ||
      `${d.property_type} ${d.neighborhood}`.toLowerCase().includes(q)
    const matchStatus = statusFilter === 'all' || d.status === statusFilter
    return matchSearch && matchStatus
  })
}
