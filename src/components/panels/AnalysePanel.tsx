'use client'

import { useEffect, useState } from 'react'
import AgentMessage from '@/components/shared/AgentMessage'
import UserMessage from '@/components/shared/UserMessage'
import AdjustmentsTable from '@/components/shared/AdjustmentsTable'
import ValeurCard from '@/components/shared/ValeurCard'
import ChatInput from '@/components/shared/ChatInput'
import PanelLoader from '@/components/shared/PanelLoader'
import PanelError from '@/components/shared/PanelError'
import { fetchAdjustments } from '@/lib/supabase/queries/adjustments'
import { fetchAppState, fetchRuntimeEnrichment, sendRuntimeMessage } from '@/lib/runtime-api'
import type { Adjustment, EnrichmentFinancier } from '@/types'

interface Props {
  dossierId: string | null
}

const VALUATION_STATUS_LABELS: Record<string, string> = {
  A_VALIDER_PAR_EVALUATEUR_AGREE: 'À valider — évaluateur agréé requis',
  VALIDE: 'Validé en revue interne',
  A_CORRIGER: 'À corriger',
  PRET_REVUE: 'Prêt pour revue',
  ASSISTANCE_DOSSIER_ACTIVE: 'Assistance active',
  UNKNOWN: 'Statut inconnu',
}

function statusLabel(raw: string): string {
  return VALUATION_STATUS_LABELS[raw] ?? raw.replace(/_/g, ' ')
}

function formatPrice(n: number) {
  return new Intl.NumberFormat('fr-CA', {
    style: 'currency',
    currency: 'CAD',
    maximumFractionDigits: 0,
  }).format(n).replace('CA', '').trim()
}

function fmt(n: number | null | undefined, digits = 1): string {
  return n != null ? new Intl.NumberFormat('fr-CA', { maximumFractionDigits: digits }).format(n) : '—'
}

const SEUIL_COLOR: Record<string, string> = {
  'abordable': 'text-emerald-600 dark:text-emerald-400',
  'limite': 'text-amber-600 dark:text-amber-400',
  'non abordable': 'text-red-600 dark:text-red-400',
}

function FinancierContexte({ f }: { f: EnrichmentFinancier }) {
  const rows: Array<{ label: string; value: string; sub?: string; colorClass?: string }> = []

  if (f.total_mensuel != null)
    rows.push({ label: 'Coût mensuel total estimé', value: formatPrice(f.total_mensuel) })
  if (f.versement_hypo_mensuel != null)
    rows.push({ label: 'Dont versement hypothécaire', value: formatPrice(f.versement_hypo_mensuel) })
  if (f.ratio_revenu_pct != null)
    rows.push({
      label: 'Ratio coûts / revenu médian',
      value: `${fmt(f.ratio_revenu_pct)} %`,
      sub: f.interpretation_couts ?? undefined,
      colorClass: f.ratio_revenu_pct > 40 ? 'text-red-600 dark:text-red-400'
        : f.ratio_revenu_pct > 30 ? 'text-amber-600 dark:text-amber-400'
        : 'text-emerald-600 dark:text-emerald-400',
    })
  if (f.versement_mensuel_estime != null)
    rows.push({ label: 'Mensualité estimée (25 ans, 20 % MDP)', value: formatPrice(f.versement_mensuel_estime) })
  if (f.ratio_mensualite_revenu_pct != null)
    rows.push({
      label: 'Ratio mensualité / revenu médian',
      value: `${fmt(f.ratio_mensualite_revenu_pct)} %`,
      sub: f.seuil_propriete ?? undefined,
      colorClass: SEUIL_COLOR[f.seuil_propriete ?? ''] ?? undefined,
    })
  if (f.ratio_loyer_revenu_pct != null)
    rows.push({
      label: 'Ratio loyer marché / revenu médian',
      value: `${fmt(f.ratio_loyer_revenu_pct)} %`,
      sub: f.seuil_location ?? undefined,
      colorClass: SEUIL_COLOR[f.seuil_location ?? ''] ?? undefined,
    })
  if (f.revenu_median_menage != null)
    rows.push({ label: 'Revenu médian ménage CMA (2021)', value: formatPrice(f.revenu_median_menage) })
  if (f.pct_proprietaires != null)
    rows.push({ label: 'Propriétaires / locataires', value: `${fmt(f.pct_proprietaires, 0)} % / ${fmt(f.pct_locataires ?? null, 0)} %` })
  if (f.valeur_mediane_logement != null)
    rows.push({ label: 'Valeur médiane logement (2021)', value: formatPrice(f.valeur_mediane_logement) })
  if (f.ratio_dette_revenu_pct != null)
    rows.push({
      label: 'Ratio dette / revenu (Canada)',
      value: `${fmt(f.ratio_dette_revenu_pct)} %`,
      sub: f.variation_dette_revenu_pct != null
        ? `${f.variation_dette_revenu_pct >= 0 ? '+' : ''}${fmt(f.variation_dette_revenu_pct)} % /an`
        : undefined,
      colorClass: f.ratio_dette_revenu_pct > 175 ? 'text-red-600 dark:text-red-400'
        : f.ratio_dette_revenu_pct > 150 ? 'text-amber-600 dark:text-amber-400'
        : undefined,
    })
  if (f.ratio_hypotheque_revenu_pct != null)
    rows.push({ label: 'Ratio hypothèque / revenu (Canada)', value: `${fmt(f.ratio_hypotheque_revenu_pct)} %` })
  if (f.taux_epargne_pct != null)
    rows.push({ label: "Taux d\u2019\u00e9pargne (Canada)", value: `${fmt(f.taux_epargne_pct)} %` })

  if (rows.length === 0) return null

  return (
    <div className="mt-3 mb-1">
      <div className="text-[11px] uppercase tracking-widest text-[#8a8780] mb-2">Contexte financier</div>
      <div className="flex flex-col divide-y divide-[rgba(0,0,0,.06)] rounded-xl overflow-hidden bg-[rgba(0,0,0,.03)] dark:bg-[rgba(255,255,255,.04)]">
        {rows.map(row => (
          <div key={row.label} className="flex items-baseline justify-between px-3 py-2 gap-4">
            <span className="text-[12px] text-[#6a6763] dark:text-[#9a9790] flex-1">{row.label}</span>
            <div className="text-right flex-shrink-0">
              <span className={`text-[13px] font-semibold ${row.colorClass ?? 'text-[#1a1916] dark:text-white'}`}>
                {row.value}
              </span>
              {row.sub && (
                <div className={`text-[11px] ${row.colorClass ?? 'text-[#8a8780]'}`}>{row.sub}</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function AnalysePanel({ dossierId }: Props) {
  const [adjustments, setAdjustments] = useState<Adjustment[]>([])
  const [conclusion, setConclusion] = useState<number | null>(null)
  const [status, setStatus] = useState('A_VALIDER_PAR_EVALUATEUR_AGREE')
  const [financier, setFinancier] = useState<EnrichmentFinancier | null>(null)
  const [reply, setReply] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  function load() {
    if (!dossierId) return
    setLoading(true)
    setError(false)
    Promise.all([
      fetchAdjustments(dossierId),
      fetchAppState(dossierId),
      fetchRuntimeEnrichment(dossierId),
    ]).then(([rows, state, enrichment]) => {
      setAdjustments(rows)
      setConclusion(state.active?.valuation.conclusion.value ?? null)
      setStatus(state.active?.valuation.status ?? 'A_VALIDER_PAR_EVALUATEUR_AGREE')
      setFinancier(enrichment?.financier ?? null)
      setLoading(false)
    }).catch(() => { setError(true); setLoading(false) })
  }

  useEffect(() => { load() }, [dossierId]) // eslint-disable-line react-hooks/exhaustive-deps

  async function handleAsk(value: string) {
    if (!dossierId) return
    const response = await sendRuntimeMessage(dossierId, value, 'valuation-draft')
    setReply(response.message.answer)
  }

  if (!dossierId || loading) return <PanelLoader />
  if (error) return <PanelError onRetry={load} />

  return (
    <div className="flex flex-col items-center justify-end flex-1 px-6 pb-9">
      <div className="w-full max-w-[640px] flex flex-col gap-0 mb-5 flex-1 overflow-y-auto pt-5 scroll-fade">
        <UserMessage>{'Afficher la valeur propos\u00e9e et la trace d\u2019ajustements.'}</UserMessage>
        <AgentMessage agentName="Agent Analyse">
          {'Voici la trace d\u2019analyse issue du runtime. Elle n\u2019est pas une certification.'}
          <AdjustmentsTable rows={adjustments} />
          {conclusion !== null && (
            <ValeurCard
              median={`Conclusion propos\u00e9e\u00a0: ${formatPrice(conclusion)}`}
            />
          )}
          {financier && <FinancierContexte f={financier} />}
        </AgentMessage>
        <AgentMessage agentName="Agent Analyse" last={!reply}>
          {'Statut\u00a0: '}<strong>{statusLabel(status)}</strong>{'. La validation d\u2019un \u00e9valuateur agr\u00e9\u00e9 reste obligatoire avant toute diffusion.'}
        </AgentMessage>
        {reply && (
          <AgentMessage agentName="Agent Analyse" last>
            <pre className="whitespace-pre-wrap font-sans text-[13px] leading-6">{reply}</pre>
          </AgentMessage>
        )}
      </div>
      <ChatInput placeholder="Questionner l'Agent Analyse..." onSend={handleAsk} />
    </div>
  )
}
