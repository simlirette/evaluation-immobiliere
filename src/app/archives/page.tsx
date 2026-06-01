'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import Toast from '@/components/shared/Toast'
import { createClient } from '@/lib/supabase/client'
import { ARCHIVES, groupByYear, getYears } from '@/data/archives-mock'
import type { DossierArchive } from '@/data/archives-mock'

function formatCAD(v: number): string {
  return new Intl.NumberFormat('fr-CA', {
    style: 'currency',
    currency: 'CAD',
    maximumFractionDigits: 0,
  }).format(v)
}

function formatDate(iso: string): string {
  const [y, m, d] = iso.split('-')
  const months = ['jan', 'fév', 'mar', 'avr', 'mai', 'jun', 'jul', 'aoû', 'sep', 'oct', 'nov', 'déc']
  return `${parseInt(d)} ${months[parseInt(m) - 1]}. ${y}`
}

const COL_TEMPLATE = '120px 2fr 120px 120px 130px 120px'

function TableHeader() {
  return (
    <div
      className="grid items-center px-5 py-2.5 text-[11px] font-medium uppercase tracking-[.06em]"
      style={{
        gridTemplateColumns: COL_TEMPLATE,
        gap: '1rem',
        color: 'var(--ink-faint)',
        background: 'var(--paper)',
        borderBottom: '1px solid var(--rule-soft)',
      }}
    >
      <span>Date</span>
      <span>Adresse</span>
      <span>Type</span>
      <span>Valeur</span>
      <span>Client</span>
      <span>Évaluateur</span>
    </div>
  )
}

function ArchiveRow({ dossier, isLast }: { dossier: DossierArchive; isLast: boolean }) {
  const router = useRouter()
  return (
    <div
      className="grid items-center px-5 py-3 cursor-pointer transition-colors"
      role="button"
      tabIndex={0}
      onClick={() => router.push(`/dossier/${dossier.id}`)}
      onKeyDown={e => e.key === 'Enter' && router.push(`/dossier/${dossier.id}`)}
      style={{
        gridTemplateColumns: COL_TEMPLATE,
        gap: '1rem',
        borderBottom: isLast ? 'none' : '1px solid var(--rule-soft)',
      }}
      onMouseEnter={e => (e.currentTarget.style.background = 'var(--paper-2)')}
      onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
    >
      {/* Date */}
      <span
        style={{
          fontSize: '12px',
          color: 'var(--ink-faint)',
          fontFamily: 'var(--font-sans)',
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        {formatDate(dossier.dateCompletion)}
      </span>

      {/* Adresse + ville */}
      <div>
        <p
          className="font-medium leading-snug"
          style={{ color: 'var(--ink)', fontFamily: 'var(--font-sans)', fontSize: '13.5px' }}
        >
          {dossier.adresse}
        </p>
        <p
          className="leading-snug"
          style={{ color: 'var(--ink-faint)', fontSize: '12px', fontFamily: 'var(--font-sans)' }}
        >
          {dossier.ville} · {dossier.mandat}
        </p>
      </div>

      {/* Type badge */}
      <div>
        <span
          className="pill"
          style={{
            fontSize: '11px',
            padding: '2px 8px',
            border: '1px solid var(--rule)',
            color: 'var(--ink-faint)',
            background: 'transparent',
            borderRadius: 'var(--r-pill)',
            fontFamily: 'var(--font-sans)',
            whiteSpace: 'nowrap',
          }}
        >
          {dossier.type}
        </span>
      </div>

      {/* Valeur */}
      <span
        className="font-semibold"
        style={{
          color: 'var(--navy)',
          fontFamily: 'var(--font-sans)',
          fontSize: '13.5px',
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        {formatCAD(dossier.valeur)}
      </span>

      {/* Client */}
      <span
        style={{
          color: 'var(--ink-mute)',
          fontSize: '13px',
          fontFamily: 'var(--font-sans)',
        }}
      >
        {dossier.client}
      </span>

      {/* Évaluateur */}
      <span
        style={{
          color: 'var(--ink-faint)',
          fontSize: '12px',
          fontFamily: 'var(--font-sans)',
        }}
      >
        {dossier.evaluateur}
      </span>
    </div>
  )
}

export default function ArchivesPage() {
  const router = useRouter()
  const [search, setSearch] = useState('')
  const [selectedYear, setSelectedYear] = useState<number | null>(null)
  const [toast, setToast] = useState<string | null>(null)

  async function handleSignOut() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push('/login')
  }

  // Filter
  const filtered = ARCHIVES.filter(d => {
    const matchSearch =
      !search ||
      [d.adresse, d.client, d.id, d.ville].some(v =>
        v.toLowerCase().includes(search.toLowerCase())
      )
    const matchYear =
      selectedYear === null || parseInt(d.dateCompletion.slice(0, 4)) === selectedYear
    return matchSearch && matchYear
  })

  // Stats
  const totalValeur = filtered.reduce((sum, d) => sum + d.valeur, 0)
  const years = getYears(ARCHIVES)

  const dateRange = (() => {
    if (filtered.length === 0) return null
    const sorted = [...filtered].sort((a, b) => a.dateCompletion.localeCompare(b.dateCompletion))
    const earliest = sorted[0].dateCompletion.slice(0, 4)
    const latest = sorted[sorted.length - 1].dateCompletion.slice(0, 4)
    return earliest === latest ? earliest : `${earliest} – ${latest}`
  })()

  // Group by year descending
  const grouped = groupByYear(filtered)
  const groupedYears = Object.keys(grouped)
    .map(Number)
    .sort((a, b) => b - a)

  return (
    <div
      className="relative w-full h-screen overflow-hidden flex"
      style={{ background: 'var(--paper)' }}
    >
      <Sidebar onSignOut={handleSignOut} />

      <div className="main-content flex flex-col overflow-hidden">
        {/* Topbar */}
        <div className="topbar pb-4">
          <div className="flex items-end justify-between">
            <div>
              <h1 className="page-h1">Archives</h1>
              <p
                className="eyebrow mt-0.5"
                style={{ color: 'var(--ink-faint)', fontFamily: 'var(--font-sans)', fontSize: '12px' }}
              >
                Dossiers complétés · OEAQ
              </p>
            </div>
          </div>
        </div>

        {/* Toolbar: search + year pills */}
        <div
          className="flex items-center gap-3 px-10 py-3 flex-shrink-0 border-b flex-wrap"
          style={{ borderBottomColor: 'var(--rule-soft)' }}
        >
          {/* Search */}
          <div className="relative" style={{ width: '320px' }}>
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none"
              width="14"
              height="14"
              viewBox="0 0 14 14"
              fill="none"
              aria-hidden="true"
              style={{ color: 'var(--ink-faint)' }}
            >
              <circle cx="6" cy="6" r="4.5" stroke="currentColor" strokeWidth="1.4" />
              <path d="M9.5 9.5l3 3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
            </svg>
            <input
              type="search"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Rechercher par adresse, client, numéro…"
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

          {/* Year pills */}
          <div className="flex gap-1 flex-wrap">
            <button
              onClick={() => setSelectedYear(null)}
              className={`pill text-[12px] py-1.5 px-3 ${selectedYear === null ? 'active' : ''}`}
            >
              Tous
            </button>
            {years.map(y => {
              const count = ARCHIVES.filter(d => parseInt(d.dateCompletion.slice(0, 4)) === y).length
              return (
                <button
                  key={y}
                  onClick={() => setSelectedYear(y)}
                  className={`pill text-[12px] py-1.5 px-3 ${selectedYear === y ? 'active' : ''}`}
                >
                  {y}
                  <span
                    className="ml-1.5"
                    style={{
                      fontSize: '10px',
                      opacity: 0.6,
                      fontVariantNumeric: 'tabular-nums',
                    }}
                  >
                    {count}
                  </span>
                </button>
              )
            })}
          </div>

          {/* Summary stats */}
          {filtered.length > 0 && (
            <div
              className="ml-auto flex items-center gap-4 text-[12px]"
              style={{ color: 'var(--ink-faint)', fontFamily: 'var(--font-sans)' }}
            >
              <span>
                <span style={{ color: 'var(--ink-mute)', fontWeight: 500 }}>{filtered.length}</span>{' '}
                dossier{filtered.length !== 1 ? 's' : ''}
              </span>
              <span
                style={{
                  width: '1px',
                  height: '14px',
                  background: 'var(--rule)',
                  display: 'inline-block',
                  verticalAlign: 'middle',
                }}
              />
              <span>
                <span style={{ color: 'var(--navy)', fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
                  {formatCAD(totalValeur)}
                </span>{' '}
                total
              </span>
              {dateRange && (
                <>
                  <span
                    style={{
                      width: '1px',
                      height: '14px',
                      background: 'var(--rule)',
                      display: 'inline-block',
                      verticalAlign: 'middle',
                    }}
                  />
                  <span>{dateRange}</span>
                </>
              )}
            </div>
          )}
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto">
          <div className="px-10 pt-6 pb-16">
            {filtered.length === 0 ? (
              /* Empty state */
              <div className="flex flex-col items-center justify-center mt-24">
                <div
                  className="w-12 h-12 rounded-full flex items-center justify-center mb-4"
                  style={{ background: 'var(--paper-2)', border: '1px solid var(--rule)' }}
                >
                  <svg
                    width="22"
                    height="22"
                    viewBox="0 0 22 22"
                    fill="none"
                    aria-hidden="true"
                    style={{ color: 'var(--ink-faint)' }}
                  >
                    <rect x="3" y="5" width="16" height="14" rx="2" stroke="currentColor" strokeWidth="1.4" />
                    <path d="M7 3h8M9 9h4M7 13h8" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
                  </svg>
                </div>
                <p
                  className="font-medium"
                  style={{
                    fontFamily: 'var(--font-serif)',
                    fontSize: '17px',
                    color: 'var(--ink)',
                    marginBottom: '6px',
                  }}
                >
                  Aucun dossier archivé
                </p>
                <p
                  style={{
                    fontSize: '13px',
                    color: 'var(--ink-faint)',
                    fontFamily: 'var(--font-sans)',
                  }}
                >
                  {search || selectedYear !== null
                    ? 'Aucun dossier ne correspond aux filtres actifs.'
                    : 'Les dossiers complétés apparaîtront ici.'}
                </p>
                {(search || selectedYear !== null) && (
                  <button
                    className="btn ghost btn-sm mt-5"
                    onClick={() => { setSearch(''); setSelectedYear(null) }}
                  >
                    Réinitialiser les filtres
                  </button>
                )}
              </div>
            ) : (
              /* Grouped list */
              <div className="flex flex-col gap-8">
                {groupedYears.map(year => {
                  const rows = grouped[year]
                  return (
                    <div key={year}>
                      {/* Year heading */}
                      <h2
                        className="mb-3"
                        style={{
                          fontFamily: 'var(--font-serif)',
                          fontSize: '20px',
                          color: 'var(--ink)',
                          fontWeight: 400,
                          letterSpacing: '0.01em',
                        }}
                      >
                        {year}
                      </h2>

                      {/* Panel */}
                      <div
                        className="panel overflow-hidden"
                        style={{
                          padding: 0,
                          border: '1px solid var(--rule)',
                          borderRadius: 'var(--r-lg)',
                        }}
                      >
                        <TableHeader />
                        {rows.map((d, i) => (
                          <ArchiveRow key={d.id} dossier={d} isLast={i === rows.length - 1} />
                        ))}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      <Toast message={toast} onDismiss={() => setToast(null)} />
    </div>
  )
}
