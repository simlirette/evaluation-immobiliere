export interface VenteMock {
  id: string
  adresse: string
  arrondissement: string
  type: string
  annee: number
  superficie: number
  lotArea: number
  prix: number
  date: string
  source: string
}

export interface MarcheMock {
  nom: string
  prixMedian: number
  variation: number
  jrs: number
  volume: number
  tendance: number[]
}

export interface CoutMock {
  categorie: string
  qualite: string
  taux: number
  unite: string
}

export interface TauxMock {
  segment: string
  zone: string
  bas: number
  haut: number
  vacance: number
}

export const VENTES: VenteMock[] = [
  { id: 'V001', adresse: '3420 av. de Vendôme', arrondissement: 'Côte-des-Neiges', type: 'Unifamiliale', annee: 1928, superficie: 1650, lotArea: 4200, prix: 1295000, date: '2026-03-15', source: 'JLR' },
  { id: 'V002', adresse: '5812 av. Glencairn', arrondissement: 'Côte-des-Neiges', type: 'Unifamiliale', annee: 1952, superficie: 1480, lotArea: 3800, prix: 1105000, date: '2026-03-02', source: 'JLR' },
  { id: 'V003', adresse: '2240 ch. de la Côte-Ste-Catherine', arrondissement: 'Outremont', type: 'Unifamiliale', annee: 1935, superficie: 2100, lotArea: 6200, prix: 1890000, date: '2026-02-18', source: 'Centris' },
  { id: 'V004', adresse: '95 av. Bernard', arrondissement: 'Outremont', type: 'Unifamiliale', annee: 1908, superficie: 1920, lotArea: 5100, prix: 1725000, date: '2026-02-05', source: 'JLR' },
  { id: 'V005', adresse: '1540 rue de l\'Épée', arrondissement: 'Outremont', type: 'Unifamiliale', annee: 1941, superficie: 1740, lotArea: 4400, prix: 1450000, date: '2026-01-22', source: 'Centris' },
  { id: 'V006', adresse: '680 av. Rockland', arrondissement: 'Mont-Royal', type: 'Unifamiliale', annee: 1948, superficie: 2340, lotArea: 8100, prix: 2150000, date: '2026-01-10', source: 'JLR' },
  { id: 'V007', adresse: '240 av. Lajoie', arrondissement: 'Outremont', type: 'Duplex', annee: 1929, superficie: 2800, lotArea: 4600, prix: 1580000, date: '2025-12-12', source: 'JLR' },
  { id: 'V008', adresse: '4125 rue Jean-Brillant', arrondissement: 'Côte-des-Neiges', type: 'Condo', annee: 2018, superficie: 920, lotArea: 0, prix: 645000, date: '2025-12-02', source: 'Centris' },
  { id: 'V009', adresse: '3980 av. Prud\'homme', arrondissement: 'NDG', type: 'Unifamiliale', annee: 1962, superficie: 1320, lotArea: 3600, prix: 895000, date: '2025-11-28', source: 'Centris' },
  { id: 'V010', adresse: '5432 av. Victoria', arrondissement: 'Côte-des-Neiges', type: 'Triplex', annee: 1955, superficie: 3600, lotArea: 4200, prix: 1340000, date: '2025-11-14', source: 'JLR' },
]

export const MARCHES: MarcheMock[] = [
  { nom: 'Outremont', prixMedian: 1580000, variation: 4.2, jrs: 18, volume: 84, tendance: [1380, 1420, 1450, 1490, 1510, 1540, 1565, 1580] },
  { nom: 'Côte-des-Neiges', prixMedian: 1120000, variation: 3.1, jrs: 24, volume: 142, tendance: [1020, 1040, 1060, 1075, 1090, 1100, 1112, 1120] },
  { nom: 'Mont-Royal', prixMedian: 1950000, variation: 5.8, jrs: 14, volume: 62, tendance: [1680, 1720, 1770, 1820, 1860, 1895, 1930, 1950] },
  { nom: 'Plateau', prixMedian: 870000, variation: 2.4, jrs: 21, volume: 198, tendance: [820, 830, 840, 848, 855, 860, 866, 870] },
  { nom: 'Rosemont', prixMedian: 720000, variation: 1.8, jrs: 28, volume: 231, tendance: [685, 692, 698, 703, 708, 712, 717, 720] },
  { nom: 'NDG', prixMedian: 940000, variation: 3.5, jrs: 22, volume: 177, tendance: [870, 885, 898, 910, 920, 928, 936, 940] },
  { nom: 'Westmount', prixMedian: 2350000, variation: 6.1, jrs: 31, volume: 45, tendance: [2020, 2080, 2140, 2200, 2250, 2290, 2325, 2350] },
  { nom: 'Verdun', prixMedian: 610000, variation: 1.2, jrs: 32, volume: 186, tendance: [590, 594, 598, 601, 604, 607, 609, 610] },
]

export const COUTS: CoutMock[] = [
  { categorie: 'Unifamiliale', qualite: 'Économique', taux: 185, unite: '$/pi²' },
  { categorie: 'Unifamiliale', qualite: 'Courant', taux: 240, unite: '$/pi²' },
  { categorie: 'Unifamiliale', qualite: 'Supérieur', taux: 295, unite: '$/pi²' },
  { categorie: 'Unifamiliale', qualite: 'Prestige', taux: 380, unite: '$/pi²' },
  { categorie: 'Duplex', qualite: 'Courant', taux: 220, unite: '$/pi²' },
  { categorie: 'Duplex', qualite: 'Supérieur', taux: 275, unite: '$/pi²' },
  { categorie: 'Triplex', qualite: 'Courant', taux: 215, unite: '$/pi²' },
  { categorie: 'Condo', qualite: 'Courant', taux: 260, unite: '$/pi²' },
  { categorie: 'Condo', qualite: 'Supérieur', taux: 315, unite: '$/pi²' },
  { categorie: 'Commercial', qualite: 'Courant', taux: 195, unite: '$/pi²' },
  { categorie: 'Industriel', qualite: 'Léger', taux: 140, unite: '$/pi²' },
  { categorie: 'Garage attenant', qualite: 'Standard', taux: 75, unite: '$/pi²' },
  { categorie: 'Sous-sol fini', qualite: 'Standard', taux: 95, unite: '$/pi²' },
]

export const TAUX: TauxMock[] = [
  { segment: 'Multifamilial — 6 logements et moins', zone: 'Centre', bas: 4.25, haut: 5.50, vacance: 1.8 },
  { segment: 'Multifamilial — 6 logements et moins', zone: 'Périphérie', bas: 4.75, haut: 6.00, vacance: 2.4 },
  { segment: 'Multifamilial — 7 logements et plus', zone: 'Centre', bas: 3.75, haut: 4.75, vacance: 1.5 },
  { segment: 'Multifamilial — 7 logements et plus', zone: 'Périphérie', bas: 4.25, haut: 5.25, vacance: 2.1 },
  { segment: 'Commercial — Rue principale', zone: 'Centre', bas: 5.00, haut: 6.50, vacance: 5.2 },
  { segment: 'Commercial — Centre commercial', zone: 'Banlieue', bas: 5.50, haut: 7.00, vacance: 6.8 },
  { segment: 'Industriel léger', zone: 'Grand Montréal', bas: 5.25, haut: 6.75, vacance: 3.1 },
  { segment: 'Bureau — Classe A', zone: 'Centre-ville', bas: 4.50, haut: 5.75, vacance: 14.2 },
  { segment: 'Bureau — Classe B', zone: 'Centre-ville', bas: 5.25, haut: 6.50, vacance: 18.5 },
  { segment: 'Hôtel / Hospitalité', zone: 'Grand Montréal', bas: 6.50, haut: 8.00, vacance: 22.0 },
]
