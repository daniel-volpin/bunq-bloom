"use client";

import Link from "next/link";
import { ArrowRight, RefreshCcw, Sparkles } from "lucide-react";
import { Header } from "@/components/bloom/header";
import { HeroCard } from "@/components/bloom/hero-card";
import { OpenGigs } from "@/components/bloom/open-gigs";
import { useBloomSummary } from "@/lib/use-bloom-summary";

function LoadingState() {
  return (
    <div className="space-y-4 px-5 pt-4">
      <div className="h-48 animate-pulse rounded-3xl bg-white/70" />
      <div className="h-28 animate-pulse rounded-3xl bg-white/70" />
      <div className="h-20 animate-pulse rounded-3xl bg-white/70" />
    </div>
  );
}

export default function HomePage() {
  const {
    loading,
    error,
    balanceLoading,
    reportLoading,
    balanceResponse,
    report,
    openGigs,
    fallbackMode,
    modes,
    reload
  } =
    useBloomSummary();

  if (loading && openGigs.length === 0) {
    return (
      <div className="pb-8">
        <Header />
        <LoadingState />
      </div>
    );
  }

  return (
    <div className="pb-8">
      <Header />

      <HeroCard
        balanceAmount={balanceResponse?.balance.amount ?? "0.00"}
        balanceAmountLoading={balanceLoading && !balanceResponse}
        earnedThisWeek={report?.stats.money_earned.amount}
        earnedThisWeekLoading={reportLoading && !report}
      />

      {fallbackMode ? (
        <section className="px-5 pt-4">
          <div className="rounded-3xl bg-bloom-sky/10 p-4 text-sm leading-6 text-slate-700 shadow-card">
            Bloom is running with demo fallback enabled right now.
            {modes.length > 0 ? ` Modes: ${modes.join(", ")}.` : ""}
          </div>
        </section>
      ) : null}

      {error ? (
        <section className="px-5 pt-4">
          <div className="rounded-3xl border border-bloom-coral/20 bg-bloom-coral/10 p-4 text-sm text-slate-700 shadow-card">
            <p className="font-extrabold text-foreground">Some data could not load.</p>
            <p className="mt-1 leading-6">{error}</p>
            <button
              type="button"
              onClick={reload}
              className="tap-target mt-3 inline-flex items-center gap-2 rounded-full bg-card px-4 py-2 font-extrabold text-bloom-green-deep shadow-card"
            >
              <RefreshCcw className="h-4 w-4" />
              Refresh
            </button>
          </div>
        </section>
      ) : null}

      {openGigs.length > 0 ? (
        <OpenGigs gigs={openGigs.slice(0, 3)} />
      ) : (
        <section className="px-5 pt-6">
          <div className="rounded-3xl bg-card p-6 text-center shadow-card">
            <Sparkles className="mx-auto h-8 w-8 text-bloom-green" />
            <p className="mt-3 text-base font-extrabold text-foreground">No open gigs yet</p>
            <p className="mt-1 text-sm font-semibold text-muted-foreground">
              Post a new gig and Bloom will turn it into the next earning moment.
            </p>
            <Link
              href="/gigs/new"
              className="tap-target mt-4 inline-flex items-center gap-2 rounded-full bg-bloom-green px-5 py-3 font-extrabold text-white"
            >
              Create a gig
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>
      )}

      {report ? (
        <section className="px-5 pt-6">
          <div className="rounded-3xl bg-card p-5 shadow-card">
            <p className="text-xs font-black uppercase tracking-[0.2em] text-bloom-green-deep/70">
              Family highlight
            </p>
            <h2 className="mt-2 text-xl font-extrabold text-foreground">
              {report.highlights[0]?.title ?? "This week with Bloom"}
            </h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              {report.highlights[0]?.detail ?? report.savings_insight}
            </p>
            <p className="mt-4 rounded-2xl bg-bloom-green/10 p-3 text-sm font-semibold text-bloom-green-deep">
              {report.conversation_starter}
            </p>
          </div>
        </section>
      ) : reportLoading ? (
        <section className="px-5 pt-6">
          <div className="rounded-3xl bg-card p-5 shadow-card">
            <div className="h-3 w-28 animate-pulse rounded-full bg-slate-100" />
            <div className="mt-3 h-6 w-40 animate-pulse rounded-full bg-slate-100" />
            <div className="mt-3 h-4 w-full animate-pulse rounded-full bg-slate-100" />
            <div className="mt-2 h-4 w-5/6 animate-pulse rounded-full bg-slate-100" />
            <div className="mt-4 h-12 animate-pulse rounded-2xl bg-bloom-green/10" />
          </div>
        </section>
      ) : null}
    </div>
  );
}
