'use client'

import { useEffect } from 'react'

interface Props {
  error: Error & { digest?: string }
  reset: () => void
}

export default function GlobalError({ error, reset }: Props) {
  useEffect(() => {
    console.error('[EvalImmo]', error)
  }, [error])

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
        <p className="text-[48px] leading-none select-none">⚠️</p>
        <div>
          <h1
            className="text-[20px] font-medium text-[#1a1916] leading-snug"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Une erreur est survenue
          </h1>
          <p className="mt-1.5 text-[13px] text-[#8a8780]">
            Le runtime est peut-être inaccessible. Réessayez ou contactez l&apos;équipe.
          </p>
        </div>
        <button
          onClick={reset}
          className="mt-1 rounded-full px-5 py-2.5 text-[13px] font-medium text-white transition-opacity hover:opacity-90 border-none cursor-pointer"
          style={{ background: '#334155' }}
        >
          Réessayer
        </button>
      </div>
    </main>
  )
}
