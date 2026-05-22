'use client'

import { useEffect, useState, useCallback } from 'react'
import {
  fetchCheckpointFacts,
  confirmCheckpoint,
  resumeCheckpoint,
  type IntakeFacts,
  type IntakeField,
} from '@/lib/runtime-api'

interface Props {
  dossierId: string
  checkpoint: number
  onConfirmed: () => void
}

function FieldRow({ field }: { field: IntakeField }) {
  const baseCls = 'grid grid-cols-[1fr_1fr] gap-x-4 px-3 py-2 text-sm border-b border-white/5 last:border-0'
  const missingCls = field.missing ? 'bg-orange-500/5' : ''

  return (
    <div className={`${baseCls} ${missingCls}`}>
      <span className="text-foreground/70 flex items-center gap-1">
        {field.required && field.missing && (
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-orange-400 shrink-0" title="Champ requis" />
        )}
        {field.label}
      </span>
      <span className="text-right">
        {field.missing ? (
          <span className="inline-flex items-center gap-1 text-orange-400 font-medium text-xs">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden>
              <circle cx="6" cy="6" r="5" stroke="currentColor" strokeWidth="1.5" />
              <line x1="6" y1="3.5" x2="6" y2="6.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              <circle cx="6" cy="8.5" r="0.75" fill="currentColor" />
            </svg>
            À compléter
          </span>
        ) : (
          <span className="text-foreground">{field.value}</span>
        )}
      </span>
    </div>
  )
}

const CP_LABELS: Record<number, string> = {
  1: 'Faits du bien sujet',
  2: 'Comparables',
  3: 'Réconciliation',
  4: 'Rapport final',
}

export default function CheckpointReviewPanel({ dossierId, checkpoint, onConfirmed }: Props) {
  const [facts, setFacts] = useState<IntakeFacts | null>(null)
  const [loading, setLoading] = useState(true)
  const [confirming, setConfirming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [ingestionError, setIngestionError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetchCheckpointFacts(dossierId)
      .then(setFacts)
      .catch(e => {
        const msg = e instanceof Error ? e.message : String(e)
        if (msg.toLowerCase().includes('extraction') || msg.toLowerCase().includes('pdf')) {
          setIngestionError(msg)
        } else {
          setError(msg)
        }
      })
      .finally(() => setLoading(false))
  }, [dossierId])

  const handleConfirm = useCallback(async () => {
    if (!facts) return
    setConfirming(true)
    setError(null)
    try {
      await confirmCheckpoint(dossierId, checkpoint)
      if (checkpoint < 4) {
        await resumeCheckpoint(dossierId, checkpoint + 1)
      }
      onConfirmed()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setConfirming(false)
    }
  }, [dossierId, checkpoint, facts, onConfirmed])

  const label = CP_LABELS[checkpoint] ?? `Checkpoint ${checkpoint}`

  return (
    <div className="flex flex-col gap-4 p-6 max-w-2xl mx-auto">

      {/* Header */}
      <div className="flex items-center gap-3">
        <span className="flex items-center justify-center w-8 h-8 rounded-full bg-amber-500/15 text-amber-400 font-bold text-sm shrink-0">
          {checkpoint}
        </span>
        <div>
          <p className="text-xs text-foreground/50 uppercase tracking-wider">Confirmation requise</p>
          <h2 className="font-semibold text-foreground">{label}</h2>
        </div>
      </div>

      {/* Ingestion error banner */}
      {ingestionError && (
        <div className="flex items-start gap-3 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="shrink-0 mt-0.5" aria-hidden>
            <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
            <line x1="8" y1="4.5" x2="8" y2="9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            <circle cx="8" cy="11.5" r="1" fill="currentColor" />
          </svg>
          <span>{ingestionError}</span>
        </div>
      )}

      {/* General error */}
      {error && (
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="py-8 text-center text-foreground/40 text-sm animate-pulse">
          Chargement des faits extraits…
        </div>
      )}

      {/* Fields table */}
      {!loading && facts && (
        <>
          <div className="rounded-xl border border-white/8 overflow-hidden bg-white/2">
            <div className="grid grid-cols-[1fr_1fr] gap-x-4 px-3 py-2 text-xs font-medium text-foreground/40 uppercase tracking-wider border-b border-white/8">
              <span>Champ</span>
              <span className="text-right">Valeur extraite</span>
            </div>
            {facts.fields.map(f => <FieldRow key={f.key} field={f} />)}
          </div>

          {/* Summary */}
          <div className="flex items-center justify-between text-sm text-foreground/60">
            <span>
              {facts.missing_count > 0
                ? `${facts.missing_count} champ${facts.missing_count > 1 ? 's' : ''} manquant${facts.missing_count > 1 ? 's' : ''}`
                : 'Tous les champs sont renseignés'}
            </span>
            {facts.required_missing.length > 0 && (
              <span className="text-orange-400 text-xs">
                {facts.required_missing.length} requis manquant{facts.required_missing.length > 1 ? 's' : ''}
              </span>
            )}
          </div>

          {/* Required missing list */}
          {facts.required_missing.length > 0 && (
            <div className="p-3 rounded-lg bg-orange-500/8 border border-orange-500/15 text-orange-300 text-xs">
              <p className="font-medium mb-1">Champs requis manquants :</p>
              <ul className="list-disc list-inside space-y-0.5">
                {facts.required_missing.map(label => (
                  <li key={label}>{label}</li>
                ))}
              </ul>
              <p className="mt-2 text-orange-400/70">
                Vous pouvez confirmer et compléter ces informations dans la fiche dossier.
              </p>
            </div>
          )}

          {/* Confirm button */}
          <button
            onClick={handleConfirm}
            disabled={confirming}
            className={[
              'w-full py-3 px-4 rounded-xl font-semibold text-sm transition-all',
              confirming
                ? 'bg-white/5 text-foreground/30 cursor-not-allowed'
                : 'bg-amber-500 hover:bg-amber-400 text-white active:scale-[0.98]',
            ].join(' ')}
          >
            {confirming
              ? 'Confirmation en cours…'
              : `Confirmer — ${label}`}
          </button>

          <p className="text-center text-xs text-foreground/30">
            En confirmant, vous attestez avoir vérifié les faits ci-dessus.
            Cette action est horodatée et rattachée à votre compte.
          </p>
        </>
      )}
    </div>
  )
}
