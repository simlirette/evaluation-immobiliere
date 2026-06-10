'use client'

/* Stepper — markup 1:1 du design handoff (num → Check verdigris quand done). */

import { TABS } from '@/constants/app'
import { Icon } from '@/components/shared/Icon'
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
            {isDone ? <Icon.Check/> : <span className="num numeric">{i + 1}</span>}
            <span className="label">{tab.label}</span>
          </button>
        )
      })}
    </div>
  )
}
