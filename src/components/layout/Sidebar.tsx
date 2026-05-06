'use client'

import { useState, useEffect } from 'react'
import SidebarWordmark from './SidebarWordmark'
import SidebarNav from './SidebarNav'
import SidebarRecent from './SidebarRecent'
import SidebarFooter from './SidebarFooter'
import ContextMenu from './ContextMenu'
import { useContextMenu } from '@/hooks/useContextMenu'
import { fetchDossiers } from '@/lib/supabase/queries/dossiers'
import { togglePin } from '@/lib/supabase/queries/pins'
import type { Dossier, TabId } from '@/types'

interface Props {
  activeDossierId: string | null
  activeTab: TabId
  showMesDossiers: boolean
  currentDossierName: string
  onTabChange: (tab: TabId) => void
  onDossierSelect: (id: string, name: string) => void
  onNewDossier: () => void
  onMesDossiers: () => void
  onSignOut: () => void
}

export default function Sidebar({
  activeDossierId, activeTab, showMesDossiers,
  currentDossierName, onTabChange, onDossierSelect,
  onNewDossier, onMesDossiers, onSignOut,
}: Props) {
  const [dossiers, setDossiers] = useState<Dossier[]>([])
  const ctx = useContextMenu()

  useEffect(() => {
    fetchDossiers().then(setDossiers)
  }, [])

  function handlePin(name: string, pinned: boolean) {
    const dossier = dossiers.find(d => d.address === name)
    if (!dossier) return
    setDossiers(prev => prev.map(d =>
      d.address === name ? { ...d, pinned: !pinned } : d
    ))
    togglePin(dossier.id, pinned)
  }

  function handleDelete(name: string) {
    setDossiers(prev => prev.filter(d => d.address !== name))
  }

  return (
    <>
      <aside
        className="absolute left-3 top-3 bottom-3 w-[200px] z-20 flex flex-col pt-7 pb-5 rounded-[18px] border transition-[background] duration-300"
        style={{
          background: 'linear-gradient(165deg, rgba(238,232,222,.75) 0%, rgba(228,222,212,.65) 55%, rgba(218,212,200,.60) 100%)',
          backdropFilter: 'var(--glass-blur)',
          WebkitBackdropFilter: 'var(--glass-blur)',
          border: '1px solid var(--glass-border)',
          boxShadow: 'var(--shadow-glass)',
        }}
      >
        <SidebarWordmark />

        <div
          className="mx-3 mb-0 px-3 py-2 rounded-lg flex items-center gap-2 text-[13px] text-[#8a8780] cursor-pointer hover:bg-black/[.03] transition-colors"
          onClick={onNewDossier}
        >
          <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4"/>
          </svg>
          Nouveau dossier
        </div>

        <div
          className={`mx-3 mb-[18px] px-3 py-2 rounded-lg flex items-center gap-2 text-[13px] cursor-pointer hover:bg-black/[.03] transition-colors ${showMesDossiers ? 'text-[#1a1916] bg-black/[.05]' : 'text-[#8a8780]'}`}
          onClick={onMesDossiers}
        >
          <svg width="13" height="13" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V7z"/>
          </svg>
          Mes dossiers
        </div>

        {!showMesDossiers && (
          <div className="px-6 pb-2.5">
            <div className="text-[11px] text-[#b5b2ac] uppercase tracking-[.07em] font-medium truncate">
              {currentDossierName}
            </div>
          </div>
        )}

        <SidebarNav
          activeTab={activeTab}
          showMesDossiers={showMesDossiers}
          onTabChange={onTabChange}
        />

        <SidebarRecent
          dossiers={dossiers}
          activeDossierId={activeDossierId}
          onSelect={onDossierSelect}
          onContextMenu={(e, name, pinned) => ctx.open(e, name, pinned)}
        />

        <SidebarFooter onSignOut={onSignOut} />
      </aside>

      <ContextMenu
        target={ctx.target}
        onClose={ctx.close}
        onPin={handlePin}
        onDelete={handleDelete}
      />
    </>
  )
}
