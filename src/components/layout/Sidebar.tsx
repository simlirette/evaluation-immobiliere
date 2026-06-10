'use client'

/* Sidebar — anatomie 1:1 du design handoff (components.jsx → Sidebar).
   Données réelles : dossiers runtime (compte, épinglés, récents) + profil É.A. */

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Icon } from '@/components/shared/Icon'
import { fetchRuntimeDossiers, fetchEvaluateurProfile, type EvaluateurProfile } from '@/lib/runtime-api'
import { VENTES } from '@/data/bibliotheque-mock'
import { MODELES } from '@/data/modeles-mock'
import { ARCHIVES } from '@/data/archives-mock'
import type { Dossier } from '@/types'

type Theme = 'light' | 'dark'

interface Props {
  onSignOut?: () => void
  currentDossierAddress?: string | null
  currentDossierId?: string | null
  currentDossierCity?: string | null
}

function getTheme(): Theme {
  if (typeof document === 'undefined') return 'light'
  return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light'
}

function initials(name: string): string {
  const parts = name.trim().split(/\s+/)
  return ((parts[0]?.[0] ?? '') + (parts[parts.length - 1]?.[0] ?? '')).toUpperCase() || 'ÉA'
}

export default function Sidebar({ onSignOut, currentDossierAddress, currentDossierId, currentDossierCity }: Props) {
  const pathname = usePathname()
  const [menuOpen, setMenuOpen] = useState(false)
  const [theme, setThemeState] = useState<Theme>('light')
  const [dossiers, setDossiers] = useState<Dossier[]>([])
  const [profile, setProfile] = useState<EvaluateurProfile | null>(null)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setThemeState(getTheme())
    fetchRuntimeDossiers().then(setDossiers).catch(() => undefined)
    fetchEvaluateurProfile().then(setProfile).catch(() => undefined)
  }, [])

  useEffect(() => {
    if (!menuOpen) return
    function onDoc(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [menuOpen])

  function pickTheme(t: Theme) {
    document.documentElement.setAttribute('data-theme', t)
    try { localStorage.setItem('evalimmo-theme', t) } catch { /* ignore */ }
    setThemeState(t)
  }

  function isActive(href: string) {
    if (href === '/dossier/nouveau') return pathname === '/dossier/nouveau'
    return pathname === href || pathname.startsWith(href + '/')
  }

  const pinned = dossiers.filter(d => d.pinned)
  const recents = dossiers.filter(d => !d.pinned).slice(0, 3)
  const name = profile?.nom_ea || 'Évaluateur agréé'
  const credential = profile?.no_permis_oeaq ? `OEAQ ${profile.no_permis_oeaq}` : 'OEAQ —'

  return (
    <aside className="sidebar no-select">
      <div className="brand">
        <div className="wordmark">Éval&nbsp;<em>Immo</em></div>
        <div className="tag">Évaluateurs agréés — Québec</div>
      </div>

      {currentDossierAddress && (
        <div
          className="current-dossier"
          title={currentDossierCity ? `${currentDossierAddress}, ${currentDossierCity}` : currentDossierAddress}
        >
          <div className="cd-addr">
            {currentDossierAddress}
            {currentDossierId && <span className="cd-id numeric">{currentDossierId}</span>}
          </div>
          {currentDossierCity && <div className="cd-city">{currentDossierCity}</div>}
        </div>
      )}

      <nav className="nav">
        <div className="nav-label">Travail</div>
        <Link className={isActive('/dossier/nouveau') ? 'active' : ''} href="/dossier/nouveau">
          <Icon.Plus/>
          <span>Nouveau dossier</span>
        </Link>
        <Link className={isActive('/dossiers') ? 'active' : ''} href="/dossiers">
          <Icon.Folder/>
          <span>Dossiers</span>
          {dossiers.length > 0 && <span className="count numeric">{dossiers.length}</span>}
        </Link>
        <Link className={isActive('/bibliotheque') ? 'active' : ''} href="/bibliotheque">
          <Icon.Library/>
          <span>Bibliothèque</span>
          <span className="count numeric">{VENTES.length}</span>
        </Link>
        <Link className={isActive('/modeles') ? 'active' : ''} href="/modeles">
          <Icon.Template/>
          <span>Modèles</span>
          <span className="count numeric">{MODELES.length}</span>
        </Link>
        <Link className={isActive('/archives') ? 'active' : ''} href="/archives">
          <Icon.Archive/>
          <span>Archives</span>
          <span className="count numeric">{ARCHIVES.length}</span>
        </Link>

        {pinned.length > 0 && (
          <>
            <div className="nav-label" style={{ marginTop: 18 }}>Épinglés</div>
            {pinned.map(d => (
              <Link
                key={d.id}
                className="nav-doc"
                title={d.address}
                href={`/dossier/${encodeURIComponent(d.slug)}`}
              >
                <span className={`dot ${d.status === 'en-cours' ? 'encours' : d.status}`}/>
                <span className="doc-label">{d.address}</span>
              </Link>
            ))}
          </>
        )}

        {recents.length > 0 && (
          <>
            <div className="nav-label" style={{ marginTop: 18 }}>Récents</div>
            {recents.map(d => (
              <Link
                key={d.id}
                className="nav-doc"
                title={d.address}
                href={`/dossier/${encodeURIComponent(d.slug)}`}
              >
                <span className={`dot ${d.status === 'en-cours' ? 'encours' : d.status}`}/>
                <span className="doc-label">{d.address}</span>
              </Link>
            ))}
          </>
        )}
      </nav>

      <div className="spacer"/>

      <div className="firm-wrap" ref={menuRef}>
        {menuOpen && (
          <div className="firm-menu" role="menu">
            <Link
              role="menuitem"
              className="firm-menu-item"
              href="/parametres"
              onClick={() => setMenuOpen(false)}
            >
              <Icon.Settings/>
              <span>Paramètres</span>
            </Link>
            <Link
              role="menuitem"
              className="firm-menu-item"
              href="/aide"
              onClick={() => setMenuOpen(false)}
            >
              <Icon.Help/>
              <span>Aide</span>
            </Link>
            <div className="firm-menu-sep"/>
            <div className="theme-toggle-row" role="group" aria-label="Thème">
              <span className="ttr-label">
                <span>Apparence</span>
              </span>
              <span className="theme-pill">
                <button className={theme === 'light' ? 'active' : ''} onClick={() => pickTheme('light')}>
                  <Icon.Sun/>Clair
                </button>
                <button className={theme === 'dark' ? 'active' : ''} onClick={() => pickTheme('dark')}>
                  <Icon.Moon/>Sombre
                </button>
              </span>
            </div>
            <div className="firm-menu-sep"/>
            <button
              role="menuitem"
              className="firm-menu-item"
              onClick={() => { setMenuOpen(false); onSignOut?.() }}
            >
              <span>Se déconnecter</span>
            </button>
          </div>
        )}
        <button
          className={`firm ${menuOpen ? 'open' : ''}`}
          type="button"
          aria-haspopup="menu"
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen(o => !o)}
        >
          <div className="seal">{initials(name)}</div>
          <div className="who">
            <div className="name">{name}</div>
            <div className="credential">É.A. <span className="numeric">— {credential}</span></div>
          </div>
          <Icon.Chevron/>
        </button>
      </div>
    </aside>
  )
}
