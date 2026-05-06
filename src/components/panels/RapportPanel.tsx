'use client'

import { useState } from 'react'
import AgentMessage from '@/components/shared/AgentMessage'
import UserMessage from '@/components/shared/UserMessage'
import RapportArtifact from '@/components/shared/RapportArtifact'
import RapportDoc from '@/components/shared/RapportDoc'
import ChatInput from '@/components/shared/ChatInput'

export default function RapportPanel() {
  const [split, setSplit] = useState(false)

  return (
    <div className={`flex flex-1 overflow-hidden ${split ? 'flex-row' : 'flex-col items-center justify-end'}`}>
      {/* Chat column */}
      <div className={`flex flex-col ${split ? 'flex-[0_0_380px] border-r border-black/[.07] overflow-hidden' : 'w-full items-center justify-end'}`}>
        <div className={`flex flex-col gap-0 mb-5 flex-1 overflow-y-auto pt-5 scroll-fade ${split ? 'px-5' : 'w-full max-w-[640px] px-6'}`}>
          <UserMessage>Génère le rapport OEAQ complet pour le 1842 Sherbrooke O.</UserMessage>
          <AgentMessage agentName="Agent Rapport" last>
            Le rapport d'évaluation OEAQ a été rédigé et certifié.
            <RapportArtifact
              title="Rapport d'évaluation immobilière"
              subtitle="Certifié OEAQ · 1842, rue Sherbrooke O."
              label={split ? 'Fermer' : 'Ouvrir'}
              onClick={() => setSplit(s => !s)}
            />
          </AgentMessage>
        </div>
        <div className={`${split ? 'px-4 pb-5' : 'px-6 pb-9 w-full flex justify-center'}`}>
          <ChatInput placeholder="Modifier ou compléter le rapport..." />
        </div>
      </div>

      {/* Document column */}
      {split && <RapportDoc onClose={() => setSplit(false)} />}
    </div>
  )
}
