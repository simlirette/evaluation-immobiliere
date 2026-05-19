'use client'

import { useEffect, useState } from 'react'
import PanelSkeleton from '@/components/shared/PanelSkeleton'
import EmptyState from '@/components/shared/EmptyState'
import ValuationTrace from '@/components/shared/ValuationTrace'
import { fetchRuntimeEnrichment } from '@/lib/runtime-api'
import { printWindow } from '@/lib/print-window'
import { buildSyntheseHtml } from '@/lib/synthese-html'
import { formatCAD, fmtNum, formatPct } from '@/lib/format-number'
import type { Enrichment, EnrichmentAlerte } from '@/types'

interface Props {
  dossierId: string | null
  address?: string
  onCritiqueFound?: (count: number) => void
}

function fmt(n: number | null | undefined, digits = 0): string { return fmtNum(n, digits) }
function fmtMoney(n: number | null | undefined): string {
  if (n == null) return '—'
  return formatCAD(n)
}

// ── Score global badge ────────────────────────────────────────────────────────

const GRADE_COLORS: Record<string, { bg: string; text: string; ring: string }> = {
  A: { bg: 'bg-emerald-50 dark:bg-emerald-950', text: 'text-emerald-700 dark:text-emerald-300', ring: 'ring-emerald-300 dark:ring-emerald-700' },
  B: { bg: 'bg-sky-50 dark:bg-sky-950',         text: 'text-sky-700 dark:text-sky-300',         ring: 'ring-sky-300 dark:ring-sky-700' },
  C: { bg: 'bg-amber-50 dark:bg-amber-950',     text: 'text-amber-700 dark:text-amber-300',     ring: 'ring-amber-300 dark:ring-amber-700' },
  D: { bg: 'bg-orange-50 dark:bg-orange-950',   text: 'text-orange-700 dark:text-orange-300',   ring: 'ring-orange-300 dark:ring-orange-700' },
  F: { bg: 'bg-red-50 dark:bg-red-950',         text: 'text-red-700 dark:text-red-300',         ring: 'ring-red-300 dark:ring-red-700' },
}

function ScoreGlobalCard({ sg }: { sg: NonNullable<Enrichment['score_global']> }) {
  const colors = GRADE_COLORS[sg.grade] ?? GRADE_COLORS['C']
  return (
    <div className={`rounded-2xl ring-1 ${colors.ring} ${colors.bg} p-5 flex items-center gap-5`}>
      <div className={`text-6xl font-semibold leading-none ${colors.text} w-16 text-center`}>
        {sg.grade}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[11px] uppercase tracking-widest text-[#8a8780] mb-0.5">Score global</div>
        <div className="text-2xl font-semibold text-[#1a1916] dark:text-white">
          {fmt(sg.score, 2)} <span className="text-base font-normal text-[#8a8780]">/ 10</span>
        </div>
        <div className="text-[13px] text-[#4a4743] dark:text-[#b8b5b0] mt-1 leading-snug">
          {sg.recommandation}
        </div>
      </div>
    </div>
  )
}

// ── Alertes ───────────────────────────────────────────────────────────────────

const ALERTE_STYLES: Record<string, { dot: string; badge: string; text: string }> = {
  critique: { dot: 'bg-red-500',    badge: 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300',    text: 'CRITIQUE' },
  attention: { dot: 'bg-amber-500', badge: 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300', text: 'ATTENTION' },
  info:      { dot: 'bg-sky-400',   badge: 'bg-sky-100 text-sky-700 dark:bg-sky-950 dark:text-sky-300',    text: 'INFO' },
}

function AlerteRow({ alerte }: { alerte: EnrichmentAlerte }) {
  const s = ALERTE_STYLES[alerte.niveau] ?? ALERTE_STYLES['info']
  return (
    <div className="flex items-start gap-3 py-2.5">
      <span className={`mt-1.5 w-2 h-2 rounded-full flex-shrink-0 ${s.dot}`} />
      <div className="flex-1 min-w-0">
        <span className={`inline-block text-[10px] font-semibold tracking-wider px-1.5 py-0.5 rounded mr-2 ${s.badge}`}>
          {s.text}
        </span>
        <span className="text-[12px] text-[#4a4743] dark:text-[#b8b5b0] capitalize">
          {alerte.categorie.replace(/_/g, ' ')}
        </span>
        <p className="text-[13px] text-[#1a1916] dark:text-white mt-0.5 leading-snug">
          {alerte.message}
        </p>
      </div>
    </div>
  )
}

// ── Score chip ────────────────────────────────────────────────────────────────

function ScoreChip({ label, score, sub }: { label: string; score: number | null | undefined; sub?: string }) {
  const pct = score != null ? Math.round((score / 10) * 100) : 0
  const color = pct >= 70 ? '#1f7a5c' : pct >= 50 ? '#c77e00' : '#c0392b'
  return (
    <div className="flex flex-col gap-1.5 p-4 rounded-xl bg-[rgba(255,255,255,.55)] dark:bg-[rgba(30,28,25,.55)] ring-1 ring-[rgba(0,0,0,.07)]">
      <div className="text-[11px] uppercase tracking-widest text-[#8a8780]">{label}</div>
      <div className="text-2xl font-semibold" style={{ color }}>
        {score != null ? fmt(score, 1) : '—'}
        {score != null && <span className="text-sm font-normal text-[#8a8780]"> / 10</span>}
      </div>
      {sub && <div className="text-[12px] text-[#6a6763] dark:text-[#9a9790] leading-snug">{sub}</div>}
      {score != null && (
        <div className="h-1 rounded-full bg-[rgba(0,0,0,.08)] overflow-hidden">
          <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, backgroundColor: color }} />
        </div>
      )}
    </div>
  )
}

// ── Projection table ──────────────────────────────────────────────────────────

function ProjectionTable({ pv }: { pv: NonNullable<Enrichment['projection_valeur']> }) {
  return (
    <div className="p-4 rounded-xl bg-[rgba(255,255,255,.55)] dark:bg-[rgba(30,28,25,.55)] ring-1 ring-[rgba(0,0,0,.07)]">
      <div className="text-[11px] uppercase tracking-widest text-[#8a8780] mb-3">Projection (scénario de base)</div>
      <div className="text-[12px] text-[#6a6763] dark:text-[#9a9790] mb-2">
        Base&nbsp;: <span className="font-medium text-[#1a1916] dark:text-white">{fmtMoney(pv.valeur_base)}</span>
        &nbsp;· Taux&nbsp;: {formatPct(pv.taux_base_pct, 2)}/an
      </div>
      <div className="grid grid-cols-3 gap-2">
        {([['1 an', pv.an1], ['3 ans', pv.an3], ['5 ans', pv.an5]] as [string, number][]).map(([label, val]) => (
          <div key={label} className="text-center">
            <div className="text-[10px] text-[#8a8780] uppercase tracking-wide">{label}</div>
            <div className="text-[14px] font-semibold text-[#1a1916] dark:text-white">{fmtMoney(val)}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Main panel ────────────────────────────────────────────────────────────────

export default function SynthesePanel({ dossierId, address, onCritiqueFound }: Props) {
  const [enrichment, setEnrichment] = useState<Enrichment | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!dossierId) { setLoading(false); return }
    setLoading(true)
    fetchRuntimeEnrichment(dossierId).then(data => {
      setEnrichment(data)
      setLoading(false)
      const nb = data?.alertes?.nb_critiques ?? 0
      if (nb > 0) onCritiqueFound?.(nb)
    }).catch(() => setLoading(false))
  }, [dossierId, onCritiqueFound])

  if (loading) return <PanelSkeleton />

  if (!enrichment || !enrichment.score_global) {
    return (
      <EmptyState
        title="Synthèse non disponible"
        subtitle="Lancez le pipeline pour générer le tableau de bord de synthèse."
      />
    )
  }

  const { score_global, alertes, score_investissement, indice_qualite_vie, score_risque, projection_valeur, rendement_locatif, valeur_indicative, taxes_municipales, ratio_prix_loyer, vetuste_batiment, cout_renovation, marche } = enrichment

  return (
    <div className="absolute inset-0 overflow-y-auto px-6 pb-10 pt-5">
      <div className="max-w-[720px] mx-auto flex flex-col gap-5">

        {/* Score global */}
        {score_global && <ScoreGlobalCard sg={score_global} />}

        {/* Alertes */}
        {alertes && alertes.liste.length > 0 && (
          <div className="rounded-2xl ring-1 ring-[rgba(0,0,0,.08)] bg-[rgba(255,255,255,.45)] dark:bg-[rgba(30,28,25,.45)] p-5">
            <div className="flex items-center gap-3 mb-3">
              <h2 className="text-[13px] font-semibold text-[#1a1916] dark:text-white">Alertes</h2>
              {alertes.nb_critiques > 0 && (
                <span className="text-[11px] font-semibold bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300 px-2 py-0.5 rounded-full">
                  {alertes.nb_critiques} critique{alertes.nb_critiques > 1 ? 's' : ''}
                </span>
              )}
              {alertes.nb_attention > 0 && (
                <span className="text-[11px] font-semibold bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300 px-2 py-0.5 rounded-full">
                  {alertes.nb_attention} attention{alertes.nb_attention > 1 ? 's' : ''}
                </span>
              )}
            </div>
            <div className="divide-y divide-[rgba(0,0,0,.06)]">
              {alertes.liste.map((a, i) => <AlerteRow key={i} alerte={a} />)}
            </div>
          </div>
        )}

        {/* Scores grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <ScoreChip
            label="Investissement"
            score={score_investissement?.score}
            sub={score_investissement?.recommandation}
          />
          <ScoreChip
            label="Marché"
            score={marche?.score_marche}
            sub={marche?.marche_interpretation ?? marche?.tension_locative ?? undefined}
          />
          <ScoreChip
            label="Qualité de vie"
            score={indice_qualite_vie?.score}
            sub={indice_qualite_vie?.interpretation}
          />
          <ScoreChip
            label="Risque"
            score={score_risque?.score}
            sub={score_risque?.categorie}
          />
        </div>

        {/* Valeur + projection */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {valeur_indicative && (
            <div className="p-4 rounded-xl bg-[rgba(255,255,255,.55)] dark:bg-[rgba(30,28,25,.55)] ring-1 ring-[rgba(0,0,0,.07)]">
              <div className="text-[11px] uppercase tracking-widest text-[#8a8780] mb-1">Valeur indicative</div>
              <div className="text-xl font-semibold text-[#1a1916] dark:text-white">{fmtMoney(valeur_indicative.valeur)}</div>
              <div className="text-[12px] text-[#6a6763] dark:text-[#9a9790] mt-0.5">{valeur_indicative.fiabilite}</div>
            </div>
          )}
          {rendement_locatif && (
            <div className="p-4 rounded-xl bg-[rgba(255,255,255,.55)] dark:bg-[rgba(30,28,25,.55)] ring-1 ring-[rgba(0,0,0,.07)]">
              <div className="text-[11px] uppercase tracking-widest text-[#8a8780] mb-1">Rendement locatif</div>
              <div className="text-xl font-semibold text-[#1a1916] dark:text-white">
                {formatPct(rendement_locatif.taux_brut_pct, 2)}
                <span className="text-sm font-normal text-[#8a8780]"> brut</span>
              </div>
              <div className="text-[12px] text-[#6a6763] dark:text-[#9a9790] mt-0.5">
                Net estimé&nbsp;: {formatPct(rendement_locatif.taux_net_pct, 2)}
              </div>
            </div>
          )}
        </div>

        {/* Projection */}
        {projection_valeur && <ProjectionTable pv={projection_valeur} />}

        {/* Secondary metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[13px]">
          {taxes_municipales && (
            <div className="p-4 rounded-xl bg-[rgba(255,255,255,.55)] dark:bg-[rgba(30,28,25,.55)] ring-1 ring-[rgba(0,0,0,.07)]">
              <div className="text-[11px] uppercase tracking-widest text-[#8a8780] mb-1">Taxes mun.</div>
              <div className="font-semibold text-[#1a1916] dark:text-white">{fmtMoney(taxes_municipales.annuel)}/an</div>
              <div className="text-[12px] text-[#6a6763] dark:text-[#9a9790]">{fmt(taxes_municipales.taux_pct, 3)}&nbsp;%</div>
            </div>
          )}
          {ratio_prix_loyer && (
            <div className="p-4 rounded-xl bg-[rgba(255,255,255,.55)] dark:bg-[rgba(30,28,25,.55)] ring-1 ring-[rgba(0,0,0,.07)]">
              <div className="text-[11px] uppercase tracking-widest text-[#8a8780] mb-1">Ratio P/L</div>
              <div className="font-semibold text-[#1a1916] dark:text-white">{fmt(ratio_prix_loyer.ratio, 1)}×</div>
              <div className="text-[12px] text-[#6a6763] dark:text-[#9a9790]">{ratio_prix_loyer.signal}</div>
            </div>
          )}
          {vetuste_batiment && (
            <div className="p-4 rounded-xl bg-[rgba(255,255,255,.55)] dark:bg-[rgba(30,28,25,.55)] ring-1 ring-[rgba(0,0,0,.07)]">
              <div className="text-[11px] uppercase tracking-widest text-[#8a8780] mb-1">Vétusté</div>
              <div className="font-semibold text-[#1a1916] dark:text-white">{vetuste_batiment.age_ans} ans</div>
              <div className="text-[12px] text-[#6a6763] dark:text-[#9a9790]">{vetuste_batiment.categorie}</div>
            </div>
          )}
          {cout_renovation && (
            <div className="p-4 rounded-xl bg-[rgba(255,255,255,.55)] dark:bg-[rgba(30,28,25,.55)] ring-1 ring-[rgba(0,0,0,.07)]">
              <div className="text-[11px] uppercase tracking-widest text-[#8a8780] mb-1">Rénovation estimée</div>
              <div className="font-semibold text-[#1a1916] dark:text-white">
                {fmtMoney(cout_renovation.cout_min)}–{fmtMoney(cout_renovation.cout_max)}
              </div>
              <div className="text-[12px] text-[#6a6763] dark:text-[#9a9790]">{cout_renovation.type_travaux}</div>
            </div>
          )}
        </div>

        {dossierId && <ValuationTrace sessionId={dossierId} />}

        <div className="flex justify-center">
          <button
            type="button"
            onClick={() => printWindow(buildSyntheseHtml(enrichment, address), address ?? 'Synthèse')}
            className="rounded-full px-3.5 py-2 text-[11px] bg-black/[.05] text-[#5a5854] hover:bg-black/[.09] transition-colors"
          >
            🖨 Imprimer la synthèse
          </button>
        </div>
        <p className="text-center text-[11px] text-[#8a8780] pb-2">
          {`Données calculées à titre indicatif — validation d'un évaluateur agréé requise.`}
        </p>
      </div>
    </div>
  )
}
