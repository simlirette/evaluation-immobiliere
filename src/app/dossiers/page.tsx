'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import DossierCard from '@/components/dossiers/DossierCard'
import ThemeToggle from '@/components/layout/ThemeToggle'
import { fetchDossiers } from '@/lib/supabase/queries/dossiers'
import type { Dossier } from '@/types'

export default function MesDossiersPage() {
  const router = useRouter()
  const [search, setSearch] = useState('')
  const [dossiers, setDossiers] = useState<Dossier[]>([])

  useEffect(() => {
    fetchDossiers().then(setDossiers)
  }, [])

  const filtered = dossiers.filter(d =>
    d.address.toLowerCase().includes(search.toLowerCase()) ||
    `${d.property_type} ${d.neighborhood}`.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="relative min-h-screen overflow-y-auto">
      <ThemeToggle />
      <div className="flex flex-col px-10 py-7 pb-9 max-w-[1100px] mx-auto">

        {/* Search bar */}
        <div className="flex justify-center mb-7">
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
                className="bg-transparent border-none outline-none text-[13px] text-[#1a1916] w-full placeholder:text-[#b5b2ac]"
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
            >
              <svg width="15" height="15" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h18M7 12h10M11 20h2"/>
              </svg>
            </button>
          </div>
        </div>

        {/* Grid */}
        <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
          {filtered.map(d => (
            <DossierCard
              key={d.id}
              dossier={d}
              onClick={() => router.push(`/dossier/${d.slug}?tab=dossier`)}
            />
          ))}
        </div>

      </div>
    </div>
  )
}
