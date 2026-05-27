import { signIn } from './actions'

interface Props {
  searchParams: Promise<{ error?: string }>
}

export default async function LoginPage({ searchParams }: Props) {
  const { error } = await searchParams

  return (
    <main
      className="min-h-screen flex flex-col items-center justify-center gap-8"
      style={{
        background: 'radial-gradient(ellipse 75% 50% at 30% 20%, rgba(245,238,226,.80) 0%, transparent 60%), radial-gradient(ellipse 55% 60% at 75% 85%, rgba(218,212,202,.55) 0%, transparent 55%), #e6e0d7',
      }}
    >
      {/* Wordmark — outside card, editorial presence */}
      <div className="text-center select-none">
        <div
          className="text-[44px] font-semibold leading-[0.90] tracking-[-0.02em] text-[#1a1916]"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          {'\u00c9val'}
          <br />
          Immo
        </div>
        <p className="mt-3 text-[10px] uppercase tracking-[.14em] text-[#8a8780] font-medium">
          {'\u00c9valuation immobili\u00e8re assist\u00e9e'}
        </p>
      </div>

      {/* Card */}
      <div
        className="w-full max-w-[360px] rounded-[18px] px-8 py-9 flex flex-col gap-6"
        style={{
          background: 'linear-gradient(165deg, rgba(248,244,238,.90) 0%, rgba(235,229,220,.82) 100%)',
          backdropFilter: 'var(--glass-blur)',
          WebkitBackdropFilter: 'var(--glass-blur)',
          border: '1px solid rgba(255,255,255,.58)',
          boxShadow: 'var(--shadow-glass), var(--glass-inset)',
        }}
      >
        <div>
          <h1 className="text-[15px] font-medium text-[#1a1916] mb-0.5">Connexion</h1>
          <p className="text-[13px] text-[#8a8780]">{'Acc\u00e9dez \u00e0 votre espace de travail'}</p>
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
              className="w-full rounded-[10px] px-4 py-2.5 text-[14px] text-[#1a1916] outline-none transition-shadow focus:shadow-[0_0_0_2px_rgba(51,65,85,.18)] placeholder:text-[#b5b2ac]"
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
              className="w-full rounded-[10px] px-4 py-2.5 text-[14px] text-[#1a1916] outline-none transition-shadow focus:shadow-[0_0_0_2px_rgba(51,65,85,.18)] placeholder:text-[#b5b2ac]"
              style={{
                background: 'var(--input-bg)',
                border: '1px solid var(--input-border)',
              }}
            />
          </div>

          <button
            type="submit"
            className="mt-1 w-full rounded-[10px] py-2.5 text-[14px] font-medium text-white transition-opacity hover:opacity-90 active:opacity-80 cursor-pointer"
            style={{ background: '#334155' }}
          >
            Se connecter
          </button>
        </form>
      </div>

      {/* Footer */}
      <p className="text-[11px] text-[#b5b2ac]">Usage {'\u00e9val'}uateurs agr{'\u00e9\u00e9'}s seulement</p>
    </main>
  )
}
