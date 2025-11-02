import Link from 'next/link';
import { Badge } from './badge';
import { Card, CardContent } from './card';
import { TokenAvatar } from './token-avatar';
import { MetricChip } from './metric-chip';

interface TokenCardProps {
  ca: string;
  chain: string;
  tokenName?: string | null;
  symbol?: string | null;
  score?: number | null;
  priceUsd?: number | null;
  volumeUsd24h?: number | null;
  liquidityUsd?: number | null;
  priceChange24h?: number | null;
  age?: string | null;
  riskLevel?: 'low' | 'medium' | 'high' | null;
}

export function TokenCard({
  ca,
  chain,
  tokenName,
  symbol,
  score,
  priceUsd,
  volumeUsd24h,
  liquidityUsd,
  priceChange24h,
  age,
  riskLevel,
}: TokenCardProps) {
  const formatNumber = (value: number | null | undefined, prefix = ''): string => {
    if (value == null) return 'N/A';
    if (value >= 1e9) return `${prefix}${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `${prefix}${(value / 1e6).toFixed(2)}M`;
    if (value >= 1e3) return `${prefix}${(value / 1e3).toFixed(2)}K`;
    return `${prefix}${value.toFixed(2)}`;
  };

  const getRiskBadgeVariant = (
    risk?: 'low' | 'medium' | 'high' | null
  ): 'success' | 'warning' | 'destructive' | 'neutral' => {
    if (!risk) return 'neutral';
    switch (risk) {
      case 'low':
        return 'success';
      case 'medium':
        return 'warning';
      case 'high':
        return 'destructive';
      default:
        return 'neutral';
    }
  };

  return (
    <Link href={`/token/${ca}?chain=${chain}`}>
      <Card className="group cursor-pointer border border-white/5 bg-white/[0.02] transition-all duration-200 hover:border-white/10 hover:bg-white/[0.04] hover:shadow-lg">
        <CardContent className="space-y-4 p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <TokenAvatar name={tokenName || ''} symbol={symbol || ''} size="md" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-white">
                  {tokenName || 'Unknown Token'}
                </p>
                <p className="truncate text-xs uppercase tracking-wide text-[hsl(var(--muted-foreground))]">
                  {symbol || 'N/A'}
                </p>
              </div>
            </div>
            {riskLevel && (
              <Badge variant={getRiskBadgeVariant(riskLevel)} className="text-xs uppercase">
                {riskLevel}
              </Badge>
            )}
          </div>

          <div className="grid grid-cols-2 gap-2">
            {priceUsd != null && (
              <MetricChip
                label="Price"
                value={formatNumber(priceUsd, '$')}
                delta={priceChange24h}
              />
            )}
            {score != null && (
              <MetricChip label="Score" value={score.toFixed(1)} variant="neutral" />
            )}
            {volumeUsd24h != null && (
              <MetricChip label="Volume 24h" value={formatNumber(volumeUsd24h, '$')} />
            )}
            {liquidityUsd != null && (
              <MetricChip label="Liquidity" value={formatNumber(liquidityUsd, '$')} />
            )}
          </div>

          {age && (
            <div className="pt-2 text-xs text-[hsl(var(--muted-foreground))]">
              <span className="opacity-60">Age:</span> {age}
            </div>
          )}

          <div className="truncate pt-1 text-xs font-mono text-[hsl(var(--muted-foreground))] opacity-50">
            {ca.slice(0, 8)}...{ca.slice(-6)}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
