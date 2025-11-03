import { createBrowserClient } from '@supabase/ssr';
import type { SupabaseClient } from '@supabase/supabase-js';

type CreateClientOptions = {
  supabaseUrl?: string;
  supabaseAnonKey?: string;
};

export function createClient(options: CreateClientOptions = {}): SupabaseClient {
  const supabaseUrl = options.supabaseUrl ?? process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = options.supabaseAnonKey ?? process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error('Missing Supabase configuration');
  }

  return createBrowserClient(supabaseUrl, supabaseAnonKey);
}
