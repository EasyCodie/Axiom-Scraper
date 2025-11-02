import type { Metadata } from 'next';
import { inter, jetbrainsMono } from '@/lib/fonts';
import { Providers } from './providers';
import { StickyHeader } from '@/components/layout/sticky-header';
import './globals.css';

export const metadata: Metadata = {
  title: 'Axiom | Meme Coin Scoring Platform',
  description:
    'Track and analyze meme coin performance on Solana with real-time Pulse data and Tracker insights.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${inter.variable} ${jetbrainsMono.variable} font-sans`}>
        <Providers>
          <div className="relative flex min-h-screen flex-col">
            <StickyHeader />
            <main className="flex-1">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
