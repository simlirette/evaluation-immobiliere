import { describe, it, expect } from 'vitest'
import { buildAnalyseHtml } from './analyse-html'
import type { Comparable, Adjustment, EnrichmentFinancier } from '@/types'

const adjs: Adjustment[] = [
  { id: 'a1', comparable_id: 'c1', comparableLabel: '10 rue Laval', salePrice: 420000, surface_adj: 5000, year_adj: -3000, condition_adj: 0, garage_adj: 0, adjusted: 422000 },
  { id: 'a2', comparable_id: 'c2', comparableLabel: '25 av. Cartier', salePrice: 395000, surface_adj: 12000, year_adj: 2000, condition_adj: -5000, garage_adj: 0, adjusted: 404000 },
]

const financier: EnrichmentFinancier = {
  total_mensuel: 2850, versement_hypo_mensuel: 2100, ratio_revenu_pct: 38.2, interpretation_couts: 'Limite',
  ratio_loyer_revenu_pct: 28.5, seuil_location: 'abordable', versement_mensuel_estime: 2100,
  ratio_mensualite_revenu_pct: 35.0, seuil_propriete: 'limite', revenu_median_menage: 74000,
  pct_proprietaires: 62, pct_locataires: 38, valeur_mediane_logement: 485000,
  ratio_dette_revenu_pct: 178, variation_dette_revenu_pct: 2.1,
  ratio_hypotheque_revenu_pct: 95, taux_epargne_pct: 6.8,
}

describe('buildAnalyseHtml', () => {
  it('includes address and heading', () => {
    const html = buildAnalyseHtml(adjs, 413000, 'PRET_REVUE', financier, '5 rue Test')
    expect(html).toContain('5 rue Test')
    expect(html).toContain('Analyse — ajustements')
  })

  it('includes conclusion value', () => {
    const html = buildAnalyseHtml(adjs, 413000, 'PRET_REVUE', financier)
    expect(html).toContain('Conclusion de valeur')
    expect(html).toContain('413')
  })

  it('includes status label', () => {
    const html = buildAnalyseHtml(adjs, 413000, 'PRET_REVUE', financier)
    expect(html).toContain('Prêt pour revue')
  })

  it('includes adjustment rows', () => {
    const html = buildAnalyseHtml(adjs, 413000, 'PRET_REVUE', financier)
    expect(html).toContain('10 rue Laval')
    expect(html).toContain('25 av. Cartier')
    expect(html).toContain('2 comparables')
  })

  it('includes financial context', () => {
    const html = buildAnalyseHtml(adjs, 413000, 'PRET_REVUE', financier)
    expect(html).toContain('Contexte financier')
    expect(html).toContain('Coût mensuel total')
    expect(html).toContain('dette / revenu')
  })

  it('handles null conclusion', () => {
    const html = buildAnalyseHtml(adjs, null, 'ASSISTANCE_DOSSIER_ACTIVE', null)
    expect(html).not.toContain('Conclusion de valeur')
    expect(html).toContain('10 rue Laval')
  })

  it('handles empty adjustments', () => {
    const html = buildAnalyseHtml([], 413000, 'PRET_REVUE', null)
    expect(html).toContain('Conclusion de valeur')
    expect(html).not.toContain('ajustements (')
  })

  it('includes OEAQ section when comparables provided', () => {
    const comps: Comparable[] = [
      { id: 'c1', rank: '1', address: '10 rue Laval', hab_m2: 100, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price: 420000, sale_date: '2024-01-01', meta: '', price: '', date: '' },
      { id: 'c2', rank: '2', address: '25 av. Cartier', hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price: 395000, sale_date: '2024-06-01', meta: '', price: '', date: '' },
      { id: 'c3', rank: '3', address: '8 boul. Rosemont', hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price: 410000, sale_date: '2025-01-01', meta: '', price: '', date: '' },
    ]
    const html = buildAnalyseHtml(adjs, 413000, 'PRET_REVUE', null, undefined, comps)
    expect(html).toContain('Conformité OEAQ')
    expect(html).toContain('Nombre minimal')
    expect(html).toContain('Récence des ventes')
  })

  it('omits OEAQ section when no comparables provided', () => {
    const html = buildAnalyseHtml(adjs, 413000, 'PRET_REVUE', null)
    expect(html).not.toContain('Conformité OEAQ')
  })

  it('includes subject context note when conclusion within range', () => {
    // adjs adjusted values: 422000 and 404000 → median 413000, conclusion at median
    const html = buildAnalyseHtml(adjs, 413000, 'PRET_REVUE', null)
    expect(html).toContain('médiane')
    expect(html).toContain('fourchette')
  })

  it('includes out-of-range warning when conclusion outside range', () => {
    // adjs range 404000–422000; conclusion 600000 is outside
    const html = buildAnalyseHtml(adjs, 600000, 'PRET_REVUE', null)
    expect(html).toContain('hors de la fourchette')
    expect(html).toContain('justification requise')
  })

  it('shows outlier note when a comparable is atypical (>15% vs median)', () => {
    // median of [422000, 404000, 700000] = 422000; 700000 → +65.7% → outlier
    const adjs3: Adjustment[] = [
      ...adjs,
      { id: 'a3', comparable_id: 'c3', comparableLabel: '99 rue Test', salePrice: 690000, surface_adj: 0, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted: 700000 },
    ]
    const html = buildAnalyseHtml(adjs3, 422000, 'PRET_REVUE', null)
    expect(html).toContain('atypique')
    expect(html).toContain('15 %')
  })

  it('omits outlier note when all values within threshold', () => {
    // adjs only 2 → detectOutlierComparables returns [] → no note
    const html = buildAnalyseHtml(adjs, 413000, 'PRET_REVUE', null)
    expect(html).not.toContain('atypique')
  })

  it('shows per-row deviation label for outlier comparable', () => {
    const adjs3: Adjustment[] = [
      ...adjs,
      { id: 'a3', comparable_id: 'c3', comparableLabel: '99 rue Test', salePrice: 690000, surface_adj: 0, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted: 700000 },
    ]
    const html = buildAnalyseHtml(adjs3, 422000, 'PRET_REVUE', null)
    expect(html).toContain('vs méd.')
  })

  it('includes adjustment profile section when adjustments have non-zero values', () => {
    // adjs have surface_adj and year_adj → profile should appear
    const html = buildAnalyseHtml(adjs, 413000, 'PRET_REVUE', null)
    expect(html).toContain('Répartition des ajustements')
    expect(html).toContain('Surface')
  })

  it('includes reconciled value line when multiple adjustments', () => {
    const html = buildAnalyseHtml(adjs, 413000, 'PRET_REVUE', null)
    expect(html).toContain('réconciliée')
    expect(html).toContain('confiance')
  })

  it('shows consistency warning when adjustments have mixed directions', () => {
    // a1: surface_adj +5000; a2: surface_adj -3000 → mixed → warning
    const mixedAdjs: Adjustment[] = [
      { id: 'a1', comparable_id: 'c1', comparableLabel: 'A', salePrice: 400000, surface_adj: 5000, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted: 405000 },
      { id: 'a2', comparable_id: 'c2', comparableLabel: 'B', salePrice: 400000, surface_adj: -3000, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted: 397000 },
    ]
    const html = buildAnalyseHtml(mixedAdjs, 401000, 'PRET_REVUE', null)
    expect(html).toContain('Cohérence des ajustements')
    expect(html).toContain('directions mixtes')
  })

  it('omits consistency section when all directions are consistent', () => {
    // all same direction per type — no mixed signals
    const consistent: Adjustment[] = [
      { id: 'a1', comparable_id: 'c1', comparableLabel: 'A', salePrice: 400000, surface_adj: 5000, year_adj: -2000, condition_adj: 0, garage_adj: 0, adjusted: 403000 },
      { id: 'a2', comparable_id: 'c2', comparableLabel: 'B', salePrice: 410000, surface_adj: 8000, year_adj: -3000, condition_adj: 0, garage_adj: 0, adjusted: 415000 },
    ]
    const html = buildAnalyseHtml(consistent, 409000, 'PRET_REVUE', null)
    expect(html).not.toContain('Cohérence des ajustements')
  })

  it('shows time adjustment rate note when comparables with different dates and prices provided', () => {
    const comps: Comparable[] = [
      { id: 'c1', rank: '1', address: '10 rue Laval', hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price: 400000, sale_date: '2024-01-01', meta: '', price: '', date: '' },
      { id: 'c2', rank: '2', address: '25 av. Cartier', hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price: 412000, sale_date: '2025-01-01', meta: '', price: '', date: '' },
    ]
    const html = buildAnalyseHtml(adjs, 413000, 'PRET_REVUE', null, undefined, comps)
    expect(html).toContain("Taux implicite d'appréciation")
    expect(html).toContain('%/an')
    expect(html).toContain('confiance')
  })

  it('omits time rate note when no comparables provided', () => {
    const html = buildAnalyseHtml(adjs, 413000, 'PRET_REVUE', null)
    expect(html).not.toContain("Taux implicite d'appréciation")
  })

  it('shows reconciliation weight % for each comparable in print table', () => {
    // 2 comps → weights computed → "poids X %" sub-line in Prix ajusté cell
    const html = buildAnalyseHtml(adjs, 413000, 'PRET_REVUE', null)
    expect(html).toContain('poids')
    expect(html).toContain('%')
  })

  it('shows CV dispersion note in conclusion section when ≥2 adjustments', () => {
    const html = buildAnalyseHtml(adjs, 413000, 'PRET_REVUE', null)
    expect(html).toContain('Dispersion')
    expect(html).toContain('CV')
    expect(html).toContain('cohésion')
  })

  it('shows sensitivity table when ≥3 adjustments', () => {
    const adjs3: Adjustment[] = [
      ...adjs,
      { id: 'a3', comparable_id: 'c3', comparableLabel: '8 boul. Rosemont', salePrice: 430000, surface_adj: -5000, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted: 425000 },
    ]
    const html = buildAnalyseHtml(adjs3, 415000, 'PRET_REVUE', null)
    expect(html).toContain('Sensibilité de la réconciliation')
    expect(html).toContain('Sans ')
    expect(html).toContain('Exclusion')
  })

  it('omits sensitivity table when fewer than 3 adjustments', () => {
    const html = buildAnalyseHtml(adjs, 413000, 'PRET_REVUE', null)
    expect(html).not.toContain('Sensibilité de la réconciliation')
  })

  it('shows comparable ranking table when comparables and adjustments provided', () => {
    const comps: Comparable[] = [
      { id: 'c1', rank: '1', address: '10 rue Laval', hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price: 420000, sale_date: '2024-01-01', meta: '', price: '', date: '' },
      { id: 'c2', rank: '2', address: '25 av. Cartier', hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price: 395000, sale_date: '2024-06-01', meta: '', price: '', date: '' },
    ]
    const html = buildAnalyseHtml(adjs, 413000, 'PRET_REVUE', null, undefined, comps)
    expect(html).toContain('Classement des comparables')
    expect(html).toContain('#1')
    expect(html).toContain('Qualité')
  })

  it('omits ranking table when no comparables provided', () => {
    const html = buildAnalyseHtml(adjs, 413000, 'PRET_REVUE', null)
    expect(html).not.toContain('Classement des comparables')
  })

  it('shows structured conclusion section with reconciledValue and reliability', () => {
    const html = buildAnalyseHtml(adjs, 413000, 'PRET_REVUE', null)
    expect(html).toContain('Conclusion structurée')
    expect(html).toContain('Valeur réconciliée')
    expect(html).toContain('Fiabilité globale')
    expect(html).toContain('Intervalle')
  })
})
