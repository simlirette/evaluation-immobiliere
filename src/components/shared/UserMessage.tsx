interface Props {
  children: React.ReactNode
}

export default function UserMessage({ children }: Props) {
  return (
    <div className="py-3.5 border-b border-black/[.06] dark:border-white/[.05] text-right">
      <div
        className="inline-block rounded-[18px_18px_4px_18px] px-4 py-2.5 text-sm font-light text-[#1a1916] dark:text-[#e8e5e0] max-w-[420px] text-left"
        style={{ background: 'rgba(0,0,0,.07)' }}
      >
        {children}
      </div>
    </div>
  )
}
