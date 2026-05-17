'use client'

import type { Dossier, DossierStatus } from '@/types'
import { formatRelativeDate } from '@/lib/format-date'

const statusStyles: Record<DossierStatus, string> = {
  'en-cours': 'bg-[rgba(51,65,85,.10)] text-[#334155]',
  complet: 'bg-[rgba(34,136,102,.10)] text-[#228866]',
  brouillon: 'bg-black/[.06] text-[#8a8780]',
}

const statusLabels: Record<DossierStatus, string> = {
  'en-cours': 'En cours',
  complet: 'Complet',
  brouillon: 'Brouillon',
}

interface Props {
  dossier: Dossier
  onClick: () => void
  onContextMenu?: (e: React.MouseEvent) => void
}

export default function DossierCard({ dossier, onClick, onContextMenu }: Props) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && onClick()}
      aria-label={`Ouvrir le dossier ${dossier.address}`}
      className="group relative rounded-[18px] px-[22px] pt-[22px] pb-[18px] cursor-pointer transition-[transform,box-shadow] duration-200 hover:-translate-y-[3px] border border-white/[.72] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#334155]"
      style={{
        background: 'linear-gradient(165deg, rgba(248,244,238,.96) 0%, rgba(238,232,223,.90) 100%)',
        boxShadow: 'var(--shadow-card)',
      }}
    >
      {onContextMenu && (
        <button
          className="absolute top-3.5 right-3.5 w-[26px] h-[26px] rounded-[6px] flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/[.07] bg-transparent border-none cursor-pointer text-[#8a8780] z-10"
          onClick={e => { e.stopPropagation(); onContextMenu(e) }}
          aria-label="Options du dossier"
        >
          <svg width="14" height="14" fill="currentColor" viewBox="0 0 24 24">
            <circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/>
          </svg>
        </button>
      )}
      <div
        className="text-[17px] font-medium text-[#1a1916] mb-1 leading-[1.2] tracking-[.01em] pr-7"
        style={{ fontFamily: 'var(--font-serif)' }}
      >
        {dossier.address}
      </div>
      <div className="text-xs text-[#8a8780] font-light mb-3.5">{dossier.property_type} - {dossier.neighborhood}</div>
      <div className="flex items-center justify-between">
        <span className="text-[11px] text-[#b5b2ac]">{formatRelativeDate(dossier.updatedAt)}</span>
        <span className={`text-[10px] font-medium px-[9px] py-[3px] rounded-full tracking-[.02em] ${statusStyles[dossier.status]}`}>
          {statusLabels[dossier.status]}
        </span>
      </div>
    </div>
  )
}
