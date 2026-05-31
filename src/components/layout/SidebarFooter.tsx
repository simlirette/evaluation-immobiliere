'use client'

import { useState } from 'react'
import Link from 'next/link'

interface Props {
  onSignOut?: () => void
}

export default function SidebarFooter({ onSignOut }: Props) {
  const [popoverOpen, setPopoverOpen] = useState(false)

  function handleThemeToggle() {
    const html = document.documentElement
    const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark'
    html.setAttribute('data-theme', next)
    try { localStorage.setItem('evalimmo-theme', next) } catch { /* ignore */ }
  }

  return (
    <div className="mt-auto border-t border-[var(--rule-soft)] flex-shrink-0">
      {/* Theme toggle */}
      <div className="px-4 py-3 flex items-center justify-between">
        <span
          className="text-[12px]"
          style={{ color: 'var(--ink-faint)', fontFamily: 'var(--font-sans)' }}
        >
          Apparence
        </span>
        <button
          onClick={handleThemeToggle}
          className="text-[12px] px-3 py-1 rounded-[var(--r-pill)] border border-[var(--rule)] cursor-pointer transition-colors"
          style={{ color: 'var(--ink-mute)', fontFamily: 'var(--font-sans)', background: 'transparent' }}
          onMouseEnter={e => (e.currentTarget.style.background = 'var(--paper-2)')}
          onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
        >
          Changer
        </button>
      </div>

      {/* Firm card */}
      <div className="relative px-3 pb-3">
        <button
          onClick={() => setPopoverOpen(v => !v)}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-[var(--r-md)] transition-colors text-left cursor-pointer border-none"
          style={{ background: 'transparent' }}
          aria-expanded={popoverOpen}
          aria-haspopup="menu"
          onMouseEnter={e => (e.currentTarget.style.background = 'var(--paper-2)')}
          onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
        >
          <div
            className="w-8 h-8 rounded-[var(--r-md)] flex items-center justify-center flex-shrink-0 text-[13px] font-semibold text-white"
            style={{ background: 'var(--navy)', fontFamily: 'var(--font-sans)' }}
          >
            MT
          </div>
          <div className="min-w-0 flex-1">
            <div
              className="text-[13px] font-medium truncate"
              style={{ color: 'var(--ink)', fontFamily: 'var(--font-sans)' }}
            >
              Maxime Tremblay
            </div>
            <div
              className="text-[11px] truncate"
              style={{ color: 'var(--ink-faint)', fontFamily: 'var(--font-sans)' }}
            >
              É.A. — OEAQ 4218
            </div>
          </div>
          <svg
            width="14" height="14" viewBox="0 0 14 14" fill="none"
            aria-hidden="true"
            style={{
              color: 'var(--ink-faint)',
              flexShrink: 0,
              transform: popoverOpen ? 'rotate(180deg)' : '',
              transition: 'transform .15s',
            }}
          >
            <path d="M3 5l4 4 4-4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>

        {popoverOpen && (
          <div
            className="absolute bottom-full left-3 right-3 mb-1 rounded-[var(--r-lg)] border border-[var(--rule)] overflow-hidden"
            style={{ background: 'var(--paper-hi)', boxShadow: 'var(--shadow-float)' }}
            role="menu"
          >
            <Link
              href="/parametres"
              className="flex items-center gap-2.5 px-3 py-2.5 text-[13px] no-underline transition-colors"
              style={{ color: 'var(--ink-2)', fontFamily: 'var(--font-sans)', display: 'flex' }}
              role="menuitem"
              onClick={() => setPopoverOpen(false)}
              onMouseEnter={e => (e.currentTarget.style.background = 'var(--paper-2)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <circle cx="7" cy="7" r="2" stroke="currentColor" strokeWidth="1.4"/>
                <path d="M7 1v1.5M7 11.5V13M1 7h1.5M11.5 7H13" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
              </svg>
              Paramètres
            </Link>
            <Link
              href="/aide"
              className="flex items-center gap-2.5 px-3 py-2.5 text-[13px] no-underline transition-colors"
              style={{ color: 'var(--ink-2)', fontFamily: 'var(--font-sans)', display: 'flex' }}
              role="menuitem"
              onClick={() => setPopoverOpen(false)}
              onMouseEnter={e => (e.currentTarget.style.background = 'var(--paper-2)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="1.4"/>
                <path d="M7 10v-1M7 4.5c0-1 1.5-1 1.5 0 0 .8-.5 1.2-1 1.5-.5.3-.5.6-.5 1" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
              </svg>
              Aide
            </Link>
            <div className="border-t border-[var(--rule-soft)]" />
            <button
              onClick={() => { setPopoverOpen(false); onSignOut?.() }}
              className="w-full flex items-center gap-2.5 px-3 py-2.5 text-[13px] text-left cursor-pointer border-none transition-colors"
              style={{ color: 'var(--ink-mute)', fontFamily: 'var(--font-sans)', background: 'transparent' }}
              role="menuitem"
              onMouseEnter={e => (e.currentTarget.style.background = 'var(--paper-2)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <path d="M5 2H3a1 1 0 00-1 1v8a1 1 0 001 1h2M9 10l3-3-3-3M12 7H5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              Déconnexion
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
