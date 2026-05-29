'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import {
  fetchComparableCandidates,
  uploadJlrCsv,
  confirmComparables,
  resumeCheckpoint,
  type ComparableCandidate,
} from '@/lib/runtime-api'
import { formatCAD } from '@/lib/format-number'

interface Props {
  dossierId: string
  checkpoint: number
  onConfirmed: () => void
}

const MIN_COMPARABLES = 3

function ScoreBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const style =
    score >= 0.75
      ? { background: 'rgba(74,107,84,.12)', color: 'var(--verdigris)', border: '1px solid rgba(74,107,84,.22)' }
      : score >= 0.55
      ? { background: 'rgba(184,138,62,.12)', color: 'var(--ochre)', border: '1px solid rgba(184,138,62,.22)' }
      : { background: 'rgba(138,48,48,.10)', color: 'var(--oxblood)', border: '1px solid rgba(138,48,48,.20)' }
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium"
      style={style}
    >
      {pct}%
    </span>
  )
}

function CandidateRow({
  candidate,
  selected,
  onToggle,
}: {
  candidate: ComparableCandidate
  selected: boolean
  onToggle: () => void
}) {
  return (
    <label
      className="flex items-start gap-3 px-3 py-3 rounded-[var(--r-md)] cursor-pointer transition-colors"
      style={{
        border: selected ? '1px solid var(--navy)' : '1px solid var(--rule)',
        background: selected ? 'var(--navy-tint)' : 'var(--paper-hi)',
      }}
    >
      <input
        type="checkbox"
        checked={selected}
        onChange={onToggle}
        className="mt-0.5 flex-shrink-0 w-4 h-4"
        style={{ accentColor: 'var(--navy)' }}
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <span className="text-[13px] font-medium truncate" style={{ color: 'var(--ink)' }}>
            {candidate.adresse}
          </span>
          <ScoreBadge score={candidate.score} />
        </div>
        <div
          className="flex flex-wrap gap-x-4 gap-y-0.5 mt-1 text-[12px]"
          style={{ color: 'var(--ink-mute)' }}
        >
          <span>{formatCAD(candidate.prix_vente)}</span>
          {candidate.date_vente && <span>{candidate.date_vente.slice(0, 10)}</span>}
          {candidate.surface_habitable != null && (
            <span>{Math.round(candidate.surface_habitable).toLocaleString('fr-CA')} pi²</span>
          )}
          {candidate.nb_chambres != null && <span>{candidate.nb_chambres} ch.</span>}
          {candidate.type_bien && <span className="capitalize">{candidate.type_bien}</span>}
          {candidate.distance_km != null && (
            <span>{candidate.distance_km.toFixed(1)} km</span>
          )}
          <span style={{ color: 'var(--ink-faint)' }}>{candidate.source_id}</span>
        </div>
      </div>
    </label>
  )
}

export default function CheckpointComparablePanel({ dossierId, checkpoint, onConfirmed }: Props) {
  const [candidates, setCandidates] = useState<ComparableCandidate[]>([])
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [subjectAddress, setSubjectAddress] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const loadCandidates = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetchComparableCandidates(dossierId)
      setCandidates(result.candidates)
      setSubjectAddress(result.subject_address)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }, [dossierId])

  useEffect(() => { loadCandidates() }, [loadCandidates])

  const handleFileChange = useCallback(async (file: File) => {
    setUploading(true)
    setError(null)
    try {
      const result = await uploadJlrCsv(dossierId, file)
      setCandidates(result.candidates)
      setSelectedIds(new Set())
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setUploading(false)
    }
  }, [dossierId])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0]
    if (file) handleFileChange(file)
  }, [handleFileChange])

  const toggleId = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const handleConfirm = useCallback(async () => {
    if (selectedIds.size < MIN_COMPARABLES) return
    setConfirming(true)
    setError(null)
    try {
      await confirmComparables(dossierId, Array.from(selectedIds), checkpoint)
      if (checkpoint < 4) {
        await resumeCheckpoint(dossierId, checkpoint + 1)
      }
      onConfirmed()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setConfirming(false)
    }
  }, [dossierId, checkpoint, selectedIds, onConfirmed])

  const nSelected = selectedIds.size
  const canConfirm = nSelected >= MIN_COMPARABLES

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
          <h2 className="text-[16px] font-medium mt-0.5" style={{ color: 'var(--ink)' }}>
            Sélection des comparables
          </h2>
        </div>
      </div>

      {subjectAddress && (
        <div className="text-[12px]" style={{ color: 'var(--ink-mute)' }}>
          Bien sujet : <span style={{ color: 'var(--ink)' }}>{subjectAddress}</span>
        </div>
      )}

      {/* Upload zone */}
      <div
        onDrop={handleDrop}
        onDragOver={e => e.preventDefault()}
        onClick={() => inputRef.current?.click()}
        className="flex flex-col items-center justify-center gap-2 rounded-[var(--r-md)] px-6 py-5 transition-colors text-center"
        style={{
          border: uploading ? '2px dashed var(--ochre)' : '2px dashed var(--rule)',
          background: uploading ? 'rgba(184,138,62,.05)' : 'var(--paper-2)',
          cursor: uploading ? 'wait' : 'pointer',
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={e => {
            const f = e.target.files?.[0]
            if (f) handleFileChange(f)
            e.target.value = ''
          }}
        />
        {uploading ? (
          <span className="text-[13px] animate-pulse" style={{ color: 'var(--ochre)' }}>
            Import en cours…
          </span>
        ) : (
          <>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden
              style={{ color: 'var(--ink-faint)' }}>
              <path d="M10 3v10M6 7l4-4 4 4" stroke="currentColor" strokeWidth="1.5"
                strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M3 15h14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            <span className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>
              {candidates.length > 0
                ? 'Importer un autre export JLR (CSV)'
                : "Importer l'export CSV JLR"}
            </span>
            <span className="text-[12px]" style={{ color: 'var(--ink-faint)' }}>
              Glisser-déposer ou cliquer — CSV uniquement, max 5 Mo
            </span>
          </>
        )}
      </div>

      {/* Error */}
      {error && (
        <div
          className="flex items-start gap-3 p-3 rounded-[var(--r-md)] text-[13px]"
          style={{
            background: 'rgba(138,48,48,.08)',
            border: '1px solid rgba(138,48,48,.18)',
            color: 'var(--oxblood)',
          }}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"
            className="flex-shrink-0 mt-0.5" aria-hidden>
            <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5"/>
            <line x1="8" y1="4.5" x2="8" y2="9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            <circle cx="8" cy="11.5" r="1" fill="currentColor"/>
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="py-6 text-center text-[13px] animate-pulse" style={{ color: 'var(--ink-faint)' }}>
          Chargement des comparables…
        </div>
      )}

      {/* Candidates list */}
      {!loading && candidates.length > 0 && (
        <>
          <div className="flex items-center justify-between text-[12px]" style={{ color: 'var(--ink-mute)' }}>
            <span>
              {candidates.length} comparable{candidates.length > 1 ? 's' : ''} proposé
              {candidates.length > 1 ? 's' : ''} — sélectionnez-en au moins {MIN_COMPARABLES}
            </span>
            {nSelected > 0 && (
              <button
                type="button"
                onClick={() => setSelectedIds(new Set())}
                style={{ color: 'var(--ink-mute)', background: 'none', border: 'none', cursor: 'pointer', fontSize: '12px' }}
                onMouseEnter={e => (e.currentTarget.style.color = 'var(--ink)')}
                onMouseLeave={e => (e.currentTarget.style.color = 'var(--ink-mute)')}
              >
                Tout désélectionner
              </button>
            )}
          </div>

          <div className="flex flex-col gap-2">
            {candidates.map(c => (
              <CandidateRow
                key={c.id}
                candidate={c}
                selected={selectedIds.has(c.id)}
                onToggle={() => toggleId(c.id)}
              />
            ))}
          </div>

          {/* Selection summary */}
          <div className="flex items-center text-[13px]">
            <span style={{ color: nSelected < MIN_COMPARABLES ? 'var(--ochre)' : 'var(--verdigris)' }}>
              {nSelected} sélectionné{nSelected > 1 ? 's' : ''}
              {nSelected < MIN_COMPARABLES && ` — minimum ${MIN_COMPARABLES} requis (B007)`}
            </span>
          </div>

          {/* Confirm button */}
          <button
            onClick={handleConfirm}
            disabled={!canConfirm || confirming}
            className="btn accent btn-full disabled:opacity-40"
          >
            {confirming
              ? 'Confirmation en cours…'
              : `Confirmer les comparables (${nSelected} sélectionné${nSelected > 1 ? 's' : ''})`}
          </button>

          <p className="text-center text-[12px]" style={{ color: 'var(--ink-faint)' }}>
            En confirmant, vous attestez avoir vérifié et retenu ces comparables.
            Cette action est horodatée et rattachée à votre compte.
          </p>
        </>
      )}

      {/* Empty state */}
      {!loading && candidates.length === 0 && !error && (
        <div className="py-6 text-center text-[13px]" style={{ color: 'var(--ink-mute)' }}>
          Importez un export CSV JLR pour afficher les comparables.
        </div>
      )}
    </div>
  )
}
