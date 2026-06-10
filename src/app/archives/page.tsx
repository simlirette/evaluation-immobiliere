'use client'

/* Archives — port 1:1 du design handoff (archives.jsx + archives.css). */

import { useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import Dropdown from '@/components/shared/Dropdown'
import { Icon } from '@/components/shared/Icon'
import { formatCAD, fmtNum } from '@/lib/format-number'
import {
  ARCHIVES, TOTAL_ARCHIVES, MANDATE_OPTIONS,
  archiveYear, completedLabel, mandateSlug,
  type DossierArchive,
} from '@/data/archives-mock'
import { createClient } from '@/lib/supabase/client'
import './archives.css'

export default function ArchivesPage() {
  const router = useRouter()
  const all = ARCHIVES

  const [query, setQuery] = useState('')
  const [year, setYear] = useState('all')
  const [mandate, setMandate] = useState('Tous')

  const years = useMemo(
    () => [...new Set(all.map(archiveYear))].sort((a, b) => b.localeCompare(a)),
    [all]
  )

  const filtered = useMemo(() => {
    let arr = all.slice()
    if (year !== 'all')     arr = arr.filter(a => archiveYear(a) === year)
    if (mandate !== 'Tous') arr = arr.filter(a => a.mandate === mandate)
    if (query.trim()) {
      const q = query.trim().toLowerCase()
      arr = arr.filter(a =>
        a.addr.toLowerCase().includes(q) ||
        a.city.toLowerCase().includes(q) ||
        a.client.toLowerCase().includes(q) ||
        a.mandate.toLowerCase().includes(q) ||
        a.id.toLowerCase().includes(q)
      )
    }
    arr.sort((a, b) => b.completedAt.localeCompare(a.completedAt))
    return arr
  }, [all, query, year, mandate])

  const grouped = useMemo(() => {
    const g: Record<string, DossierArchive[]> = {}
    for (const a of filtered) {
      const y = archiveYear(a)
      ;(g[y] = g[y] || []).push(a)
    }
    return g
  }, [filtered])

  const totalValue = useMemo(() => filtered.reduce((s, a) => s + (a.value || 0), 0), [filtered])

  const yearCounts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const a of all) {
      const y = archiveYear(a)
      c[y] = (c[y] || 0) + 1
    }
    return c
  }, [all])

  function clearFilters() { setQuery(''); setYear('all'); setMandate('Tous') }
  const hasFilter = Boolean(query) || year !== 'all' || mandate !== 'Tous'

  async function handleSignOut() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push('/login')
  }

  return (
    <div className="app">
      <Sidebar onSignOut={handleSignOut} />

      <div className="main">
        <div className="topbar arch-topbar">
          <div className="crumbs">
            <span className="today">
              <span className="numeric">{TOTAL_ARCHIVES}</span> dossiers archivés
            </span>
          </div>

          <div className="pagehead arch-head">
            <div>
              <h1>Archives</h1>
              <div className="subtitle">
                Dossiers terminés, classés par année. Consultez, clonez ou exportez vos évaluations passées.
              </div>
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn secondary"><Icon.Print/> Exporter le registre</button>
            </div>
          </div>
        </div>

        <div className="arch-body">
          {/* Filter row */}
          <div className="arch-toolbar">
            <div className="search">
              <Icon.Glass/>
              <input
                type="text"
                placeholder="Rechercher par adresse, client ou nº de dossier…"
                value={query}
                onChange={e => setQuery(e.target.value)}
              />
              {query && <span className="kbd" onClick={() => setQuery('')} style={{ cursor: 'pointer' }}>esc</span>}
            </div>
            <Dropdown
              label="Mandat"
              value={mandate}
              onChange={setMandate}
              options={MANDATE_OPTIONS}
            />
            {hasFilter && (
              <button className="btn ghost" onClick={clearFilters}>Réinitialiser</button>
            )}
          </div>

          {/* Year pills */}
          <div className="year-strip">
            <button
              className={`year-pill ${year === 'all' ? 'active' : ''}`}
              onClick={() => setYear('all')}>
              <span className="y-label">Toutes années</span>
              <span className="y-count numeric">{all.length}</span>
            </button>
            {years.map(y => (
              <button
                key={y}
                className={`year-pill ${year === y ? 'active' : ''}`}
                onClick={() => setYear(y)}>
                <span className="y-label numeric">{y}</span>
                <span className="y-count numeric">{yearCounts[y]}</span>
              </button>
            ))}
          </div>

          {/* Summary card */}
          {filtered.length > 0 && (
            <div className="arch-summary">
              <div>
                <span className="k">Affichage</span>
                <span className="v numeric">{filtered.length}</span>
                <span className="suffix">sur {all.length}</span>
              </div>
              <div>
                <span className="k">Valeur totale évaluée</span>
                <span className="v numeric">{formatCAD(totalValue)}</span>
              </div>
              <div>
                <span className="k">Plus récent</span>
                <span className="v">{completedLabel(filtered[0])}</span>
              </div>
              <div>
                <span className="k">Plus ancien</span>
                <span className="v">{completedLabel(filtered[filtered.length - 1])}</span>
              </div>
            </div>
          )}

          {/* Results — grouped by year */}
          {filtered.length === 0 ? (
            <div className="arch-empty">
              <div className="empty-seal">—</div>
              <h3>Aucune archive ne correspond à ces filtres.</h3>
              <button className="btn secondary" onClick={clearFilters}>Réinitialiser les filtres</button>
            </div>
          ) : (
            <div className="arch-groups">
              {Object.entries(grouped)
                .sort(([a], [b]) => b.localeCompare(a))
                .map(([yr, items]) => (
                <section className="arch-group" key={yr}>
                  <div className="ag-head">
                    <div className="ag-year numeric">{yr}</div>
                    <div className="ag-count">
                      <span className="numeric">{items.length}</span> dossier{items.length > 1 ? 's' : ''}
                    </div>
                  </div>
                  <div className="ag-list">
                    {items.map(a => <ArchiveRow key={a.id} a={a}/>)}
                  </div>
                </section>
              ))}
            </div>
          )}

          {/* Showing N of total */}
          {filtered.length > 0 && filtered.length < TOTAL_ARCHIVES && !hasFilter && (
            <div className="arch-more">
              <span>Affichage de <b className="numeric">{filtered.length}</b> sur <b className="numeric">{TOTAL_ARCHIVES}</b> dossiers archivés</span>
              <button className="btn secondary">Charger plus</button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function ArchiveRow({ a }: { a: DossierArchive }) {
  return (
    <article className="arch-row">
      <div className="ar-date">
        <div className="ar-day numeric">{a.completedAt.slice(8, 10)}</div>
        <div className="ar-month">{completedLabel(a).split(' ')[1]}</div>
      </div>
      <div className="ar-main">
        <div className="ar-addr">{a.addr}</div>
        <div className="ar-meta">
          <span>{a.city}</span>
          <span className="dot-sep">·</span>
          <span>{a.type}</span>
          <span className="dot-sep">·</span>
          <span className="numeric">{a.yearBuilt}</span>
          <span className="dot-sep">·</span>
          <span className="numeric">{fmtNum(a.area)} pi²</span>
        </div>
      </div>
      <div className="ar-mandate">
        <span className={`m-pill mandate-${mandateSlug(a.mandate)}`}>{a.mandate}</span>
      </div>
      <div className="ar-client">{a.client}</div>
      <div className="ar-value numeric">{formatCAD(a.value)}</div>
      <div className="ar-id numeric">{a.id}</div>
      <div className="ar-actions">
        <button className="btn ghost btn-sm">Voir</button>
        <button className="btn ghost btn-sm">Cloner</button>
      </div>
    </article>
  )
}
