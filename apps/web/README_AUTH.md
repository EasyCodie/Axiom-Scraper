# Authentication Integration

This document describes the Supabase authentication integration in the Axiom web application.

## Overview

The application uses Supabase Auth with Next.js App Router, supporting:

- Email magic links (passwordless authentication)
- Google OAuth
- GitHub OAuth
- Session management with HTTP-only cookies
- Protected routes with middleware
- User profile bootstrap with FastAPI backend

## Architecture

### Client-Side Components

#### 1. Supabase Provider (`components/providers/supabase-provider.tsx`)

Context provider that:

- Initializes Supabase client
- Manages authentication state
- Provides session and user data to components
- Listens for auth state changes

Usage:

```tsx
import { useSupabase } from '@/components/providers';

function MyComponent() {
  const { user, session, client, isLoading } = useSupabase();
  // ...
}
```

#### 2. Login Modal (`components/auth/login-modal.tsx`)

Modal component with:

- Email input for magic link
- OAuth provider buttons (Google, GitHub)
- Loading states and error handling
- Success feedback via toast notifications

#### 3. Header with Auth State (`components/layout/sticky-header.tsx`)

Header component that:

- Shows login/access buttons when not authenticated
- Displays user avatar and email when authenticated
- Provides sign-out functionality
- Opens login modal on auth requirement

### Server-Side Components

#### 1. Server Client (`lib/supabase/server.ts`)

Creates Supabase client for Server Components:

```tsx
import { createServerClient } from '@/lib/supabase/server';

export default async function Page() {
  const supabase = createServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  // ...
}
```

#### 2. Middleware (`lib/supabase/middleware.ts`)

Updates session in middleware for cookie management.

#### 3. Auth Callback Route (`app/auth/callback/route.ts`)

Route handler that:

- Exchanges OAuth code for session
- Bootstraps user profile in backend
- Redirects to intended destination

### Middleware Protection (`middleware.ts`)

Protects routes:

- `/watchlist`
- `/compare`
- `/alerts`

Redirects unauthenticated users to home with query params:

- `?redirect=/watchlist` - intended destination
- `&auth=required` - triggers login modal

## Authentication Flows

### Magic Link Flow

1. User enters email in login modal
2. Client calls `supabase.auth.signInWithOtp()`
3. Supabase sends email with magic link
4. User clicks link → redirected to `/auth/callback?code=...`
5. Callback handler exchanges code for session
6. Backend profile bootstrap called
7. User redirected to intended page

### OAuth Flow (Google/GitHub)

1. User clicks OAuth provider button
2. Client calls `supabase.auth.signInWithOAuth()`
3. User redirected to provider login
4. Provider redirects back to `/auth/callback?code=...`
5. Callback handler exchanges code for session
6. Backend profile bootstrap called
7. User redirected to intended page

### Sign Out Flow

1. User clicks "Sign out" button
2. Client calls `supabase.auth.signOut()`
3. Session cleared from cookies
4. User redirected to home page
5. Toast notification confirms sign out

## Backend Integration

### Profile Bootstrap

On first login, the callback handler calls:

```
GET /user/favorites
Authorization: Bearer <access_token>
```

The FastAPI backend:

1. Validates JWT token
2. Extracts user ID from token
3. Creates user profile in DuckDB (via `ensure_user_profile` dependency)
4. Returns user data

### Protected API Calls

All subsequent API calls include the access token:

```tsx
const {
  data: { session },
} = await supabase.auth.getSession();

fetch('/api/endpoint', {
  headers: {
    Authorization: `Bearer ${session.access_token}`,
  },
});
```

## Session Management

### Session Storage

- Sessions stored in HTTP-only cookies (secure)
- Managed automatically by `@supabase/auth-helpers-nextjs`
- No local storage or session storage used

### Session Refresh

- Automatic refresh handled by Supabase client
- Refresh tokens stored securely in cookies
- Default expiration: 7 days (configurable in Supabase)

### Session Validation

- Middleware validates session on each request
- Invalid/expired sessions trigger re-authentication
- Protected routes redirect to login

## Environment Variables

Required environment variables (`.env.local`):

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# App
NEXT_PUBLIC_APP_URL=http://localhost:3000

# API
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Testing

### Manual Testing

1. Start backend: `python -m services.api`
2. Start frontend: `pnpm dev`
3. Navigate to protected route: http://localhost:3000/watchlist
4. Verify login modal opens
5. Test auth flows:
   - Email magic link
   - Google OAuth
   - GitHub OAuth
6. Verify redirection after login
7. Test sign out

### Playwright Tests

Run integration tests:

```bash
pytest tests/integration/test_auth_flow.py -v
```

Tests cover:

- Login modal opening on protected routes
- OAuth provider buttons rendering
- Email validation
- Modal close functionality
- Header state changes

## Toast Notifications

Toast notifications provide user feedback:

- **Success**: "Check your email" (magic link sent)
- **Success**: "Signed out"
- **Error**: Authentication failures
- **Info**: "Authentication required" (protected route)

Powered by `sonner` library with custom styling.

## Security Considerations

1. **JWT Validation**: Backend validates all JWTs via JWKS
2. **HTTP-Only Cookies**: Session tokens not accessible to JavaScript
3. **CSRF Protection**: Built into Supabase auth flow
4. **Rate Limiting**: Supabase provides built-in rate limiting
5. **Secure Redirect**: Middleware validates redirect URLs

## Troubleshooting

### Login modal doesn't open

- Check Supabase environment variables
- Verify middleware is configured correctly
- Check browser console for errors

### OAuth redirect fails

- Verify redirect URLs in Supabase dashboard
- Check OAuth provider credentials
- Ensure `NEXT_PUBLIC_APP_URL` is correct

### Session not persisting

- Check cookie settings in browser
- Verify Supabase project is active
- Clear browser cookies and retry

### Backend profile not created

- Check FastAPI is running
- Verify `NEXT_PUBLIC_API_URL` is correct
- Review backend logs for errors
- Ensure DuckDB is initialized with user tables

## Future Enhancements

- [ ] Passwordless SMS authentication
- [ ] Multi-factor authentication (MFA)
- [ ] Social login with Telegram
- [ ] User profile settings page
- [ ] Email change flow
- [ ] Account deletion
- [ ] Session management dashboard
- [ ] Webhook handlers for auth events
