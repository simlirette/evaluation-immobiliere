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
    <div className="px-3 flex flex-col gap-px">
      {TABS.map(tab => (
        <div
          key={tab.id}
          className={`px-3 py-[7px] text-[13px] rounded-[6px] cursor-pointer transition-[color,background] duration-200 ${
            !showMesDossiers && activeTab === tab.id
              ? 'text-[#1a1916] bg-black/[.05]'
              : 'text-[#8a8780] hover:text-[#1a1916] hover:bg-black/[.03]'
          }`}
          onClick={() => onTabChange(tab.id)}
        >
          {tab.label}
        </div>
      ))}
    </div>
  )
}
