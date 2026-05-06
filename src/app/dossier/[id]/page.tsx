'use client'

import { useState, Suspense } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import TabBar from '@/components/layout/TabBar'
import ThemeToggle from '@/components/layout/ThemeToggle'
import DossierPanel from '@/components/panels/DossierPanel'
import MarchePanel from '@/components/panels/MarchePanel'
import AnalysePanel from '@/components/panels/AnalysePanel'
import RapportPanel from '@/components/panels/RapportPanel'
import { createClient } from '@/lib/supabase/client'
import { MOCK_DOSSIERS } from '@/data/mock'
import type { TabId } from '@/types'

const VALID_TABS: TabId[] = ['dossier', 'marche', 'analyse', 'rapport']

function DossierShellInner() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const searchParams = useSearchParams()

  const rawTab = searchParams.get('tab') as TabId | null
  const activeTab: TabId = rawTab && VALID_TABS.includes(rawTab) ? rawTab : 'dossier'

  const [activeDossierId, setActiveDossierId] = useState(params.id)
  const [currentDossierName, setCurrentDossierName] = useState(() => {
    const found = MOCK_DOSSIERS.find(d => d.id === params.id)
    return found?.address ?? params.id
  })
  const [showMesDossiers, setShowMesDossiers] = useState(false)
  const [isNew, setIsNew] = useState(params.id === 'nouveau')
  const [visible, setVisible] = useState(true)

  function setTab(tab: TabId) {
    setShowMesDossiers(false)
    setVisible(false)
    setTimeout(() => {
      router.replace(`/dossier/${activeDossierId}?tab=${tab}`)
      setVisible(true)
    }, 200)
  }

  function handleDossierSelect(id: string, name: string) {
    setVisible(false)
    setTimeout(() => {
      setActiveDossierId(id)
      setCurrentDossierName(name)
      setShowMesDossiers(false)
      setIsNew(false)
      router.push(`/dossier/${id}?tab=dossier`)
      setVisible(true)
    }, 200)
  }

  function handleNewDossier() {
    setVisible(false)
    setTimeout(() => {
      setActiveDossierId('nouveau')
      setCurrentDossierName('Nouveau dossier')
      setShowMesDossiers(false)
      setIsNew(true)
      router.push('/dossier/nouveau?tab=dossier')
      setVisible(true)
    }, 200)
  }

  function handleMesDossiers() {
    router.push('/dossiers')
  }

  return (
    <div className="relative w-full h-screen overflow-hidden">
      <ThemeToggle />

      <Sidebar
        activeDossierId={activeDossierId}
        activeTab={activeTab}
        showMesDossiers={showMesDossiers}
        currentDossierName={currentDossierName}
        onTabChange={setTab}
        onDossierSelect={handleDossierSelect}
        onNewDossier={handleNewDossier}
        onMesDossiers={handleMesDossiers}
        onSignOut={async () => {
          const supabase = createClient()
          await supabase.auth.signOut()
          router.push('/login')
        }}
      />

      <div className="absolute inset-0 flex flex-col" style={{ paddingLeft: '224px' }}>
        <TabBar
          activeTab={activeTab}
          onTabChange={setTab}
          hidden={showMesDossiers}
        />

        <div
          className="flex-1 relative overflow-hidden transition-[opacity,transform] duration-300"
          style={{
            opacity: visible ? 1 : 0,
            transform: visible ? 'translateY(0)' : 'translateY(6px)',
          }}
        >
          <div className="absolute inset-0 flex">
            {activeTab === 'dossier'  && <DossierPanel isNew={isNew} />}
            {activeTab === 'marche'   && <MarchePanel />}
            {activeTab === 'analyse'  && <AnalysePanel />}
            {activeTab === 'rapport'  && <RapportPanel />}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function DossierShell() {
  return (
    <Suspense>
      <DossierShellInner />
    </Suspense>
  )
}
