interface Props {
  title: string
  subtitle: string
  onClick?: () => void
  label: string
  disabled?: boolean
}

export default function RapportArtifact({ title, subtitle, onClick, label, disabled }: Props) {
  return (
    <button
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      className={`flex items-center gap-2.5 mt-3 px-3.5 py-2.5 w-full rounded-[10px] border border-black/[.07] text-left transition-colors bg-transparent ${disabled ? 'cursor-default opacity-70' : 'hover:bg-black/[.08] active:bg-black/10 cursor-pointer'}`}
      style={{ background: 'rgba(0,0,0,.05)' }}
    >
      <div className="w-7 h-7 bg-[#334155] rounded-[6px] flex items-center justify-center flex-shrink-0">
        <svg width="14" height="14" fill="none" stroke="white" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.6}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
        </svg>
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[13px] font-normal text-[#1a1916]">{title}</div>
        <div className="text-[11px] text-[#8a8780] mt-px">{subtitle}</div>
      </div>
      {!disabled && <div className="text-[11px] text-[#8a8780] flex-shrink-0">{label}</div>}
    </button>
  )
}
