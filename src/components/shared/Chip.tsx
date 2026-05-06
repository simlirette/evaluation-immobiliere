interface Props {
  label: string
  highlight?: boolean
}

export default function Chip({ label, highlight }: Props) {
  return (
    <span
      className={`px-3 py-1 rounded-full text-xs border ${
        highlight
          ? 'bg-[rgba(51,65,85,.10)] border-[rgba(51,65,85,.20)] text-[#334155]'
          : 'bg-black/[.06] border-black/[.08] text-[#8a8780]'
      }`}
    >
      {label}
    </span>
  )
}
