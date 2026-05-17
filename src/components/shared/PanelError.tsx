interface Props {
  onRetry?: () => void
}

export default function PanelError({ onRetry }: Props) {
  return (
    <div className="flex flex-col items-center justify-center flex-1 gap-3">
      <svg width="32" height="32" fill="none" stroke="currentColor" viewBox="0 0 24 24" className="text-[#c0392b] opacity-60">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
      </svg>
      <div className="text-center">
        <div className="text-[14px] text-[#4a4845] font-medium mb-1">Erreur de chargement</div>
        <div className="text-[12px] text-[#b5b2ac]">Les données n&apos;ont pas pu être récupérées.</div>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-1 px-4 py-1.5 rounded-full text-[12px] text-[#334155] border border-[#334155]/20 hover:bg-[#334155]/[.06] transition-colors bg-transparent cursor-pointer font-sans"
        >
          Réessayer
        </button>
      )}
    </div>
  )
}
