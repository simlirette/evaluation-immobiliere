import Link from 'next/link'

export default function NotFound() {
  return (
    <main
      className="min-h-screen flex items-center justify-center"
      style={{ background: 'var(--color-bg)' }}
    >
      <div
        className="w-full max-w-[360px] rounded-[18px] px-8 py-10 flex flex-col gap-5 text-center"
        style={{
          background: 'linear-gradient(165deg, rgba(238,232,222,.80) 0%, rgba(228,222,212,.70) 100%)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '1px solid rgba(255,255,255,.55)',
          boxShadow: '0 8px 32px rgba(0,0,0,.08)',
        }}
      >
        <p className="text-[48px] leading-none select-none">404</p>
        <div>
          <h1
            className="text-[20px] font-medium text-[#1a1916] leading-snug"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Page introuvable
          </h1>
          <p className="mt-1.5 text-[13px] text-[#8a8780]">
            Cette page n&apos;existe pas ou a été déplacée.
          </p>
        </div>
        <Link
          href="/dossiers"
          className="mt-1 inline-block rounded-full px-5 py-2.5 text-[13px] font-medium text-white transition-opacity hover:opacity-90"
          style={{ background: '#334155' }}
        >
          Retour aux dossiers
        </Link>
      </div>
    </main>
  )
}
