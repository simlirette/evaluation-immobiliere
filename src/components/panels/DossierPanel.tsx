'use client'

import { useState, useEffect } from 'react'
import AgentMessage from '@/components/shared/AgentMessage'
import UserMessage from '@/components/shared/UserMessage'
import Chip from '@/components/shared/Chip'
import DocItem from '@/components/shared/DocItem'
import ChatInput from '@/components/shared/ChatInput'
import DropZone from '@/components/shared/DropZone'
import { fetchDocuments, uploadDocument } from '@/lib/supabase/queries/documents'
import { fetchPropertyFacts } from '@/lib/supabase/queries/property_facts'
import type { Document, FactChip } from '@/types'

interface Props {
  isNew: boolean
  dossierId: string | null
}

export default function DossierPanel({ isNew: initialIsNew, dossierId }: Props) {
  const [isNew, setIsNew] = useState(initialIsNew)
  const [chips, setChips] = useState<FactChip[]>([])
  const [documents, setDocuments] = useState<Document[]>([])

  useEffect(() => {
    if (!dossierId) return
    fetchDocuments(dossierId).then(setDocuments)
    fetchPropertyFacts(dossierId).then(setChips)
  }, [dossierId])

  async function handleDrop(files: FileList) {
    if (!dossierId) return
    const newDocs = await Promise.all(Array.from(files).map(f => uploadDocument(dossierId, f)))
    setDocuments(prev => [...prev, ...newDocs])
    setTimeout(() => setIsNew(false), 300)
  }

  return (
    <div className="flex flex-col items-center justify-end flex-1 px-6 pb-9">
      {isNew ? (
        <DropZone onDrop={handleDrop} />
      ) : (
        <div className="w-full max-w-[640px] flex flex-col gap-0 mb-5 flex-1 overflow-y-auto pt-5 scroll-fade">
          <AgentMessage agentName="Agent Dossier">
            J'ai analysé les <strong>{documents.length} documents</strong> soumis pour ce dossier. Voici les faits extraits :
            <div className="flex flex-wrap gap-1.5 mt-2.5">
              {chips.map((c, i) => <Chip key={i} label={c.label} highlight={c.highlight} />)}
            </div>
          </AgentMessage>
          <UserMessage>Voici les documents du dossier</UserMessage>
          <AgentMessage agentName="Agent Dossier" last>
            Joignez les documents du dossier pour commencer l'extraction des faits.
            <div className="flex flex-col gap-1.5 mt-2.5">
              {documents.map(doc => <DocItem key={doc.id} doc={doc} />)}
            </div>
          </AgentMessage>
        </div>
      )}
      <ChatInput placeholder="Écrivez ou collez vos notes ici..." />
    </div>
  )
}
