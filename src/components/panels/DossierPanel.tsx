'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import type { FormEvent } from 'react'
import AgentMessage from '@/components/shared/AgentMessage'
import UserMessage from '@/components/shared/UserMessage'
import Chip from '@/components/shared/Chip'
import DocItem from '@/components/shared/DocItem'
import ChatInput from '@/components/shared/ChatInput'
import DropZone from '@/components/shared/DropZone'
import PanelLoader from '@/components/shared/PanelLoader'
import { fetchDocuments, uploadDocument } from '@/lib/supabase/queries/documents'
import { fetchPropertyFacts } from '@/lib/supabase/queries/property_facts'
import { createDossier } from '@/lib/supabase/queries/dossiers'
import { sendRuntimeMessage } from '@/lib/runtime-api'
import type { Document, FactChip } from '@/types'

interface Props {
  isNew: boolean
  dossierId: string | null
}

interface AssistantReply {
  id: string
  agent: string
  answer: string
}

interface UploadStatus {
  name: string
  state: 'uploading' | 'error'
  error?: string
}

function NewDossierForm() {
  const router = useRouter()
  const [address, setAddress] = useState('Dossier pilote residentiel')
  const [propertyType, setPropertyType] = useState('Residentiel unifamilial')
  const [neighborhood, setNeighborhood] = useState('Zone anonymisee')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!address.trim() || !propertyType.trim() || !neighborhood.trim()) return
    setLoading(true)
    setError('')
    try {
      const dossier = await createDossier({
        address: address.trim(),
        property_type: propertyType.trim(),
        neighborhood: neighborhood.trim(),
      })
      router.push(`/dossier/${dossier.slug}?tab=dossier`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la creation du dossier.')
      setLoading(false)
    }
  }

  const inputStyle = {
    background: 'var(--input-bg)',
    border: '1px solid var(--input-border)',
  }

  return (
    <div className="w-full max-w-[520px] flex flex-col gap-6 pb-9">
      <div className="text-center">
        <div
          className="text-[20px] font-medium text-[#1a1916] tracking-[-.01em]"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          Nouveau dossier
        </div>
        <p className="mt-1 text-[13px] text-[#8a8780]">
          Lance un dossier pilote dans le backend runtime et ouvre les agents AI.
        </p>
      </div>

      {error && (
        <div className="rounded-[10px] px-4 py-3 text-[13px] text-red-700 bg-red-50/80 border border-red-200/60">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <label className="text-[12px] text-[#8a8780] font-medium">Nom du dossier</label>
          <input
            type="text"
            required
            value={address}
            onChange={e => setAddress(e.target.value)}
            className="w-full rounded-[10px] px-4 py-2.5 text-[14px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
            style={inputStyle}
          />
        </div>

        <div className="flex gap-3">
          <div className="flex flex-col gap-1.5 flex-1">
            <label className="text-[12px] text-[#8a8780] font-medium">Type</label>
            <input
              type="text"
              required
              value={propertyType}
              onChange={e => setPropertyType(e.target.value)}
              className="w-full rounded-[10px] px-4 py-2.5 text-[14px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
              style={inputStyle}
            />
          </div>
          <div className="flex flex-col gap-1.5 flex-1">
            <label className="text-[12px] text-[#8a8780] font-medium">Secteur</label>
            <input
              type="text"
              required
              value={neighborhood}
              onChange={e => setNeighborhood(e.target.value)}
              className="w-full rounded-[10px] px-4 py-2.5 text-[14px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
              style={inputStyle}
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="mt-1 w-full rounded-[10px] py-2.5 text-[14px] font-medium text-white transition-opacity hover:opacity-90 active:opacity-80 disabled:opacity-50"
          style={{ background: '#334155' }}
        >
          {loading ? 'Lancement...' : 'Lancer le dossier pilote'}
        </button>
      </form>
    </div>
  )
}

export default function DossierPanel({ isNew, dossierId }: Props) {
  const [chips, setChips] = useState<FactChip[]>([])
  const [documents, setDocuments] = useState<Document[]>([])
  const [showDropZone, setShowDropZone] = useState(false)
  const [loading, setLoading] = useState(true)
  const [replies, setReplies] = useState<AssistantReply[]>([])
  const [uploads, setUploads] = useState<UploadStatus[]>([])

  useEffect(() => {
    if (!dossierId) return
    setLoading(true)
    Promise.all([
      fetchDocuments(dossierId),
      fetchPropertyFacts(dossierId),
    ]).then(([docs, facts]) => {
      setDocuments(docs)
      setChips(facts)
      setLoading(false)
    })
  }, [dossierId])

  async function handleDrop(files: FileList) {
    if (!dossierId) return
    const fileArray = Array.from(files)
    setUploads(fileArray.map(f => ({ name: f.name, state: 'uploading' as const })))
    setShowDropZone(false)

    const results = await Promise.allSettled(fileArray.map(f => uploadDocument(dossierId, f)))

    const newDocs: Document[] = []
    const errors: UploadStatus[] = []
    results.forEach((r, i) => {
      if (r.status === 'fulfilled') {
        newDocs.push(r.value)
      } else {
        errors.push({ name: fileArray[i].name, state: 'error', error: r.reason?.message ?? 'Erreur inconnue' })
      }
    })

    setDocuments(prev => [...prev, ...newDocs])
    setUploads(errors)
  }

  async function handleAsk(value: string) {
    if (!dossierId) return
    const response = await sendRuntimeMessage(dossierId, value, 'data-facts')
    setReplies(prev => [
      ...prev,
      {
        id: `${Date.now()}`,
        agent: response.message.agent_label,
        answer: response.message.answer,
      },
    ])
  }

  if (!isNew && (!dossierId || loading)) return <PanelLoader />

  if (isNew && !dossierId) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 px-6 pb-9">
        <NewDossierForm />
      </div>
    )
  }

  if (showDropZone) {
    return (
      <div className="flex flex-col items-center justify-end flex-1 px-6 pb-9">
        <DropZone onDrop={handleDrop} />
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center justify-end flex-1 px-6 pb-9">
      <div className="w-full max-w-[640px] flex flex-col gap-0 mb-5 flex-1 overflow-y-auto pt-5 scroll-fade">
        {chips.length > 0 && (
          <AgentMessage agentName="Agent Dossier">
            {'J\u2019ai charg\u00e9 les faits produits par le backend runtime.'}
            <div className="flex flex-wrap gap-1.5 mt-2.5">
              {chips.map((c, i) => <Chip key={i} label={c.label} highlight={c.highlight} />)}
            </div>
          </AgentMessage>
        )}
        {documents.length > 0 && <UserMessage>{'Sources rattach\u00e9es au dossier'}</UserMessage>}
        <AgentMessage agentName="Agent Dossier" last={replies.length === 0}>
          {documents.length === 0
            ? "Aucune source runtime n\u2019est encore rattach\u00e9e."
            : "Ces sources viennent des art\u00e9facts runtime. Elles restent \u00e0 valider avant toute conclusion professionnelle."}
          {documents.length > 0 && (
            <div className="flex flex-col gap-1.5 mt-2.5">
              {documents.map(doc => <DocItem key={doc.id} doc={doc} />)}
            </div>
          )}
          <button
            onClick={() => setShowDropZone(true)}
            className="mt-3 text-[12px] text-[#8a8780] hover:text-[#1a1916] underline underline-offset-2 bg-transparent border-none cursor-pointer font-sans"
          >
            + Ajouter un fichier local
          </button>
        </AgentMessage>
        {uploads.map((u, i) => (
          u.state === 'uploading' ? (
            <div key={i} className="text-[12px] text-[#8a8780] px-1 py-0.5 animate-pulse">
              {'\u2026 '}{u.name}
            </div>
          ) : (
            <div key={i} className="rounded-[8px] px-3 py-2 text-[12px] text-red-700 bg-red-50/80 border border-red-200/60">
              {u.name}{' — '}{u.error}
            </div>
          )
        ))}
        {replies.map((reply, index) => (
          <AgentMessage key={reply.id} agentName={reply.agent} last={index === replies.length - 1}>
            <pre className="whitespace-pre-wrap font-sans text-[13px] leading-6">{reply.answer}</pre>
          </AgentMessage>
        ))}
      </div>
      <ChatInput placeholder="Questionner l'Agent Dossier..." onSend={handleAsk} />
    </div>
  )
}
