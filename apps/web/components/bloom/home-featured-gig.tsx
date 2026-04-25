import { GigListCard } from "@/components/bloom/gig-list-card";
import { formatEuro } from "@/lib/gig-presentation";
import type { Gig } from "@/lib/types";

export function HomeFeaturedGig({ gig }: { gig: Gig }) {
  return (
    <section className="px-5 pt-4">
      <div className="mb-3 px-1">
        <p className="text-[11px] font-black uppercase tracking-[0.18em] text-bloom-green-deep/70">
          Best next gig
        </p>
        <h3 className="mt-1 text-lg font-extrabold text-foreground">Earn the most right now</h3>
        <p className="mt-1 text-sm font-semibold text-muted-foreground">
          {gig.title} pays {formatEuro(gig.reward_amount)} and moves your goal faster.
        </p>
      </div>
      <GigListCard gig={gig} />
    </section>
  );
}
