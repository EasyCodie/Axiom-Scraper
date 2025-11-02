import { createServerClient } from '@/lib/supabase/server';
import { redirect } from 'next/navigation';

export default async function ComparePage() {
  const supabase = createServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect('/?auth=required&redirect=/compare');
  }

  return (
    <section className="mx-auto w-full max-w-5xl px-4 py-24 md:px-6">
      <h1 className="text-3xl font-semibold text-white">Token comparison</h1>
      <p className="mt-4 text-sm text-[hsl(var(--muted-foreground))]">
        Compare multiple tokens side-by-side across key metrics: price, volume, social engagement,
        and wallet activity.
      </p>
      <div className="mt-10 rounded-2xl border border-white/5 bg-white/5 p-6 text-sm text-[hsl(var(--muted-foreground))]">
        Authentication is required to use the comparison tool.
      </div>
    </section>
  );
}
