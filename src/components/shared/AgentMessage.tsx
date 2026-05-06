interface Props {
  agentName: string
  children: React.ReactNode
  last?: boolean
}

export default function AgentMessage({ agentName, children, last }: Props) {
  return (
    <div className={`py-4 ${last ? '' : 'border-b border-black/[.06]'}`}>
      <div className="flex items-center gap-1.5 mb-2 text-[11px] font-medium text-[#b5b2ac] uppercase tracking-[.06em]">
        <div className="w-1.5 h-1.5 rounded-full bg-[#334155]" />
        {agentName}
      </div>
      <div className="text-sm font-light text-[#1a1916] leading-[1.65]">
        {children}
      </div>
    </div>
  )
}
