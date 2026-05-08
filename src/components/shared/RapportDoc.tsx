'use client'

import { useState } from 'react'

interface Props {
  address?: string
  valeur?: string | null
  content?: string
  onClose: () => void
}

export default function RapportDoc({ address, valeur, content, onClose }: Props) {
  const [editing, setEditing] = useState(false)

  return (
    <div className="flex flex-col flex-1 relative overflow-hidden">
      <div className="absolute top-3 right-8 z-10 flex gap-0.5">
        <button
          onClick={() => setEditing(e => !e)}
          className={`w-7 h-7 rounded-[7px] flex items-center justify-center bg-transparent border-none cursor-pointer transition-colors ${
            editing ? 'text-[#228866]' : 'text-[#b5b2ac] hover:text-[#1a1916] hover:bg-black/[.06]'
          }`}
          title={editing ? 'Terminer' : 'Modifier'}
        >
          <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {editing ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7"/>
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M15 5l4 4L6 21H3v-3L15 5z"/>
            )}
          </svg>
        </button>
        <button
          onClick={onClose}
          className="w-7 h-7 rounded-[7px] flex items-center justify-center bg-transparent border-none cursor-pointer text-[#b5b2ac] hover:text-[#1a1916] hover:bg-black/[.06] transition-colors"
          title="Fermer"
        >
          <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
              d="M20 4L13 11M17 11H13V7M4 20L11 13M7 13H11V17"/>
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-8 py-10 scroll-fade">
        <div
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
            BROUILLON DE RAPPORT D'EVALUATION
          </div>
          <div className="text-[11px] text-[#8a8780] mb-4 pb-3.5 border-b border-black/[.07]">
            Non certifie. Aucune reponse d'evaluateur externe n'est inventee. Validation et signature hors systeme requises.
          </div>

          <div className="grid grid-cols-2 gap-2 text-[12px] mb-4">
            <div className="rounded-[8px] bg-black/[.03] px-3 py-2">
              <div className="text-[10px] uppercase tracking-[.07em] text-[#b5b2ac]">Dossier</div>
              <div>{address || '-'}</div>
            </div>
            <div className="rounded-[8px] bg-black/[.03] px-3 py-2">
              <div className="text-[10px] uppercase tracking-[.07em] text-[#b5b2ac]">Conclusion proposee</div>
              <div>{valeur ?? '-'}</div>
            </div>
          </div>

          <pre className="whitespace-pre-wrap font-sans text-[13px] leading-6 text-[#1a1916]">
            {content || 'Aucun brouillon runtime disponible.'}
          </pre>
        </div>
      </div>
    </div>
  )
}
