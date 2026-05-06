import type { Comparable } from '@/types'

export default function ComparableItem({ comp }: { comp: Comparable }) {
  return (
    <div
      className="grid items-center gap-2.5 px-3.5 py-[11px] rounded-[11px] border border-black/[.055] transition-colors hover:bg-black/[.06]"
      style={{ gridTemplateColumns: '20px 1fr auto', background: 'rgba(0,0,0,.04)' }}
    >
      <div className="text-[10px] text-[#b5b2ac] font-medium text-center">{comp.rank}</div>
      <div className="min-w-0">
        <div className="text-[13px] text-[#1a1916]">{comp.address}</div>
        <div className="text-[11px] text-[#8a8780] mt-0.5">{comp.meta}</div>
      </div>
      <div className="text-right">
        <div className="text-[13px] font-medium text-[#1a1916]">{comp.price}</div>
        <div className="text-[11px] text-[#8a8780] mt-0.5">{comp.date}</div>
      </div>
    </div>
  )
}
