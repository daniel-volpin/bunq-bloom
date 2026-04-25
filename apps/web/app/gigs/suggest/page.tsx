import Link from "next/link";
import { ChevronLeft, MessageSquarePlus, Sparkles } from "lucide-react";

export default function GigSuggestPage() {
  return (
    <div className="px-5 pt-6 pb-8">
      <header className="flex items-center gap-2 pb-3">
        <Link
          href="/gigs"
          aria-label="Back to gigs"
          className="tap-target grid h-10 w-10 place-items-center rounded-full bg-card shadow-card"
        >
          <ChevronLeft className="h-5 w-5 text-foreground" />
        </Link>
        <div>
          <p className="text-sm font-bold text-muted-foreground">Kid idea</p>
          <h1 className="text-2xl font-extrabold text-foreground">Suggest a gig</h1>
        </div>
      </header>

      <section className="rounded-3xl bg-card p-5 shadow-card">
        <span className="grid h-14 w-14 place-items-center rounded-full bg-petal-blue text-bloom-green-deep">
          <MessageSquarePlus className="h-7 w-7" />
        </span>
        <h2 className="mt-4 text-xl font-extrabold text-foreground">This screen is ready for the next backend step</h2>
        <p className="mt-3 text-sm leading-6 text-muted-foreground">
          The attached frontend includes gig suggestions, but the current MVP backend does not expose a suggestion API yet. For now, use the parent post-gig flow so the earning loop stays real and demo-safe.
        </p>
        <div className="mt-4 rounded-2xl bg-bloom-green/10 p-4 text-sm font-semibold text-bloom-green-deep">
          Once a suggestion endpoint exists, this page can be upgraded without redoing the rest of the frontend.
        </div>
      </section>

      <div className="mt-5 grid grid-cols-2 gap-2">
        <Link
          href="/gigs"
          className="tap-target flex items-center justify-center rounded-full bg-card px-4 py-3 text-sm font-extrabold text-bloom-green-deep shadow-card"
        >
          Back to gigs
        </Link>
        <Link
          href="/gigs/new"
          className="tap-target flex items-center justify-center gap-2 rounded-full bg-bloom-green px-4 py-3 text-sm font-extrabold text-white shadow-card"
        >
          <Sparkles className="h-4 w-4" />
          Post a gig
        </Link>
      </div>
    </div>
  );
}