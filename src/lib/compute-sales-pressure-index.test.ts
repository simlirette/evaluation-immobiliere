import { describe, it, expect } from 'vitest'
import { computeSalesPressureIndex } from './compute-sales-pressure-index'
import type { EnrichmentMarche } from '@/types'

function mkMarche(overrides: Partial<EnrichmentMarche>): EnrichmentMarche {
  return {
    score_marche: null, tension_locative: null, marche_interpretation: null,
    taux_inoccupation_pct: null, nhpi_variation_pct: null, taux_hypo_5ans_pct: null,
    taux_directeur_pct: null, taux_chomage_pct: null, taux_emploi_pct: null,
    taux_participation_pct: null, inoccupation_annee: null, nhpi_indice: null,
    mises_en_chantier_12m: null, permis_unites_12m: null, permis_variation_6m_pct: null,
    population: null, population_variation_pct: null, completions_12m: null,
    unites_en_construction: null, taux_absorption_pct: null, unites_absorbees_total: null,
    variation_absorbees_pct_4q: null, ipc_variation_logement_pct: null, ipc_logement_indice: null,
    ...overrides,
  } as EnrichmentMarche
}

describe('computeSalesPressureIndex', () => {
  it('returns null when no signals available', () => {
    expect(computeSalesPressureIndex(mkMarche({}))).toBeNull()
  })

  it('regime vendeur when index >= 60', () => {
    // absorption 100% → index 100
    const r = computeSalesPressureIndex(mkMarche({ taux_absorption_pct: 100 }))!
    expect(r.regime).toBe('vendeur')
    expect(r.index).toBe(100)
  })

  it('regime acheteur when index < 40', () => {
    // absorption 0% → index 0
    const r = computeSalesPressureIndex(mkMarche({ taux_absorption_pct: 0 }))!
    expect(r.regime).toBe('acheteur')
    expect(r.index).toBe(0)
  })

  it('regime équilibré when 40 <= index < 60', () => {
    // absorption 50% → index 50
    const r = computeSalesPressureIndex(mkMarche({ taux_absorption_pct: 50 }))!
    expect(r.regime).toBe('équilibré')
    expect(r.index).toBe(50)
  })

  it('vacancy 0% maps to 100 signal (full seller pressure)', () => {
    const r = computeSalesPressureIndex(mkMarche({ taux_inoccupation_pct: 0 }))!
    expect(r.index).toBe(100)
    expect(r.regime).toBe('vendeur')
  })

  it('vacancy 8%+ maps to 0 signal (full buyer pressure)', () => {
    const r = computeSalesPressureIndex(mkMarche({ taux_inoccupation_pct: 8 }))!
    expect(r.index).toBe(0)
  })

  it('score_marche 10 maps to index 100', () => {
    const r = computeSalesPressureIndex(mkMarche({ score_marche: 10 }))!
    expect(r.index).toBe(100)
  })

  it('averages all three signals when all present', () => {
    // absorption=100→100, vacancy=0%→100, score=10→100 → avg=100
    const r = computeSalesPressureIndex(mkMarche({ taux_absorption_pct: 100, taux_inoccupation_pct: 0, score_marche: 10 }))!
    expect(r.index).toBe(100)
    expect(r.signalCount).toBe(3)
  })

  it('signalCount reflects used signals', () => {
    const r = computeSalesPressureIndex(mkMarche({ taux_absorption_pct: 80 }))!
    expect(r.signalCount).toBe(1)
  })

  it('label matches regime', () => {
    const seller = computeSalesPressureIndex(mkMarche({ taux_absorption_pct: 100 }))!
    expect(seller.label).toContain('vendeurs')
    const buyer = computeSalesPressureIndex(mkMarche({ taux_absorption_pct: 0 }))!
    expect(buyer.label).toContain('acheteurs')
    const balanced = computeSalesPressureIndex(mkMarche({ taux_absorption_pct: 50 }))!
    expect(balanced.label).toContain('équilibré')
  })

  it('clamps out-of-range inputs', () => {
    const r = computeSalesPressureIndex(mkMarche({ taux_absorption_pct: 150 }))!
    expect(r.index).toBe(100)
    const r2 = computeSalesPressureIndex(mkMarche({ taux_absorption_pct: -10 }))!
    expect(r2.index).toBe(0)
  })
})
