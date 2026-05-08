'use client'

import { useEffect, useState } from 'react'
import AgentMessage from '@/components/shared/AgentMessage'
import UserMessage from '@/components/shared/UserMessage'
import ComparableItem from '@/components/shared/ComparableItem'
import ChatInput from '@/components/shared/ChatInput'
import PanelLoader from '@/components/shared/PanelLoader'
import { fetchComparables } from '@/lib/supabase/queries/comparables'
import { sendRuntimeMessage } from '@/lib/runtime-api'
import type { Comparable } from '@/types'

interface Props {
  dossierId: string | null
}

export default function MarchePanel({ dossierId }: Props) {
  const [comparables, setComparables] = useState<Comparable[]>([])
  const [reply, setReply] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!dossierId) return
    setLoading(true)
    fetchComparables(dossierId).then(data => {
      setComparables(data)
      setLoading(false)
    })
  }, [dossierId])

  async function handleAsk(value: string) {
    if (!dossierId) return
    const response = await sendRuntimeMessage(dossierId, value, 'comps-market')
    setReply(response.message.answer)
  }

  if (!dossierId || loading) return <PanelLoader />

  return (
    <div className="flex flex-col items-center justify-end flex-1 px-6 pb-9">
      <div className="w-full max-w-[640px] flex flex-col gap-0 mb-5 flex-1 overflow-y-auto pt-5 scroll-fade">
        <UserMessage>Comparer les ventes retenues et expliquer leur pertinence.</UserMessage>
        <AgentMessage agentName="Agent March\u00e9">
          {'J\u2019ai charg\u00e9 '}<strong>{comparables.length} comparables</strong>{' depuis les art\u00e9facts du backend.'}
          <div className="flex flex-col gap-2 mt-2.5">
            {comparables.map(c => <ComparableItem key={c.id} comp={c} />)}
          </div>
        </AgentMessage>
        {comparables.length > 0 && (
          <AgentMessage agentName="Agent March\u00e9" last={!reply}>
            {'Les comparables sont retenus par score, source et r\u00e9cence. Les sources restent \u00e0 valider avant signature.'}
          </AgentMessage>
        )}
        {reply && (
          <AgentMessage agentName="Agent March\u00e9" last>
            <pre className="whitespace-pre-wrap font-sans text-[13px] leading-6">{reply}</pre>
          </AgentMessage>
        )}
      </div>
      <ChatInput placeholder="Questionner l'Agent March\u00e9..." onSend={handleAsk} />
    </div>
  )
}
