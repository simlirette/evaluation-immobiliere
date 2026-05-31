# É.A. Workflow Frontend Gaps — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-optimized:subagent-driven-development (recommended) or superpowers-optimized:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the 6 É.A. workflow frontend gaps: checkpoint panel design tokens, lettre de mandat card, dossier shell state lift, SideCard live data, topbar buttons, and documents SideCard.

**Architecture:** All changes are confined to the existing dossier shell (`src/app/dossier/[id]/page.tsx`) and two panel components. The shell already calls `fetchRuntimeDossier` which internally calls `fetchAppState` (cached via `dedup`); we switch to calling `fetchAppState` directly to access commanditaire/mandat/documents data without an extra API round-trip. No new pages, no new routes.

**Tech Stack:** Next.js App Router, `'use client'`, paper design system CSS vars (`--ink`, `--navy`, `--ochre`, `--oxblood`, `--verdigris`, `--rule`, `--rule-soft`, `--paper-2`, `--paper-hi`, `--navy-tint`, `--r-*`), `.btn` utility classes from globals.css.

**Assumptions:**
- `AppState.active.commanditaire` and `AppState.active.mandat` are populated after pipeline starts — will show `—` for new dossiers before first pipeline run.
- `AppState.active.documents` array exists; its length is used as doc count.
- `navigator.clipboard` is available in modern browsers (HTTPS context only).
- `window.print()` triggers the browser print dialog — no custom print stylesheet required.

---

## File Structure

| File | Change |
|------|--------|
| `src/components/panels/CheckpointReviewPanel.tsx` | Replace all glass/amber Tailwind with paper inline styles + `.btn` classes |
| `src/components/panels/CheckpointComparablePanel.tsx` | Same paper token migration |
| `src/components/panels/DossierPanel.tsx` | Upgrade lettre de mandat from bare link to styled card |
| `src/app/dossier/[id]/page.tsx` | Add `DossierMeta` state, fetch AppState, wire SideCards + topbar metadata + topbar buttons |

---

### Task 1: Checkpoint Panel Design Token Migration

**Files:**
- Modify: `src/components/panels/CheckpointReviewPanel.tsx`
- Modify: `src/components/panels/CheckpointComparablePanel.tsx`

**Security flag:** `none`

**Does NOT cover:** Dark mode–specific overrides beyond what paper vars already handle natively; `AccentColor` CSS property for the checkbox in `CheckpointComparablePanel` (left as-is).

- [ ] **Step 1: Rewrite `CheckpointReviewPanel.tsx`**

Replace the entire file content:

```tsx
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
```

- [ ] **Step 2: Rewrite `CheckpointComparablePanel.tsx`**

Replace the entire file content:

```tsx
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
        className="flex flex-col items-center justify-center gap-2 rounded-[var(--r-md)] px-6 py-5 cursor-pointer transition-colors text-center"
        style={{
          border: uploading
            ? '2px dashed var(--ochre)'
            : '2px dashed var(--rule)',
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
                className="transition-colors"
                style={{ color: 'var(--ink-mute)', background: 'none', border: 'none', cursor: 'pointer' }}
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
```

- [ ] **Step 3: Verify TypeScript**

Run: `npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 4: Commit**

```bash
git add src/components/panels/CheckpointReviewPanel.tsx src/components/panels/CheckpointComparablePanel.tsx
git commit -m "design: migrate checkpoint panels to paper design tokens"
```

---

### Task 2: Lettre de Mandat Display Card in DossierPanel

**Files:**
- Modify: `src/components/panels/DossierPanel.tsx`

**Security flag:** `none`

**Does NOT cover:** Fetching live honoraires/date_livraison fields — these are not returned in AppState; only commanditaire.nom + fin_evaluation shown in the card.

- [ ] **Step 1: Locate and replace the lettre de mandat button block**

In `src/components/panels/DossierPanel.tsx`, find this block (around line 1063):

```tsx
          {dossierId && (
            <button
              onClick={async () => {
                setMandatDownloading(true)
                try { await downloadLettreMandat(dossierId) } finally { setMandatDownloading(false) }
              }}
              disabled={mandatDownloading}
              className="mt-1 text-[12px] text-[#8a8780] hover:text-[#1a1916] underline underline-offset-2 bg-transparent border-none cursor-pointer font-sans disabled:opacity-40"
            >
              {mandatDownloading ? 'Génération…' : '↓ Lettre de mandat (PDF)'}
            </button>
          )}
```

Replace with:

```tsx
          {dossierId && (
            <div
              className="mt-3 rounded-[var(--r-md)] px-4 py-3 flex items-center justify-between gap-4"
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
```

- [ ] **Step 2: Verify TypeScript**

Run: `npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 3: Commit**

```bash
git add src/components/panels/DossierPanel.tsx
git commit -m "feat: upgrade lettre de mandat to panel card with commanditaire summary"
```

---

### Task 3: Shell State Lift — SideCards + Topbar Metadata

**Files:**
- Modify: `src/app/dossier/[id]/page.tsx`

**Security flag:** `none`

**Does NOT cover:** superficie/annee fields — not available in `Dossier` type or AppState without parsing fact_chips. Shows property_type and neighborhood only.

- [ ] **Step 1: Add `DossierMeta` interface and state, update imports, rewrite data-fetch effect**

Open `src/app/dossier/[id]/page.tsx`. Make these changes:

**1a. Update import** — replace `fetchRuntimeDossier, fetchRuntimeEnrichment` with `fetchAppState, fetchRuntimeEnrichment`:

```tsx
import { fetchAppState, fetchRuntimeEnrichment } from '@/lib/runtime-api'
```

**1b. Add helper functions** — place after the imports, before the component:

```tsx
function formatPropertyType(pt: string): string {
  const map: Record<string, string> = {
    residentiel_unifamilial: 'Unifamiliale',
    condo: 'Condo',
    duplex: 'Duplex',
    triplex: 'Triplex',
    quadruplex: 'Quadruplex',
    commercial: 'Commercial',
    terrain: 'Terrain',
    autre: 'Autre',
  }
  return map[pt] ?? pt
}

function formatFinEval(fe: string): string {
  const map: Record<string, string> = {
    hypothecaire: 'Hypothécaire',
    succession: 'Succession',
    litige: 'Litige judiciaire',
    assurance: 'Valeur assurable',
    commercial: 'Investissement commercial',
    expropriation: 'Expropriation',
    autre: 'Autre',
  }
  return map[fe] ?? fe
}

function formatMandatType(mt: string): string {
  const map: Record<string, string> = {
    residentiel_standard: 'Résidentiel standard',
    residentiel_rural: 'Résidentiel rural',
    commercial: 'Commercial',
    multilogement: 'Multilogement',
    terrain: 'Terrain',
    industriel: 'Industriel',
    special: 'Propriété spéciale',
  }
  return map[mt] ?? mt
}

interface DossierMeta {
  propertyType: string
  neighborhood: string
  commanditaire: { nom: string; organisation: string; fin_evaluation: string } | null
  mandat: { mandat_type: string } | null
  docCount: number
}
```

**1c. Add state** — inside `DossierShellInner`, after the existing `useState` declarations:

```tsx
const [dossierMeta, setDossierMeta] = useState<DossierMeta | null>(null)
```

**1d. Replace the data-fetch `useEffect`** — find the current useEffect that calls `fetchRuntimeDossier`:

```tsx
  useEffect(() => {
    if (params.id === 'nouveau') return
    setActiveDossierId(params.id)
    fetchRuntimeDossier(params.id)
      .then(d => {
        if (d) {
          setCurrentDossierName(d.address)
          setDossierId(d.id)
        } else {
          router.push('/dossiers')
        }
      })
      .catch(() => router.push('/dossiers'))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id])
```

Replace with:

```tsx
  useEffect(() => {
    if (params.id === 'nouveau') return
    setActiveDossierId(params.id)
    fetchAppState(params.id)
      .then(app => {
        const d = app.active?.dossier
        if (d) {
          setCurrentDossierName(d.address)
          setDossierId(d.id)
          setDossierMeta({
            propertyType: d.property_type,
            neighborhood: d.neighborhood,
            commanditaire: app.active?.commanditaire ?? null,
            mandat: app.active?.mandat
              ? { mandat_type: app.active.mandat.mandat_type }
              : null,
            docCount: app.active?.documents?.length ?? 0,
          })
        } else {
          router.push('/dossiers')
        }
      })
      .catch(() => router.push('/dossiers'))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id])
```

- [ ] **Step 2: Update topbar subtitle**

Find the hardcoded subtitle (around line 109):

```tsx
              <div
                className="text-[13.5px] mt-1"
                style={{ color: 'var(--ink-mute)', fontFamily: 'var(--font-sans)' }}
              >
                Montréal · Résidentiel · 2024
              </div>
```

Replace with:

```tsx
              <div
                className="text-[13.5px] mt-1"
                style={{ color: 'var(--ink-mute)', fontFamily: 'var(--font-sans)' }}
              >
                {dossierMeta
                  ? `${dossierMeta.neighborhood} · ${formatPropertyType(dossierMeta.propertyType)}`
                  : '\u00a0'}
              </div>
```

- [ ] **Step 3: Update SideCard "Faits saillants"**

Find the SideCard with hardcoded facts (around line 170):

```tsx
              <SideCard
                title="Faits saillants"
                facts={[
                  { label: 'Adresse', value: dossierLabel },
                  { label: 'Type', value: 'Résidentiel' },
                  { label: 'Année', value: '2024' },
                  { label: 'Superficie', value: '—' },
                  { label: 'Stade', value: `${reportReady ? 5 : 1}/5` },
                ]}
              />
```

Replace with:

```tsx
              <SideCard
                title="Faits saillants"
                facts={[
                  { label: 'Adresse', value: dossierLabel },
                  { label: 'Type', value: dossierMeta ? formatPropertyType(dossierMeta.propertyType) : '—' },
                  { label: 'Quartier', value: dossierMeta?.neighborhood ?? '—' },
                  { label: 'Stade', value: `${reportReady ? 5 : 1}/5` },
                ]}
              />
```

- [ ] **Step 4: Update SideCard "Mandat & client"**

Find the SideCard (around line 178):

```tsx
              <SideCard title="Mandat & client">
                <p className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>—</p>
              </SideCard>
```

Replace with:

```tsx
              <SideCard title="Mandat & client">
                {dossierMeta?.commanditaire ? (
                  <div className="flex flex-col">
                    <div
                      className="flex items-baseline justify-between py-2.5"
                      style={{ borderBottom: '1px dashed var(--rule-soft)' }}
                    >
                      <span className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>Client</span>
                      <span className="text-[13px] font-medium text-right ml-3" style={{ color: 'var(--ink)' }}>
                        {dossierMeta.commanditaire.nom}
                      </span>
                    </div>
                    {dossierMeta.commanditaire.organisation && (
                      <div
                        className="flex items-baseline justify-between py-2.5"
                        style={{ borderBottom: '1px dashed var(--rule-soft)' }}
                      >
                        <span className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>Organisation</span>
                        <span className="text-[13px] font-medium text-right ml-3" style={{ color: 'var(--ink)' }}>
                          {dossierMeta.commanditaire.organisation}
                        </span>
                      </div>
                    )}
                    <div
                      className="flex items-baseline justify-between py-2.5"
                      style={{ borderBottom: dossierMeta.mandat ? '1px dashed var(--rule-soft)' : 'none' }}
                    >
                      <span className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>Mandat</span>
                      <span className="text-[13px] font-medium text-right ml-3" style={{ color: 'var(--ink)' }}>
                        {formatFinEval(dossierMeta.commanditaire.fin_evaluation)}
                      </span>
                    </div>
                    {dossierMeta.mandat && (
                      <div className="flex items-baseline justify-between py-2.5">
                        <span className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>Type</span>
                        <span className="text-[13px] font-medium text-right ml-3" style={{ color: 'var(--ink)' }}>
                          {formatMandatType(dossierMeta.mandat.mandat_type)}
                        </span>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>—</p>
                )}
              </SideCard>
```

- [ ] **Step 5: Verify TypeScript**

Run: `npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 6: Commit**

```bash
git add src/app/dossier/[id]/page.tsx
git commit -m "feat: lift AppState to dossier shell, wire SideCards and topbar with live data"
```

---

### Task 4: Topbar Action Buttons

**Files:**
- Modify: `src/app/dossier/[id]/page.tsx`

**Security flag:** `none`

**Does NOT cover:** Sharing via native share sheet on mobile (`navigator.share`) — clipboard fallback only.

- [ ] **Step 1: Replace the three placeholder topbar buttons**

Find this block in `src/app/dossier/[id]/page.tsx` (around line 113):

```tsx
            <div className="flex items-center gap-2 flex-shrink-0 pt-1">
              <button className="btn ghost btn-sm">Imprimer</button>
              <button className="btn secondary btn-sm">Partager</button>
              <button className="btn accent btn-sm">Reprendre</button>
            </div>
```

Replace with:

```tsx
            <div className="flex items-center gap-2 flex-shrink-0 pt-1">
              <button
                className="btn ghost btn-sm"
                onClick={() => window.print()}
              >
                Imprimer
              </button>
              <button
                className="btn secondary btn-sm"
                onClick={() => {
                  navigator.clipboard.writeText(window.location.href)
                    .then(() => setToast('Lien copié dans le presse-papiers'))
                    .catch(() => setToast('Impossible de copier le lien'))
                }}
              >
                Partager
              </button>
              <button
                className="btn accent btn-sm"
                onClick={() => setTab('dossier')}
              >
                Reprendre
              </button>
            </div>
```

- [ ] **Step 2: Verify TypeScript**

Run: `npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 3: Commit**

```bash
git add src/app/dossier/[id]/page.tsx
git commit -m "feat: wire topbar Imprimer/Partager/Reprendre buttons"
```

---

### Task 5: SideCard Documents — Count + Navigate

**Files:**
- Modify: `src/app/dossier/[id]/page.tsx`

**Security flag:** `none`

**Does NOT cover:** Refreshing docCount after a user uploads a document in DossierPanel — the count reflects the state at page load only. Full document management stays in DossierPanel.

- [ ] **Step 1: Replace the SideCard "Documents" hardcoded content**

Find (around line 184):

```tsx
              <SideCard title="Documents">
                <p className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>
                  Aucun document joint.
                </p>
              </SideCard>
```

Replace with:

```tsx
              <SideCard title="Documents">
                <div className="flex items-center justify-between">
                  <p className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>
                    {dossierMeta && dossierMeta.docCount > 0
                      ? `${dossierMeta.docCount} document${dossierMeta.docCount > 1 ? 's' : ''}`
                      : 'Aucun document joint'}
                  </p>
                  <button
                    className="btn ghost btn-sm"
                    onClick={() => setTab('dossier')}
                  >
                    {dossierMeta && dossierMeta.docCount > 0 ? 'Gérer' : '+ Ajouter'}
                  </button>
                </div>
              </SideCard>
```

- [ ] **Step 2: Verify build**

Run: `npx next build`
Expected: Build succeeds, 0 TypeScript errors, all routes compile

- [ ] **Step 3: Commit**

```bash
git add src/app/dossier/[id]/page.tsx
git commit -m "feat: SideCard Documents shows live count and navigate-to-dossier button"
```

---

## Self-Review

**Spec coverage:**
1. ✅ Checkpoint panels design tokens — Task 1 (full rewrite of both panels)
2. ✅ Lettre de mandat display — Task 2 (card with commanditaire info + `.btn.secondary` download)
3. ✅ SideCard Faits saillants — Task 3, Step 3
4. ✅ Topbar metadata — Task 3, Step 2
5. ✅ SideCard Mandat & client — Task 3, Step 4
6. ✅ Topbar buttons — Task 4
7. ✅ SideCard Documents — Task 5

**Placeholder scan:** None found.

**Type consistency:**
- `DossierMeta.commanditaire` matches `AppState.active.commanditaire` shape exactly
- `DossierMeta.mandat` uses `{ mandat_type: string }` — mapped from `app.active.mandat.mandat_type`
- `formatPropertyType`, `formatFinEval`, `formatMandatType` defined before first use
- `setTab` already defined in shell — used in Tasks 4 and 5

**Scope-reduction scan:** No scope reductions vs spec. "Aucun document joint" in Task 5 replaces hardcoded with live data. docCount refresh limitation explicitly documented in Does NOT cover.
