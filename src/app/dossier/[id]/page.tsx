'use client'

import { useState, useEffect, Suspense, useCallback } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import Stepper from '@/components/layout/Stepper'
import Toast from '@/components/shared/Toast'
import ShortcutHelp from '@/components/shared/ShortcutHelp'
import SideCard from '@/components/dossier/SideCard'
import AgentChat from '@/components/dossier/AgentChat'
import DossierPanel from '@/components/panels/DossierPanel'
import MarchePanel from '@/components/panels/MarchePanel'
import AnalysePanel from '@/components/panels/AnalysePanel'
import SynthesePanel from '@/components/panels/SynthesePanel'
import RapportPanel from '@/components/panels/RapportPanel'
import { fetchRuntimeDossier, fetchRuntimeEnrichment } from '@/lib/runtime-api'
import { createClient } from '@/lib/supabase/client'
import type { TabId } from '@/types'

const VALID_TABS: TabId[] = ['dossier', 'marche', 'analyse', 'synthese', 'rapport']

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

  useEffect(() => {
    if (params.id === 'nouveau') return
    setActiveDossierId(params.id)
    fetchRuntimeDossier(params.id)
      .then(d => {
        if (d) {
          setCurrentDossierName(d.address)
          setDossierId(d.id)
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
                Montréal · Résidentiel · 2024
              </div>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0 pt-1">
              <button className="btn ghost btn-sm">Imprimer</button>
              <button className="btn secondary btn-sm">Partager</button>
              <button className="btn accent btn-sm">Reprendre</button>
            </div>
          </div>

          <Stepper activeTab={activeTab} onTabChange={setTab} />
        </div>

        {/* Body */}
        <div
          className="flex-1 overflow-y-auto transition-[opacity,transform] duration-200"
          style={{
            opacity: visible ? 1 : 0,
            transform: visible ? 'translateY(0)' : 'translateY(5px)',
          }}
        >
          <div
            className="grid gap-7 px-10 pt-6 pb-36"
            style={{ gridTemplateColumns: 'minmax(0,1fr) 340px' }}
          >
            {/* Main panel column */}
            <div>
              {/* DossierPanel always mounted — keeps pipeline polling alive */}
              <div className={activeTab === 'dossier' ? 'block' : 'hidden'}>
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
              {activeTab === 'marche'   && <MarchePanel dossierId={dossierId} address={currentDossierName} />}
              {activeTab === 'analyse'  && <AnalysePanel dossierId={dossierId} address={currentDossierName} />}
              {activeTab === 'synthese' && (
                <SynthesePanel
                  dossierId={dossierId}
                  address={currentDossierName}
                  onCritiqueFound={setSyntheseCritiques}
                />
              )}
              {activeTab === 'rapport'  && (
                <RapportPanel dossierId={dossierId} dossierAddress={currentDossierName} />
              )}
            </div>

            {/* Aside column */}
            <div className="flex flex-col gap-4">
              <SideCard
                title="Faits saillants"
                facts={[
                  { label: 'Adresse', value: dossierLabel },
                  { label: 'Type', value: 'Résidentiel' },
                  { label: 'Année', value: '2024' },
                  { label: 'Superficie', value: '—' },
                  { label: 'Stade', value: `${reportReady ? 5 : 1}/5` },
                ]}
              />
              <SideCard title="Mandat & client">
                <p className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>—</p>
              </SideCard>
              <SideCard title="Activité">
                <p className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>—</p>
              </SideCard>
              <SideCard title="Documents">
                <p className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>
                  Aucun document joint.
                </p>
              </SideCard>
            </div>
          </div>
        </div>
      </div>

      <AgentChat activeTab={activeTab} />

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
