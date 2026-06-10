'use client'

/* Workspace dossier — phase 5a de la refonte handoff :
   topbar (adresse + ID + méta + actions), grid 1fr/340px, aside design
   (Faits saillants / Mandat & client / Activité / Documents) sur données
   réelles. Les panels existants (checkpoints, pipeline, streaming) occupent
   la colonne principale ; leur conversion document-first = phase 5b. */

import { useState, useEffect, Suspense, useCallback } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import Stepper from '@/components/layout/Stepper'
import Toast from '@/components/shared/Toast'
import ShortcutHelp from '@/components/shared/ShortcutHelp'
import { Icon } from '@/components/shared/Icon'
import DossierPanel from '@/components/panels/DossierPanel'
import AgentChatCapsule from '@/components/dossier/AgentChatCapsule'
import MarchePanel from '@/components/panels/MarchePanel'
import AnalysePanel from '@/components/panels/AnalysePanel'
import SynthesePanel from '@/components/panels/SynthesePanel'
import RapportPanel from '@/components/panels/RapportPanel'
import { fetchAppState, fetchRuntimeEnrichment, fetchCheckpointLog, type CheckpointLogEntry } from '@/lib/runtime-api'
import { createClient } from '@/lib/supabase/client'
import type { TabId, Document, FactChip } from '@/types'
import './dossier.css'

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

function docExt(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase() ?? 'doc'
  return ['pdf', 'zip', 'csv'].includes(ext) ? ext : 'doc'
}

/* Les fact_chips arrivent en « Libellé : valeur » — découpage k/v pour
   les fact-rows du design. */
function chipToRow(chip: FactChip): { k: string; v: string } {
  const idx = chip.label.indexOf(':')
  if (idx === -1) return { k: chip.label, v: '' }
  return { k: chip.label.slice(0, idx).trim(), v: chip.label.slice(idx + 1).trim() }
}

interface DossierMeta {
  dossierId: string
  propertyType: string
  neighborhood: string
  commanditaire: { nom: string; organisation: string; fin_evaluation: string } | null
  mandat: { mandat_type: string } | null
  documents: Document[]
  factChips: FactChip[]
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
  const [visible, setVisible] = useState(true)
  const [reportReady, setReportReady] = useState(false)
  const [, setSyntheseCritiques] = useState(0)
  const [toast, setToast] = useState<string | null>(null)
  const dismissToast = useCallback(() => setToast(null), [])
  const [showHelp, setShowHelp] = useState(false)
  const [meta, setMeta] = useState<DossierMeta | null>(null)
  const [activity, setActivity] = useState<CheckpointLogEntry[]>([])

  useEffect(() => {
    setActiveDossierId(params.id)
    fetchAppState(params.id)
      .then(app => {
        const d = app.active?.dossier
        if (d) {
          setCurrentDossierName(d.address)
          setDossierId(d.id)
          setMeta({
            dossierId: d.slug,
            propertyType: d.property_type,
            neighborhood: d.neighborhood,
            commanditaire: app.active?.commanditaire ?? null,
            mandat: app.active?.mandat
              ? { mandat_type: app.active.mandat.mandat_type }
              : null,
            documents: app.active?.documents ?? [],
            factChips: app.active?.fact_chips ?? [],
          })
        } else {
          router.push('/dossiers')
        }
      })
      .catch(() => router.push('/dossiers'))
    fetchCheckpointLog(params.id).then(setActivity).catch(() => undefined)
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

  const dossierLabel = currentDossierName || params.id
  const factRows = (meta?.factChips ?? []).map(chipToRow).filter(r => r.v)
  const chatTab = ['dossier', 'marche', 'analyse', 'rapport'].includes(activeTab)

  return (
    <div className="app">
      <Sidebar
        onSignOut={handleSignOut}
        currentDossierAddress={dossierLabel}
        currentDossierCity={meta?.neighborhood ?? null}
      />

      <div className="main" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Topbar — design handoff */}
        <div className="topbar dossier-topbar" style={{ flexShrink: 0 }}>
          <div className="pagehead dossier-head">
            <div className="head-left">
              <h1>
                {dossierLabel}
                {meta && <span className="head-id numeric">{meta.dossierId}</span>}
              </h1>
              <div className="head-meta">
                <span>{meta?.neighborhood ?? ' '}</span>
                {meta && <>
                  <span className="dot-sep">·</span>
                  <span>{formatPropertyType(meta.propertyType)}</span>
                </>}
              </div>
            </div>
            <div className="head-actions">
              <button className="btn ghost" onClick={() => window.print()}><Icon.Print/> Imprimer</button>
              <button
                className="btn secondary"
                onClick={() => {
                  navigator.clipboard.writeText(window.location.href)
                    .then(() => setToast('Lien copié dans le presse-papiers'))
                    .catch(() => setToast('Impossible de copier le lien'))
                }}
              >
                <Icon.Share/> Partager
              </button>
              <button className="btn accent" onClick={() => setTab('dossier')}>Reprendre</button>
            </div>
          </div>

          <Stepper activeTab={activeTab} onTabChange={setTab} />
        </div>

        {/* Body — grid 1fr / 340px (design) */}
        <div
          className="dossier-body"
          style={{
            flex: 1,
            minHeight: 0,
            paddingBottom: 24,
            opacity: visible ? 1 : 0,
            transform: visible ? 'translateY(0)' : 'translateY(5px)',
            transition: 'opacity .2s, transform .2s',
          }}
        >
          {/* Colonne principale — panels existants (conversion design = 5b) */}
          <div className={`dossier-main ${chatTab ? 'h-full overflow-hidden' : 'overflow-y-auto'}`} style={{ minHeight: 0 }}>
            {/* DossierPanel toujours monté — garde le polling pipeline vivant */}
            <div className={activeTab === 'dossier' ? 'h-full flex flex-col' : 'hidden'}>
              <DossierPanel
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
            {reportReady && null}
          </div>

          {/* Aside — design handoff, données réelles */}
          <aside className="dossier-aside" style={{ overflowY: 'auto', minHeight: 0 }}>
            <section className="side-card">
              <h3>Faits saillants</h3>
              <div className="side-card-body">
                {factRows.length > 0 ? factRows.map((r, i) => (
                  <div className="fact-row" key={i}>
                    <div className="k">{r.k}</div>
                    <div className="v numeric">{r.v}</div>
                  </div>
                )) : (
                  <>
                    <div className="fact-row">
                      <div className="k">Type</div>
                      <div className="v">{meta ? formatPropertyType(meta.propertyType) : '—'}</div>
                    </div>
                    <div className="fact-row">
                      <div className="k">Quartier</div>
                      <div className="v">{meta?.neighborhood ?? '—'}</div>
                    </div>
                  </>
                )}
              </div>
            </section>

            <section className="side-card">
              <h3>Mandat &amp; client</h3>
              <div className="side-card-body">
                {meta?.commanditaire ? (
                  <>
                    <div className="client-block">
                      <div className="client-org">{meta.commanditaire.organisation || meta.commanditaire.nom}</div>
                      <div className="client-person">{meta.commanditaire.nom}</div>
                      {meta.mandat && (
                        <div className="client-role">{meta.mandat.mandat_type.replace(/_/g, ' ')}</div>
                      )}
                    </div>
                    <div className="mandate-tag">
                      <span className="dot"/> {formatFinEval(meta.commanditaire.fin_evaluation)}
                    </div>
                  </>
                ) : (
                  <div className="fact-row"><div className="k">Client</div><div className="v muted">—</div></div>
                )}
              </div>
            </section>

            <section className="side-card tight">
              <h3>Activité</h3>
              <div className="side-card-body">
                <ul className="activity">
                  {activity.length === 0 && (
                    <li>
                      <div className="when">—</div>
                      <div className="what">Aucun checkpoint confirmé pour l&apos;instant.</div>
                    </li>
                  )}
                  {activity.slice(-6).reverse().map((a, i) => (
                    <li key={i}>
                      <div className="when">{a.confirmed_at?.slice(0, 10) ?? '—'}</div>
                      <div className="what">
                        <span className="who">É.A.</span> a confirmé le checkpoint {a.checkpoint}
                        {a.label ? ` — ${a.label.replace(/_/g, ' ')}` : ''}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </section>

            <section className="side-card tight">
              <h3>Documents ({meta?.documents.length ?? 0})</h3>
              <div className="side-card-body">
                <ul className="docs">
                  {(meta?.documents ?? []).map(doc => (
                    <li key={doc.id}>
                      <div className={`doc-icon doc-${docExt(doc.filename)}`}>{docExt(doc.filename).toUpperCase()}</div>
                      <div className="doc-info">
                        <div className="doc-name">{doc.name}</div>
                        <div className="doc-meta">{doc.sizeLabel}</div>
                      </div>
                    </li>
                  ))}
                  {(meta?.documents.length ?? 0) === 0 && (
                    <li>
                      <div className="doc-info">
                        <div className="doc-meta">Aucun document joint</div>
                      </div>
                    </li>
                  )}
                </ul>
                <button className="btn ghost btn-full" onClick={() => setTab('dossier')}>
                  <Icon.Plus/> Ajouter un document
                </button>
              </div>
            </section>
          </aside>
        </div>
      </div>

      {/* Capsule agent (design) — composer persistant sur toutes les étapes */}
      <AgentChatCapsule dossierId={dossierId} stage={activeTab} />

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
