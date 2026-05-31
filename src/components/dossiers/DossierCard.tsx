'use client'

import type { Dossier, DossierStatus } from '@/types'
import { formatRelativeDate } from '@/lib/format-date'
import StageBar from './StageBar'

const STATUS_META: Record<DossierStatus, { label: string; cls: string }> = {
  'en-cours': { label: 'En cours',  cls: 'encours' },
  complet:    { label: 'Complet',   cls: 'complet' },
  brouillon:  { label: 'Brouillon', cls: 'brouillon' },
}

interface Props {
  dossier: Dossier
  onClick: () => void
  onContextMenu?: (e: React.MouseEvent) => void
  index?: number
}

export default function DossierCard({ dossier, onClick, onContextMenu, index = 0 }: Props) {
  const meta = STATUS_META[dossier.status]
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && onClick()}
      aria-label={`Ouvrir le dossier ${dossier.address}`}
      className={`card-enter card-hover group relative rounded-[var(--r-lg)] cursor-pointer border border-[var(--rule)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--navy)] ${dossier.pinned ? 'card-pinned' : ''}`}
      style={{ background: 'var(--paper-hi)', animationDelay: `${index * 45}ms` }}
    >
      {/* Header */}
      <div className="px-5 pt-5 pb-3">
        <div className="flex items-start justify-between gap-2 mb-2">
          <span className={`status-chip ${meta.cls}`}>{meta.label}</span>
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {dossier.pinned && (
              <span
                className="text-[11px] font-medium px-2 py-0.5 rounded-[var(--r-pill)]"
                style={{ background: 'rgba(184,138,62,.12)', color: 'var(--ochre)' }}
              >
                Épinglé
              </span>
            )}
            {onContextMenu && (
              <button
                className="w-6 h-6 flex items-center justify-center rounded-[var(--r-sm)] hover:bg-[var(--paper-2)] transition-colors cursor-pointer bg-transparent border-none"
                onClick={e => { e.stopPropagation(); onContextMenu(e) }}
                aria-label="Options"
                style={{ color: 'var(--ink-mute)' }}
              >
                <svg width="14" height="14" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <circle cx="12" cy="5" r="1.5"/>
                  <circle cx="12" cy="12" r="1.5"/>
                  <circle cx="12" cy="19" r="1.5"/>
                </svg>
              </button>
            )}
          </div>
        </div>

        <div
          className="text-[19px] font-medium leading-[1.2] pr-2 mb-0.5"
          style={{ fontFamily: 'var(--font-serif)', letterSpacing: '-.005em', color: 'var(--ink)' }}
        >
          {dossier.address}
        </div>
        <div
          className="text-[13px]"
          style={{ color: 'var(--ink-mute)', fontStyle: 'italic', fontFamily: 'var(--font-serif)' }}
        >
          {dossier.property_type}
          {dossier.neighborhood && (
            <span style={{ color: 'var(--ink-faint)' }}> · {dossier.neighborhood}</span>
          )}
        </div>
      </div>

      {/* Stage bar */}
      <div className="px-5 pb-3">
        <StageBar stage={1} />
      </div>

      {/* Footer */}
      <div
        className="px-5 pb-4 flex items-center justify-between border-t pt-3"
        style={{ borderTopColor: 'var(--rule-soft)' }}
      >
        <span className="text-[12px] truncate mr-2" style={{ color: 'var(--ink-faint)', fontFamily: 'var(--font-sans)' }}>
          —
        </span>
        <span className="text-[11.5px] flex-shrink-0" style={{ color: 'var(--ink-faint)', fontFamily: 'var(--font-sans)' }}>
          Mod. {formatRelativeDate(dossier.updatedAt)}
        </span>
      </div>
    </div>
  )
}
