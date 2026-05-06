export type Theme = 'light' | 'dark'

export type TabId = 'dossier' | 'marche' | 'analyse' | 'rapport'

export interface Tab {
  id: TabId
  label: string
}

export type DossierStatus = 'en-cours' | 'complet' | 'brouillon'

export interface Dossier {
  id: string
  address: string
  meta: string
  status: DossierStatus
  updatedAt: string
  pinned: boolean
}

export interface Document {
  id: string
  name: string
  filename: string
  sizeLabel: string
}

export interface FactChip {
  label: string
  highlight: boolean
}

export interface Comparable {
  rank: string
  address: string
  meta: string
  price: string
  date: string
}

export interface Adjustment {
  comparable: string
  salePrice: string
  surface: string
  year: string
  condition: string
  garage: string
  adjusted: string
}

export interface ContextMenuTarget {
  name: string
  pinned: boolean
  x: number
  y: number
}
