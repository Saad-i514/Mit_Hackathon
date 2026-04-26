import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { SSEProvider } from '@/components/providers/sse-provider'
import { Toaster as SonnerToaster } from 'sonner'
import { ThemeProvider } from '@/components/theme-provider'
import { CursorParticles } from '@/components/cursor-particles'

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
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          forcedTheme="dark"
          disableTransitionOnChange
        >
          <SSEProvider>
            <CursorParticles />
            <div className="relative z-10 min-h-screen font-sans antialiased">
              <div className="flex min-h-screen flex-col">
                <div className="flex-1">
                  {children}
                </div>
              </div>
            </div>
            <SonnerToaster position="bottom-right" richColors closeButton />
          </SSEProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}