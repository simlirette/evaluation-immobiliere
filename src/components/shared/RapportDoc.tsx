'use client'

import { useState, useRef } from 'react'

interface Props {
  address?: string
  valeur?: string | null
  onClose: () => void
}

export default function RapportDoc({ address, valeur, onClose }: Props) {
  const [editing, setEditing] = useState(false)
  const docRef = useRef<HTMLDivElement>(null)

  return (
    <div className="flex flex-col flex-1 relative overflow-hidden">
      {/* Corner tools */}
      <div className="absolute top-3 right-8 z-10 flex gap-0.5">
        {editing ? (
          <button
            onClick={() => setEditing(false)}
            className="w-7 h-7 rounded-[7px] flex items-center justify-center bg-transparent border-none cursor-pointer text-[#228866] hover:bg-[rgba(34,136,102,.08)] transition-colors"
          >
            <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7"/>
            </svg>
          </button>
        ) : (
          <button
            onClick={() => setEditing(true)}
            className="w-7 h-7 rounded-[7px] flex items-center justify-center bg-transparent border-none cursor-pointer text-[#b5b2ac] hover:text-[#1a1916] hover:bg-black/[.06] transition-colors"
          >
            <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M15 5l4 4L6 21H3v-3L15 5z"/>
            </svg>
          </button>
        )}
        <button
          onClick={onClose}
          className="w-7 h-7 rounded-[7px] flex items-center justify-center bg-transparent border-none cursor-pointer text-[#b5b2ac] hover:text-[#1a1916] hover:bg-black/[.06] transition-colors"
        >
          <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
              d="M20 4L13 11M17 11H13V7M4 20L11 13M7 13H11V17"/>
          </svg>
        </button>
      </div>

      {/* Scrollable document */}
      <div className="flex-1 overflow-y-auto px-8 py-10 scroll-fade">
        <div
          ref={docRef}
          contentEditable={editing}
          suppressContentEditableWarning
          className={`px-7 py-6 rounded-[14px] text-[13px] leading-[1.75] border border-black/[.06] ${
            editing ? 'outline-none border-[rgba(51,65,85,.25)] shadow-[0_0_0_3px_rgba(51,65,85,.05)]' : ''
          }`}
          style={{
            background: 'rgba(255,255,255,.55)',
            boxShadow: editing ? undefined : 'inset 0 1px 0 rgba(255,255,255,.8)',
          }}
        >
          <div
            className="text-[18px] font-medium text-[#1a1916] mb-1 tracking-[.01em]"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            RAPPORT D'ÉVALUATION IMMOBILIÈRE
          </div>
          <div className="text-[11px] text-[#8a8780] text-center mb-4 pb-3.5 border-b border-black/[.07]">
            Préparé conformément aux normes de l'<strong>Ordre des évaluateurs agréés du Québec (OEAQ)</strong>
          </div>

          <h2 className="text-[14px] font-medium text-[#1a1916] mt-4 mb-1.5 tracking-[.01em]"
            style={{ fontFamily: 'var(--font-serif)' }}>
            1. MANDAT ET OBJET DE L'ÉVALUATION
          </h2>
          <p className="text-[#1a1916] font-light mb-2.5">
            Le soussigné a reçu mandat afin de déterminer la <strong>valeur marchande</strong> de la propriété résidentielle sise au {address || '—'}, en vue d'une décision de financement hypothécaire.
          </p>

          <h2 className="text-[14px] font-medium text-[#1a1916] mt-4 mb-1.5 tracking-[.01em]"
            style={{ fontFamily: 'var(--font-serif)' }}>
            6. CONCLUSION DE VALEUR
          </h2>
          <div
            className="mt-3.5 mb-3.5 px-[18px] py-4 border-l-[3px] border-black/[.15] rounded-[0_6px_6px_0]"
            style={{ background: 'rgba(0,0,0,.03)' }}
          >
            <div className="text-[10px] uppercase tracking-[.07em] text-[#b5b2ac] mb-1.5">Valeur marchande estimée</div>
            <div className="text-[22px] font-semibold tracking-[-.01em]" style={{ fontFamily: 'var(--font-serif)' }}>
              {valeur ?? '—'}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
