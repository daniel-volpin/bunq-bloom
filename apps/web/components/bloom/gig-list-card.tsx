import Link from "next/link";
import { CheckCircle2, ChevronRight, Clock } from "lucide-react";
import { GigIcon, accentBg } from "@/components/bloom/gig-icon";
import { RewardChip } from "@/components/bloom/reward-chip";
import {
  estimateGigDuration,
  gigAccent,
  gigIcon,
  nextGigActionLabel
} from "@/lib/gig-presentation";
import type { Gig } from "@/lib/types";

function ctaClassName(status: Gig["status"]): string {
  switch (status) {
    case "open":
      return "bg-bloom-green text-primary-foreground";
    case "paid":
      return "bg-bloom-green/10 text-bloom-green-deep";
    case "payment_failed":
    case "rejected":
      return "bg-bloom-coral/15 text-bloom-coral";
    default:
      return "bg-bloom-blue text-primary-foreground";
  }
}

export function GigListCard({ gig }: { gig: Gig }) {
  const accent = gigAccent(gig);
  const ctaLabel = nextGigActionLabel(gig.status);

  return (
    <Link
      href={`/gigs/${gig.id}`}
      aria-label={`Open gig: ${gig.title}`}
      className="block rounded-3xl bg-card p-3 text-left shadow-card transition-transform active:scale-[0.99]"
    >
      <div className="flex items-start gap-3">
        <div className={`grid h-14 w-14 shrink-0 place-items-center rounded-2xl ${accentBg[accent]}`}>
          <GigIcon kind={gigIcon(gig)} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <p className="truncate text-[15px] font-extrabold text-foreground">{gig.title}</p>
            <RewardChip amount={gig.reward_amount} size="sm" />
          </div>
          {gig.description ? (
            <p className="mt-0.5 line-clamp-1 text-xs font-semibold text-muted-foreground">
              {gig.description}
            </p>
          ) : null}
          <div className="mt-2 flex items-center justify-between gap-2">
            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-muted-foreground">
              <Clock className="h-3 w-3" />
              {estimateGigDuration(gig)} mins
            </span>
            <span
              className={`inline-flex h-8 items-center gap-1 rounded-full px-3 text-xs font-extrabold ${ctaClassName(gig.status)}`}
            >
              {gig.status === "paid" ? <CheckCircle2 className="h-4 w-4" /> : null}
              {ctaLabel}
              {gig.status !== "paid" ? <ChevronRight className="h-4 w-4" /> : null}
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}