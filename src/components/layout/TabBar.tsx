'use client'

import { TABS } from '@/constants/app'
import { useTabPill } from '@/hooks/useTabPill'
import type { TabId } from '@/types'

interface Props {
  activeTab: TabId
  onTabChange: (tab: TabId) => void
  hidden: boolean
}

export default function TabBar({ activeTab, onTabChange, hidden }: Props) {
  const { groupRef, pillRef } = useTabPill(activeTab)

  return (
    <div
      className={`flex justify-center px-6 pt-[22px] flex-shrink-0 relative z-10 transition-[opacity,height,padding] duration-300 ${
        hidden ? 'opacity-0 pointer-events-none h-0 pt-0 overflow-hidden' : ''
      }`}
    >
      <div
        ref={groupRef}
        className="inline-flex relative rounded-full p-1 gap-0.5 max-w-full overflow-x-auto"
        role="tablist"
        aria-label="Onglets du dossier"
        style={{
          background: 'linear-gradient(180deg, rgba(230,224,214,.80) 0%, rgba(218,211,200,.70) 100%)',
          backdropFilter: 'var(--glass-blur)',
          WebkitBackdropFilter: 'var(--glass-blur)',
          border: '1px solid rgba(255,255,255,.38)',
          boxShadow: 'var(--shadow-glass)',
        }}
      >
        <div
          ref={pillRef}
          className="absolute top-1 h-[calc(100%-8px)] rounded-full pointer-events-none z-0"
          style={{
            background: 'var(--tab-active-bg)',
            backdropFilter: 'blur(8px)',
            WebkitBackdropFilter: 'blur(8px)',
            border: '1px solid var(--tab-active-border)',
            boxShadow: 'var(--shadow-pill)',
            transition: 'left .28s cubic-bezier(.45,.05,.15,1), width .28s cubic-bezier(.45,.05,.15,1)',
          }}
        />
        {TABS.map(tab => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            data-active={activeTab === tab.id}
            className={`relative z-[1] px-[14px] sm:px-[22px] py-[7px] rounded-full text-[13px] cursor-pointer whitespace-nowrap transition-colors duration-200 select-none bg-transparent border-none font-sans focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#334155] focus-visible:ring-offset-1 ${
              activeTab === tab.id ? 'text-[#1a1916] font-medium' : 'text-[#8a8780] hover:text-[#1a1916]'
            }`}
            onClick={() => onTabChange(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </div>
  )
}
