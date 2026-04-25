"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { MessageSquarePlus, RefreshCcw, Trophy } from "lucide-react";
import { GigListCard } from "@/components/bloom/gig-list-card";
import { Header } from "@/components/bloom/header";
import { gigBucket } from "@/lib/gig-presentation";
import { useBloomSummary } from "@/lib/use-bloom-summary";

type Filter = "available" | "in-progress" | "done";

const filters: { id: Filter; label: string }[] = [
  { id: "available", label: "Available" },
  { id: "in-progress", label: "In progress" },
  { id: "done", label: "Done" }
];

export default function GigsPage() {
  const { loading, error, gigs, reload } = useBloomSummary();
  const [filter, setFilter] = useState<Filter>("available");

  const visible = useMemo(
    () => gigs.filter((gig) => gigBucket(gig.status) === filter),
    [filter, gigs]
  );

  const openCount = gigs.filter((gig) => gig.status === "open").length;

  return (
    <div className="pb-8">
      <Header actionHref="/parent/gigs/new" actionLabel="Post gig" />

      <div className="px-5 pt-2">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-extrabold text-foreground">Gigs</h1>
            <p className="text-xs font-semibold text-muted-foreground">
              {openCount} open · earn money the Bloom way
            </p>
          </div>
          <button
            type="button"
            onClick={reload}
            className="tap-target inline-flex items-center gap-2 rounded-full bg-card px-4 py-2 text-sm font-extrabold text-bloom-green-deep shadow-card"
          >
            <RefreshCcw className="h-4 w-4" />
            Refresh
          </button>
        </div>

        <div className="mt-4 flex gap-2 overflow-x-auto pb-1">
          {filters.map((item) => {
            const active = item.id === filter;

            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setFilter(item.id)}
                className={`tap-target inline-flex shrink-0 items-center rounded-full px-4 text-sm font-bold transition-colors ${
                  active
                    ? "bg-bloom-green text-white shadow-card"
                    : "bg-card text-muted-foreground"
                }`}
              >
                {item.label}
              </button>
            );
          })}
        </div>

        {loading ? (
          <div className="mt-5 rounded-3xl bg-card p-5 text-sm font-bold text-slate-600 shadow-card">
            Loading gigs...
          </div>
        ) : null}

        {error ? (
          <div className="mt-5 rounded-3xl border border-bloom-coral/20 bg-bloom-coral/10 p-5 text-sm leading-6 text-slate-700 shadow-card">
            {error}
          </div>
        ) : null}

        <div className="mt-5 space-y-3">
          {!loading && visible.length === 0 ? (
            <div className="flex flex-col items-center gap-2 rounded-3xl bg-card p-8 text-center shadow-card">
              <Trophy className="h-8 w-8 text-bloom-green" />
              <p className="text-sm font-extrabold text-foreground">Nothing here yet</p>
              <p className="text-xs font-semibold text-muted-foreground">
                {filter === "available"
                  ? "Post a new gig to kick off the next earning loop."
                  : filter === "in-progress"
                    ? "Claim a gig or finish the photo flow to see progress here."
                    : "Paid gigs will show up here once the loop completes."}
              </p>
            </div>
          ) : null}

          {visible.map((gig) => (
            <GigListCard key={gig.id} gig={gig} />
          ))}
        </div>

        <Link
          href="/gigs/suggest"
          className="tap-target mt-5 flex w-full items-center justify-center gap-2 rounded-full border-2 border-dashed border-bloom-green/50 bg-transparent px-4 py-4 text-sm font-extrabold text-bloom-green-deep transition-colors active:bg-bloom-green/5"
        >
          <MessageSquarePlus className="h-5 w-5" />
          Suggest a gig to Mom or Dad
        </Link>
      </div>
    </div>
  );
}
