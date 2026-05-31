'use client'

/**
 * CostInputForm — Saisie manuelle des coûts pour l'approche par le coût (T2.4/D2).
 * Permet à l'É.A. de fournir le coût unitaire réel (Altus, MEFQ, devis)
 * pour remplacer la valeur PROXY et produire une approche coût certifiable.
 */
import { useState } from 'react'
import { saveRuntimeFactOverrides } from '@/lib/runtime-api'

interface Props {
  dossierId: string
  initial?: { cout_unitaire_m2?: number; source_couts?: string } | null
  onSaved?: () => void
}

const SOURCES = [
  { value: 'altus_2025', label: 'Altus Group (2025)' },
  { value: 'mefq_2025', label: 'MEFQ 2025 (barème base)' },
  { value: 'devis_entrepreneur', label: 'Devis entrepreneur' },
  { value: 'comparable_cout', label: 'Comparable de coût' },
  { value: 'autre', label: 'Autre source (préciser)' },
]

export default function CostInputForm({ dossierId, initial, onSaved }: Props) {
  const [coutUnitaire, setCoutUnitaire] = useState(
    initial?.cout_unitaire_m2 ? String(initial.cout_unitaire_m2) : ''
  )
  const [source, setSource] = useState(initial?.source_couts ?? 'mefq_2025')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const cout = parseFloat(coutUnitaire)
  const valid = !isNaN(cout) && cout > 500 && cout < 20_000

  async function handleSave() {
    if (!valid) return
    setSaving(true)
    setError(null)
    try {
      // Injecter dans les fact overrides (accessibles au pipeline)
      await saveRuntimeFactOverrides(dossierId, {
        cout_unitaire_m2: cout,
        source_couts: source,
      } as Parameters<typeof saveRuntimeFactOverrides>[1] & { cout_unitaire_m2?: number; source_couts?: string })
      setSaved(true)
      onSaved?.()
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
        <span className="text-[11px] uppercase tracking-widest" style={{ color: 'var(--ink-mute)' }}>
          Coût de construction (approche coût)
        </span>
        {!initial?.cout_unitaire_m2 && (
          <span className="text-[10px] px-1.5 py-0.5 rounded"
            style={{ background: 'rgba(184,138,62,.12)', color: 'var(--ochre)' }}>
            PROXY actif
          </span>
        )}
      </div>

      <div className="flex gap-2">
        <div className="flex flex-col gap-1 flex-1">
          <label className="text-[11px]" style={{ color: 'var(--ink-mute)' }}>
            Coût unitaire ($/m²) *
          </label>
          <input
            type="number"
            value={coutUnitaire}
            onChange={e => setCoutUnitaire(e.target.value)}
            placeholder="ex. 2 800"
            min={500}
            max={20000}
            className="rounded-[6px] px-2.5 py-1.5 text-[12px] focus:outline-none focus:ring-1"
            style={{ border: '1px solid var(--rule)', background: 'var(--paper)', color: 'var(--ink)' }}
          />
          {coutUnitaire && !valid && (
            <span className="text-[11px]" style={{ color: 'var(--oxblood)' }}>
              Valeur hors plage (500–20 000 $/m²)
            </span>
          )}
        </div>
        <div className="flex flex-col gap-1 flex-1">
          <label className="text-[11px]" style={{ color: 'var(--ink-mute)' }}>Source</label>
          <select
            value={source}
            onChange={e => setSource(e.target.value)}
            className="rounded-[6px] px-2.5 py-1.5 text-[12px] focus:outline-none"
            style={{ border: '1px solid var(--rule)', background: 'var(--paper)', color: 'var(--ink)' }}
          >
            {SOURCES.map(s => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>
      </div>

      {error && <p className="text-[12px]" style={{ color: 'var(--oxblood)' }}>{error}</p>}

      <button
        onClick={handleSave}
        disabled={!valid || saving}
        className="btn accent disabled:opacity-40 text-[12px] py-1.5"
      >
        {saving ? 'Enregistrement…' : saved ? '✓ Coût enregistré' : 'Enregistrer le coût'}
      </button>
    </div>
  )
}
