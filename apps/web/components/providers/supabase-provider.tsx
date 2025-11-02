'use client';

import { createContext, useContext, useEffect, useMemo, useState } from 'react';

import type { Session, SupabaseClient, User } from '@supabase/supabase-js';
import { createClient } from '@/lib/supabase/client';

export type SupabaseProviderProps = {
  children: React.ReactNode;
};

type SupabaseContextValue = {
  client: SupabaseClient;
  session: Session | null;
  user: User | null;
  isLoading: boolean;
};

const SupabaseContext = createContext<SupabaseContextValue | undefined>(undefined);

export function SupabaseProvider({ children }: SupabaseProviderProps) {
  const [client] = useState(() => createClient());
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const {
          data: { session: currentSession },
        } = await client.auth.getSession();
        setSession(currentSession);
        setUser(currentSession?.user ?? null);
      } catch (error) {
        console.error('Error initializing auth:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();

    const {
      data: { subscription },
    } = client.auth.onAuthStateChange((_event, newSession) => {
      setSession(newSession);
      setUser(newSession?.user ?? null);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [client]);

  const value = useMemo(
    () => ({ client, session, user, isLoading }),
    [client, session, user, isLoading],
  );

  return <SupabaseContext.Provider value={value}>{children}</SupabaseContext.Provider>;
}

export function useSupabase() {
  const context = useContext(SupabaseContext);
  if (context === undefined) {
    throw new Error('useSupabase must be used within SupabaseProvider');
  }
  return context;
}
