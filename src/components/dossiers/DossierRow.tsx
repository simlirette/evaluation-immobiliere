'use client'

import type { Dossier, DossierStatus } from '@/types'
import { formatRelativeDate } from '@/lib/format-date'

const STATUS_META: Record<DossierStatus, { label: string; cls: string }> = {
  'en-cours': { label: 'En cours',  cls: 'encours' },
  complet:    { label: 'Complet',   cls: 'complet' },
  brouillon:  { label: 'Brouillon', cls: 'brouillon' },
}

interface Props {
  dossier: Dossier
  onClick: () => void
}

export default function DossierRow({ dossier, onClick }: Props) {
  const meta = STATUS_META[dossier.status]
  return (
    <div
      role="row"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && onClick()}
      className="grid items-center gap-4 px-5 py-3.5 cursor-pointer transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[var(--navy)]"
      style={{
        gridTemplateColumns: '2fr 140px 100px 80px 1fr 140px',
        borderTop: '1px solid var(--rule-soft)',
      }}
      onMouseEnter={e => (e.currentTarget.style.background = 'var(--paper-2)')}
      onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
    >
      {/* Address */}
      <div>
        <div className="text-[15px] font-medium" style={{ fontFamily: 'var(--font-serif)', color: 'var(--ink)' }}>
          {dossier.address}
        </div>
        {dossier.neighborhood && (
          <div className="text-[12px]" style={{ color: 'var(--ink-faint)' }}>{dossier.neighborhood}</div>
        )}
      </div>
      {/* Type */}
      <div className="text-[13px]" style={{ color: 'var(--ink-3)', fontStyle: 'italic', fontFamily: 'var(--font-serif)' }}>
        {dossier.property_type}
      </div>
      {/* Status */}
      <div><span className={`status-chip ${meta.cls}`}>{meta.label}</span></div>
      {/* Stage */}
      <div className="text-[13px]" style={{ color: 'var(--ink-mute)', fontVariantNumeric: 'tabular-nums' }}>1/5</div>
      {/* Client */}
      <div className="text-[13px] truncate" style={{ color: 'var(--ink-3)' }}>—</div>
      {/* Modified */}
      <div className="text-[12px] text-right" style={{ color: 'var(--ink-faint)' }}>
        {formatRelativeDate(dossier.updatedAt)}
      </div>
    </div>
  )
}
