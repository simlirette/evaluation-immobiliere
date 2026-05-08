interface Props {
  range?: string
  median: string
}

export default function ValeurCard({ range, median }: Props) {
  return (
    <div
      className="mt-3.5 px-5 py-[18px] rounded-[14px] flex items-baseline gap-3 border border-[rgba(51,65,85,.12)]"
      style={{ background: 'rgba(51,65,85,.07)' }}
    >
      <span className="text-[11px] text-[#8a8780] uppercase tracking-[.07em] font-medium whitespace-nowrap">
        Valeur
      </span>
      {range && <span className="text-[12px] font-medium text-[#1a1916]">{range}</span>}
      <span className={`text-[13px] text-[#1a1916] whitespace-nowrap ${range ? 'ml-auto' : ''}`}>{median}</span>
    </div>
  )
}
