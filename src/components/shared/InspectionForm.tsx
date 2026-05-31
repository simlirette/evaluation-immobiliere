'use client'

import { useState } from 'react'
import { saveRuntimeInspection, type InspectionData } from '@/lib/runtime-api'

interface Props {
  dossierId: string
  initial?: InspectionData | null
  onSaved?: (inspection: InspectionData) => void
}

const TYPE_LABELS: Record<InspectionData['type_inspection'], string> = {
  interieure_exterieure: 'Intérieure et extérieure',
  exterieure: 'Extérieure seulement',
  documentaire: 'Documentaire (sans visite physique)',
}

export default function InspectionForm({ dossierId, initial, onSaved }: Props) {
  const [dateVisite, setDateVisite] = useState(initial?.date_visite ?? '')
  const [typeInspection, setTypeInspection] = useState<InspectionData['type_inspection']>(
    initial?.type_inspection ?? 'interieure_exterieure'
  )
  const [etendue, setEtendue] = useState(initial?.etendue ?? '')
  const [observations, setObservations] = useState(initial?.observations ?? '')
  const [accesLimite, setAccesLimite] = useState(initial?.acces_limite ?? false)
  const [notesAcces, setNotesAcces] = useState(initial?.notes_acces ?? '')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isComplete = dateVisite.length > 0 && etendue.trim().length > 0

  async function handleSave() {
    if (!isComplete) return
    setSaving(true)
    setError(null)
    try {
      const result = await saveRuntimeInspection(dossierId, {
        date_visite: dateVisite,
        type_inspection: typeInspection,
        etendue: etendue.trim(),
        observations: observations.trim(),
        acces_limite: accesLimite,
        notes_acces: notesAcces.trim(),
      })
      setSaved(true)
      onSaved?.(result)
      setTimeout(() => setSaved(false), 3000)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex flex-col gap-3 p-4 rounded-[10px]"
      style={{ border: '1px solid var(--rule)', background: 'var(--paper-hi)' }}>

      <div className="flex items-center gap-2">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden
          className="flex-shrink-0" style={{ color: 'var(--ink-mute)' }}>
          <circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="1.5"/>
          <path d="M7 4v3l2 1.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
        <span className="text-[11px] uppercase tracking-widest" style={{ color: 'var(--ink-mute)' }}>
          Inspection — Élément 14 NPP
        </span>
      </div>

      {/* Date + type */}
      <div className="flex gap-2">
        <div className="flex flex-col gap-1 flex-1">
          <label className="text-[11px]" style={{ color: 'var(--ink-mute)' }}>Date de visite *</label>
          <input
            type="date"
            value={dateVisite}
            onChange={e => setDateVisite(e.target.value)}
            className="rounded-[6px] px-2.5 py-1.5 text-[12px] focus:outline-none focus:ring-1"
            style={{
              border: '1px solid var(--rule)',
              background: 'var(--paper)',
              color: 'var(--ink)',
              ['--tw-ring-color' as string]: 'var(--navy)',
            }}
          />
        </div>
        <div className="flex flex-col gap-1 flex-1">
          <label className="text-[11px]" style={{ color: 'var(--ink-mute)' }}>Type d'inspection</label>
          <select
            value={typeInspection}
            onChange={e => setTypeInspection(e.target.value as InspectionData['type_inspection'])}
            className="rounded-[6px] px-2.5 py-1.5 text-[12px] focus:outline-none focus:ring-1"
            style={{
              border: '1px solid var(--rule)',
              background: 'var(--paper)',
              color: 'var(--ink)',
            }}
          >
            {Object.entries(TYPE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Étendue */}
      <div className="flex flex-col gap-1">
        <label className="text-[11px]" style={{ color: 'var(--ink-mute)' }}>
          Étendue de l'inspection *
        </label>
        <input
          type="text"
          value={etendue}
          onChange={e => setEtendue(e.target.value)}
          placeholder="ex. Inspection complète intérieure et extérieure de toutes les pièces"
          className="rounded-[6px] px-2.5 py-1.5 text-[12px] focus:outline-none focus:ring-1"
          style={{
            border: '1px solid var(--rule)',
            background: 'var(--paper)',
            color: 'var(--ink)',
          }}
        />
      </div>

      {/* Observations */}
      <div className="flex flex-col gap-1">
        <label className="text-[11px]" style={{ color: 'var(--ink-mute)' }}>Observations</label>
        <textarea
          value={observations}
          onChange={e => setObservations(e.target.value)}
          placeholder="Observations principales : état général, anomalies notées, composantes vérifiées…"
          rows={3}
          className="rounded-[6px] px-2.5 py-1.5 text-[12px] resize-none focus:outline-none focus:ring-1"
          style={{
            border: '1px solid var(--rule)',
            background: 'var(--paper)',
            color: 'var(--ink)',
          }}
        />
      </div>

      {/* Accès limité */}
      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={accesLimite}
          onChange={e => setAccesLimite(e.target.checked)}
          className="w-3.5 h-3.5"
        />
        <span className="text-[12px]" style={{ color: 'var(--ink)' }}>Accès limité</span>
      </label>
      {accesLimite && (
        <input
          type="text"
          value={notesAcces}
          onChange={e => setNotesAcces(e.target.value)}
          placeholder="Préciser les limitations d'accès…"
          className="rounded-[6px] px-2.5 py-1.5 text-[12px] focus:outline-none focus:ring-1"
          style={{
            border: '1px solid var(--rule)',
            background: 'var(--paper)',
            color: 'var(--ink)',
          }}
        />
      )}

      {/* Error */}
      {error && (
        <p className="text-[12px]" style={{ color: 'var(--oxblood)' }}>{error}</p>
      )}

      {/* Save button */}
      <button
        onClick={handleSave}
        disabled={!isComplete || saving}
        className="btn accent disabled:opacity-40 text-[12px] py-1.5"
      >
        {saving ? 'Enregistrement…' : saved ? '✓ Enregistré' : 'Enregistrer l’inspection'}
      </button>
    </div>
  )
}
