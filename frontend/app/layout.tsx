import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { SSEProvider } from '@/components/providers/sse-provider'
import { Toaster } from '@/components/ui/toaster'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AI Scientist Platform',
  description: 'Transform scientific hypotheses into complete experiment plans using AI',
  keywords: ['AI', 'science', 'experiment', 'planning', 'research', 'hypothesis'],
  authors: [{ name: 'AI Scientist Platform Team' }],
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <SSEProvider>
          <div className="min-h-screen bg-background font-sans antialiased">
            <div className="relative flex min-h-screen flex-col">
              <div className="flex-1">
                {children}
              </div>
            </div>
          </div>
          <Toaster />
        </SSEProvider>
      </body>
    </html>
  )
}