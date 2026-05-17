import { describe, it, expect } from 'vitest'
import { buildSyntheseHtml } from './synthese-html'
import type { Enrichment } from '@/types'

const base: Enrichment = {
  score_global: { score: 7.5, grade: 'B', recommandation: 'Bon potentiel' },
  alertes: { liste: [{ niveau: 'critique', categorie: 'zone_inondable', message: 'En zone 0-20 ans' }], nb_critiques: 1, nb_attention: 0, nb_info: 0 },
  score_investissement: { score: 6.0, recommandation: 'Potentiel modéré' },
  indice_qualite_vie: { score: 8.2, interpretation: 'Bon' },
  score_risque: { score: 4.1, categorie: 'risque élevé' },
  projection_valeur: { valeur_base: 500000, taux_base_pct: 2.5, an1: 512500, an3: 538443, an5: 565705 },
  rendement_locatif: { taux_brut_pct: 5.2, taux_net_pct: 3.38, interpretation: 'Acceptable' },
  valeur_indicative: { valeur: 498000, fiabilite: 'Bonne' },
  taxes_municipales: { taux_pct: 0.701, annuel: 3491 },
  ratio_prix_loyer: { ratio: 18.5, signal: 'Équilibré' },
  vetuste_batiment: { age_ans: 32, categorie: 'mi-vie', depreciation_pct: 40 },
  cout_renovation: { cout_min: 30000, cout_max: 60000, cout_median: 45000, type_travaux: 'Rénovations majeures' },
  marche: { score_marche: 7.1, tension_locative: 'tendu', marche_interpretation: 'Marché dynamique', taux_inoccupation_pct: null, inoccupation_annee: null, nhpi_variation_pct: null, nhpi_indice: null, taux_directeur_pct: null, taux_hypo_5ans_pct: null, mises_en_chantier_12m: null, permis_unites_12m: null, permis_variation_6m_pct: null, taux_chomage_pct: null, taux_emploi_pct: null, taux_participation_pct: null, population: null, population_variation_pct: null, completions_12m: null, unites_en_construction: null, taux_absorption_pct: null, unites_absorbees_total: null, variation_absorbees_pct_4q: null, ipc_variation_logement_pct: null, ipc_logement_indice: null },
  financier: null,
  localisation: null,
}

describe('buildSyntheseHtml', () => {
  it('includes address and grade', () => {
    const html = buildSyntheseHtml(base, '123 rue Test')
    expect(html).toContain('123 rue Test')
    expect(html).toContain('B')
    expect(html).toContain('/ 10')
  })

  it('includes alerte critique', () => {
    const html = buildSyntheseHtml(base)
    expect(html).toContain('CRITIQUE')
    expect(html).toContain('En zone 0-20 ans')
  })

  it('includes score rows', () => {
    const html = buildSyntheseHtml(base)
    expect(html).toContain('Investissement')
    expect(html).toContain('Qualité de vie')
    expect(html).toContain('Marché')
    expect(html).toContain('Risque')
  })

  it('includes projection table', () => {
    const html = buildSyntheseHtml(base)
    expect(html).toContain('1 an')
    expect(html).toContain('3 ans')
    expect(html).toContain('5 ans')
    expect(html).toContain('500')
  })

  it('includes key metrics', () => {
    const html = buildSyntheseHtml(base)
    expect(html).toContain('Valeur indicative')
    expect(html).toContain('Taxes municipales')
    expect(html).toContain('Ratio prix/loyer')
    expect(html).toContain('Rénovation estimée')
  })

  it('handles missing optional fields gracefully', () => {
    const minimal: Enrichment = { ...base, projection_valeur: null, cout_renovation: null, vetuste_batiment: null, taxes_municipales: null, ratio_prix_loyer: null }
    const html = buildSyntheseHtml(minimal)
    expect(html).toContain('B') // grade still present
    expect(html).not.toContain('Projection de valeur')
  })

  it('handles null score_global', () => {
    const empty: Enrichment = { ...base, score_global: null, alertes: null, score_investissement: null, indice_qualite_vie: null, score_risque: null, projection_valeur: null }
    const html = buildSyntheseHtml(empty)
    expect(html).toBeDefined()
    expect(html).not.toContain('undefined')
  })
})
