'use client'

import { useEffect } from 'react'

interface Props {
  open: boolean
  onClose: () => void
}

const SHORTCUTS = [
  { keys: ['Ctrl', '1'], label: 'Onglet Dossier' },
  { keys: ['Ctrl', '2'], label: 'Onglet Marché' },
  { keys: ['Ctrl', '3'], label: 'Onglet Analyse' },
  { keys: ['Ctrl', '4'], label: 'Onglet Synthèse' },
  { keys: ['Ctrl', '5'], label: 'Onglet Rapport' },
  { keys: ['?'], label: 'Aide clavier' },
  { keys: ['Esc'], label: 'Fermer ce panneau' },
]

export default function ShortcutHelp({ open, onClose }: Props) {
  useEffect(() => {
    if (!open) return
    function handler(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-[700] flex items-center justify-center"
      onClick={onClose}
    >
      <div
        className="rounded-[20px] px-7 py-6 min-w-[280px]"
        style={{
          background: 'linear-gradient(160deg, rgba(248,244,238,.97) 0%, rgba(235,229,220,.95) 100%)',
          backdropFilter: 'blur(32px) saturate(180%)',
          WebkitBackdropFilter: 'blur(32px) saturate(180%)',
          border: '1px solid rgba(255,255,255,.70)',
          boxShadow: '0 8px 40px rgba(0,0,0,.14), inset 0 1px 0 rgba(255,255,255,.90)',
        }}
        onClick={e => e.stopPropagation()}
      >
        <div className="text-[11px] uppercase tracking-[.08em] text-[#b5b2ac] font-medium mb-4">
          Raccourcis clavier
        </div>
        <div className="flex flex-col gap-2">
          {SHORTCUTS.map(({ keys, label }) => (
            <div key={label} className="flex items-center justify-between gap-6">
              <span className="text-[13px] text-[#6a6763]">{label}</span>
              <div className="flex items-center gap-1">
                {keys.map((k, i) => (
                  <span key={i} className="inline-flex items-center">
                    {i > 0 && <span className="text-[10px] text-[#b5b2ac] mx-0.5">+</span>}
                    <kbd
                      className="px-1.5 py-0.5 rounded-[5px] text-[11px] text-[#334155] font-mono"
                      style={{ background: 'rgba(51,65,85,.08)', border: '1px solid rgba(51,65,85,.14)' }}
                    >
                      {k}
                    </kbd>
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
        <button
          className="mt-5 w-full py-1.5 rounded-[8px] text-[12px] text-[#8a8780] hover:text-[#1a1916] hover:bg-black/[.04] transition-colors bg-transparent border-none cursor-pointer font-sans"
          onClick={onClose}
        >
          Fermer
        </button>
      </div>
    </div>
  )
}
