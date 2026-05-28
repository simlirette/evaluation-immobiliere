'use client'

import { useState, useEffect } from 'react'
import SidebarWordmark from './SidebarWordmark'
import SidebarNav from './SidebarNav'
import SidebarFooter from './SidebarFooter'
import SidebarToggle from './SidebarToggle'

interface Props {
  onSignOut?: () => void
  currentDossierAddress?: string | null
}

export default function Sidebar({ onSignOut, currentDossierAddress }: Props) {
  const [open, setOpen] = useState(true)

  // Restore preference
  useEffect(() => {
    try {
      const saved = localStorage.getItem('sidebar-open')
      if (saved !== null) setOpen(saved === 'true')
    } catch { /* ignore */ }
  }, [])

  function toggle() {
    setOpen(v => {
      const next = !v
      try { localStorage.setItem('sidebar-open', String(next)) } catch { /* ignore */ }
      return next
    })
  }

  return (
    <>
      <nav
        className={`sidebar ${open ? 'open' : ''}`}
        aria-label="Navigation principale"
      >
        <SidebarWordmark />

        {/* Current dossier block (dossier detail only) */}
        {currentDossierAddress && (
          <div className="mx-3 my-2 px-3 py-2 rounded-[var(--r-md)] border border-[var(--rule-soft)] flex-shrink-0" style={{ background: 'var(--paper-2)' }}>
            <div className="eyebrow mb-1">Dossier ouvert</div>
            <div
              className="text-[14px] font-medium truncate"
              style={{ fontFamily: 'var(--font-serif)', color: 'var(--ink)' }}
            >
              {currentDossierAddress}
            </div>
          </div>
        )}

        <div className="flex-1 overflow-y-auto scroll-fade min-h-0">
          <div className="px-3 pt-3 pb-1">
            <span className="eyebrow">Travail</span>
          </div>
          <SidebarNav />
        </div>

        <SidebarFooter onSignOut={onSignOut} />
      </nav>

      <SidebarToggle open={open} onToggle={toggle} />
    </>
  )
}
