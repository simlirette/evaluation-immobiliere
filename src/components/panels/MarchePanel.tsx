'use client'

import { Fragment, useEffect, useRef, useState } from 'react'
import AgentMessage from '@/components/shared/AgentMessage'
import UserMessage from '@/components/shared/UserMessage'
import ComparableItem from '@/components/shared/ComparableItem'
import ChatInput from '@/components/shared/ChatInput'
import PanelLoader from '@/components/shared/PanelLoader'
import PanelError from '@/components/shared/PanelError'
import { fetchRuntimeEnrichment, fetchRuntimeComparables, fetchRuntimeAdjustments } from '@/lib/runtime-api'
import SourceDiagnosticPanel from '@/components/shared/SourceDiagnosticPanel'
import { useAgentChat } from '@/hooks/useAgentChat'
import { printWindow } from '@/lib/print-window'
import { buildMarcheHtml } from '@/lib/marche-html'
import { sortComparables, type ComparableSortKey } from '@/lib/sort-comparables'
import { filterComparablesByQuery } from '@/lib/filter-comparables'
import { formatListCount } from '@/lib/format-list-count'
import { checkComparableMinimum } from '@/lib/check-comparable-minimum'
import { computeComparableStats } from '@/lib/compute-comparable-stats'
import { detectDuplicateComparables } from '@/lib/detect-duplicate-comparables'
import { buildComparablesCsv } from '@/lib/build-comparables-csv'
import { computeMarketPriceTrend } from '@/lib/compute-market-price-trend'
import { computeComparableQualityScore } from '@/lib/compute-comparable-quality-score'
import { computePricePerM2Stats } from '@/lib/compute-price-per-m2-stats'
import { computeTimeAdjustmentRate } from '@/lib/compute-time-adjustment-rate'
import { computeComparableCompleteness } from '@/lib/compute-comparable-completeness'
import { computeDataQualityReport } from '@/lib/compute-data-quality-report'
import { computeSalesPressureIndex } from '@/lib/compute-sales-pressure-index'
import { fmtNum, formatCAD, formatCADCompact } from '@/lib/format-number'
import type { Comparable, Adjustment, EnrichmentMarche, SourceCoverage } from '@/types'

interface Props {
  dossierId: string | null
  address?: string
}

function fmt(n: number | null | undefined, digits = 1): string { return fmtNum(n, digits) }

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
  const scrollRef = useRef<HTMLDivElement>(null)
  const [comparables, setComparables] = useState<Comparable[]>([])
  const [adjustments, setAdjustments] = useState<Adjustment[]>([])
  const [marche, setMarche] = useState<EnrichmentMarche | null>(null)
  const [sourceCoverage, setSourceCoverage] = useState<SourceCoverage | null>(null)
  const [sortKey, setSortKey] = useState<ComparableSortKey>('rank')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const { replies, asking, ask } = useAgentChat(dossierId, 'comps-market')
  const [error, setError] = useState(false)

  function load() {
    if (!dossierId) return
    setLoading(true)
    setError(false)
    Promise.all([
      fetchRuntimeComparables(dossierId),
      fetchRuntimeAdjustments(dossierId),
      fetchRuntimeEnrichment(dossierId),
    ]).then(([comps, adjs, enrichment]) => {
      setComparables(comps)
      setAdjustments(adjs)
      setMarche(enrichment?.marche ?? null)
      setSourceCoverage(enrichment?.source_coverage ?? null)
      setLoading(false)
    }).catch(() => { setError(true); setLoading(false) })
  }

  useEffect(() => { load() }, [dossierId]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [replies, asking])


  if (!dossierId || loading) return <PanelLoader />
  if (error) return <PanelError onRetry={load} />

  const visibleComps = sortComparables(filterComparablesByQuery(comparables, query), sortKey)
  const countLabel = formatListCount(visibleComps.length, comparables.length)
  const minimumCheck = checkComparableMinimum(comparables)
  const duplicates = detectDuplicateComparables(comparables)
  const stats = computeComparableStats(comparables)
  const trend = computeMarketPriceTrend(comparables)
  const qualityScores = computeComparableQualityScore(comparables, adjustments)
  const qualityMap = new Map(qualityScores.map(q => [q.comparableId, q.label]))
  const m2Stats = computePricePerM2Stats(comparables)
  const timeRate = computeTimeAdjustmentRate(comparables)
  const completeness = computeComparableCompleteness(comparables)
  const completenessMap = new Map(completeness.map(c => [c.comparableId, c]))
  const avgCompletenessPct = completeness.length > 0
    ? Math.round(completeness.reduce((s, c) => s + c.completenessPct, 0) / completeness.length)
    : null
  const dataQuality = comparables.length > 0 ? computeDataQualityReport(comparables, adjustments) : null
  const pressureIndex = marche ? computeSalesPressureIndex(marche) : null

  return (
    <div className="flex flex-col flex-1 h-full overflow-hidden">
      <div ref={scrollRef} className="w-full max-w-[960px] mx-auto px-6 flex flex-col gap-0 flex-1 overflow-y-auto pt-5 pb-2 scroll-fade">
        <UserMessage>Comparer les ventes retenues et expliquer leur pertinence.</UserMessage>
        <AgentMessage agentName="Agent Marché">
          {'J\u2019ai charg\u00e9 '}<strong>{comparables.length} comparable{comparables.length !== 1 ? 's' : ''}</strong>{' depuis les art\u00e9facts du backend.'}
          {comparables.length === 0 && sourceCoverage && (
            <div className="mt-3">
              <SourceDiagnosticPanel coverage={sourceCoverage} />
            </div>
          )}
          {comparables.length === 0 && !sourceCoverage && (
            <p className="mt-2 text-[13px] text-[#8a8780]">
              Aucune source de comparables disponible. Importez un export CSV JLR au checkpoint 2.
            </p>
          )}
          {marche && <MarcheContexte m={marche} />}
          {stats && comparables.length > 1 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              <span className="text-[10px] text-[#b5b2ac] bg-black/[.04] rounded-full px-2.5 py-1 whitespace-nowrap">
                {formatCADCompact(stats.priceMin)} – {formatCADCompact(stats.priceMax)}
              </span>
              <span className="text-[10px] text-[#b5b2ac] bg-black/[.04] rounded-full px-2.5 py-1 whitespace-nowrap">
                {stats.dateMin.slice(0, 4)}{stats.dateMin.slice(0, 4) !== stats.dateMax.slice(0, 4) ? ` – ${stats.dateMax.slice(0, 4)}` : ''}
              </span>
              {m2Stats && (
                <span className="text-[10px] text-[#b5b2ac] bg-black/[.04] rounded-full px-2.5 py-1 whitespace-nowrap">
                  {fmtNum(m2Stats.median, 0)} $/m² <span className="text-[9px]">méd.</span>
                </span>
              )}
              {m2Stats && (
                <span className="text-[10px] text-[#b5b2ac] bg-black/[.04] rounded-full px-2.5 py-1 whitespace-nowrap">
                  {fmtNum(m2Stats.min, 0)} – {fmtNum(m2Stats.max, 0)} $/m²
                </span>
              )}
              {trend && (
                <span className={`text-[10px] rounded-full px-2.5 py-1 whitespace-nowrap ${
                  trend.direction === 'hausse' ? 'text-emerald-600 bg-emerald-50/80 dark:bg-emerald-900/20'
                  : trend.direction === 'baisse' ? 'text-red-500 bg-red-50/80 dark:bg-red-900/20'
                  : 'text-[#b5b2ac] bg-black/[.04]'
                }`}>
                  {trend.direction === 'hausse' ? '↑' : trend.direction === 'baisse' ? '↓' : '→'}{' '}
                  {trend.annualizedPct > 0 ? '+' : ''}{fmtNum(trend.annualizedPct, 1)} %/an
                </span>
              )}
              {timeRate && (
                <span className="text-[10px] text-[#b5b2ac] bg-black/[.04] rounded-full px-2.5 py-1 whitespace-nowrap" title={`Taux implicite — confiance ${timeRate.confidence}`}>
                  {timeRate.annualRatePct > 0 ? '+' : ''}{fmtNum(timeRate.annualRatePct, 1)} %/an <span className="text-[9px]">impl.</span>
                </span>
              )}
              {pressureIndex && (
                <span className={`text-[10px] rounded-full px-2.5 py-1 whitespace-nowrap ${
                  pressureIndex.regime === 'vendeur' ? 'text-amber-700 bg-amber-50/80 dark:bg-amber-900/20'
                  : pressureIndex.regime === 'acheteur' ? 'text-sky-600 bg-sky-50/80 dark:bg-sky-900/20'
                  : 'text-[#b5b2ac] bg-black/[.04]'
                }`} title={pressureIndex.label}>
                  {pressureIndex.regime} · {pressureIndex.index}
                </span>
              )}
            </div>
          )}
          {comparables.length > 0 && (
            <div className="mt-2.5 mb-1 flex flex-col gap-2">
              <div className="relative">
                <input
                  type="text"
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  placeholder="Filtrer par adresse…"
                  className="w-full rounded-full bg-black/[.04] border border-black/[.07] px-3.5 py-1.5 text-[12px] text-[#1a1916] placeholder:text-[#b5b2ac] focus:outline-none focus:ring-1 focus:ring-black/[.15]"
                />
                {query && (
                  <button
                    type="button"
                    onClick={() => setQuery('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[#b5b2ac] hover:text-[#1a1916] text-[13px] leading-none"
                    aria-label="Effacer"
                  >×</button>
                )}
              </div>
              {comparables.length > 1 && (
                <div className="flex flex-wrap gap-1.5">
                  {([
                    { key: 'rank',    label: 'Rang' },
                    { key: 'prix',    label: 'Prix ↑' },
                    { key: 'prix_m2', label: '$/m² ↑' },
                    { key: 'date',    label: 'Récent' },
                    { key: 'surface', label: 'Surface ↓' },
                  ] as { key: ComparableSortKey; label: string }[]).map(({ key, label }) => (
                    <button
                      key={key}
                      type="button"
                      onClick={() => setSortKey(key)}
                      className={`rounded-full px-2.5 py-1 text-[11px] transition-colors ${
                        sortKey === key
                          ? 'bg-[#1a1916] text-white'
                          : 'bg-black/[.06] text-[#6a6763] hover:bg-black/[.1]'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
          {countLabel && (
            <div className="text-[11px] text-[#b5b2ac] mt-1 mb-0.5">{countLabel}</div>
          )}
          <div className="flex flex-col gap-2 mt-1">
            {visibleComps.length > 0
              ? visibleComps.map(c => {
                  const cp = completenessMap.get(c.id)
                  return (
                    <ComparableItem
                      key={c.id}
                      comp={c}
                      qualityLabel={qualityMap.get(c.id)}
                      completenessGrade={cp?.grade}
                      missingFields={cp?.missingFields}
                    />
                  )
                })
              : query
                ? <div className="text-[12px] text-[#b5b2ac] py-2">Aucun comparable ne correspond à «&nbsp;{query}&nbsp;».</div>
                : <div className="rounded-[10px] px-4 py-5 text-center" style={{ background: 'var(--input-bg)', border: '1px dashed var(--input-border)' }}>
                    <div className="text-[13px] text-[#8a8780] mb-1">Aucun comparable disponible</div>
                    <div className="text-[12px] text-[#b5b2ac]">Le pipeline n&apos;a pas encore trouvé de ventes comparables.<br />Lancez l&apos;analyse depuis l&apos;onglet Dossier.</div>
                  </div>
            }
          </div>
        </AgentMessage>
        {minimumCheck.warning && (
          <AgentMessage agentName="Agent Marché">
            <div className="rounded-[8px] bg-amber-50/80 border border-amber-200/60 px-3 py-2 text-[11px] text-amber-800">
              {minimumCheck.warning}
            </div>
          </AgentMessage>
        )}
        {duplicates.length > 0 && (
          <AgentMessage agentName="Agent Marché">
            <div className="rounded-[8px] bg-amber-50/80 border border-amber-200/60 px-3 py-2 text-[11px] text-amber-800">
              {`${duplicates.length} doublon${duplicates.length > 1 ? 's' : ''} potentiel${duplicates.length > 1 ? 's' : ''} détecté${duplicates.length > 1 ? 's' : ''} — vérifier les sources avant validation.`}
            </div>
          </AgentMessage>
        )}
        {dataQuality && dataQuality.grade !== 'bon' && (
          <AgentMessage agentName="Agent Marché">
            <div className={`rounded-[10px] px-3 py-2.5 ${dataQuality.grade === 'faible' ? 'bg-red-50/70 dark:bg-red-900/15 border border-red-200/50' : 'bg-amber-50/80 dark:bg-amber-900/20 border border-amber-200/50'}`}>
              <div className={`text-[11px] font-semibold mb-1 ${dataQuality.grade === 'faible' ? 'text-red-700 dark:text-red-400' : 'text-amber-700 dark:text-amber-400'}`}>
                Qualité des données — {dataQuality.grade}
              </div>
              <div className="flex flex-col gap-0.5">
                {dataQuality.issues.map(issue => (
                  <div key={issue} className={`text-[11px] ${dataQuality.grade === 'faible' ? 'text-red-700 dark:text-red-400' : 'text-amber-800 dark:text-amber-300'}`}>
                    · {issue}
                  </div>
                ))}
              </div>
            </div>
          </AgentMessage>
        )}
        {comparables.length > 0 && (
          <AgentMessage agentName="Agent Marché" last={replies.length === 0 && !asking}>
            {'Les comparables sont retenus par score, source et r\u00e9cence. Les sources restent \u00e0 valider avant signature.'}
          </AgentMessage>
        )}
        {replies.map((r, i) => (
          <Fragment key={i}>
            {r.userMessage && <UserMessage>{r.userMessage}</UserMessage>}
            <AgentMessage agentName={r.agentLabel || 'Agent Marché'} last={i === replies.length - 1 && !asking}>
              <pre className="whitespace-pre-wrap font-sans text-[13px] leading-6">
                {r.text}
                {r.streaming && <span className="text-[#b5b2ac] animate-pulse">▊</span>}
              </pre>
            </AgentMessage>
          </Fragment>
        ))}
        {asking && replies.length === 0 && (
          <AgentMessage agentName="Agent Marché" last>
            <span className="text-[#b5b2ac] text-[13px] animate-pulse">···</span>
          </AgentMessage>
        )}
      </div>
      {comparables.length > 0 && (
        <div className="w-full max-w-[640px] flex justify-end gap-2 mb-3">
          <button
            type="button"
            onClick={() => {
              const csv = buildComparablesCsv(visibleComps)
              const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = `comparables${address ? '-' + address.slice(0, 30).replace(/\s+/g, '-') : ''}.csv`
              a.click()
              URL.revokeObjectURL(url)
            }}
            className="btn ghost btn-sm"
          >
            Export CSV
          </button>
          <button
            type="button"
            onClick={() => printWindow(buildMarcheHtml(visibleComps, marche, address, adjustments), address ?? 'Marché')}
            className="btn ghost btn-sm"
          >
            Imprimer le rapport marché
          </button>
        </div>
      )}
      <div className="w-full max-w-[960px] mx-auto px-6 flex-shrink-0 pb-6 pt-2">
        <ChatInput placeholder="Questionner l'Agent Marché..." onSend={ask} disabled={asking} />
      </div>
    </div>
  )
}
