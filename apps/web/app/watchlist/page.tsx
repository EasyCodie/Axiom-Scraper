import { createServerClient } from '@/lib/supabase/server';
import { redirect } from 'next/navigation';

export default async function WatchlistPage() {
  const supabase = createServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect('/?auth=required&redirect=/watchlist');
  }

  return (
    <section className="mx-auto w-full max-w-5xl px-4 py-24 md:px-6">
      <h1 className="text-3xl font-semibold text-white">Your watchlist</h1>
      <p className="mt-4 text-sm text-[hsl(var(--muted-foreground))]">
        Save the tokens you want to monitor and get notified when liquidity or social signals shift.
      </p>
      <div className="mt-10 rounded-2xl border border-white/5 bg-white/5 p-6 text-sm text-[hsl(var(--muted-foreground))]">
        Authentication is required to view your personalized watchlist.
      </div>
    </section>
  );
}
