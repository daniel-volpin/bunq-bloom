import Link from "next/link";
import { GigIcon, accentBg } from "@/components/bloom/gig-icon";
import { formatEuro, gigAccent, gigIcon } from "@/lib/gig-presentation";
import type { Gig } from "@/lib/types";

function formatRelative(isoDate?: string): string {
  if (!isoDate) {
    return "recently";
  }

  const timestamp = Date.parse(isoDate);
  if (Number.isNaN(timestamp)) {
    return "recently";
  }

  const diff = Date.now() - timestamp;
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) {
    return "just now";
  }
  if (minutes < 60) {
    return `${minutes}m ago`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours}h ago`;
  }
  const days = Math.floor(hours / 24);
  if (days < 7) {
    return `${days}d ago`;
  }

  return new Date(timestamp).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric"
  });
}

export function EarningRow({ gig }: { gig: Gig }) {
  const accent = gigAccent(gig);

  return (
    <Link
      href={`/gigs/${gig.id}`}
      className="flex w-full items-center gap-3 rounded-2xl bg-card p-3 text-left shadow-card transition-transform active:scale-[0.99]"
    >
      <div className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl ${accentBg[accent]}`}>
        <GigIcon kind={gigIcon(gig)} className="h-5 w-5" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-extrabold text-foreground">{gig.title}</p>
        <p className="text-[11px] font-semibold text-muted-foreground">
          {formatRelative(gig.updated_at)}
        </p>
      </div>
      <p className="shrink-0 text-sm font-extrabold text-bloom-green-deep">
        +{formatEuro(gig.reward_amount)}
      </p>
    </Link>
  );
}