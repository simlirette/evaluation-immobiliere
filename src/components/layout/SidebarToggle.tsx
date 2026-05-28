'use client'

interface Props {
  open: boolean
  onToggle: () => void
}

export default function SidebarToggle({ open, onToggle }: Props) {
  return (
    <button
      onClick={onToggle}
      aria-label={open ? 'Fermer la navigation' : 'Ouvrir la navigation'}
      className={`sidebar-toggle w-7 h-14 flex items-center justify-center border border-[var(--rule-soft)] border-l-0 rounded-r-[var(--r-md)] transition-colors cursor-pointer ${open ? 'sidebar-open' : ''}`}
      style={{ background: 'var(--paper)', color: 'var(--ink-mute)' }}
      onMouseEnter={e => {
        e.currentTarget.style.background = 'var(--paper-2)'
        e.currentTarget.style.color = 'var(--ink)'
      }}
      onMouseLeave={e => {
        e.currentTarget.style.background = 'var(--paper)'
        e.currentTarget.style.color = 'var(--ink-mute)'
      }}
    >
      <svg
        width="10" height="16" viewBox="0 0 10 16" fill="none"
        aria-hidden="true"
        style={{ transform: open ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform .22s' }}
      >
        <path d="M3 3l4 5-4 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    </button>
  )
}
