'use client'

import { useEffect, useCallback, useState } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import DossierCard from '@/components/dossiers/DossierCard'
import DossierRow from '@/components/dossiers/DossierRow'
import EmptyState from '@/components/shared/EmptyState'
import ContextMenu from '@/components/layout/ContextMenu'
import Toast from '@/components/shared/Toast'
import { fetchRuntimeDossiers, deleteRuntimeDossier, renameRuntimeDossier, toggleRuntimePin, createRuntimeDossier } from '@/lib/runtime-api'
import { useContextMenu } from '@/hooks/useContextMenu'
import { sortDossiers, type SortKey } from '@/lib/sort-dossiers'
import { filterDossiers, type StatusFilter } from '@/lib/filter-dossiers'
import { createClient } from '@/lib/supabase/client'
import type { Dossier } from '@/types'

const SORT_LABELS: Record<SortKey, string> = {
  recent: 'Modifié récemment',
  oldest: 'Plus ancien',
  az: 'Adresse (A–Z)',
  za: 'Adresse (Z–A)',
}

const STATUS_FILTER_LABELS: Record<StatusFilter, string> = {
  all: 'Tous',
  brouillon: 'Brouillons',
  'en-cours': 'En cours',
  complet: 'Complets',
}

function SkeletonCard() {
  return (
    <div
      className="skeleton-shimmer rounded-[var(--r-lg)] border border-[var(--rule)] h-[196px]"
    />
  )
}

export default function MesDossiersPage() {
  const router = useRouter()
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState<SortKey>('recent')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [view, setView] = useState<'grid' | 'list'>('grid')
  const [dossiers, setDossiers] = useState<Dossier[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [toast, setToast] = useState<string | null>(null)
  const dismissToast = useCallback(() => setToast(null), [])
  const ctx = useContextMenu()

  useEffect(() => {
    fetchRuntimeDossiers()
      .then(data => { setDossiers(data); setLoading(false) })
      .catch(() => { setError(true); setLoading(false) })
  }, [])

  function handlePin(name: string, pinned: boolean) {
    const d = dossiers.find(x => x.address === name)
    if (!d) return
    setDossiers(prev => prev.map(x => x.address === name ? { ...x, pinned: !pinned } : x))
    toggleRuntimePin(d.slug, pinned)
    setToast(pinned ? 'Dossier désépinglé' : 'Dossier épinglé')
  }

  function handleRename(name: string, newName: string) {
    const d = dossiers.find(x => x.address === name)
    if (!d) return
    setDossiers(prev => prev.map(x => x.address === name ? { ...x, address: newName } : x))
    renameRuntimeDossier(d.slug, newName)
    setToast('Dossier renommé')
  }

  async function handleDuplicate(name: string) {
    const d = dossiers.find(x => x.address === name)
    if (!d) return
    setToast('Duplication en cours…')
    try {
      const newD = await createRuntimeDossier({
        address: `Copie de ${d.address}`,
        property_type: d.property_type,
        neighborhood: d.neighborhood,
      })
      setDossiers(prev => [newD, ...prev])
      setToast('Dossier dupliqué')
      router.push(`/dossier/${newD.slug}?tab=dossier`)
    } catch {
      setToast('Erreur lors de la duplication')
    }
  }

  function handleDelete(name: string) {
    const d = dossiers.find(x => x.address === name)
    if (!d) return
    setDossiers(prev => prev.filter(x => x.address !== name))
    deleteRuntimeDossier(d.slug)
    setToast('Dossier supprimé')
  }

  async function handleSignOut() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push('/login')
  }

  const hasActiveFilter = sort !== 'recent' || statusFilter !== 'all' || search.trim() !== ''
  const filtered = sortDossiers(filterDossiers(dossiers, search, statusFilter), sort)

  return (
    <div className="relative w-full h-screen overflow-hidden flex" style={{ background: 'var(--paper)' }}>
      <Sidebar onSignOut={handleSignOut} />

      <div className="main-content flex flex-col overflow-hidden">
        {/* Topbar */}
        <div className="topbar pb-4">
          <div className="flex items-end justify-between">
            <h1 className="page-h1">Dossiers</h1>
            <div className="flex gap-2 pb-1">
              <button className="btn secondary btn-sm">Importer</button>
              <button
                className="btn accent btn-sm"
                onClick={() => router.push('/dossier/nouveau')}
              >
                + Nouveau dossier
              </button>
            </div>
          </div>
        </div>

        {/* Toolbar */}
        <div
          className="flex items-center gap-3 px-10 py-3 flex-shrink-0 border-b"
          style={{ borderBottomColor: 'var(--rule-soft)' }}
        >
          {/* Search */}
          <div className="relative flex-1 max-w-[360px]">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none"
              width="14" height="14" viewBox="0 0 14 14" fill="none"
              aria-hidden="true" style={{ color: 'var(--ink-faint)' }}
            >
              <circle cx="6" cy="6" r="4.5" stroke="currentColor" strokeWidth="1.4"/>
              <path d="M9.5 9.5l3 3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
            </svg>
            <input
              type="search"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Rechercher par adresse…"
              className="w-full pl-9 pr-4 py-2 text-[13.5px] border focus:outline-none transition-colors"
              style={{
                borderRadius: 'var(--r-pill)',
                borderColor: 'var(--rule)',
                fontFamily: 'var(--font-sans)',
                color: 'var(--ink)',
                background: 'var(--paper-hi)',
              }}
              onFocus={e => (e.currentTarget.style.borderColor = 'var(--ink-mute)')}
              onBlur={e => (e.currentTarget.style.borderColor = 'var(--rule)')}
            />
          </div>

          {/* Filter pills */}
          <div className="flex gap-1">
            {(Object.keys(STATUS_FILTER_LABELS) as StatusFilter[]).map(f => (
              <button
                key={f}
                onClick={() => setStatusFilter(f)}
                className={`pill text-[12px] py-1.5 px-3 ${statusFilter === f ? 'active' : ''}`}
              >
                {STATUS_FILTER_LABELS[f]}
              </button>
            ))}
          </div>

          <div className="ml-auto flex items-center gap-2">
            {/* Sort */}
            <select
              value={sort}
              onChange={e => setSort(e.target.value as SortKey)}
              className="text-[13px] px-3 py-1.5 border cursor-pointer focus:outline-none"
              style={{
                borderRadius: 'var(--r-md)',
                borderColor: 'var(--rule)',
                color: 'var(--ink-3)',
                fontFamily: 'var(--font-sans)',
                background: 'var(--paper-hi)',
              }}
            >
              {(Object.keys(SORT_LABELS) as SortKey[]).map(k => (
                <option key={k} value={k}>{SORT_LABELS[k]}</option>
              ))}
            </select>

            {/* View toggle */}
            <div
              className="flex border overflow-hidden"
              style={{ borderRadius: 'var(--r-md)', borderColor: 'var(--rule)' }}
            >
              <button
                onClick={() => setView('grid')}
                aria-pressed={view === 'grid'}
                className="px-3 py-1.5 cursor-pointer border-none transition-colors"
                style={{
                  background: view === 'grid' ? 'var(--ink)' : 'var(--paper-hi)',
                  color: view === 'grid' ? 'var(--paper-hi)' : 'var(--ink-mute)',
                }}
              >
                <svg width="13" height="13" viewBox="0 0 13 13" fill="currentColor" aria-hidden="true">
                  <rect x="0" y="0" width="5.5" height="5.5"/>
                  <rect x="7.5" y="0" width="5.5" height="5.5"/>
                  <rect x="0" y="7.5" width="5.5" height="5.5"/>
                  <rect x="7.5" y="7.5" width="5.5" height="5.5"/>
                </svg>
              </button>
              <button
                onClick={() => setView('list')}
                aria-pressed={view === 'list'}
                className="px-3 py-1.5 cursor-pointer border-none border-l transition-colors"
                style={{
                  borderLeftColor: 'var(--rule)',
                  background: view === 'list' ? 'var(--ink)' : 'var(--paper-hi)',
                  color: view === 'list' ? 'var(--paper-hi)' : 'var(--ink-mute)',
                }}
              >
                <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                  <path d="M0 2h13M0 6.5h13M0 11h13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto">
          <div className="px-10 pt-6 pb-16">
            {error ? (
              <div className="flex flex-col items-center justify-center mt-20">
                <EmptyState
                  title="Erreur de chargement"
                  subtitle="Impossible de récupérer les dossiers. Vérifiez votre connexion."
                />
                <button
                  onClick={() => {
                    setError(false); setLoading(true)
                    fetchRuntimeDossiers()
                      .then(data => { setDossiers(data); setLoading(false) })
                      .catch(() => { setError(true); setLoading(false) })
                  }}
                  className="btn accent btn-sm mt-5"
                >
                  Réessayer
                </button>
              </div>
            ) : loading ? (
              <div className="dossier-card-grid">
                {[1, 2, 3, 4, 5, 6].map(i => <SkeletonCard key={i} />)}
              </div>
            ) : filtered.length === 0 ? (
              <div className="flex flex-col items-center justify-center mt-20">
                <EmptyState
                  title={hasActiveFilter ? 'Aucun résultat' : 'Aucun dossier'}
                  subtitle={hasActiveFilter
                    ? 'Aucun dossier ne correspond aux filtres actifs.'
                    : 'Créez votre premier dossier pour commencer.'}
                />
                {!hasActiveFilter && (
                  <button
                    onClick={() => router.push('/dossier/nouveau')}
                    className="btn accent btn-sm mt-5"
                  >
                    Nouveau dossier
                  </button>
                )}
                {hasActiveFilter && (
                  <button
                    onClick={() => { setSearch(''); setSort('recent'); setStatusFilter('all') }}
                    className="btn ghost btn-sm mt-4"
                  >
                    Réinitialiser les filtres
                  </button>
                )}
              </div>
            ) : view === 'grid' ? (
              <div className="dossier-card-grid">
                {filtered.map((d, i) => (
                  <DossierCard
                    key={d.id}
                    dossier={d}
                    onClick={() => router.push(`/dossier/${d.slug}?tab=dossier`)}
                    onContextMenu={e => ctx.open(e, d.address, d.pinned)}
                    index={i}
                  />
                ))}
              </div>
            ) : (
              /* List view */
              <div
                className="rounded-[var(--r-lg)] border border-[var(--rule)] overflow-hidden"
                style={{ background: 'var(--paper-hi)' }}
              >
                {/* List header */}
                <div
                  className="grid px-5 py-2.5 text-[11px] font-medium uppercase tracking-[.04em]"
                  style={{
                    gridTemplateColumns: '2fr 140px 100px 80px 1fr 140px',
                    gap: '1rem',
                    color: 'var(--ink-faint)',
                    borderBottom: '1px solid var(--rule-soft)',
                    background: 'var(--paper)',
                  }}
                >
                  <span>Adresse</span>
                  <span>Type</span>
                  <span>Statut</span>
                  <span>Stade</span>
                  <span>Client</span>
                  <span className="text-right">Modifié</span>
                </div>
                {filtered.map(d => (
                  <DossierRow
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

      <ContextMenu
        target={ctx.target}
        onClose={ctx.close}
        onPin={handlePin}
        onRename={handleRename}
        onDuplicate={handleDuplicate}
        onDelete={handleDelete}
      />
      <Toast message={toast} onDismiss={dismissToast} />
    </div>
  )
}
