import type { Dossier, Comparable, Adjustment, Document, FactChip } from '@/types'

export const MOCK_DOSSIERS: Dossier[] = [
  { id: 'uuid-1', slug: '1842-sherbrooke', address: '1842, rue Sherbrooke O.', property_type: 'Unifamiliale', neighborhood: 'Westmount', status: 'en-cours', updatedAt: "Modifié aujourd'hui", pinned: false },
  { id: 'uuid-2', slug: '90-cote-saint-luc', address: '90, av. Côte-Saint-Luc', property_type: 'Condo', neighborhood: 'Côte-Saint-Luc', status: 'complet', updatedAt: 'Il y a 2 jours', pinned: true },
  { id: 'uuid-3', slug: '455-rene-levesque', address: '455, boul. René-Lévesque E.', property_type: 'Immeuble commercial', neighborhood: 'Centre-ville', status: 'en-cours', updatedAt: 'Il y a 4 jours', pinned: false },
  { id: 'uuid-4', slug: '740-victoria', address: '740, av. Victoria', property_type: 'Duplex', neighborhood: 'Saint-Lambert', status: 'complet', updatedAt: 'Il y a 1 semaine', pinned: false },
  { id: 'uuid-5', slug: '1100-gauchetiere', address: '1100, rue de la Gauchetière O.', property_type: 'Condo', neighborhood: 'Centre-ville', status: 'brouillon', updatedAt: 'Il y a 2 semaines', pinned: false },
  { id: 'uuid-6', slug: '4220-saint-denis', address: '4220, rue Saint-Denis', property_type: 'Triplex', neighborhood: 'Plateau-Mont-Royal', status: 'brouillon', updatedAt: 'Il y a 3 semaines', pinned: false },
]

export const MOCK_DOCUMENTS: Document[] = [
  { id: '1', name: 'Certificat de localisation', filename: '1842-sherbrooke-cert.pdf', sizeLabel: '2.4 MB' },
  { id: '2', name: 'Titre de propriété', filename: 'titre-1842.pdf', sizeLabel: '890 KB' },
]

export const MOCK_CHIPS: FactChip[] = [
  { label: 'Surface : 248 m²', highlight: true },
  { label: 'Terrain : 520 m²', highlight: true },
  { label: 'Année : 1952', highlight: true },
  { label: 'Zonage : R-2', highlight: true },
  { label: 'Garage double', highlight: false },
  { label: '4 chambres', highlight: false },
  { label: 'Rénové 2019', highlight: false },
  { label: 'Titre : propre', highlight: false },
]

export const MOCK_COMPARABLES: Comparable[] = [
  { id: 'c1', rank: 'C1', address: '1624, rue Sherbrooke O.', hab_m2: 248, terrain_m2: 480, year_built: null, renovated_year: 2021, garage_type: 'simple', sale_price: 1195000, sale_date: '2025-02-01', meta: '248 m² hab. · 480 m² terrain · Rénové 2021 · Garage simple', price: '1 195 000 $', date: 'Fév. 2025' },
  { id: 'c2', rank: 'C2', address: '1890, rue Sherbrooke O.', hab_m2: 262, terrain_m2: 540, year_built: 1948, renovated_year: null, garage_type: 'double', sale_price: 1420000, sale_date: '2024-11-01', meta: '262 m² hab. · 540 m² terrain · 1948 · Garage double', price: '1 420 000 $', date: 'Nov. 2024' },
  { id: 'c3', rank: 'C3', address: '44, av. Metcalfe', hab_m2: 231, terrain_m2: 495, year_built: 1955, renovated_year: null, garage_type: 'simple', sale_price: 1150000, sale_date: '2024-08-01', meta: '231 m² hab. · 495 m² terrain · 1955 · Garage simple', price: '1 150 000 $', date: 'Août 2024' },
  { id: 'c4', rank: 'C4', address: '2104, rue Sherbrooke O.', hab_m2: 255, terrain_m2: 510, year_built: null, renovated_year: 2018, garage_type: 'double', sale_price: 1310000, sale_date: '2024-06-01', meta: '255 m² hab. · 510 m² terrain · Rénové 2018 · Garage double', price: '1 310 000 $', date: 'Juin 2024' },
]

export const MOCK_ADJUSTMENTS: Adjustment[] = [
  { id: 'a1', comparable_id: 'c1', comparableLabel: 'C1 — 1624 Sherbrooke', salePrice: 1195000, surface_adj: 22000, year_adj: -8000, condition_adj: -15000, garage_adj: 18000, adjusted: 1212000 },
  { id: 'a2', comparable_id: 'c2', comparableLabel: 'C2 — 1890 Sherbrooke', salePrice: 1420000, surface_adj: -18000, year_adj: 4000, condition_adj: -20000, garage_adj: 0, adjusted: 1386000 },
  { id: 'a3', comparable_id: 'c3', comparableLabel: 'C3 — 44 av. Metcalfe', salePrice: 1150000, surface_adj: 24000, year_adj: -6000, condition_adj: -15000, garage_adj: 18000, adjusted: 1171000 },
  { id: 'a4', comparable_id: 'c4', comparableLabel: 'C4 — 2104 Sherbrooke', salePrice: 1310000, surface_adj: -10000, year_adj: 2000, condition_adj: 5000, garage_adj: 0, adjusted: 1307000 },
]
