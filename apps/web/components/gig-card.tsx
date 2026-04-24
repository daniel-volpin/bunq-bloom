import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";
import type { Gig } from "@/lib/types";

function nextAction(status: Gig["status"]) {
  switch (status) {
    case "open":
      return "Claim this gig";
    case "claimed":
      return "Take before photo";
    case "awaiting_after_photo":
      return "Take after photo";
    case "rejected":
      return "Try again";
    case "payment_failed":
      return "Retry payment";
    case "paid":
      return "View result";
    default:
      return "Open gig";
  }
}

export function GigCard({ gig }: { gig: Gig }) {
  return (
    <Link
      href={`/gigs/${gig.id}`}
      className="block rounded-[1.75rem] border border-white/70 bg-white/90 p-5 shadow-bloom transition hover:-translate-y-0.5"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="mb-2 inline-flex items-center gap-1 rounded-full bg-bloom-sun/35 px-3 py-1 text-xs font-bold uppercase tracking-wide text-amber-800">
            <Sparkles size={14} />
            {gig.status.replaceAll("_", " ")}
          </p>
          <h2 className="text-xl font-black leading-tight text-bloom-ink">{gig.title}</h2>
          <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-600">
            {gig.description}
          </p>
        </div>
        <div className="rounded-2xl bg-bloom-leaf px-3 py-2 text-right font-black text-white">
          {gig.reward_amount}
          <span className="block text-[10px]">{gig.currency}</span>
        </div>
      </div>
      <div className="mt-5 flex items-center justify-between text-sm font-bold text-bloom-sky">
        <span>{nextAction(gig.status)}</span>
        <ArrowRight size={18} />
      </div>
    </Link>
  );
}
