'use client'

import { useState, useEffect } from 'react'
import AgentMessage from '@/components/shared/AgentMessage'
import UserMessage from '@/components/shared/UserMessage'
import RapportArtifact from '@/components/shared/RapportArtifact'
import RapportDoc from '@/components/shared/RapportDoc'
import ChatInput from '@/components/shared/ChatInput'
import PanelLoader from '@/components/shared/PanelLoader'
import { fetchAdjustments } from '@/lib/supabase/queries/adjustments'
import type { Adjustment } from '@/types'

interface Props {
  dossierId: string | null
  dossierAddress: string
}

export default function RapportPanel({ dossierId, dossierAddress }: Props) {
  const [split, setSplit] = useState(false)
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
    <div className={`flex flex-1 overflow-hidden ${split ? 'flex-row' : 'flex-col items-center justify-end'}`}>
      {/* Chat column */}
      <div className={`flex flex-col ${split ? 'flex-[0_0_380px] border-r border-black/[.07] overflow-hidden' : 'w-full items-center justify-end'}`}>
        <div className={`flex flex-col gap-0 mb-5 flex-1 overflow-y-auto pt-5 scroll-fade ${split ? 'px-5' : 'w-full max-w-[640px] px-6'}`}>
          <UserMessage>Génère le rapport OEAQ complet pour {dossierAddress || 'ce dossier'}.</UserMessage>
          <AgentMessage agentName="Agent Rapport" last>
            Le rapport d'évaluation OEAQ a été rédigé et certifié.
            <RapportArtifact
              title="Rapport d'évaluation immobilière"
              subtitle={`Certifié OEAQ · ${dossierAddress || 'Dossier en cours'}`}
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
      {split && (
        <RapportDoc
          address={dossierAddress}
          valeur={median ? formatPrice(median) : null}
          onClose={() => setSplit(false)}
        />
      )}
    </div>
  )
}
