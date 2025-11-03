'use client';

import * as React from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';

import {
  DEFAULT_CHAIN,
  countActiveFilters,
  serializeDiscoveryFilters,
  type DiscoveryFilters,
  type DiscoveryToken,
} from '@/lib/discovery';

import { Badge, Button, FilterDrawer, TokenCard } from '@/components/ui';

interface DiscoverClientProps {
  tokens: (DiscoveryToken & {
    ca: string;
    token_name?: string | null;
    symbol?: string | null;
    price_usd?: number | null;
    price_change_24h?: number | null;
  })[];
  filters: DiscoveryFilters;
  totalTokens: number;
  updatedAt: string;
}

export function DiscoverClient({ tokens, filters, totalTokens, updatedAt }: DiscoverClientProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [viewMode, setViewMode] = React.useState<'grid' | 'list'>('grid');
  const [localFilters, setLocalFilters] = React.useState<DiscoveryFilters>({
    chain: filters.chain ?? DEFAULT_CHAIN,
    ...filters,
  });
  const [isPending, startTransition] = React.useTransition();

  React.useEffect(() => {
    setLocalFilters({ chain: filters.chain ?? DEFAULT_CHAIN, ...filters });
  }, [filters]);

  const handleApplyFilters = React.useCallback(
    (nextFilters: DiscoveryFilters) => {
      const mergedFilters: DiscoveryFilters = {
        chain: nextFilters.chain ?? DEFAULT_CHAIN,
        ...nextFilters,
      };
      setLocalFilters(mergedFilters);

      startTransition(() => {
        const params = serializeDiscoveryFilters(mergedFilters);
        const query = params.toString();
        router.replace(query ? `${pathname}?${query}` : pathname);
      });
    },
    [pathname, router],
  );

  const handleClearFilters = React.useCallback(() => {
    setLocalFilters({ chain: DEFAULT_CHAIN });
    startTransition(() => {
      router.replace(pathname);
    });
  }, [pathname, router]);

  const activeFiltersCount = countActiveFilters(filters);

  const formatAge = (days: number | null | undefined): string => {
    if (days == null) return 'N/A';
    if (days < 1) return '< 1 day';
    if (days < 7) return `${Math.floor(days)} days`;
    if (days < 30) return `${Math.floor(days / 7)} weeks`;
    return `${Math.floor(days / 30)} months`;
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            Discover Tokens
          </h1>
          <p className="mt-2 text-sm text-[hsl(var(--muted-foreground))]">
            Explore and filter tokens by chain, score, volume, liquidity, and age. Updated at{' '}
            {new Date(updatedAt).toLocaleTimeString()}.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <FilterDrawer
            value={localFilters}
            onApply={handleApplyFilters}
            onClear={handleClearFilters}
          />
          <div className="flex gap-2">
            <Button
              variant={viewMode === 'grid' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('grid')}
            >
              Grid
            </Button>
            <Button
              variant={viewMode === 'list' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('list')}
            >
              List
            </Button>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 text-xs text-[hsl(var(--muted-foreground))]">
        <span>
          Showing {tokens.length} of {totalTokens} tokens
        </span>
        {activeFiltersCount > 0 && (
          <>
            <span>•</span>
            <Badge variant="neutral" className="text-xs">
              {activeFiltersCount} filter{activeFiltersCount === 1 ? '' : 's'} applied
            </Badge>
          </>
        )}
        <span>•</span>
        <span className="uppercase">ISR refresh every 120s</span>
        {isPending && (
          <>
            <span>•</span>
            <span className="animate-pulse text-white/80">Updating…</span>
          </>
        )}
      </div>

      {tokens.length === 0 ? (
        <div className="flex min-h-[400px] items-center justify-center rounded-lg border border-white/5 bg-white/[0.02]">
          <div className="text-center">
            <p className="text-lg font-medium text-white">No tokens found</p>
            <p className="mt-2 text-sm text-[hsl(var(--muted-foreground))]">
              Try adjusting your filters or check back later.
            </p>
          </div>
        </div>
      ) : (
        <div
          className={viewMode === 'grid' ? 'grid gap-4 sm:grid-cols-2 lg:grid-cols-3' : 'space-y-4'}
        >
          {tokens.map((token) => (
            <TokenCard
              key={`${token.ca}-${token.chain}`}
              ca={token.ca}
              chain={token.chain}
              tokenName={token.token_name}
              symbol={token.symbol}
              score={token.score}
              priceUsd={token.price_usd}
              volumeUsd24h={token.volume_usd_24h}
              liquidityUsd={token.liquidity_usd}
              priceChange24h={token.price_change_24h}
              age={formatAge(token.age_days)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
