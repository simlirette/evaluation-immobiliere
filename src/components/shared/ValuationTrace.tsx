'use client'

import { useEffect, useState } from 'react'
import { fetchValuationTrace } from '@/lib/runtime-api'
import type { ValuationTrace as TraceData, ValuationApproachTrace } from '@/lib/runtime-api'
import { formatCAD } from '@/lib/format-number'

interface Props {
  sessionId: string
}

function fmtMoney(n: number | null | undefined) {
  return n != null ? formatCAD(n) : '—'
}

function ApproachCard({ a }: { a: ValuationApproachTrace }) {
  const [open, setOpen] = useState(false)
  const hasValue = a.value != null

  return (
    <div className="rounded-[10px] border border-black/[.07] overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-3 text-left bg-black/[.02] hover:bg-black/[.04] transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-[12px] font-medium text-[#1a1916]">{a.label}</span>
          <span className="text-[11px] text-[#8a8780]">{a.method}</span>
        </div>
        <div className="flex items-center gap-3">
          {hasValue && (
            <span className="text-[13px] font-semibold text-[#1a1916]">{fmtMoney(a.value)}</span>
          )}
          {!hasValue && (
            <span className="text-[11px] text-[#b5b2ac]">Non calculé</span>
          )}
          <span className="text-[10px] text-[#b5b2ac]">{open ? '▲' : '▼'}</span>
        </div>
      </button>

      {open && (
        <div className="px-4 pb-4 pt-3 flex flex-col gap-3 bg-white/40 dark:bg-black/10">

          {/* Value breakdown */}
          {hasValue && (
            <div className="grid grid-cols-3 gap-2">
              <div className="rounded-[8px] bg-black/[.03] px-3 py-2">
                <div className="text-[10px] uppercase tracking-wide text-[#8a8780] mb-0.5">Valeur brute</div>
                <div className="text-[12px] font-medium text-[#1a1916]">{fmtMoney(a.base_value)}</div>
              </div>
              <div className="rounded-[8px] bg-black/[.03] px-3 py-2">
                <div className="text-[10px] uppercase tracking-wide text-[#8a8780] mb-0.5">Ajustements</div>
                <div className="text-[12px] font-medium text-[#1a1916]">
                  {a.adjustment_total != null
                    ? (a.adjustment_total >= 0 ? '+' : '') + fmtMoney(a.adjustment_total)
                    : '—'}
                </div>
              </div>
              <div className="rounded-[8px] bg-black/[.03] px-3 py-2">
                <div className="text-[10px] uppercase tracking-wide text-[#8a8780] mb-0.5">Comparables retenus</div>
                <div className="text-[12px] font-medium text-[#1a1916]">{a.input_count}</div>
              </div>
            </div>
          )}

          {/* Selected comparables */}
          {a.selected_comparables.length > 0 && (
            <div>
              <div className="text-[10px] uppercase tracking-wide text-[#8a8780] mb-1.5">Comparables utilisés</div>
              <div className="flex flex-col gap-1">
                {a.selected_comparables.map((c, i) => (
                  <div key={i} className="flex items-center justify-between rounded-[7px] bg-black/[.02] px-3 py-1.5 text-[11px]">
                    <span className="text-[#4a4743] font-mono">{c.source_id || c.comparable_id || `#${i + 1}`}</span>
                    <div className="flex gap-4 text-[#8a8780]">
                      <span>{c.date_vente || '—'}</span>
                      <span className="font-medium text-[#1a1916]">{fmtMoney(c.prix_vente)}</span>
                      {c.score != null && (
                        <span>score&nbsp;{c.score.toFixed(2)}</span>
                      )}
                      {a.weights[i] != null && (
                        <span>w={a.weights[i].toFixed(3)}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Policy */}
          {a.policy.length > 0 && (
            <div>
              <div className="text-[10px] uppercase tracking-wide text-[#8a8780] mb-1.5">Politiques de calcul</div>
              <ul className="flex flex-col gap-0.5">
                {a.policy.map((p, i) => (
                  <li key={i} className="text-[11px] text-[#6a6763] leading-snug flex gap-1.5">
                    <span className="text-[#b5b2ac] flex-shrink-0">·</span>
                    {p}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function ValuationTrace({ sessionId }: Props) {
  const [open, setOpen] = useState(false)
  const [trace, setTrace] = useState<TraceData | null>(null)
  const [loading, setLoading] = useState(false)
  const [traceError, setTraceError] = useState(false)

  useEffect(() => {
    if (!open || trace || !sessionId) return
    setLoading(true)
    setTraceError(false)
    fetchValuationTrace(sessionId).then(data => {
      setTrace(data)
      setLoading(false)
    }).catch(() => { setTraceError(true); setLoading(false) })
  }, [open, sessionId, trace])

  const hasData = trace && trace.approaches.length > 0

  return (
    <div className="rounded-2xl ring-1 ring-[rgba(0,0,0,.08)] bg-[rgba(255,255,255,.45)] dark:bg-[rgba(30,28,25,.45)] overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-black/[.02] transition-colors"
      >
        <div>
          <div className="text-[13px] font-semibold text-[#1a1916] dark:text-white">Trace de calcul</div>
          <div className="text-[11px] text-[#8a8780] mt-0.5">Approches, poids, ajustements, politiques OEAQ</div>
        </div>
        <span className="text-[11px] text-[#b5b2ac]">{open ? '▲ Fermer' : '▼ Développer'}</span>
      </button>

      {open && (
        <div className="px-5 pb-5 flex flex-col gap-3 border-t border-black/[.06]">
          {loading && (
            <div className="py-4 text-center text-[12px] text-[#b5b2ac]">Chargement…</div>
          )}
          {!loading && traceError && (
            <div className="py-4 text-center text-[12px] text-red-500">
              Erreur lors du chargement de la trace.
            </div>
          )}
          {!loading && !traceError && !hasData && (
            <div className="py-4 text-center text-[12px] text-[#b5b2ac]">
              Aucune trace — le pipeline de valorisation n&apos;a pas encore été exécuté.
            </div>
          )}
          {!loading && hasData && (
            <>
              <div className="pt-3 flex flex-col gap-2">
                {trace.approaches.map(a => (
                  <ApproachCard key={a.approach} a={a} />
                ))}
              </div>

              {trace.hypotheses.length > 0 && (
                <div>
                  <div className="text-[10px] uppercase tracking-wide text-[#8a8780] mb-1.5 mt-1">Hypothèses explicites</div>
                  <ul className="flex flex-col gap-0.5">
                    {trace.hypotheses.map((h, i) => (
                      <li key={i} className="text-[12px] text-[#4a4743] dark:text-[#b8b5b0] flex gap-1.5 leading-snug">
                        <span className="text-[#b5b2ac] flex-shrink-0">·</span>
                        {h.hypothese ?? JSON.stringify(h)}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <p className="text-[10px] text-[#b5b2ac] mt-1">
                Trace déterministe générée par le moteur de calcul interne — non certifiée.
              </p>
            </>
          )}
        </div>
      )}
    </div>
  )
}
