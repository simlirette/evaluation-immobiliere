export interface ModeleMock {
  id: string
  categorie: string
  titre: string
  description: string
  sections: number
  pages: number
  documents: number
  oeaqConforme: boolean
  nbDossiers: number
  modifieLe: string
}

export const MODELES: ModeleMock[] = [
  {
    id: 'M001',
    categorie: 'Résidentiel',
    titre: 'Unifamiliale — Rapport abrégé',
    description: 'Rapport standard pour propriétés unifamiliales. Comparaison directe, un ou deux approches. Format conforme hypothécaire OEAQ.',
    sections: 8, pages: 18, documents: 4,
    oeaqConforme: true,
    nbDossiers: 142,
    modifieLe: '2026-04-10',
  },
  {
    id: 'M002',
    categorie: 'Résidentiel',
    titre: 'Unifamiliale — Rapport complet',
    description: 'Rapport détaillé avec trois approches et analyse de marché approfondie. Inclut section patrimoine et analyse de risque.',
    sections: 12, pages: 32, documents: 6,
    oeaqConforme: true,
    nbDossiers: 87,
    modifieLe: '2026-03-22',
  },
  {
    id: 'M003',
    categorie: 'Résidentiel',
    titre: 'Condo — Rapport abrégé',
    description: 'Rapport spécialisé pour condominiums. Inclut frais de copropriété, fonds de prévoyance et comparaison par étage.',
    sections: 9, pages: 20, documents: 5,
    oeaqConforme: true,
    nbDossiers: 68,
    modifieLe: '2026-02-14',
  },
  {
    id: 'M004',
    categorie: 'Multifamilial',
    titre: 'Plex (2–5 logements)',
    description: 'Rapport pour duplex, triplex, quadruplex. Approche revenus obligatoire. Tableau de loyers et taux de capitalisation.',
    sections: 11, pages: 28, documents: 7,
    oeaqConforme: true,
    nbDossiers: 54,
    modifieLe: '2026-01-30',
  },
  {
    id: 'M005',
    categorie: 'Commercial',
    titre: 'Local commercial — Rue principale',
    description: 'Rapport pour locaux commerciaux de rue. Analyse de rendement, achalandage piétonnier et comparaison avec baux récents.',
    sections: 13, pages: 35, documents: 8,
    oeaqConforme: true,
    nbDossiers: 23,
    modifieLe: '2025-12-05',
  },
  {
    id: 'M006',
    categorie: 'Spécialisé',
    titre: 'Succession & liquidation',
    description: 'Rapport adapté aux contextes successoraux. Inclut la date de valeur historique, attestation conforme et section héritiers.',
    sections: 10, pages: 24, documents: 5,
    oeaqConforme: true,
    nbDossiers: 31,
    modifieLe: '2025-11-18',
  },
]
