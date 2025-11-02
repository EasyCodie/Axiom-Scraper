'use client';

import type * as React from 'react';

import { cn } from '@/lib/utils';

export type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  variant?: 'neutral' | 'success' | 'warning' | 'destructive';
};

const badgeVariants: Record<NonNullable<BadgeProps['variant']>, string> = {
  neutral:
    'bg-[hsl(var(--muted))/0.6] text-[hsl(var(--foreground))] ring-1 ring-[hsl(var(--border))]',
  success:
    'bg-[hsl(var(--success))]/15 text-[hsl(var(--success))] ring-1 ring-[hsl(var(--success))/0.4]',
  warning:
    'bg-[hsl(var(--warning))]/20 text-[hsl(var(--warning))] ring-1 ring-[hsl(var(--warning))/0.5]',
  destructive:
    'bg-[hsl(var(--error))]/20 text-[hsl(var(--error))] ring-1 ring-[hsl(var(--error))/0.5]',
};

export function Badge({ className, variant = 'neutral', ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-3 py-[0.25rem] text-xs font-semibold uppercase tracking-wide',
        badgeVariants[variant],
        className,
      )}
      {...props}
    />
  );
}
