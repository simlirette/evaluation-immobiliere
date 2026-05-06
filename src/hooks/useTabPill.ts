'use client'

import { useRef, useEffect, useCallback } from 'react'
import type { TabId } from '@/types'

export function useTabPill(activeTab: TabId) {
  const groupRef = useRef<HTMLDivElement>(null)
  const pillRef  = useRef<HTMLDivElement>(null)

  const movePill = useCallback(() => {
    const group = groupRef.current
    const pill  = pillRef.current
    if (!group || !pill) return
    const active = group.querySelector<HTMLElement>('[data-active="true"]')
    if (!active) return
    const gr = group.getBoundingClientRect()
    const ar = active.getBoundingClientRect()
    pill.style.left  = `${ar.left - gr.left}px`
    pill.style.width = `${ar.width}px`
  }, [])

  useEffect(() => {
    const pill = pillRef.current
    if (pill) pill.style.transition = 'none'
    movePill()
    requestAnimationFrame(() => {
      if (pill) pill.style.transition = ''
    })
  }, [activeTab, movePill])

  return { groupRef, pillRef, movePill }
}
