'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { SearchIcon } from 'lucide-react';

import { cn } from '@/lib/utils';
import { Badge } from './badge';
import { Popover, PopoverContent, PopoverTrigger } from './popover';
import { Skeleton } from './skeleton';

interface SearchResult {
  ca: string;
  chain: string;
  token_name?: string | null;
  symbol?: string | null;
  score?: number | null;
  price_usd?: number | null;
  source: string;
}

interface SearchResponse {
  results: SearchResult[];
  count: number;
  query: string;
  sources: string[];
  error?: string;
}

interface SearchBarProps {
  placeholder?: string;
  debounceMs?: number;
  className?: string;
  onSelectResult?: (result: SearchResult) => void;
}

export function SearchBar({
  placeholder = 'Search tokens, symbols, or addresses…',
  debounceMs = 300,
  className,
  onSelectResult,
}: SearchBarProps) {
  const router = useRouter();
  const [query, setQuery] = React.useState('');
  const [open, setOpen] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [results, setResults] = React.useState<SearchResult[]>([]);
  const [activeIndex, setActiveIndex] = React.useState<number>(-1);

  const abortRef = React.useRef<AbortController | null>(null);
  const debounceRef = React.useRef<NodeJS.Timeout | null>(null);

  const handleSelect = React.useCallback(
    (result: SearchResult) => {
      if (!result) return;
      if (onSelectResult) {
        onSelectResult(result);
      } else {
        router.push(`/token/${result.ca}?chain=${result.chain}`);
      }
      setOpen(false);
      setActiveIndex(-1);
    },
    [onSelectResult, router]
  );

  React.useEffect(() => {
    if (!query) {
      setResults([]);
      setLoading(false);
      setError(null);
      return;
    }

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(async () => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setLoading(true);
      setError(null);

      try {
        const params = new URLSearchParams({ q: query, chain: 'sol', limit: '10' });
        const response = await fetch(`/api/search?${params}`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error('Search failed');
        }

        const data = (await response.json()) as SearchResponse;
        setResults(data.results ?? []);
        setActiveIndex(data.results && data.results.length > 0 ? 0 : -1);
      } catch (err) {
        if ((err as DOMException).name === 'AbortError') return;
        setError('Unable to fetch results. Try again.');
        setActiveIndex(-1);
      } finally {
        setLoading(false);
      }
    }, debounceMs);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
      abortRef.current?.abort();
    };
  }, [query, debounceMs]);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setActiveIndex((prev) => Math.min(prev + 1, results.length - 1));
      setOpen(true);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      setActiveIndex((prev) => Math.max(prev - 1, 0));
    } else if (event.key === 'Enter') {
      if (activeIndex >= 0 && activeIndex < results.length) {
        handleSelect(results[activeIndex]);
      }
    } else if (event.key === 'Escape') {
      setOpen(false);
      setActiveIndex(-1);
    }
  };

  return (
    <Popover open={open} onOpenChange={(next) => setOpen(next)}>
      <PopoverTrigger>
        <div className={cn('relative w-full max-w-xl', className)}>
          <SearchIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[hsl(var(--muted-foreground))]" />
          <input
            className="w-full rounded-lg border border-white/5 bg-white/[0.02] py-2 pl-10 pr-4 text-sm text-white outline-none transition focus:border-white/20 focus:bg-white/[0.05]"
            placeholder={placeholder}
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setOpen(true);
            }}
            onFocus={() => setOpen(true)}
            onKeyDown={handleKeyDown}
            aria-autocomplete="list"
            aria-expanded={open}
            aria-controls="search-results"
            role="combobox"
          />
        </div>
      </PopoverTrigger>
      <PopoverContent open={open} align="start" className="w-[var(--radix-popover-trigger-width,24rem)]">
        <div
          id="search-results"
          role="listbox"
          aria-activedescendant={activeIndex >= 0 ? `search-result-${activeIndex}` : undefined}
          className="max-h-96 w-full space-y-1 overflow-y-auto"
        >
          {loading && (
            <div className="space-y-2 p-2">
              {[...Array(4)].map((_, index) => (
                <Skeleton key={index} className="h-10 w-full bg-white/[0.08]" />
              ))}
            </div>
          )}

          {!loading && error && (
            <div className="p-3 text-sm text-red-400">{error}</div>
          )}

          {!loading && !error && results.length === 0 && query && (
            <div className="p-3 text-sm text-[hsl(var(--muted-foreground))]">
              No results found for “{query}”.
            </div>
          )}

          {!loading && !error &&
            results.map((result, index) => (
              <button
                key={`${result.ca}-${index}`}
                id={`search-result-${index}`}
                role="option"
                aria-selected={activeIndex === index}
                onClick={() => handleSelect(result)}
                onMouseEnter={() => setActiveIndex(index)}
                className={cn(
                  'flex w-full items-center justify-between gap-3 rounded-lg border border-transparent p-3 text-left transition-colors',
                  activeIndex === index
                    ? 'border-white/20 bg-white/[0.08] text-white'
                    : 'bg-white/[0.03] text-white/80 hover:border-white/10 hover:bg-white/[0.06]'
                )}
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-white">
                    {result.token_name || result.symbol || result.ca.slice(0, 8)}
                  </p>
                  <p className="truncate text-xs text-[hsl(var(--muted-foreground))]">
                    {result.symbol ? `${result.symbol} • ${result.chain.toUpperCase()}` : result.chain}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {result.score != null && (
                    <Badge variant="neutral" className="text-xs uppercase">
                      Score {result.score.toFixed(1)}
                    </Badge>
                  )}
                  <Badge variant="outline" className="text-xs uppercase">
                    {result.source}
                  </Badge>
                </div>
              </button>
            ))}
        </div>
      </PopoverContent>
    </Popover>
  );
}
