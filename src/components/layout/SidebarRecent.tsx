'use client'

import { useState } from 'react'
import DossierListItem from './DossierListItem'
import type { Dossier } from '@/types'

interface Props {
  dossiers: Dossier[]
  activeDossierId: string | null
  onSelect: (id: string, name: string) => void
  onContextMenu: (e: React.MouseEvent, name: string, pinned: boolean) => void
}

export default function SidebarRecent({ dossiers, activeDossierId, onSelect, onContextMenu }: Props) {
  const [expanded, setExpanded] = useState(false)

  const pinned  = dossiers.filter(d => d.pinned)
  const recents = dossiers.filter(d => !d.pinned)
  const visible = expanded ? recents : recents.slice(0, 3)
  const hidden  = recents.length - 3

  return (
    <div className="px-3 flex-1 overflow-y-auto scroll-fade">
      {pinned.length > 0 && (
        <>
          <div className="text-[10px] text-[#b5b2ac] uppercase tracking-[.07em] font-medium px-3 pb-1.5">Épinglés</div>
          {pinned.map(d => (
            <DossierListItem
              key={d.id}
              name={d.address}
              active={d.id === activeDossierId}
              onSelect={() => onSelect(d.id, d.address)}
              onContextMenu={e => onContextMenu(e, d.address, true)}
            />
          ))}
        </>
      )}
      <div className="text-[10px] text-[#b5b2ac] uppercase tracking-[.07em] font-medium px-3 pb-1.5 mt-2.5">Récents</div>
      {visible.map(d => (
        <DossierListItem
          key={d.id}
          name={d.address}
          active={d.id === activeDossierId}
          onSelect={() => onSelect(d.id, d.address)}
          onContextMenu={e => onContextMenu(e, d.address, false)}
        />
      ))}
      {hidden > 0 && (
        <button
          className="flex items-center gap-1 px-3 py-1.5 text-[11px] text-[#b5b2ac] hover:text-[#8a8780] transition-colors bg-transparent border-none cursor-pointer font-sans"
          onClick={() => setExpanded(e => !e)}
        >
          {expanded ? '− Moins' : `+ ${hidden} autres`}
        </button>
      )}
    </div>
  )
}
