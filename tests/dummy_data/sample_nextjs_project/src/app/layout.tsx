import React from 'react'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Sample App',
  description: 'A sample Next.js application',
}

interface RootLayoutProps {
  children: React.ReactNode
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

function Header() {
  return (
    <header>
      <nav>
        <a href="/">Home</a>
        <a href="/about">About</a>
      </nav>
    </header>
  )
}

const Footer: React.FC = () => {
  return (
    <footer>
      <p>Copyright 2024</p>
    </footer>
  )
}
