import { NextRequest, NextResponse } from 'next/server';

interface RateLimitStore {
  count: number;
  resetAt: number;
}

const rateLimitMap = new Map<string, RateLimitStore>();
const RATE_LIMIT_WINDOW = 60 * 1000; // 1 minute
const RATE_LIMIT_MAX = 30; // 30 requests per minute

const responseCache = new Map<
  string,
  {
    data: any;
    expiresAt: number;
  }
>();
const CACHE_TTL = 10 * 60 * 1000; // 10 minutes

function getClientIp(request: NextRequest): string {
  return (
    request.headers.get('x-forwarded-for')?.split(',')[0] ||
    request.headers.get('x-real-ip') ||
    'unknown'
  );
}

function checkRateLimit(ip: string): boolean {
  const now = Date.now();
  const store = rateLimitMap.get(ip);

  if (!store || store.resetAt < now) {
    rateLimitMap.set(ip, { count: 1, resetAt: now + RATE_LIMIT_WINDOW });
    return true;
  }

  if (store.count >= RATE_LIMIT_MAX) {
    return false;
  }

  store.count++;
  return true;
}

function getCachedResponse(cacheKey: string): any | null {
  const cached = responseCache.get(cacheKey);
  if (cached && cached.expiresAt > Date.now()) {
    return cached.data;
  }
  responseCache.delete(cacheKey);
  return null;
}

function setCachedResponse(cacheKey: string, data: any, ttl: number = CACHE_TTL): void {
  responseCache.set(cacheKey, {
    data,
    expiresAt: Date.now() + ttl,
  });
}

export async function GET(request: NextRequest) {
  const ip = getClientIp(request);

  if (!checkRateLimit(ip)) {
    return NextResponse.json({ error: 'Rate limit exceeded' }, { status: 429 });
  }

  const { searchParams } = new URL(request.url);
  const query = searchParams.get('q');
  const chain = searchParams.get('chain') || 'sol';
  const limit = Math.min(parseInt(searchParams.get('limit') || '20', 10), 100);
  const includeExternal = searchParams.get('include_external') !== 'false';

  if (!query || query.length < 1) {
    return NextResponse.json({ error: 'Query parameter "q" is required' }, { status: 400 });
  }

  const cacheKey = `search:${query}:${chain}:${limit}:${includeExternal}`;
  const cached = getCachedResponse(cacheKey);
  if (cached) {
    return NextResponse.json(cached, {
      headers: {
        'X-Cache': 'HIT',
      },
    });
  }

  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const params = new URLSearchParams({
      q: query,
      chain,
      limit: limit.toString(),
      include_external: includeExternal.toString(),
    });

    const response = await fetch(`${apiUrl}/search?${params}`, {
      headers: {
        'Content-Type': 'application/json',
      },
      next: { revalidate: 0 },
    });

    if (!response.ok) {
      throw new Error(`FastAPI responded with status ${response.status}`);
    }

    const data = await response.json();

    const deduped = new Map<string, any>();
    for (const result of data.results || []) {
      const key = `${result.ca.toLowerCase()}:${result.chain}`;
      if (!deduped.has(key)) {
        deduped.set(key, result);
      } else {
        const existing = deduped.get(key);
        if (result.source === 'local') {
          deduped.set(key, result);
        } else if (existing.source !== 'local' && result.score != null) {
          deduped.set(key, result);
        }
      }
    }

    const mergedResults = Array.from(deduped.values()).slice(0, limit);

    const responseData = {
      results: mergedResults,
      count: mergedResults.length,
      query,
      sources: data.sources || [],
    };

    setCachedResponse(cacheKey, responseData);

    return NextResponse.json(responseData, {
      headers: {
        'X-Cache': 'MISS',
      },
    });
  } catch (error) {
    console.error('Search API error:', error);
    return NextResponse.json(
      {
        error: 'Failed to fetch search results',
        results: [],
        count: 0,
        query,
        sources: [],
      },
      { status: 500 }
    );
  }
}
