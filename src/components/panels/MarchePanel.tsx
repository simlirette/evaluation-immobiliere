'use client'

import { useState, useEffect } from 'react'
import AgentMessage from '@/components/shared/AgentMessage'
import UserMessage from '@/components/shared/UserMessage'
import ComparableItem from '@/components/shared/ComparableItem'
import ChatInput from '@/components/shared/ChatInput'
import { fetchComparables } from '@/lib/supabase/queries/comparables'
import type { Comparable } from '@/types'

interface Props {
  dossierId: string | null
}

export default function MarchePanel({ dossierId }: Props) {
  const [comparables, setComparables] = useState<Comparable[]>([])

  useEffect(() => {
    if (!dossierId) return
    fetchComparables(dossierId).then(setComparables)
  }, [dossierId])

  return (
    <div className="flex flex-col items-center justify-end flex-1 px-6 pb-9">
      <div className="w-full max-w-[640px] flex flex-col gap-0 mb-5 flex-1 overflow-y-auto pt-5 scroll-fade">
        <UserMessage>Unifamiliales R-2, rayon 1 km, vendues dans les 18 derniers mois</UserMessage>
        <AgentMessage agentName="Agent Marché">
          J'ai identifié <strong>{comparables.length} comparables</strong> correspondant aux critères.
          <div className="flex flex-col gap-2 mt-2.5">
            {comparables.map(c => <ComparableItem key={c.id} comp={c} />)}
          </div>
        </AgentMessage>
        {comparables.length > 0 && (
          <AgentMessage agentName="Agent Marché" last>
            Prix médian des comparables : <strong>{comparables[Math.floor(comparables.length / 2)]?.price}</strong>.
          </AgentMessage>
        )}
      </div>
      <ChatInput placeholder="Affiner les critères de recherche..." />
    </div>
  )
}
