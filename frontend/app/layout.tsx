import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'AI Visibility Score Tracker',
  description: 'Measure brand visibility across AI models',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
