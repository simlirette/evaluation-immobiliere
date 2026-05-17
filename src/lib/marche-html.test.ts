import { describe, it, expect } from 'vitest'
import { buildMarcheHtml } from './marche-html'
import type { Comparable, EnrichmentMarche } from '@/types'

const comps: Comparable[] = [
  { id: 'c1', rank: '1', address: '10 rue Laval', hab_m2: 120, terrain_m2: 400, year_built: 1985, renovated_year: null, garage_type: 'Détaché', sale_price: 420000, sale_date: '2024-03-15', meta: '120 m² · 1985', price: '420 000 $', date: '15 mars 2024' },
  { id: 'c2', rank: '2', address: '25 av. Cartier', hab_m2: 110, terrain_m2: 350, year_built: 1992, renovated_year: null, garage_type: null, sale_price: 395000, sale_date: '2024-02-01', meta: '110 m² · 1992', price: '395 000 $', date: '1 févr. 2024' },
]

const marche: EnrichmentMarche = {
  score_marche: 7.4, tension_locative: 'tendu', marche_interpretation: 'Marché dynamique favorable',
  taux_inoccupation_pct: 1.8, nhpi_variation_pct: 4.2, taux_hypo_5ans_pct: 5.24, taux_directeur_pct: 4.25,
  taux_chomage_pct: 4.1, taux_emploi_pct: 62.1, taux_participation_pct: 65.0,
  inoccupation_annee: 2023, nhpi_indice: 103.2, mises_en_chantier_12m: 2100, permis_unites_12m: 1900,
  permis_variation_6m_pct: 3.2, population: 2100000, population_variation_pct: 1.1,
  completions_12m: 1800, unites_en_construction: 8200, taux_absorption_pct: 88, unites_absorbees_total: 1400,
  variation_absorbees_pct_4q: 5.0, ipc_variation_logement_pct: 3.1, ipc_logement_indice: 155.2,
}

describe('buildMarcheHtml', () => {
  it('includes address and heading', () => {
    const html = buildMarcheHtml(comps, marche, '5 rue Test')
    expect(html).toContain('5 rue Test')
    expect(html).toContain('Rapport de marché')
  })

  it('includes score marché', () => {
    const html = buildMarcheHtml(comps, marche)
    expect(html).toContain('Score de marché')
    expect(html).toContain('/&nbsp;10')
    expect(html).toContain('tendu')
  })

  it('includes all comparables', () => {
    const html = buildMarcheHtml(comps, marche)
    expect(html).toContain('10 rue Laval')
    expect(html).toContain('25 av. Cartier')
    expect(html).toContain('2 comparables retenus')
  })

  it('shows comparable count in heading', () => {
    const html = buildMarcheHtml([comps[0]], marche)
    expect(html).toContain('1 comparable retenu')
  })

  it('includes market context chips', () => {
    const html = buildMarcheHtml(comps, marche)
    expect(html).toContain('Inoccupation')
    expect(html).toContain('NHPI variation')
    expect(html).toContain('Taux directeur')
  })

  it('handles empty comparables', () => {
    const html = buildMarcheHtml([], marche)
    expect(html).toContain('Aucun comparable chargé')
  })

  it('handles null marche', () => {
    const html = buildMarcheHtml(comps, null)
    expect(html).toContain('10 rue Laval')
    expect(html).not.toContain('Score de marché')
  })
})
