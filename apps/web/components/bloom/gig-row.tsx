import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { GigIcon, accentBg } from "@/components/bloom/gig-icon";
import {
  estimateGigDuration,
  formatEuro,
  gigAccent,
  gigIcon
} from "@/lib/gig-presentation";
import type { Gig } from "@/lib/types";

export function GigRow({ gig }: { gig: Gig }) {
  const accent = gigAccent(gig);

  return (
    <div className="flex items-center gap-3 rounded-3xl bg-card px-3 py-3 shadow-card">
      <div className={`grid h-14 w-14 shrink-0 place-items-center rounded-full ${accentBg[accent]}`}>
        <GigIcon kind={gigIcon(gig)} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-[15px] font-extrabold text-foreground">{gig.title}</p>
        <p className="text-xs font-semibold text-muted-foreground">
          {estimateGigDuration(gig)} mins <span className="text-bloom-green">•</span>{" "}
          <span className="text-bloom-green">{formatEuro(gig.reward_amount)}</span>
        </p>
      </div>
      <Link
        href={`/gigs/${gig.id}`}
        className="tap-target inline-flex items-center gap-0.5 rounded-full bg-bloom-green pl-4 pr-3 text-xs font-bold text-primary-foreground shadow-card transition-transform active:scale-95"
      >
        View gig
        <ChevronRight className="h-4 w-4" />
      </Link>
    </div>
  );
}