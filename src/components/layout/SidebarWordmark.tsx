import { APP_WORDMARK } from '@/constants/app'

export default function SidebarWordmark() {
  return (
    <div className="px-[22px] pb-[26px]">
      <div
        className="text-[30px] font-semibold text-[#1a1916] leading-none tracking-[.01em]"
        style={{ fontFamily: 'var(--font-serif)' }}
      >
        {APP_WORDMARK}
      </div>
    </div>
  )
}
