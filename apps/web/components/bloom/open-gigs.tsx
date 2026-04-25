import Image from "next/image";
import { GigRow } from "@/components/bloom/gig-row";
import type { Gig } from "@/lib/types";

export function OpenGigs({ gigs }: { gigs: Gig[] }) {
  return (
    <section className="px-5 pt-6">
      <div className="mb-3 flex items-center gap-2 px-1">
        <Image src="/bloom/tulip-emblem.svg" alt="" width={20} height={20} className="h-5 w-5" />
        <h3 className="text-base font-extrabold text-foreground">Open gigs</h3>
      </div>
      <div className="space-y-3">
        {gigs.map((gig) => (
          <GigRow key={gig.id} gig={gig} />
        ))}
      </div>
    </section>
  );
}