'use client'

/* Marché — vue document-first du design handoff (StageMarche) :
   panel « Analyse comparative » avec comp-table + bloc de réconciliation.
   Données réelles du runtime ; le chat passe par la capsule globale (P5b). */

import { useEffect, useState } from 'react'
import PanelLoader from '@/components/shared/PanelLoader'
import PanelError from '@/components/shared/PanelError'
import SourceDiagnosticPanel from '@/components/shared/SourceDiagnosticPanel'
import { Icon } from '@/components/shared/Icon'
import { fetchRuntimeEnrichment, fetchRuntimeComparables, fetchRuntimeAdjustments } from '@/lib/runtime-api'
import { printWindow } from '@/lib/print-window'
import { buildMarcheHtml } from '@/lib/marche-html'
import { buildComparablesCsv } from '@/lib/build-comparables-csv'
import { checkComparableMinimum } from '@/lib/check-comparable-minimum'
import { detectDuplicateComparables } from '@/lib/detect-duplicate-comparables'
import { computePricePerM2Stats } from '@/lib/compute-price-per-m2-stats'
import { computeDataQualityReport } from '@/lib/compute-data-quality-report'
import { fmtNum, formatCAD } from '@/lib/format-number'
import type { Comparable, Adjustment, EnrichmentMarche, SourceCoverage } from '@/types'

interface Props {
  dossierId: string | null
  address?: string
}

export default function MarchePanel({ dossierId, address }: Props) {
  const [comparables, setComparables] = useState<Comparable[]>([])
  const [adjustments, setAdjustments] = useState<Adjustment[]>([])
  const [marche, setMarche] = useState<EnrichmentMarche | null>(null)
  const [valeurIndicative, setValeurIndicative] = useState<number | null>(null)
  const [sourceCoverage, setSourceCoverage] = useState<SourceCoverage | null>(null)
  const [loading, setLoading] = useState(true)
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
      setValeurIndicative(enrichment?.valeur_indicative?.valeur ?? null)
      setSourceCoverage(enrichment?.source_coverage ?? null)
      setLoading(false)
    }).catch(() => { setError(true); setLoading(false) })
  }

  useEffect(() => { load() }, [dossierId]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!dossierId || loading) return <PanelLoader />
  if (error) return <PanelError onRetry={load} />

  const minimumCheck = checkComparableMinimum(comparables)
  const duplicates = detectDuplicateComparables(comparables)
  const m2Stats = computePricePerM2Stats(comparables)
  const dataQuality = comparables.length > 0 ? computeDataQualityReport(comparables, adjustments) : null

  return (
    <div className="flex-1 overflow-y-auto" style={{ minHeight: 0 }}>
      <div className="flex flex-col gap-5 pb-10">
        <section className="panel">
          <div className="panel-head">
            <div>
              <div className="eyebrow">Étape 2 — Marché</div>
              <h2>Analyse comparative</h2>
            </div>
            <div className="panel-actions" style={{ display: 'flex', gap: 8 }}>
              {comparables.length > 0 && (
                <>
                  <button
                    type="button"
                    className="btn ghost btn-sm"
                    onClick={() => {
                      const csv = buildComparablesCsv(comparables)
                      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
                      const url = URL.createObjectURL(blob)
                      const a = document.createElement('a')
                      a.href = url
                      a.download = `comparables${address ? '-' + address.slice(0, 30).replace(/\s+/g, '-') : ''}.csv`
                      a.click()
                      URL.revokeObjectURL(url)
                    }}
                  >
                    Export CSV
                  </button>
                  <button
                    type="button"
                    className="btn secondary btn-sm"
                    onClick={() => printWindow(buildMarcheHtml(comparables, marche, address, adjustments), address ?? 'Marché')}
                  >
                    <Icon.Print/> Imprimer
                  </button>
                </>
              )}
            </div>
          </div>

          {comparables.length === 0 ? (
            <>
              {sourceCoverage
                ? <SourceDiagnosticPanel coverage={sourceCoverage} />
                : (
                  <p className="notes-body">
                    Aucune source de comparables disponible. Importez un export CSV JLR au
                    checkpoint 2 ou lancez l&apos;analyse depuis l&apos;onglet Dossier.
                  </p>
                )}
            </>
          ) : (
            <>
              <div className="comp-table">
                <div className="comp-head">
                  <div>Comparable</div>
                  <div>Vendu</div>
                  <div className="num">Superficie</div>
                  <div className="num">Prix</div>
                  <div className="num">$/m²</div>
                  <div className="num">Score</div>
                  <div className="num">Année</div>
                </div>
                {comparables.map(c => {
                  const ppm2 = c.hab_m2 ? c.sale_price / c.hab_m2 : null
                  return (
                    <div className="comp-row" key={c.id}>
                      <div className="c-addr">
                        <div className="line1">{c.address}</div>
                        <div className="line2">{c.meta || c.source_id || ''}</div>
                      </div>
                      <div className="c-when">{c.date}</div>
                      <div className="num">{c.hab_m2 ? `${fmtNum(c.hab_m2)} m²` : '—'}</div>
                      <div className="num strong">{formatCAD(c.sale_price)}</div>
                      <div className="num">{ppm2 ? `${Math.round(ppm2)} $` : '—'}</div>
                      <div className="num">{c.score != null ? fmtNum(c.score, 1) : '—'}</div>
                      <div className="num muted">{c.year_built ?? '—'}</div>
                    </div>
                  )
                })}
              </div>

              <div className="recon">
                {m2Stats && (
                  <>
                    <div className="recon-row">
                      <div className="recon-k">Médiane $/m²</div>
                      <div className="recon-v numeric">{fmtNum(m2Stats.median, 0)} $</div>
                    </div>
                    <div className="recon-row">
                      <div className="recon-k">Étendue</div>
                      <div className="recon-v numeric">{fmtNum(m2Stats.min, 0)}–{fmtNum(m2Stats.max, 0)} $</div>
                    </div>
                  </>
                )}
                {valeurIndicative != null && (
                  <div className="recon-row recon-final">
                    <div className="recon-k">Valeur indiquée</div>
                    <div className="recon-v numeric strong">{formatCAD(valeurIndicative)}</div>
                  </div>
                )}
              </div>
            </>
          )}
        </section>

        {(minimumCheck.warning || duplicates.length > 0 || (dataQuality && dataQuality.grade !== 'bon')) && (
          <section className="panel">
            <div className="panel-head">
              <h2>Vérifications</h2>
            </div>
            <div className="flex flex-col gap-2">
              {minimumCheck.warning && (
                <div className="rounded-[8px] px-3 py-2 text-[12.5px]"
                  style={{ color: 'var(--ochre)', background: 'rgba(184,138,62,.10)', border: '1px solid rgba(184,138,62,.2)' }}>
                  {minimumCheck.warning}
                </div>
              )}
              {duplicates.length > 0 && (
                <div className="rounded-[8px] px-3 py-2 text-[12.5px]"
                  style={{ color: 'var(--ochre)', background: 'rgba(184,138,62,.10)', border: '1px solid rgba(184,138,62,.2)' }}>
                  {`${duplicates.length} doublon${duplicates.length > 1 ? 's' : ''} potentiel${duplicates.length > 1 ? 's' : ''} détecté${duplicates.length > 1 ? 's' : ''} — vérifier les sources avant validation.`}
                </div>
              )}
              {dataQuality && dataQuality.grade !== 'bon' && dataQuality.issues.map(issue => (
                <div key={issue} className="rounded-[8px] px-3 py-2 text-[12.5px]"
                  style={dataQuality.grade === 'faible'
                    ? { color: 'var(--oxblood)', background: 'rgba(138,48,48,.08)', border: '1px solid rgba(138,48,48,.15)' }
                    : { color: 'var(--ochre)', background: 'rgba(184,138,62,.10)', border: '1px solid rgba(184,138,62,.2)' }}>
                  · {issue}
                </div>
              ))}
            </div>
          </section>
        )}

        {comparables.length > 0 && (
          <section className="panel">
            <div className="panel-head">
              <h2>Notes</h2>
            </div>
            <p className="notes-body">
              Les comparables sont retenus par score, source et récence. Les sources restent
              à valider avant signature.
            </p>
          </section>
        )}
      </div>
    </div>
  )
}
