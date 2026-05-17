'use client'

import { useEffect, useRef, useState } from 'react'
import type { ContextMenuTarget } from '@/types'

type Mode = 'idle' | 'confirming' | 'renaming'

interface Props {
  target: ContextMenuTarget | null
  onClose: () => void
  onPin: (name: string, pinned: boolean) => void
  onRename: (name: string, newName: string) => void
  onDuplicate: (name: string) => void
  onDelete: (name: string) => void
}

export default function ContextMenu({ target, onClose, onPin, onRename, onDuplicate, onDelete }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const [mode, setMode] = useState<Mode>('idle')
  const [renameValue, setRenameValue] = useState('')

  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setMode('idle')
        onClose()
      }
    }
    document.addEventListener('click', handler)
    return () => document.removeEventListener('click', handler)
  }, [onClose])

  useEffect(() => {
    if (!target) { setMode('idle'); return }
    setRenameValue(target.name)
  }, [target])

  useEffect(() => {
    if (mode === 'renaming') inputRef.current?.select()
  }, [mode])

  function handleRenameSubmit() {
    const trimmed = renameValue.trim()
    if (trimmed && trimmed !== target!.name) {
      onRename(target!.name, trimmed)
    }
    setMode('idle')
    onClose()
  }

  const open = !!target

  return (
    <div
      ref={ref}
      className="fixed z-[500] min-w-[180px] rounded-xl p-[5px]"
      style={{
        left: target?.x ?? 0,
        top: target?.y ?? 0,
        background: 'linear-gradient(160deg, rgba(246,242,236,.96) 0%, rgba(234,228,218,.92) 100%)',
        backdropFilter: 'blur(32px) saturate(180%)',
        WebkitBackdropFilter: 'blur(32px) saturate(180%)',
        border: '1px solid rgba(255,255,255,.65)',
        boxShadow: '0 2px 8px rgba(0,0,0,.08), 0 12px 32px rgba(0,0,0,.12), inset 0 1px 0 rgba(255,255,255,.85)',
        opacity: open ? 1 : 0,
        pointerEvents: open ? 'all' : 'none',
        transform: open ? 'scale(1) translateY(0)' : 'scale(.95) translateY(-4px)',
        transformOrigin: 'top left',
        transition: 'opacity .14s ease, transform .14s ease',
      }}
    >
      {mode === 'renaming' ? (
        <div className="px-2.5 py-2">
          <input
            ref={inputRef}
            value={renameValue}
            onChange={e => setRenameValue(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter') handleRenameSubmit()
              if (e.key === 'Escape') { setMode('idle'); onClose() }
            }}
            className="w-full rounded-[6px] px-2 py-1.5 text-[12px] text-[#1a1916] bg-white/70 border border-black/[.12] outline-none focus:border-[#334155] font-sans mb-2"
            placeholder="Nouveau nom…"
          />
          <div className="flex gap-1.5">
            <button
              className="flex-1 px-2 py-1 rounded-[6px] text-[12px] text-white bg-[#334155] hover:opacity-90 transition-opacity border-none cursor-pointer font-sans"
              onClick={handleRenameSubmit}
            >
              Renommer
            </button>
            <button
              className="flex-1 px-2 py-1 rounded-[6px] text-[12px] text-[#6a6763] hover:bg-black/[.06] transition-colors border border-black/[.08] cursor-pointer bg-transparent font-sans"
              onClick={() => { setMode('idle'); onClose() }}
            >
              Annuler
            </button>
          </div>
        </div>
      ) : mode === 'confirming' ? (
        <div className="px-2.5 py-1.5">
          <div className="text-[11px] text-[#8a8780] mb-2">Supprimer ce dossier ?</div>
          <div className="flex gap-1.5">
            <button
              className="flex-1 px-2 py-1 rounded-[6px] text-[12px] text-white bg-[#c0392b] hover:opacity-90 transition-opacity border-none cursor-pointer font-sans"
              onClick={() => { onDelete(target!.name); setMode('idle'); onClose() }}
            >
              Supprimer
            </button>
            <button
              className="flex-1 px-2 py-1 rounded-[6px] text-[12px] text-[#6a6763] hover:bg-black/[.06] transition-colors border border-black/[.08] cursor-pointer bg-transparent font-sans"
              onClick={() => setMode('idle')}
            >
              Annuler
            </button>
          </div>
        </div>
      ) : (
        <>
          <button
            className="flex w-full items-center gap-2 px-2.5 py-1.5 rounded-lg text-[13px] text-[#1a1916] hover:bg-black/[.05] transition-colors text-left bg-transparent border-none cursor-pointer"
            onClick={() => { onPin(target!.name, target!.pinned); onClose() }}
          >
            <svg width="13" height="13" fill="currentColor" viewBox="0 0 24 24" className="text-[#8a8780] flex-shrink-0">
              <path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"/>
            </svg>
            {target?.pinned ? 'Désépingler' : 'Épingler'}
          </button>
          <button
            className="flex w-full items-center gap-2 px-2.5 py-1.5 rounded-lg text-[13px] text-[#1a1916] hover:bg-black/[.05] transition-colors text-left bg-transparent border-none cursor-pointer"
            onClick={() => setMode('renaming')}
          >
            <svg width="13" height="13" fill="none" stroke="currentColor" viewBox="0 0 24 24" className="text-[#8a8780] flex-shrink-0">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
            </svg>
            Renommer
          </button>
          <button
            className="flex w-full items-center gap-2 px-2.5 py-1.5 rounded-lg text-[13px] text-[#1a1916] hover:bg-black/[.05] transition-colors text-left bg-transparent border-none cursor-pointer"
            onClick={() => { onDuplicate(target!.name); onClose() }}
          >
            <svg width="13" height="13" fill="none" stroke="currentColor" viewBox="0 0 24 24" className="text-[#8a8780] flex-shrink-0">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
            </svg>
            Dupliquer
          </button>
          <div className="h-px bg-black/[.07] mx-1.5 my-1" />
          <button
            className="flex w-full items-center gap-2 px-2.5 py-1.5 rounded-lg text-[13px] text-[#c0392b] hover:bg-black/[.05] transition-colors text-left bg-transparent border-none cursor-pointer"
            onClick={() => setMode('confirming')}
          >
            <svg width="13" height="13" fill="none" stroke="currentColor" viewBox="0 0 24 24" className="flex-shrink-0">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
            Supprimer
          </button>
        </>
      )}
    </div>
  )
}
