'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import type { FormEvent } from 'react'
import AgentMessage from '@/components/shared/AgentMessage'
import UserMessage from '@/components/shared/UserMessage'
import Chip from '@/components/shared/Chip'
import DocItem from '@/components/shared/DocItem'
import ChatInput from '@/components/shared/ChatInput'
import DropZone from '@/components/shared/DropZone'
import PanelLoader from '@/components/shared/PanelLoader'
import PipelineProgress from '@/components/shared/PipelineProgress'
import { usePipelinePolling, PIPELINE_TERMINAL_STATUSES } from '@/hooks/usePipelinePolling'
import type { PipelineStep } from '@/hooks/usePipelinePolling'
import { fetchDocuments, uploadDocument } from '@/lib/supabase/queries/documents'
import { fetchPropertyFacts } from '@/lib/supabase/queries/property_facts'
import { createDossier } from '@/lib/supabase/queries/dossiers'
import { sendRuntimeMessage, fetchAppState, fetchRuntimeEnrichment } from '@/lib/runtime-api'
import type { Document, EnrichmentLocalisation, FactChip, ComparableInput } from '@/types'

interface Props {
  isNew: boolean
  dossierId: string | null
  onPipelineComplete?: () => void
}

interface AssistantReply {
  id: string
  agent: string
  answer: string
}

interface UploadStatus {
  name: string
  state: 'uploading' | 'error'
  error?: string
}

const LAUNCH_STEPS = [
  { label: 'Création du dossier…', delay: 0 },
  { label: 'Initialisation du runtime…', delay: 3000 },
  { label: 'Collecte des données marché…', delay: 7000 },
  { label: 'Analyse des comparables…', delay: 11000 },
  { label: 'Génération du rapport…', delay: 14000 },
]

const FIN_EVAL_OPTIONS = [
  { value: 'hypothecaire', label: 'Hypothécaire / financement' },
  { value: 'succession', label: 'Succession / liquidation' },
  { value: 'litige', label: 'Litige judiciaire' },
  { value: 'assurance', label: 'Valeur assurable' },
  { value: 'commercial', label: 'Investissement commercial' },
  { value: 'expropriation', label: 'Expropriation' },
  { value: 'autre', label: 'Autre' },
]

function NewDossierForm() {
  const router = useRouter()
  const [formStep, setFormStep] = useState<1 | 2 | 3>(1)
  const [address, setAddress] = useState('Dossier pilote residentiel')
  const [propertyType, setPropertyType] = useState('Residentiel unifamilial')
  const [neighborhood, setNeighborhood] = useState('Zone anonymisee')
  const [cmdNom, setCmdNom] = useState('')
  const [cmdOrg, setCmdOrg] = useState('')
  const [cmdFin, setCmdFin] = useState('hypothecaire')
  const [loading, setLoading] = useState(false)
  const [stepIndex, setStepIndex] = useState(0)
  const [error, setError] = useState('')
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([])

  useEffect(() => {
    return () => timersRef.current.forEach(clearTimeout)
  }, [])

  const [comparables, setComparables] = useState<ComparableInput[]>([])
  const [expandedId, setExpandedId] = useState<string | null>(null)

  function addComparable() {
    const id = Math.random().toString(36).slice(2, 10)
    setComparables(prev => [...prev, {
      id,
      adresse: '',
      date_vente: '',
      prix_vente: 0,
      source_id: '',
      source_type: 'mls_centris',
      type_propriete: '',
      surface_hab: null,
      surface_terrain: null,
      annee_construction: null,
      nb_logements: null,
      conditions_vente: 'normale',
      notes: '',
    }])
    setExpandedId(id)
  }

  function updateComp(id: string, field: keyof ComparableInput, value: string | number | null) {
    setComparables(prev => prev.map(c => c.id === id ? { ...c, [field]: value } : c))
  }

  function removeComp(id: string) {
    setComparables(prev => prev.filter(c => c.id !== id))
    if (expandedId === id) setExpandedId(null)
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!address.trim() || !propertyType.trim() || !neighborhood.trim()) return
    if (!cmdNom.trim()) return
    setLoading(true)
    setStepIndex(0)
    setError('')

    LAUNCH_STEPS.forEach((step, i) => {
      if (i === 0) return
      const t = setTimeout(() => setStepIndex(i), step.delay)
      timersRef.current.push(t)
    })

    try {
      const dossier = await createDossier({
        address: address.trim(),
        property_type: propertyType.trim(),
        neighborhood: neighborhood.trim(),
        commanditaire: {
          nom: cmdNom.trim(),
          organisation: cmdOrg.trim(),
          fin_evaluation: cmdFin,
        },
        comparables: comparables.length > 0 ? comparables : undefined,
      })
      router.push(`/dossier/${dossier.slug}?tab=dossier`)
    } catch (err) {
      timersRef.current.forEach(clearTimeout)
      timersRef.current = []
      setError(err instanceof Error ? err.message : 'Erreur lors de la creation du dossier.')
      setLoading(false)
    }
  }

  const inputStyle = {
    background: 'var(--input-bg)',
    border: '1px solid var(--input-border)',
  }

  const selectStyle = {
    background: 'var(--input-bg)',
    border: '1px solid var(--input-border)',
    appearance: 'none' as const,
    WebkitAppearance: 'none' as const,
  }

  return (
    <div className="w-full max-w-[520px] flex flex-col gap-6 pb-9">
      <div className="text-center">
        <div
          className="text-[20px] font-medium text-[#1a1916] tracking-[-.01em]"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          Nouveau dossier
        </div>
        <p className="mt-1 text-[13px] text-[#8a8780]">
          {formStep === 1
            ? 'Lance un dossier pilote dans le backend runtime et ouvre les agents AI.'
            : formStep === 2
            ? 'Identifiez le commanditaire du mandat.'
            : 'Ajoutez les ventes comparables (optionnel).'}
        </p>
      </div>

      {error && (
        <div className="rounded-[10px] px-4 py-3 text-[13px] text-red-700 bg-red-50/80 border border-red-200/60">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex flex-col gap-3 py-2">
          <div className="w-full h-[3px] rounded-full overflow-hidden" style={{ background: 'var(--input-bg)' }}>
            <div
              className="h-full rounded-full transition-all duration-700 ease-out"
              style={{
                background: '#334155',
                width: `${Math.round(((stepIndex + 1) / LAUNCH_STEPS.length) * 100)}%`,
              }}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            {LAUNCH_STEPS.map((step, i) => (
              <div
                key={i}
                className="flex items-center gap-2 text-[13px] transition-opacity duration-300"
                style={{ opacity: i <= stepIndex ? 1 : 0.28 }}
              >
                <span style={{ color: i < stepIndex ? '#334155' : i === stepIndex ? '#334155' : '#b5b2ac' }}>
                  {i < stepIndex ? '✓' : i === stepIndex ? '›' : '·'}
                </span>
                <span style={{ color: i === stepIndex ? '#1a1916' : i < stepIndex ? '#8a8780' : '#b5b2ac' }}>
                  {step.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : formStep === 1 ? (
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-[12px] text-[#8a8780] font-medium">Nom du dossier</label>
            <input
              type="text"
              required
              value={address}
              onChange={e => setAddress(e.target.value)}
              className="w-full rounded-[10px] px-4 py-2.5 text-[14px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
              style={inputStyle}
            />
          </div>

          <div className="flex gap-3">
            <div className="flex flex-col gap-1.5 flex-1">
              <label className="text-[12px] text-[#8a8780] font-medium">Type</label>
              <input
                type="text"
                required
                value={propertyType}
                onChange={e => setPropertyType(e.target.value)}
                className="w-full rounded-[10px] px-4 py-2.5 text-[14px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
                style={inputStyle}
              />
            </div>
            <div className="flex flex-col gap-1.5 flex-1">
              <label className="text-[12px] text-[#8a8780] font-medium">Secteur</label>
              <input
                type="text"
                required
                value={neighborhood}
                onChange={e => setNeighborhood(e.target.value)}
                className="w-full rounded-[10px] px-4 py-2.5 text-[14px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
                style={inputStyle}
              />
            </div>
          </div>

          <button
            type="button"
            onClick={() => {
              if (address.trim() && propertyType.trim() && neighborhood.trim()) {
                setError('')
                setFormStep(2)
              }
            }}
            className="mt-1 w-full rounded-[10px] py-2.5 text-[14px] font-medium text-white transition-opacity hover:opacity-90 active:opacity-80"
            style={{ background: '#334155' }}
          >
            Suivant →
          </button>
        </div>
      ) : formStep === 2 ? (
        <form onSubmit={e => { e.preventDefault(); if (cmdNom.trim()) { setError(''); setFormStep(3) } }} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-[12px] text-[#8a8780] font-medium">Nom du commanditaire <span className="text-red-500">*</span></label>
            <input
              type="text"
              required
              placeholder="ex. Banque Nationale"
              value={cmdNom}
              onChange={e => setCmdNom(e.target.value)}
              className="w-full rounded-[10px] px-4 py-2.5 text-[14px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
              style={inputStyle}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-[12px] text-[#8a8780] font-medium">Organisation <span className="text-[#b5b2ac]">(optionnel)</span></label>
            <input
              type="text"
              placeholder="ex. Financement immobilier"
              value={cmdOrg}
              onChange={e => setCmdOrg(e.target.value)}
              className="w-full rounded-[10px] px-4 py-2.5 text-[14px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
              style={inputStyle}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-[12px] text-[#8a8780] font-medium">Fin d&apos;évaluation</label>
            <select
              value={cmdFin}
              onChange={e => setCmdFin(e.target.value)}
              className="w-full rounded-[10px] px-4 py-2.5 text-[14px] text-[#1a1916] outline-none"
              style={selectStyle}
            >
              {FIN_EVAL_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div className="flex gap-2 mt-1">
            <button
              type="button"
              onClick={() => { setError(''); setFormStep(1) }}
              className="flex-1 rounded-[10px] py-2.5 text-[14px] font-medium text-[#8a8780] transition-opacity hover:opacity-90 active:opacity-80"
              style={{ background: 'var(--input-bg)', border: '1px solid var(--input-border)' }}
            >
              ← Retour
            </button>
            <button
              type="submit"
              className="flex-[2] rounded-[10px] py-2.5 text-[14px] font-medium text-white transition-opacity hover:opacity-90 active:opacity-80"
              style={{ background: '#334155' }}
            >
              Suivant →
            </button>
          </div>
        </form>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-3">
            {comparables.map(comp => (
              <div
                key={comp.id}
                className="rounded-[10px] overflow-hidden"
                style={{ border: '1px solid var(--input-border)' }}
              >
                <button
                  type="button"
                  onClick={() => setExpandedId(expandedId === comp.id ? null : comp.id)}
                  className="w-full flex items-center justify-between px-4 py-2.5 text-left"
                  style={{ background: 'var(--input-bg)' }}
                >
                  <span className="text-[13px] text-[#1a1916] truncate">
                    {comp.adresse || 'Comparable sans adresse'}{comp.prix_vente > 0 ? ` · ${comp.prix_vente.toLocaleString('fr-CA')} $` : ''}
                  </span>
                  <span className="text-[11px] text-[#8a8780] ml-2 shrink-0">{expandedId === comp.id ? '▲' : '▼'}</span>
                </button>

                {expandedId === comp.id && (
                  <div className="flex flex-col gap-3 px-4 pb-4 pt-3" style={{ background: 'var(--input-bg)', borderTop: '1px solid var(--input-border)' }}>
                    <div className="flex flex-col gap-1.5">
                      <label className="text-[11px] text-[#8a8780] font-medium">Adresse</label>
                      <input type="text" value={comp.adresse} onChange={e => updateComp(comp.id, 'adresse', e.target.value)}
                        className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
                        style={inputStyle} placeholder="123 rue Example, Montréal" />
                    </div>

                    <div className="flex gap-3">
                      <div className="flex flex-col gap-1.5 flex-1">
                        <label className="text-[11px] text-[#8a8780] font-medium">Date de vente</label>
                        <input type="date" value={comp.date_vente} onChange={e => updateComp(comp.id, 'date_vente', e.target.value)}
                          className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none"
                          style={inputStyle} />
                      </div>
                      <div className="flex flex-col gap-1.5 flex-1">
                        <label className="text-[11px] text-[#8a8780] font-medium">Prix de vente ($)</label>
                        <input type="number" min="0" value={comp.prix_vente || ''} onChange={e => updateComp(comp.id, 'prix_vente', parseFloat(e.target.value) || 0)}
                          className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none"
                          style={inputStyle} placeholder="450000" />
                      </div>
                    </div>

                    <div className="flex gap-3">
                      <div className="flex flex-col gap-1.5 flex-1">
                        <label className="text-[11px] text-[#8a8780] font-medium">
                          Source ID <span className="text-[#b5b2ac]">(traçabilité OEAQ)</span>
                        </label>
                        <input type="text" value={comp.source_id} onChange={e => updateComp(comp.id, 'source_id', e.target.value)}
                          className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
                          style={inputStyle} placeholder="CENTRIS-12345678" />
                      </div>
                      <div className="flex flex-col gap-1.5 flex-1">
                        <label className="text-[11px] text-[#8a8780] font-medium">Source</label>
                        <select value={comp.source_type} onChange={e => updateComp(comp.id, 'source_type', e.target.value as ComparableInput['source_type'])}
                          className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none"
                          style={selectStyle}>
                          <option value="mls_centris">Centris / MLS</option>
                          <option value="registre_foncier">Registre foncier</option>
                          <option value="dlc">DLC</option>
                          <option value="autre">Autre</option>
                        </select>
                      </div>
                    </div>

                    <div className="flex gap-3">
                      <div className="flex flex-col gap-1.5 flex-1">
                        <label className="text-[11px] text-[#8a8780] font-medium">Type de propriété</label>
                        <input type="text" value={comp.type_propriete} onChange={e => updateComp(comp.id, 'type_propriete', e.target.value)}
                          className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
                          style={inputStyle} placeholder="Unifamiliale" />
                      </div>
                      <div className="flex flex-col gap-1.5 flex-1">
                        <label className="text-[11px] text-[#8a8780] font-medium">Conditions de vente</label>
                        <select value={comp.conditions_vente} onChange={e => updateComp(comp.id, 'conditions_vente', e.target.value as ComparableInput['conditions_vente'])}
                          className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none"
                          style={selectStyle}>
                          <option value="normale">Normale</option>
                          <option value="liee">Liée</option>
                          <option value="autre">Autre</option>
                        </select>
                      </div>
                    </div>

                    <div className="flex gap-3">
                      <div className="flex flex-col gap-1.5 flex-1">
                        <label className="text-[11px] text-[#8a8780] font-medium">Superficie hab. (m²)</label>
                        <input type="number" min="0" value={comp.surface_hab ?? ''} onChange={e => updateComp(comp.id, 'surface_hab', e.target.value ? parseFloat(e.target.value) : null)}
                          className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none"
                          style={inputStyle} placeholder="145" />
                      </div>
                      <div className="flex flex-col gap-1.5 flex-1">
                        <label className="text-[11px] text-[#8a8780] font-medium">Superficie terrain (m²)</label>
                        <input type="number" min="0" value={comp.surface_terrain ?? ''} onChange={e => updateComp(comp.id, 'surface_terrain', e.target.value ? parseFloat(e.target.value) : null)}
                          className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none"
                          style={inputStyle} placeholder="350" />
                      </div>
                    </div>

                    <div className="flex gap-3">
                      <div className="flex flex-col gap-1.5 flex-1">
                        <label className="text-[11px] text-[#8a8780] font-medium">Année construction</label>
                        <input type="number" min="1800" max="2099" value={comp.annee_construction ?? ''} onChange={e => updateComp(comp.id, 'annee_construction', e.target.value ? parseInt(e.target.value) : null)}
                          className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none"
                          style={inputStyle} placeholder="1985" />
                      </div>
                      <div className="flex flex-col gap-1.5 flex-1">
                        <label className="text-[11px] text-[#8a8780] font-medium">Nb logements <span className="text-[#b5b2ac]">(opt.)</span></label>
                        <input type="number" min="1" value={comp.nb_logements ?? ''} onChange={e => updateComp(comp.id, 'nb_logements', e.target.value ? parseInt(e.target.value) : null)}
                          className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none"
                          style={inputStyle} placeholder="1" />
                      </div>
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <label className="text-[11px] text-[#8a8780] font-medium">Notes</label>
                      <input type="text" value={comp.notes} onChange={e => updateComp(comp.id, 'notes', e.target.value)}
                        className="w-full rounded-[8px] px-3 py-2 text-[13px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
                        style={inputStyle} placeholder="Particularités, ajustements prévus…" />
                    </div>

                    <button
                      type="button"
                      onClick={() => removeComp(comp.id)}
                      className="text-[12px] text-red-400 hover:text-red-600 text-left transition-colors"
                    >
                      Supprimer ce comparable
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>

          <button
            type="button"
            onClick={addComparable}
            className="w-full rounded-[10px] py-2.5 text-[14px] font-medium text-[#334155] transition-opacity hover:opacity-80"
            style={{ background: 'var(--input-bg)', border: '1px dashed var(--input-border)' }}
          >
            + Ajouter un comparable
          </button>

          {comparables.length === 0 && (
            <div className="rounded-[8px] px-3 py-2.5 text-[12px] text-[#8a8780]" style={{ background: 'var(--input-bg)', border: '1px solid var(--input-border)' }}>
              Aucun comparable — le rapport sera marqué <strong>A_REVOIR</strong> (CONF002). Vous pouvez continuer et corriger après.
            </div>
          )}

          <div className="flex gap-2 mt-1">
            <button
              type="button"
              onClick={() => { setError(''); setFormStep(2) }}
              className="flex-1 rounded-[10px] py-2.5 text-[14px] font-medium text-[#8a8780] transition-opacity hover:opacity-90 active:opacity-80"
              style={{ background: 'var(--input-bg)', border: '1px solid var(--input-border)' }}
            >
              ← Retour
            </button>
            <button
              type="submit"
              className="flex-[2] rounded-[10px] py-2.5 text-[14px] font-medium text-white transition-opacity hover:opacity-90 active:opacity-80"
              style={{ background: '#334155' }}
            >
              Lancer l&apos;évaluation
            </button>
          </div>
        </form>
      )}
    </div>
  )
}

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

  if (items.length === 0) return null

  return (
    <div className="mt-3 mb-1">
      <div className="text-[11px] uppercase tracking-widest text-[#8a8780] mb-2">Localisation</div>
      <div className="flex flex-col divide-y divide-[rgba(0,0,0,.06)] rounded-xl overflow-hidden bg-[rgba(0,0,0,.03)] dark:bg-[rgba(255,255,255,.04)]">
        {items.map(item => (
          <div key={item.label} className="flex items-start justify-between px-3 py-2 gap-4">
            <span className="text-[12px] text-[#6a6763] dark:text-[#9a9790] flex-shrink-0">{item.label}</span>
            <span className={`text-[12px] text-right ${item.warn ? 'text-amber-600 dark:text-amber-400 font-medium' : 'text-[#1a1916] dark:text-white'}`}>
              {item.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function DossierPanel({ isNew, dossierId, onPipelineComplete }: Props) {
  const [chips, setChips] = useState<FactChip[]>([])
  const [documents, setDocuments] = useState<Document[]>([])
  const [showDropZone, setShowDropZone] = useState(false)
  const [loading, setLoading] = useState(true)
  const [replies, setReplies] = useState<AssistantReply[]>([])
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

  const [isRunning, setIsRunning] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)

  const {
    steps: pipelineSteps,
    workflowStatus: liveStatus,
    error: pipelineError,
  } = usePipelinePolling(dossierId, isRunning)

  useEffect(() => {
    if (!dossierId) return
    setLoading(true)
    Promise.all([
      fetchDocuments(dossierId),
      fetchPropertyFacts(dossierId),
      fetchAppState(dossierId),
      fetchRuntimeEnrichment(dossierId),
    ]).then(([docs, facts, appState, enrichment]) => {
      setDocuments(docs)
      setChips(facts)
      setMandat(appState.active?.mandat ?? null)
      setConflitData(appState.active?.conflit ?? null)
      setLocalisation(enrichment?.localisation ?? null)
      setLoading(false)
      // Démarrer le polling uniquement si le pipeline tourne encore
      if (!isNew) {
        const status = (appState.active?.workflow.status as string | null) ?? ''
        const existingSteps = (appState.active?.workflow.steps ?? []) as PipelineStep[]
        const allDone = existingSteps.length > 0 && existingSteps.every(s => s.complete)
        if (!PIPELINE_TERMINAL_STATUSES.has(status) && !allDone) {
          setIsRunning(true)
        }
      }
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dossierId, refreshKey])

  useEffect(() => {
    if (!isRunning) return
    const allDone = pipelineSteps.length > 0 && pipelineSteps.every(s => s.complete)
    if (PIPELINE_TERMINAL_STATUSES.has(liveStatus) || allDone) {
      setIsRunning(false)
      onPipelineComplete?.()
      setRefreshKey(k => k + 1)
    }
  }, [liveStatus, pipelineSteps, isRunning, onPipelineComplete])

  async function handleDrop(files: FileList) {
    if (!dossierId) return
    const fileArray = Array.from(files)
    setUploads(fileArray.map(f => ({ name: f.name, state: 'uploading' as const })))
    setShowDropZone(false)

    const results = await Promise.allSettled(fileArray.map(f => uploadDocument(dossierId, f)))

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

  async function handleAsk(value: string) {
    if (!dossierId) return
    const response = await sendRuntimeMessage(dossierId, value, 'data-facts')
    setReplies(prev => [
      ...prev,
      {
        id: `${Date.now()}`,
        agent: response.message.agent_label,
        answer: response.message.answer,
      },
    ])
  }

  if (!isNew && (!dossierId || loading)) return <PanelLoader />

  if (isNew && !dossierId) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 px-6 pb-9">
        <NewDossierForm />
      </div>
    )
  }

  if (showDropZone) {
    return (
      <div className="flex flex-col items-center justify-end flex-1 px-6 pb-9">
        <DropZone onDrop={handleDrop} />
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center justify-end flex-1 px-6 pb-9">
      <div className="w-full max-w-[640px] flex flex-col gap-0 mb-5 flex-1 overflow-y-auto pt-5 scroll-fade">
        {isRunning && (
          <PipelineProgress
            steps={pipelineSteps}
            workflowStatus={liveStatus}
            error={pipelineError}
          />
        )}
        {conflit?.detecte && (
          <AgentMessage agentName="Agent Mandat">
            <div className="rounded-[8px] px-3 py-2 text-[12px] text-red-700 bg-red-50/80 border border-red-200/60">
              {'Conflit d\u2019int\u00e9r\u00eats d\u00e9tect\u00e9\u00a0\u2014 pipeline arr\u00eat\u00e9'}
              {conflit.motif && <div className="mt-1 opacity-80">{conflit.motif}</div>}
            </div>
          </AgentMessage>
        )}
        {chips.length > 0 && (
          <AgentMessage agentName="Agent Dossier">
            {'J\u2019ai charg\u00e9 les faits produits par le backend runtime.'}
            <div className="flex flex-wrap gap-1.5 mt-2.5">
              {chips.map((c, i) => <Chip key={i} label={c.label} highlight={c.highlight} />)}
            </div>
            {localisation && <LocalisationContexte loc={localisation} />}
          </AgentMessage>
        )}
        {mandat && (
          <AgentMessage agentName="Agent Mandat">
            {'Plan de mandat'}
            <div className="flex flex-wrap gap-1.5 mt-2.5">
              <Chip label={`Mandat\u00a0: ${mandat.mandat_type.replace(/_/g, '\u00a0')}`} highlight />
              <Chip label={`Format\u00a0: ${mandat.format_rapport.replace(/_/g, '\u00a0')}`} highlight />
              {mandat.methodes_requises.map((m, i) => (
                <Chip key={i} label={m.replace(/_/g, '\u00a0')} />
              ))}
            </div>
          </AgentMessage>
        )}
        {documents.length > 0 && <UserMessage>{'Sources rattach\u00e9es au dossier'}</UserMessage>}
        <AgentMessage agentName="Agent Dossier" last={replies.length === 0}>
          {documents.length === 0
            ? "Aucune source runtime n\u2019est encore rattach\u00e9e."
            : "Ces sources viennent des art\u00e9facts runtime. Elles restent \u00e0 valider avant toute conclusion professionnelle."}
          {documents.length > 0 && (
            <div className="flex flex-col gap-1.5 mt-2.5">
              {documents.map(doc => <DocItem key={doc.id} doc={doc} />)}
            </div>
          )}
          <button
            onClick={() => setShowDropZone(true)}
            className="mt-3 text-[12px] text-[#8a8780] hover:text-[#1a1916] underline underline-offset-2 bg-transparent border-none cursor-pointer font-sans"
          >
            + Ajouter un fichier local
          </button>
        </AgentMessage>
        {uploads.map((u, i) => (
          u.state === 'uploading' ? (
            <div key={i} className="text-[12px] text-[#8a8780] px-1 py-0.5 animate-pulse">
              {'\u2026 '}{u.name}
            </div>
          ) : (
            <div key={i} className="rounded-[8px] px-3 py-2 text-[12px] text-red-700 bg-red-50/80 border border-red-200/60">
              {u.name}{' — '}{u.error}
            </div>
          )
        ))}
        {replies.map((reply, index) => (
          <AgentMessage key={reply.id} agentName={reply.agent} last={index === replies.length - 1}>
            <pre className="whitespace-pre-wrap font-sans text-[13px] leading-6">{reply.answer}</pre>
          </AgentMessage>
        ))}
      </div>
      <ChatInput placeholder="Questionner l'Agent Dossier..." onSend={handleAsk} />
    </div>
  )
}
