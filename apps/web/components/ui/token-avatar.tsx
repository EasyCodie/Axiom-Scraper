'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

export type TokenAvatarProps = {
  name: string;
  symbol?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
};

const sizeMap: Record<NonNullable<TokenAvatarProps['size']>, string> = {
  sm: 'h-8 w-8 text-xs',
  md: 'h-12 w-12 text-sm',
  lg: 'h-16 w-16 text-base',
};

export function TokenAvatar({ name, symbol, size = 'md', className }: TokenAvatarProps) {
  const initials = symbol?.slice(0, 3).toUpperCase() || name.slice(0, 3).toUpperCase();

  return (
    <motion.div
      className={cn(
        'relative grid place-items-center overflow-hidden rounded-full border border-white/10 text-[hsl(var(--foreground))]',
        sizeMap[size],
        className,
      )}
      initial={{ rotate: -5, scale: 0.9, opacity: 0 }}
      animate={{ rotate: 0, scale: 1, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 300, damping: 24 }}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-[hsl(var(--primary))] via-[hsl(var(--accent))] to-[hsl(var(--secondary))]" />
      <span className="relative z-10 font-semibold uppercase tracking-wide text-white">
        {initials}
      </span>
    </motion.div>
  );
}
