'use client'

import { useState } from 'react'
import DossierListItem from './DossierListItem'
import type { Dossier, DossierStatus } from '@/types'

interface Props {
  dossiers: Dossier[]
  activeDossierId: string | null
  onSelect: (id: string, name: string) => void
  onContextMenu: (e: React.MouseEvent, name: string, pinned: boolean) => void
}

type FilterPill = 'all' | DossierStatus

const PILLS: { id: FilterPill; label: string }[] = [
  { id: 'all', label: 'Tous' },
  { id: 'en-cours', label: 'En cours' },
  { id: 'complet', label: 'Prêts' },
]

export default function SidebarRecent({ dossiers, activeDossierId, onSelect, onContextMenu }: Props) {
  const [expanded, setExpanded] = useState(false)
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<FilterPill>('all')

  const q = query.trim().toLowerCase()
  const byStatus = filter === 'all' ? dossiers : dossiers.filter(d => d.status === filter)
  const filtered = q ? byStatus.filter(d => d.address.toLowerCase().includes(q)) : byStatus

  const pinned = filtered.filter(d => d.pinned)
  const recents = filtered.filter(d => !d.pinned)
  const visible = expanded || q ? recents : recents.slice(0, 3)
  const hidden = q ? 0 : recents.length - 3

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {dossiers.length > 3 && (
        <div className="px-4 pb-2">
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Rechercher…"
            className="w-full rounded-[8px] px-2.5 py-1.5 text-[12px] text-[#1a1916] outline-none placeholder:text-[#b5b2ac]"
            style={{ background: 'var(--input-bg)', border: '1px solid var(--input-border)' }}
          />
        </div>
      )}
      <div className="px-4 pb-2 flex gap-1.5">
        {PILLS.map(p => (
          <button
            key={p.id}
            onClick={() => { setFilter(p.id); setExpanded(false) }}
            className="rounded-full px-2.5 py-0.5 text-[10px] font-medium transition-colors border"
            style={filter === p.id
              ? { background: 'var(--sidebar-active-bg, rgba(0,0,0,.09))', borderColor: 'transparent', color: '#1a1916' }
              : { background: 'transparent', borderColor: 'var(--input-border)', color: '#8a8780' }
            }
          >
            {p.label}
          </button>
        ))}
      </div>
      <div className="px-3 flex-1 overflow-y-auto scroll-fade">
        {pinned.length > 0 && (
          <>
            <div className="text-[10px] text-[#b5b2ac] uppercase tracking-[.07em] font-medium px-3 pb-1.5">{'\u00c9pingl\u00e9s'}</div>
            {pinned.map(d => (
              <DossierListItem
                key={d.id}
                name={d.address}
                active={d.slug === activeDossierId}
                status={d.status}
                onSelect={() => onSelect(d.slug, d.address)}
                onContextMenu={e => onContextMenu(e, d.address, true)}
              />
            ))}
          </>
        )}
        {(!q || recents.length > 0) && (
          <div className="text-[10px] text-[#b5b2ac] uppercase tracking-[.07em] font-medium px-3 pb-1.5 mt-2.5">{'R\u00e9cents'}</div>
        )}
        {visible.map(d => (
          <DossierListItem
            key={d.id}
            name={d.address}
            active={d.slug === activeDossierId}
            status={d.status}
            onSelect={() => onSelect(d.slug, d.address)}
            onContextMenu={e => onContextMenu(e, d.address, false)}
          />
        ))}
        {q && filtered.length === 0 && (
          <div className="px-3 py-2 text-[12px] text-[#b5b2ac]">Aucun résultat</div>
        )}
        {hidden > 0 && (
          <button
            className="flex items-center gap-1 px-3 py-1.5 text-[11px] text-[#b5b2ac] hover:text-[#8a8780] transition-colors bg-transparent border-none cursor-pointer font-sans"
            onClick={() => setExpanded(e => !e)}
          >
            {expanded ? '- Moins' : `+ ${hidden} autres`}
          </button>
        )}
      </div>
    </div>
  )
}
