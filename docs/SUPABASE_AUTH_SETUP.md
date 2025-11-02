# Supabase Authentication Setup

This guide explains how to configure Supabase authentication for the Axiom web application.

## Prerequisites

- A Supabase account ([supabase.com](https://supabase.com))
- Node.js 18+ and pnpm installed
- Access to your Supabase project settings

## 1. Create a Supabase Project

1. Log in to [Supabase Dashboard](https://app.supabase.com)
2. Click **New Project**
3. Fill in project details:
   - Project name: `axiom-production` (or your preference)
   - Database password: Generate a strong password
   - Region: Choose closest to your users
4. Wait for project creation (1-2 minutes)

## 2. Configure Authentication Providers

### Email Magic Link (Default Enabled)

Magic links are enabled by default in Supabase.

1. Go to **Authentication** > **Providers** > **Email**
2. Ensure **Enable Email Provider** is checked
3. Configure email settings:
   - **Enable Email Confirmations**: Recommended for production
   - **Secure Email Change**: Enabled
   - **Mailer**: Use Supabase's default or configure a custom SMTP

### Google OAuth

1. Go to **Authentication** > **Providers** > **Google**
2. Enable Google provider
3. Get OAuth credentials from [Google Cloud Console](https://console.cloud.google.com/):
   - Create a new project or select existing
   - Navigate to **APIs & Services** > **Credentials**
   - Click **Create Credentials** > **OAuth 2.0 Client IDs**
   - Application type: **Web application**
   - Authorized redirect URIs: Add your Supabase callback URL (shown in Supabase dashboard)
4. Copy **Client ID** and **Client Secret** to Supabase

### Telegram OAuth

1. Go to **Authentication** > **Providers** > **Telegram**
2. Enable Telegram provider
3. Open Telegram and start a conversation with [@BotFather](https://t.me/BotFather)
4. Create a new bot:
   - Use `/newbot`
   - Follow prompts to name the bot and get a **Bot Token**
5. Set up Telegram login widget with BotFather:
   - Send `/setdomain` and provide your domain (e.g., `your-domain.com`)
   - (Optional) Send `/setjoingroups` to disable group chats
6. In Supabase dashboard, paste the **Bot Token**
7. Configure `Redirect URLs`: include the Supabase callback URL and your local development URL (e.g., `http://localhost:3000/auth/callback`)

## 3. Configure Redirect URLs

1. Go to **Authentication** > **URL Configuration**
2. Add your application URLs:
   - **Site URL**: `https://your-domain.com` (production) or `http://localhost:3000` (development)
   - **Redirect URLs**: Add all URLs where users can be redirected after authentication:
     ```
     http://localhost:3000/auth/callback
     https://your-domain.com/auth/callback
     ```

## 4. Get API Keys

1. Go to **Settings** > **API**
2. Copy the following values:
   - **Project URL**: `https://your-project.supabase.co`
   - **anon public**: Your anonymous/public API key

## 5. Configure Environment Variables

Create `.env.local` in `apps/web/`:

```bash
# App configuration
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Supabase authentication
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-public-key-here
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-public-key-here

# FastAPI backend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Never commit `.env.local` to version control!**

## 6. Update Next.js Configuration

The `next.config.js` is already configured to expose Supabase environment variables.

## 7. Test Authentication Locally

1. Start the FastAPI backend:
   ```bash
   cd /home/engine/project
   python -m services.api
   ```

2. Start the Next.js development server:
   ```bash
   cd /home/engine/project/apps/web
   pnpm dev
   ```

3. Visit `http://localhost:3000`
4. Click **Log in** or **Request access**
5. Test authentication flows:
   - Email magic link
   - Google OAuth
   - GitHub OAuth

## 8. User Profile Bootstrap

On first login, the application automatically calls the FastAPI `/user/favorites` endpoint to bootstrap the user profile in DuckDB. This happens in the `/auth/callback` route handler.

The backend's `ensure_user_profile` dependency automatically creates a user profile record if it doesn't exist.

## 9. Protected Routes

The following routes are protected by authentication middleware:

- `/watchlist` - User's favorite tokens
- `/compare` - Token comparison tool
- `/alerts` - Price alert management

Users will be redirected to the login modal when accessing these routes without authentication.

## 10. Session Management

- Sessions are managed via HTTP-only cookies set by Supabase
- Session refresh is handled automatically by `@supabase/auth-helpers-nextjs`
- Sessions persist across browser restarts (until expiration)
- Default session expiration: 7 days (configurable in Supabase dashboard)

## Troubleshooting

### "Invalid redirect URL" error

- Ensure your redirect URLs are added in Supabase dashboard (**Authentication** > **URL Configuration**)
- Check that `NEXT_PUBLIC_APP_URL` matches your actual application URL

### OAuth provider not working

- Verify OAuth credentials are correctly entered in Supabase
- Check that redirect URIs in OAuth provider dashboard match Supabase callback URL
- Ensure provider is enabled in Supabase dashboard

### Email magic links not sending

- Check Supabase email provider settings
- For development, check Supabase dashboard **Authentication** > **Logs** for email deliverability
- Consider setting up a custom SMTP provider for production

### User profile not created in backend

- Ensure FastAPI backend is running
- Check `NEXT_PUBLIC_API_URL` environment variable is correct
- Review backend logs for errors
- Verify DuckDB database has user tables initialized

## Production Considerations

1. **Email Provider**: Configure a custom SMTP provider (SendGrid, Postmark, etc.) for production
2. **Rate Limiting**: Supabase has built-in rate limiting; monitor usage in dashboard
3. **Security**: 
   - Enable email confirmations
   - Configure appropriate session timeouts
   - Review Supabase security settings
4. **Monitoring**: Set up alerts for auth failures in Supabase dashboard
5. **Backup**: Regularly backup user data from DuckDB

## References

- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [Next.js Auth Helpers](https://supabase.com/docs/guides/auth/auth-helpers/nextjs)
- [OAuth Provider Setup](https://supabase.com/docs/guides/auth/social-login)
