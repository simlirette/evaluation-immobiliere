'use client'

import { useEffect, useRef, useState } from 'react'
import AgentMessage from '@/components/shared/AgentMessage'
import UserMessage from '@/components/shared/UserMessage'
import AdjustmentsTable from '@/components/shared/AdjustmentsTable'
import ValeurCard from '@/components/shared/ValeurCard'
import ChatInput from '@/components/shared/ChatInput'
import PanelLoader from '@/components/shared/PanelLoader'
import PanelError from '@/components/shared/PanelError'
import { fetchAdjustments } from '@/lib/supabase/queries/adjustments'
import { fetchComparables } from '@/lib/supabase/queries/comparables'
import { fetchAppState, fetchRuntimeEnrichment, sendRuntimeMessage } from '@/lib/runtime-api'
import { printWindow } from '@/lib/print-window'
import { buildAnalyseHtml } from '@/lib/analyse-html'
import { summarizeAdjustments } from '@/lib/summarize-adjustments'
import { buildOEAQChecklist } from '@/lib/build-oeaq-checklist'
import { computeSubjectContext } from '@/lib/compute-subject-context'
import { buildAdjustmentsCsv } from '@/lib/build-adjustments-csv'
import { computeAdjustmentProfile } from '@/lib/compute-adjustment-profile'
import { formatCAD, fmtNum, formatPct } from '@/lib/format-number'
import { formatAgentError } from '@/lib/agent-error'
import type { Comparable, Adjustment, EnrichmentFinancier } from '@/types'

interface Props {
  dossierId: string | null
  address?: string
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

function formatPrice(n: number) { return formatCAD(n) }
function fmt(n: number | null | undefined, digits = 1): string { return fmtNum(n, digits) }

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
      value: formatPct(f.ratio_revenu_pct),
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
      value: formatPct(f.ratio_mensualite_revenu_pct),
      sub: f.seuil_propriete ?? undefined,
      colorClass: SEUIL_COLOR[f.seuil_propriete ?? ''] ?? undefined,
    })
  if (f.ratio_loyer_revenu_pct != null)
    rows.push({
      label: 'Ratio loyer marché / revenu médian',
      value: formatPct(f.ratio_loyer_revenu_pct),
      sub: f.seuil_location ?? undefined,
      colorClass: SEUIL_COLOR[f.seuil_location ?? ''] ?? undefined,
    })
  if (f.revenu_median_menage != null)
    rows.push({ label: 'Revenu médian ménage CMA (2021)', value: formatPrice(f.revenu_median_menage) })
  if (f.pct_proprietaires != null)
    rows.push({ label: 'Propriétaires / locataires', value: `${formatPct(f.pct_proprietaires, 0)} / ${formatPct(f.pct_locataires ?? null, 0)}` })
  if (f.valeur_mediane_logement != null)
    rows.push({ label: 'Valeur médiane logement (2021)', value: formatPrice(f.valeur_mediane_logement) })
  if (f.ratio_dette_revenu_pct != null)
    rows.push({
      label: 'Ratio dette / revenu (Canada)',
      value: formatPct(f.ratio_dette_revenu_pct),
      sub: f.variation_dette_revenu_pct != null
        ? `${f.variation_dette_revenu_pct >= 0 ? '+' : ''}${formatPct(f.variation_dette_revenu_pct)} /an`
        : undefined,
      colorClass: f.ratio_dette_revenu_pct > 175 ? 'text-red-600 dark:text-red-400'
        : f.ratio_dette_revenu_pct > 150 ? 'text-amber-600 dark:text-amber-400'
        : undefined,
    })
  if (f.ratio_hypotheque_revenu_pct != null)
    rows.push({ label: 'Ratio hypothèque / revenu (Canada)', value: formatPct(f.ratio_hypotheque_revenu_pct) })
  if (f.taux_epargne_pct != null)
    rows.push({ label: "Taux d\u2019\u00e9pargne (Canada)", value: formatPct(f.taux_epargne_pct) })

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

export default function AnalysePanel({ dossierId, address }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const [comparables, setComparables] = useState<Comparable[]>([])
  const [adjustments, setAdjustments] = useState<Adjustment[]>([])
  const [conclusion, setConclusion] = useState<number | null>(null)
  const [status, setStatus] = useState('A_VALIDER_PAR_EVALUATEUR_AGREE')
  const [financier, setFinancier] = useState<EnrichmentFinancier | null>(null)
  const [replies, setReplies] = useState<string[]>([])
  const [asking, setAsking] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  function load() {
    if (!dossierId) return
    setLoading(true)
    setError(false)
    Promise.all([
      fetchAdjustments(dossierId),
      fetchComparables(dossierId),
      fetchAppState(dossierId),
      fetchRuntimeEnrichment(dossierId),
    ]).then(([rows, comps, state, enrichment]) => {
      setAdjustments(rows)
      setComparables(comps)
      setConclusion(state.active?.valuation.conclusion.value ?? null)
      setStatus(state.active?.valuation.status ?? 'A_VALIDER_PAR_EVALUATEUR_AGREE')
      setFinancier(enrichment?.financier ?? null)
      setLoading(false)
    }).catch(() => { setError(true); setLoading(false) })
  }

  useEffect(() => { load() }, [dossierId]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [replies, asking])

  async function handleAsk(value: string) {
    if (!dossierId) return
    setAsking(true)
    try {
      const response = await sendRuntimeMessage(dossierId, value, 'valuation-draft')
      setReplies(prev => [...prev, response.message.answer])
    } catch (err) {
      setReplies(prev => [...prev, formatAgentError(err)])
    } finally {
      setAsking(false)
    }
  }

  if (!dossierId || loading) return <PanelLoader />
  if (error) return <PanelError onRetry={load} />

  return (
    <div className="flex flex-col items-center justify-end flex-1 px-6 pb-9">
      <div ref={scrollRef} className="w-full max-w-[640px] flex flex-col gap-0 mb-5 flex-1 overflow-y-auto pt-5 scroll-fade">
        <UserMessage>{'Afficher la valeur propos\u00e9e et la trace d\u2019ajustements.'}</UserMessage>
        <AgentMessage agentName="Agent Analyse">
          {'Voici la trace d\u2019analyse issue du runtime. Elle n\u2019est pas une certification.'}
          <AdjustmentsTable rows={adjustments} />
          {conclusion !== null && (() => {
            const summary = summarizeAdjustments(adjustments)
            const range = summary && adjustments.length > 1
              ? `${formatPrice(summary.min)} – ${formatPrice(summary.max)}`
              : undefined
            const ctx = adjustments.length > 0 ? computeSubjectContext(conclusion, adjustments) : null
            return (
              <>
                <ValeurCard
                  median={`Conclusion proposée\u00a0: ${formatPrice(conclusion)}`}
                  range={range}
                />
                {ctx && (
                  <div className={`mt-1.5 text-[11px] px-1 ${ctx.withinRange ? 'text-[#6a6763]' : 'text-amber-700 dark:text-amber-400'}`}>
                    {ctx.withinRange
                      ? `Conclusion dans la fourchette des valeurs indiquées${Math.abs(ctx.deviationFromMedianPct) >= 1 ? ` · ${ctx.deviationFromMedianPct > 0 ? '+' : ''}${ctx.deviationFromMedianPct} % vs médiane` : ' · en ligne avec la médiane'}.`
                      : `⚠ Conclusion hors de la fourchette des valeurs indiquées (${ctx.deviationFromMedianPct > 0 ? '+' : ''}${ctx.deviationFromMedianPct} % vs médiane) — justification requise.`
                    }
                  </div>
                )}
              </>
            )
          })()}
          {financier && <FinancierContexte f={financier} />}
          {adjustments.length > 0 && (() => {
            const checklist = buildOEAQChecklist(comparables, adjustments)
            const hasWarning = checklist.some(c => !c.pass)
            return (
              <div className="mt-3 mb-1">
                <div className="text-[11px] uppercase tracking-widest text-[#8a8780] mb-2">Conformité OEAQ</div>
                <div className={`flex flex-col gap-1 rounded-xl px-3 py-2 ${hasWarning ? 'bg-amber-50/70 dark:bg-amber-900/20 border border-amber-200/50' : 'bg-[rgba(0,0,0,.03)] dark:bg-[rgba(255,255,255,.04)]'}`}>
                  {checklist.map(c => (
                    <div key={c.id} className="flex items-start gap-2 py-0.5">
                      <span className={`mt-0.5 text-[11px] font-semibold flex-shrink-0 ${c.pass ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-700 dark:text-amber-400'}`}>
                        {c.pass ? '✓' : '⚠'}
                      </span>
                      <div className="flex-1 min-w-0">
                        <span className={`text-[12px] ${c.pass ? 'text-[#4a4845] dark:text-[#b5b2ac]' : 'text-amber-800 dark:text-amber-300'}`}>
                          {c.rule}
                        </span>
                        {c.message && (
                          <div className="text-[11px] text-amber-700 dark:text-amber-400 mt-0.5">{c.message}</div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })()}
          {adjustments.length > 0 && (() => {
            const profile = computeAdjustmentProfile(adjustments)
            if (!profile || profile.grossTotal === 0) return null
            const active = profile.types.filter(t => t.totalAbsolute > 0)
            return (
              <div className="mt-3 mb-1">
                <div className="text-[11px] uppercase tracking-widest text-[#8a8780] mb-2">Répartition des ajustements</div>
                <div className="flex flex-col gap-1">
                  {active.map(t => (
                    <div key={t.type} className="flex items-center gap-2">
                      <span className="text-[11px] text-[#6a6763] dark:text-[#9a9790] w-16 flex-shrink-0">{t.label}</span>
                      <div className="flex-1 h-1.5 rounded-full bg-black/[.06] dark:bg-white/[.08] overflow-hidden">
                        <div
                          className={`h-full rounded-full ${t.direction === 'positive' ? 'bg-emerald-500/60' : t.direction === 'negative' ? 'bg-red-400/60' : 'bg-[#b5b2ac]/60'}`}
                          style={{ width: `${t.pctOfGrossTotal}%` }}
                        />
                      </div>
                      <span className={`text-[10px] w-8 text-right flex-shrink-0 ${t.direction === 'positive' ? 'text-emerald-600 dark:text-emerald-400' : t.direction === 'negative' ? 'text-red-500' : 'text-[#b5b2ac]'}`}>
                        {t.pctOfGrossTotal}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )
          })()}
        </AgentMessage>
        <AgentMessage agentName="Agent Analyse" last={replies.length === 0 && !asking}>
          {'Statut\u00a0: '}<strong>{statusLabel(status)}</strong>{'. La validation d\u2019un \u00e9valuateur agr\u00e9\u00e9 reste obligatoire avant toute diffusion.'}
        </AgentMessage>
        {replies.map((r, i) => (
          <AgentMessage key={i} agentName="Agent Analyse" last={i === replies.length - 1 && !asking}>
            <pre className="whitespace-pre-wrap font-sans text-[13px] leading-6">{r}</pre>
          </AgentMessage>
        ))}
        {asking && (
          <AgentMessage agentName="Agent Analyse" last>
            <span className="text-[#b5b2ac] text-[13px] animate-pulse">···</span>
          </AgentMessage>
        )}
      </div>
      {(adjustments.length > 0 || conclusion !== null) && (
        <div className="w-full max-w-[640px] flex justify-end gap-2 mb-3">
          {adjustments.length > 0 && (
            <button
              type="button"
              onClick={() => {
                const csv = buildAdjustmentsCsv(adjustments)
                const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = `ajustements${address ? '-' + address.slice(0, 30).replace(/\s+/g, '-') : ''}.csv`
                a.click()
                URL.revokeObjectURL(url)
              }}
              className="rounded-full px-3.5 py-2 text-[11px] bg-black/[.05] text-[#5a5854] hover:bg-black/[.09] transition-colors"
            >
              ⬇ Export CSV
            </button>
          )}
          <button
            type="button"
            onClick={() => printWindow(buildAnalyseHtml(adjustments, conclusion, status, financier, address, comparables), address ?? 'Analyse')}
            className="rounded-full px-3.5 py-2 text-[11px] bg-black/[.05] text-[#5a5854] hover:bg-black/[.09] transition-colors"
          >
            {`🖨 Imprimer l'analyse`}
          </button>
        </div>
      )}
      <ChatInput placeholder="Questionner l'Agent Analyse..." onSend={handleAsk} disabled={asking} />
    </div>
  )
}
