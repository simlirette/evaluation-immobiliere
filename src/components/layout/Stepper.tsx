'use client'

import { TABS } from '@/constants/app'
import type { TabId } from '@/types'

interface Props {
  activeTab: TabId
  onTabChange: (tab: TabId) => void
  completedTabs?: TabId[]
}

const STEP_ORDER: TabId[] = ['dossier', 'marche', 'analyse', 'synthese', 'rapport']

export default function Stepper({ activeTab, onTabChange, completedTabs = [] }: Props) {
  const activeIdx = STEP_ORDER.indexOf(activeTab)

  return (
    <div className="stepper" role="tablist" aria-label="Étapes du dossier">
      {TABS.map((tab, i) => {
        const isDone = completedTabs.includes(tab.id) || i < activeIdx
        const isNow  = tab.id === activeTab
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isNow}
            className={`step ${isDone ? 'done' : ''} ${isNow ? 'now' : ''}`}
            onClick={() => onTabChange(tab.id)}
          >
            <span className="step-num">
              {isDone ? (
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                  <path d="M2.5 7l3 3 6-6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              ) : (
                i + 1
              )}
            </span>
            {tab.label}
          </button>
        )
      })}
    </div>
  )
}
