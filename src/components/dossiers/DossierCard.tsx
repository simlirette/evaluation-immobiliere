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
  index?: number
}

export default function DossierCard({ dossier, onClick, onContextMenu, index = 0 }: Props) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && onClick()}
      aria-label={`Ouvrir le dossier ${dossier.address}`}
      className={`card-enter group relative rounded-[18px] px-[22px] pt-[22px] pb-[18px] cursor-pointer transition-[transform,box-shadow] duration-200 hover:-translate-y-[3px] border border-white/[.72] dark:border-white/[.08] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#334155] ${dossier.pinned ? 'card-pinned' : ''}`}
      style={{
        background: 'linear-gradient(165deg, rgba(248,244,238,.96) 0%, rgba(238,232,223,.90) 100%)',
        boxShadow: 'var(--shadow-card)',
        animationDelay: `${index * 55}ms`,
      }}
    >
      <div className="absolute top-3.5 right-3.5 flex items-center gap-1.5 z-10">
        {dossier.pinned && (
          <span className="text-[10px] font-medium px-2 py-0.5 rounded-full tracking-wide text-[#334155] bg-[rgba(51,65,85,.10)]">
            Épinglé
          </span>
        )}
        {onContextMenu && (
          <button
            className="w-[26px] h-[26px] rounded-[6px] flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/[.07] bg-transparent border-none cursor-pointer text-[#8a8780]"
            onClick={e => { e.stopPropagation(); onContextMenu(e) }}
            aria-label="Options du dossier"
          >
            <svg width="14" height="14" fill="currentColor" viewBox="0 0 24 24">
              <circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/>
            </svg>
          </button>
        )}
      </div>
      <div
        className="text-[18px] font-medium text-[#1a1916] dark:text-[#e8e5e0] mb-0.5 leading-[1.18] tracking-[.005em] pr-[60px]"
        style={{ fontFamily: 'var(--font-serif)' }}
      >
        {dossier.address}
      </div>
      <div
        className="text-[13px] text-[#8a8780] mb-4 leading-snug"
        style={{ fontFamily: 'var(--font-serif)', fontStyle: 'italic' }}
      >
        {dossier.property_type}
        {dossier.neighborhood && (
          <span className="text-[#b5b2ac]"> · {dossier.neighborhood}</span>
        )}
      </div>
      <div className="flex items-center justify-between">
        <span className="text-[11px] text-[#b5b2ac]">{formatRelativeDate(dossier.updatedAt)}</span>
        <span className={`text-[10px] font-medium px-[9px] py-[3px] rounded-full tracking-[.02em] ${statusStyles[dossier.status]}`}>
          {statusLabels[dossier.status]}
        </span>
      </div>
    </div>
  )
}
