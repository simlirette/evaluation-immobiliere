'use client'

/* Rangée dossier (vue liste) — DOM 1:1 du design handoff (components.jsx → DossierRow). */

import { Icon } from '@/components/shared/Icon'
import { formatPropertyType } from './DossierCard'
import type { Dossier, DossierStatus } from '@/types'

const STATUS_META: Record<DossierStatus, { label: string; cls: string }> = {
  'en-cours': { label: 'En cours',  cls: 'encours' },
  complet:    { label: 'Complet',   cls: 'complet' },
  brouillon:  { label: 'Brouillon', cls: 'brouillon' },
}

interface Props {
  dossier: Dossier
  onClick: () => void
  onPin?: (dossier: Dossier) => void
  onContextMenu?: (e: React.MouseEvent) => void
}

export default function DossierRow({ dossier: d, onClick, onPin, onContextMenu }: Props) {
  const meta = STATUS_META[d.status]
  return (
    <article
      className="dossier-row"
      role="button"
      tabIndex={0}
      aria-label={`Ouvrir le dossier ${d.address}`}
      onClick={onClick}
      onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && onClick()}
      onContextMenu={onContextMenu}
    >
      <div className="col-addr">
        <div className="addr-line">
          <span className={`status-dot ${meta.cls}`} title={meta.label}/>
          <span className="addr">{d.address}</span>
        </div>
        <div className="city">{d.neighborhood}</div>
      </div>
      <div className="col-type">{formatPropertyType(d.property_type)}</div>
      <div className="col-year numeric">—</div>
      <div className="col-area numeric">—</div>
      <div className="col-stage">
        {d.status === 'brouillon'
          ? <span className="v muted">Saisie</span>
          : <span className="v muted">—</span>}
      </div>
      <div className="col-client">{d.neighborhood}</div>
      <div className="col-modified">{d.updatedAt}</div>
      <div className="col-actions">
        <button
          className={`pin ${d.pinned ? 'active' : ''}`}
          title={d.pinned ? 'Désépingler' : 'Épingler'}
          onClick={e => { e.stopPropagation(); onPin?.(d) }}>
          <Icon.Pin/>
        </button>
      </div>
    </article>
  )
}
