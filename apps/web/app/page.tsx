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
} from '@/components/ui';

const sampleTokens = [
  { name: 'Solana Pepe', symbol: 'SPEPE', change: '+18.4%' },
  { name: 'Goofy Gator', symbol: 'GGTR', change: '+12.1%' },
  { name: 'Axiom Labs', symbol: 'AXL', change: '+45.0%' },
];

export default function HomePage() {
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

            <div className="flex flex-wrap gap-4">
              <Button size="lg">Open dashboard</Button>
              <Button size="lg" variant="ghost">
                View changelog
              </Button>
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
              <CardTitle>Live token momentum</CardTitle>
              <CardDescription>
                Sample of trending tokens captured from Pulse with signal attribution.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {sampleTokens.map((token) => (
                <div
                  key={token.symbol}
                  className="flex items-center justify-between gap-4 rounded-lg border border-white/5 bg-white/5 px-4 py-3"
                >
                  <div className="flex items-center gap-3">
                    <TokenAvatar name={token.name} symbol={token.symbol} size="sm" />
                    <div>
                      <p className="text-sm font-semibold text-white">{token.name}</p>
                      <p className="text-xs uppercase tracking-wide text-[hsl(var(--muted-foreground))]">
                        {token.symbol}
                      </p>
                    </div>
                  </div>
                  <Badge variant="success">{token.change}</Badge>
                </div>
              ))}

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
          {[...Array(4)].map((_, index) => (
            <Card key={index} className="border border-white/5 bg-white/[0.04]">
              <CardHeader>
                <CardTitle className="text-sm text-[hsl(var(--muted-foreground))]">
                  Pipeline overview
                </CardTitle>
                <CardDescription>Observability metrics</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Skeleton className="h-10 w-3/5 bg-white/[0.07]" />
                <Skeleton className="h-10 w-2/5 bg-white/[0.07]" />
                <Skeleton className="h-10 w-4/5 bg-white/[0.07]" />
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
