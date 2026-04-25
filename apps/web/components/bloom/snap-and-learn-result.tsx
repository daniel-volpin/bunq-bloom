import Link from "next/link";
import { Camera, Coins, Goal, Sparkles } from "lucide-react";
import type { BloomReportResponse, SnapAndLearnResponse } from "@/lib/types";

function buildSaveGoalHref(result: SnapAndLearnResponse) {
  const params = new URLSearchParams({
    openGoal: "1",
    label: result.analysis.item_name,
    amount: result.analysis.estimated_price.amount
  });

  return `/profile?${params.toString()}`;
}

function modeMessage(result: SnapAndLearnResponse) {
  if (result.fallback_mode) {
    return "Bloom used an explicit fallback estimate because AI was unavailable. Keep the suggestion honest in the demo.";
  }

  switch (result.mode) {
    case "fake_local":
      return "The price idea is ready, and the balance is coming from local demo money data.";
    case "fake_ai":
      return "The balance is live, but the item analysis came from demo AI.";
    case "real":
      return "This suggestion used the live configured providers.";
    default:
      return "Bloom prepared a savings suggestion for this item.";
  }
}

function paceMessage(result: SnapAndLearnResponse, report: BloomReportResponse | null, reportLoading: boolean) {
  if (reportLoading) {
    return "Checking your recent earning pace...";
  }

  if (!report) {
    return "Bloom could not load your recent earning pace yet.";
  }

  const targetAmount = Number(result.analysis.estimated_price.amount);
  const balanceAmount = Number(result.kid_balance.amount);
  const weeklyEarnings = Number(report.stats.money_earned.amount);
  const start = Date.parse(`${report.period.start_date}T00:00:00Z`);
  const end = Date.parse(`${report.period.end_date}T00:00:00Z`);

  if (!Number.isFinite(targetAmount) || !Number.isFinite(balanceAmount) || !Number.isFinite(weeklyEarnings)) {
    return "Bloom could not turn this into a time estimate yet.";
  }

  const remainingAmount = Math.max(0, targetAmount - balanceAmount);

  if (remainingAmount <= 0) {
    return "At your current balance, you could already afford this now.";
  }

  if (weeklyEarnings <= 0) {
    return "Finish a paid gig first, then Bloom can estimate how long this goal should take.";
  }

  const periodDays =
    Number.isFinite(start) && Number.isFinite(end) ? Math.max(1, Math.round((end - start) / 86400000) + 1) : 7;
  const dailyRate = weeklyEarnings / periodDays;

  if (!Number.isFinite(dailyRate) || dailyRate <= 0) {
    return "Bloom needs a bit more earning history before it can predict timing.";
  }

  const estimatedDays = Math.max(1, Math.ceil(remainingAmount / dailyRate));

  if (estimatedDays === 1) {
    return `At your recent pace of about EUR ${dailyRate.toFixed(2)} a day, this could take around 1 day.`;
  }

  if (estimatedDays < 14) {
    return `At your recent pace of about EUR ${dailyRate.toFixed(2)} a day, this could take around ${estimatedDays} days.`;
  }

  const estimatedWeeks = Math.ceil(estimatedDays / 7);
  return `At your recent pace of about EUR ${weeklyEarnings.toFixed(2)} a week, this could take around ${estimatedWeeks} weeks.`;
}

export function SnapAndLearnResult({
  result,
  report,
  reportLoading,
  onTryAnother
}: {
  result: SnapAndLearnResponse;
  report: BloomReportResponse | null;
  reportLoading: boolean;
  onTryAnother: () => void;
}) {
  const confidence = result.analysis.confidence;
  const saveGoalHref = buildSaveGoalHref(result);
  const goalPaceMessage = paceMessage(result, report, reportLoading);

  return (
    <section className="space-y-4 rounded-3xl bg-card p-5 shadow-card">
      <div className="rounded-[1.5rem] bg-bloom-blue/10 p-4 text-bloom-green-deep">
        <div className="mb-2 flex items-center gap-2 font-black">
          <Sparkles className="h-5 w-5" />
          Bloom spotted something to save for
        </div>
        <p className="text-xl font-extrabold text-foreground">{result.analysis.item_name}</p>
        {typeof confidence === "number" && confidence > 0 ? (
          <p className="mt-2 text-sm font-semibold text-slate-600">
            About {Math.round(confidence * 100)}% confident in this estimate.
          </p>
        ) : null}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-2xl bg-slate-50 p-4">
          <Coins className="mb-2 h-5 w-5 text-bloom-green" />
          <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Estimated price</p>
          <p className="text-lg font-black text-foreground">
            {result.analysis.estimated_price.amount} {result.analysis.estimated_price.currency}
          </p>
        </div>
        <div className="rounded-2xl bg-slate-50 p-4">
          <Goal className="mb-2 h-5 w-5 text-bloom-blue" />
          <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Gigs needed</p>
          <p className="text-lg font-black text-foreground">{result.analysis.gigs_needed}</p>
        </div>
      </div>

      <div className="rounded-2xl bg-bloom-green p-4 text-white">
        <p className="text-sm font-bold opacity-90">Current balance</p>
        <p className="text-3xl font-black">
          {result.kid_balance.amount} {result.kid_balance.currency}
        </p>
        <p className="text-xs font-bold opacity-80">Source: {result.kid_balance.source}</p>
      </div>

      <div className="rounded-2xl bg-bloom-cream p-4 text-sm leading-6 text-slate-700">
        <p className="mb-1 text-xs font-black uppercase tracking-wide text-slate-500">Suggested goal</p>
        <p className="font-extrabold text-foreground">{result.analysis.suggested_goal}</p>
      </div>

      <div className="rounded-2xl bg-petal-blue p-4 text-sm leading-6 text-bloom-green-deep">
        <p className="mb-1 text-xs font-black uppercase tracking-wide text-slate-500">Time to goal</p>
        <p className="font-extrabold">{goalPaceMessage}</p>
      </div>

      <Link
        href={saveGoalHref}
        className="tap-target flex w-full items-center justify-center rounded-2xl bg-bloom-blue px-4 py-3 text-center font-black text-white"
      >
        Save as my goal
      </Link>

      <div className="rounded-2xl bg-bloom-sky/10 p-4 text-sm leading-6 text-slate-700">
        {modeMessage(result)}
      </div>

      <button
        type="button"
        onClick={onTryAnother}
        className="tap-target flex w-full items-center justify-center gap-2 rounded-2xl bg-bloom-green px-4 py-3 text-center font-black text-white"
      >
        <Camera className="h-4 w-4" />
        Try another item
      </button>

      <Link
        href="/gigs"
        className="tap-target flex w-full items-center justify-center rounded-2xl bg-bloom-ink px-4 py-3 text-center font-black text-white"
      >
        Find gigs to earn it
      </Link>
    </section>
  );
}