'use client'

import { Fragment, useEffect, useRef, useState } from 'react'
import AgentMessage from '@/components/shared/AgentMessage'
import UserMessage from '@/components/shared/UserMessage'
import RapportArtifact from '@/components/shared/RapportArtifact'
import RapportDoc from '@/components/shared/RapportDoc'
import ChatInput from '@/components/shared/ChatInput'
import PanelLoader from '@/components/shared/PanelLoader'
import PanelError from '@/components/shared/PanelError'
import {
  fetchAppState,
  generateRuntimePackage,
  validateRuntimeReview,
  downloadRuntimePackage,
  saveRapport,
  generateRapport,
} from '@/lib/runtime-api'
import { useAgentChat } from '@/hooks/useAgentChat'
import { saveVersion, loadVersions } from '@/lib/rapport-versions'
import RapportVersionHistory from '@/components/shared/RapportVersionHistory'
import type { Comparable, Adjustment, FactChip } from '@/types'
import DragHandle from '@/components/shared/DragHandle'

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
  const scrollRef = useRef<HTMLDivElement>(null)
  const [state, setState] = useState<RapportState | null>(null)
  const { replies, asking, ask } = useAgentChat(dossierId, 'redaction')
  const [busy, setBusy] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [showHistory, setShowHistory] = useState(false)

  async function reload() {
    if (!dossierId) return
    const app = await fetchAppState(dossierId)
    const compliance = app.active?.compliance as { blocking_failures?: string[]; warnings?: string[]; status?: string } | null
    setState({
      conclusion: app.active?.valuation.conclusion_label ?? null,
      workflowStatus: app.active?.workflow.status ?? 'ASSISTANCE_DOSSIER_ACTIVE',
      canValidate: Boolean(app.active?.workflow.can_validate_review),
      canPackage: Boolean(app.active?.workflow.can_generate_package),
      packageStatus: app.active?.package.status ?? 'ABSENT',
      steps: app.active?.workflow.steps ?? [],
      blockingFailures: compliance?.blocking_failures ?? [],
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
          await saveVersion(
            dossierId,
            realId,
            preview,
            'abrege',
            'Génération initiale',
            true
          )
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

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [replies, asking])

  async function handleAsk(value: string) {
    await ask(value)
  }

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
      alert((e as Error).message)
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
      alert('Quota atteint : 5 versions manuelles + 1 initiale maximum. Aucune nouvelle version sauvegardée.')
      return
    }
    const now = new Date()
    const label = `Manuelle ${now.toLocaleDateString('fr-CA')} ${now.toLocaleTimeString('fr-CA', { hour: '2-digit', minute: '2-digit' })}`
    try {
      await saveVersion(dossierId, state.realDossierId, markdown, 'abrege', label, false)
      setState(prev => prev ? { ...prev, versionCount: prev.versionCount + 1 } : prev)
    } catch {
      alert('Version non sauvegardée — vérifier la connexion Supabase.')
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

  return (
    <div className={`flex flex-1 overflow-hidden ${split ? 'flex-row' : 'flex-col items-center justify-end'}`}>
      <div
        className={`flex flex-col ${split ? 'border-r border-black/[.07] overflow-hidden' : 'w-full items-center justify-end'}`}
        style={split ? { flexBasis: `${leftWidth}px`, flexGrow: 0, flexShrink: 0 } : undefined}
      >
        <div ref={scrollRef} className={`flex flex-col gap-0 mb-5 flex-1 overflow-y-auto pt-5 scroll-fade ${split ? 'px-5' : 'w-full max-w-[640px] px-6'}`}>
          <UserMessage>{'Pr\u00e9parer la revue interne et le paquet V1 sans inventer de certification.'}</UserMessage>
          <AgentMessage agentName="Agent Rapport">
            {'Brouillon runtime charg\u00e9. Statut workflow\u00a0: '}<strong>{state.workflowStatus}</strong>{'.'}
            {state.conclusion && (
              <div className="mt-3 rounded-[10px] px-4 py-3" style={{ background: 'rgba(31,122,92,.07)', border: '1px solid rgba(31,122,92,.18)' }}>
                <div className="text-[10px] uppercase tracking-[.07em] font-medium mb-1" style={{ color: '#1f7a5c' }}>
                  {'Conclusion de valeur propos\u00e9e'}
                </div>
                <div className="text-[22px] font-semibold leading-tight" style={{ fontFamily: 'var(--font-serif)', color: '#0f3d2e' }}>
                  {state.conclusion}
                </div>
                {state.complianceStatus && (
                  <div className="text-[11px] mt-1" style={{ color: '#1f7a5c' }}>{state.complianceStatus}</div>
                )}
              </div>
            )}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-3">
              {state.steps.map(step => (
                <div key={step.id} className="rounded-[9px] bg-black/[.035] px-3 py-2 text-[12px]">
                  <div className="text-[#1a1916]">{step.label}</div>
                  <div className="text-[11px] text-[#8a8780]">{step.status}</div>
                </div>
              ))}
            </div>
            {state.blockingFailures.length > 0 && (
              <div className="mt-3 rounded-[9px] bg-red-50/80 border border-red-200/60 px-3 py-2">
                <div className="text-[11px] font-medium text-red-700 mb-1">
                  {state.blockingFailures.length} blocage{state.blockingFailures.length > 1 ? 's' : ''} — revue impossible
                </div>
                <ul className="text-[11px] text-red-600 list-disc list-inside space-y-0.5">
                  {state.blockingFailures.slice(0, 5).map((f, i) => <li key={i}>{f}</li>)}
                </ul>
              </div>
            )}
            <div className="flex gap-2 mt-3">
              <button
                onClick={handleValidate}
                disabled={!state.canValidate || busy !== ''}
                className="rounded-full px-3.5 py-2 text-[12px] bg-[#334155] text-white disabled:opacity-40"
              >
                {busy === 'review' ? 'Validation...' : 'Valider revue interne'}
              </button>
              <button
                onClick={handlePackage}
                disabled={!state.canPackage || busy !== ''}
                className="rounded-full px-3.5 py-2 text-[12px] bg-[#1f7a5c] text-white disabled:opacity-40"
              >
                {busy === 'package' ? 'G\u00e9n\u00e9ration...' : 'G\u00e9n\u00e9rer paquet V1'}
              </button>
              {state.packageStatus === 'PRET_REVUE_EVALUATEUR_AGREE' && (
                <button
                  onClick={handleDownload}
                  disabled={busy !== ''}
                  className="rounded-full px-3.5 py-2 text-[12px] bg-[#334155] text-white disabled:opacity-40"
                >
                  {busy === 'download' ? 'Téléchargement...' : '↓ Télécharger paquet'}
                </button>
              )}
            </div>
            <RapportArtifact
              title="Brouillon de rapport"
              subtitle={`Non certifi\u00e9 \u2014 paquet\u00a0: ${state.packageStatus}`}
              label={split ? 'Fermer' : 'Ouvrir'}
              onClick={isMobile ? undefined : () => setSplit(s => !s)}
              disabled={isMobile}
            />
            {split && (
              <button
                type="button"
                onClick={() => setShowHistory(s => !s)}
                className="mt-2 rounded-full px-3 py-1.5 text-[11px] bg-black/[.05] text-[#5a5854] hover:bg-black/[.09] transition-colors"
              >
                {showHistory ? 'Fermer historique' : `Historique (${state.versionCount})`}
              </button>
            )}
            {showHistory && dossierId && (
              <div className="mt-2 rounded-[10px] border border-black/[.07] overflow-hidden">
                <RapportVersionHistory
                  sessionId={dossierId}
                  onRestore={handleRestoreVersion}
                />
              </div>
            )}
          </AgentMessage>
          {replies.map((r, i) => (
            <Fragment key={i}>
              {r.userMessage && <UserMessage>{r.userMessage}</UserMessage>}
              <AgentMessage agentName={r.agentLabel || 'Agent Rapport'} last={i === replies.length - 1 && !asking}>
                <pre className="whitespace-pre-wrap font-sans text-[13px] leading-6">
                  {r.text}{r.streaming ? '▊' : ''}
                </pre>
              </AgentMessage>
            </Fragment>
          ))}
        </div>
        <div className={`${split ? 'px-4 pb-5' : 'px-6 pb-9 w-full flex justify-center'}`}>
          <ChatInput placeholder="Questionner l'Agent Rapport..." onSend={handleAsk} disabled={asking} />
        </div>
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
