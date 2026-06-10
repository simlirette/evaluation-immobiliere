'use client'

/* Dossiers — port 1:1 du design handoff (mes-dossiers.jsx).
   Données réelles (runtime) ; tri valeur/année/superficie sans effet tant que
   la liste backend n'expose pas ces champs. */

import { useEffect, useCallback, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import DossierCard, { formatPropertyType } from '@/components/dossiers/DossierCard'
import DossierRow from '@/components/dossiers/DossierRow'
import ContextMenu from '@/components/layout/ContextMenu'
import Toast from '@/components/shared/Toast'
import { Icon } from '@/components/shared/Icon'
import { fetchRuntimeDossiers, deleteRuntimeDossier, renameRuntimeDossier, toggleRuntimePin, createRuntimeDossier } from '@/lib/runtime-api'
import { useContextMenu } from '@/hooks/useContextMenu'
import { createClient } from '@/lib/supabase/client'
import type { Dossier, DossierStatus } from '@/types'

type StatusFilter = 'all' | DossierStatus
type SortKey = 'modified' | 'created' | 'alpha' | 'value' | 'type' | 'year' | 'area' | 'stage' | 'client'

export default function MesDossiersPage() {
  const router = useRouter()
  const [query, setQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [sort, setSort] = useState<SortKey>('modified')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [view, setView] = useState<'grid' | 'rows'>('grid')
  const [dossiers, setDossiers] = useState<Dossier[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [toast, setToast] = useState<string | null>(null)
  const dismissToast = useCallback(() => setToast(null), [])
  const ctx = useContextMenu()

  function load() {
    setError(false)
    setLoading(true)
    fetchRuntimeDossiers()
      .then(data => { setDossiers(data); setLoading(false) })
      .catch(() => { setError(true); setLoading(false) })
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { load() }, [])

  const counts = useMemo(() => {
    const c = { all: dossiers.length, brouillon: 0, 'en-cours': 0, complet: 0 }
    for (const d of dossiers) c[d.status]++
    return c
  }, [dossiers])

  const filtered = useMemo(() => {
    let arr = dossiers.slice()
    if (statusFilter !== 'all') arr = arr.filter(d => d.status === statusFilter)
    if (query.trim()) {
      const q = query.trim().toLowerCase()
      arr = arr.filter(d =>
        d.address.toLowerCase().includes(q) ||
        d.neighborhood.toLowerCase().includes(q) ||
        formatPropertyType(d.property_type).toLowerCase().includes(q) ||
        d.id.toLowerCase().includes(q)
      )
    }
    arr.sort((a, b) => {
      // épinglés d'abord, quel que soit le tri (comportement design)
      if (a.pinned !== b.pinned) return a.pinned ? -1 : 1
      const dir = sortDir === 'asc' ? 1 : -1
      const cmpStr = (x: string, y: string) => (x || '').localeCompare(y || '', 'fr-CA')
      switch (sort) {
        case 'alpha':  return cmpStr(a.address, b.address) * (sortDir === 'asc' ? 1 : -1)
        case 'type':   return cmpStr(a.property_type, b.property_type) * (sortDir === 'asc' ? 1 : -1)
        case 'client': return cmpStr(a.neighborhood, b.neighborhood) * (sortDir === 'asc' ? 1 : -1)
        case 'modified':
        case 'created':
        case 'value':
        case 'year':
        case 'area':
        case 'stage':
        default:       return cmpStr(a.updatedAt, b.updatedAt) * dir
      }
    })
    return arr
  }, [dossiers, query, statusFilter, sort, sortDir])

  function onSort(key: SortKey) {
    if (sort === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSort(key)
      setSortDir(['alpha', 'type', 'client'].includes(key) ? 'asc' : 'desc')
    }
  }

  function onPin(d: Dossier) {
    setDossiers(ds => ds.map(x => x.id === d.id ? { ...x, pinned: !x.pinned } : x))
    toggleRuntimePin(d.slug, d.pinned)
    setToast(d.pinned ? 'Dossier désépinglé' : 'Dossier épinglé')
  }

  function handlePin(name: string, pinned: boolean) {
    const d = dossiers.find(x => x.address === name)
    if (d) onPin(d)
    void pinned
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

  function clearFilters() {
    setQuery('')
    setStatusFilter('all')
  }

  async function handleSignOut() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push('/login')
  }

  const todayStr = new Date().toLocaleDateString('fr-CA', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
  })

  return (
    <div className="app">
      <Sidebar onSignOut={handleSignOut} />

      <div className="main">
        {/* Page head */}
        <div className="topbar">
          <div className="crumbs">
            <span className="today">{todayStr}</span>
          </div>
          <div className="pagehead">
            <div>
              <h1>Dossiers</h1>
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn secondary">Importer un dossier</button>
              <button className="btn accent" onClick={() => router.push('/dossier/nouveau')}>
                <Icon.Plus/> Nouveau dossier
              </button>
            </div>
          </div>
        </div>

        {/* Toolbar */}
        <div className="toolbar">
          <div className="search">
            <Icon.Glass/>
            <input
              type="text"
              placeholder="Rechercher par adresse, quartier, client ou nº de dossier…"
              value={query}
              onChange={e => setQuery(e.target.value)}
            />
            {query && <span className="kbd" onClick={() => setQuery('')} style={{ cursor: 'pointer' }}>esc</span>}
          </div>

          <div className="filter-pills">
            <button className={`pill ${statusFilter === 'all' ? 'active' : ''}`} onClick={() => setStatusFilter('all')}>
              <span>Tous</span><span className="count">{counts.all}</span>
            </button>
            <button className={`pill ${statusFilter === 'en-cours' ? 'active' : ''}`} onClick={() => setStatusFilter('en-cours')}>
              <span>En cours</span><span className="count">{counts['en-cours']}</span>
            </button>
            <button className={`pill ${statusFilter === 'complet' ? 'active' : ''}`} onClick={() => setStatusFilter('complet')}>
              <span>Complets</span><span className="count">{counts.complet}</span>
            </button>
            <button className={`pill ${statusFilter === 'brouillon' ? 'active' : ''}`} onClick={() => setStatusFilter('brouillon')}>
              <span>Brouillons</span><span className="count">{counts.brouillon}</span>
            </button>
          </div>

          <div className="sort-select">
            <span className="label">Trier par</span>
            <select value={sort} onChange={e => setSort(e.target.value as SortKey)}>
              <option value="modified">Modifié récemment</option>
              <option value="created">Créé récemment</option>
              <option value="alpha">Adresse (A–Z)</option>
              <option value="value">Valeur (décroissant)</option>
            </select>
          </div>

          <div className="view-toggle">
            <button className={view === 'grid' ? 'active' : ''} title="Vue en grille" onClick={() => setView('grid')}>
              <Icon.Grid/>
            </button>
            <button className={view === 'rows' ? 'active' : ''} title="Vue en liste" onClick={() => setView('rows')}>
              <Icon.Rows/>
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="grid-wrap">
          {loading && <LoadingState/>}
          {!loading && error && <ErrorState onRetry={load}/>}
          {!loading && !error && dossiers.length === 0 && (
            <EmptyState onNew={() => router.push('/dossier/nouveau')}/>
          )}
          {!loading && !error && dossiers.length > 0 && (
            filtered.length === 0 ? (
              <NoResultsState query={query} onClear={clearFilters}/>
            ) : (
              <div className={view === 'grid' ? 'card-grid' : 'card-list'}>
                {view === 'rows' && (
                  <div className="list-head">
                    <SortHead k="alpha"    sort={sort} dir={sortDir} onSort={onSort}>Adresse</SortHead>
                    <SortHead k="type"     sort={sort} dir={sortDir} onSort={onSort}>Type</SortHead>
                    <SortHead k="year"     sort={sort} dir={sortDir} onSort={onSort}>Année</SortHead>
                    <SortHead k="area"     sort={sort} dir={sortDir} onSort={onSort}>Superficie</SortHead>
                    <SortHead k="stage"    sort={sort} dir={sortDir} onSort={onSort}>Stade / Valeur</SortHead>
                    <SortHead k="client"   sort={sort} dir={sortDir} onSort={onSort}>Client</SortHead>
                    <SortHead k="modified" sort={sort} dir={sortDir} onSort={onSort}>Modifié</SortHead>
                    <div></div>
                  </div>
                )}
                {filtered.map(d => view === 'grid'
                  ? <DossierCard key={d.id} dossier={d} onPin={onPin}
                      onClick={() => router.push(`/dossier/${d.slug}?tab=dossier`)}
                      onContextMenu={e => ctx.open(e, d.address, d.pinned)}/>
                  : <DossierRow key={d.id} dossier={d} onPin={onPin}
                      onClick={() => router.push(`/dossier/${d.slug}?tab=dossier`)}
                      onContextMenu={e => ctx.open(e, d.address, d.pinned)}/>
                )}
              </div>
            )
          )}
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

/* ── Sortable list-head cell ── */
function SortHead({ k, sort, dir, onSort, children }: {
  k: SortKey
  sort: SortKey
  dir: 'asc' | 'desc'
  onSort: (k: SortKey) => void
  children: React.ReactNode
}) {
  const active = sort === k
  return (
    <button
      type="button"
      className={`sort-head ${active ? 'active' : ''}`}
      onClick={() => onSort(k)}>
      <span>{children}</span>
      <span className={`caret ${active ? (dir === 'asc' ? 'asc' : 'desc') : ''}`}>
        <svg viewBox="0 0 10 6" width="9" height="6" aria-hidden="true">
          <path d="M0 1l5 4 5-4" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </span>
    </button>
  )
}

/* ── State views (design handoff) ── */
function LoadingState() {
  return (
    <div className="skeleton-grid">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="skeleton-card">
          <div className="body">
            <div className="line w2"/>
            <div className="line w1"/>
            <div className="line w3"/>
            <div style={{ height: 8 }}/>
            <div className="line w2"/>
          </div>
        </div>
      ))}
    </div>
  )
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="state">
      <div className="seal" style={{ background: 'rgba(138,48,48,.08)', color: 'var(--oxblood)' }}>!</div>
      <h2>Connexion <em style={{ color: 'var(--oxblood)' }}>interrompue</em></h2>
      <p>
        Le serveur d&apos;évaluation n&apos;a pas répondu. Vos dossiers locaux sont
        intacts ; seule la synchronisation est en pause.
      </p>
      <div className="actions">
        <button className="btn" onClick={onRetry}>Réessayer la connexion</button>
        <button className="btn secondary">Travailler hors ligne</button>
      </div>
    </div>
  )
}

function EmptyState({ onNew }: { onNew: () => void }) {
  return (
    <div className="state">
      <div className="seal">É.A.</div>
      <h2>Aucun dossier <em>ouvert</em>.</h2>
      <p>
        Commencez votre premier dossier d&apos;évaluation. Vous pourrez importer les
        données du rôle d&apos;évaluation ou saisir manuellement les caractéristiques de la propriété.
      </p>
      <div className="actions">
        <button className="btn accent" onClick={onNew}><Icon.Plus/> Nouveau dossier</button>
        <button className="btn secondary">Importer depuis le rôle</button>
      </div>
    </div>
  )
}

function NoResultsState({ query, onClear }: { query: string; onClear: () => void }) {
  return (
    <div className="state" style={{ padding: '60px 40px' }}>
      <div className="seal" style={{ width: 72, height: 72, fontSize: 14 }}>—</div>
      <h2>Aucun résultat</h2>
      <p>
        Aucun dossier ne correspond à
        {query ? <> «&nbsp;<i style={{ color: 'var(--ink)' }}>{query}</i>&nbsp;»</> : ' ces filtres'}.
        Essayez d&apos;élargir votre recherche ou de retirer un filtre.
      </p>
      <div className="actions">
        <button className="btn secondary" onClick={onClear}>Réinitialiser les filtres</button>
      </div>
    </div>
  )
}
