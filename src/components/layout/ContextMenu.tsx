'use client'

import { useEffect, useRef } from 'react'
import type { ContextMenuTarget } from '@/types'

interface Props {
  target: ContextMenuTarget | null
  onClose: () => void
  onPin: (name: string, pinned: boolean) => void
  onDelete: (name: string) => void
}

export default function ContextMenu({ target, onClose, onPin, onDelete }: Props) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose()
    }
    document.addEventListener('click', handler)
    return () => document.removeEventListener('click', handler)
  }, [onClose])

  const open = !!target

  return (
    <div
      ref={ref}
      className="fixed z-[500] min-w-[148px] rounded-xl p-[5px]"
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
      <button
        className="flex w-full items-center gap-2 px-2.5 py-1.5 rounded-lg text-[13px] text-[#1a1916] hover:bg-black/[.05] transition-colors text-left"
        onClick={() => { onPin(target!.name, target!.pinned); onClose() }}
      >
        <svg width="13" height="13" fill="currentColor" viewBox="0 0 24 24" className="text-[#8a8780]">
          <path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"/>
        </svg>
        {target?.pinned ? 'Désépingler' : 'Épingler'}
      </button>
      <div className="h-px bg-black/[.07] mx-1.5 my-1" />
      <button
        className="flex w-full items-center gap-2 px-2.5 py-1.5 rounded-lg text-[13px] text-[#c0392b] hover:bg-black/[.05] transition-colors text-left"
        onClick={() => { onDelete(target!.name); onClose() }}
      >
        <svg width="13" height="13" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
        </svg>
        Masquer
      </button>
    </div>
  )
}
