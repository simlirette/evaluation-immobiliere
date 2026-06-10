'use client'

/* Rapport — vue document-first du design handoff (StageRapport) :
   rapport-hero (cover + stats + actions) et checklist des sections,
   en conservant revue interne / paquet V1 / éditeur TipTap / versions.
   Le chat passe par la capsule globale. */

import { useEffect, useState } from 'react'
import RapportDoc from '@/components/shared/RapportDoc'
import PanelLoader from '@/components/shared/PanelLoader'
import PanelError from '@/components/shared/PanelError'
import Toast from '@/components/shared/Toast'
import RapportVersionHistory from '@/components/shared/RapportVersionHistory'
import DragHandle from '@/components/shared/DragHandle'
import { Icon } from '@/components/shared/Icon'
import {
  fetchAppState,
  generateRuntimePackage,
  validateRuntimeReview,
  downloadRuntimePackage,
  saveRapport,
  generateRapport,
} from '@/lib/runtime-api'
import { saveVersion, loadVersions } from '@/lib/rapport-versions'
import type { Comparable, Adjustment, FactChip } from '@/types'

interface Props {
  dossierId: string | null
  dossierAddress: string
}

interface RapportState {
  conclusion: string | null
  workflowStatus: string
  canValidate: boolean
  canPackage: boolean
  packageStatus: string
  steps: Array<{ id: string; label: string; status: string; complete: boolean }>
  blockingFailures: string[]
  gateMessages: string[]
  warnings: string[]
  comparables: Comparable[]
  adjustments: Adjustment[]
  factChips: FactChip[]
  valuationValues: Record<string, number>
  reportText: string
  complianceStatus: string
  versionCount: number
  realDossierId: string
}

export default function RapportPanel({ dossierId, dossierAddress }: Props) {
  const [split, setSplit] = useState(false)
  const [isMobile, setIsMobile] = useState(() =>
    typeof window !== 'undefined' && window.innerWidth < 640
  )
  const [leftWidth, setLeftWidth] = useState<number>(() => {
    if (typeof window === 'undefined') return 400
    return Number(localStorage.getItem('rapport-panel-width') ?? '400') || 400
  })
  const [state, setState] = useState<RapportState | null>(null)
  const [busy, setBusy] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [toast, setToast] = useState<string | null>(null)

  async function reload() {
    if (!dossierId) return
    const app = await fetchAppState(dossierId)
    const compliance = app.active?.compliance as { blocking_failures?: string[]; warnings?: string[]; status?: string } | null
    const workflowGateMessages = app.active?.workflow.blocking_messages ?? app.active?.workflow.certifiability_gate?.blocking_messages ?? []
    setState({
      conclusion: app.active?.valuation.conclusion_label ?? null,
      workflowStatus: app.active?.workflow.status ?? 'ASSISTANCE_DOSSIER_ACTIVE',
      canValidate: Boolean(app.active?.workflow.can_validate_review),
      canPackage: Boolean(app.active?.workflow.can_generate_package),
      packageStatus: app.active?.package.status ?? 'ABSENT',
      steps: app.active?.workflow.steps ?? [],
      blockingFailures: compliance?.blocking_failures ?? [],
      gateMessages: workflowGateMessages,
      warnings: compliance?.warnings ?? [],
      comparables: app.active?.comparables ?? [],
      adjustments: app.active?.adjustments ?? [],
      factChips: app.active?.fact_chips ?? [],
      valuationValues: app.active?.valuation.values ?? {},
      reportText: app.active?.report?.preview ?? '',
      complianceStatus: compliance?.status ?? '',
      versionCount: 0,
      realDossierId: app.active?.dossier?.id ?? dossierId ?? '',
    })
    setLoading(false)

    // Auto-save version initiale si aucune version n'existe
    const preview = app.active?.report?.preview ?? ''
    if (preview && dossierId) {
      try {
        const versions = await loadVersions(dossierId)
        setState(prev => prev ? { ...prev, versionCount: versions.length } : prev)
        if (versions.length === 0) {
          const realId = app.active?.dossier?.id ?? dossierId
          await saveVersion(dossierId, realId, preview, 'abrege', 'Génération initiale', true)
          setState(prev => prev ? { ...prev, versionCount: 1 } : prev)
        }
      } catch {
        // Supabase non configuré — silencieux
      }
    }
  }

  useEffect(() => {
    function onResize() {
      const mobile = window.innerWidth < 640
      setIsMobile(mobile)
      if (mobile) setSplit(false)
    }
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  useEffect(() => {
    setLoading(true)
    setError(false)
    reload().catch(() => { setError(true); setLoading(false) })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dossierId])

  async function handleValidate() {
    if (!dossierId) return
    setBusy('review')
    try {
      await validateRuntimeReview(dossierId)
      await reload()
    } finally {
      setBusy('')
    }
  }

  async function handlePackage() {
    if (!dossierId) return
    setBusy('package')
    try {
      await generateRuntimePackage(dossierId)
      await reload()
    } finally {
      setBusy('')
    }
  }

  async function handleDownload() {
    if (!dossierId || !state) return
    setBusy('download')
    try {
      await downloadRuntimePackage(dossierId, state.realDossierId || dossierId)
    } catch (e) {
      setToast((e as Error).message)
    } finally {
      setBusy('')
    }
  }

  async function handleSaveReport(content: string) {
    if (!dossierId) return
    await saveRapport(dossierId, content)
  }

  async function handleGenerateReport(format: 'abrege' | 'complet') {
    if (!dossierId) return
    const newContent = await generateRapport(dossierId, format)
    setState(prev => prev ? { ...prev, reportText: newContent } : prev)
  }

  async function handleSaveVersion(markdown: string) {
    if (!dossierId || !state) return
    if (state.versionCount >= 6) {
      setToast('Quota atteint — 5 versions manuelles maximum.')
      return
    }
    const now = new Date()
    const label = `Manuelle ${now.toLocaleDateString('fr-CA')} ${now.toLocaleTimeString('fr-CA', { hour: '2-digit', minute: '2-digit' })}`
    try {
      await saveVersion(dossierId, state.realDossierId, markdown, 'abrege', label, false)
      setState(prev => prev ? { ...prev, versionCount: prev.versionCount + 1 } : prev)
    } catch {
      setToast('Version non sauvegardée — vérifier la connexion Supabase.')
    }
  }

  function handleRestoreVersion(content: string) {
    setState(prev => prev ? { ...prev, reportText: content } : prev)
    setShowHistory(false)
  }

  function handleDrag(delta: number) {
    setLeftWidth(w => {
      const min = 280
      const max = Math.floor(window.innerWidth * 0.8)
      return Math.max(min, Math.min(max, w + delta))
    })
  }

  function handleDragEnd() {
    setLeftWidth(w => {
      localStorage.setItem('rapport-panel-width', String(w))
      return w
    })
  }

  if (!dossierId || loading || !state) return <PanelLoader />
  if (error) return <PanelError onRetry={() => { setError(false); setLoading(true); reload().catch(() => { setError(true); setLoading(false) }) }} />

  const completedSteps = state.steps.filter(s => s.complete).length

  const docView = (
    <div className="flex flex-col gap-5 pb-10">
      {/* ── Hero — cover + stats + actions (design) ── */}
      <section className="panel rapport-hero">
        <div className="rapport-cover">
          <div className="cover-eyebrow">Rapport d&apos;évaluation</div>
          <div className="cover-addr">{dossierAddress}</div>
          <div className="cover-bottom">
            <div>
              <div className="cover-meta-k">Conclusion</div>
              <div className="cover-meta-v numeric">{state.conclusion ?? '—'}</div>
            </div>
            <div>
              <div className="cover-meta-k">Dossier</div>
              <div className="cover-meta-v numeric">{state.realDossierId}</div>
            </div>
          </div>
          <div className="cover-seal">É.A.</div>
        </div>
        <div className="rapport-side">
          <div className="rs-stat">
            <div className="rs-num numeric">{completedSteps}/{state.steps.length || '—'}</div>
            <div className="rs-lbl">étapes complètes</div>
          </div>
          <div className="rs-stat">
            <div className="rs-num" style={{ fontSize: 15 }}>{state.packageStatus.replace(/_/g, ' ').toLowerCase()}</div>
            <div className="rs-lbl">paquet V1</div>
          </div>
          <div className="rs-actions">
            <button
              className="btn accent btn-full disabled:opacity-40"
              onClick={handlePackage}
              disabled={!state.canPackage || busy !== ''}
            >
              {busy === 'package' ? 'Génération…' : 'Générer paquet V1'}
            </button>
            <button
              className="btn secondary btn-full disabled:opacity-40"
              onClick={handleValidate}
              disabled={!state.canValidate || busy !== ''}
            >
              {busy === 'review' ? 'Validation…' : 'Valider revue interne'}
            </button>
            {state.packageStatus === 'PRET_REVUE_EVALUATEUR_AGREE' && (
              <button
                className="btn secondary btn-full disabled:opacity-40"
                onClick={handleDownload}
                disabled={busy !== ''}
              >
                {busy === 'download' ? 'Téléchargement…' : 'Télécharger le paquet'}
              </button>
            )}
            {!isMobile && (
              <button className="btn ghost btn-full" onClick={() => setSplit(s => !s)}>
                {split ? 'Fermer l’éditeur' : 'Ouvrir l’éditeur'}
              </button>
            )}
          </div>
        </div>
      </section>

      {/* ── Sections / étapes du pipeline ── */}
      <section className="panel">
        <div className="panel-head">
          <h2>Étapes du rapport</h2>
          <button
            type="button"
            className="btn ghost btn-sm"
            onClick={() => setShowHistory(s => !s)}
          >
            {showHistory ? 'Fermer historique' : `Historique (${state.versionCount})`}
          </button>
        </div>
        {state.steps.length > 0 ? (
          <ul className="rapport-sections">
            {state.steps.map((s, i) => (
              <li key={s.id} className={s.complete ? 'done' : 'pending'}>
                <span className="sec-icon">
                  {s.complete ? <Icon.Check/> : <Icon.Clock/>}
                </span>
                <span className="sec-num numeric">{String(i + 1).padStart(2, '0')}</span>
                <span className="sec-name">{s.label}</span>
                <span className="sec-pages">{s.status}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="notes-body">
            Pipeline non démarré. Créez un dossier et lancez l&apos;analyse depuis
            l&apos;onglet Dossier pour générer le rapport.
          </p>
        )}
        {showHistory && dossierId && (
          <div className="mt-3 rounded-[var(--r-md)] overflow-hidden" style={{ border: '1px solid var(--rule)' }}>
            <RapportVersionHistory sessionId={dossierId} onRestore={handleRestoreVersion} />
          </div>
        )}
      </section>

      {/* ── Blocages / conditions ── */}
      {(state.blockingFailures.length > 0 || state.gateMessages.length > 0) && (
        <section className="panel">
          <div className="panel-head">
            <h2>Conditions avant certification</h2>
          </div>
          <div className="flex flex-col gap-2">
            {state.blockingFailures.map((f, i) => (
              <div key={`b${i}`} className="rounded-[8px] px-3 py-2 text-[12.5px]"
                style={{ color: 'var(--oxblood)', background: 'rgba(138,48,48,.08)', border: '1px solid rgba(138,48,48,.15)' }}>
                · {f}
              </div>
            ))}
            {state.gateMessages.map((m, i) => (
              <div key={`g${i}`} className="rounded-[8px] px-3 py-2 text-[12.5px]"
                style={{ color: 'var(--ochre)', background: 'rgba(184,138,62,.10)', border: '1px solid rgba(184,138,62,.2)' }}>
                · {m}
              </div>
            ))}
          </div>
        </section>
      )}

      <p className="text-center text-[11px] pb-2" style={{ color: 'var(--ink-faint)' }}>
        Brouillon non certifié — paquet&nbsp;: {state.packageStatus}
      </p>
    </div>
  )

  return (
    <div className={`relative flex flex-1 h-full overflow-hidden ${split ? 'flex-row' : 'flex-col'}`}>
      <Toast message={toast} onDismiss={() => setToast(null)} />
      <div
        className={`flex flex-col overflow-y-auto ${split ? '' : 'w-full flex-1'}`}
        style={split ? { flexBasis: `${leftWidth}px`, flexGrow: 0, flexShrink: 0, borderRight: '1px solid var(--rule-soft)', paddingRight: 16 } : { minHeight: 0 }}
      >
        {docView}
      </div>

      {split && (
        <>
          <DragHandle onDrag={handleDrag} onDragEnd={handleDragEnd} />
          <RapportDoc
            address={dossierAddress}
            valeur={state.conclusion}
            comparables={state.comparables}
            adjustments={state.adjustments}
            factChips={state.factChips}
            valuationValues={state.valuationValues}
            complianceStatus={state.complianceStatus}
            blockingFailures={state.blockingFailures}
            warnings={state.warnings}
            onClose={() => setSplit(false)}
            reportText={state.reportText}
            onSave={handleSaveReport}
            onGenerate={handleGenerateReport}
            sessionId={dossierId ?? ''}
            dossierId={state.realDossierId}
            onSaveVersion={handleSaveVersion}
          />
        </>
      )}
    </div>
  )
}
