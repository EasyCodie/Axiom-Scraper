# Axiom Web App

Next.js 13+ App Router application for the Axiom Meme Coin Scoring Platform.

## Features

- **Next.js 13+ App Router**: Modern React framework with server components
- **TypeScript**: Full type safety across the application
- **Tailwind CSS**: Utility-first CSS framework with custom dark theme
- **Framer Motion**: Smooth animations and transitions
- **Custom UI Primitives**: Reusable components (Button, Card, Badge, Skeleton, TokenAvatar)
- **Theme Provider**: Dark mode with system preference support
- **Supabase Ready**: Placeholder provider for future authentication integration

## Tech Stack

- **Framework**: Next.js 14
- **Language**: TypeScript
- **Styling**: Tailwind CSS v3 + @tailwindcss/typography
- **Animations**: Framer Motion
- **Linting**: ESLint + Prettier
- **Package Manager**: pnpm

## Getting Started

### Prerequisites

- Node.js 18+ (recommended 20+)
- pnpm 8+ (`npm install -g pnpm`)

### Installation

```bash
# From the project root
pnpm install
```

### Development

```bash
# Start the development server
pnpm dev

# Or from the web directory
cd apps/web
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

```bash
# Production build
pnpm build

# Start production server
pnpm start
```

## Project Structure

```
apps/web/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx         # Root layout with providers
│   ├── page.tsx           # Homepage
│   ├── providers.tsx      # Provider re-export
│   └── globals.css        # Global styles
├── components/
│   ├── layout/            # Layout components
│   │   └── sticky-header.tsx
│   ├── providers/         # Context providers
│   │   ├── theme-provider.tsx
│   │   ├── supabase-provider.tsx
│   │   └── index.tsx
│   └── ui/                # UI primitives
│       ├── button.tsx
│       ├── card.tsx
│       ├── badge.tsx
│       ├── skeleton.tsx
│       ├── token-avatar.tsx
│       └── index.ts
├── lib/                   # Utilities
│   ├── fonts.ts          # Font configuration
│   └── utils.ts          # Utility functions
├── styles/                # Style utilities
├── public/                # Static assets
├── next.config.js         # Next.js configuration
├── tailwind.config.ts     # Tailwind configuration
├── tsconfig.json          # TypeScript configuration
└── package.json           # Dependencies and scripts
```

## Design Tokens

### Color Palette

The app uses a custom dark color palette:

- **Dark**: Base background colors (950-50)
- **Primary**: Blue accent (950-50)
- **Secondary**: Green accent (950-50)
- **Accent**: Purple highlights (950-50)
- **Status**: Success, Warning, Error, Info

### Typography

- **Sans**: Inter (default, 300-700)
- **Mono**: JetBrains Mono (code, 400-700)

### Spacing & Sizing

- Custom spacing: 18, 88, 128
- Border radius: 4xl (2rem)
- Custom shadows: glow-sm, glow-md, glow-lg

### Animations

- `fade-in`: 0.5s ease-in-out
- `slide-up`: 0.4s ease-out
- `slide-down`: 0.4s ease-out
- `pulse-slow`: 3s infinite

## Scripts

```bash
# Development
pnpm dev              # Start dev server
pnpm build            # Build for production
pnpm start            # Start production server

# Code Quality
pnpm lint             # Run ESLint
pnpm format           # Format with Prettier
pnpm format:check     # Check formatting
pnpm type-check       # TypeScript type checking
```

## Environment Variables

Copy `.env.example` to `.env.local` and configure:

```env
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

## UI Components

### Button

```tsx
import { Button } from '@/components/ui';

<Button variant="primary" size="md">Click me</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
```

### Card

```tsx
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui';

<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>Content here</CardContent>
</Card>;
```

### Badge

```tsx
import { Badge } from '@/components/ui';

<Badge variant="success">+12.5%</Badge>
<Badge variant="warning">Warning</Badge>
<Badge variant="destructive">Error</Badge>
```

### Token Avatar

```tsx
import { TokenAvatar } from '@/components/ui';

<TokenAvatar name="Bitcoin" symbol="BTC" size="md" />;
```

### Skeleton

```tsx
import { Skeleton } from '@/components/ui';

<Skeleton className="h-10 w-full" />;
```

## Theme

The app uses a dark theme by default. The ThemeProvider supports:

- `dark`: Dark mode (default)
- `light`: Light mode
- `system`: Follow system preference

```tsx
import { useTheme } from '@/components/providers/theme-provider';

const { theme, setTheme, resolvedTheme } = useTheme();
```

## Absolute Imports

Configured in `tsconfig.json`:

```typescript
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
```

## Styling Guidelines

- Use Tailwind utility classes for styling
- Prefer `hsl(var(--token))` for theme colors
- Use `cn()` from `@/lib/utils` for conditional classes
- Add custom utilities to `globals.css` under `@layer components`

## Performance

- Server Components by default (add `'use client'` only when needed)
- Optimized font loading with `next/font`
- Image optimization with `next/image`
- SWC minification enabled

## Future Enhancements

- [ ] Storybook integration for component documentation
- [ ] Supabase authentication
- [ ] API route handlers for backend integration
- [ ] Responsive mobile navigation
- [ ] Token detail pages
- [ ] Analytics dashboard
- [ ] Real-time data subscriptions

## Contributing

1. Create a feature branch
2. Make your changes
3. Run `pnpm format` and `pnpm lint`
4. Submit a pull request

## License

Proprietary - Internal project

## Support

For issues or questions, contact the development team.
