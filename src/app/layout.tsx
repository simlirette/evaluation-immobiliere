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

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" data-theme="light">
      <body className={sourceSerif.variable}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
