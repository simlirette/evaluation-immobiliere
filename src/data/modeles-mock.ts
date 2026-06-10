/* Modèles — données du design handoff (modeles.jsx), copie verbatim.
   À remplacer par un endpoint backend (gabarits réels) en phase ultérieure. */

export type ModeleCat = 'résidentiel' | 'commercial' | 'spécialisé' | 'restreint'

export interface ModeleMock {
  id: string
  title: string
  cat: ModeleCat
  desc: string
  sections: number
  pages: number
  docs: number
  used: number
  last: string
  norm: string
}

export const MODELES: ModeleMock[] = [
  {
    id: 'hypo-res',
    title: 'Hypothécaire — Résidentiel',
    cat: 'résidentiel',
    desc: 'Rapport narratif complet conforme aux exigences des prêteurs hypothécaires. Approches comparative et coût, attestation OEAQ.',
    sections: 8, pages: 32, docs: 6,
    used: 28, last: '12 mai 2026',
    norm: 'OEAQ — Rapport narratif',
  },
  {
    id: 'pre-vente',
    title: 'Pré-vente — Résidentiel',
    cat: 'résidentiel',
    desc: 'Évaluation orientée vendeur. Étude de marché élargie, fourchette de prix de mise en vente, recommandations stratégiques.',
    sections: 6, pages: 22, docs: 4,
    used: 14, last: '28 avril 2026',
    norm: 'OEAQ — Rapport narratif',
  },
  {
    id: 'successoral',
    title: 'Successoral & donation',
    cat: 'résidentiel',
    desc: 'Valeur marchande à une date passée précise. Justification de la date de valeur, comparables historiques, attestation notariale.',
    sections: 7, pages: 26, docs: 5,
    used: 9, last: '3 mars 2026',
    norm: 'OEAQ — Rapport narratif',
  },
  {
    id: 'litige',
    title: 'Litige & expropriation',
    cat: 'spécialisé',
    desc: "Rapport d'expertise judiciaire. Analyse détaillée des trois approches, démonstration méthodologique, annexes substantielles.",
    sections: 11, pages: 64, docs: 12,
    used: 5, last: '18 février 2026',
    norm: "OEAQ — Rapport d'expert",
  },
  {
    id: 'revenus',
    title: 'Acquisition — Immeuble à revenus',
    cat: 'commercial',
    desc: 'Approche par les revenus en méthode dominante. État des revenus et dépenses normalisé, taux de capitalisation justifié.',
    sections: 9, pages: 42, docs: 8,
    used: 7, last: '22 avril 2026',
    norm: 'OEAQ — Rapport narratif',
  },
  {
    id: 'avis',
    title: 'Avis de valeur restreint',
    cat: 'restreint',
    desc: 'Rapport court à portée limitée. Une seule approche, hypothèses explicites. Pour usage interne ou validation rapide.',
    sections: 4, pages: 8, docs: 2,
    used: 18, last: '26 mai 2026',
    norm: 'OEAQ — Avis de valeur',
  },
]
