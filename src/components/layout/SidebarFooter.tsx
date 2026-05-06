interface Props {
  onSignOut: () => void
}

export default function SidebarFooter({ onSignOut }: Props) {
  return (
    <div className="px-3 pt-3.5 mt-4 border-t border-black/[.06]">
      <div className="flex items-center gap-2 px-3 py-[7px] text-xs text-[#8a8780] cursor-pointer rounded-[6px] hover:bg-black/[.03] hover:text-[#1a1916] transition-[background,color]">
        <svg width="13" height="13" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
        </svg>
        Mon compte
      </div>
      <button
        onClick={onSignOut}
        className="flex w-full items-center gap-2 px-3 py-[7px] text-xs text-[#8a8780] cursor-pointer rounded-[6px] hover:bg-black/[.03] hover:text-[#1a1916] transition-[background,color] bg-transparent border-none font-sans"
      >
        <svg width="13" height="13" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
        </svg>
        Déconnexion
      </button>
    </div>
  )
}
