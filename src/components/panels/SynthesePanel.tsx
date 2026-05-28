'use client'

import { useEffect, useState } from 'react'
import PanelSkeleton from '@/components/shared/PanelSkeleton'
import PanelError from '@/components/shared/PanelError'
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
    <div className={`rounded-[var(--r-lg)] ring-1 ${colors.ring} ${colors.bg} px-4 py-2 flex items-center gap-3`}>
      <div className={`text-4xl font-semibold leading-none ${colors.text}`}>{sg.grade}</div>
      <div className="min-w-0">
        <div className="text-[18px] font-semibold" style={{ color: 'var(--ink)' }}>
          {fmt(sg.score, 2)} <span className="text-[13px] font-normal" style={{ color: 'var(--ink-mute)' }}>/ 10</span>
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
    <div className="flex items-start gap-3 py-2.5" style={{ borderBottom: '1px solid var(--rule-soft)' }}>
      <span className={`mt-1.5 w-2 h-2 rounded-full flex-shrink-0 ${s.dot}`} />
      <div className="flex-1 min-w-0">
        <span className={`inline-block text-[10px] font-semibold tracking-wider px-1.5 py-0.5 rounded mr-2 ${s.badge}`}>
          {s.text}
        </span>
        <span className="text-[12px] capitalize" style={{ color: 'var(--ink-mute)' }}>
          {alerte.categorie.replace(/_/g, ' ')}
        </span>
        <p className="text-[13px] mt-0.5 leading-snug" style={{ color: 'var(--ink)' }}>
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
    <div className="panel flex flex-col gap-1.5">
      <div className="eyebrow">{label}</div>
      <div className="text-[22px] font-medium" style={{ fontFamily: 'var(--font-serif)', color }}>
        {score != null ? fmt(score, 1) : '—'}
        {score != null && <span className="text-[13px] font-normal" style={{ color: 'var(--ink-mute)' }}> / 10</span>}
      </div>
      {sub && <div className="text-[12px] leading-snug" style={{ color: 'var(--ink-mute)' }}>{sub}</div>}
      {score != null && (
        <div className="h-1 rounded-full overflow-hidden mt-1" style={{ background: 'var(--rule)' }}>
          <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, backgroundColor: color }} />
        </div>
      )}
    </div>
  )
}

// ── Projection table ──────────────────────────────────────────────────────────

function ProjectionTable({ pv }: { pv: NonNullable<Enrichment['projection_valeur']> }) {
  return (
    <section className="panel">
      <div className="panel-head">
        <h2 className="panel-title">Projection (scénario de base)</h2>
      </div>
      <div className="text-[13px] mb-4" style={{ color: 'var(--ink-mute)' }}>
        Base&nbsp;: <span className="font-medium" style={{ color: 'var(--ink)' }}>{fmtMoney(pv.valeur_base)}</span>
        &nbsp;· Taux&nbsp;: {formatPct(pv.taux_base_pct, 2)}/an
      </div>
      <div className="grid grid-cols-3 gap-4">
        {([['1 an', pv.an1], ['3 ans', pv.an3], ['5 ans', pv.an5]] as [string, number][]).map(([label, val]) => (
          <div key={label}>
            <div className="eyebrow mb-1">{label}</div>
            <div className="text-[17px] font-medium" style={{ fontFamily: 'var(--font-serif)', color: 'var(--ink)' }}>{fmtMoney(val)}</div>
          </div>
        ))}
      </div>
    </section>
  )
}

// ── Main panel ────────────────────────────────────────────────────────────────

export default function SynthesePanel({ dossierId, address, onCritiqueFound }: Props) {
  const [enrichment, setEnrichment] = useState<Enrichment | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    if (!dossierId) { setLoading(false); return }
    setLoading(true)
    setError(false)
    fetchRuntimeEnrichment(dossierId).then(data => {
      setEnrichment(data)
      setLoading(false)
      const nb = data?.alertes?.nb_critiques ?? 0
      if (nb > 0) onCritiqueFound?.(nb)
    }).catch(() => { setError(true); setLoading(false) })
  }, [dossierId, onCritiqueFound])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError />

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
    <div className="flex flex-col gap-5 pb-10">

      {/* Score global */}
      {score_global && (
        <section className="panel">
          <div className="panel-head">
            <div>
              <div className="eyebrow">Étape 4 — Synthèse</div>
              <h2 className="panel-title">Score global</h2>
            </div>
            <ScoreGlobalCard sg={score_global} />
          </div>
          <p className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>{score_global.recommandation}</p>
        </section>
      )}

      {/* Alertes */}
      {alertes && alertes.liste.length > 0 && (
        <section className="panel">
          <div className="panel-head">
            <h2 className="panel-title">Alertes</h2>
            <div className="flex gap-2">
              {alertes.nb_critiques > 0 && (
                <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full"
                  style={{ background: 'rgba(138,48,48,.1)', color: 'var(--oxblood)' }}>
                  {alertes.nb_critiques} critique{alertes.nb_critiques > 1 ? 's' : ''}
                </span>
              )}
              {alertes.nb_attention > 0 && (
                <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full"
                  style={{ background: 'rgba(180,130,0,.1)', color: 'var(--ochre)' }}>
                  {alertes.nb_attention} attention{alertes.nb_attention > 1 ? 's' : ''}
                </span>
              )}
            </div>
          </div>
          <div style={{ borderTop: '1px solid var(--rule-soft)' }}>
            {alertes.liste.map((a, i) => <AlerteRow key={i} alerte={a} />)}
          </div>
        </section>
      )}

      {/* Scores grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <ScoreChip label="Investissement" score={score_investissement?.score} sub={score_investissement?.recommandation} />
        <ScoreChip label="Marché" score={marche?.score_marche} sub={marche?.marche_interpretation ?? marche?.tension_locative ?? undefined} />
        <ScoreChip label="Qualité de vie" score={indice_qualite_vie?.score} sub={indice_qualite_vie?.interpretation} />
        <ScoreChip label="Risque" score={score_risque?.score} sub={score_risque?.categorie} />
      </div>

      {/* Valeur + rendement */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {valeur_indicative && (
          <section className="panel">
            <div className="eyebrow mb-1">Valeur indicative</div>
            <div className="text-[22px] font-medium" style={{ fontFamily: 'var(--font-serif)', color: 'var(--ink)' }}>
              {fmtMoney(valeur_indicative.valeur)}
            </div>
            <div className="text-[12px] mt-1" style={{ color: 'var(--ink-mute)' }}>{valeur_indicative.fiabilite}</div>
          </section>
        )}
        {rendement_locatif && (
          <section className="panel">
            <div className="eyebrow mb-1">Rendement locatif</div>
            <div className="text-[22px] font-medium" style={{ fontFamily: 'var(--font-serif)', color: 'var(--ink)' }}>
              {formatPct(rendement_locatif.taux_brut_pct, 2)}
              <span className="text-[14px] font-normal" style={{ color: 'var(--ink-mute)' }}> brut</span>
            </div>
            <div className="text-[12px] mt-1" style={{ color: 'var(--ink-mute)' }}>
              Net estimé&nbsp;: {formatPct(rendement_locatif.taux_net_pct, 2)}
            </div>
          </section>
        )}
      </div>

      {/* Projection */}
      {projection_valeur && <ProjectionTable pv={projection_valeur} />}

      {/* Secondary metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {taxes_municipales && (
          <section className="panel">
            <div className="eyebrow mb-1">Taxes mun.</div>
            <div className="font-semibold text-[15px]" style={{ color: 'var(--ink)' }}>{fmtMoney(taxes_municipales.annuel)}/an</div>
            <div className="text-[12px] mt-0.5" style={{ color: 'var(--ink-mute)' }}>{fmt(taxes_municipales.taux_pct, 3)}&nbsp;%</div>
          </section>
        )}
        {ratio_prix_loyer && (
          <section className="panel">
            <div className="eyebrow mb-1">Ratio P/L</div>
            <div className="font-semibold text-[15px]" style={{ color: 'var(--ink)' }}>{fmt(ratio_prix_loyer.ratio, 1)}×</div>
            <div className="text-[12px] mt-0.5" style={{ color: 'var(--ink-mute)' }}>{ratio_prix_loyer.signal}</div>
          </section>
        )}
        {vetuste_batiment && (
          <section className="panel">
            <div className="eyebrow mb-1">Vétusté</div>
            <div className="font-semibold text-[15px]" style={{ color: 'var(--ink)' }}>{vetuste_batiment.age_ans} ans</div>
            <div className="text-[12px] mt-0.5" style={{ color: 'var(--ink-mute)' }}>{vetuste_batiment.categorie}</div>
          </section>
        )}
        {cout_renovation && (
          <section className="panel">
            <div className="eyebrow mb-1">Rénovation estimée</div>
            <div className="font-semibold text-[13px]" style={{ color: 'var(--ink)' }}>
              {fmtMoney(cout_renovation.cout_min)}–{fmtMoney(cout_renovation.cout_max)}
            </div>
            <div className="text-[12px] mt-0.5" style={{ color: 'var(--ink-mute)' }}>{cout_renovation.type_travaux}</div>
          </section>
        )}
      </div>

      {dossierId && <ValuationTrace sessionId={dossierId} />}

      <div className="flex justify-center gap-2">
        <button
          type="button"
          onClick={() => printWindow(buildSyntheseHtml(enrichment, address), address ?? 'Synthèse')}
          className="btn ghost btn-sm"
        >
          Imprimer la synthèse
        </button>
      </div>
      <p className="text-center text-[11px] pb-2" style={{ color: 'var(--ink-faint)' }}>
        {`Données calculées à titre indicatif — validation d'un évaluateur agréé requise.`}
      </p>
    </div>
  )
}
