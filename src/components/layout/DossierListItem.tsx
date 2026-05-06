'use client'

interface Props {
  name: string
  active: boolean
  onSelect: () => void
  onContextMenu: (e: React.MouseEvent) => void
}

export default function DossierListItem({ name, active, onSelect, onContextMenu }: Props) {
  return (
    <div
      className={`group relative flex items-center px-3 py-1.5 text-xs rounded-[6px] cursor-pointer transition-[background,color] duration-150 ${
        active
          ? 'text-[#1a1916] bg-black/[.05]'
          : 'text-[#8a8780] hover:text-[#1a1916] hover:bg-black/[.03]'
      }`}
      onClick={onSelect}
    >
      <span className="flex-1 min-w-0 truncate">{name}</span>
      <button
        className="w-[22px] h-[22px] rounded-[5px] flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/[.07] bg-transparent border-none cursor-pointer"
        onClick={e => { e.stopPropagation(); onContextMenu(e) }}
      >
        <svg width="13" height="13" fill="currentColor" viewBox="0 0 24 24">
          <circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/>
        </svg>
      </button>
    </div>
  )
}
