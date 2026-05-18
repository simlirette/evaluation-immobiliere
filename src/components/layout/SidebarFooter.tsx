interface Props { onSignOut: () => void }

export default function SidebarFooter({ onSignOut }: Props) {
  return (
    <div className="px-3 pb-4 pt-2 border-t border-[var(--glass-border)]">
      <button
        onClick={onSignOut}
        className="w-full flex items-center gap-2.5 px-3 py-2 rounded-[10px] text-[13px] text-[#8a8780] hover:text-[#1a1916] dark:hover:text-white/80 hover:bg-black/5 dark:hover:bg-white/5 transition-colors text-left cursor-pointer"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
          <path
            d="M5 2H3a1 1 0 00-1 1v8a1 1 0 001 1h2M9 10l3-3-3-3M12 7H5"
            stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"
          />
        </svg>
        Déconnexion
      </button>
    </div>
  )
}
