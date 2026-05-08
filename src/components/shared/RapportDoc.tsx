interface Props {
  address?: string
  valeur?: string | null
  content?: string
  onClose: () => void
}

export default function RapportDoc({ address, valeur, content, onClose }: Props) {
  return (
    <div className="flex flex-col flex-1 relative overflow-hidden">
      <div className="absolute top-3 right-8 z-10">
        <button
          onClick={onClose}
          className="w-7 h-7 rounded-[7px] flex items-center justify-center bg-transparent border-none cursor-pointer text-[#b5b2ac] hover:text-[#1a1916] hover:bg-black/[.06] transition-colors"
          title="Fermer"
        >
          <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
              d="M20 4L13 11M17 11H13V7M4 20L11 13M7 13H11V17"/>
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-8 py-10 scroll-fade">
        <div
          className="px-7 py-6 rounded-[14px] text-[13px] leading-[1.75] border border-black/[.06]"
          style={{
            background: 'rgba(255,255,255,.55)',
            boxShadow: 'inset 0 1px 0 rgba(255,255,255,.8)',
          }}
        >
          <div
            className="text-[18px] font-medium text-[#1a1916] mb-1 tracking-[.01em]"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            BROUILLON DE RAPPORT D{'\u2019'}{'ÉVALUATION'}
          </div>
          <div className="text-[11px] text-[#8a8780] mb-4 pb-3.5 border-b border-black/[.07]">
            Brouillon non certifi{'\u00e9'} {'\u2014'} aucune r{'\u00e9'}ponse d{'\u2019'}{'\u00e9'}valuateur externe n{'\u2019'}est invent{'\u00e9'}e.
            Validation et signature par un {'\u00e9'}valuateur agr{'\u00e9'}{'\u00e9'} hors syst{'\u00e8'}me requises avant toute diffusion.
          </div>

          <div className="grid grid-cols-2 gap-2 text-[12px] mb-4">
            <div className="rounded-[8px] bg-black/[.03] px-3 py-2">
              <div className="text-[10px] uppercase tracking-[.07em] text-[#b5b2ac]">Dossier</div>
              <div>{address || '-'}</div>
            </div>
            <div className="rounded-[8px] bg-black/[.03] px-3 py-2">
              <div className="text-[10px] uppercase tracking-[.07em] text-[#b5b2ac]">Conclusion propos{'\u00e9'}e</div>
              <div>{valeur ?? '-'}</div>
            </div>
          </div>

          <div className="mb-4 px-3 py-2 rounded-[8px] bg-amber-50/80 border border-amber-200/60 text-[11px] text-amber-800">
            Ce brouillon est produit par un assistant IA. Il ne constitue pas une certification de valeur
            et ne remplace pas l{'\u2019'}opinion professionnelle d{'\u2019'}un {'\u00e9'}valuateur agr{'\u00e9'}{'\u00e9'}.
          </div>

          <pre className="whitespace-pre-wrap font-sans text-[13px] leading-6 text-[#1a1916]">
            {content || 'Aucun brouillon runtime disponible.'}
          </pre>
        </div>
      </div>
    </div>
  )
}
