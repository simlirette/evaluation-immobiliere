export interface DossierArchive {
  id: string
  adresse: string
  ville: string
  type: string
  annee: number
  superficie: number
  valeur: number
  client: string
  mandat: string
  dateCompletion: string
  evaluateur: string
}

export const ARCHIVES: DossierArchive[] = [
  { id: 'EI-2026-042', adresse: '3420 av. de Vendôme', ville: 'Montréal (CDN)', type: 'Unifamiliale', annee: 1928, superficie: 1650, valeur: 1295000, client: 'Banque Nationale', mandat: 'Hypothécaire', dateCompletion: '2026-03-28', evaluateur: 'Maxime Tremblay, É.A.' },
  { id: 'EI-2026-039', adresse: '5812 av. Glencairn', ville: 'Montréal (CDN)', type: 'Unifamiliale', annee: 1952, superficie: 1480, valeur: 1105000, client: 'Desjardins', mandat: 'Hypothécaire', dateCompletion: '2026-03-15', evaluateur: 'Maxime Tremblay, É.A.' },
  { id: 'EI-2026-031', adresse: '2240 ch. de la Côte-Ste-Catherine', ville: 'Outremont', type: 'Unifamiliale', annee: 1935, superficie: 2100, valeur: 1890000, client: 'Succession Beauchamp', mandat: 'Successoral', dateCompletion: '2026-02-20', evaluateur: 'Geneviève Roy, É.A.' },
  { id: 'EI-2026-024', adresse: '95 av. Bernard', ville: 'Outremont', type: 'Unifamiliale', annee: 1908, superficie: 1920, valeur: 1725000, client: 'Colliers International', mandat: 'Pré-vente', dateCompletion: '2026-02-08', evaluateur: 'Maxime Tremblay, É.A.' },
  { id: 'EI-2026-017', adresse: '1540 rue de l\'Épée', ville: 'Outremont', type: 'Unifamiliale', annee: 1941, superficie: 1740, valeur: 1450000, client: 'BMO Banque', mandat: 'Hypothécaire', dateCompletion: '2026-01-25', evaluateur: 'Geneviève Roy, É.A.' },
  { id: 'EI-2026-009', adresse: '680 av. Rockland', ville: 'Mont-Royal', type: 'Unifamiliale', annee: 1948, superficie: 2340, valeur: 2150000, client: 'Tribunal administratif', mandat: 'Litige', dateCompletion: '2026-01-14', evaluateur: 'Maxime Tremblay, É.A.' },
  { id: 'EI-2025-198', adresse: '240 av. Lajoie', ville: 'Outremont', type: 'Duplex', annee: 1929, superficie: 2800, valeur: 1580000, client: 'CMHC', mandat: 'Hypothécaire', dateCompletion: '2025-12-18', evaluateur: 'Geneviève Roy, É.A.' },
  { id: 'EI-2025-191', adresse: '4125 rue Jean-Brillant', ville: 'Montréal (CDN)', type: 'Condo', annee: 2018, superficie: 920, valeur: 645000, client: 'RBC Banque Royale', mandat: 'Hypothécaire', dateCompletion: '2025-12-05', evaluateur: 'Maxime Tremblay, É.A.' },
  { id: 'EI-2025-185', adresse: '3980 av. Prud\'homme', ville: 'NDG', type: 'Unifamiliale', annee: 1962, superficie: 1320, valeur: 895000, client: 'Famille Lapointe', mandat: 'Pré-vente', dateCompletion: '2025-11-30', evaluateur: 'Geneviève Roy, É.A.' },
  { id: 'EI-2025-179', adresse: '5432 av. Victoria', ville: 'Montréal (CDN)', type: 'Triplex', annee: 1955, superficie: 3600, valeur: 1340000, client: 'Succession Tran', mandat: 'Successoral', dateCompletion: '2025-11-18', evaluateur: 'Maxime Tremblay, É.A.' },
  { id: 'EI-2025-163', adresse: '1820 av. Dufresnoy', ville: 'Outremont', type: 'Unifamiliale', annee: 1932, superficie: 2240, valeur: 2050000, client: 'TD Canada Trust', mandat: 'Hypothécaire', dateCompletion: '2025-10-22', evaluateur: 'Geneviève Roy, É.A.' },
  { id: 'EI-2025-154', adresse: '8420 rue de Gaspé', ville: 'Rosemont', type: 'Duplex', annee: 1958, superficie: 2600, valeur: 980000, client: 'Desjardins', mandat: 'Hypothécaire', dateCompletion: '2025-10-08', evaluateur: 'Maxime Tremblay, É.A.' },
  { id: 'EI-2025-142', adresse: '1145 av. du Docteur-Penfield', ville: 'Westmount', type: 'Unifamiliale', annee: 1924, superficie: 3200, valeur: 3250000, client: 'BMO Banque', mandat: 'Hypothécaire', dateCompletion: '2025-09-19', evaluateur: 'Geneviève Roy, É.A.' },
  { id: 'EI-2025-128', adresse: '3560 av. du Parc', ville: 'Plateau', type: 'Triplex', annee: 1947, superficie: 4100, valeur: 1650000, client: 'CMHC', mandat: 'Hypothécaire', dateCompletion: '2025-09-02', evaluateur: 'Maxime Tremblay, É.A.' },
  { id: 'EI-2025-115', adresse: '5910 ch. Côte-des-Neiges', ville: 'Montréal (CDN)', type: 'Condo', annee: 2015, superficie: 1080, valeur: 742000, client: 'RBC Banque Royale', mandat: 'Hypothécaire', dateCompletion: '2025-08-14', evaluateur: 'Geneviève Roy, É.A.' },
  { id: 'EI-2025-101', adresse: '740 av. Lajoie', ville: 'Outremont', type: 'Unifamiliale', annee: 1939, superficie: 1890, valeur: 1620000, client: 'Famille Nguyen', mandat: 'Pré-vente', dateCompletion: '2025-07-28', evaluateur: 'Maxime Tremblay, É.A.' },
  { id: 'EI-2024-284', adresse: '2985 av. Maplewood', ville: 'Mont-Royal', type: 'Unifamiliale', annee: 1954, superficie: 2680, valeur: 2380000, client: 'Succession Moreau', mandat: 'Successoral', dateCompletion: '2024-12-15', evaluateur: 'Geneviève Roy, É.A.' },
  { id: 'EI-2024-271', adresse: '4220 rue Drolet', ville: 'Plateau', type: 'Duplex', annee: 1908, superficie: 2450, valeur: 1125000, client: 'Desjardins', mandat: 'Hypothécaire', dateCompletion: '2024-11-29', evaluateur: 'Maxime Tremblay, É.A.' },
  { id: 'EI-2024-258', adresse: '1680 rue Sainte-Famille', ville: 'Plateau', type: 'Condo', annee: 2021, superficie: 840, valeur: 598000, client: 'BMO Banque', mandat: 'Hypothécaire', dateCompletion: '2024-11-12', evaluateur: 'Geneviève Roy, É.A.' },
  { id: 'EI-2024-245', adresse: '6340 av. Somerled', ville: 'NDG', type: 'Unifamiliale', annee: 1965, superficie: 1540, valeur: 1020000, client: 'Tribunal administratif', mandat: 'Expropriation', dateCompletion: '2024-10-24', evaluateur: 'Maxime Tremblay, É.A.' },
]

export function groupByYear(archives: DossierArchive[]): Record<number, DossierArchive[]> {
  return archives.reduce((acc, d) => {
    const year = parseInt(d.dateCompletion.slice(0, 4))
    if (!acc[year]) acc[year] = []
    acc[year].push(d)
    return acc
  }, {} as Record<number, DossierArchive[]>)
}

export function getYears(archives: DossierArchive[]): number[] {
  return [...new Set(archives.map(d => parseInt(d.dateCompletion.slice(0, 4))))].sort((a, b) => b - a)
}
