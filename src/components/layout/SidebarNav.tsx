'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const NAV_ITEMS = [
  { href: '/dossiers',     label: 'Dossiers',     icon: FolderIcon,  count: null as number | null },
  { href: '/bibliotheque', label: 'Bibliothèque', icon: LibraryIcon, count: 348 },
  { href: '/modeles',      label: 'Modèles',      icon: TemplateIcon,count: 6 },
  { href: '/archives',     label: 'Archives',     icon: ArchiveIcon, count: 142 },
]

export default function SidebarNav() {
  const pathname = usePathname()

  function isActive(href: string) {
    if (href === '/dossiers') return pathname === '/dossiers'
    return pathname === href || pathname.startsWith(href + '/')
  }

  return (
    <div className="px-3 py-3 flex flex-col gap-px">
      <Link
        href="/dossier/nouveau"
        className="nav-item mb-1"
        style={{ color: 'var(--navy)', fontWeight: 500 }}
      >
        <span className="nav-icon"><PlusIcon /></span>
        <span>Nouveau dossier</span>
      </Link>
      {NAV_ITEMS.map(item => (
        <Link
          key={item.href}
          href={item.href}
          className={`nav-item ${isActive(item.href) ? 'active' : ''}`}
        >
          <span className="nav-icon"><item.icon /></span>
          <span>{item.label}</span>
          {item.count != null && <span className="nav-count">{item.count}</span>}
        </Link>
      ))}
    </div>
  )
}

function PlusIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M8 3v10M3 8h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  )
}
function FolderIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M2 5a1 1 0 011-1h3l1.5 2H13a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1V5z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"/>
    </svg>
  )
}
function LibraryIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <rect x="2" y="3" width="3" height="10" rx="1" stroke="currentColor" strokeWidth="1.4"/>
      <rect x="6.5" y="3" width="3" height="10" rx="1" stroke="currentColor" strokeWidth="1.4"/>
      <path d="M11 4l2.5 8.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
    </svg>
  )
}
function TemplateIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.4"/>
      <path d="M2 6h12M6 6v8" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
    </svg>
  )
}
function ArchiveIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <rect x="2" y="4" width="12" height="9" rx="1" stroke="currentColor" strokeWidth="1.4"/>
      <path d="M1 4h14M6 8h4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
    </svg>
  )
}
