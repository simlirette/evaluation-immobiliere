'use client'

import { useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import { createClient } from '@/lib/supabase/client'
import { VENTES, MARCHES, COUTS, TAUX } from '@/data/bibliotheque-mock'
import type { VenteMock, MarcheMock, CoutMock, TauxMock } from '@/data/bibliotheque-mock'

type Tab = 'ventes' | 'marches' | 'couts' | 'taux'

const TAB_LABELS: Record<Tab, string> = {
  ventes: 'Ventes',
  marches: 'Marchés',
  couts: 'Coûts',
  taux: 'Taux',
}

function formatPrix(n: number) {
  return new Intl.NumberFormat('fr-CA', { style: 'currency', currency: 'CAD', maximumFractionDigits: 0 }).format(n)
}

function formatNum(n: number) {
  return new Intl.NumberFormat('fr-CA').format(n)
}

function medianOf(nums: number[]) {
  if (nums.length === 0) return 0
  const sorted = [...nums].sort((a, b) => a - b)
  const mid = Math.floor(sorted.length / 2)
  return sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid]
}

// ─── Ventes ──────────────────────────────────────────────────────────────────

function VentesTab() {
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim()
    if (!q) return VENTES
    return VENTES.filter(
      v =>
        v.adresse.toLowerCase().includes(q) ||
        v.arrondissement.toLowerCase().includes(q),
    )
  }, [search])

  const medianPrix = medianOf(filtered.map(v => v.prix))

  return (
    <div>
      {/* Search + stats row */}
      <div
        className="flex items-center gap-4 px-10 py-4 flex-shrink-0"
        style={{ borderBottom: '1px solid var(--rule-soft)' }}
      >
        <div className="relative flex-1 max-w-[380px]">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none"
            width="14" height="14" viewBox="0 0 14 14" fill="none"
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
            placeholder="Filtrer par adresse ou arrondissement…"
            className="field w-full pl-9"
            style={{ borderRadius: 'var(--r-pill)' }}
          />
        </div>

        <div
          className="flex items-center gap-5 text-[13px] ml-auto"
          style={{ color: 'var(--ink-mute)' }}
        >
          <span>
            <span style={{ color: 'var(--ink)', fontWeight: 600 }}>{filtered.length}</span>
            {' '}vente{filtered.length !== 1 ? 's' : ''}
          </span>
          {filtered.length > 0 && (
            <span>
              Médiane{' '}
              <span
                style={{
                  color: 'var(--navy)',
                  fontWeight: 600,
                  fontVariantNumeric: 'tabular-nums lining-nums',
                }}
              >
                {formatPrix(medianPrix)}
              </span>
            </span>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        {/* Header */}
        <div
          className="grid px-10 py-2.5 text-[11px] font-medium uppercase tracking-[.05em]"
          style={{
            gridTemplateColumns: '2.5fr 1.4fr 100px 60px 90px 1fr 120px',
            gap: '1rem',
            color: 'var(--ink-faint)',
            borderBottom: '1px solid var(--rule-soft)',
            background: 'var(--paper)',
          }}
        >
          <span>Adresse</span>
          <span>Arrondissement</span>
          <span>Type</span>
          <span>Année</span>
          <span>Superficie</span>
          <span style={{ textAlign: 'right' }}>Prix</span>
          <span style={{ textAlign: 'right' }}>Date</span>
        </div>

        {/* Rows */}
        {filtered.length === 0 ? (
          <div
            className="px-10 py-12 text-center text-[14px]"
            style={{ color: 'var(--ink-faint)' }}
          >
            Aucune vente ne correspond à la recherche.
          </div>
        ) : (
          filtered.map(v => <VenteRow key={v.id} vente={v} />)
        )}
      </div>
    </div>
  )
}

function VenteRow({ vente: v }: { vente: VenteMock }) {
  const [hovered, setHovered] = useState(false)
  return (
    <div
      className="grid px-10 py-3 text-[13.5px] transition-colors"
      style={{
        gridTemplateColumns: '2.5fr 1.4fr 100px 60px 90px 1fr 120px',
        gap: '1rem',
        borderBottom: '1px solid var(--rule-soft)',
        background: hovered ? 'var(--paper-2)' : 'transparent',
        cursor: 'default',
        alignItems: 'center',
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <span style={{ color: 'var(--ink)', fontWeight: 500 }}>{v.adresse}</span>
      <span style={{ color: 'var(--ink-mute)' }}>{v.arrondissement}</span>
      <span style={{ color: 'var(--ink-mute)' }}>{v.type}</span>
      <span style={{ color: 'var(--ink-faint)' }}>{v.annee}</span>
      <span style={{ color: 'var(--ink-mute)', fontVariantNumeric: 'tabular-nums lining-nums' }}>
        {formatNum(v.superficie)} pi²
      </span>
      <span
        style={{
          color: 'var(--navy)',
          fontWeight: 600,
          fontVariantNumeric: 'tabular-nums lining-nums',
          textAlign: 'right',
        }}
      >
        {formatPrix(v.prix)}
      </span>
      <span
        style={{
          color: 'var(--ink-faint)',
          fontVariantNumeric: 'tabular-nums lining-nums',
          textAlign: 'right',
        }}
      >
        {new Date(v.date).toLocaleDateString('fr-CA', { year: 'numeric', month: 'short', day: 'numeric' })}
      </span>
    </div>
  )
}

// ─── Marchés ─────────────────────────────────────────────────────────────────

function MarchesTab() {
  return (
    <div className="px-10 py-8">
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
          gap: '1.25rem',
        }}
      >
        {MARCHES.map(m => <MarcheCard key={m.nom} marche={m} />)}
      </div>
    </div>
  )
}

function MarcheCard({ marche: m }: { marche: MarcheMock }) {
  const maxVal = Math.max(...m.tendance)
  const positive = m.variation >= 0

  return (
    <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      <div className="flex items-start justify-between gap-2">
        <h3
          style={{
            fontFamily: 'var(--font-serif)',
            fontSize: '1.05rem',
            color: 'var(--ink)',
            margin: 0,
            fontWeight: 600,
          }}
        >
          {m.nom}
        </h3>
        <span
          style={{
            fontSize: '11px',
            fontWeight: 600,
            padding: '2px 7px',
            borderRadius: 'var(--r-pill)',
            background: positive ? 'color-mix(in srgb, var(--navy) 10%, transparent)' : 'color-mix(in srgb, var(--oxblood) 10%, transparent)',
            color: positive ? 'var(--navy)' : 'var(--oxblood)',
            fontVariantNumeric: 'tabular-nums lining-nums',
            flexShrink: 0,
          }}
        >
          {positive ? '+' : ''}{m.variation.toFixed(1)} %
        </span>
      </div>

      <div>
        <div
          style={{
            fontFamily: 'var(--font-serif)',
            fontSize: '1.6rem',
            fontWeight: 700,
            color: 'var(--navy)',
            fontVariantNumeric: 'tabular-nums lining-nums',
            lineHeight: 1.1,
          }}
        >
          {formatPrix(m.prixMedian)}
        </div>
        <div style={{ fontSize: '11px', color: 'var(--ink-faint)', marginTop: '2px' }}>
          prix médian
        </div>
      </div>

      {/* Sparkline */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-end',
          gap: '2px',
          height: '32px',
        }}
      >
        {m.tendance.map((val, i) => (
          <div
            key={i}
            style={{
              width: '4px',
              height: `${Math.round((val / maxVal) * 32)}px`,
              background: 'var(--navy)',
              opacity: 0.25 + (i / m.tendance.length) * 0.75,
              borderRadius: '1px 1px 0 0',
              flexShrink: 0,
            }}
          />
        ))}
      </div>

      {/* Meta */}
      <div
        style={{
          display: 'flex',
          gap: '1rem',
          fontSize: '12px',
          color: 'var(--ink-mute)',
          borderTop: '1px solid var(--rule-soft)',
          paddingTop: '0.625rem',
        }}
      >
        <span><span style={{ color: 'var(--ink)', fontWeight: 500 }}>{m.jrs}</span> j. DOM</span>
        <span><span style={{ color: 'var(--ink)', fontWeight: 500 }}>{m.volume}</span> ventes</span>
      </div>
    </div>
  )
}

// ─── Coûts ───────────────────────────────────────────────────────────────────

function CoutsTab() {
  const groups = useMemo(() => {
    const map = new Map<string, CoutMock[]>()
    for (const c of COUTS) {
      if (!map.has(c.categorie)) map.set(c.categorie, [])
      map.get(c.categorie)!.push(c)
    }
    return [...map.entries()]
  }, [])

  return (
    <div className="px-10 py-8" style={{ maxWidth: '680px' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        {groups.map(([categorie, rows]) => (
          <div key={categorie}>
            <div
              className="eyebrow"
              style={{ marginBottom: '0.5rem' }}
            >
              {categorie}
            </div>
            <div
              style={{
                border: '1px solid var(--rule)',
                borderRadius: 'var(--r-md)',
                overflow: 'hidden',
                background: 'var(--paper-hi)',
              }}
            >
              {rows.map((row, i) => (
                <div
                  key={row.qualite}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.625rem 1rem',
                    borderTop: i === 0 ? 'none' : '1px solid var(--rule-soft)',
                  }}
                >
                  <span style={{ fontSize: '13.5px', color: 'var(--ink-mute)' }}>
                    {row.qualite}
                  </span>
                  <span
                    style={{
                      fontSize: '13.5px',
                      color: 'var(--ink)',
                      fontWeight: 600,
                      fontVariantNumeric: 'tabular-nums lining-nums',
                    }}
                  >
                    {row.taux} {row.unite}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Taux ────────────────────────────────────────────────────────────────────

function TauxTab() {
  const groups = useMemo(() => {
    const map = new Map<string, TauxMock[]>()
    for (const t of TAUX) {
      if (!map.has(t.segment)) map.set(t.segment, [])
      map.get(t.segment)!.push(t)
    }
    return [...map.entries()]
  }, [])

  return (
    <div className="px-10 py-8" style={{ maxWidth: '760px' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        {groups.map(([segment, rows]) => (
          <div key={segment}>
            <div className="eyebrow" style={{ marginBottom: '0.5rem' }}>
              {segment}
            </div>
            <div
              style={{
                border: '1px solid var(--rule)',
                borderRadius: 'var(--r-md)',
                overflow: 'hidden',
                background: 'var(--paper-hi)',
              }}
            >
              {/* Column header */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1.4fr 1fr 1fr 1fr',
                  gap: '1rem',
                  padding: '0.5rem 1rem',
                  background: 'var(--paper)',
                  borderBottom: '1px solid var(--rule-soft)',
                  fontSize: '11px',
                  fontWeight: 500,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  color: 'var(--ink-faint)',
                }}
              >
                <span>Zone</span>
                <span style={{ textAlign: 'right' }}>Taux bas</span>
                <span style={{ textAlign: 'right' }}>Taux haut</span>
                <span style={{ textAlign: 'right' }}>Vacance</span>
              </div>

              {rows.map((row, i) => (
                <div
                  key={row.zone}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1.4fr 1fr 1fr 1fr',
                    gap: '1rem',
                    padding: '0.625rem 1rem',
                    alignItems: 'center',
                    borderTop: i === 0 ? 'none' : '1px solid var(--rule-soft)',
                    fontSize: '13.5px',
                  }}
                >
                  <span style={{ color: 'var(--ink-mute)' }}>{row.zone}</span>
                  <span
                    style={{
                      color: 'var(--navy)',
                      fontWeight: 600,
                      fontVariantNumeric: 'tabular-nums lining-nums',
                      textAlign: 'right',
                    }}
                  >
                    {row.bas.toFixed(2)} %
                  </span>
                  <span
                    style={{
                      color: 'var(--navy)',
                      fontWeight: 600,
                      fontVariantNumeric: 'tabular-nums lining-nums',
                      textAlign: 'right',
                    }}
                  >
                    {row.haut.toFixed(2)} %
                  </span>
                  <span
                    style={{
                      color: 'var(--ink-mute)',
                      fontVariantNumeric: 'tabular-nums lining-nums',
                      textAlign: 'right',
                    }}
                  >
                    {row.vacance.toFixed(1)} %
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function BibliothequePage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<Tab>('ventes')

  async function handleSignOut() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push('/login')
  }

  return (
    <div
      className="relative w-full h-screen overflow-hidden flex"
      style={{ background: 'var(--paper)' }}
    >
      <Sidebar onSignOut={handleSignOut} />

      <div className="main-content flex flex-col overflow-hidden">
        {/* Topbar */}
        <div className="topbar pb-0">
          <div className="flex items-end justify-between mb-4">
            <div>
              <h1 className="page-h1">Bibliothèque</h1>
              <p
                style={{
                  fontSize: '13px',
                  color: 'var(--ink-faint)',
                  marginTop: '2px',
                  fontFamily: 'var(--font-sans)',
                }}
              >
                Ventes · Marchés · Coûts · Taux
              </p>
            </div>
          </div>

          {/* Tab pills */}
          <div
            className="flex gap-1 pb-0"
            style={{ borderBottom: '1px solid var(--rule-soft)' }}
          >
            {(Object.keys(TAB_LABELS) as Tab[]).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`pill ${activeTab === tab ? 'active' : ''}`}
                style={{ marginBottom: '-1px', borderBottomLeftRadius: 0, borderBottomRightRadius: 0 }}
              >
                {TAB_LABELS[tab]}
              </button>
            ))}
          </div>
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-y-auto">
          {activeTab === 'ventes' && <VentesTab />}
          {activeTab === 'marches' && <MarchesTab />}
          {activeTab === 'couts' && <CoutsTab />}
          {activeTab === 'taux' && <TauxTab />}
        </div>
      </div>
    </div>
  )
}
