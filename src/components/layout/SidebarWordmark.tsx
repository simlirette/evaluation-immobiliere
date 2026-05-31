import Link from 'next/link'

export default function SidebarWordmark() {
  return (
    <div className="px-5 py-5 border-b border-[var(--rule-soft)] flex-shrink-0">
      <Link href="/dossiers" className="block no-underline">
        <div
          className="text-[22px] font-medium leading-tight"
          style={{ fontFamily: 'var(--font-serif)', letterSpacing: '-.015em', color: 'var(--ink)' }}
        >
          Éval{' '}
          <span style={{ color: 'var(--navy)', fontStyle: 'italic' }}>Immo</span>
        </div>
        <div
          className="text-[11px] mt-0.5"
          style={{ color: 'var(--ink-faint)', fontFamily: 'var(--font-sans)', letterSpacing: '.01em' }}
        >
          Évaluateurs agréés — Québec
        </div>
      </Link>
    </div>
  )
}
