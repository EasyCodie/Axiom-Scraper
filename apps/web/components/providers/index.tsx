'use client';

import type { ReactNode } from 'react';

import { ThemeProvider } from './theme-provider';
import { SupabaseProvider } from './supabase-provider';

export { useTheme } from './theme-provider';
export { useSupabase } from './supabase-provider';

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider defaultTheme="dark">
      <SupabaseProvider>{children}</SupabaseProvider>
    </ThemeProvider>
  );
}
