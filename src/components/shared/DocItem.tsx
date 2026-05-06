import type { Document } from '@/types'

export default function DocItem({ doc }: { doc: Document }) {
  return (
    <div
      className="flex items-center gap-2.5 px-3.5 py-2.5 rounded-[10px] text-sm text-[#1a1916] border border-black/[.07]"
      style={{ background: 'rgba(0,0,0,.05)' }}
    >
      <div className="w-7 h-7 bg-[#334155] rounded-[6px] flex items-center justify-center flex-shrink-0">
        <svg width="14" height="14" fill="none" stroke="white" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
        </svg>
      </div>
      <div>
        <div className="font-normal">{doc.name}</div>
        <div className="text-[11px] text-[#8a8780]">{doc.filename}</div>
      </div>
      <span className="text-[11px] text-[#8a8780] ml-auto">{doc.sizeLabel}</span>
    </div>
  )
}
