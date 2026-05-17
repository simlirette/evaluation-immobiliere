'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import ThemeToggle from '@/components/layout/ThemeToggle'
import DossierCard from '@/components/dossiers/DossierCard'
import EmptyState from '@/components/shared/EmptyState'
import { fetchDossiers } from '@/lib/supabase/queries/dossiers'
import { createClient } from '@/lib/supabase/client'
import type { Dossier, DossierStatus, TabId } from '@/types'

type SortKey = 'recent' | 'oldest' | 'az' | 'za'
type StatusFilter = 'all' | DossierStatus

const SORT_LABELS: Record<SortKey, string> = {
  recent: 'Récent en premier',
  oldest: 'Plus ancien',
  az: 'A → Z',
  za: 'Z → A',
}

const STATUS_FILTER_LABELS: Record<StatusFilter, string> = {
  all: 'Tous',
  brouillon: 'Brouillon',
  'en-cours': 'En cours',
  complet: 'Complet',
}

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

function FilterPanel({
  sort, onSort, status, onStatus,
}: {
  sort: SortKey
  onSort: (s: SortKey) => void
  status: StatusFilter
  onStatus: (s: StatusFilter) => void
}) {
  return (
    <div
      className="absolute top-[calc(100%+8px)] right-0 z-50 rounded-[14px] p-4 min-w-[220px]"
      style={{
        background: 'linear-gradient(165deg, rgba(248,244,238,.97) 0%, rgba(235,229,220,.95) 100%)',
        backdropFilter: 'var(--glass-blur)',
        WebkitBackdropFilter: 'var(--glass-blur)',
        border: '1px solid rgba(255,255,255,.60)',
        boxShadow: 'var(--shadow-card)',
      }}
    >
      <div className="text-[10px] uppercase tracking-widest text-[#8a8780] mb-2">Trier par</div>
      <div className="flex flex-col gap-0.5 mb-4">
        {(Object.entries(SORT_LABELS) as [SortKey, string][]).map(([key, label]) => (
          <button
            key={key}
            onClick={() => onSort(key)}
            className={`text-left px-2 py-1.5 rounded-[6px] text-[13px] transition-colors bg-transparent border-none cursor-pointer ${
              sort === key ? 'text-[#1a1916] bg-black/[.06] font-medium' : 'text-[#6a6763] hover:bg-black/[.04]'
            }`}
          >
            {label}
          </button>
        ))}
      </div>
      <div className="text-[10px] uppercase tracking-widest text-[#8a8780] mb-2">Statut</div>
      <div className="flex flex-col gap-0.5">
        {(Object.entries(STATUS_FILTER_LABELS) as [StatusFilter, string][]).map(([key, label]) => (
          <button
            key={key}
            onClick={() => onStatus(key)}
            className={`text-left px-2 py-1.5 rounded-[6px] text-[13px] transition-colors bg-transparent border-none cursor-pointer ${
              status === key ? 'text-[#1a1916] bg-black/[.06] font-medium' : 'text-[#6a6763] hover:bg-black/[.04]'
            }`}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  )
}

function sortDossiers(dossiers: Dossier[], sort: SortKey): Dossier[] {
  return [...dossiers].sort((a, b) => {
    if (sort === 'az') return a.address.localeCompare(b.address, 'fr')
    if (sort === 'za') return b.address.localeCompare(a.address, 'fr')
    if (sort === 'oldest') return a.updatedAt.localeCompare(b.updatedAt)
    return b.updatedAt.localeCompare(a.updatedAt) // recent first (default)
  })
}

export default function MesDossiersPage() {
  const router = useRouter()
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState<SortKey>('recent')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [showFilter, setShowFilter] = useState(false)
  const [dossiers, setDossiers] = useState<Dossier[]>([])
  const [loading, setLoading] = useState(true)
  const filterRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchDossiers()
      .then(data => setDossiers(data))
      .finally(() => setLoading(false))
  }, [])

  // Close filter panel on outside click
  useEffect(() => {
    if (!showFilter) return
    function handleClick(e: MouseEvent) {
      if (filterRef.current && !filterRef.current.contains(e.target as Node)) {
        setShowFilter(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [showFilter])

  async function handleSignOut() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push('/login')
  }

  const hasActiveFilter = sort !== 'recent' || statusFilter !== 'all'

  const filtered = sortDossiers(
    dossiers.filter(d => {
      const matchSearch =
        d.address.toLowerCase().includes(search.toLowerCase()) ||
        `${d.property_type} ${d.neighborhood}`.toLowerCase().includes(search.toLowerCase())
      const matchStatus = statusFilter === 'all' || d.status === statusFilter
      return matchSearch && matchStatus
    }),
    sort
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
                {search && (
                  <button
                    onClick={() => setSearch('')}
                    className="text-[#b5b2ac] hover:text-[#8a8780] transition-colors bg-transparent border-none cursor-pointer p-0"
                    aria-label="Effacer la recherche"
                  >
                    <svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                  </button>
                )}
              </div>

              {/* Filter button + panel */}
              <div ref={filterRef} className="relative">
                <button
                  onClick={() => setShowFilter(s => !s)}
                  className={`w-[38px] h-[38px] rounded-full flex items-center justify-center flex-shrink-0 transition-colors cursor-pointer border-none ${
                    hasActiveFilter ? 'text-[#334155]' : 'text-[#8a8780] hover:text-[#1a1916]'
                  }`}
                  style={{
                    background: hasActiveFilter
                      ? 'rgba(51,65,85,.12)'
                      : 'linear-gradient(180deg, rgba(248,244,238,.72) 0%, rgba(235,229,220,.62) 100%)',
                    backdropFilter: 'var(--glass-blur)',
                    WebkitBackdropFilter: 'var(--glass-blur)',
                    border: hasActiveFilter ? '1px solid rgba(51,65,85,.20)' : '1px solid rgba(255,255,255,.55)',
                    boxShadow: 'var(--shadow-glass)',
                  }}
                  title="Trier et filtrer"
                  aria-label="Trier et filtrer"
                  aria-expanded={showFilter}
                >
                  <svg width="15" height="15" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h18M7 12h10M11 20h2"/>
                  </svg>
                </button>
                {showFilter && (
                  <FilterPanel
                    sort={sort}
                    onSort={s => { setSort(s); setShowFilter(false) }}
                    status={statusFilter}
                    onStatus={s => { setStatusFilter(s); setShowFilter(false) }}
                  />
                )}
              </div>
            </div>
          </div>

          {/* Active filters summary */}
          {hasActiveFilter && (
            <div className="flex justify-center mb-4 gap-2 flex-shrink-0">
              {sort !== 'recent' && (
                <span className="inline-flex items-center gap-1.5 text-[11px] text-[#334155] bg-[rgba(51,65,85,.10)] px-3 py-1 rounded-full">
                  {SORT_LABELS[sort]}
                  <button onClick={() => setSort('recent')} className="bg-transparent border-none cursor-pointer p-0 text-[#334155] opacity-60 hover:opacity-100">×</button>
                </span>
              )}
              {statusFilter !== 'all' && (
                <span className="inline-flex items-center gap-1.5 text-[11px] text-[#334155] bg-[rgba(51,65,85,.10)] px-3 py-1 rounded-full">
                  {STATUS_FILTER_LABELS[statusFilter]}
                  <button onClick={() => setStatusFilter('all')} className="bg-transparent border-none cursor-pointer p-0 text-[#334155] opacity-60 hover:opacity-100">×</button>
                </span>
              )}
            </div>
          )}

          {/* Grid */}
          {loading ? (
            <div className="dossier-grid grid gap-4 grid-cols-1">
              {[1, 2, 3].map(i => <SkeletonCard key={i} />)}
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center mt-20">
              <EmptyState
                title={search || hasActiveFilter ? 'Aucun résultat' : 'Aucun dossier'}
                subtitle={search || hasActiveFilter
                  ? 'Aucun dossier ne correspond aux filtres actifs.'
                  : 'Créez un dossier pilote pour lancer les agents.'}
              />
              {!search && !hasActiveFilter && (
                <button
                  onClick={() => router.push('/dossier/nouveau?tab=dossier')}
                  className="mt-5 rounded-full px-5 py-2.5 text-[13px] text-white bg-[#334155] hover:opacity-90 transition-opacity"
                >
                  Nouveau dossier
                </button>
              )}
              {(search || hasActiveFilter) && (
                <button
                  onClick={() => { setSearch(''); setSort('recent'); setStatusFilter('all') }}
                  className="mt-4 text-[13px] text-[#8a8780] hover:text-[#1a1916] transition-colors bg-transparent border-none cursor-pointer"
                >
                  Réinitialiser les filtres
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
