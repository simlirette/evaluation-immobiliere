export type Theme = 'light' | 'dark'

export type TabId = 'dossier' | 'marche' | 'analyse' | 'synthese' | 'rapport'

export interface EnrichmentAlerte {
  niveau: 'critique' | 'attention' | 'info'
  categorie: string
  message: string
}

export interface EnrichmentMarche {
  taux_inoccupation_pct: number | null
  inoccupation_annee: number | null
  nhpi_variation_pct: number | null
  nhpi_indice: number | null
  taux_directeur_pct: number | null
  taux_hypo_5ans_pct: number | null
  mises_en_chantier_12m: number | null
  permis_unites_12m: number | null
  permis_variation_6m_pct: number | null
  taux_chomage_pct: number | null
  taux_emploi_pct: number | null
  taux_participation_pct: number | null
  population: number | null
  population_variation_pct: number | null
  score_marche: number | null
  tension_locative: string | null
  marche_interpretation: string | null
  completions_12m: number | null
  unites_en_construction: number | null
  taux_absorption_pct: number | null
  unites_absorbees_total: number | null
  variation_absorbees_pct_4q: number | null
  ipc_variation_logement_pct: number | null
  ipc_logement_indice: number | null
}

export interface EnrichmentLocalisation {
  distance_cbd_km: number | null
  distance_interpretation: string | null
  en_zone_inondable: boolean | null
  inondable_recurrence: string | null
  en_zone_agricole: boolean | null
  zone_code: string | null
  type_zone: string | null
  ecoles_1km: number | null
  arrets_transport_500m: number | null
  epiceries_500m: number | null
  score_nuisances: number | null
  nuisances_interpretation: string | null
  patrimoine_repertorie: boolean | null
  patrimoine_nom: string | null
  crime_taux_total: number | null
  crime_taux_violents: number | null
  cegep_5km: number | null
  universite_10km: number | null
  postsec_interpretation: string | null
  autoroute_km: number | null
  route_nationale_km: number | null
  artere_km: number | null
  routes_interpretation: string | null
  temperature_moy_c: number | null
  precipitations_mm: number | null
  jours_gel: number | null
  jours_chaleur_extreme: number | null
}

export interface EnrichmentFinancier {
  total_mensuel: number | null
  versement_hypo_mensuel: number | null
  ratio_revenu_pct: number | null
  interpretation_couts: string | null
  ratio_loyer_revenu_pct: number | null
  seuil_location: string | null
  versement_mensuel_estime: number | null
  ratio_mensualite_revenu_pct: number | null
  seuil_propriete: string | null
  revenu_median_menage: number | null
  pct_proprietaires: number | null
  pct_locataires: number | null
  valeur_mediane_logement: number | null
  ratio_dette_revenu_pct: number | null
  variation_dette_revenu_pct: number | null
  ratio_hypotheque_revenu_pct: number | null
  taux_epargne_pct: number | null
}

export interface Enrichment {
  score_global: { score: number; grade: string; recommandation: string } | null
  alertes: { liste: EnrichmentAlerte[]; nb_critiques: number; nb_attention: number; nb_info: number } | null
  score_investissement: { score: number; recommandation: string } | null
  indice_qualite_vie: { score: number; interpretation: string } | null
  score_risque: { score: number; categorie: string } | null
  projection_valeur: { valeur_base: number; taux_base_pct: number; an1: number; an3: number; an5: number } | null
  rendement_locatif: { taux_brut_pct: number; taux_net_pct: number; interpretation: string } | null
  valeur_indicative: { valeur: number; fiabilite: string } | null
  taxes_municipales: { taux_pct: number; annuel: number } | null
  ratio_prix_loyer: { ratio: number; signal: string } | null
  vetuste_batiment: { age_ans: number; categorie: string; depreciation_pct: number } | null
  cout_renovation: { cout_min: number; cout_max: number; cout_median: number; type_travaux: string } | null
  marche: EnrichmentMarche | null
  financier: EnrichmentFinancier | null
  localisation: EnrichmentLocalisation | null
}

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

export interface ComparableInput {
  id: string                        // UUID client-side (React key)
  adresse: string
  date_vente: string                // ISO: "2024-06-15"
  prix_vente: number
  source_id: string                 // ex: "CENTRIS-12345678" | "RF-2024-ABC"
  source_type: 'mls_centris' | 'registre_foncier' | 'dlc' | 'autre'
  type_propriete: string
  surface_hab: number | null        // m²
  surface_terrain: number | null    // m²
  annee_construction: number | null
  nb_logements: number | null
  conditions_vente: 'normale' | 'liee' | 'autre'
  notes: string
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
