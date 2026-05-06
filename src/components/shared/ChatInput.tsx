'use client'

import { useState } from 'react'

interface Props {
  placeholder: string
  onSend?: (value: string) => void
}

export default function ChatInput({ placeholder, onSend }: Props) {
  const [value, setValue] = useState('')
  const ready = value.trim().length > 0

  function handleSend() {
    if (!ready) return
    onSend?.(value.trim())
    setValue('')
  }

  return (
    <div className="w-full max-w-[640px]">
      <div
        className="flex items-center gap-1.5 rounded-full px-2 py-2 border transition-[border-color,box-shadow] duration-200"
        style={{
          background: 'linear-gradient(180deg, rgba(242,237,230,.72) 0%, rgba(232,226,216,.62) 100%)',
          backdropFilter: 'var(--glass-blur)',
          WebkitBackdropFilter: 'var(--glass-blur)',
          border: '1px solid var(--input-border)',
          boxShadow: 'var(--shadow-glass)',
        }}
      >
        <button className="w-[34px] h-[34px] rounded-full flex items-center justify-center text-[#b5b2ac] hover:text-[#8a8780] transition-colors">
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/>
          </svg>
        </button>
        <input
          className="flex-1 bg-transparent border-none outline-none text-sm font-light text-[#1a1916] placeholder:text-[#b5b2ac] min-w-0"
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder={placeholder}
        />
        <button
          onClick={handleSend}
          className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 border-none cursor-pointer transition-[background,transform] duration-200 hover:scale-[1.06]"
          style={{ background: ready ? '#334155' : 'var(--send-idle)' }}
        >
          <svg width="16" height="16" fill="none" stroke="white" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </button>
      </div>
    </div>
  )
}
