'use client';

import { motion, useScroll, useTransform } from 'framer-motion';
import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export function StickyHeader() {
  const { scrollY } = useScroll();
  const background = useTransform(scrollY, [0, 120], ['rgba(8,11,19,0.65)', 'rgba(8,11,19,0.92)']);
  const blur = useTransform(scrollY, [0, 120], ['blur(12px)', 'blur(18px)']);
  const border = useTransform(
    scrollY,
    [0, 120],
    ['1px solid rgba(255,255,255,0.12)', '1px solid rgba(255,255,255,0.28)'],
  );

  return (
    <motion.header
      className="sticky top-0 z-50 w-full"
      style={{
        background,
        backdropFilter: blur,
        WebkitBackdropFilter: blur,
        borderBottom: border,
      }}
    >
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-4 md:px-6">
        <Link
          href="/"
          className="group flex items-center space-x-2 font-semibold text-[hsl(var(--foreground))]"
        >
          <span
            className={cn(
              'grid h-9 w-9 place-items-center rounded-lg border border-white/10 bg-gradient-to-br from-[hsl(var(--primary))] to-[hsl(var(--secondary))] text-lg text-white transition-transform group-hover:scale-110',
            )}
          >
            λ
          </span>
          <div className="flex flex-col leading-none">
            <span className="text-sm uppercase tracking-[0.25em] text-[hsl(var(--muted-foreground))]">
              Axiom
            </span>
            <span className="text-base">Meme Coin Ops</span>
          </div>
        </Link>

        <nav className="hidden items-center space-x-6 text-sm font-medium text-[hsl(var(--muted-foreground))] md:flex">
          <Link href="/pulse" className="transition-colors hover:text-[hsl(var(--foreground))]">
            Pulse
          </Link>
          <Link href="/trackers" className="transition-colors hover:text-[hsl(var(--foreground))]">
            Trackers
          </Link>
          <Link href="/analytics" className="transition-colors hover:text-[hsl(var(--foreground))]">
            Analytics
          </Link>
          <Link href="/docs" className="transition-colors hover:text-[hsl(var(--foreground))]">
            Docs
          </Link>
        </nav>

        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="sm" className="hidden md:inline-flex">
            Log in
          </Button>
          <Button size="sm" className="shadow-glow-sm">
            Request access
          </Button>
        </div>
      </div>
    </motion.header>
  );
}
