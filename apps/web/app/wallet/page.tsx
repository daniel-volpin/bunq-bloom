"use client";

import Link from "next/link";
import { RefreshCcw, Sparkles } from "lucide-react";
import { EarningRow } from "@/components/bloom/earning-row";
import { Header } from "@/components/bloom/header";
import { WalletHero } from "@/components/bloom/wallet-hero";
import { WeeklyStats } from "@/components/bloom/weekly-stats";
import { useBloomSummary } from "@/lib/use-bloom-summary";

export default function WalletPage() {
  const { loading, error, balanceResponse, report, paidGigs, fallbackMode, reload } =
    useBloomSummary();

  return (
    <div className="pb-8">
      <Header actionHref="/gigs" actionLabel="All gigs" />

      <div className="px-5 pt-2">
        <h1 className="text-2xl font-extrabold text-foreground">Wallet</h1>
        <p className="text-xs font-semibold text-muted-foreground">
          Track what you’ve earned and how the week is going.
        </p>

        {error ? (
          <div className="mt-4 rounded-3xl border border-bloom-coral/20 bg-bloom-coral/10 p-4 text-sm leading-6 text-slate-700 shadow-card">
            {error}
            <button
              type="button"
              onClick={reload}
              className="tap-target mt-3 inline-flex items-center gap-2 rounded-full bg-card px-4 py-2 font-extrabold text-bloom-green-deep shadow-card"
            >
              <RefreshCcw className="h-4 w-4" />
              Refresh
            </button>
          </div>
        ) : null}

        <div className="mt-4 space-y-4">
          <WalletHero
            balanceAmount={balanceResponse?.balance.amount ?? "0.00"}
            earnedThisWeek={report?.stats.money_earned.amount ?? "0.00"}
          />

          {report ? <WeeklyStats report={report} /> : null}

          {report ? (
            <div className="rounded-3xl bg-card p-4 shadow-card">
              <p className="text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
                Savings insight
              </p>
              <p className="mt-2 text-sm font-semibold text-foreground/80">{report.savings_insight}</p>
              <p className="mt-3 rounded-2xl bg-bloom-green/10 p-3 text-sm font-semibold text-bloom-green-deep">
                {report.conversation_starter}
              </p>
            </div>
          ) : null}

          {fallbackMode ? (
            <div className="rounded-3xl bg-bloom-sky/10 p-4 text-sm leading-6 text-slate-700 shadow-card">
              Demo fallback is visible here too, so balance and earnings stay honest during the demo.
            </div>
          ) : null}

          <div>
            <div className="mb-2 flex items-center gap-2 px-1">
              <Sparkles className="h-4 w-4 text-bloom-green" />
              <h3 className="text-sm font-extrabold text-foreground">Recent earnings</h3>
            </div>

            {loading ? (
              <div className="space-y-2">
                <div className="h-16 animate-pulse rounded-2xl bg-white/70" />
                <div className="h-16 animate-pulse rounded-2xl bg-white/70" />
              </div>
            ) : paidGigs.length === 0 ? (
              <div className="rounded-3xl bg-card p-8 text-center shadow-card">
                <p className="text-sm font-extrabold text-foreground">No earnings yet</p>
                <p className="mt-1 text-xs font-semibold text-muted-foreground">
                  Complete your first gig to see it here.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {paidGigs.slice(0, 8).map((gig) => (
                  <EarningRow key={gig.id} gig={gig} />
                ))}
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-2">
            <Link
              href="/gigs"
              className="tap-target flex items-center justify-center rounded-full bg-card px-4 py-3 text-sm font-extrabold text-bloom-green-deep shadow-card"
            >
              View gigs
            </Link>
            <Link
              href="/gigs/new"
              className="tap-target flex items-center justify-center rounded-full bg-bloom-green px-4 py-3 text-sm font-extrabold text-white shadow-card"
            >
              Post a gig
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
