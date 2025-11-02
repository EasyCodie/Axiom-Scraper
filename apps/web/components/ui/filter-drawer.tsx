'use client';

import * as React from 'react';
import { FilterIcon, XIcon } from 'lucide-react';

import { DEFAULT_CHAIN, countActiveFilters, type DiscoveryFilters } from '@/lib/discovery';
import { cn } from '@/lib/utils';

import { Badge } from './badge';
import { Button } from './button';

interface FilterDrawerProps {
  value: DiscoveryFilters;
  onApply: (filters: DiscoveryFilters) => void;
  onClear?: () => void;
  className?: string;
}

export function FilterDrawer({ value, onApply, onClear, className }: FilterDrawerProps) {
  const [open, setOpen] = React.useState(false);
  const [draft, setDraft] = React.useState<DiscoveryFilters>(value);

  React.useEffect(() => {
    setDraft(value);
  }, [value]);

  const updateDraft = (key: keyof DiscoveryFilters, rawValue: string) => {
    const next = { ...draft };
    if (rawValue === '') {
      delete next[key];
    } else if (key === 'chain') {
      next[key] = rawValue;
    } else {
      const numeric = Number(rawValue);
      next[key] = Number.isNaN(numeric) ? undefined : numeric;
    }
    setDraft(next);
  };

  const handleClear = () => {
    const cleared: DiscoveryFilters = { chain: value.chain ?? DEFAULT_CHAIN };
    setDraft(cleared);
    onClear?.();
    onApply(cleared);
    setOpen(false);
  };

  const handleApply = () => {
    onApply(draft);
    setOpen(false);
  };

  const activeFiltersCount = countActiveFilters(value);

  return (
    <div className={cn('relative', className)}>
      <Button
        variant={activeFiltersCount > 0 ? 'default' : 'ghost'}
        size="default"
        onClick={() => setOpen((prev) => !prev)}
        className="gap-2"
      >
        <FilterIcon className="h-4 w-4" />
        Filters
        {activeFiltersCount > 0 && (
          <Badge variant="neutral" className="ml-1 h-5 w-5 rounded-full p-0 text-xs">
            {activeFiltersCount}
          </Badge>
        )}
      </Button>

      {open && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
            onClick={() => setOpen(false)}
          />
          <div className="fixed inset-y-0 right-0 z-50 w-full max-w-sm border-l border-white/10 bg-[hsl(var(--background))] p-6 shadow-2xl">
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-white">Filters</h2>
              <Button variant="ghost" size="sm" onClick={() => setOpen(false)}>
                <XIcon className="h-5 w-5" />
              </Button>
            </div>

            <div className="space-y-6">
              <FilterSection label="Chain">
                <select
                  className="w-full rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white outline-none transition focus:border-white/20 focus:bg-white/[0.05]"
                  value={draft.chain ?? DEFAULT_CHAIN}
                  onChange={(event) => updateDraft('chain', event.target.value)}
                >
                  <option value="sol">Solana</option>
                  <option value="eth">Ethereum</option>
                  <option value="bsc">BSC</option>
                  <option value="base">Base</option>
                </select>
              </FilterSection>

              <FilterSection label="Score Range">
                <RangeInputs
                  minValue={draft.minScore}
                  maxValue={draft.maxScore}
                  minKey="minScore"
                  maxKey="maxScore"
                  onChange={updateDraft}
                  min={0}
                  max={100}
                />
              </FilterSection>

              <FilterSection label="Volume (24h USD)">
                <RangeInputs
                  minValue={draft.minVolume}
                  maxValue={draft.maxVolume}
                  minKey="minVolume"
                  maxKey="maxVolume"
                  onChange={updateDraft}
                />
              </FilterSection>

              <FilterSection label="Liquidity (USD)">
                <RangeInputs
                  minValue={draft.minLiquidity}
                  maxValue={draft.maxLiquidity}
                  minKey="minLiquidity"
                  maxKey="maxLiquidity"
                  onChange={updateDraft}
                />
              </FilterSection>

              <FilterSection label="Age (days)">
                <RangeInputs
                  minValue={draft.minAge}
                  maxValue={draft.maxAge}
                  minKey="minAge"
                  maxKey="maxAge"
                  onChange={updateDraft}
                />
              </FilterSection>

              <div className="flex gap-3 pt-4">
                <Button
                  variant="ghost"
                  size="default"
                  onClick={handleClear}
                  className="flex-1"
                  disabled={activeFiltersCount === 0}
                >
                  Clear All
                </Button>
                <Button
                  variant="default"
                  size="default"
                  onClick={handleApply}
                  className="flex-1"
                >
                  Apply Filters
                </Button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function FilterSection({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-white">{label}</label>
      {children}
    </div>
  );
}

interface RangeInputsProps {
  minValue?: number;
  maxValue?: number;
  minKey: keyof DiscoveryFilters;
  maxKey: keyof DiscoveryFilters;
  onChange: (key: keyof DiscoveryFilters, value: string) => void;
  min?: number;
  max?: number;
}

function RangeInputs({ minValue, maxValue, minKey, maxKey, onChange, min, max }: RangeInputsProps) {
  return (
    <div className="grid grid-cols-2 gap-3">
      <input
        type="number"
        placeholder="Min"
        className="w-full rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white outline-none transition focus:border-white/20 focus:bg-white/[0.05]"
        value={minValue ?? ''}
        onChange={(event) => onChange(minKey, event.target.value)}
        min={min}
        max={max}
      />
      <input
        type="number"
        placeholder="Max"
        className="w-full rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white outline-none transition focus:border-white/20 focus:bg-white/[0.05]"
        value={maxValue ?? ''}
        onChange={(event) => onChange(maxKey, event.target.value)}
        min={min}
        max={max}
      />
    </div>
  );
}
