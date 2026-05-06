'use client'

import { useState } from 'react'
import AgentMessage from '@/components/shared/AgentMessage'
import UserMessage from '@/components/shared/UserMessage'
import Chip from '@/components/shared/Chip'
import DocItem from '@/components/shared/DocItem'
import ChatInput from '@/components/shared/ChatInput'
import DropZone from '@/components/shared/DropZone'
import { MOCK_CHIPS, MOCK_DOCUMENTS } from '@/data/mock'

interface Props {
  isNew: boolean
}

export default function DossierPanel({ isNew: initialIsNew }: Props) {
  const [isNew, setIsNew] = useState(initialIsNew)

  function handleDrop(_files: FileList) {
    setTimeout(() => setIsNew(false), 300)
  }

  return (
    <div className="flex flex-col items-center justify-end flex-1 px-6 pb-9">
      {isNew ? (
        <DropZone onDrop={handleDrop} />
      ) : (
        <div className="w-full max-w-[640px] flex flex-col gap-0 mb-5 flex-1 overflow-y-auto pt-5 scroll-fade">
          <AgentMessage agentName="Agent Dossier">
            J'ai analysé les <strong>3 documents</strong> soumis pour le 1842, rue Sherbrooke Ouest. Voici les faits extraits :
            <div className="flex flex-wrap gap-1.5 mt-2.5">
              {MOCK_CHIPS.map((c, i) => <Chip key={i} label={c.label} highlight={c.highlight} />)}
            </div>
          </AgentMessage>
          <UserMessage>Voici les 3 documents du dossier</UserMessage>
          <AgentMessage agentName="Agent Dossier" last>
            Joignez les documents du dossier pour commencer l'extraction des faits.
            <div className="flex flex-col gap-1.5 mt-2.5">
              {MOCK_DOCUMENTS.map(doc => <DocItem key={doc.id} doc={doc} />)}
            </div>
          </AgentMessage>
        </div>
      )}
      <ChatInput placeholder="Écrivez ou collez vos notes ici..." />
    </div>
  )
}
