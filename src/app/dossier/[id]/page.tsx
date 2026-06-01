'use client'

import { useState, useEffect, Suspense, useCallback } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import Stepper from '@/components/layout/Stepper'
import Toast from '@/components/shared/Toast'
import ShortcutHelp from '@/components/shared/ShortcutHelp'
import SideCard from '@/components/dossier/SideCard'
import DossierPanel from '@/components/panels/DossierPanel'
import MarchePanel from '@/components/panels/MarchePanel'
import AnalysePanel from '@/components/panels/AnalysePanel'
import SynthesePanel from '@/components/panels/SynthesePanel'
import RapportPanel from '@/components/panels/RapportPanel'
import { fetchAppState, fetchRuntimeEnrichment } from '@/lib/runtime-api'
import { createClient } from '@/lib/supabase/client'
import type { TabId } from '@/types'

const VALID_TABS: TabId[] = ['dossier', 'marche', 'analyse', 'synthese', 'rapport']

function formatPropertyType(pt: string): string {
  const map: Record<string, string> = {
    residentiel_unifamilial: 'Unifamiliale',
    condo: 'Condo',
    duplex: 'Duplex',
    triplex: 'Triplex',
    quadruplex: 'Quadruplex',
    commercial: 'Commercial',
    terrain: 'Terrain',
    autre: 'Autre',
  }
  return map[pt] ?? pt
}

function formatFinEval(fe: string): string {
  const map: Record<string, string> = {
    hypothecaire: 'Hypothécaire',
    succession: 'Succession',
    litige: 'Litige judiciaire',
    assurance: 'Valeur assurable',
    commercial: 'Investissement commercial',
    expropriation: 'Expropriation',
    autre: 'Autre',
  }
  return map[fe] ?? fe
}

function formatMandatType(mt: string): string {
  const map: Record<string, string> = {
    residentiel_standard: 'Résidentiel standard',
    residentiel_rural: 'Résidentiel rural',
    commercial: 'Commercial',
    multilogement: 'Multilogement',
    terrain: 'Terrain',
    industriel: 'Industriel',
    special: 'Propriété spéciale',
  }
  return map[mt] ?? mt
}

interface DossierMeta {
  propertyType: string
  neighborhood: string
  commanditaire: { nom: string; organisation: string; fin_evaluation: string } | null
  mandat: { mandat_type: string } | null
  docCount: number
}

function DossierShellInner() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const searchParams = useSearchParams()

  const rawTab = searchParams.get('tab') as TabId | null
  const activeTab: TabId = rawTab && VALID_TABS.includes(rawTab) ? rawTab : 'dossier'

  const [activeDossierId, setActiveDossierId] = useState(params.id)
  const [currentDossierName, setCurrentDossierName] = useState(params.id)
  const [dossierId, setDossierId] = useState<string | null>(null)
  const [isNew] = useState(params.id === 'nouveau')
  const [visible, setVisible] = useState(true)
  const [reportReady, setReportReady] = useState(false)
  const [syntheseCritiques, setSyntheseCritiques] = useState(0)
  const [toast, setToast] = useState<string | null>(null)
  const dismissToast = useCallback(() => setToast(null), [])
  const [showHelp, setShowHelp] = useState(false)
  const [dossierMeta, setDossierMeta] = useState<DossierMeta | null>(null)

  useEffect(() => {
    if (params.id === 'nouveau') return
    setActiveDossierId(params.id)
    fetchAppState(params.id)
      .then(app => {
        const d = app.active?.dossier
        if (d) {
          setCurrentDossierName(d.address)
          setDossierId(d.id)
          setDossierMeta({
            propertyType: d.property_type,
            neighborhood: d.neighborhood,
            commanditaire: app.active?.commanditaire ?? null,
            mandat: app.active?.mandat
              ? { mandat_type: app.active.mandat.mandat_type }
              : null,
            docCount: app.active?.documents?.length ?? 0,
          })
        } else {
          router.push('/dossiers')
        }
      })
      .catch(() => router.push('/dossiers'))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id])

  useEffect(() => {
    if (activeTab === 'rapport') setReportReady(false)
  }, [activeTab])

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === '?') { setShowHelp(h => !h); return }
      if (!e.ctrlKey && !e.metaKey) return
      const map: Record<string, TabId> = { '1': 'dossier', '2': 'marche', '3': 'analyse', '4': 'synthese', '5': 'rapport' }
      const tab = map[e.key]
      if (!tab) return
      e.preventDefault()
      setTab(tab)
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeDossierId])

  function setTab(tab: TabId) {
    setVisible(false)
    setTimeout(() => {
      router.replace(`/dossier/${activeDossierId}?tab=${tab}`)
      setVisible(true)
    }, 180)
  }

  async function handleSignOut() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push('/login')
  }

  const dossierLabel = isNew ? 'Nouveau dossier' : (currentDossierName || params.id)

  return (
    <div className="relative w-full h-screen overflow-hidden flex" style={{ background: 'var(--paper)' }}>
      <Sidebar
        onSignOut={handleSignOut}
        currentDossierAddress={isNew ? null : currentDossierName}
      />

      <div className="main-content flex flex-col overflow-hidden">
        {/* Topbar */}
        <div className="topbar pb-0">
          <div className="flex items-start justify-between gap-4 mb-3">
            <div>
              <h1 className="dossier-h1">{dossierLabel}</h1>
              <div
                className="text-[13.5px] mt-1"
                style={{ color: 'var(--ink-mute)', fontFamily: 'var(--font-sans)' }}
              >
                {dossierMeta
                  ? `${dossierMeta.neighborhood} · ${formatPropertyType(dossierMeta.propertyType)}`
                  : '\u00a0'}
              </div>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0 pt-1">
              <button
                className="btn ghost btn-sm"
                onClick={() => window.print()}
              >
                Imprimer
              </button>
              <button
                className="btn secondary btn-sm"
                onClick={() => {
                  navigator.clipboard.writeText(window.location.href)
                    .then(() => setToast('Lien copié dans le presse-papiers'))
                    .catch(() => setToast('Impossible de copier le lien'))
                }}
              >
                Partager
              </button>
              <button
                className="btn accent btn-sm"
                onClick={() => setTab('dossier')}
              >
                Reprendre
              </button>
            </div>
          </div>

          {/* Stepper centré par CSS (justify-content: center dans .stepper) */}
          <Stepper activeTab={activeTab} onTabChange={setTab} />
        </div>

        {/* Body — overflow-hidden sur onglet dossier (DossierPanel gère son propre scroll + ChatInput fixe) */}
        <div
          className={`flex-1 transition-[opacity,transform] duration-200 ${['dossier','marche','analyse','rapport'].includes(activeTab) ? 'overflow-hidden' : 'overflow-y-auto'}`}
          style={{
            opacity: visible ? 1 : 0,
            transform: visible ? 'translateY(0)' : 'translateY(5px)',
          }}
        >
          <div
            className={`gap-7 px-8 pt-6 ${['dossier','marche','analyse','rapport'].includes(activeTab) ? 'h-full flex' : 'grid pb-36'}`}
            style={{ gridTemplateColumns: !['dossier','marche','analyse','rapport'].includes(activeTab) ? 'minmax(0,1fr) 300px' : undefined }}
          >
            {/* Main panel column */}
            <div className={['dossier','marche','analyse','rapport'].includes(activeTab) ? 'flex-1 min-w-0 h-full overflow-hidden' : ''}>
              {/* DossierPanel always mounted — keeps pipeline polling alive */}
              <div className={activeTab === 'dossier' ? 'h-full flex flex-col' : 'hidden'}>
                <DossierPanel
                  isNew={isNew}
                  dossierId={dossierId}
                  onPipelineComplete={() => {
                    setReportReady(true)
                    setToast('Analyse terminée — rapport disponible')
                    if (dossierId) {
                      fetchRuntimeEnrichment(dossierId).then(e => {
                        setSyntheseCritiques(e?.alertes?.nb_critiques ?? 0)
                      }).catch(() => undefined)
                    }
                  }}
                />
              </div>
              {activeTab === 'marche'   && <div className="h-full flex flex-col"><MarchePanel dossierId={dossierId} address={currentDossierName} /></div>}
              {activeTab === 'analyse'  && <div className="h-full flex flex-col"><AnalysePanel dossierId={dossierId} address={currentDossierName} /></div>}
              {activeTab === 'synthese' && (
                <SynthesePanel
                  dossierId={dossierId}
                  address={currentDossierName}
                  onCritiqueFound={setSyntheseCritiques}
                />
              )}
              {activeTab === 'rapport'  && (
                <div className="h-full flex flex-col">
                  <RapportPanel dossierId={dossierId} dossierAddress={currentDossierName} />
                </div>
              )}
            </div>

            {/* Aside column */}
            <div className="flex flex-col gap-4">
              <SideCard
                title="Faits saillants"
                facts={[
                  { label: 'Adresse', value: dossierLabel },
                  { label: 'Type', value: dossierMeta ? formatPropertyType(dossierMeta.propertyType) : '—' },
                  { label: 'Quartier', value: dossierMeta?.neighborhood ?? '—' },
                  { label: 'Stade', value: `${reportReady ? 5 : 1}/5` },
                ]}
              />
              <SideCard title="Mandat & client">
                {dossierMeta?.commanditaire ? (
                  <div className="flex flex-col">
                    <div
                      className="flex items-baseline justify-between py-2.5"
                      style={{ borderBottom: '1px dashed var(--rule-soft)' }}
                    >
                      <span className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>Client</span>
                      <span className="text-[13px] font-medium text-right ml-3" style={{ color: 'var(--ink)' }}>
                        {dossierMeta.commanditaire.nom}
                      </span>
                    </div>
                    {dossierMeta.commanditaire.organisation && (
                      <div
                        className="flex items-baseline justify-between py-2.5"
                        style={{ borderBottom: '1px dashed var(--rule-soft)' }}
                      >
                        <span className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>Organisation</span>
                        <span className="text-[13px] font-medium text-right ml-3" style={{ color: 'var(--ink)' }}>
                          {dossierMeta.commanditaire.organisation}
                        </span>
                      </div>
                    )}
                    <div
                      className="flex items-baseline justify-between py-2.5"
                      style={{ borderBottom: dossierMeta.mandat ? '1px dashed var(--rule-soft)' : 'none' }}
                    >
                      <span className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>Mandat</span>
                      <span className="text-[13px] font-medium text-right ml-3" style={{ color: 'var(--ink)' }}>
                        {formatFinEval(dossierMeta.commanditaire.fin_evaluation)}
                      </span>
                    </div>
                    {dossierMeta.mandat && (
                      <div className="flex items-baseline justify-between py-2.5">
                        <span className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>Type</span>
                        <span className="text-[13px] font-medium text-right ml-3" style={{ color: 'var(--ink)' }}>
                          {formatMandatType(dossierMeta.mandat.mandat_type)}
                        </span>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>—</p>
                )}
              </SideCard>
              <SideCard title="Activité">
                <p className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>—</p>
              </SideCard>
              <SideCard title="Documents">
                <div className="flex items-center justify-between">
                  <p className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>
                    {dossierMeta && dossierMeta.docCount > 0
                      ? `${dossierMeta.docCount} document${dossierMeta.docCount > 1 ? 's' : ''}`
                      : 'Aucun document joint'}
                  </p>
                  <button
                    className="btn ghost btn-sm"
                    onClick={() => setTab('dossier')}
                  >
                    {dossierMeta && dossierMeta.docCount > 0 ? 'Gérer' : '+ Ajouter'}
                  </button>
                </div>
              </SideCard>
            </div>
          </div>
        </div>
      </div>

      <Toast message={toast} onDismiss={dismissToast} />
      <ShortcutHelp open={showHelp} onClose={() => setShowHelp(false)} />
    </div>
  )
}

export default function DossierShell() {
  return (
    <Suspense>
      <DossierShellInner />
    </Suspense>
  )
}
