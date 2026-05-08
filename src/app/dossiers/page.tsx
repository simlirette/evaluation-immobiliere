'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import ThemeToggle from '@/components/layout/ThemeToggle'
import DossierCard from '@/components/dossiers/DossierCard'
import EmptyState from '@/components/shared/EmptyState'
import { fetchDossiers } from '@/lib/supabase/queries/dossiers'
import { createClient } from '@/lib/supabase/client'
import type { Dossier, TabId } from '@/types'

function SkeletonCard() {
  return (
    <div
      className="rounded-[18px] px-[22px] pt-[22px] pb-[18px] border border-white/[.72] dark:border-white/[.08]"
      style={{
        background: 'linear-gradient(165deg, rgba(248,244,238,.96) 0%, rgba(238,232,223,.90) 100%)',
        boxShadow: 'var(--shadow-card)',
      }}
    >
      <div className="h-5 w-3/4 rounded-md bg-black/[.06] mb-2 animate-pulse" />
      <div className="h-3 w-1/2 rounded-md bg-black/[.04] mb-5 animate-pulse" />
      <div className="flex justify-between items-center">
        <div className="h-3 w-20 rounded-md bg-black/[.04] animate-pulse" />
        <div className="h-5 w-16 rounded-full bg-black/[.04] animate-pulse" />
      </div>
    </div>
  )
}

export default function MesDossiersPage() {
  const router = useRouter()
  const [search, setSearch] = useState('')
  const [dossiers, setDossiers] = useState<Dossier[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDossiers()
      .then(data => setDossiers(data))
      .finally(() => setLoading(false))
  }, [])

  async function handleSignOut() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push('/login')
  }

  const filtered = dossiers.filter(d =>
    d.address.toLowerCase().includes(search.toLowerCase()) ||
    `${d.property_type} ${d.neighborhood}`.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="relative w-full h-screen overflow-hidden">
      <ThemeToggle />

      <Sidebar
        activeDossierId={null}
        activeTab="dossier"
        showMesDossiers={true}
        currentDossierName=""
        onTabChange={(tab: TabId) => router.push(`/dossier/nouveau?tab=${tab}`)}
        onDossierSelect={(id: string) => router.push(`/dossier/${id}?tab=dossier`)}
        onNewDossier={() => router.push('/dossier/nouveau?tab=dossier')}
        onMesDossiers={() => {}}
        onSignOut={handleSignOut}
      />

      <div className="main-content absolute inset-0 flex flex-col overflow-y-auto">
        <div className="flex flex-col px-10 pt-7 pb-9 flex-1">
          {/* Search + filter row */}
          <div className="flex justify-center mb-7 flex-shrink-0">
            <div className="flex items-center gap-2.5">
              <div
                className="flex items-center gap-2 rounded-full px-5 py-[9px] w-[340px]"
                style={{
                  background: 'linear-gradient(180deg, rgba(248,244,238,.72) 0%, rgba(235,229,220,.62) 100%)',
                  backdropFilter: 'var(--glass-blur)',
                  WebkitBackdropFilter: 'var(--glass-blur)',
                  border: '1px solid rgba(255,255,255,.55)',
                  boxShadow: 'var(--shadow-glass)',
                }}
              >
                <svg width="13" height="13" fill="none" stroke="#b5b2ac" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
                <input
                  className="bg-transparent border-none outline-none text-[13px] text-[#1a1916] dark:text-[#e8e5e0] w-full placeholder:text-[#b5b2ac]"
                  placeholder="Rechercher un dossier..."
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                />
              </div>
              <button
                className="w-[38px] h-[38px] rounded-full flex items-center justify-center flex-shrink-0 text-[#8a8780] hover:text-[#1a1916] transition-colors cursor-pointer border-none"
                style={{
                  background: 'linear-gradient(180deg, rgba(248,244,238,.72) 0%, rgba(235,229,220,.62) 100%)',
                  backdropFilter: 'var(--glass-blur)',
                  WebkitBackdropFilter: 'var(--glass-blur)',
                  border: '1px solid rgba(255,255,255,.55)',
                  boxShadow: 'var(--shadow-glass)',
                }}
                title="Filtrer"
              >
                <svg width="15" height="15" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h18M7 12h10M11 20h2"/>
                </svg>
              </button>
            </div>
          </div>

          {/* Grid */}
          {loading ? (
            <div className="dossier-grid grid gap-4 grid-cols-1">
              {[1, 2, 3].map(i => <SkeletonCard key={i} />)}
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center mt-20">
              <EmptyState
                title={search ? 'Aucun r\u00e9sultat' : 'Aucun dossier'}
                subtitle={search
                  ? `Aucun dossier ne correspond \u00e0 \u00ab\u202f${search}\u202f\u00bb`
                  : 'Cr\u00e9ez un dossier pilote pour lancer les agents.'}
              />
              {!search && (
                <button
                  onClick={() => router.push('/dossier/nouveau?tab=dossier')}
                  className="mt-5 rounded-full px-5 py-2.5 text-[13px] text-white bg-[#334155] hover:opacity-90 transition-opacity"
                >
                  Nouveau dossier
                </button>
              )}
            </div>
          ) : (
            <div className="dossier-grid grid gap-4 grid-cols-1">
              {filtered.map(d => (
                <DossierCard
                  key={d.id}
                  dossier={d}
                  onClick={() => router.push(`/dossier/${d.slug}?tab=dossier`)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
