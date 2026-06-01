'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import { createClient } from '@/lib/supabase/client'
import { ModeleMock, MODELES } from '@/data/modeles-mock'

type SortKey = 'usage' | 'alpha' | 'recent'

const SORT_LABELS: Record<SortKey, string> = {
  usage: 'Par utilisation',
  alpha: 'Alphabétique',
  recent: 'Récent',
}

function sortModeles(modeles: ModeleMock[], sort: SortKey): ModeleMock[] {
  const copy = [...modeles]
  if (sort === 'usage') {
    return copy.sort((a, b) => b.nbDossiers - a.nbDossiers)
  }
  if (sort === 'alpha') {
    return copy.sort((a, b) => a.titre.localeCompare(b.titre, 'fr'))
  }
  // recent
  return copy.sort((a, b) => new Date(b.modifieLe).getTime() - new Date(a.modifieLe).getTime())
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('fr-CA', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export default function ModelesPage() {
  const router = useRouter()
  const [sort, setSort] = useState<SortKey>('usage')

  async function handleSignOut() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push('/login')
  }

  const sorted = sortModeles(MODELES, sort)

  return (
    <div
      className="relative w-full h-screen overflow-hidden flex"
      style={{ background: 'var(--paper)' }}
    >
      <Sidebar onSignOut={handleSignOut} />

      <div className="main-content flex flex-col overflow-hidden">
        {/* Topbar */}
        <div className="topbar">
          <div className="flex items-end justify-between">
            <div>
              <h1 className="page-h1">Modèles</h1>
              <p
                className="eyebrow mt-1"
                style={{ color: 'var(--ink-faint)', fontSize: 13, fontFamily: 'var(--font-sans)', letterSpacing: '0.01em' }}
              >
                Gabarits de rapport · OEAQ
              </p>
            </div>
          </div>
        </div>

        {/* Toolbar */}
        <div
          className="flex items-center gap-2 px-10 py-3 flex-shrink-0 border-b"
          style={{ borderBottomColor: 'var(--rule-soft)' }}
        >
          {(Object.keys(SORT_LABELS) as SortKey[]).map(key => (
            <button
              key={key}
              onClick={() => setSort(key)}
              className={`pill${sort === key ? ' active' : ''}`}
            >
              {SORT_LABELS[key]}
            </button>
          ))}
        </div>

        {/* Card grid */}
        <div className="flex-1 overflow-y-auto">
          <div className="px-10 pt-6 pb-16">
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
                gap: 20,
              }}
            >
              {sorted.map(modele => (
                <ModeleCard
                  key={modele.id}
                  modele={modele}
                  onNouveauDossier={() => router.push('/dossier/nouveau')}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function ModeleCard({
  modele,
  onNouveauDossier,
}: {
  modele: ModeleMock
  onNouveauDossier: () => void
}) {
  return (
    <div
      className="panel card-hover"
      style={{ display: 'flex', flexDirection: 'column', gap: 0 }}
    >
      {/* Header — colonne */}
      <div style={{ padding: '20px 20px 0', display: 'flex', flexDirection: 'column', gap: 10 }}>
        {/* Badges row */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{
            fontSize: 10, fontFamily: 'var(--font-sans)', textTransform: 'uppercase',
            letterSpacing: '0.06em', color: 'var(--ink-faint)',
            border: '1px solid var(--ink-faint)', borderRadius: 'var(--r-pill)', padding: '2px 7px',
          }}>
            {modele.categorie}
          </span>
          {modele.oeaqConforme && (
            <span style={{
              fontSize: 10, fontFamily: 'var(--font-sans)', textTransform: 'uppercase',
              letterSpacing: '0.06em', color: 'var(--navy)',
              border: '1px solid var(--navy)', borderRadius: 'var(--r-pill)', padding: '2px 7px',
            }}>
              OEAQ ✓
            </span>
          )}
        </div>

        {/* Title */}
        <h3 style={{ fontSize: 16, fontWeight: 500, fontFamily: 'var(--font-serif)', color: 'var(--ink)', margin: 0, lineHeight: 1.3 }}>
          {modele.titre}
        </h3>

        {/* Description */}
        <p style={{ fontSize: 12.5, fontFamily: 'var(--font-sans)', color: 'var(--ink-mute)', margin: 0, lineHeight: 1.55 }}>
          {modele.description}
        </p>
      </div>

      {/* Stats + meta */}
      <div style={{ padding: '12px 20px 0' }}>
        {/* Stats row */}
        <p
          style={{
            fontSize: 12,
            fontFamily: 'var(--font-sans)',
            color: 'var(--ink-mute)',
            marginBottom: 4,
          }}
        >
          {modele.sections} sections · {modele.pages} p. · {modele.documents} docs
        </p>

        {/* Usage + date row */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginTop: 6,
            marginBottom: 14,
          }}
        >
          <span
            style={{
              fontSize: 12,
              fontFamily: 'var(--font-sans)',
              color: 'var(--ink-faint)',
            }}
          >
            Utilisé dans {modele.nbDossiers} dossiers
          </span>
          <span
            style={{
              fontSize: 12,
              fontFamily: 'var(--font-sans)',
              color: 'var(--ink-faint)',
            }}
          >
            Modifié le {formatDate(modele.modifieLe)}
          </span>
        </div>

        {/* Divider */}
        <div
          style={{
            height: 1,
            background: 'var(--rule-soft)',
            marginLeft: -20,
            marginRight: -20,
          }}
        />

        {/* Actions */}
        <div
          style={{
            display: 'flex',
            gap: 8,
            paddingTop: 12,
            paddingBottom: 16,
          }}
        >
          <button className="btn ghost btn-sm">Aperçu</button>
          <button
            className="btn secondary btn-sm"
            onClick={onNouveauDossier}
          >
            Nouveau dossier
          </button>
        </div>
      </div>
    </div>
  )
}
