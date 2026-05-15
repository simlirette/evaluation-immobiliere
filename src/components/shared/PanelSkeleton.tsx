export default function PanelSkeleton() {
  return (
    <div className="flex flex-col flex-1 px-6 pt-6 pb-9 gap-3 max-w-[640px] mx-auto w-full">
      <div className="h-3 w-2/3 rounded-full bg-black/[.06] animate-pulse" />
      <div className="h-3 w-1/2 rounded-full bg-black/[.06] animate-pulse" />
      <div className="mt-2 h-[72px] rounded-[12px] bg-black/[.04] animate-pulse" />
      <div className="h-3 w-3/4 rounded-full bg-black/[.06] animate-pulse" />
      <div className="h-3 w-2/5 rounded-full bg-black/[.06] animate-pulse" />
      <div className="mt-1 h-[48px] rounded-[12px] bg-black/[.04] animate-pulse" />
      <div className="h-3 w-1/2 rounded-full bg-black/[.06] animate-pulse" />
    </div>
  )
}
