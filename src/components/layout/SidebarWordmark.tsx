export default function SidebarWordmark() {
  return (
    <div className="px-[22px] pb-[22px]">
      <div
        className="text-[30px] font-semibold text-[#1a1916] dark:text-[#e8e5e0] leading-none tracking-[.01em]"
        style={{ fontFamily: 'var(--font-serif)' }}
      >
        {'\u00c9val'}
        <br />
        Immo
      </div>
      <div className="mt-3 h-px w-8 rounded-full bg-[rgba(0,0,0,.12)] dark:bg-[rgba(255,255,255,.10)]" />
    </div>
  )
}
