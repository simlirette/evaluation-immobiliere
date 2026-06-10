'use client'

/* Carte dossier — DOM 1:1 du design handoff (components.jsx → DossierCard).
   Champs absents du backend (année, superficie, valeur, client) : « — » muted. */

import { Icon } from '@/components/shared/Icon'
import type { Dossier, DossierStatus } from '@/types'

const STATUS_META: Record<DossierStatus, { label: string; cls: string }> = {
  'en-cours': { label: 'En cours',  cls: 'encours' },
  complet:    { label: 'Complet',   cls: 'complet' },
  brouillon:  { label: 'Brouillon', cls: 'brouillon' },
}

export function formatPropertyType(pt: string): string {
  const map: Record<string, string> = {
    residentiel_unifamilial: 'Unifamiliale',
    condo: 'Condo',
    duplex: 'Duplex',
    triplex: 'Triplex',
    quadruplex: 'Quadruplex',
    commercial: 'Commercial',
    terrain: 'Terrain',
    autre: 'Autre',
  }
  return map[pt] ?? pt
}

interface Props {
  dossier: Dossier
  onClick: () => void
  onPin?: (dossier: Dossier) => void
  onContextMenu?: (e: React.MouseEvent) => void
}

export default function DossierCard({ dossier: d, onClick, onPin, onContextMenu }: Props) {
  const meta = STATUS_META[d.status]
  return (
    <article
      className="dossier-card"
      role="button"
      tabIndex={0}
      aria-label={`Ouvrir le dossier ${d.address}`}
      onClick={onClick}
      onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && onClick()}
      onContextMenu={onContextMenu}
    >
      <div className="card-head">
        <span className={`status-chip ${meta.cls}`}>
          <span>{meta.label}</span>
        </span>
        <button
          className={`pin ${d.pinned ? 'active' : ''}`}
          title={d.pinned ? 'Désépingler' : 'Épingler'}
          onClick={e => { e.stopPropagation(); onPin?.(d) }}>
          <Icon.Pin/>
        </button>
      </div>

      <div className="addr">
        {d.address}
        <span className="city">{d.neighborhood} &nbsp;·&nbsp; <em>{formatPropertyType(d.property_type)}</em></span>
      </div>

      <div className="facts">
        <div className="fact">
          <div className="k">Année</div>
          <div className="v muted">—</div>
        </div>
        <div className="fact">
          <div className="k">Superficie</div>
          <div className="v muted">—</div>
        </div>
        <div className="fact">
          <div className="k">{d.status === 'complet' ? 'Valeur' : 'Stade'}</div>
          <div className="v">
            {d.status === 'brouillon' ? <span className="muted">Saisie</span> : <span className="muted">—</span>}
          </div>
        </div>
      </div>

      <div className="foot">
        <span className="client">{d.neighborhood}</span>
        <span className="stamp">Mod. {d.updatedAt}</span>
      </div>
    </article>
  )
}
