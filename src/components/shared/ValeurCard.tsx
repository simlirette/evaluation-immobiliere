interface Props {
  range?: string
  median: string
}

export default function ValeurCard({ range, median }: Props) {
  return (
    <div className="mt-3.5 rounded-[14px] border border-[rgba(51,65,85,.12)] overflow-hidden"
      style={{ background: 'rgba(51,65,85,.07)' }}
    >
      <div className="flex items-baseline gap-3 px-5 py-[18px]">
        <span className="text-[11px] text-[#8a8780] uppercase tracking-[.07em] font-medium whitespace-nowrap">
          Valeur
        </span>
        {range && <span className="text-[12px] font-medium text-[#1a1916]">{range}</span>}
        <span className={`text-[13px] text-[#1a1916] whitespace-nowrap ${range ? 'ml-auto' : ''}`}>{median}</span>
      </div>
      <div className="px-5 pb-3 text-[11px] text-[#8a8780] border-t border-[rgba(51,65,85,.08)] pt-2">
        Brouillon non certifi{'\u00e9'} {'\u2014'} validation par un {'\u00e9'}valuateur agr{'\u00e9'}{'\u00e9'} requise avant toute diffusion.
      </div>
    </div>
  )
}
