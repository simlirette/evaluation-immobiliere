import type { Metadata } from 'next'
import Providers from '@/providers/Providers'
import './globals.css'

export const metadata: Metadata = {
  title: 'Eval Immo',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" data-theme="light">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
