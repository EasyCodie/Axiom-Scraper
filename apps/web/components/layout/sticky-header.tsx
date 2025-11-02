'use client';

import { useEffect, useMemo, useState } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import Link from 'next/link';
import Image from 'next/image';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useSupabase } from '@/components/providers';
import { LoginModal } from '@/components/auth/login-modal';

export function StickyHeader() {
  const { scrollY } = useScroll();
  const background = useTransform(scrollY, [0, 120], ['rgba(8,11,19,0.65)', 'rgba(8,11,19,0.92)']);
  const blur = useTransform(scrollY, [0, 120], ['blur(12px)', 'blur(18px)']);
  const border = useTransform(
    scrollY,
    [0, 120],
    ['1px solid rgba(255,255,255,0.12)', '1px solid rgba(255,255,255,0.28)'],
  );
  const { user, client, isLoading } = useSupabase();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [avatarFallback, setAvatarFallback] = useState('');

  useEffect(() => {
    if (user?.email) {
      const fallback = user.email
        .split('@')[0]
        .split('.')
        .map((part) => part.charAt(0).toUpperCase())
        .join('')
        .slice(0, 2);
      setAvatarFallback(fallback || 'AX');
    } else if (user?.user_metadata?.full_name) {
      setAvatarFallback(
        user.user_metadata.full_name
          .split(' ')
          .map((part: string) => part.charAt(0).toUpperCase())
          .join('')
          .slice(0, 2),
      );
    } else {
      setAvatarFallback('AX');
    }
  }, [user]);

  const redirectParams = useMemo(() => {
    if (typeof window === 'undefined') {
      return undefined;
    }
    const params = new URLSearchParams(window.location.search);
    if (params.get('auth') === 'required') {
      return params.get('redirect') || '/watchlist';
    }
    return params.get('redirect') || undefined;
  }, []);

  useEffect(() => {
    if (!isLoading && redirectParams && !user) {
      setIsModalOpen(true);
      toast.info('Authentication required', {
        description: 'Sign in to access this feature.',
      });

      if (typeof window !== 'undefined') {
        const url = new URL(window.location.href);
        url.searchParams.delete('auth');
        window.history.replaceState({}, '', url.toString());
      }
    }
  }, [isLoading, redirectParams, user]);

  useEffect(() => {
    if (user && typeof window !== 'undefined') {
      const url = new URL(window.location.href);
      if (url.searchParams.has('redirect')) {
        url.searchParams.delete('redirect');
        window.history.replaceState({}, '', url.toString());
      }
      setIsModalOpen(false);
    }
  }, [user]);

  const handleLogout = async () => {
    const { error } = await client.auth.signOut();
    if (error) {
      toast.error('Failed to sign out', { description: error.message });
    } else {
      toast.success('Signed out');
      if (typeof window !== 'undefined') {
        window.location.href = '/';
      }
    }
  };

  return (
    <>
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
            <Link
              href="/discover"
              className="transition-colors hover:text-[hsl(var(--foreground))]"
            >
              Discover
            </Link>
            <Link href="/pulse" className="transition-colors hover:text-[hsl(var(--foreground))]">
              Pulse
            </Link>
            <Link
              href="/trackers"
              className="transition-colors hover:text-[hsl(var(--foreground))]"
            >
              Trackers
            </Link>
            <Link
              href="/analytics"
              className="transition-colors hover:text-[hsl(var(--foreground))]"
            >
              Analytics
            </Link>
            <Link href="/docs" className="transition-colors hover:text-[hsl(var(--foreground))]">
              Docs
            </Link>
          </nav>

          <div className="flex items-center space-x-4">
            {user ? (
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  {user.user_metadata?.avatar_url ? (
                    <Image
                      src={user.user_metadata.avatar_url}
                      alt={user.user_metadata.full_name || 'User avatar'}
                      width={32}
                      height={32}
                      className="h-8 w-8 rounded-full border border-white/10 object-cover"
                    />
                  ) : (
                    <div className="grid h-8 w-8 place-items-center rounded-full border border-white/10 bg-white/10 text-sm font-semibold text-white">
                      {avatarFallback}
                    </div>
                  )}
                  <div className="hidden flex-col text-left text-xs text-[hsl(var(--muted-foreground))] sm:flex">
                    <span className="text-white">
                      {user.user_metadata?.full_name ?? user.email}
                    </span>
                    <span>Signed in</span>
                  </div>
                </div>
                <Button variant="ghost" size="sm" onClick={handleLogout}>
                  Sign out
                </Button>
              </div>
            ) : (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  className="hidden md:inline-flex"
                  onClick={() => setIsModalOpen(true)}
                >
                  Log in
                </Button>
                <Button size="sm" className="shadow-glow-sm" onClick={() => setIsModalOpen(true)}>
                  Request access
                </Button>
              </>
            )}
          </div>
        </div>
      </motion.header>

      <LoginModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        redirectTo={redirectParams}
      />
    </>
  );
}
