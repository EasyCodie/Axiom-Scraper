import { cn } from '@/lib/utils';
import { TrendingDownIcon, TrendingUpIcon } from 'lucide-react';

interface MetricChipProps {
  label: string;
  value: string;
  delta?: number | null;
  variant?: 'neutral' | 'success' | 'warning';
}

const variantClasses: Record<MetricChipProps['variant'], string> = {
  neutral: 'bg-white/[0.04] text-white',
  success: 'bg-emerald-500/10 text-emerald-300',
  warning: 'bg-amber-500/10 text-amber-300',
};

export function MetricChip({ label, value, delta, variant = 'neutral' }: MetricChipProps) {
  const deltaVariant = delta == null ? 'neutral' : delta >= 0 ? 'success' : 'warning';
  const DisplayIcon = delta == null ? null : delta >= 0 ? TrendingUpIcon : TrendingDownIcon;

  return (
    <div className="flex flex-col gap-1 rounded-lg border border-white/5 bg-white/[0.02] p-2">
      <span className="text-[11px] uppercase tracking-wide text-[hsl(var(--muted-foreground))]">
        {label}
      </span>
      <div className="flex items-center gap-2">
        <span className="text-sm font-semibold text-white">{value}</span>
        {DisplayIcon && (
          <span
            className={cn(
              'flex items-center gap-0.5 rounded-full px-1 text-[10px] uppercase tracking-wide',
              variantClasses[deltaVariant]
            )}
          >
            <DisplayIcon className="h-3 w-3" />
            {Math.abs(delta ?? 0).toFixed(2)}%
          </span>
        )}
      </div>
    </div>
  );
}
