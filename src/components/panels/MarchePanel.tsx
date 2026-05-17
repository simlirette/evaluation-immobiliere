'use client'

import { useEffect, useState } from 'react'
import AgentMessage from '@/components/shared/AgentMessage'
import UserMessage from '@/components/shared/UserMessage'
import ComparableItem from '@/components/shared/ComparableItem'
import ChatInput from '@/components/shared/ChatInput'
import PanelLoader from '@/components/shared/PanelLoader'
import PanelError from '@/components/shared/PanelError'
import { fetchComparables } from '@/lib/supabase/queries/comparables'
import { fetchRuntimeEnrichment, sendRuntimeMessage } from '@/lib/runtime-api'
import { printWindow } from '@/lib/print-window'
import { buildMarcheHtml } from '@/lib/marche-html'
import type { Comparable, EnrichmentMarche } from '@/types'

interface Props {
  dossierId: string | null
  address?: string
}

function fmt(n: number | null | undefined, digits = 1): string {
  return n != null ? new Intl.NumberFormat('fr-CA', { maximumFractionDigits: digits }).format(n) : '—'
}

function MarketChip({ label, value, unit = '' }: { label: string; value: string; unit?: string }) {
  return (
    <div className="flex flex-col gap-0.5 px-3 py-2 rounded-lg bg-[rgba(0,0,0,.04)] dark:bg-[rgba(255,255,255,.05)]">
      <span className="text-[10px] uppercase tracking-wider text-[#8a8780]">{label}</span>
      <span className="text-[13px] font-semibold text-[#1a1916] dark:text-white">
        {value}{unit && <span className="text-[11px] font-normal text-[#8a8780] ml-0.5">{unit}</span>}
      </span>
    </div>
  )
}

const TENSION_COLOR: Record<string, string> = {
  'tendu':      'text-red-600 dark:text-red-400',
  'équilibré':  'text-amber-600 dark:text-amber-400',
  'détendu':    'text-emerald-600 dark:text-emerald-400',
}

function MarcheContexte({ m }: { m: EnrichmentMarche }) {
  const chips: Array<{ label: string; value: string; unit?: string }> = []
  if (m.taux_inoccupation_pct != null) chips.push({ label: 'Inoccupation', value: fmt(m.taux_inoccupation_pct), unit: '%' })
  if (m.nhpi_variation_pct != null)    chips.push({ label: 'NHPI variation', value: (m.nhpi_variation_pct >= 0 ? '+' : '') + fmt(m.nhpi_variation_pct), unit: '%/an' })
  if (m.taux_hypo_5ans_pct != null)    chips.push({ label: 'Hypo 5 ans', value: fmt(m.taux_hypo_5ans_pct), unit: '%' })
  if (m.taux_directeur_pct != null)    chips.push({ label: 'Taux directeur', value: fmt(m.taux_directeur_pct), unit: '%' })
  if (m.taux_chomage_pct != null)      chips.push({ label: 'Chômage CMA', value: fmt(m.taux_chomage_pct), unit: '%' })
  if (m.taux_emploi_pct != null)       chips.push({ label: 'Emploi CMA', value: fmt(m.taux_emploi_pct), unit: '%' })
  if (m.taux_participation_pct != null) chips.push({ label: 'Participation CMA', value: fmt(m.taux_participation_pct), unit: '%' })
  if (m.mises_en_chantier_12m != null) chips.push({ label: 'Mises en chantier', value: fmt(m.mises_en_chantier_12m, 0), unit: '/an' })
  if (m.completions_12m != null)       chips.push({ label: 'Complétions neuf', value: fmt(m.completions_12m, 0), unit: '/an' })
  if (m.unites_en_construction != null) chips.push({ label: 'En construction', value: fmt(m.unites_en_construction, 0), unit: 'unités' })
  if (m.taux_absorption_pct != null)   chips.push({ label: 'Absorption', value: fmt(m.taux_absorption_pct), unit: '%' })
  if (m.unites_absorbees_total != null) chips.push({ label: 'Unités absorbées', value: fmt(m.unites_absorbees_total, 0) })
  if (m.ipc_variation_logement_pct != null) chips.push({ label: 'IPC logement', value: (m.ipc_variation_logement_pct >= 0 ? '+' : '') + fmt(m.ipc_variation_logement_pct), unit: '%/an' })
  if (chips.length === 0 && !m.score_marche) return null
  return (
    <div className="mt-2 mb-1">
      {m.score_marche != null && (
        <div className="mb-2">
          <div className="flex items-center justify-between">
            <div className="text-[11px] uppercase tracking-widest text-[#8a8780]">Score de marché</div>
            <div className="flex items-center gap-2">
              <span className="text-[13px] font-semibold text-[#1a1916] dark:text-white">
                {fmt(m.score_marche)}<span className="text-[11px] font-normal text-[#8a8780]">/10</span>
              </span>
              {m.tension_locative && (
                <span className={`text-[11px] font-medium ${TENSION_COLOR[m.tension_locative] ?? 'text-[#6a6763]'}`}>
                  {m.tension_locative}
                </span>
              )}
            </div>
          </div>
          {m.marche_interpretation && (
            <div className="text-[12px] text-[#6a6763] dark:text-[#9a9790] mt-0.5">{m.marche_interpretation}</div>
          )}
        </div>
      )}
      {chips.length > 0 && (
        <>
          <div className="text-[11px] uppercase tracking-widest text-[#8a8780] mb-2">Contexte de marché</div>
          <div className="flex flex-wrap gap-2">
            {chips.map(c => <MarketChip key={c.label} label={c.label} value={c.value} unit={c.unit} />)}
          </div>
        </>
      )}
    </div>
  )
}

export default function MarchePanel({ dossierId, address }: Props) {
  const [comparables, setComparables] = useState<Comparable[]>([])
  const [marche, setMarche] = useState<EnrichmentMarche | null>(null)
  const [replies, setReplies] = useState<string[]>([])
  const [asking, setAsking] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  function load() {
    if (!dossierId) return
    setLoading(true)
    setError(false)
    Promise.all([
      fetchComparables(dossierId),
      fetchRuntimeEnrichment(dossierId),
    ]).then(([comps, enrichment]) => {
      setComparables(comps)
      setMarche(enrichment?.marche ?? null)
      setLoading(false)
    }).catch(() => { setError(true); setLoading(false) })
  }

  useEffect(() => { load() }, [dossierId]) // eslint-disable-line react-hooks/exhaustive-deps

  async function handleAsk(value: string) {
    if (!dossierId) return
    setAsking(true)
    try {
      const response = await sendRuntimeMessage(dossierId, value, 'comps-market')
      setReplies(prev => [...prev, response.message.answer])
    } finally {
      setAsking(false)
    }
  }

  if (!dossierId || loading) return <PanelLoader />
  if (error) return <PanelError onRetry={load} />

  return (
    <div className="flex flex-col items-center justify-end flex-1 px-6 pb-9">
      <div className="w-full max-w-[640px] flex flex-col gap-0 mb-5 flex-1 overflow-y-auto pt-5 scroll-fade">
        <UserMessage>Comparer les ventes retenues et expliquer leur pertinence.</UserMessage>
        <AgentMessage agentName="Agent Marché">
          {'J\u2019ai charg\u00e9 '}<strong>{comparables.length} comparables</strong>{' depuis les art\u00e9facts du backend.'}
          {marche && <MarcheContexte m={marche} />}
          <div className="flex flex-col gap-2 mt-2.5">
            {comparables.map(c => <ComparableItem key={c.id} comp={c} />)}
          </div>
        </AgentMessage>
        {comparables.length > 0 && (
          <AgentMessage agentName="Agent Marché" last={replies.length === 0 && !asking}>
            {'Les comparables sont retenus par score, source et r\u00e9cence. Les sources restent \u00e0 valider avant signature.'}
          </AgentMessage>
        )}
        {replies.map((r, i) => (
          <AgentMessage key={i} agentName="Agent Marché" last={i === replies.length - 1 && !asking}>
            <pre className="whitespace-pre-wrap font-sans text-[13px] leading-6">{r}</pre>
          </AgentMessage>
        ))}
        {asking && (
          <AgentMessage agentName="Agent Marché" last>
            <span className="text-[#b5b2ac] text-[13px] animate-pulse">···</span>
          </AgentMessage>
        )}
      </div>
      {comparables.length > 0 && (
        <div className="w-full max-w-[640px] flex justify-end mb-3">
          <button
            type="button"
            onClick={() => printWindow(buildMarcheHtml(comparables, marche, address), address ?? 'Marché')}
            className="rounded-full px-3.5 py-2 text-[11px] bg-black/[.05] text-[#5a5854] hover:bg-black/[.09] transition-colors"
          >
            🖨 Imprimer le rapport marché
          </button>
        </div>
      )}
      <ChatInput placeholder="Questionner l'Agent Marché..." onSend={handleAsk} disabled={asking} />
    </div>
  )
}
