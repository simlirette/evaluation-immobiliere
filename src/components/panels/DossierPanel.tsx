'use client'

/* Dossier — vue document-first du design handoff (StageDossier) :
   panels Faits / Mandat / Visite / Documents sur données runtime réelles,
   en conservant pipeline (polling + progress), checkpoints CP1-CP4,
   upload de documents, correction de faits et inspection (élément 14 NPP).
   Le chat passe par la capsule globale. La création de dossier vit dans
   le wizard /dossier/nouveau. */

import { useEffect, useState } from 'react'
import Chip from '@/components/shared/Chip'
import DocItem from '@/components/shared/DocItem'
import DropZone from '@/components/shared/DropZone'
import PanelLoader from '@/components/shared/PanelLoader'
import PanelError from '@/components/shared/PanelError'
import PipelineProgress from '@/components/shared/PipelineProgress'
import CheckpointReviewPanel from '@/components/panels/CheckpointReviewPanel'
import CheckpointComparablePanel from '@/components/panels/CheckpointComparablePanel'
import InspectionForm from '@/components/shared/InspectionForm'
import { Icon } from '@/components/shared/Icon'
import { usePipelinePolling, PIPELINE_TERMINAL_STATUSES } from '@/hooks/usePipelinePolling'
import type { PipelineStep } from '@/hooks/usePipelinePolling'
import {
  fetchAppState, fetchRuntimeEnrichment, fetchRuntimeInspection,
  fetchRuntimeDocuments, uploadRuntimeDocument, saveRuntimeFactOverrides,
  downloadLettreMandat,
} from '@/lib/runtime-api'
import type { InspectionData } from '@/lib/runtime-api'
import type { Document, EnrichmentLocalisation, FactChip, SourceCoverage } from '@/types'

interface Props {
  dossierId: string | null
  onPipelineComplete?: () => void
}

interface UploadStatus {
  name: string
  state: 'uploading' | 'error'
  error?: string
}

/* Les fact_chips arrivent en « Libellé : valeur » — découpage k/v pour kv-grid. */
function chipToKV(chip: FactChip): { k: string; v: string } | null {
  const idx = chip.label.indexOf(':')
  if (idx === -1) return null
  return { k: chip.label.slice(0, idx).trim(), v: chip.label.slice(idx + 1).trim() }
}

export default function DossierPanel({ dossierId, onPipelineComplete }: Props) {
  const [chips, setChips] = useState<FactChip[]>([])
  const [documents, setDocuments] = useState<Document[]>([])
  const [showDropZone, setShowDropZone] = useState(false)
  const [loading, setLoading] = useState(true)
  const [fetchError, setFetchError] = useState(false)
  const [uploads, setUploads] = useState<UploadStatus[]>([])

  type MandatData = {
    mandat_type: string
    format_rapport: string
    methodes_requises: string[]
    methode_preponderante: string
  } | null
  const [mandat, setMandat] = useState<MandatData>(null)

  type ConflitData = { detecte: boolean; motif: string } | null
  const [conflit, setConflitData] = useState<ConflitData>(null)
  const [localisation, setLocalisation] = useState<EnrichmentLocalisation | null>(null)
  const [sourceCoverage, setSourceCoverage] = useState<SourceCoverage | null>(null)

  type CommanditaireData = { nom: string; organisation: string; fin_evaluation: string } | null
  const [commanditaire, setCommanditaire] = useState<CommanditaireData>(null)
  const [inspection, setInspection] = useState<InspectionData | null>(null)
  const [showInspectionForm, setShowInspectionForm] = useState(false)

  const [editFacts, setEditFacts] = useState(false)
  const [draftSurface, setDraftSurface] = useState('')
  const [draftZone, setDraftZone] = useState('')
  const [draftDate, setDraftDate] = useState('')
  const [factsSaving, setFactsSaving] = useState(false)

  const [isRunning, setIsRunning] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)
  const [mandatDownloading, setMandatDownloading] = useState(false)

  const {
    steps: pipelineSteps,
    workflowStatus: liveStatus,
    error: pipelineError,
    waitingCheckpoint,
  } = usePipelinePolling(dossierId, isRunning)

  useEffect(() => {
    if (!dossierId) return
    setLoading(true)
    setFetchError(false)
    Promise.all([
      fetchRuntimeDocuments(dossierId),
      fetchAppState(dossierId),
      fetchRuntimeEnrichment(dossierId),
      fetchRuntimeInspection(dossierId).catch(() => null),
    ]).then(([docs, appState, enrichment, insp]) => {
      setDocuments(docs)
      setChips(appState.active?.fact_chips ?? [])
      setMandat(appState.active?.mandat ?? null)
      setConflitData(appState.active?.conflit ?? null)
      setCommanditaire(appState.active?.commanditaire ?? null)
      setLocalisation(enrichment?.localisation ?? null)
      setSourceCoverage(enrichment?.source_coverage ?? null)
      setInspection(insp ?? null)
      setLoading(false)
      // Démarrer le polling uniquement si le pipeline tourne encore
      const status = (appState.active?.workflow.status as string | null) ?? ''
      const existingSteps = (appState.active?.workflow.steps ?? []) as PipelineStep[]
      const allDone = existingSteps.length > 0 && existingSteps.every(s => s.complete)
      if (!PIPELINE_TERMINAL_STATUSES.has(status) && !allDone) {
        setIsRunning(true)
      }
    }).catch(() => {
      setFetchError(true)
      setLoading(false)
    })
  }, [dossierId, refreshKey])

  useEffect(() => {
    if (!isRunning) return
    // Segment terminé → attente checkpoint (polling déjà arrêté par usePipelinePolling)
    if (waitingCheckpoint !== null) {
      setIsRunning(false)
      return
    }
    const allDone = pipelineSteps.length > 0 && pipelineSteps.every(s => s.complete)
    if (PIPELINE_TERMINAL_STATUSES.has(liveStatus) || allDone) {
      setIsRunning(false)
      onPipelineComplete?.()
      setRefreshKey(k => k + 1)
    }
  }, [liveStatus, pipelineSteps, isRunning, waitingCheckpoint, onPipelineComplete])

  async function handleDrop(files: FileList) {
    if (!dossierId) return
    const fileArray = Array.from(files)
    setUploads(fileArray.map(f => ({ name: f.name, state: 'uploading' as const })))
    setShowDropZone(false)

    const results = await Promise.allSettled(fileArray.map(f => uploadRuntimeDocument(dossierId, f)))

    const newDocs: Document[] = []
    const errors: UploadStatus[] = []
    results.forEach((r, i) => {
      if (r.status === 'fulfilled') {
        newDocs.push(r.value)
      } else {
        errors.push({ name: fileArray[i].name, state: 'error', error: r.reason?.message ?? 'Erreur inconnue' })
      }
    })

    setDocuments(prev => [...prev, ...newDocs])
    setUploads(errors)
  }

  if (!dossierId || loading) return <PanelLoader />
  if (fetchError) return <PanelError />

  if (showDropZone) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 gap-4 px-6 pb-9">
        <DropZone onDrop={handleDrop} />
        <button className="btn ghost btn-sm" onClick={() => setShowDropZone(false)}>Annuler</button>
      </div>
    )
  }

  // Checkpoint gate — segment terminé, confirmation humaine requise
  if (waitingCheckpoint !== null && dossierId) {
    const onConfirmed = () => {
      setRefreshKey(k => k + 1)
      setIsRunning(true) // relance le polling du segment suivant
    }
    return (
      <div className="flex flex-col flex-1 overflow-y-auto">
        {waitingCheckpoint === 2
          ? <CheckpointComparablePanel
              dossierId={dossierId}
              checkpoint={waitingCheckpoint}
              onConfirmed={onConfirmed}
            />
          : <CheckpointReviewPanel
              dossierId={dossierId}
              checkpoint={waitingCheckpoint}
              onConfirmed={onConfirmed}
            />
        }
      </div>
    )
  }

  const kvRows = chips.map(chipToKV).filter((r): r is { k: string; v: string } => r !== null)
  const plainChips = chips.filter(c => c.label.indexOf(':') === -1)

  return (
    <div className="flex-1 overflow-y-auto" style={{ minHeight: 0 }}>
      <div className="flex flex-col gap-5 pb-10">

        {/* ── Pipeline en cours ── */}
        {isRunning && (
          <section className="panel">
            <PipelineProgress
              steps={pipelineSteps}
              workflowStatus={liveStatus}
              error={pipelineError}
            />
          </section>
        )}

        {/* ── Conflit d'intérêts ── */}
        {conflit?.detecte && (
          <section className="panel">
            <div className="rounded-[8px] px-3 py-2 text-[12.5px]"
              style={{ color: 'var(--oxblood)', background: 'rgba(138,48,48,.08)', border: '1px solid rgba(138,48,48,.15)' }}>
              Conflit d&apos;intérêts détecté — pipeline arrêté
              {conflit.motif && <div className="mt-1 opacity-80">{conflit.motif}</div>}
            </div>
          </section>
        )}

        {/* ── Caractéristiques (faits runtime) ── */}
        <section className="panel">
          <div className="panel-head">
            <div>
              <div className="eyebrow">Étape 1 — Dossier</div>
              <h2>Caractéristiques</h2>
            </div>
            {!editFacts && chips.length > 0 && (
              <button
                className="btn ghost"
                onClick={() => {
                  setDraftSurface('')
                  setDraftZone('')
                  setDraftDate('')
                  setEditFacts(true)
                }}
              >
                <Icon.Edit/> Corriger
              </button>
            )}
          </div>

          {chips.length === 0 ? (
            <p className="notes-body">
              Aucun fait extrait pour l&apos;instant. Déposez les documents du mandat
              (contrat, acte, photos) puis lancez l&apos;analyse.
            </p>
          ) : (
            <>
              <div className="kv-grid kv-grid-3">
                {kvRows.map((r, i) => (
                  <div className="kv" key={i}>
                    <div className="k">{r.k}</div>
                    <div className="v">{r.v}</div>
                  </div>
                ))}
              </div>
              {plainChips.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {plainChips.map((c, i) => <Chip key={i} label={c.label} highlight={c.highlight} />)}
                </div>
              )}
            </>
          )}

          {editFacts && dossierId && (
            <div className="mt-4 flex flex-col gap-2" style={{ borderTop: '1px solid var(--rule-soft)', paddingTop: 14 }}>
              <div className="grid grid-cols-2 gap-2">
                <div className="flex flex-col gap-1">
                  <label className="text-[11px]" style={{ color: 'var(--ink-faint)' }}>Surface (pi²)</label>
                  <input
                    type="number"
                    min="0"
                    placeholder="ex. 1450"
                    value={draftSurface}
                    onChange={e => setDraftSurface(e.target.value)}
                    className="field"
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[11px]" style={{ color: 'var(--ink-faint)' }}>Zone</label>
                  <input
                    type="text"
                    placeholder="ex. Rosemont"
                    value={draftZone}
                    onChange={e => setDraftZone(e.target.value)}
                    className="field"
                  />
                </div>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-[11px]" style={{ color: 'var(--ink-faint)' }}>Date de référence</label>
                <input
                  type="date"
                  value={draftDate}
                  onChange={e => setDraftDate(e.target.value)}
                  className="field"
                />
              </div>
              <div className="flex gap-2 mt-1">
                <button
                  type="button"
                  disabled={factsSaving}
                  className="btn accent btn-sm disabled:opacity-40"
                  onClick={async () => {
                    setFactsSaving(true)
                    try {
                      await saveRuntimeFactOverrides(dossierId, {
                        surface_pi2: draftSurface ? parseFloat(draftSurface) : null,
                        zone: draftZone || undefined,
                        date_reference: draftDate || undefined,
                      })
                      const appState = await fetchAppState(dossierId)
                      setChips(appState.active?.fact_chips ?? [])
                      setEditFacts(false)
                    } finally {
                      setFactsSaving(false)
                    }
                  }}
                >
                  {factsSaving ? 'Sauvegarde…' : 'Sauvegarder'}
                </button>
                <button type="button" className="btn ghost btn-sm" onClick={() => setEditFacts(false)}>
                  Annuler
                </button>
              </div>
            </div>
          )}

          {sourceCoverage && <SourceCoverageSummary coverage={sourceCoverage} />}
          {localisation && <LocalisationContexte loc={localisation} />}
        </section>

        {/* ── Mandat ── */}
        {(mandat || commanditaire) && (
          <section className="panel">
            <div className="panel-head">
              <h2>Mandat</h2>
            </div>
            <div className="kv-grid kv-grid-2">
              {mandat && (
                <>
                  <div className="kv">
                    <div className="k">Type de mandat</div>
                    <div className="v">{mandat.mandat_type.replace(/_/g, ' ')}</div>
                  </div>
                  <div className="kv">
                    <div className="k">Format de rapport</div>
                    <div className="v">{mandat.format_rapport.replace(/_/g, ' ')}</div>
                  </div>
                </>
              )}
              {commanditaire && (
                <>
                  <div className="kv">
                    <div className="k">Client</div>
                    <div className="v">{commanditaire.organisation || commanditaire.nom}</div>
                  </div>
                  <div className="kv">
                    <div className="k">Représentant</div>
                    <div className="v">{commanditaire.nom}</div>
                  </div>
                  <div className="kv">
                    <div className="k">Fin d&apos;évaluation</div>
                    <div className="v">{commanditaire.fin_evaluation.replace(/_/g, ' ')}</div>
                  </div>
                </>
              )}
            </div>
            {mandat && mandat.methodes_requises.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-3">
                {mandat.methodes_requises.map((m, i) => (
                  <Chip key={i} label={m.replace(/_/g, ' ')} highlight={m === mandat.methode_preponderante} />
                ))}
              </div>
            )}
            {dossierId && (
              <div
                className="mt-4 rounded-[var(--r-md)] px-4 py-3 flex items-center justify-between gap-4"
                style={{ background: 'var(--paper-2)', border: '1px solid var(--rule-soft)' }}
              >
                <div className="min-w-0">
                  <div className="text-[13px] font-medium" style={{ color: 'var(--ink)' }}>
                    Lettre de mandat
                  </div>
                  <div className="text-[12px] mt-0.5" style={{ color: 'var(--ink-mute)' }}>
                    {commanditaire
                      ? `${commanditaire.nom}${commanditaire.organisation ? ` · ${commanditaire.organisation}` : ''}`
                      : 'Document signé requis avant rapport'}
                  </div>
                </div>
                <button
                  onClick={async () => {
                    setMandatDownloading(true)
                    try { await downloadLettreMandat(dossierId) } finally { setMandatDownloading(false) }
                  }}
                  disabled={mandatDownloading}
                  className="btn secondary btn-sm flex-shrink-0 disabled:opacity-40"
                >
                  {mandatDownloading ? 'Génération…' : '↓ PDF'}
                </button>
              </div>
            )}
          </section>
        )}

        {/* ── Visite (élément 14 NPP) ── */}
        <section className="panel">
          <div className="panel-head">
            <h2>Visite</h2>
            <button className="btn secondary" onClick={() => setShowInspectionForm(v => !v)}>
              {inspection
                ? (showInspectionForm ? 'Fermer' : 'Modifier')
                : <><Icon.Plus/> Saisir l&apos;inspection</>}
            </button>
          </div>
          {inspection ? (
            <div className="visit-row">
              <div className="visit-status visit-done">
                <Icon.Check/>
                <div>
                  <div className="visit-title">Inspection enregistrée</div>
                  <div className="visit-meta">
                    {inspection.date_visite} · {inspection.type_inspection.replace(/_/g, ' ')}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <p className="notes-body">
              Aucune inspection consignée. L&apos;élément 14 NPP exige l&apos;information
              sur l&apos;inspection avant l&apos;attestation finale.
            </p>
          )}
          {showInspectionForm && (
            <div className="mt-3">
              <InspectionForm
                dossierId={dossierId}
                initial={inspection}
                onSaved={insp => { setInspection(insp); setShowInspectionForm(false) }}
              />
            </div>
          )}
        </section>

        {/* ── Documents ── */}
        <section className="panel">
          <div className="panel-head">
            <h2>Documents ({documents.length})</h2>
            <button className="btn secondary" onClick={() => setShowDropZone(true)}>
              <Icon.Plus/> Ajouter
            </button>
          </div>
          {documents.length === 0 ? (
            <p className="notes-body">
              Aucune source rattachée. Déposez le mandat, l&apos;acte et les photos —
              les champs seront extraits automatiquement.
            </p>
          ) : (
            <div className="flex flex-col gap-1.5">
              {documents.map(doc => <DocItem key={doc.id} doc={doc} />)}
            </div>
          )}
          {uploads.map((u, i) => (
            u.state === 'uploading' ? (
              <div key={i} className="text-[12px] mt-2 animate-pulse" style={{ color: 'var(--ink-mute)' }}>
                … {u.name}
              </div>
            ) : (
              <div key={i} className="rounded-[8px] px-3 py-2 mt-2 text-[12px]"
                style={{ color: 'var(--oxblood)', background: 'rgba(138,48,48,.08)', border: '1px solid rgba(138,48,48,.15)' }}>
                {u.name} — {u.error}
              </div>
            )
          ))}
          <p className="text-[12px] mt-3" style={{ color: 'var(--ink-faint)' }}>
            Ces sources viennent des artéfacts runtime. Elles restent à valider avant
            toute conclusion professionnelle.
          </p>
        </section>
      </div>
    </div>
  )
}

/* ── Helpers contextuels (inchangés) ── */

function LocalisationContexte({ loc }: { loc: EnrichmentLocalisation }) {
  const items: Array<{ label: string; value: string; warn?: boolean }> = []

  if (loc.distance_cbd_km != null)
    items.push({ label: 'Distance CBD', value: `${loc.distance_cbd_km.toFixed(1)} km — ${loc.distance_interpretation ?? ''}` })
  if (loc.zone_code)
    items.push({ label: 'Zonage', value: `${loc.zone_code}${loc.type_zone ? ` — ${loc.type_zone}` : ''}` })
  if (loc.en_zone_inondable != null)
    items.push({ label: 'Zone inondable', value: loc.en_zone_inondable ? `Oui (${loc.inondable_recurrence ?? '—'})` : 'Non', warn: loc.en_zone_inondable ?? false })
  if (loc.en_zone_agricole != null)
    items.push({ label: 'Zone agricole', value: loc.en_zone_agricole ? 'Oui — CPTAQ' : 'Non', warn: loc.en_zone_agricole ?? false })
  if (loc.patrimoine_repertorie != null)
    items.push({ label: 'Patrimoine culturel', value: loc.patrimoine_repertorie ? (loc.patrimoine_nom ?? 'Répertorié') : 'Non répertorié', warn: loc.patrimoine_repertorie ?? false })
  if (loc.ecoles_1km != null || loc.arrets_transport_500m != null || loc.epiceries_500m != null) {
    const parts = [
      loc.ecoles_1km != null ? `${loc.ecoles_1km} école(s) ≤1 km` : null,
      loc.arrets_transport_500m != null ? `${loc.arrets_transport_500m} arrêt(s) ≤500 m` : null,
      loc.epiceries_500m != null ? `${loc.epiceries_500m} épicerie(s) ≤500 m` : null,
    ].filter(Boolean)
    if (parts.length > 0) items.push({ label: 'Proximité services', value: parts.join(' · ') })
  }
  if (loc.score_nuisances != null)
    items.push({ label: 'Nuisances env.', value: `Score ${loc.score_nuisances}/4 — ${loc.nuisances_interpretation ?? ''}`, warn: (loc.score_nuisances ?? 0) >= 2 })
  if (loc.crime_taux_total != null)
    items.push({ label: 'Criminalité CMA', value: `${Math.round(loc.crime_taux_total).toLocaleString('fr-CA')} / 100 k hab.`, warn: loc.crime_taux_total > 6000 })
  if (loc.cegep_5km != null || loc.universite_10km != null) {
    const parts = [
      loc.cegep_5km != null ? `${loc.cegep_5km} cégep(s) ≤5 km` : null,
      loc.universite_10km != null ? `${loc.universite_10km} univ. ≤10 km` : null,
    ].filter(Boolean)
    if (parts.length > 0) items.push({ label: 'Enseignement sup.', value: (loc.postsec_interpretation ? `${loc.postsec_interpretation} — ` : '') + parts.join(' · ') })
  }
  if (loc.routes_interpretation)
    items.push({ label: 'Accès axes routiers', value: [
      loc.routes_interpretation,
      loc.autoroute_km != null ? `A-${loc.autoroute_km.toFixed(1)} km` : null,
      loc.artere_km != null ? `artère ${loc.artere_km.toFixed(1)} km` : null,
    ].filter(Boolean).join(' · ') })
  if (loc.temperature_moy_c != null || loc.jours_gel != null) {
    const parts = [
      loc.temperature_moy_c != null ? `T moy ${loc.temperature_moy_c.toFixed(1)}°C` : null,
      loc.precipitations_mm != null ? `${Math.round(loc.precipitations_mm)} mm/an` : null,
      loc.jours_gel != null ? `${loc.jours_gel} j gel` : null,
      loc.jours_chaleur_extreme != null ? `${loc.jours_chaleur_extreme} j canicule` : null,
    ].filter(Boolean)
    if (parts.length > 0) items.push({ label: 'Climat (2023)', value: parts.join(' · ') })
  }

  if (items.length === 0) return null

  return (
    <div className="mt-4">
      <div className="eyebrow mb-2">Localisation</div>
      <div className="flex flex-col rounded-[var(--r-md)] overflow-hidden" style={{ background: 'var(--paper-2)' }}>
        {items.map(item => (
          <div key={item.label} className="flex items-start justify-between px-3 py-2 gap-4" style={{ borderBottom: '1px solid var(--rule-soft)' }}>
            <span className="text-[12px] flex-shrink-0" style={{ color: 'var(--ink-mute)' }}>{item.label}</span>
            <span className="text-[12px] text-right" style={{ color: item.warn ? 'var(--ochre)' : 'var(--ink)', fontWeight: item.warn ? 500 : 400 }}>
              {item.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function SourceCoverageSummary({ coverage }: { coverage: SourceCoverage }) {
  const problemItems = coverage.diagnostics
    .filter(d => ['failed', 'empty', 'skipped', 'partial'].includes(d.status))
    .slice(-4)

  if (coverage.status === 'unknown' || coverage.diagnostics.length === 0) return null

  const warn = coverage.failed_count > 0

  return (
    <div className="mt-4 rounded-[8px] px-3 py-2"
      style={warn
        ? { color: 'var(--ochre)', background: 'rgba(184,138,62,.10)', border: '1px solid rgba(184,138,62,.2)' }
        : { color: 'var(--ink-2)', background: 'var(--paper-2)', border: '1px solid var(--rule-soft)' }}>
      <div className="flex items-center justify-between gap-3">
        <span className="eyebrow">Sources publiques</span>
        <span className="text-[11px] font-medium numeric">{coverage.available_count}/{coverage.expected_sources.length}</span>
      </div>
      {problemItems.length > 0 && (
        <div className="mt-1.5 flex flex-col gap-1">
          {problemItems.map((d, i) => (
            <div key={`${d.source}-${d.stage}-${i}`} className="text-[12px] leading-snug">
              <span className="font-medium uppercase">{d.source}</span>
              <span className="opacity-80"> - {d.message}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
