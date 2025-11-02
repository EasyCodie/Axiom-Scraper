import { DEFAULT_CHAIN, parseDiscoveryFilters, applyDiscoveryFilters } from '@/lib/discovery';
import { DiscoverClient } from '@/components/discover/discover-client';

export const revalidate = 120;

interface PageProps {
  searchParams: { [key: string]: string | string[] | undefined };
}

interface Token {
  ca: string;
  chain: string;
  token_name?: string | null;
  symbol?: string | null;
  score?: number | null;
  price_usd?: number | null;
  volume_usd_24h?: number | null;
  liquidity_usd?: number | null;
  price_change_24h?: number | null;
  age_days?: number | null;
  last_seen_at?: string | null;
}

async function fetchTokens(chain: string): Promise<Token[]> {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const params = new URLSearchParams({ chain, limit: '300' });

    const response = await fetch(`${apiUrl}/tokens?${params}`, {
      next: { revalidate: 120, tags: ['discovery-tokens'] },
    });

    if (!response.ok) {
      console.error(`Token fetch failed: ${response.status}`);
      return [];
    }

    const data = await response.json();
    return data.tokens || [];
  } catch (error) {
    console.error('Failed to fetch tokens:', error);
    return [];
  }
}

export default async function DiscoverPage({ searchParams }: PageProps) {
  const filters = parseDiscoveryFilters(searchParams);
  const chain = filters.chain ?? DEFAULT_CHAIN;

  const allTokens = await fetchTokens(chain);
  const filteredTokens = applyDiscoveryFilters(allTokens, filters);

  return (
    <div className="relative min-h-screen">
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top,#1e293b_0%,_rgba(2,6,23,0.8)_45%,_rgba(2,6,23,0.95)_100%)]" />
      <div className="mx-auto max-w-7xl px-4 py-16 md:px-6">
        <DiscoverClient
          tokens={filteredTokens}
          filters={filters}
          totalTokens={allTokens.length}
          updatedAt={new Date().toISOString()}
        />
      </div>
    </div>
  );
}
