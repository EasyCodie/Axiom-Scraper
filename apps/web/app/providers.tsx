'use client';

import { Providers as RootProviders } from '@/components/providers';

export function Providers({ children }: { children: React.ReactNode }) {
  return <RootProviders>{children}</RootProviders>;
}
