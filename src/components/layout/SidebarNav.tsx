'use client'

import { TABS } from '@/constants/app'
import type { TabId } from '@/types'

interface Props {
  activeTab: TabId
  onTabChange: (tab: TabId) => void
  showMesDossiers: boolean
}

export default function SidebarNav({ activeTab, onTabChange, showMesDossiers }: Props) {
  return (
    <div className="px-3 flex flex-col gap-px" role="navigation" aria-label="Sections du dossier">
      {TABS.map(tab => (
        <div
          key={tab.id}
          role="button"
          tabIndex={0}
          className={`px-3 py-[7px] text-[13px] rounded-[6px] cursor-pointer transition-[color,background] duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#334155] ${
            !showMesDossiers && activeTab === tab.id
              ? 'text-[#1a1916] dark:text-[#e8e5e0] bg-black/[.05] dark:bg-white/[.05]'
              : 'text-[#8a8780] hover:text-[#1a1916] dark:hover:text-[#e8e5e0] hover:bg-black/[.03] dark:hover:bg-white/[.03]'
          }`}
          onClick={() => onTabChange(tab.id)}
          onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && onTabChange(tab.id)}
          aria-current={!showMesDossiers && activeTab === tab.id ? 'page' : undefined}
        >
          {tab.label}
        </div>
      ))}
    </div>
  )
}
