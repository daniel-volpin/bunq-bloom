"use client";

import Link from "next/link";
import { ArrowRight, RefreshCcw, Sparkles } from "lucide-react";
import { HomeFeaturedGig } from "@/components/bloom/home-featured-gig";
import { Header } from "@/components/bloom/header";
import { HomeGoalStrip } from "@/components/bloom/home-goal-strip";
import { HeroCard } from "@/components/bloom/hero-card";
import { OpenGigs } from "@/components/bloom/open-gigs";
import { useBloomSummary } from "@/lib/use-bloom-summary";
import { useSavedGoal } from "@/lib/use-saved-goal";

function LoadingState() {
  return (
    <div className="space-y-3 px-5 pt-3">
      <div className="h-48 animate-pulse rounded-3xl bg-white/70" />
      <div className="h-28 animate-pulse rounded-3xl bg-white/70" />
      <div className="h-20 animate-pulse rounded-3xl bg-white/70" />
    </div>
  );
}

export default function HomePage() {
  const { savedGoal } = useSavedGoal();
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
  const featuredGig = [...openGigs].sort(
    (left, right) => Number(right.reward_amount) - Number(left.reward_amount)
  )[0] ?? null;
  const moreOpenGigs = featuredGig ? openGigs.filter((gig) => gig.id !== featuredGig.id).slice(0, 3) : [];

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

      {savedGoal && balanceResponse ? (
        <section className="px-5 pt-4">
          <div className="overflow-hidden rounded-3xl shadow-card">
            <HeroCard
              balanceAmount={balanceResponse.balance.amount}
              balanceAmountLoading={balanceLoading && !balanceResponse}
              connected
            />
            <HomeGoalStrip goal={savedGoal} balanceAmount={balanceResponse.balance.amount} connected />
          </div>
        </section>
      ) : (
        <HeroCard
          balanceAmount={balanceResponse?.balance.amount ?? "0.00"}
          balanceAmountLoading={balanceLoading && !balanceResponse}
        />
      )}

      {fallbackMode ? (
        <section className="px-5 pt-3">
          <div className="rounded-3xl bg-bloom-sky/10 p-4 text-sm leading-6 text-slate-700 shadow-card">
            Bloom is running with demo fallback enabled right now.
            {modes.length > 0 ? ` Modes: ${modes.join(", ")}.` : ""}
          </div>
        </section>
      ) : null}

      {error ? (
        <section className="px-5 pt-3">
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

      {featuredGig ? (
        <>
          <HomeFeaturedGig gig={featuredGig} />
          {moreOpenGigs.length > 0 ? <OpenGigs gigs={moreOpenGigs} /> : null}
        </>
      ) : (
        <section className="px-5 pt-4">
          <div className="rounded-3xl bg-card p-6 text-center shadow-card">
            <Sparkles className="mx-auto h-8 w-8 text-bloom-green" />
            <p className="mt-3 text-base font-extrabold text-foreground">No open gigs yet</p>
            <p className="mt-1 text-sm font-semibold text-muted-foreground">
              Post a new gig and Bloom will turn it into the next earning moment.
            </p>
            <Link
              href="/parent/gigs/new"
              className="tap-target mt-4 inline-flex items-center gap-2 rounded-full bg-bloom-green px-5 py-3 font-extrabold text-white"
            >
              Create a gig
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>
      )}

      {report ? (
        <section className="px-5 pt-4">
          <div className="relative overflow-hidden rounded-[2rem] bg-[linear-gradient(135deg,#fff7d6_0%,#fffdf7_48%,#ddf6ee_100%)] p-5 shadow-card">
            <div className="pointer-events-none absolute -right-8 -top-10 h-28 w-28 rounded-full bg-petal-blue/60 blur-2xl" />
            <div className="pointer-events-none absolute -left-8 bottom-0 h-24 w-24 rounded-full bg-petal-coral/45 blur-2xl" />

            <div className="relative">
              <div className="inline-flex items-center gap-2 rounded-full bg-white/80 px-3 py-1 shadow-card backdrop-blur">
                <Sparkles className="h-4 w-4 text-bloom-green" />
                <p className="text-[11px] font-black uppercase tracking-[0.2em] text-bloom-green-deep/70">
                  Family highlight
                </p>
              </div>

              <h2 className="mt-3 text-2xl font-extrabold leading-tight text-foreground">
                {report.highlights[0]?.title ?? "This week with Bloom"}
              </h2>

              <p className="mt-2 max-w-[28ch] text-sm font-semibold leading-6 text-slate-700">
                {report.highlights[0]?.detail ?? report.savings_insight}
              </p>

              <div className="mt-4 rounded-2xl bg-white/85 p-4 shadow-card ring-1 ring-white/80 backdrop-blur">
                <p className="text-[11px] font-black uppercase tracking-[0.18em] text-bloom-green-deep/70">
                  Talk about it tonight
                </p>
                <p className="mt-2 text-sm font-extrabold leading-6 text-bloom-green-deep">
                  {report.conversation_starter}
                </p>
              </div>
            </div>
          </div>
        </section>
      ) : reportLoading ? (
        <section className="px-5 pt-4">
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
