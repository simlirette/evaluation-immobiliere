'use client'

/* Modèles — port 1:1 du design handoff (modeles.jsx + modeles.css). */

import { useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import { Icon } from '@/components/shared/Icon'
import { MODELES, type ModeleMock } from '@/data/modeles-mock'
import { createClient } from '@/lib/supabase/client'
import './modeles.css'

export default function ModelesPage() {
  const router = useRouter()
  const [sort, setSort] = useState('used')

  const sorted = useMemo(() => {
    const arr = MODELES.slice()
    if (sort === 'used')  arr.sort((a, b) => b.used - a.used)
    if (sort === 'alpha') arr.sort((a, b) => a.title.localeCompare(b.title, 'fr-CA'))
    if (sort === 'last')  arr.sort((a, b) => b.last.localeCompare(a.last))
    return arr
  }, [sort])

  async function handleSignOut() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push('/login')
  }

  return (
    <div className="app">
      <Sidebar onSignOut={handleSignOut} />

      <div className="main">
        <div className="topbar modeles-topbar">
          <div className="crumbs">
            <span className="today">{MODELES.length} modèles disponibles</span>
          </div>

          <div className="pagehead modeles-head">
            <div>
              <h1>Modèles</h1>
              <div className="subtitle">
                Un point de départ pour chaque type de mandat — conformes aux exigences de l&apos;OEAQ.
              </div>
            </div>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <div className="sort-select" style={{ padding: 0 }}>
                <span className="label">Trier par</span>
                <select value={sort} onChange={e => setSort(e.target.value)}>
                  <option value="used">Plus utilisés</option>
                  <option value="alpha">Nom (A–Z)</option>
                  <option value="last">Modifié récemment</option>
                </select>
              </div>
              <button className="btn accent"><Icon.Plus/> Nouveau modèle</button>
            </div>
          </div>
        </div>

        <div className="modeles-body">
          <div className="modeles-grid">
            {sorted.map(m => <ModelCard key={m.id} m={m}/>)}
          </div>
        </div>
      </div>
    </div>
  )
}

function ModelCard({ m }: { m: ModeleMock }) {
  const router = useRouter()
  return (
    <article className="model-card">
      <div className="mc-head">
        <span className={`mc-cat cat-${m.cat}`}>{m.cat}</span>
        <button className="mc-action" title="Options" onClick={e => e.stopPropagation()}>
          <Icon.More/>
        </button>
      </div>

      <h2 className="mc-title">{m.title}</h2>
      <p className="mc-desc">{m.desc}</p>

      <div className="mc-stats">
        <div className="mc-stat">
          <div className="mc-stat-v numeric">{m.sections}</div>
          <div className="mc-stat-k">sections</div>
        </div>
        <div className="mc-stat">
          <div className="mc-stat-v numeric">{m.pages}</div>
          <div className="mc-stat-k">pages env.</div>
        </div>
        <div className="mc-stat">
          <div className="mc-stat-v numeric">{m.docs}</div>
          <div className="mc-stat-k">documents</div>
        </div>
      </div>

      <div className="mc-foot">
        <div className="mc-norm">
          <Icon.Seal/>
          <span>{m.norm}</span>
        </div>
        <div className="mc-meta">
          <span className="mc-meta-l">Utilisé dans <b className="numeric">{m.used}</b> dossier{m.used > 1 ? 's' : ''}</span>
          <span className="mc-meta-d">Mod. {m.last}</span>
        </div>
      </div>

      <div className="mc-actions">
        <button className="btn ghost">Aperçu</button>
        <button className="btn secondary" onClick={() => router.push('/dossier/nouveau')}>Démarrer un dossier</button>
      </div>
    </article>
  )
}
