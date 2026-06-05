'use client'

import { useState, useTransition } from 'react'
import { useRouter } from 'next/navigation'
import { inviteEvaluateur } from './actions'
import { APP_WORDMARK } from '@/constants/app'

export default function InviterPage() {
  const router = useRouter()
  const [isPending, startTransition] = useTransition()
  const [result, setResult] = useState<{ ok: boolean; message: string } | null>(null)
  const [email, setEmail] = useState('')

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    startTransition(async () => {
      const res = await inviteEvaluateur(formData)
      if (res.ok) {
        setResult({ ok: true, message: `Invitation envoyée à ${res.email}` })
        setEmail('')
      } else {
        setResult({ ok: false, message: res.error })
      }
    })
  }

  return (
    <main
      className="min-h-screen flex items-center justify-center"
      style={{ background: 'var(--color-bg)' }}
    >
      <div
        className="w-full max-w-[400px] rounded-[18px] px-8 py-10 flex flex-col gap-7"
        style={{
          background: 'linear-gradient(165deg, rgba(238,232,222,.80) 0%, rgba(228,222,212,.70) 100%)',
          backdropFilter: 'var(--glass-blur)',
          WebkitBackdropFilter: 'var(--glass-blur)',
          border: '1px solid var(--glass-border)',
          boxShadow: 'var(--shadow-glass)',
        }}
      >
        <div className="text-center">
          <span className="font-serif text-[24px] font-medium tracking-[-0.02em] text-[#1a1916]">
            {APP_WORDMARK}
          </span>
          <p className="mt-1 text-[13px] text-[#8a8780]">Inviter un évaluateur</p>
        </div>

        {result && (
          <div
            className={`rounded-[10px] px-4 py-3 text-[13px] border ${
              result.ok
                ? 'text-green-800 bg-green-50/80 border-green-200/60'
                : 'text-red-700 bg-red-50/80 border-red-200/60'
            }`}
          >
            {result.message}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="email" className="text-[12px] text-[#8a8780] font-medium">
              Adresse e-mail de l&apos;évaluateur
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="evaluateur@bureau.com"
              className="rounded-[10px] px-4 py-[10px] text-[14px] text-[#1a1916] outline-none border border-transparent transition-all"
              style={{
                background: 'rgba(255,255,255,.55)',
                boxShadow: 'inset 0 1px 2px rgba(0,0,0,.06)',
              }}
              onFocus={e => e.currentTarget.style.borderColor = 'rgba(51,65,85,.30)'}
              onBlur={e => e.currentTarget.style.borderColor = 'transparent'}
            />
          </div>

          <button
            type="submit"
            disabled={isPending || !email}
            className="rounded-full py-[10px] text-[14px] font-medium text-white transition-opacity disabled:opacity-50"
            style={{ background: '#334155' }}
          >
            {isPending ? 'Envoi en cours…' : "Envoyer l\u2019invitation"}
          </button>
        </form>

        <button
          onClick={() => router.push('/dossiers')}
          className="text-[12px] text-[#8a8780] hover:text-[#1a1916] transition-colors bg-transparent border-none cursor-pointer text-center"
        >
          ← Retour aux dossiers
        </button>
      </div>
    </main>
  )
}
