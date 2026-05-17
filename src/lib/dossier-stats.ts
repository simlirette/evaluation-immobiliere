import type { Dossier } from '@/types'

export interface DossierStats {
  total: number
  complet: number
  en_cours: number
  brouillon: number
}

export function computeDossierStats(dossiers: Dossier[]): DossierStats {
  return dossiers.reduce<DossierStats>(
    (acc, d) => {
      acc.total++
      if (d.status === 'complet') acc.complet++
      else if (d.status === 'en-cours') acc.en_cours++
      else acc.brouillon++
      return acc
    },
    { total: 0, complet: 0, en_cours: 0, brouillon: 0 },
  )
}
