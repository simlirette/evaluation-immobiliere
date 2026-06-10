import type { Metadata } from 'next'
import { Source_Serif_4 } from 'next/font/google'
import Providers from '@/providers/Providers'
import './globals.css'

const sourceSerif = Source_Serif_4({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  style: ['normal', 'italic'],
  variable: '--font-source-serif',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Éval Immo',
  description: 'Espace de travail pour évaluateurs agréés — pipeline d\u2019évaluation immobilière assisté par IA.',
  robots: { index: false, follow: false },
}

/* Boot thème avant peinture (anti-FOUC) — pattern theme.js du design handoff :
   localStorage "evalimmo-theme", repli sur prefers-color-scheme. */
const themeBoot = `(function(){try{var t=localStorage.getItem("evalimmo-theme");if(t!=="dark"&&t!=="light"){t=window.matchMedia&&window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"}document.documentElement.setAttribute("data-theme",t)}catch(e){}})()`

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" data-theme="light" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeBoot }} />
      </head>
      <body className={sourceSerif.variable}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
