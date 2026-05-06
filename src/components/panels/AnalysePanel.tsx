'use client'

import { useState, useEffect } from 'react'
import AgentMessage from '@/components/shared/AgentMessage'
import UserMessage from '@/components/shared/UserMessage'
import AdjustmentsTable from '@/components/shared/AdjustmentsTable'
import ValeurCard from '@/components/shared/ValeurCard'
import ChatInput from '@/components/shared/ChatInput'
import PanelLoader from '@/components/shared/PanelLoader'
import { fetchAdjustments } from '@/lib/supabase/queries/adjustments'
import type { Adjustment } from '@/types'

interface Props {
  dossierId: string | null
}

export default function AnalysePanel({ dossierId }: Props) {
  const [adjustments, setAdjustments] = useState<Adjustment[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!dossierId) return
    setLoading(true)
    fetchAdjustments(dossierId).then(data => {
      setAdjustments(data)
      setLoading(false)
    })
  }, [dossierId])

  if (!dossierId || loading) return <PanelLoader />

  const adjustedValues = adjustments.map(a => a.adjusted).filter(v => v > 0).sort((a, b) => a - b)
  const median = adjustedValues.length
    ? adjustedValues[Math.floor(adjustedValues.length / 2)]
    : null

  const formatPrice = (n: number) =>
    new Intl.NumberFormat('fr-CA', { style: 'currency', currency: 'CAD', maximumFractionDigits: 0 })
      .format(n).replace('CA', '').trim()

  return (
    <div className="flex flex-col items-center justify-end flex-1 px-6 pb-9">
      <div className="w-full max-w-[640px] flex flex-col gap-0 mb-5 flex-1 overflow-y-auto pt-5 scroll-fade">
        <UserMessage>Applique un ajustement +5% pour la rénovation 2019 et tiens compte du garage double</UserMessage>
        <AgentMessage agentName="Agent Analyse">
          Voici le tableau d'ajustements :
          <AdjustmentsTable rows={adjustments} />
          {median && (
            <ValeurCard median={`Médiane ajustée : ${formatPrice(median)}`} />
          )}
        </AgentMessage>
        {adjustments.length > 0 && (
          <AgentMessage agentName="Agent Analyse" last>
            Médiane ajustée : <strong>{median ? formatPrice(median) : '—'}</strong>.
          </AgentMessage>
        )}
      </div>
      <ChatInput placeholder="Modifier les ajustements..." />
    </div>
  )
}
