import { signIn } from './actions'
import { APP_WORDMARK } from '@/constants/app'

interface Props {
  searchParams: Promise<{ error?: string }>
}

export default async function LoginPage({ searchParams }: Props) {
  const { error } = await searchParams

  return (
    <main
      className="min-h-screen flex items-center justify-center"
      style={{ background: 'var(--color-bg)' }}
    >
      <div
        className="w-full max-w-[360px] rounded-[18px] px-8 py-10 flex flex-col gap-7"
        style={{
          background: 'linear-gradient(165deg, rgba(238,232,222,.80) 0%, rgba(228,222,212,.70) 100%)',
          backdropFilter: 'var(--glass-blur)',
          WebkitBackdropFilter: 'var(--glass-blur)',
          border: '1px solid var(--glass-border)',
          boxShadow: 'var(--shadow-glass)',
        }}
      >
        {/* Wordmark */}
        <div className="text-center">
          <span
            className="font-serif text-[28px] font-medium tracking-[-0.02em] text-[#1a1916]"
          >
            {APP_WORDMARK}
          </span>
          <p className="mt-1 text-[13px] text-[#8a8780]">Connexion à votre espace</p>
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-[10px] px-4 py-3 text-[13px] text-red-700 bg-red-50/80 border border-red-200/60">
            {decodeURIComponent(error)}
          </div>
        )}

        {/* Form */}
        <form action={signIn} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="email" className="text-[12px] text-[#8a8780] font-medium">
              Adresse e-mail
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              placeholder="vous@exemple.com"
              className="w-full rounded-[10px] px-4 py-2.5 text-[14px] text-[#1a1916] outline-none transition-shadow placeholder:text-[#b5b2ac]"
              style={{
                background: 'var(--input-bg)',
                border: '1px solid var(--input-border)',
              }}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="password" className="text-[12px] text-[#8a8780] font-medium">
              Mot de passe
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              placeholder="••••••••"
              className="w-full rounded-[10px] px-4 py-2.5 text-[14px] text-[#1a1916] outline-none transition-shadow placeholder:text-[#b5b2ac]"
              style={{
                background: 'var(--input-bg)',
                border: '1px solid var(--input-border)',
              }}
            />
          </div>

          <button
            type="submit"
            className="mt-1 w-full rounded-[10px] py-2.5 text-[14px] font-medium text-white transition-opacity hover:opacity-90 active:opacity-80"
            style={{ background: '#334155' }}
          >
            Se connecter
          </button>
        </form>
      </div>
    </main>
  )
}
