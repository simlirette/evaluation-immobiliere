// Raw DB row shapes — match table columns exactly.

export interface DbDossier {
  id: string
  slug: string
  address: string
  property_type: string
  neighborhood: string
  status: 'brouillon' | 'en-cours' | 'complet'
  hab_m2: number | null
  terrain_m2: number | null
  year_built: number | null
  zoning: string | null
  garage_type: string | null
  created_by: string
  created_at: string
  updated_at: string
  pinned?: boolean
}

export interface DbPropertyFact {
  id: string
  dossier_id: string
  label: string
  highlight: boolean
  sort_order: number
}

export interface DbDocument {
  id: string
  dossier_id: string
  display_name: string
  storage_path: string
  size_bytes: number | null
  uploaded_by: string | null
  uploaded_at: string
}

export interface DbRapportVersion {
  id: string
  session_id: string
  dossier_id: string
  content: string
  format: 'abrege' | 'complet' | 'markdown' | 'html'
  label: string
  is_initial: boolean
  created_by: string | null
  created_at: string
  updated_at: string
}

export interface DbComparable {
  id: string
  dossier_id: string
  rank: string
  address: string
  hab_m2: number | null
  terrain_m2: number | null
  year_built: number | null
  renovated_year: number | null
  garage_type: string | null
  sale_price: number
  sale_date: string
  sort_order: number
}

export interface DbAdjustment {
  id: string
  dossier_id: string
  comparable_id: string
  surface_adj: number
  year_adj: number
  condition_adj: number
  garage_adj: number
}
