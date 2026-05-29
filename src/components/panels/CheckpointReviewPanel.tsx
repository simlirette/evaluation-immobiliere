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
  return (
    <div
      className="grid grid-cols-[1fr_1fr] gap-x-4 px-3 py-2 text-[13px]"
      style={{
        borderBottom: '1px solid var(--rule-soft)',
        background: field.missing ? 'rgba(184,138,62,.05)' : 'transparent',
      }}
    >
      <span className="flex items-center gap-1.5" style={{ color: 'var(--ink-mute)' }}>
        {field.required && field.missing && (
          <span
            className="inline-block w-1.5 h-1.5 rounded-full flex-shrink-0"
            style={{ background: 'var(--ochre)' }}
            title="Champ requis"
          />
        )}
        {field.label}
      </span>
      <span className="text-right">
        {field.missing ? (
          <span
            className="inline-flex items-center gap-1 text-[12px] font-medium"
            style={{ color: 'var(--ochre)' }}
          >
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden>
              <circle cx="6" cy="6" r="5" stroke="currentColor" strokeWidth="1.5" />
              <line x1="6" y1="3.5" x2="6" y2="6.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              <circle cx="6" cy="8.5" r="0.75" fill="currentColor" />
            </svg>
            À compléter
          </span>
        ) : (
          <span style={{ color: 'var(--ink)' }}>{field.value}</span>
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
        <span
          className="flex items-center justify-center text-[14px] font-bold flex-shrink-0"
          style={{
            width: '2rem',
            height: '2rem',
            borderRadius: '50%',
            background: 'rgba(184,138,62,.12)',
            color: 'var(--ochre)',
          }}
        >
          {checkpoint}
        </span>
        <div>
          <div className="eyebrow">Confirmation requise</div>
          <h2 className="text-[16px] font-medium mt-0.5" style={{ color: 'var(--ink)' }}>{label}</h2>
        </div>
      </div>

      {/* Ingestion error banner */}
      {ingestionError && (
        <div
          className="flex items-start gap-3 p-3 rounded-[var(--r-md)] text-[13px]"
          style={{
            background: 'rgba(138,48,48,.08)',
            border: '1px solid rgba(138,48,48,.18)',
            color: 'var(--oxblood)',
          }}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="flex-shrink-0 mt-0.5" aria-hidden>
            <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
            <line x1="8" y1="4.5" x2="8" y2="9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            <circle cx="8" cy="11.5" r="1" fill="currentColor" />
          </svg>
          <span>{ingestionError}</span>
        </div>
      )}

      {/* General error */}
      {error && (
        <div
          className="p-3 rounded-[var(--r-md)] text-[13px]"
          style={{
            background: 'rgba(138,48,48,.08)',
            border: '1px solid rgba(138,48,48,.18)',
            color: 'var(--oxblood)',
          }}
        >
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="py-8 text-center text-[13px] animate-pulse" style={{ color: 'var(--ink-faint)' }}>
          Chargement des faits extraits…
        </div>
      )}

      {/* Fields table */}
      {!loading && facts && (
        <>
          <div
            className="rounded-[var(--r-md)] overflow-hidden"
            style={{ border: '1px solid var(--rule)', background: 'var(--paper-2)' }}
          >
            <div
              className="grid grid-cols-[1fr_1fr] gap-x-4 px-3 py-2 text-[11px] font-medium uppercase tracking-[.05em]"
              style={{
                color: 'var(--ink-faint)',
                background: 'var(--paper)',
                borderBottom: '1px solid var(--rule)',
              }}
            >
              <span>Champ</span>
              <span className="text-right">Valeur extraite</span>
            </div>
            {facts.fields.map(f => <FieldRow key={f.key} field={f} />)}
          </div>

          {/* Summary */}
          <div className="flex items-center justify-between text-[13px]" style={{ color: 'var(--ink-mute)' }}>
            <span>
              {facts.missing_count > 0
                ? `${facts.missing_count} champ${facts.missing_count > 1 ? 's' : ''} manquant${facts.missing_count > 1 ? 's' : ''}`
                : 'Tous les champs sont renseignés'}
            </span>
            {facts.required_missing.length > 0 && (
              <span className="text-[12px]" style={{ color: 'var(--ochre)' }}>
                {facts.required_missing.length} requis manquant{facts.required_missing.length > 1 ? 's' : ''}
              </span>
            )}
          </div>

          {/* Required missing list */}
          {facts.required_missing.length > 0 && (
            <div
              className="p-3 rounded-[var(--r-md)] text-[12px]"
              style={{
                background: 'rgba(184,138,62,.08)',
                border: '1px solid rgba(184,138,62,.18)',
                color: 'var(--ochre)',
              }}
            >
              <p className="font-medium mb-1">Champs requis manquants :</p>
              <ul className="list-disc list-inside space-y-0.5">
                {facts.required_missing.map(lbl => (
                  <li key={lbl}>{lbl}</li>
                ))}
              </ul>
              <p className="mt-2" style={{ color: 'var(--ink-mute)' }}>
                Vous pouvez confirmer et compléter ces informations dans la fiche dossier.
              </p>
            </div>
          )}

          {/* Confirm button */}
          <button
            onClick={handleConfirm}
            disabled={confirming}
            className="btn accent btn-full disabled:opacity-40"
          >
            {confirming ? 'Confirmation en cours…' : `Confirmer — ${label}`}
          </button>

          <p className="text-center text-[12px]" style={{ color: 'var(--ink-faint)' }}>
            En confirmant, vous attestez avoir vérifié les faits ci-dessus.
            Cette action est horodatée et rattachée à votre compte.
          </p>
        </>
      )}
    </div>
  )
}
