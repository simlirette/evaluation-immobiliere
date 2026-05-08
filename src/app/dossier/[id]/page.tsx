'use client'

import { useState, useEffect, Suspense } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import TabBar from '@/components/layout/TabBar'
import ThemeToggle from '@/components/layout/ThemeToggle'
import DossierPanel from '@/components/panels/DossierPanel'
import MarchePanel from '@/components/panels/MarchePanel'
import AnalysePanel from '@/components/panels/AnalysePanel'
import RapportPanel from '@/components/panels/RapportPanel'
import { fetchDossier } from '@/lib/supabase/queries/dossiers'
import type { TabId } from '@/types'

const VALID_TABS: TabId[] = ['dossier', 'marche', 'analyse', 'rapport']

function DossierShellInner() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const searchParams = useSearchParams()

  const rawTab = searchParams.get('tab') as TabId | null
  const activeTab: TabId = rawTab && VALID_TABS.includes(rawTab) ? rawTab : 'dossier'

  const [activeDossierId, setActiveDossierId] = useState(params.id)
  const [currentDossierName, setCurrentDossierName] = useState(params.id)
  const [dossierId, setDossierId] = useState<string | null>(null)
  const [showMesDossiers, setShowMesDossiers] = useState(false)
  const [isNew, setIsNew] = useState(params.id === 'nouveau')
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    if (params.id === 'nouveau') return
    fetchDossier(params.id)
      .then(d => {
        if (d) {
          setCurrentDossierName(d.address)
          setDossierId(d.id)
        } else {
          router.push('/dossiers')
        }
      })
      .catch(() => router.push('/dossiers'))
  }, [params.id])

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
        onSignOut={() => router.push('/dossiers')}
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
            {activeTab === 'dossier'  && <DossierPanel isNew={isNew} dossierId={dossierId} />}
            {activeTab === 'marche'   && <MarchePanel dossierId={dossierId} />}
            {activeTab === 'analyse'  && <AnalysePanel dossierId={dossierId} />}
            {activeTab === 'rapport'  && <RapportPanel dossierId={dossierId} dossierAddress={currentDossierName} />}
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
