import { createServerClient } from '@/lib/supabase/server';
import { NextResponse, type NextRequest } from 'next/server';

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get('code');
  const redirectTo = requestUrl.searchParams.get('redirect') || '/';

  const supabase = createServerClient();

  if (code) {
    await supabase.auth.exchangeCodeForSession(code);

    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (session) {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        await fetch(`${apiUrl}/user/favorites`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        }).catch(() => {});
      }
    } catch (error) {
      console.error('Profile bootstrap error:', error);
    }
  }

  return NextResponse.redirect(new URL(redirectTo, requestUrl.origin));
}
