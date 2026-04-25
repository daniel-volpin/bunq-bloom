import Link from "next/link";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Coins,
  RefreshCcw,
  ShieldCheck
} from "lucide-react";
import type { CompleteGigResponse, Currency } from "@/lib/types";

function formatMode(mode: string): string {
  return mode.replaceAll("_", " ");
}

function integrationMessage(result: CompleteGigResponse): string | null {
  if (result.fallback_mode) {
    return `Demo fallback is active: ${formatMode(result.mode)}. Bloom is explicit when part of the flow runs without a live integration.`;
  }

  if (result.payment_mode === "fake_local") {
    return `Demo payment mode: AI is ${formatMode(result.ai_mode)}, but payment and balance use local demo data.`;
  }

  if (result.ai_mode === "fake") {
    return "Demo AI mode: payment uses the real bunq sandbox path, while verification uses deterministic local AI.";
  }

  if (result.payment_mode === "real" && result.ai_mode === "real") {
    return "Live sandbox path: AI verification and bunq payment both used configured integrations.";
  }

  return null;
}

export function VerdictScreen({
  result,
  rewardAmount,
  currency = "EUR",
  onRetryPayment,
  onRetryWork,
  retryPending = false,
  backHref = "/gigs"
}: {
  result: CompleteGigResponse;
  rewardAmount?: string;
  currency?: Currency;
  onRetryPayment?: () => void;
  onRetryWork?: () => void;
  retryPending?: boolean;
  backHref?: string;
}) {
  const approved = result.verification.approved;
  const paymentSucceeded = result.payment?.status === "succeeded";
  const paymentFailed = result.payment?.status === "failed";
  const shownRewardAmount = result.payment?.amount ?? rewardAmount ?? "0.00";
  const shownCurrency = result.payment?.currency ?? currency;
  const detailMessage = integrationMessage(result);

  return (
    <section className="space-y-4 rounded-3xl bg-card p-5 shadow-card">
      <div
        className={`rounded-[1.5rem] p-4 ${
          approved ? "bg-bloom-green/10 text-bloom-green-deep" : "bg-bloom-sun/25 text-amber-900"
        }`}
      >
        <div className="mb-2 flex items-center gap-2 font-black">
          {approved ? <CheckCircle2 size={24} /> : <AlertTriangle size={24} />}
          {approved ? (paymentSucceeded ? "Approved and paid" : "Approved") : "Needs another try"}
        </div>
        <p className="text-sm leading-6">{result.verification.message_for_kid}</p>
      </div>

      {detailMessage ? (
        <div className="rounded-2xl bg-bloom-sky/10 p-4 text-sm leading-6 text-slate-700">
          {detailMessage}
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
          {result.payment?.merchant_reference ? (
            <p className="mt-1 truncate text-[10px] font-bold text-slate-500">
              Ref: {result.payment.merchant_reference}
            </p>
          ) : null}
        </div>
      </div>

      {paymentFailed ? (
        <div className="flex items-start gap-2 rounded-2xl border border-bloom-coral/20 bg-bloom-coral/10 p-4 text-sm leading-6 text-slate-700">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-bloom-coral" />
          <div>
            <p className="font-extrabold text-foreground">Payment still needs a retry.</p>
            <p>
              The work was approved, but the transfer did not complete yet. You can retry payment
              without taking new photos.
            </p>
            {result.payment?.error_code ? (
              <p className="mt-1 text-xs font-bold text-bloom-coral">
                Error code: {result.payment.error_code}
              </p>
            ) : null}
          </div>
        </div>
      ) : null}

      {result.balance_refresh_status === "failed" ? (
        <div className="flex items-start gap-2 rounded-2xl border border-bloom-sun/40 bg-bloom-sun/20 p-4 text-sm leading-6 text-slate-700">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-700" />
          <div>
            <p className="font-extrabold text-foreground">Payment succeeded, balance is catching up.</p>
            <p>
              Bloom will not retry the transfer automatically. Refresh the wallet later to avoid
              duplicate payments.
            </p>
            {result.balance_refresh_error ? (
              <p className="mt-1 text-xs font-bold text-amber-800">
                Balance refresh error: {result.balance_refresh_error}
              </p>
            ) : null}
          </div>
        </div>
      ) : null}

      {result.kid_balance ? (
        <div className="rounded-[1.5rem] bg-bloom-green p-4 text-white">
          <p className="text-sm font-bold opacity-90">New balance</p>
          <p className="text-3xl font-black">
            {result.kid_balance.amount} {result.kid_balance.currency}
          </p>
          <p className="text-xs font-bold opacity-80">Source: {result.kid_balance.source}</p>
        </div>
      ) : null}

      {!approved && onRetryWork ? (
        <button
          type="button"
          onClick={onRetryWork}
          disabled={retryPending}
          className="tap-target flex w-full items-center justify-center gap-2 rounded-2xl bg-bloom-green px-4 py-3 text-center font-black text-white disabled:cursor-not-allowed disabled:opacity-60"
        >
          <RefreshCcw size={18} />
          Try another after photo
        </button>
      ) : null}

      {paymentFailed && onRetryPayment ? (
        <button
          type="button"
          onClick={onRetryPayment}
          disabled={retryPending}
          className="tap-target flex w-full items-center justify-center gap-2 rounded-2xl bg-bloom-green px-4 py-3 text-center font-black text-white disabled:cursor-not-allowed disabled:opacity-60"
        >
          <RefreshCcw size={18} />
          {retryPending ? "Retrying payment..." : "Retry payment"}
        </button>
      ) : null}

      <Link
        href={backHref}
        className="tap-target flex w-full items-center justify-center rounded-2xl bg-bloom-ink px-4 py-3 text-center font-black text-white"
      >
        Back to gigs
      </Link>
    </section>
  );
}
