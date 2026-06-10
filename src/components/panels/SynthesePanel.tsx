'use client'

/* Synthèse — vue document-first du design handoff (StageSynthese) :
   hero valeur marchande + méta, narratif, attestation (signature É.A. réelle),
   suivi du tableau de bord d'alertes et de scores du runtime. */

import { useEffect, useState } from 'react'
import PanelSkeleton from '@/components/shared/PanelSkeleton'
import PanelError from '@/components/shared/PanelError'
import EmptyState from '@/components/shared/EmptyState'
import ValuationTrace from '@/components/shared/ValuationTrace'
import SignatureForm from '@/components/shared/SignatureForm'
import { Icon } from '@/components/shared/Icon'
import { fetchRuntimeEnrichment, fetchAppState, fetchRuntimeSignature, type SignatureData } from '@/lib/runtime-api'
import { printWindow } from '@/lib/print-window'
import { buildSyntheseHtml } from '@/lib/synthese-html'
import { formatCAD, fmtNum } from '@/lib/format-number'
import type { Enrichment, EnrichmentAlerte } from '@/types'

interface Props {
  dossierId: string | null
  address?: string
  onCritiqueFound?: (count: number) => void
}

const METHODE_LABELS: Record<string, string> = {
  approche_comparative: 'Comparaison directe',
  approche_cout: 'Coût',
  approche_revenu: 'Revenu',
  approche_fta: 'Flux de trésorerie actualisés',
}

const ALERTE_STYLES: Record<string, { color: string; bg: string; text: string }> = {
  critique:  { color: 'var(--oxblood)', bg: 'rgba(138,48,48,.08)', text: 'CRITIQUE' },
  attention: { color: 'var(--ochre)',   bg: 'rgba(184,138,62,.10)', text: 'ATTENTION' },
  info:      { color: 'var(--navy)',    bg: 'var(--navy-tint)',     text: 'INFO' },
}

function AlerteRow({ alerte }: { alerte: EnrichmentAlerte }) {
  const s = ALERTE_STYLES[alerte.niveau] ?? ALERTE_STYLES['info']
  return (
    <div className="flex items-start gap-3 py-2.5" style={{ borderBottom: '1px solid var(--rule-soft)' }}>
      <span className="mt-1.5 w-2 h-2 rounded-full flex-shrink-0" style={{ background: s.color }} />
      <div className="flex-1 min-w-0">
        <span className="inline-block text-[10px] font-semibold tracking-wider px-1.5 py-0.5 rounded mr-2"
          style={{ color: s.color, background: s.bg }}>
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

export default function SynthesePanel({ dossierId, address, onCritiqueFound }: Props) {
  const [enrichment, setEnrichment] = useState<Enrichment | null>(null)
  const [conclusion, setConclusion] = useState<number | null>(null)
  const [conclusionStatus, setConclusionStatus] = useState<string>('')
  const [methode, setMethode] = useState<string | null>(null)
  const [signature, setSignature] = useState<SignatureData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    if (!dossierId) { setLoading(false); return }
    setLoading(true)
    setError(false)
    Promise.all([
      fetchRuntimeEnrichment(dossierId),
      fetchAppState(dossierId),
      fetchRuntimeSignature(dossierId).catch(() => null),
    ]).then(([data, state, sig]) => {
      setEnrichment(data)
      setConclusion(state.active?.valuation.conclusion.value ?? null)
      setConclusionStatus(state.active?.valuation.status ?? '')
      setMethode(state.active?.mandat?.methode_preponderante ?? null)
      setSignature(sig)
      setLoading(false)
      const nb = data?.alertes?.nb_critiques ?? 0
      if (nb > 0) onCritiqueFound?.(nb)
    }).catch(() => { setError(true); setLoading(false) })
  }, [dossierId, onCritiqueFound])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError />

  if (!enrichment && conclusion == null) {
    return (
      <EmptyState
        title="Synthèse non disponible"
        subtitle="Lancez le pipeline pour générer la synthèse de valeur."
      />
    )
  }

  const heroValue = conclusion ?? enrichment?.valeur_indicative?.valeur ?? null
  const confiance = enrichment?.score_global?.grade
    ? (['A', 'B'].includes(enrichment.score_global.grade) ? 'Élevé'
      : enrichment.score_global.grade === 'C' ? 'Moyen' : 'À revoir')
    : null
  const alertes = enrichment?.alertes ?? null

  return (
    <div className="flex flex-col gap-5 pb-10">

      {/* ── Hero — design handoff ── */}
      <section className="panel synthese-hero">
        <div className="eyebrow">Étape 4 — Synthèse</div>
        <div className="syn-label">Valeur marchande estimée</div>
        <div className="syn-value numeric">{heroValue != null ? formatCAD(heroValue) : '—'}</div>
        {enrichment?.valeur_indicative?.fiabilite && (
          <div className="syn-range">{enrichment.valeur_indicative.fiabilite}</div>
        )}
        <div className="syn-meta">
          {methode && (
            <div><span className="k">Méthode dominante</span><span className="v">{METHODE_LABELS[methode] ?? methode}</span></div>
          )}
          {confiance && (
            <div><span className="k">Niveau de confiance</span><span className={`v ${confiance === 'Élevé' ? 'conf' : ''}`}>{confiance}</span></div>
          )}
          {conclusionStatus && (
            <div><span className="k">Statut</span><span className="v">{conclusionStatus.replace(/_/g, ' ').toLowerCase()}</span></div>
          )}
        </div>
      </section>

      {/* ── Narratif ── */}
      {enrichment?.score_global?.recommandation && (
        <section className="panel">
          <div className="panel-head">
            <h2>Narratif de synthèse</h2>
          </div>
          <p className="notes-body">{enrichment.score_global.recommandation}</p>
        </section>
      )}

      {/* ── Alertes ── */}
      {alertes && alertes.liste.length > 0 && (
        <section className="panel">
          <div className="panel-head">
            <h2>Alertes</h2>
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

      {/* ── Attestation — design signoff + signature É.A. réelle ── */}
      <section className="panel signoff">
        <div className="panel-head">
          <h2>Attestation</h2>
          <div className="status-pill">
            {signature ? <><Icon.Check/> Signée</> : <><Icon.Clock/> En attente de signature</>}
          </div>
        </div>
        <div className="signoff-body">
          <div className="signoff-text">
            Je certifie que la présente évaluation a été préparée conformément aux
            normes de l&apos;Ordre des évaluateurs agréés du Québec (OEAQ) et qu&apos;elle
            reflète mon opinion professionnelle indépendante de la valeur marchande
            de l&apos;immeuble à la date de valeur indiquée.
          </div>
          {signature && (
            <div className="signoff-sig">
              <div className="sig-line"/>
              <div className="sig-name">{signature.nom_ea}, É.A.</div>
              <div className="sig-cred">OEAQ {signature.no_permis_oeaq} · Évaluateur agréé</div>
            </div>
          )}
        </div>
        {!signature && dossierId && (
          <div style={{ marginTop: 16 }}>
            <SignatureForm dossierId={dossierId} initial={signature} onSigned={setSignature} />
          </div>
        )}
      </section>

      {dossierId && <ValuationTrace sessionId={dossierId} />}

      <div className="flex justify-center gap-2">
        {enrichment && (
          <button
            type="button"
            onClick={() => printWindow(buildSyntheseHtml(enrichment, address), address ?? 'Synthèse')}
            className="btn ghost btn-sm"
          >
            <Icon.Print/> Imprimer la synthèse
          </button>
        )}
      </div>
      <p className="text-center text-[11px] pb-2" style={{ color: 'var(--ink-faint)' }}>
        {`Données calculées à titre indicatif — validation d'un évaluateur agréé requise.`}
      </p>
    </div>
  )
}
