export type ChainId = 'sol' | 'eth' | 'bsc' | 'base' | 'arbitrum' | 'optimism' | 'all';

export interface DiscoveryFilters {
  chain?: ChainId;
  minScore?: number;
  maxScore?: number;
  minVolume?: number;
  maxVolume?: number;
  minLiquidity?: number;
  maxLiquidity?: number;
  minAge?: number;
  maxAge?: number;
  search?: string;
  tags?: string[];
}

export interface DiscoveryToken {
  ca: string;
  chain: string;
  score?: number | null;
  volume_usd_24h?: number | null;
  liquidity_usd?: number | null;
  age_days?: number | null;
}

export const DEFAULT_CHAIN: ChainId = 'sol';

export const DEFAULT_FILTERS: DiscoveryFilters = {
  chain: DEFAULT_CHAIN,
};

export function countActiveFilters(filters: DiscoveryFilters): number {
  let count = 0;

  if (filters.chain && filters.chain !== DEFAULT_CHAIN) {
    count++;
  }

  if (filters.minScore !== undefined || filters.maxScore !== undefined) {
    count++;
  }

  if (filters.minVolume !== undefined || filters.maxVolume !== undefined) {
    count++;
  }

  if (filters.minLiquidity !== undefined || filters.maxLiquidity !== undefined) {
    count++;
  }

  if (filters.minAge !== undefined || filters.maxAge !== undefined) {
    count++;
  }

  if (filters.search && filters.search.trim().length > 0) {
    count++;
  }

  if (filters.tags && filters.tags.length > 0) {
    count++;
  }

  return count;
}

export function parseDiscoveryFilters(searchParams: {
  [key: string]: string | string[] | undefined;
}): DiscoveryFilters {
  const filters: DiscoveryFilters = {};

  const chain = searchParams.chain;
  if (typeof chain === 'string') {
    filters.chain = chain as ChainId;
  }

  const parseNumber = (value: string | string[] | undefined): number | undefined => {
    if (typeof value === 'string') {
      const num = Number(value);
      return Number.isNaN(num) ? undefined : num;
    }
    return undefined;
  };

  filters.minScore = parseNumber(searchParams.minScore);
  filters.maxScore = parseNumber(searchParams.maxScore);
  filters.minVolume = parseNumber(searchParams.minVolume);
  filters.maxVolume = parseNumber(searchParams.maxVolume);
  filters.minLiquidity = parseNumber(searchParams.minLiquidity);
  filters.maxLiquidity = parseNumber(searchParams.maxLiquidity);
  filters.minAge = parseNumber(searchParams.minAge);
  filters.maxAge = parseNumber(searchParams.maxAge);

  const search = searchParams.search;
  if (typeof search === 'string') {
    filters.search = search;
  }

  const tags = searchParams.tags;
  if (typeof tags === 'string') {
    filters.tags = tags.split(',').filter(Boolean);
  } else if (Array.isArray(tags)) {
    filters.tags = tags.filter((t): t is string => typeof t === 'string');
  }

  return filters;
}

export function serializeDiscoveryFilters(filters: DiscoveryFilters): URLSearchParams {
  const params = new URLSearchParams();

  if (filters.chain && filters.chain !== DEFAULT_CHAIN) {
    params.set('chain', filters.chain);
  }

  if (filters.minScore !== undefined) {
    params.set('minScore', String(filters.minScore));
  }
  if (filters.maxScore !== undefined) {
    params.set('maxScore', String(filters.maxScore));
  }

  if (filters.minVolume !== undefined) {
    params.set('minVolume', String(filters.minVolume));
  }
  if (filters.maxVolume !== undefined) {
    params.set('maxVolume', String(filters.maxVolume));
  }

  if (filters.minLiquidity !== undefined) {
    params.set('minLiquidity', String(filters.minLiquidity));
  }
  if (filters.maxLiquidity !== undefined) {
    params.set('maxLiquidity', String(filters.maxLiquidity));
  }

  if (filters.minAge !== undefined) {
    params.set('minAge', String(filters.minAge));
  }
  if (filters.maxAge !== undefined) {
    params.set('maxAge', String(filters.maxAge));
  }

  if (filters.search && filters.search.trim().length > 0) {
    params.set('search', filters.search);
  }

  if (filters.tags && filters.tags.length > 0) {
    params.set('tags', filters.tags.join(','));
  }

  return params;
}

export function applyDiscoveryFilters<T extends DiscoveryToken>(
  tokens: T[],
  filters: DiscoveryFilters,
): T[] {
  return tokens.filter((token) => {
    if (filters.chain && filters.chain !== 'all' && token.chain !== filters.chain) {
      return false;
    }

    if (filters.minScore !== undefined && (token.score ?? 0) < filters.minScore) {
      return false;
    }
    if (filters.maxScore !== undefined && (token.score ?? 0) > filters.maxScore) {
      return false;
    }

    if (filters.minVolume !== undefined && (token.volume_usd_24h ?? 0) < filters.minVolume) {
      return false;
    }
    if (filters.maxVolume !== undefined && (token.volume_usd_24h ?? 0) > filters.maxVolume) {
      return false;
    }

    if (filters.minLiquidity !== undefined && (token.liquidity_usd ?? 0) < filters.minLiquidity) {
      return false;
    }
    if (filters.maxLiquidity !== undefined && (token.liquidity_usd ?? 0) > filters.maxLiquidity) {
      return false;
    }

    if (filters.minAge !== undefined && (token.age_days ?? 0) < filters.minAge) {
      return false;
    }
    if (filters.maxAge !== undefined && (token.age_days ?? 0) > filters.maxAge) {
      return false;
    }

    return true;
  });
}
