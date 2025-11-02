# Discovery Pages Documentation

This document describes the implementation of the discovery pages, search functionality, and related components built to support token browsing and filtering.

## Features

### 1. Search Autocomplete (`/api/search` + `SearchBar`)

**Backend API Route**: `app/api/search/route.ts`
- Rate limits requests (30/minute per IP)
- Caches responses for 10 minutes
- Proxies to FastAPI `/search` endpoint
- Merges and deduplicates results from local DB and Moralis
- Prioritizes local data over external sources

**Frontend Component**: `components/ui/search-bar.tsx`
- Debounced input (300ms default)
- Popover with results display
- Keyboard navigation (Arrow keys, Enter, Escape)
- Loading states with skeleton placeholders
- ARIA-compliant accessibility

**Usage**:
```tsx
import { SearchBar } from '@/components/ui';

<SearchBar 
  placeholder="Search tokens..." 
  debounceMs={300}
  onSelectResult={(result) => console.log(result)}
/>
```

### 2. Discovery Page (`/discover`)

**Server Component**: `app/discover/page.tsx`
- ISR with 120-second revalidation
- Fetches tokens server-side with caching
- Parses filter query parameters
- Applies filters server-side

**Client Component**: `components/discover/discover-client.tsx`
- Interactive filter controls
- URL parameter synchronization
- View mode toggle (grid/list)
- Loading states during transitions

**Filter Support**:
- Chain selection (sol, eth, bsc, base)
- Score range (min/max)
- Volume range (24h USD)
- Liquidity range (USD)
- Age range (days)

**URL Parameters**:
```
/discover?chain=sol&minScore=5&maxScore=10&minVolume=10000
```

### 3. Reusable Components

#### TokenCard (`components/ui/token-card.tsx`)
Displays token information with:
- Token avatar and name
- Symbol and contract address
- Score, price, volume, liquidity metrics
- Price change delta with color coding
- Age display
- Risk badges
- Hover effects and link to detail page

#### MetricChip (`components/ui/metric-chip.tsx`)
Shows a single metric with:
- Label and value
- Optional delta percentage
- Trend icons (up/down arrows)
- Color-coded variants (success, warning, neutral)

#### FilterDrawer (`components/ui/filter-drawer.tsx`)
Full-screen drawer with:
- Draft state management
- Range inputs for numeric filters
- Chain selector dropdown
- Clear all filters button
- Apply filters button
- Active filter count badge

### 4. Homepage Updates (`app/page.tsx`)

Enhanced with:
- Server-side trending tokens fetch (90s cache)
- SearchBar integration
- CTAs to discovery and watchlist
- Live metrics cards
- Responsive design

### 5. Utility Functions (`lib/discovery.ts`)

**Filter Utilities**:
- `parseDiscoveryFilters(params)` - Parse URL params into filter object
- `serializeDiscoveryFilters(filters)` - Convert filters to URL params
- `applyDiscoveryFilters(tokens, filters)` - Client-side filtering logic
- `countActiveFilters(filters)` - Count non-default filters

**Constants**:
- `DEFAULT_CHAIN = 'sol'` - Default chain identifier

## Testing

### Unit Tests (`tests/unit/web/test_search_utils.py`)

Tests for search result deduplication and merging:
- Dedupe same token from different sources
- Handle case-insensitive contract addresses
- Prioritize local results over external
- Merge empty result sets
- Preserve order of appearance

Run with:
```bash
pytest tests/unit/web/test_search_utils.py -v
```

### Integration Tests (Playwright)

**Search Autocomplete** (`tests/integration/test_web_search_autocomplete.py`):
- Display results on input
- Keyboard navigation (arrows, enter, escape)
- Debounce behavior
- Loading states
- Close on escape

**Discovery Filters** (`tests/integration/test_web_discovery_filters.py`):
- Page loads correctly
- Filter drawer opens/closes
- Chain filter application
- Score range filtering
- Volume filtering
- Clear all filters
- View mode toggle
- Token count updates with filters

Run with:
```bash
# Start Next.js dev server first
cd apps/web && npm run dev

# Run tests
pytest tests/integration/test_web_search_autocomplete.py -v
pytest tests/integration/test_web_discovery_filters.py -v
```

## Architecture

### Data Flow

1. **Search**:
   - User types → SearchBar debounces → `/api/search` → FastAPI `/search` + Moralis
   - Results merged, deduped, cached → displayed in popover

2. **Discovery**:
   - URL params parsed → Server fetches tokens (ISR 120s)
   - Filters applied server-side → rendered in client component
   - User changes filters → URL updated → server re-renders

### Caching Strategy

- **Search API**: 10-minute in-memory cache (per query)
- **Homepage Trending**: 90-second revalidation with tags
- **Discovery Tokens**: 120-second ISR with tags

### Rate Limiting

- **Search API**: 30 requests/minute per IP
- Uses in-memory Map with reset timestamps
- Returns 429 status when exceeded

## Future Enhancements

- [ ] Add persistent filter preferences (user settings)
- [ ] Implement sort options (price, volume, score)
- [ ] Add pagination for large result sets
- [ ] Enhance mobile filter drawer UX
- [ ] Add filter presets (e.g., "High Score", "New Tokens")
- [ ] Implement real-time WebSocket updates for live prices
- [ ] Add export functionality (CSV, JSON)
- [ ] Create saved searches feature
