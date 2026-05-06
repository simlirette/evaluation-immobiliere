export type Theme = 'light' | 'dark'

export type TabId = 'dossier' | 'marche' | 'analyse' | 'rapport'

export interface Tab {
  id: TabId
  label: string
}

export type DossierStatus = 'brouillon' | 'en-cours' | 'complet'

export interface Dossier {
  id: string           // UUID
  slug: string         // URL param
  address: string
  property_type: string
  neighborhood: string
  status: DossierStatus
  updatedAt: string    // formatted for display
  pinned: boolean
}

export interface Document {
  id: string
  name: string         // display_name
  filename: string     // last segment of storage_path
  sizeLabel: string    // formatted from size_bytes
}

export interface FactChip {
  label: string
  highlight: boolean
}

export interface Comparable {
  id: string
  rank: string
  address: string
  hab_m2: number | null
  terrain_m2: number | null
  year_built: number | null
  renovated_year: number | null
  garage_type: string | null
  sale_price: number
  sale_date: string    // ISO date
  meta: string         // built from structured fields
  price: string        // formatted
  date: string         // formatted
}

export interface Adjustment {
  id: string
  comparable_id: string
  comparableLabel: string
  salePrice: number
  surface_adj: number
  year_adj: number
  condition_adj: number
  garage_adj: number
  adjusted: number
}

export interface ContextMenuTarget {
  name: string
  pinned: boolean
  x: number
  y: number
}
