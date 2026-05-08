import type { Metadata } from 'next'
import { Cormorant_Garamond, Inter } from 'next/font/google'
import Providers from '@/providers/Providers'
import './globals.css'

const cormorant = Cormorant_Garamond({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600'],
  variable: '--font-cormorant',
  display: 'swap',
})

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
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
      <body className={`${cormorant.variable} ${inter.variable}`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
