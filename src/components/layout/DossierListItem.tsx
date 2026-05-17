'use client'

import type { DossierStatus } from '@/types'

const STATUS_DOT: Record<DossierStatus, string> = {
  brouillon:  'bg-[#c4bfb8]',
  'en-cours': 'bg-[#334155]',
  complet:    'bg-[#1f7a5c]',
}

interface Props {
  name: string
  active: boolean
  status?: DossierStatus
  onSelect: () => void
  onContextMenu: (e: React.MouseEvent) => void
}

export default function DossierListItem({ name, active, status, onSelect, onContextMenu }: Props) {
  return (
    <div
      className={`group relative flex items-center px-3 py-1.5 text-xs rounded-[6px] cursor-pointer transition-[background,color] duration-150 ${
        active
          ? 'text-[#1a1916] dark:text-[#e8e5e0] bg-black/[.05] dark:bg-white/[.05]'
          : 'text-[#8a8780] hover:text-[#1a1916] dark:hover:text-[#e8e5e0] hover:bg-black/[.03] dark:hover:bg-white/[.03]'
      }`}
      onClick={onSelect}
    >
      {status && (
        <span className={`w-[5px] h-[5px] rounded-full flex-shrink-0 mr-2 ${STATUS_DOT[status]}`} />
      )}
      <span className="flex-1 min-w-0 truncate">{name}</span>
      <button
        className="w-[22px] h-[22px] rounded-[5px] flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/[.07] dark:hover:bg-white/[.07] bg-transparent border-none cursor-pointer"
        onClick={e => { e.stopPropagation(); onContextMenu(e) }}
      >
        <svg width="13" height="13" fill="currentColor" viewBox="0 0 24 24">
          <circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/>
        </svg>
      </button>
    </div>
  )
}
