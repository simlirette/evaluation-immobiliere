'use client'

import { useState, useRef } from 'react'

interface Props {
  placeholder: string
  onSend?: (value: string) => void
  disabled?: boolean
}

export default function ChatInput({ placeholder, onSend, disabled }: Props) {
  const [value, setValue] = useState('')
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const ready = value.trim().length > 0 && !disabled

  function handleSend() {
    if (!ready) return
    onSend?.(value.trim())
    setValue('')
    inputRef.current?.focus()
  }

  return (
    <div
      className="w-full rounded-[18px] border transition-[border-color,box-shadow] duration-150"
      style={{
        background: 'var(--paper-hi)',
        border: '1px solid var(--rule)',
        boxShadow: '0 2px 8px rgba(0,0,0,.06)',
      }}
      onFocus={() => {}}
    >
      {/* Input row */}
      <div className="flex items-end gap-2 px-4 pt-3.5 pb-3">
        <textarea
          ref={inputRef}
          rows={1}
          className="flex-1 bg-transparent border-none outline-none text-[14px] font-light text-[var(--ink)] placeholder:text-[var(--ink-faint)] min-w-0 resize-none leading-6 disabled:opacity-50"
          style={{ fontFamily: 'var(--font-sans)', maxHeight: '160px', overflowY: 'auto' }}
          value={value}
          disabled={disabled}
          onChange={e => {
            setValue(e.target.value)
            // Auto-resize
            const el = e.target
            el.style.height = 'auto'
            el.style.height = el.scrollHeight + 'px'
          }}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSend()
            }
          }}
          placeholder={disabled ? 'En cours…' : placeholder}
        />
      </div>

      {/* Bottom bar — attachement + send */}
      <div className="flex items-center justify-between px-3 pb-2.5">
        <button
          aria-label="Joindre un fichier"
          className="w-8 h-8 rounded-full flex items-center justify-center transition-colors border-none bg-transparent cursor-pointer"
          style={{ color: 'var(--ink-faint)' }}
          onMouseEnter={e => (e.currentTarget.style.background = 'var(--paper-2)')}
          onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
        >
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none" aria-hidden="true">
            <path d="M7.5 1v13M1 7.5h13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        </button>

        <button
          onClick={handleSend}
          aria-label="Envoyer"
          disabled={!ready}
          className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 border-none cursor-pointer transition-[background,opacity] duration-150 disabled:opacity-30 disabled:cursor-not-allowed"
          style={{
            background: ready ? 'var(--ink)' : 'var(--rule)',
          }}
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <path d="M2 7h10M8 3l4 4-4 4" stroke="white" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      </div>
    </div>
  )
}
