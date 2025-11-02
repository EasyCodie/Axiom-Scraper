import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Skeleton,
  TokenAvatar,
  SearchBar,
} from '@/components/ui';
import Link from 'next/link';

interface TrendingToken {
  ca: string;
  chain: string;
  token_name?: string | null;
  symbol?: string | null;
  score?: number | null;
  price_usd?: number | null;
  price_change_24h?: number | null;
  volume_usd_24h?: number | null;
}

async function getTrendingTokens(): Promise<TrendingToken[]> {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const response = await fetch(`${apiUrl}/tokens?chain=sol&limit=5`, {
      next: { revalidate: 90, tags: ['trending-tokens'] },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch trending tokens');
    }

    const data = await response.json();
    return (data.tokens || [])
      .filter((t: TrendingToken) => t.score != null && t.score > 0)
      .sort((a: TrendingToken, b: TrendingToken) => (b.score || 0) - (a.score || 0))
      .slice(0, 5);
  } catch (error) {
    console.error('Failed to fetch trending tokens:', error);
    return [];
  }
}

export default async function HomePage() {
  const trendingTokens = await getTrendingTokens();

  const formatChange = (change: number | null | undefined): string => {
    if (change == null) return 'N/A';
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(1)}%`;
  };

  const formatNumber = (value: number | null | undefined, prefix = ''): string => {
    if (value == null) return 'N/A';
    if (value >= 1e9) return `${prefix}${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `${prefix}${(value / 1e6).toFixed(2)}M`;
    if (value >= 1e3) return `${prefix}${(value / 1e3).toFixed(2)}K`;
    return `${prefix}${value.toFixed(2)}`;
  };

  return (
    <div className="relative">
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top,#1e293b_0%,_rgba(2,6,23,0.8)_45%,_rgba(2,6,23,0.95)_100%)]" />

      <section className="mx-auto flex w-full max-w-6xl flex-col gap-16 px-4 pb-20 pt-24 md:px-6">
        <div className="grid gap-12 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="flex flex-col gap-8">
            <div className="space-y-4">
              <Badge variant="neutral" className="max-w-fit text-xs uppercase">
                Solana • Live Analytics
              </Badge>
              <h1 className="text-4xl font-semibold tracking-tight text-white sm:text-5xl lg:text-6xl">
                Supercharge your meme coin strategy with real-time intelligence.
              </h1>
              <p className="max-w-xl text-base text-[hsl(var(--muted-foreground))] sm:text-lg">
                Ingest Pulse snapshots, wallet Tracker events, and behavioral analytics to surface
                the next viral opportunity. Built for analysts who need signal, not noise.
              </p>
            </div>

            <div className="w-full max-w-xl">
              <SearchBar placeholder="Search tokens, symbols, or addresses…" />
            </div>

            <div className="flex flex-wrap gap-4">
              <Link href="/discover">
                <Button size="lg">Discover Tokens</Button>
              </Link>
              <Link href="/watchlist">
                <Button size="lg" variant="ghost">
                  View Watchlist
                </Button>
              </Link>
            </div>

            <div className="flex flex-col gap-3 text-sm text-[hsl(var(--muted-foreground))] sm:flex-row sm:items-center">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 animate-pulse rounded-full bg-[hsl(var(--success))]" />
                <span>Live 24/7 data feed</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-[hsl(var(--secondary))]" />
                <span>Backed by Axiom scrapers</span>
              </div>
            </div>
          </div>

          <Card className="border border-white/10 bg-gradient-to-br from-white/5 via-white/[0.03] to-transparent shadow-xl">
            <CardHeader>
              <CardTitle>Trending Tokens</CardTitle>
              <CardDescription>
                Top performing tokens captured from Pulse with high scores and activity.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {trendingTokens.length > 0 ? (
                trendingTokens.map((token) => (
                  <Link
                    key={`${token.ca}-${token.chain}`}
                    href={`/token/${token.ca}?chain=${token.chain}`}
                    className="block"
                  >
                    <div className="flex items-center justify-between gap-4 rounded-lg border border-white/5 bg-white/5 px-4 py-3 transition-colors hover:border-white/10 hover:bg-white/[0.07]">
                      <div className="flex items-center gap-3">
                        <TokenAvatar
                          name={token.token_name || ''}
                          symbol={token.symbol || ''}
                          size="sm"
                        />
                        <div>
                          <p className="text-sm font-semibold text-white">
                            {token.token_name || token.symbol || 'Unknown'}
                          </p>
                          <p className="text-xs uppercase tracking-wide text-[hsl(var(--muted-foreground))]">
                            {token.symbol || 'N/A'}
                          </p>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        {token.price_change_24h != null && (
                          <Badge
                            variant={token.price_change_24h >= 0 ? 'success' : 'destructive'}
                            className="text-xs"
                          >
                            {formatChange(token.price_change_24h)}
                          </Badge>
                        )}
                        {token.volume_usd_24h != null && (
                          <span className="text-xs text-[hsl(var(--muted-foreground))]">
                            Vol: {formatNumber(token.volume_usd_24h, '$')}
                          </span>
                        )}
                      </div>
                    </div>
                  </Link>
                ))
              ) : (
                [...Array(3)].map((_, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between gap-4 rounded-lg border border-white/5 bg-white/5 px-4 py-3"
                  >
                    <div className="flex items-center gap-3">
                      <Skeleton className="h-10 w-10 rounded-full bg-white/[0.07]" />
                      <div className="space-y-1">
                        <Skeleton className="h-4 w-24 bg-white/[0.07]" />
                        <Skeleton className="h-3 w-16 bg-white/[0.07]" />
                      </div>
                    </div>
                    <Skeleton className="h-6 w-16 bg-white/[0.07]" />
                  </div>
                ))
              )}

              <div className="space-y-2 text-sm text-[hsl(var(--muted-foreground))]">
                <p>
                  Get notified when fresh liquidity enters your watchlist and monitor tracker
                  sentiment in real-time.
                </p>
                <p className="text-xs uppercase tracking-wider text-white/60">
                  Synced every 90 seconds.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: 'Active Tokens', value: 'Live tracking', description: 'Solana chain' },
            { label: 'Pulse Snapshots', value: '24/7', description: 'Real-time data' },
            { label: 'Tracker Events', value: 'Streaming', description: 'Wallet activity' },
            { label: 'API Uptime', value: '99.9%', description: 'Reliable service' },
          ].map((metric, index) => (
            <Card key={index} className="border border-white/5 bg-white/[0.04]">
              <CardHeader>
                <CardTitle className="text-sm text-[hsl(var(--muted-foreground))]">
                  {metric.label}
                </CardTitle>
                <CardDescription>{metric.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-2xl font-semibold text-white">{metric.value}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="rounded-xl border border-white/10 bg-gradient-to-br from-white/5 via-white/[0.03] to-transparent p-8 text-center shadow-xl">
          <h2 className="mb-4 text-2xl font-semibold text-white">Ready to discover opportunities?</h2>
          <p className="mx-auto mb-6 max-w-2xl text-[hsl(var(--muted-foreground))]">
            Start exploring token metrics, set up alerts, and build your watchlist. Stay ahead of the market
            with real-time intelligence.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link href="/discover">
              <Button size="lg">Explore Tokens</Button>
            </Link>
            <Link href="/auth/login">
              <Button size="lg" variant="ghost">
                Sign In
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
