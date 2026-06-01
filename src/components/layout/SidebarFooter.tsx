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
      {/* Theme toggle — Clair / Sombre */}
      <div className="px-4 py-2.5 flex items-center justify-between gap-2">
        <span className="text-[11px] uppercase tracking-widest" style={{ color: 'var(--ink-faint)', fontFamily: 'var(--font-sans)' }}>
          Apparence
        </span>
        <div className="flex rounded-[var(--r-md)] overflow-hidden border border-[var(--rule)]">
          {(['light', 'dark'] as const).map(mode => {
            const html = typeof document !== 'undefined' ? document.documentElement : null
            const active = html ? html.getAttribute('data-theme') === mode : mode === 'light'
            return (
              <button
                key={mode}
                onClick={() => {
                  if (typeof document !== 'undefined') {
                    document.documentElement.setAttribute('data-theme', mode)
                    try { localStorage.setItem('evalimmo-theme', mode) } catch { /* ignore */ }
                  }
                }}
                className="text-[11px] px-2.5 py-1 cursor-pointer border-none transition-colors"
                style={{
                  fontFamily: 'var(--font-sans)',
                  background: active ? 'var(--ink)' : 'transparent',
                  color: active ? 'var(--paper-hi)' : 'var(--ink-mute)',
                }}
              >
                {mode === 'light' ? 'Clair' : 'Sombre'}
              </button>
            )
          })}
        </div>
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
              {/* Gear icon */}
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <circle cx="7" cy="7" r="2" stroke="currentColor" strokeWidth="1.3"/>
                <path d="M7 1.5A5.5 5.5 0 017 1a6 6 0 016 6h-.5M7 12.5A5.5 5.5 0 017 13a6 6 0 01-6-6h.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
                <path d="M5.5 1.8l-.5.87M9 11.3l-.5.87M1.8 8.5l.87.5M11.3 5l.87.5M1.8 5.5l.87-.5M11.3 9l.87-.5M5.5 12.2l-.5-.87M9 2.7l-.5-.87" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
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
              {/* ? icon */}
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <circle cx="7" cy="7" r="5.5" stroke="currentColor" strokeWidth="1.3"/>
                <path d="M5.5 5.5C5.5 4.4 6.1 3.8 7 3.8c.9 0 1.5.7 1.5 1.5 0 1-1 1.3-1.2 2.2" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
                <circle cx="7" cy="10" r=".7" fill="currentColor"/>
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
