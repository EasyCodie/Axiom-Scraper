'use client';

import { createContext, useContext, useMemo } from 'react';

import type { SupabaseClient } from '@supabase/supabase-js';

export type SupabaseProviderProps = {
  children: React.ReactNode;
  client?: SupabaseClient | null;
};

type SupabaseContextValue = {
  /** Placeholder for future supabase client */
  client: SupabaseClient | null;
};

const SupabaseContext = createContext<SupabaseContextValue>({
  client: null,
});

export function SupabaseProvider({ children, client = null }: SupabaseProviderProps) {
  const value = useMemo(() => ({ client }), [client]);
  return <SupabaseContext.Provider value={value}>{children}</SupabaseContext.Provider>;
}

export function useSupabase() {
  return useContext(SupabaseContext);
}
