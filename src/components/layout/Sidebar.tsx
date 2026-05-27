'use client'

import { useState, useEffect, useCallback } from 'react'
import SidebarWordmark from './SidebarWordmark'
import SidebarNav from './SidebarNav'
import SidebarRecent from './SidebarRecent'
import SidebarFooter from './SidebarFooter'
import ContextMenu from './ContextMenu'
import Toast from '@/components/shared/Toast'
import { useContextMenu } from '@/hooks/useContextMenu'
import { fetchRuntimeDossiers, deleteRuntimeDossier, renameRuntimeDossier, toggleRuntimePin, createRuntimeDossier } from '@/lib/runtime-api'
import type { Dossier, TabId } from '@/types'

interface Props {
  activeDossierId: string | null
  activeTab: TabId
  showMesDossiers: boolean
  currentDossierName: string
  refreshKey?: number
  onTabChange: (tab: TabId) => void
  onDossierSelect: (id: string, name: string) => void
  onNewDossier: () => void
  onMesDossiers: () => void
  onSignOut: () => void
}

export default function Sidebar({
  activeDossierId, activeTab, showMesDossiers,
  currentDossierName, refreshKey, onTabChange, onDossierSelect,
  onNewDossier, onMesDossiers, onSignOut,
}: Props) {
  const [dossiers, setDossiers] = useState<Dossier[]>([])
  const [loadError, setLoadError] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [toast, setToast] = useState<string | null>(null)
  const dismissToast = useCallback(() => setToast(null), [])
  const ctx = useContextMenu()

  useEffect(() => {
    setLoadError(false)
    fetchRuntimeDossiers().then(d => { setDossiers(d); setLoadError(false) }).catch(() => setLoadError(true))
  }, [refreshKey])

  // Close drawer when viewport reaches desktop width
  useEffect(() => {
    function onResize() { if (window.innerWidth >= 768) setMobileOpen(false) }
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  function handlePin(name: string, pinned: boolean) {
    const dossier = dossiers.find(d => d.address === name)
    if (!dossier) return
    setDossiers(prev => prev.map(d =>
      d.address === name ? { ...d, pinned: !pinned } : d
    ))
    toggleRuntimePin(dossier.slug, pinned)
    setToast(pinned ? 'Dossier désépinglé' : 'Dossier épinglé')
  }

  async function handleDuplicate(name: string) {
    const dossier = dossiers.find(d => d.address === name)
    if (!dossier) return
    setToast('Duplication en cours…')
    try {
      const newDossier = await createRuntimeDossier({
        address: `Copie de ${dossier.address}`,
        property_type: dossier.property_type,
        neighborhood: dossier.neighborhood,
      })
      setDossiers(prev => [newDossier, ...prev])
      setToast('Dossier dupliqué')
      onDossierSelect(newDossier.slug, newDossier.address)
    } catch {
      setToast('Erreur lors de la duplication')
    }
  }

  function handleRename(name: string, newName: string) {
    const dossier = dossiers.find(d => d.address === name)
    if (!dossier) return
    setDossiers(prev => prev.map(d => d.address === name ? { ...d, address: newName } : d))
    renameRuntimeDossier(dossier.slug, newName)
    setToast('Dossier renommé')
  }

  function handleDelete(name: string) {
    const dossier = dossiers.find(d => d.address === name)
    if (!dossier) return
    setDossiers(prev => prev.filter(d => d.address !== name))
    deleteRuntimeDossier(dossier.slug)
    setToast('Dossier supprimé')
  }

  const glassStyle = {
    backdropFilter: 'var(--glass-blur)',
    WebkitBackdropFilter: 'var(--glass-blur)',
    border: '1px solid var(--glass-border)',
    boxShadow: 'var(--glass-shadow), var(--glass-inset)',
  }

  return (
    <>
      {/* Hamburger button — mobile only, hidden when drawer is open */}
      <button
        className={`md:hidden fixed top-4 left-4 z-[210] w-9 h-9 rounded-full flex items-center justify-center sidebar-glass text-[#8a8780] cursor-pointer transition-colors hover:text-[#1a1916] border-none ${mobileOpen ? 'hidden' : ''}`}
        style={glassStyle}
        onClick={() => setMobileOpen(true)}
        aria-label="Ouvrir la navigation"
      >
        <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16"/>
        </svg>
      </button>

      {/* Backdrop — mobile only */}
      {mobileOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/40 z-[199]"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      <aside
        className="sidebar sidebar-glass fixed top-0 bottom-0 w-[240px] z-[200] flex flex-col pt-12 pb-5 rounded-r-[18px]"
        style={{ left: mobileOpen ? '0' : '-240px', transition: 'left 300ms cubic-bezier(0.4,0,0.2,1)' }}
        aria-label="Navigation principale"
      >
        {/* Close button — mobile only */}
        <button
          className="md:hidden absolute top-3 right-3 w-7 h-7 flex items-center justify-center text-[#8a8780] hover:text-[#1a1916] bg-transparent border-none cursor-pointer rounded-[6px] hover:bg-black/[.05] transition-colors"
          onClick={() => setMobileOpen(false)}
          aria-label="Fermer la navigation"
        >
          <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>

        <SidebarWordmark />

        <div
          role="button"
          tabIndex={0}
          className="mx-3 mb-0 px-3 py-2 rounded-lg flex items-center gap-2 text-[13px] text-[#8a8780] cursor-pointer hover:bg-black/[.03] dark:hover:bg-white/[.03] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#334155]"
          onClick={() => { onNewDossier(); setMobileOpen(false) }}
          onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && (onNewDossier(), setMobileOpen(false))}
        >
          <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4"/>
          </svg>
          Nouveau dossier
        </div>

        <div
          role="button"
          tabIndex={0}
          className={`mx-3 mb-[18px] px-3 py-2 rounded-lg flex items-center gap-2 text-[13px] cursor-pointer hover:bg-black/[.03] dark:hover:bg-white/[.03] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#334155] ${showMesDossiers ? 'text-[#1a1916] dark:text-[#e8e5e0] bg-black/[.05] dark:bg-white/[.05]' : 'text-[#8a8780]'}`}
          onClick={() => { onMesDossiers(); setMobileOpen(false) }}
          onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && (onMesDossiers(), setMobileOpen(false))}
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
          onTabChange={tab => { onTabChange(tab); setMobileOpen(false) }}
        />

        {loadError ? (
          <div className="px-4 py-3 flex flex-col gap-1.5">
            <p className="text-[11px] text-[#b5b2ac]">Erreur de chargement</p>
            <button
              onClick={() => { setLoadError(false); fetchRuntimeDossiers().then(d => { setDossiers(d) }).catch(() => setLoadError(true)) }}
              className="text-left text-[11px] text-[#334155] underline underline-offset-2 bg-transparent border-none cursor-pointer"
            >
              Réessayer
            </button>
          </div>
        ) : (
          <SidebarRecent
            dossiers={dossiers}
            activeDossierId={activeDossierId}
            onSelect={(id, name) => { onDossierSelect(id, name); setMobileOpen(false) }}
            onContextMenu={(e, name, pinned) => ctx.open(e, name, pinned)}
          />
        )}

        <SidebarFooter onSignOut={onSignOut} />
      </aside>

      <ContextMenu
        target={ctx.target}
        onClose={ctx.close}
        onPin={handlePin}
        onRename={handleRename}
        onDuplicate={handleDuplicate}
        onDelete={handleDelete}
      />

      <Toast message={toast} onDismiss={dismissToast} />
    </>
  )
}
