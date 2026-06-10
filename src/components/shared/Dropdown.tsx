'use client'

/* Dropdown custom du design handoff — menu popover stylé (remplace <select> natif). */

import { useState, useEffect, useRef } from 'react'
import { Icon } from './Icon'

export interface DropdownOption {
  value: string
  label: string
}

interface Props {
  label?: string
  value: string
  options: (string | DropdownOption)[]
  onChange: (value: string) => void
  align?: 'left' | 'right'
}

export default function Dropdown({ label, value, options, onChange, align = 'left' }: Props) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDoc)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  const current = options.find(o => (typeof o === 'string' ? o : o.value) === value)
  const currentLabel = current
    ? (typeof current === 'string' ? current : current.label)
    : value

  return (
    <div className={`dropdown ${open ? 'open' : ''}`} ref={ref}>
      {label && <span className="dd-label">{label}</span>}
      <button
        type="button"
        className="dd-trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen(o => !o)}
      >
        <span className="dd-value">{currentLabel}</span>
        <span className="dd-caret">
          <svg viewBox="0 0 10 6" width="9" height="6" aria-hidden="true">
            <path d="M0 1l5 4 5-4" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </span>
      </button>
      {open && (
        <div className={`dd-menu dd-menu-${align}`} role="listbox">
          {options.map(o => {
            const v = typeof o === 'string' ? o : o.value
            const l = typeof o === 'string' ? o : o.label
            const active = v === value
            return (
              <button
                key={v}
                type="button"
                role="option"
                aria-selected={active}
                className={`dd-item ${active ? 'active' : ''}`}
                onClick={() => { onChange(v); setOpen(false) }}
              >
                <span className="dd-item-label">{l}</span>
                {active && <Icon.Check/>}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
