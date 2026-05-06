import type { Dossier, DossierStatus } from '@/types'

const statusStyles: Record<DossierStatus, string> = {
  'en-cours': 'bg-[rgba(51,65,85,.10)] text-[#334155]',
  'complet':  'bg-[rgba(34,136,102,.10)] text-[#228866]',
  'brouillon':'bg-black/[.06] text-[#8a8780]',
}

const statusLabels: Record<DossierStatus, string> = {
  'en-cours': 'En cours',
  'complet':  'Complété',
  'brouillon':'Brouillon',
}

interface Props {
  dossier: Dossier
  onClick: () => void
}

export default function DossierCard({ dossier, onClick }: Props) {
  return (
    <div
      onClick={onClick}
      className="rounded-[18px] px-[22px] pt-[22px] pb-[18px] cursor-pointer transition-[transform,box-shadow] duration-200 hover:-translate-y-[3px] border border-white/[.72]"
      style={{
        background: 'linear-gradient(165deg, rgba(248,244,238,.96) 0%, rgba(238,232,223,.90) 100%)',
        boxShadow: 'var(--shadow-card)',
      }}
    >
      <div
        className="text-[17px] font-medium text-[#1a1916] mb-1 leading-[1.2] tracking-[.01em]"
        style={{ fontFamily: 'var(--font-serif)' }}
      >
        {dossier.address}
      </div>
      <div className="text-xs text-[#8a8780] font-light mb-3.5">{dossier.meta}</div>
      <div className="flex items-center justify-between">
        <span className="text-[11px] text-[#b5b2ac]">{dossier.updatedAt}</span>
        <span className={`text-[10px] font-medium px-[9px] py-[3px] rounded-full tracking-[.02em] ${statusStyles[dossier.status]}`}>
          {statusLabels[dossier.status]}
        </span>
      </div>
    </div>
  )
}
