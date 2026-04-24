import Link from "next/link";
import { AlertTriangle, CheckCircle2, Coins, ShieldCheck } from "lucide-react";
import type { CompleteGigResponse, Currency } from "@/lib/types";

export function VerdictScreen({
  result,
  rewardAmount,
  currency = "EUR"
}: {
  result: CompleteGigResponse;
  rewardAmount?: string;
  currency?: Currency;
}) {
  const approved = result.verification.approved;
  const paymentSucceeded = result.payment?.status === "succeeded";
  const paymentFailed = result.payment?.status === "failed";
  const shownRewardAmount = result.payment?.amount ?? rewardAmount ?? "0.00";
  const shownCurrency = result.payment?.currency ?? currency;

  return (
    <section className="space-y-4 rounded-[2rem] border border-white/70 bg-white/95 p-5 shadow-bloom">
      <div
        className={`rounded-[1.5rem] p-4 ${
          approved ? "bg-bloom-leaf/12 text-emerald-900" : "bg-bloom-sun/30 text-amber-900"
        }`}
      >
        <div className="mb-2 flex items-center gap-2 font-black">
          {approved ? <CheckCircle2 size={24} /> : <AlertTriangle size={24} />}
          {approved ? "Approved" : "Needs another try"}
        </div>
        <p className="text-sm leading-6">{result.verification.message_for_kid}</p>
      </div>

      {result.fallback_mode ? (
        <div className="rounded-2xl bg-bloom-sky/10 p-4 text-sm leading-6 text-slate-700">
          Demo fallback is active: <strong>{result.mode.replace("_", " ")}</strong>. This keeps
          the flow visible while an integration is unavailable.
        </div>
      ) : null}

      <div>
        <h3 className="mb-2 text-sm font-black uppercase tracking-wide text-slate-500">
          What Bloom noticed
        </h3>
        <div className="flex flex-wrap gap-2">
          {result.verification.tags.length > 0 ? (
            result.verification.tags.map((tag) => (
              <span key={tag} className="rounded-full bg-bloom-cream px-3 py-1 text-sm font-bold">
                {tag}
              </span>
            ))
          ) : (
            <span className="text-sm text-slate-500">No checklist tags returned yet.</span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-2xl bg-slate-50 p-4">
          <Coins className="mb-2 text-bloom-leaf" size={22} />
          <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Reward</p>
          <p className="text-lg font-black">
            {shownRewardAmount} {shownCurrency}
          </p>
        </div>
        <div className="rounded-2xl bg-slate-50 p-4">
          <ShieldCheck className="mb-2 text-bloom-sky" size={22} />
          <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Payment</p>
          <p className="text-lg font-black">
            {paymentSucceeded ? "Paid" : paymentFailed ? "Failed" : "Not paid"}
          </p>
        </div>
      </div>

      {result.kid_balance ? (
        <div className="rounded-[1.5rem] bg-bloom-leaf p-4 text-white">
          <p className="text-sm font-bold opacity-90">New balance</p>
          <p className="text-3xl font-black">
            {result.kid_balance.amount} {result.kid_balance.currency}
          </p>
          <p className="text-xs font-bold opacity-80">Source: {result.kid_balance.source}</p>
        </div>
      ) : null}

      <Link
        href="/gigs"
        className="tap-target flex w-full items-center justify-center rounded-2xl bg-bloom-ink px-4 py-3 text-center font-black text-white"
      >
        Back to gigs
      </Link>
    </section>
  );
}
