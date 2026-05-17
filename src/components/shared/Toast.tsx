'use client'

import { useEffect, useRef } from 'react'

interface Props {
  message: string | null
  onDismiss: () => void
  duration?: number
}

export default function Toast({ message, onDismiss, duration = 3000 }: Props) {
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!message) return
    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(onDismiss, duration)
    return () => { if (timer.current) clearTimeout(timer.current) }
  }, [message, duration, onDismiss])

  return (
    <div
      className="fixed bottom-5 left-1/2 z-[600] -translate-x-1/2 pointer-events-none"
      style={{
        transition: 'opacity .2s ease, transform .2s ease',
        opacity: message ? 1 : 0,
        transform: message ? 'translateX(-50%) translateY(0)' : 'translateX(-50%) translateY(8px)',
      }}
    >
      <div
        className="px-4 py-2.5 rounded-full text-[13px] text-white whitespace-nowrap"
        style={{
          background: 'rgba(26,25,22,.88)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          boxShadow: '0 4px 16px rgba(0,0,0,.18)',
        }}
      >
        {message}
      </div>
    </div>
  )
}
