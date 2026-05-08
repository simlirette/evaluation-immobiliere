'use client'

import { useEffect, useState } from 'react'
import AgentMessage from '@/components/shared/AgentMessage'
import UserMessage from '@/components/shared/UserMessage'
import RapportArtifact from '@/components/shared/RapportArtifact'
import RapportDoc from '@/components/shared/RapportDoc'
import ChatInput from '@/components/shared/ChatInput'
import PanelLoader from '@/components/shared/PanelLoader'
import {
  fetchAppState,
  generateRuntimePackage,
  sendRuntimeMessage,
  validateRuntimeReview,
} from '@/lib/runtime-api'

interface Props {
  dossierId: string | null
  dossierAddress: string
}

interface RapportState {
  preview: string
  conclusion: string | null
  workflowStatus: string
  canValidate: boolean
  canPackage: boolean
  packageStatus: string
  steps: Array<{ id: string; label: string; status: string; complete: boolean }>
  blockingFailures: string[]
}

export default function RapportPanel({ dossierId, dossierAddress }: Props) {
  const [split, setSplit] = useState(false)
  const [state, setState] = useState<RapportState | null>(null)
  const [reply, setReply] = useState('')
  const [busy, setBusy] = useState('')
  const [loading, setLoading] = useState(true)

  async function reload() {
    if (!dossierId) return
    const app = await fetchAppState(dossierId)
    setState({
      preview: app.active?.report.preview ?? '',
      conclusion: app.active?.valuation.conclusion_label ?? null,
      workflowStatus: app.active?.workflow.status ?? 'ASSISTANCE_DOSSIER_ACTIVE',
      canValidate: Boolean(app.active?.workflow.can_validate_review),
      canPackage: Boolean(app.active?.workflow.can_generate_package),
      packageStatus: app.active?.package.status ?? 'ABSENT',
      steps: app.active?.workflow.steps ?? [],
      blockingFailures: (app.active?.compliance as { blocking_failures?: string[] } | null)?.blocking_failures ?? [],
    })
    setLoading(false)
  }

  useEffect(() => {
    setLoading(true)
    reload()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dossierId])

  async function handleAsk(value: string) {
    if (!dossierId) return
    const response = await sendRuntimeMessage(dossierId, value, 'redaction')
    setReply(response.message.answer)
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

  if (!dossierId || loading || !state) return <PanelLoader />

  return (
    <div className={`flex flex-1 overflow-hidden ${split ? 'flex-row' : 'flex-col items-center justify-end'}`}>
      <div className={`flex flex-col ${split ? 'flex-[0_0_400px] border-r border-black/[.07] overflow-hidden' : 'w-full items-center justify-end'}`}>
        <div className={`flex flex-col gap-0 mb-5 flex-1 overflow-y-auto pt-5 scroll-fade ${split ? 'px-5' : 'w-full max-w-[640px] px-6'}`}>
          <UserMessage>{'Pr\u00e9parer la revue interne et le paquet V1 sans inventer de certification.'}</UserMessage>
          <AgentMessage agentName="Agent Rapport">
            {'Brouillon runtime charg\u00e9. Statut workflow\u00a0: '}<strong>{state.workflowStatus}</strong>{'.'}
            <div className="grid grid-cols-2 gap-2 mt-3">
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
            </div>
            <RapportArtifact
              title="Brouillon de rapport"
              subtitle={`Non certifi\u00e9 \u2014 paquet\u00a0: ${state.packageStatus}`}
              label={split ? 'Fermer' : 'Ouvrir'}
              onClick={() => setSplit(s => !s)}
            />
          </AgentMessage>
          {reply && (
            <AgentMessage agentName="Agent Rapport" last>
              <pre className="whitespace-pre-wrap font-sans text-[13px] leading-6">{reply}</pre>
            </AgentMessage>
          )}
        </div>
        <div className={`${split ? 'px-4 pb-5' : 'px-6 pb-9 w-full flex justify-center'}`}>
          <ChatInput placeholder="Questionner l'Agent Rapport..." onSend={handleAsk} />
        </div>
      </div>

      {split && (
        <RapportDoc
          address={dossierAddress}
          valeur={state.conclusion}
          content={state.preview}
          onClose={() => setSplit(false)}
        />
      )}
    </div>
  )
}
