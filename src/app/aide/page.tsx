'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import { createClient } from '@/lib/supabase/client'

const SECTIONS = [
  { id: 'survol', label: 'Survol de l\'application' },
  { id: 'creer', label: 'Créer un dossier' },
  { id: 'etapes', label: 'Les 5 étapes' },
  { id: 'agent', label: 'L\'agent IA' },
  { id: 'bibli', label: 'Bibliothèque & modèles' },
  { id: 'oeaq', label: 'Conformité OEAQ' },
  { id: 'raccourcis', label: 'Raccourcis clavier' },
  { id: 'faq', label: 'FAQ' },
  { id: 'contact', label: 'Contact & support' },
]

const FAQ_ITEMS = [
  {
    q: 'Les données générées par l\'agent ont-elles valeur officielle ?',
    a: 'Non. Toutes les données produites par Éval Immo sont à titre indicatif et ne constituent pas une opinion professionnelle certifiée. La validation et la signature d\'un évaluateur agréé (É.A.) membre de l\'OEAQ reste obligatoire avant toute diffusion.',
  },
  {
    q: 'Quelles sources l\'agent utilise-t-il pour l\'enrichissement ?',
    a: 'L\'agent consulte les registres publics québécois (JLR, cadastre, rôle d\'évaluation), les transactions Centris/MLS disponibles, et les indicateurs macroéconomiques (Statistique Canada, BCC). La couverture de chaque source est indiquée dans l\'onglet Dossier après enrichissement.',
  },
  {
    q: 'Mes données sont-elles protégées conformément à la Loi 25 ?',
    a: 'Oui. Éval Immo héberge toutes les données sur des serveurs canadiens (Montréal). Les données clients sont chiffrées au repos et en transit. Aucune donnée personnelle n\'est partagée avec des tiers. Notre politique de confidentialité est conforme aux exigences de la Loi 25 (LPRPDE québécoise).',
  },
  {
    q: 'Puis-je importer un dossier existant ?',
    a: 'Oui. Depuis la page Dossiers, cliquez sur « Importer » pour téléverser un fichier PDF, Word ou Excel. L\'agent extraira automatiquement les informations disponibles et les organisera dans le dossier.',
  },
  {
    q: 'Comment modifier les ajustements de comparables ?',
    a: 'Dans l\'onglet Analyse, cliquez sur « Modifier les ajustements ». Vous pouvez ajuster les quatre composantes (superficie, année, condition, stationnement) pour chaque comparable. Les modifications sont sauvegardées dans l\'artefact runtime et reflétées dans la conclusion.',
  },
  {
    q: 'Le rapport PDF est-il conforme aux normes OEAQ ?',
    a: 'Le rapport généré est conforme au format abrégé ou complet de l\'OEAQ selon le modèle choisi. La checklist de conformité est disponible dans l\'onglet Analyse. La signature électronique de l\'évaluateur agréé reste requise avant toute transmission officielle.',
  },
]

const SHORTCUTS = [
  { keys: 'Ctrl + 1', action: 'Onglet Dossier' },
  { keys: 'Ctrl + 2', action: 'Onglet Marché' },
  { keys: 'Ctrl + 3', action: 'Onglet Analyse' },
  { keys: 'Ctrl + 4', action: 'Onglet Synthèse' },
  { keys: 'Ctrl + 5', action: 'Onglet Rapport' },
  { keys: '?', action: 'Afficher l\'aide des raccourcis' },
  { keys: 'Entrée', action: 'Envoyer un message à l\'agent' },
]

const ETAPES = [
  { num: '01', titre: 'Dossier', desc: 'Saisie de l\'adresse, du type de propriété et du mandat. L\'agent enrichit automatiquement les données publiques (cadastre, rôle, localisation).' },
  { num: '02', titre: 'Marché', desc: 'Recherche et sélection des ventes comparables. Filtrage, tri, indicateurs de qualité et de marché. Détection de doublons et alertes OEAQ.' },
  { num: '03', titre: 'Analyse', desc: 'Tableau d\'ajustements, réconciliation des approches (comparaison, coût, revenus), pondération et conclusion de valeur proposée.' },
  { num: '04', titre: 'Synthèse', desc: 'Tableau de bord complet : score global, alertes critiques, indicateurs financiers, projection de valeur et narratif de synthèse.' },
  { num: '05', titre: 'Rapport', desc: 'Génération du brouillon de rapport, revue interne, export PDF signé. Historique des versions et traçabilité OEAQ.' },
]

function AccordionItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false)
  return (
    <div style={{ borderBottom: '1px solid var(--rule-soft)' }}>
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full text-left flex items-center justify-between py-4 gap-4"
      >
        <span className="text-[14px] font-medium" style={{ color: 'var(--ink)' }}>{q}</span>
        <span
          className="flex-shrink-0 text-[18px] transition-transform"
          style={{ color: 'var(--ink-mute)', transform: open ? 'rotate(45deg)' : 'none' }}
        >+</span>
      </button>
      {open && (
        <p className="text-[13px] pb-4 leading-relaxed" style={{ color: 'var(--ink-mute)' }}>{a}</p>
      )}
    </div>
  )
}

export default function AidePage() {
  const router = useRouter()
  const [activeSection, setActiveSection] = useState('survol')
  const [search, setSearch] = useState('')

  async function handleSignOut() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push('/login')
  }

  const visibleSections = search
    ? SECTIONS.filter(s => s.label.toLowerCase().includes(search.toLowerCase()))
    : SECTIONS

  const renderContent = () => {
    switch (activeSection) {
      case 'survol':
        return (
          <section className="panel">
            <div className="panel-head"><h2 className="panel-title">Survol de l'application</h2></div>
            <p className="text-[14px] leading-relaxed mb-6" style={{ color: 'var(--ink-mute)' }}>
              Éval Immo est un environnement de travail intégré pour les évaluateurs agréés du Québec.
              Il réunit en un seul espace les cinq étapes du processus d'évaluation immobilière,
              de la saisie du dossier jusqu'à la génération du rapport certifiable.
            </p>
            <div className="flex flex-col gap-3">
              {ETAPES.map(e => (
                <div
                  key={e.num}
                  className="flex gap-4 p-4 rounded-[var(--r-md)]"
                  style={{ background: 'var(--paper-2)', border: '1px solid var(--rule-soft)' }}
                >
                  <div
                    className="w-8 h-8 rounded-full flex items-center justify-center text-[12px] font-bold flex-shrink-0"
                    style={{ background: 'var(--navy)', color: 'var(--paper-hi)' }}
                  >
                    {e.num}
                  </div>
                  <div>
                    <div className="text-[13px] font-semibold mb-1" style={{ color: 'var(--ink)' }}>{e.titre}</div>
                    <div className="text-[12px]" style={{ color: 'var(--ink-mute)' }}>{e.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )
      case 'creer':
        return (
          <section className="panel">
            <div className="panel-head"><h2 className="panel-title">Créer un dossier</h2></div>
            <ol className="flex flex-col gap-4">
              {[
                { n: 1, titre: 'Cliquez « + Nouveau dossier »', desc: 'Depuis la page Dossiers ou le menu de navigation latéral.' },
                { n: 2, titre: 'Renseignez la propriété', desc: 'Adresse, type de bien, secteur, superficie et année de construction (optionnel).' },
                { n: 3, titre: 'Identifiez le commanditaire', desc: 'Nom, organisation, fin d\'évaluation, honoraires et évaluateur signataire.' },
                { n: 4, titre: 'Ajoutez des comparables (optionnel)', desc: 'Vous pouvez ajouter des ventes connues avant le lancement ou les laisser à l\'agent.' },
              ].map(step => (
                <li key={step.n} className="flex gap-4">
                  <span
                    className="w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold flex-shrink-0 mt-0.5"
                    style={{ background: 'var(--navy-tint)', color: 'var(--navy)' }}
                  >{step.n}</span>
                  <div>
                    <div className="text-[13px] font-medium" style={{ color: 'var(--ink)' }}>{step.titre}</div>
                    <div className="text-[12px] mt-0.5" style={{ color: 'var(--ink-mute)' }}>{step.desc}</div>
                  </div>
                </li>
              ))}
            </ol>
          </section>
        )
      case 'etapes':
        return (
          <section className="panel">
            <div className="panel-head"><h2 className="panel-title">Les 5 étapes</h2></div>
            <div className="flex flex-col gap-5">
              {ETAPES.map(e => (
                <div key={e.num}>
                  <div className="eyebrow mb-1">Étape {e.num} — {e.titre}</div>
                  <p className="text-[13px] leading-relaxed" style={{ color: 'var(--ink-mute)' }}>{e.desc}</p>
                  <div style={{ borderBottom: '1px solid var(--rule-soft)', marginTop: '1rem' }} />
                </div>
              ))}
            </div>
          </section>
        )
      case 'agent':
        return (
          <section className="panel">
            <div className="panel-head"><h2 className="panel-title">L'agent IA</h2></div>
            <p className="text-[14px] leading-relaxed mb-4" style={{ color: 'var(--ink-mute)' }}>
              Chaque onglet du dossier dispose d'un agent spécialisé accessible via la barre de saisie en bas de l'écran.
              L'agent peut enrichir les données, rédiger des narratifs, valider la conformité et répondre à vos questions.
            </p>
            <div
              className="rounded-[var(--r-md)] p-4 mb-4"
              style={{ background: 'rgba(138,48,48,.06)', border: '1px solid rgba(138,48,48,.12)' }}
            >
              <div className="text-[12px] font-semibold mb-1" style={{ color: 'var(--oxblood)' }}>Limites importantes</div>
              <ul className="text-[12px] flex flex-col gap-1" style={{ color: 'var(--ink-mute)' }}>
                <li>· L'agent ne certifie pas les valeurs — la signature É.A. reste obligatoire</li>
                <li>· Les données publiques peuvent être incomplètes ou désactualisées</li>
                <li>· Les narratifs générés doivent être relus et validés par l'évaluateur</li>
              </ul>
            </div>
            <div className="eyebrow mb-2">Suggestions rapides par onglet</div>
            {(['Dossier', 'Marché', 'Analyse', 'Synthèse', 'Rapport'] as const).map(tab => (
              <div key={tab} className="flex items-start gap-3 py-2" style={{ borderBottom: '1px solid var(--rule-soft)' }}>
                <span className="text-[12px] font-medium w-16 flex-shrink-0" style={{ color: 'var(--navy)' }}>{tab}</span>
                <span className="text-[12px]" style={{ color: 'var(--ink-mute)' }}>Suggestions contextuelles disponibles dans la barre de chat</span>
              </div>
            ))}
          </section>
        )
      case 'bibli':
        return (
          <section className="panel">
            <div className="panel-head"><h2 className="panel-title">Bibliothèque & modèles</h2></div>
            <p className="text-[14px] leading-relaxed mb-4" style={{ color: 'var(--ink-mute)' }}>
              La bibliothèque centralise les ventes comparables, les indicateurs de marché, les coûts de construction
              et les taux de capitalisation pour la grande région de Montréal.
            </p>
            <div className="eyebrow mb-3">Modèles de rapport</div>
            <p className="text-[13px] leading-relaxed" style={{ color: 'var(--ink-mute)' }}>
              Les modèles définissent le format du rapport final (abrégé ou complet), les sections incluses
              et les méthodes d'évaluation requises. Vous pouvez créer un nouveau dossier directement depuis
              un modèle pour préremplir ces paramètres.
            </p>
          </section>
        )
      case 'oeaq':
        return (
          <section className="panel">
            <div className="panel-head"><h2 className="panel-title">Conformité OEAQ</h2></div>
            <p className="text-[14px] leading-relaxed mb-4" style={{ color: 'var(--ink-mute)' }}>
              Éval Immo vérifie automatiquement les règles de conformité de l'Ordre des évaluateurs agréés du Québec
              dans l'onglet Analyse de chaque dossier.
            </p>
            <div className="flex flex-col gap-2">
              {[
                'Minimum 3 ventes comparables pour les propriétés résidentielles',
                'Ajustements bruts ≤ 15 % par ligne, ≤ 25 % au total par comparable',
                'Conclusion encadrée entre les valeurs indiquées des comparables',
                'Identification complète de l\'évaluateur et du commanditaire',
                'Date de valeur distincte de la date de rapport',
                'Traçabilité des sources (numéros Centris, JLR, registre)',
              ].map((rule, i) => (
                <div key={i} className="flex gap-2 text-[13px]" style={{ color: 'var(--ink-mute)' }}>
                  <span style={{ color: 'var(--verdigris)', flexShrink: 0 }}>✓</span>
                  {rule}
                </div>
              ))}
            </div>
          </section>
        )
      case 'raccourcis':
        return (
          <section className="panel">
            <div className="panel-head"><h2 className="panel-title">Raccourcis clavier</h2></div>
            <div
              className="rounded-[var(--r-md)] overflow-hidden"
              style={{ border: '1px solid var(--rule)' }}
            >
              <div
                className="grid px-4 py-2 text-[11px] font-medium uppercase tracking-[.05em]"
                style={{ gridTemplateColumns: '150px 1fr', color: 'var(--ink-faint)', background: 'var(--paper)' }}
              >
                <span>Raccourci</span><span>Action</span>
              </div>
              {SHORTCUTS.map((s, i) => (
                <div
                  key={i}
                  className="grid px-4 py-3"
                  style={{ gridTemplateColumns: '150px 1fr', borderTop: '1px solid var(--rule-soft)' }}
                >
                  <span
                    className="text-[12px] font-mono font-semibold px-2 py-0.5 rounded inline-block w-fit"
                    style={{ background: 'var(--paper-2)', color: 'var(--ink)', border: '1px solid var(--rule)' }}
                  >
                    {s.keys}
                  </span>
                  <span className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>{s.action}</span>
                </div>
              ))}
            </div>
          </section>
        )
      case 'faq':
        return (
          <section className="panel">
            <div className="panel-head"><h2 className="panel-title">FAQ</h2></div>
            <div>
              {FAQ_ITEMS.map((item, i) => (
                <AccordionItem key={i} q={item.q} a={item.a} />
              ))}
            </div>
          </section>
        )
      case 'contact':
        return (
          <section className="panel">
            <div className="panel-head"><h2 className="panel-title">Contact & support</h2></div>
            <div className="flex flex-col gap-4">
              <div
                className="rounded-[var(--r-md)] p-4"
                style={{ background: 'var(--paper-2)', border: '1px solid var(--rule-soft)' }}
              >
                <div className="text-[13px] font-medium mb-1" style={{ color: 'var(--ink)' }}>Support technique</div>
                <div className="text-[12px]" style={{ color: 'var(--ink-mute)' }}>Lundi au vendredi · 8h00–17h00 EST</div>
                <div className="text-[13px] mt-2" style={{ color: 'var(--navy)' }}>support@eval-immo.qc.ca</div>
              </div>
              <div
                className="rounded-[var(--r-md)] p-4"
                style={{ background: 'var(--paper-2)', border: '1px solid var(--rule-soft)' }}
              >
                <div className="text-[13px] font-medium mb-1" style={{ color: 'var(--ink)' }}>Formation & démonstration</div>
                <div className="text-[12px]" style={{ color: 'var(--ink-mute)' }}>Formations de groupe disponibles pour les cabinets de 3 évaluateurs et plus.</div>
                <button className="btn secondary btn-sm mt-3">Planifier une démo</button>
              </div>
            </div>
          </section>
        )
      default:
        return null
    }
  }

  return (
    <div className="relative w-full h-screen overflow-hidden flex" style={{ background: 'var(--paper)' }}>
      <Sidebar onSignOut={handleSignOut} />

      <div className="main-content flex overflow-hidden">
        {/* Section nav */}
        <nav
          className="w-[220px] flex-shrink-0 flex flex-col pt-8 px-4 border-r overflow-y-auto"
          style={{ borderRightColor: 'var(--rule-soft)' }}
        >
          <div className="eyebrow mb-3">Aide</div>
          <div className="mb-4">
            <input
              type="search"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Rechercher…"
              className="w-full text-[12px] px-3 py-1.5 rounded-[var(--r-pill)]"
              style={{ background: 'var(--paper-2)', border: '1px solid var(--rule)', color: 'var(--ink)', fontFamily: 'var(--font-sans)' }}
            />
          </div>
          <div className="flex flex-col gap-0.5">
            {visibleSections.map(s => (
              <button
                key={s.id}
                onClick={() => { setActiveSection(s.id); setSearch('') }}
                className="text-left px-3 py-2 text-[13px] rounded-[var(--r-md)] transition-colors"
                style={{
                  color: activeSection === s.id ? 'var(--navy)' : 'var(--ink-mute)',
                  background: activeSection === s.id ? 'var(--navy-tint)' : 'transparent',
                  fontWeight: activeSection === s.id ? 500 : 400,
                }}
              >
                {s.label}
              </button>
            ))}
          </div>
        </nav>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-10 py-8">
          <div className="max-w-[680px] flex flex-col gap-5">
            {renderContent()}
          </div>
        </div>
      </div>
    </div>
  )
}
