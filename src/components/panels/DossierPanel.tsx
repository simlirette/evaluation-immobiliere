'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import AgentMessage from '@/components/shared/AgentMessage'
import UserMessage from '@/components/shared/UserMessage'
import Chip from '@/components/shared/Chip'
import DocItem from '@/components/shared/DocItem'
import ChatInput from '@/components/shared/ChatInput'
import DropZone from '@/components/shared/DropZone'
import { fetchDocuments, uploadDocument } from '@/lib/supabase/queries/documents'
import { fetchPropertyFacts } from '@/lib/supabase/queries/property_facts'
import { createDossier } from '@/lib/supabase/queries/dossiers'
import PanelLoader from '@/components/shared/PanelLoader'
import type { Document, FactChip } from '@/types'

interface Props {
  isNew: boolean
  dossierId: string | null
}

function NewDossierForm() {
  const router = useRouter()
  const [address, setAddress] = useState('')
  const [propertyType, setPropertyType] = useState('')
  const [neighborhood, setNeighborhood] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
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
    } catch {
      setError('Erreur lors de la création du dossier.')
      setLoading(false)
    }
  }

  const inputStyle: React.CSSProperties = {
    background: 'var(--input-bg)',
    border: '1px solid var(--input-border)',
  }

  return (
    <div className="w-full max-w-[480px] flex flex-col gap-6 pb-9">
      <div className="text-center">
        <div
          className="text-[20px] font-medium text-[#1a1916] tracking-[-.01em]"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          Nouveau dossier
        </div>
        <p className="mt-1 text-[13px] text-[#8a8780]">Renseignez les informations de base de la propriété</p>
      </div>

      {error && (
        <div className="rounded-[10px] px-4 py-3 text-[13px] text-red-700 bg-red-50/80 border border-red-200/60">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <label className="text-[12px] text-[#8a8780] font-medium">Adresse</label>
          <input
            type="text"
            required
            value={address}
            onChange={e => setAddress(e.target.value)}
            placeholder="1842, rue Sherbrooke O."
            className="w-full rounded-[10px] px-4 py-2.5 text-[14px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
            style={inputStyle}
          />
        </div>

        <div className="flex gap-3">
          <div className="flex flex-col gap-1.5 flex-1">
            <label className="text-[12px] text-[#8a8780] font-medium">Type de propriété</label>
            <input
              type="text"
              required
              value={propertyType}
              onChange={e => setPropertyType(e.target.value)}
              placeholder="Unifamiliale"
              className="w-full rounded-[10px] px-4 py-2.5 text-[14px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
              style={inputStyle}
            />
          </div>
          <div className="flex flex-col gap-1.5 flex-1">
            <label className="text-[12px] text-[#8a8780] font-medium">Quartier</label>
            <input
              type="text"
              required
              value={neighborhood}
              onChange={e => setNeighborhood(e.target.value)}
              placeholder="Westmount"
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
          {loading ? 'Création…' : 'Créer le dossier'}
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
    const newDocs = await Promise.all(Array.from(files).map(f => uploadDocument(dossierId, f)))
    setDocuments(prev => [...prev, ...newDocs])
    setShowDropZone(false)
  }

  // Loading existing dossier
  if (!isNew && (!dossierId || loading)) return <PanelLoader />

  // Creating new dossier — show form
  if (isNew && !dossierId) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 px-6 pb-9">
        <NewDossierForm />
      </div>
    )
  }

  // Existing dossier — show drop zone or chat
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
            J'ai analysé les <strong>{documents.length} documents</strong> soumis pour ce dossier. Voici les faits extraits :
            <div className="flex flex-wrap gap-1.5 mt-2.5">
              {chips.map((c, i) => <Chip key={i} label={c.label} highlight={c.highlight} />)}
            </div>
          </AgentMessage>
        )}
        {documents.length > 0 && (
          <UserMessage>Voici les documents du dossier</UserMessage>
        )}
        <AgentMessage agentName="Agent Dossier" last>
          {documents.length === 0
            ? "Joignez les documents du dossier pour commencer l\u2019extraction des faits."
            : "Vous pouvez ajouter d\u2019autres documents ou poser des questions sur ce dossier."}
          {documents.length > 0 && (
            <div className="flex flex-col gap-1.5 mt-2.5">
              {documents.map(doc => <DocItem key={doc.id} doc={doc} />)}
            </div>
          )}
          <button
            onClick={() => setShowDropZone(true)}
            className="mt-3 text-[12px] text-[#8a8780] hover:text-[#1a1916] underline underline-offset-2 bg-transparent border-none cursor-pointer font-sans"
          >
            + Ajouter des documents
          </button>
        </AgentMessage>
      </div>
      <ChatInput placeholder="Écrivez ou collez vos notes ici..." />
    </div>
  )
}
