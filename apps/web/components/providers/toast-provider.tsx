'use client';

import { Toaster } from 'sonner';

export function ToastProvider() {
  return (
    <Toaster
      position="top-right"
      toastOptions={{
        classNames: {
          toast: 'bg-[hsl(var(--card))] border-[hsl(var(--border))] text-[hsl(var(--foreground))]',
          title: 'text-sm font-medium',
          description: 'text-sm text-[hsl(var(--muted-foreground))]',
          actionButton: 'bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]',
          cancelButton: 'bg-[hsl(var(--muted))] text-[hsl(var(--muted-foreground))]',
          error: 'bg-[hsl(var(--error))] border-[hsl(var(--error))]',
          success: 'bg-[hsl(var(--success))] border-[hsl(var(--success))]',
          warning: 'bg-[hsl(var(--warning))] border-[hsl(var(--warning))]',
          info: 'bg-[hsl(var(--info))] border-[hsl(var(--info))]',
        },
      }}
    />
  );
}
