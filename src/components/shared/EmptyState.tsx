interface Props {
  title: string
  subtitle: string
}

export default function EmptyState({ title, subtitle }: Props) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center text-center mb-8">
      <div
        className="text-[22px] font-medium text-[#1a1916] mb-1.5 tracking-[.01em]"
        style={{ fontFamily: 'var(--font-serif)' }}
      >
        {title}
      </div>
      <div className="text-sm text-[#8a8780] font-light">{subtitle}</div>
    </div>
  )
}
