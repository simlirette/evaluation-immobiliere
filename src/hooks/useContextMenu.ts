'use client'

import { useState, useCallback } from 'react'
import type { ContextMenuTarget } from '@/types'

export function useContextMenu() {
  const [target, setTarget] = useState<ContextMenuTarget | null>(null)

  const open = useCallback((e: React.MouseEvent, name: string, pinned: boolean) => {
    e.stopPropagation()
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
    setTarget({ name, pinned, x: rect.right + 6, y: rect.top })
  }, [])

  const close = useCallback(() => setTarget(null), [])

  return { target, open, close }
}
