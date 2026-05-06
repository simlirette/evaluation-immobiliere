import type { Dossier, Comparable, Adjustment, Document, FactChip } from '@/types'

export const MOCK_DOSSIERS: Dossier[] = [
  { id: '1842-sherbrooke', address: '1842, rue Sherbrooke O.', meta: 'Unifamiliale · Westmount', status: 'en-cours', updatedAt: "Modifié aujourd'hui", pinned: false },
  { id: '90-cote-saint-luc', address: '90, av. Côte-Saint-Luc', meta: 'Condo · Côte-Saint-Luc', status: 'complet', updatedAt: 'Il y a 2 jours', pinned: true },
  { id: '455-rene-levesque', address: '455, boul. René-Lévesque E.', meta: 'Immeuble commercial · Centre-ville', status: 'en-cours', updatedAt: 'Il y a 4 jours', pinned: false },
  { id: '740-victoria', address: '740, av. Victoria', meta: 'Duplex · Saint-Lambert', status: 'complet', updatedAt: 'Il y a 1 semaine', pinned: false },
  { id: '1100-gauchetiere', address: '1100, rue de la Gauchetière O.', meta: 'Condo · Centre-ville', status: 'brouillon', updatedAt: 'Il y a 2 semaines', pinned: false },
  { id: '4220-saint-denis', address: '4220, rue Saint-Denis', meta: 'Triplex · Plateau-Mont-Royal', status: 'brouillon', updatedAt: 'Il y a 3 semaines', pinned: false },
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
  { rank: 'C1', address: '1624, rue Sherbrooke O.', meta: '248 m² hab. · 480 m² terrain · Rénové 2021 · Garage simple', price: '1 195 000 $', date: 'Fév. 2025' },
  { rank: 'C2', address: '1890, rue Sherbrooke O.', meta: '262 m² hab. · 540 m² terrain · 1948 · Garage double', price: '1 420 000 $', date: 'Nov. 2024' },
  { rank: 'C3', address: '44, av. Metcalfe', meta: '231 m² hab. · 495 m² terrain · 1955 · Garage simple', price: '1 150 000 $', date: 'Août 2024' },
  { rank: 'C4', address: '2104, rue Sherbrooke O.', meta: '255 m² hab. · 510 m² terrain · Rénové 2018 · Garage double', price: '1 310 000 $', date: 'Juin 2024' },
]

export const MOCK_ADJUSTMENTS: Adjustment[] = [
  { comparable: 'C1 — 1624 Sherbrooke', salePrice: '1 195 000 $', surface: '+22 000', year: '−8 000', condition: '−15 000', garage: '+18 000', adjusted: '1 212 000 $' },
  { comparable: 'C2 — 1890 Sherbrooke', salePrice: '1 420 000 $', surface: '−18 000', year: '+4 000', condition: '−20 000', garage: '—', adjusted: '1 386 000 $' },
  { comparable: 'C3 — 44 av. Metcalfe', salePrice: '1 150 000 $', surface: '+24 000', year: '−6 000', condition: '−15 000', garage: '+18 000', adjusted: '1 171 000 $' },
  { comparable: 'C4 — 2104 Sherbrooke', salePrice: '1 310 000 $', surface: '−10 000', year: '+2 000', condition: '+5 000', garage: '—', adjusted: '1 307 000 $' },
]
