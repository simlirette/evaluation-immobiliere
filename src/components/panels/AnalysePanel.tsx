'use client'

import { Fragment, useEffect, useRef, useState } from 'react'
import AgentMessage from '@/components/shared/AgentMessage'
import UserMessage from '@/components/shared/UserMessage'
import AdjustmentsTable from '@/components/shared/AdjustmentsTable'
import ValeurCard from '@/components/shared/ValeurCard'
import ChatInput from '@/components/shared/ChatInput'
import PanelLoader from '@/components/shared/PanelLoader'
import PanelError from '@/components/shared/PanelError'
import { fetchAppState, fetchRuntimeEnrichment, fetchRuntimeComparables, fetchRuntimeAdjustments, saveRuntimeAdjustments, saveRuntimeComparables } from '@/lib/runtime-api'
import { useAgentChat } from '@/hooks/useAgentChat'
import { printWindow } from '@/lib/print-window'
import { buildAnalyseHtml } from '@/lib/analyse-html'
import { summarizeAdjustments } from '@/lib/summarize-adjustments'
import { buildOEAQChecklist } from '@/lib/build-oeaq-checklist'
import { computeSubjectContext } from '@/lib/compute-subject-context'
import { buildAdjustmentsCsv } from '@/lib/build-adjustments-csv'
import { computeAdjustmentProfile } from '@/lib/compute-adjustment-profile'
import { computeAdjustmentConsistency } from '@/lib/compute-adjustment-consistency'
import { computeTimeAdjustmentRate } from '@/lib/compute-time-adjustment-rate'
import { computeAdjustedPriceStats } from '@/lib/compute-adjusted-price-stats'
import { computeSensitivityAnalysis } from '@/lib/compute-sensitivity-analysis'
import { computeComparableRanking } from '@/lib/compute-comparable-ranking'
import { computeValuationConclusion } from '@/lib/compute-valuation-conclusion'
import { computeMarketPositioning } from '@/lib/compute-market-positioning'
import { computeAppraisalRiskScore } from '@/lib/compute-appraisal-risk-score'
import { computeAdjustmentBracketAnalysis } from '@/lib/compute-adjustment-bracket-analysis'
import { computeGrossAdjustmentCeiling } from '@/lib/compute-gross-adjustment-ceiling'
import { computeAdjustmentSymmetry } from '@/lib/compute-adjustment-symmetry'
import { computeAdjustmentDirectionBalance } from '@/lib/compute-adjustment-direction-balance'
import { formatCAD, fmtNum, formatPct } from '@/lib/format-number'
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
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [draftAdj, setDraftAdj] = useState<Adjustment[]>([])
  const [adjSaving, setAdjSaving] = useState(false)
  const [editComps, setEditComps] = useState(false)
  const [draftComps, setDraftComps] = useState<Comparable[]>([])
  const [compsSaving, setCompsSaving] = useState(false)
  const { replies, asking, ask } = useAgentChat(dossierId, 'valuation-draft')

  function load() {
    if (!dossierId) return
    setLoading(true)
    setError(false)
    Promise.all([
      fetchRuntimeAdjustments(dossierId),
      fetchRuntimeComparables(dossierId),
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

  function enterEditMode() {
    setDraftAdj(adjustments.map(a => ({ ...a })))
    setEditMode(true)
  }

  function updateDraft(id: string, field: 'surface_adj' | 'year_adj' | 'condition_adj' | 'garage_adj', value: number) {
    setDraftAdj(prev => prev.map(row => {
      if (row.id !== id) return row
      const updated = { ...row, [field]: value }
      updated.adjusted = updated.salePrice + updated.surface_adj + updated.year_adj + updated.condition_adj + updated.garage_adj
      return updated
    }))
  }

  async function handleSaveAdjustments() {
    if (!dossierId) return
    setAdjSaving(true)
    try {
      await saveRuntimeAdjustments(dossierId, draftAdj)
      setAdjustments(draftAdj)
      setEditMode(false)
    } finally {
      setAdjSaving(false)
    }
  }

  function enterEditComps() {
    setDraftComps(comparables.map(c => ({ ...c })))
    setEditComps(true)
  }

  function updateDraftComp(id: string, field: keyof Comparable, value: string | number | null) {
    setDraftComps(prev => prev.map(c => c.id !== id ? c : { ...c, [field]: value }))
  }

  function addDraftComp() {
    const id = Math.random().toString(36).slice(2, 10)
    setDraftComps(prev => [...prev, {
      id, rank: '', address: '', hab_m2: null, terrain_m2: null,
      year_built: null, renovated_year: null, garage_type: null,
      sale_price: 0, sale_date: '', meta: '', price: '', date: '', score: null, source_id: '',
    }])
  }

  function removeDraftComp(id: string) {
    setDraftComps(prev => prev.filter(c => c.id !== id))
  }

  async function handleSaveComparables() {
    if (!dossierId) return
    setCompsSaving(true)
    try {
      await saveRuntimeComparables(dossierId, draftComps)
      setComparables(draftComps)
      setEditComps(false)
    } finally {
      setCompsSaving(false)
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

          {/* ── Comparables section ── */}
          {editComps ? (
            <div className="mt-2.5 flex flex-col gap-2">
              {draftComps.map((comp, idx) => (
                <div key={comp.id} className="rounded-[10px] overflow-hidden border border-black/[.08] bg-black/[.015]">
                  <div className="flex items-center justify-between px-3 py-2 border-b border-black/[.06]">
                    <span className="text-[11px] font-medium text-[#1a1916]">Comparable {idx + 1}</span>
                    <button type="button" onClick={() => removeDraftComp(comp.id)} className="text-[10px] text-red-400 hover:text-red-600 transition-colors">Supprimer</button>
                  </div>
                  <div className="px-3 pb-3 pt-2 grid grid-cols-2 gap-x-3 gap-y-2">
                    <div className="col-span-2 flex flex-col gap-1">
                      <label className="text-[10px] text-[#8a8780] font-medium">Adresse / Libellé</label>
                      <input type="text" value={comp.address} onChange={e => updateDraftComp(comp.id, 'address', e.target.value)}
                        className="w-full rounded-[6px] border border-black/[.12] bg-white px-2 py-1 text-[12px] text-[#1a1916] focus:outline-none focus:ring-1 focus:ring-[#334155]/40"
                        placeholder="ex. 456 rue des Érables" />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] text-[#8a8780] font-medium">Prix de vente ($)</label>
                      <input type="number" min="0" value={comp.sale_price || ''} onChange={e => updateDraftComp(comp.id, 'sale_price', parseFloat(e.target.value) || 0)}
                        className="w-full rounded-[6px] border border-black/[.12] bg-white px-2 py-1 text-[12px] text-[#1a1916] focus:outline-none focus:ring-1 focus:ring-[#334155]/40"
                        placeholder="450000" />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] text-[#8a8780] font-medium">Date de vente</label>
                      <input type="date" value={comp.sale_date} onChange={e => updateDraftComp(comp.id, 'sale_date', e.target.value)}
                        className="w-full rounded-[6px] border border-black/[.12] bg-white px-2 py-1 text-[12px] text-[#1a1916] focus:outline-none focus:ring-1 focus:ring-[#334155]/40" />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] text-[#8a8780] font-medium">Superficie hab. (pi²)</label>
                      <input type="number" min="0" value={comp.hab_m2 ?? ''} onChange={e => updateDraftComp(comp.id, 'hab_m2', e.target.value ? parseFloat(e.target.value) : null)}
                        className="w-full rounded-[6px] border border-black/[.12] bg-white px-2 py-1 text-[12px] text-[#1a1916] focus:outline-none focus:ring-1 focus:ring-[#334155]/40"
                        placeholder="1450" />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] text-[#8a8780] font-medium">Année construction</label>
                      <input type="number" min="1800" max="2099" value={comp.year_built ?? ''} onChange={e => updateDraftComp(comp.id, 'year_built', e.target.value ? parseInt(e.target.value) : null)}
                        className="w-full rounded-[6px] border border-black/[.12] bg-white px-2 py-1 text-[12px] text-[#1a1916] focus:outline-none focus:ring-1 focus:ring-[#334155]/40"
                        placeholder="1998" />
                    </div>
                    <div className="col-span-2 flex flex-col gap-1">
                      <label className="text-[10px] text-[#8a8780] font-medium">Source ID (traçabilité OEAQ)</label>
                      <input type="text" value={comp.source_id ?? ''} onChange={e => updateDraftComp(comp.id, 'source_id', e.target.value)}
                        className="w-full rounded-[6px] border border-black/[.12] bg-white px-2 py-1 text-[12px] text-[#1a1916] focus:outline-none focus:ring-1 focus:ring-[#334155]/40"
                        placeholder="CENTRIS-12345678" />
                    </div>
                  </div>
                </div>
              ))}
              <button type="button" onClick={addDraftComp}
                className="rounded-[10px] py-2 text-[12px] font-medium text-[#334155] border border-dashed border-black/[.15] bg-transparent hover:bg-black/[.03] transition-colors">
                + Ajouter un comparable
              </button>
              <div className="flex items-center gap-2 mt-1">
                <button type="button" onClick={handleSaveComparables} disabled={compsSaving}
                  className="rounded-full px-3.5 py-1.5 text-[12px] bg-[#334155] text-white disabled:opacity-40 transition-opacity">
                  {compsSaving ? 'Sauvegarde\u2026' : 'Sauvegarder les comparables'}
                </button>
                <button type="button" onClick={() => setEditComps(false)}
                  className="rounded-full px-3.5 py-1.5 text-[12px] bg-black/[.05] text-[#5a5854] hover:bg-black/[.09] transition-colors">
                  Annuler
                </button>
              </div>
            </div>
          ) : comparables.length > 0 ? (
            <div className="mt-2.5">
              <div className="flex flex-col divide-y divide-[rgba(0,0,0,.04)] rounded-xl overflow-hidden border border-black/[.06]">
                {comparables.map(c => (
                  <div key={c.id} className="flex items-center justify-between px-3 py-2 text-[12px]">
                    <span className="text-[11px] text-[#1a1916] truncate flex-1 min-w-0">{c.address}</span>
                    <span className="text-[11px] text-[#8a8780] ml-3 flex-shrink-0">{c.price}</span>
                    <span className="text-[10px] text-[#b5b2ac] ml-2 flex-shrink-0">{c.date}</span>
                  </div>
                ))}
              </div>
              <button type="button" onClick={enterEditComps}
                className="mt-2 rounded-full px-3 py-1.5 text-[11px] bg-black/[.05] text-[#5a5854] hover:bg-black/[.09] transition-colors">
                ✏ Modifier les comparables
              </button>
            </div>
          ) : (
            <div className="mt-2.5 rounded-[10px] px-4 py-4 text-center" style={{ background: 'var(--input-bg)', border: '1px dashed var(--input-border)' }}>
              <div className="text-[12px] text-[#b5b2ac]">Aucun comparable — lancez l&apos;analyse depuis l&apos;onglet Dossier.</div>
            </div>
          )}

          {editMode ? (
            <div className="mt-2.5">
              <div className="overflow-x-auto rounded-xl border border-black/[.08]">
                <table className="w-full border-collapse text-xs">
                  <thead>
                    <tr>
                      {['Comparable', 'Surface', 'Temps', 'Condition', 'Garage', 'Prix ajusté'].map(h => (
                        <th key={h} className={`px-2.5 py-[7px] text-[10px] font-medium text-[#b5b2ac] uppercase tracking-[.06em] border-b border-black/[.07] bg-black/[.02] ${h === 'Comparable' ? 'text-left' : 'text-right'}`}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {draftAdj.map(row => (
                      <tr key={row.id}>
                        <td className="px-2.5 py-2 border-b border-black/[.04] text-[11px] text-[#6a6763] max-w-[160px] truncate">{row.comparableLabel}</td>
                        {(['surface_adj', 'year_adj', 'condition_adj', 'garage_adj'] as const).map(field => (
                          <td key={field} className="px-1.5 py-1.5 border-b border-black/[.04]">
                            <input
                              type="number"
                              value={row[field]}
                              onChange={e => updateDraft(row.id, field, Number(e.target.value))}
                              step={100}
                              className="w-24 text-right rounded-[6px] border border-black/[.12] bg-white px-2 py-1 text-[12px] text-[#1a1916] focus:outline-none focus:ring-1 focus:ring-[#334155]/40"
                            />
                          </td>
                        ))}
                        <td className="px-2.5 py-2 border-b border-black/[.04] text-right font-semibold text-[12px] text-[#1a1916] whitespace-nowrap">
                          {formatPrice(row.adjusted)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex items-center gap-2 mt-2.5">
                <button
                  type="button"
                  onClick={handleSaveAdjustments}
                  disabled={adjSaving}
                  className="rounded-full px-3.5 py-1.5 text-[12px] bg-[#334155] text-white disabled:opacity-40 transition-opacity"
                >
                  {adjSaving ? 'Sauvegarde…' : 'Sauvegarder les ajustements'}
                </button>
                <button
                  type="button"
                  onClick={() => setEditMode(false)}
                  className="rounded-full px-3.5 py-1.5 text-[12px] bg-black/[.05] text-[#5a5854] hover:bg-black/[.09] transition-colors"
                >
                  Annuler
                </button>
              </div>
            </div>
          ) : (
            <>
              {adjustments.length > 0 ? (
                <>
                  <AdjustmentsTable rows={adjustments} comparables={comparables} />
                  <button
                    type="button"
                    onClick={enterEditMode}
                    className="mt-2 rounded-full px-3 py-1.5 text-[11px] bg-black/[.05] text-[#5a5854] hover:bg-black/[.09] transition-colors"
                  >
                    ✏ Modifier les ajustements
                  </button>
                </>
              ) : (
                <div className="mt-2 rounded-[10px] px-4 py-4 text-center" style={{ background: 'var(--input-bg)', border: '1px dashed var(--input-border)' }}>
                  <div className="text-[12px] text-[#b5b2ac]">Aucun ajustement — le pipeline n&apos;a pas encore calculé les ajustements comparatifs.</div>
                </div>
              )}
            </>
          )}
          {adjustments.length > 0 && (() => {
            const ceiling = computeGrossAdjustmentCeiling(adjustments)
            if (!ceiling || ceiling.compliant) return null
            return (
              <div className="mt-2 mb-1 flex flex-col gap-1 rounded-xl px-3 py-2 bg-red-50/80 dark:bg-red-900/20 border border-red-200/50">
                <div className="flex items-center gap-1.5">
                  <span className="text-red-600 dark:text-red-400 text-[11px] font-semibold">⚠ Plafonds OEAQ dépassés</span>
                  <span className="text-[10px] text-red-500/70">{ceiling.violationCount} comparable{ceiling.violationCount > 1 ? 's' : ''} · ligne &gt; 15 % ou total &gt; 25 %</span>
                </div>
                {ceiling.entries.filter(e => e.hasViolation).map(e => (
                  <div key={e.comparableId} className="flex items-center gap-1.5 text-[10px] text-red-700 dark:text-red-300">
                    <span className="font-medium truncate">{e.comparableLabel}</span>
                    {e.exceedsLineCeiling && <span className="rounded px-1 bg-red-100 dark:bg-red-900/40">ligne {fmtNum(e.maxLinePct, 1)} %</span>}
                    {e.exceedsTotalCeiling && <span className="rounded px-1 bg-red-100 dark:bg-red-900/40">total {fmtNum(e.totalGrossPct, 1)} %</span>}
                  </div>
                ))}
              </div>
            )
          })()}
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
                {conclusion !== null && adjustments.length > 0 && (() => {
                  const pos = computeMarketPositioning(conclusion, adjustments)
                  if (!pos) return null
                  const posColor = pos.position === 'bas' ? 'text-sky-600 dark:text-sky-400'
                    : pos.position === 'haut' ? 'text-amber-600 dark:text-amber-400'
                    : 'text-[#6a6763]'
                  return (
                    <div className="mt-1 text-[11px] px-1 text-[#8a8780]">
                      Positionnement&nbsp;:
                      <span className={`ml-1 font-medium ${posColor}`}>{pos.position}</span>
                      <span className="ml-1">({pos.countBelow} comp. en-dessous, {pos.countAbove} au-dessus)</span>
                      {pos.nearestBelow && (
                        <span className="ml-1 text-[10px]">· -{new Intl.NumberFormat('fr-CA', { maximumFractionDigits: 0 }).format(pos.nearestBelow.delta)} $ vs {pos.nearestBelow.label}</span>
                      )}
                    </div>
                  )
                })()}
                {conclusion !== null && adjustments.length > 0 && (() => {
                  const bracket = computeAdjustmentBracketAnalysis(adjustments, conclusion)
                  if (!bracket) return null
                  return (
                    <div className="mt-1 text-[11px] px-1 text-[#8a8780]">
                      Encadrement&nbsp;:
                      {bracket.isBracketed
                        ? <span className="ml-1 text-emerald-600 dark:text-emerald-400 font-medium">encadré ✓</span>
                        : <span className="ml-1 text-amber-600 dark:text-amber-400 font-medium">⚠ non encadré</span>
                      }
                      {!bracket.isBracketed && !bracket.hasBelow && <span className="ml-1 text-[10px]">(aucun comparable en-dessous)</span>}
                      {!bracket.isBracketed && !bracket.hasAbove && <span className="ml-1 text-[10px]">(aucun comparable au-dessus)</span>}
                    </div>
                  )
                })()}
                {ctx && (
                  <div className={`mt-1.5 text-[11px] px-1 ${ctx.withinRange ? 'text-[#6a6763]' : 'text-amber-700 dark:text-amber-400'}`}>
                    {ctx.withinRange
                      ? `Conclusion dans la fourchette des valeurs indiquées${Math.abs(ctx.deviationFromMedianPct) >= 1 ? ` · ${ctx.deviationFromMedianPct > 0 ? '+' : ''}${ctx.deviationFromMedianPct} % vs médiane` : ' · en ligne avec la médiane'}.`
                      : `⚠ Conclusion hors de la fourchette des valeurs indiquées (${ctx.deviationFromMedianPct > 0 ? '+' : ''}${ctx.deviationFromMedianPct} % vs médiane) — justification requise.`
                    }
                  </div>
                )}
                {(() => {
                  const stats = computeAdjustedPriceStats(adjustments)
                  if (!stats) return null
                  const cohesionColor = stats.cohesion === 'excellent' ? 'text-emerald-600 dark:text-emerald-400'
                    : stats.cohesion === 'bon' ? 'text-sky-600 dark:text-sky-400'
                    : stats.cohesion === 'acceptable' ? 'text-amber-600 dark:text-amber-400'
                    : 'text-red-500'
                  return (
                    <div className="mt-1 text-[11px] px-1 text-[#8a8780]">
                      Dispersion des valeurs indiquées&nbsp;: CV&nbsp;
                      <span className={`font-medium ${cohesionColor}`}>{fmtNum(stats.cv, 1)} %</span>
                      <span className="ml-1">— cohésion <span className={`font-medium ${cohesionColor}`}>{stats.cohesion}</span></span>
                    </div>
                  )
                })()}
              </>
            )
          })()}
          {adjustments.length > 0 && comparables.length > 0 && (() => {
            const ranking = computeComparableRanking(comparables, adjustments)
            if (ranking.length === 0) return null
            return (
              <div className="mt-3 mb-1">
                <div className="text-[11px] uppercase tracking-widest text-[#8a8780] mb-2">Classement des comparables</div>
                <div className="flex flex-col divide-y divide-[rgba(0,0,0,.04)] rounded-xl overflow-hidden bg-[rgba(0,0,0,.025)]">
                  {ranking.map(r => (
                    <div key={r.comparableId} className="flex items-center gap-2 px-3 py-1.5">
                      <span className={`text-[10px] font-semibold w-4 flex-shrink-0 ${r.rank === 1 ? 'text-emerald-600 dark:text-emerald-400' : 'text-[#b5b2ac]'}`}>#{r.rank}</span>
                      <span className="text-[11px] text-[#4a4845] dark:text-[#c5c2bc] flex-1 min-w-0 truncate">{r.comparableLabel}</span>
                      <span className="text-[10px] text-[#8a8780] flex-shrink-0">qualité {fmtNum(r.qualityScore, 1)}/10</span>
                      <span className={`text-[10px] flex-shrink-0 ${r.isOutlier ? 'text-amber-600' : 'text-[#b5b2ac]'}`}>
                        {r.isOutlier ? '⚠ atypique' : `poids ${r.weightPct} %`}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
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
          {comparables.length >= 2 && (() => {
            const timeRate = computeTimeAdjustmentRate(comparables)
            if (!timeRate) return null
            return (
              <div className="mt-1.5 text-[11px] px-1 text-[#8a8780]">
                Taux temporel implicite (comparables)&nbsp;:
                <span className={`ml-1 font-medium ${timeRate.annualRatePct > 0 ? 'text-emerald-600 dark:text-emerald-400' : timeRate.annualRatePct < 0 ? 'text-red-500' : 'text-[#8a8780]'}`}>
                  {timeRate.annualRatePct > 0 ? '+' : ''}{fmtNum(timeRate.annualRatePct, 1)} %/an
                </span>
                <span className="ml-1 text-[10px] text-[#b5b2ac]">— confiance {timeRate.confidence}</span>
              </div>
            )
          })()}
          {adjustments.length >= 2 && (() => {
            const checks = computeAdjustmentConsistency(adjustments)
            const warnings = checks.filter(c => !c.consistent)
            if (warnings.length === 0) return null
            return (
              <div className="mt-2 mb-1">
                <div className="flex flex-col gap-1.5 rounded-xl px-3 py-2 bg-amber-50/70 dark:bg-amber-900/20 border border-amber-200/50">
                  {warnings.map(w => (
                    <div key={w.type} className="flex items-start gap-2">
                      <span className="text-amber-600 text-[11px] font-semibold flex-shrink-0 mt-0.5">⚠</span>
                      <span className="text-[11px] text-amber-800 dark:text-amber-300">{w.warning}</span>
                    </div>
                  ))}
                </div>
              </div>
            )
          })()}
          {adjustments.length >= 3 && (() => {
            const symmetry = computeAdjustmentSymmetry(adjustments)
            if (!symmetry || symmetry.overallSymmetric) return null
            const typeNames: Record<string, string> = { surface: 'Surface', year: 'Année', condition: 'État', garage: 'Garage' }
            const asymTypes = (['surface', 'year', 'condition', 'garage'] as const)
              .filter(k => !symmetry[k].symmetric && symmetry[k].mean !== 0)
              .map(k => typeNames[k])
            if (asymTypes.length === 0) return null
            return (
              <div className="mt-2 mb-1 flex flex-col gap-1 rounded-xl px-3 py-2 bg-amber-50/70 dark:bg-amber-900/20 border border-amber-200/50">
                <div className="flex items-start gap-2">
                  <span className="text-amber-600 text-[11px] font-semibold flex-shrink-0 mt-0.5">⚠</span>
                  <span className="text-[11px] text-amber-800 dark:text-amber-300">
                    Symétrie des ajustements — variation élevée (CV &gt; 50 %) pour : {asymTypes.join(', ')} · application non homogène entre comparables.
                  </span>
                </div>
              </div>
            )
          })()}
          {adjustments.length >= 2 && (() => {
            const balance = computeAdjustmentDirectionBalance(adjustments)
            if (!balance || balance.balanced) return null
            const dirLabel = balance.direction === 'upward' ? 'positifs' : 'négatifs'
            const dirPct = balance.direction === 'upward' ? balance.upPct : balance.downPct
            return (
              <div className="mt-2 mb-1 flex flex-col gap-1 rounded-xl px-3 py-2 bg-amber-50/70 dark:bg-amber-900/20 border border-amber-200/50">
                <div className="flex items-start gap-2">
                  <span className="text-amber-600 text-[11px] font-semibold flex-shrink-0 mt-0.5">⚠</span>
                  <span className="text-[11px] text-amber-800 dark:text-amber-300">
                    Biais d&apos;ajustement - {fmtNum(dirPct, 0)} % des comparables reçoivent des ajustements nets {dirLabel} · possible biais {balance.direction === 'upward' ? 'haussier' : 'baissier'}.
                  </span>
                </div>
              </div>
            )
          })()}
          {adjustments.length >= 3 && (() => {
            const sensitivity = computeSensitivityAnalysis(adjustments)
            if (!sensitivity) return null
            return (
              <div className="mt-3 mb-1">
                <div className="text-[11px] uppercase tracking-widest text-[#8a8780] mb-2">Sensibilité de la réconciliation</div>
                <div className="flex flex-col divide-y divide-[rgba(0,0,0,.04)] rounded-xl overflow-hidden bg-[rgba(0,0,0,.025)]">
                  {sensitivity.entries.map(e => (
                    <div key={e.comparableId} className="flex items-center justify-between px-3 py-1.5 gap-3">
                      <span className="text-[11px] text-[#6a6763] dark:text-[#9a9790] flex-1 min-w-0 truncate">Sans {e.comparableLabel}</span>
                      <span className={`text-[11px] font-medium flex-shrink-0 ${e.influential ? 'text-amber-600 dark:text-amber-400' : 'text-[#8a8780]'}`}>
                        {e.deltaPct > 0 ? '+' : ''}{fmtNum(e.deltaPct, 1)} %
                        {e.influential && <span className="ml-1 text-[10px]">⚠</span>}
                      </span>
                      <span className="text-[11px] text-[#1a1916] dark:text-white font-medium flex-shrink-0">{formatPrice(e.reconciledWithout)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )
          })()}
        </AgentMessage>
        {adjustments.length > 0 && (() => {
          const vc = computeValuationConclusion(adjustments, comparables)
          if (!vc) return null
          const reliabilityColor = vc.reliability === 'élevée' ? 'text-emerald-600 dark:text-emerald-400'
            : vc.reliability === 'modérée' ? 'text-amber-600 dark:text-amber-400'
            : 'text-red-500'
          return (
            <AgentMessage agentName="Agent Analyse">
              <div className="rounded-xl bg-[rgba(0,0,0,.03)] dark:bg-[rgba(255,255,255,.04)] px-4 py-3 flex flex-col gap-2">
                <div className="text-[11px] uppercase tracking-widest text-[#8a8780]">Conclusion structurée</div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-[12px]">
                  <span className="text-[#6a6763]">Valeur réconciliée</span>
                  <span className="font-semibold text-right">{formatPrice(vc.reconciledValue)}</span>
                  <span className="text-[#6a6763]">Intervalle ±1σ</span>
                  <span className="font-medium text-right text-[11px] text-[#4a4845] dark:text-[#c5c2bc]">{formatPrice(vc.confidenceRange.low)} – {formatPrice(vc.confidenceRange.high)}</span>
                  <span className="text-[#6a6763]">Dispersion (CV)</span>
                  <span className="font-medium text-right">{fmtNum(vc.cv, 1)} %</span>
                  <span className="text-[#6a6763]">Fiabilité globale</span>
                  <span className={`font-semibold text-right ${reliabilityColor}`}>{vc.reliability}</span>
                  {vc.oeaqWarnings > 0 && (
                    <>
                      <span className="text-[#6a6763]">Alertes OEAQ</span>
                      <span className="font-medium text-right text-amber-600 dark:text-amber-400">{vc.oeaqWarnings} avertissement{vc.oeaqWarnings > 1 ? 's' : ''}</span>
                    </>
                  )}
                  {vc.hasTimeAdjustment && vc.annualTimeRatePct !== null && (
                    <>
                      <span className="text-[#6a6763]">Taux temporel</span>
                      <span className={`font-medium text-right ${vc.annualTimeRatePct >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-500'}`}>
                        {vc.annualTimeRatePct >= 0 ? '+' : ''}{fmtNum(vc.annualTimeRatePct, 1)} %/an
                      </span>
                    </>
                  )}
                </div>
              </div>
            </AgentMessage>
          )
        })()}
        {adjustments.length > 0 && (() => {
          const risk = computeAppraisalRiskScore(adjustments, comparables)
          if (!risk) return null
          const riskColor = risk.riskLevel === 'faible' ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-50/80 dark:bg-emerald-900/20'
            : risk.riskLevel === 'modéré' ? 'text-amber-600 dark:text-amber-400 bg-amber-50/80 dark:bg-amber-900/20'
            : 'text-red-600 dark:text-red-400 bg-red-50/80 dark:bg-red-900/20'
          return (
            <AgentMessage agentName="Agent Analyse">
              <div className="flex items-start gap-2 flex-wrap">
                <span className={`text-[10px] font-semibold rounded-full px-2.5 py-1 whitespace-nowrap ${riskColor}`}>
                  Risque dossier&nbsp;: {risk.riskLevel} ({risk.score}/100)
                </span>
                {risk.factors.length > 0 && (
                  <span className="text-[10px] text-[#8a8780]">{risk.factors.join(' · ')}</span>
                )}
              </div>
            </AgentMessage>
          )
        })()}
        <AgentMessage agentName="Agent Analyse" last={replies.length === 0 && !asking}>
          {'Statut\u00a0: '}<strong>{statusLabel(status)}</strong>{'. La validation d\u2019un \u00e9valuateur agr\u00e9\u00e9 reste obligatoire avant toute diffusion.'}
        </AgentMessage>
        {replies.map((r, i) => (
          <Fragment key={i}>
            {r.userMessage && <UserMessage>{r.userMessage}</UserMessage>}
            <AgentMessage agentName={r.agentLabel || 'Agent Analyse'} last={i === replies.length - 1 && !asking}>
              <pre className="whitespace-pre-wrap font-sans text-[13px] leading-6">
                {r.text}
                {r.streaming && <span className="text-[#b5b2ac] animate-pulse">▊</span>}
              </pre>
            </AgentMessage>
          </Fragment>
        ))}
        {asking && replies.length === 0 && (
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
      <ChatInput placeholder="Questionner l'Agent Analyse..." onSend={ask} disabled={asking} />
    </div>
  )
}
