'use client'

import { useEffect, useState } from 'react'
import AgentMessage from '@/components/shared/AgentMessage'
import UserMessage from '@/components/shared/UserMessage'
import AdjustmentsTable from '@/components/shared/AdjustmentsTable'
import ValeurCard from '@/components/shared/ValeurCard'
import ChatInput from '@/components/shared/ChatInput'
import PanelLoader from '@/components/shared/PanelLoader'
import { fetchAdjustments } from '@/lib/supabase/queries/adjustments'
import { fetchAppState, sendRuntimeMessage } from '@/lib/runtime-api'
import type { Adjustment } from '@/types'

interface Props {
  dossierId: string | null
}

const VALUATION_STATUS_LABELS: Record<string, string> = {
  A_VALIDER_PAR_EVALUATEUR_AGREE: 'À valider — évaluateur agréé requis',
  VALIDE: 'Validé en revue interne',
  A_CORRIGER: 'À corriger',
  PRET_REVUE: 'Prêt pour revue',
  ASSISTANCE_DOSSIER_ACTIVE: 'Assistance active',
  UNKNOWN: 'Statut inconnu',
}

function statusLabel(raw: string): string {
  return VALUATION_STATUS_LABELS[raw] ?? raw.replace(/_/g, ' ')
}

function formatPrice(n: number) {
  return new Intl.NumberFormat('fr-CA', {
    style: 'currency',
    currency: 'CAD',
    maximumFractionDigits: 0,
  }).format(n).replace('CA', '').trim()
}

export default function AnalysePanel({ dossierId }: Props) {
  const [adjustments, setAdjustments] = useState<Adjustment[]>([])
  const [conclusion, setConclusion] = useState<number | null>(null)
  const [status, setStatus] = useState('A_VALIDER_PAR_EVALUATEUR_AGREE')
  const [reply, setReply] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!dossierId) return
    setLoading(true)
    Promise.all([fetchAdjustments(dossierId), fetchAppState(dossierId)]).then(([rows, state]) => {
      setAdjustments(rows)
      setConclusion(state.active?.valuation.conclusion.value ?? null)
      setStatus(state.active?.valuation.status ?? 'A_VALIDER_PAR_EVALUATEUR_AGREE')
      setLoading(false)
    })
  }, [dossierId])

  async function handleAsk(value: string) {
    if (!dossierId) return
    const response = await sendRuntimeMessage(dossierId, value, 'valuation-draft')
    setReply(response.message.answer)
  }

  if (!dossierId || loading) return <PanelLoader />

  return (
    <div className="flex flex-col items-center justify-end flex-1 px-6 pb-9">
      <div className="w-full max-w-[640px] flex flex-col gap-0 mb-5 flex-1 overflow-y-auto pt-5 scroll-fade">
        <UserMessage>{'Afficher la valeur propos\u00e9e et la trace d\u2019ajustements.'}</UserMessage>
        <AgentMessage agentName="Agent Analyse">
          Voici la trace d'analyse issue du runtime. Elle n'est pas une certification.
          <AdjustmentsTable rows={adjustments} />
          {conclusion !== null && (
            <ValeurCard
              median={`Conclusion propos\u00e9e\u00a0: ${formatPrice(conclusion)}`}
            />
          )}
        </AgentMessage>
        <AgentMessage agentName="Agent Analyse" last={!reply}>
          {'Statut\u00a0: '}<strong>{statusLabel(status)}</strong>{'. La validation d\u2019un \u00e9valuateur agr\u00e9\u00e9 reste obligatoire avant toute diffusion.'}
        </AgentMessage>
        {reply && (
          <AgentMessage agentName="Agent Analyse" last>
            <pre className="whitespace-pre-wrap font-sans text-[13px] leading-6">{reply}</pre>
          </AgentMessage>
        )}
      </div>
      <ChatInput placeholder="Questionner l'Agent Analyse..." onSend={handleAsk} />
    </div>
  )
}
