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
  const color =
    score >= 0.75 ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20'
    : score >= 0.55 ? 'bg-amber-500/15 text-amber-400 border-amber-500/20'
    : 'bg-red-500/15 text-red-400 border-red-500/20'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${color}`}>
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
    <label className={[
      'flex items-start gap-3 px-3 py-3 rounded-xl border cursor-pointer transition-all',
      selected
        ? 'border-amber-500/40 bg-amber-500/5'
        : 'border-white/8 bg-white/2 hover:border-white/15',
    ].join(' ')}>
      <input
        type="checkbox"
        checked={selected}
        onChange={onToggle}
        className="mt-0.5 shrink-0 w-4 h-4 accent-amber-400"
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <span className="text-sm font-medium text-foreground truncate">{candidate.adresse}</span>
          <div className="flex items-center gap-2 shrink-0">
            <ScoreBadge score={candidate.score} />
          </div>
        </div>
        <div className="flex flex-wrap gap-x-4 gap-y-0.5 mt-1 text-xs text-foreground/50">
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
          <span className="text-foreground/30">{candidate.source_id}</span>
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
        <span className="flex items-center justify-center w-8 h-8 rounded-full bg-amber-500/15 text-amber-400 font-bold text-sm shrink-0">
          {checkpoint}
        </span>
        <div>
          <p className="text-xs text-foreground/50 uppercase tracking-wider">Confirmation requise</p>
          <h2 className="font-semibold text-foreground">Sélection des comparables</h2>
        </div>
      </div>

      {subjectAddress && (
        <div className="text-xs text-foreground/40">
          Bien sujet : <span className="text-foreground/70">{subjectAddress}</span>
        </div>
      )}

      {/* Upload zone */}
      <div
        onDrop={handleDrop}
        onDragOver={e => e.preventDefault()}
        onClick={() => inputRef.current?.click()}
        className={[
          'flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-6 py-5 cursor-pointer transition-colors text-center',
          uploading
            ? 'border-amber-500/40 bg-amber-500/5 cursor-wait'
            : 'border-white/10 hover:border-white/20 bg-white/2',
        ].join(' ')}
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
          <span className="text-sm text-amber-400 animate-pulse">Import en cours…</span>
        ) : (
          <>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="text-foreground/30" aria-hidden>
              <path d="M10 3v10M6 7l4-4 4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M3 15h14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            <span className="text-sm text-foreground/50">
              {candidates.length > 0
                ? 'Importer un autre export JLR (CSV)'
                : 'Importer l\'export CSV JLR'}
            </span>
            <span className="text-xs text-foreground/30">Glisser-déposer ou cliquer — CSV uniquement, max 5 Mo</span>
          </>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-3 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="shrink-0 mt-0.5" aria-hidden>
            <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5"/>
            <line x1="8" y1="4.5" x2="8" y2="9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            <circle cx="8" cy="11.5" r="1" fill="currentColor"/>
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="py-6 text-center text-foreground/40 text-sm animate-pulse">
          Chargement des comparables…
        </div>
      )}

      {/* Candidates list */}
      {!loading && candidates.length > 0 && (
        <>
          <div className="flex items-center justify-between text-xs text-foreground/40">
            <span>{candidates.length} comparable{candidates.length > 1 ? 's' : ''} proposé{candidates.length > 1 ? 's' : ''} — sélectionnez-en au moins {MIN_COMPARABLES}</span>
            {nSelected > 0 && (
              <button
                type="button"
                onClick={() => setSelectedIds(new Set())}
                className="text-foreground/40 hover:text-foreground/60 transition-colors"
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
          <div className="flex items-center justify-between text-sm">
            <span className={nSelected < MIN_COMPARABLES ? 'text-orange-400' : 'text-emerald-400'}>
              {nSelected} sélectionné{nSelected > 1 ? 's' : ''}
              {nSelected < MIN_COMPARABLES && ` — minimum ${MIN_COMPARABLES} requis (B007)`}
            </span>
          </div>

          {/* Confirm button */}
          <button
            onClick={handleConfirm}
            disabled={!canConfirm || confirming}
            className={[
              'w-full py-3 px-4 rounded-xl font-semibold text-sm transition-all',
              !canConfirm
                ? 'bg-white/5 text-foreground/30 cursor-not-allowed'
                : confirming
                  ? 'bg-white/5 text-foreground/30 cursor-not-allowed'
                  : 'bg-amber-500 hover:bg-amber-400 text-white active:scale-[0.98]',
            ].join(' ')}
          >
            {confirming
              ? 'Confirmation en cours…'
              : `Confirmer les comparables (${nSelected} sélectionné${nSelected > 1 ? 's' : ''})`}
          </button>

          <p className="text-center text-xs text-foreground/30">
            En confirmant, vous attestez avoir vérifié et retenu ces comparables.
            Cette action est horodatée et rattachée à votre compte.
          </p>
        </>
      )}

      {/* Empty state — no candidates yet */}
      {!loading && candidates.length === 0 && !error && (
        <div className="py-6 text-center text-foreground/40 text-sm">
          Importez un export CSV JLR pour afficher les comparables.
        </div>
      )}
    </div>
  )
}
