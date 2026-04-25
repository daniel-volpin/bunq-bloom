import Link from "next/link";
import { Coins, Goal, Sparkles } from "lucide-react";
import type { BloomReportResponse, SnapAndLearnResponse } from "@/lib/types";

function formatEurAmount(value: number) {
  return `€${value.toFixed(2)}`;
}

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
    return "Demo note: Bloom used a fallback guess for this item.";
  }

  switch (result.mode) {
    case "fake_local":
      return "Demo note: balance is coming from local demo data.";
    case "fake_ai":
      return "Demo note: this item guess came from demo AI.";
    default:
      return null;
  }
}

function paceMessage(
  result: SnapAndLearnResponse,
  report: BloomReportResponse | null,
  reportLoading: boolean
) {
  if (reportLoading) {
    return "Checking this week's pace";
  }

  if (!report) {
    return "No pace yet";
  }

  const targetAmount = Number(result.analysis.estimated_price.amount);
  const balanceAmount = Number(result.kid_balance.amount);
  const weeklyEarnings = Number(report.stats.money_earned.amount);
  const start = Date.parse(`${report.period.start_date}T00:00:00Z`);
  const end = Date.parse(`${report.period.end_date}T00:00:00Z`);

  if (!Number.isFinite(targetAmount) || !Number.isFinite(balanceAmount) || !Number.isFinite(weeklyEarnings)) {
    return "No pace yet";
  }

  const remainingAmount = Math.max(0, targetAmount - balanceAmount);

  if (remainingAmount <= 0) {
    return "You can get this now";
  }

  if (weeklyEarnings <= 0) {
    return "Do 1 paid gig first";
  }

  const periodDays =
    Number.isFinite(start) && Number.isFinite(end) ? Math.max(1, Math.round((end - start) / 86400000) + 1) : 7;
  const dailyRate = weeklyEarnings / periodDays;

  if (!Number.isFinite(dailyRate) || dailyRate <= 0) {
    return "No pace yet";
  }

  const estimatedDays = Math.max(1, Math.ceil(remainingAmount / dailyRate));

  if (estimatedDays === 1) {
    return "About 1 day";
  }

  if (estimatedDays < 14) {
    return `About ${estimatedDays} days`;
  }

  const estimatedWeeks = Math.ceil(estimatedDays / 7);
  return `About ${estimatedWeeks} weeks`;
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
  const saveGoalHref = buildSaveGoalHref(result);
  const goalPaceMessage = paceMessage(result, report, reportLoading);
  const detailMessage = modeMessage(result);
  const targetAmount = Number(result.analysis.estimated_price.amount);
  const balanceAmount = Number(result.kid_balance.amount);
  const remainingAmount =
    Number.isFinite(targetAmount) && Number.isFinite(balanceAmount)
      ? Math.max(0, targetAmount - balanceAmount)
      : null;
  const progressRatio =
    Number.isFinite(targetAmount) && targetAmount > 0 && Number.isFinite(balanceAmount)
      ? Math.min(balanceAmount / targetAmount, 1)
      : null;

  return (
    <section className="space-y-4 rounded-3xl bg-card p-5 shadow-card">
      <div className="rounded-[1.5rem] bg-bloom-blue/10 p-4 text-bloom-green-deep">
        <div className="mb-2 flex items-center gap-2 font-black">
          <Sparkles className="h-5 w-5" />
          Bloom found
        </div>
        <p className="text-xl font-extrabold text-foreground">{result.analysis.item_name}</p>
        <p className="mt-2 text-sm font-semibold text-slate-600">Can this be your next goal?</p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-2xl bg-slate-50 p-4">
          <Coins className="mb-2 h-5 w-5 text-bloom-green" />
          <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Costs</p>
          <p className="text-lg font-black text-foreground">{formatEurAmount(targetAmount)}</p>
        </div>
        <div className="rounded-2xl bg-slate-50 p-4">
          <Goal className="mb-2 h-5 w-5 text-bloom-blue" />
          <p className="text-xs font-bold uppercase tracking-wide text-slate-500">More gigs</p>
          <p className="text-lg font-black text-foreground">{result.analysis.gigs_needed}</p>
        </div>
      </div>

      {remainingAmount !== null ? (
        <div className="space-y-3 rounded-2xl bg-slate-50 p-3">
          <div className="grid grid-cols-3 gap-2">
            <div className="rounded-2xl bg-white p-3 text-center shadow-card">
              <p className="text-[10px] font-black uppercase tracking-wide text-slate-500">You have</p>
              <p className="mt-1 text-sm font-black text-foreground">{formatEurAmount(balanceAmount)}</p>
            </div>
            <div className="rounded-2xl bg-white p-3 text-center shadow-card">
              <p className="text-[10px] font-black uppercase tracking-wide text-slate-500">It costs</p>
              <p className="mt-1 text-sm font-black text-foreground">{formatEurAmount(targetAmount)}</p>
            </div>
            <div className="rounded-2xl bg-petal-yellow p-3 text-center">
              <p className="text-[10px] font-black uppercase tracking-wide text-slate-500">Still need</p>
              <p className="mt-1 text-sm font-black text-bloom-green-deep">
                {formatEurAmount(remainingAmount)}
              </p>
            </div>
          </div>

          {progressRatio !== null ? (
            <div>
              <div className="mb-1 flex items-center justify-between text-[10px] font-black uppercase tracking-wide text-slate-500">
                <span>Goal progress</span>
                <span>{Math.round(progressRatio * 100)}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-white">
                <div
                  className="h-full rounded-full bg-bloom-green transition-[width]"
                  style={{ width: `${Math.max(progressRatio * 100, 6)}%` }}
                />
              </div>
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="rounded-2xl bg-petal-blue p-4 text-sm leading-6 text-bloom-green-deep">
        <p className="mb-1 text-xs font-black uppercase tracking-wide text-slate-500">Time</p>
        <p className="text-lg font-extrabold">{goalPaceMessage}</p>
        <p className="mt-1 text-xs font-semibold text-slate-600">Based on this week&apos;s earnings.</p>
      </div>

      <div className="rounded-2xl bg-card p-4 ring-1 ring-slate-100">
        <p className="text-sm font-black text-foreground">Save for this now?</p>
        <div className="mt-3 space-y-2">
          <Link
            href={saveGoalHref}
            className="tap-target flex w-full items-center justify-center rounded-2xl bg-bloom-blue px-4 py-3 text-center font-black text-white"
          >
            Yes, make it my goal
          </Link>
          <button
            type="button"
            onClick={onTryAnother}
            className="tap-target flex w-full items-center justify-center rounded-2xl bg-muted px-4 py-3 text-center font-black text-muted-foreground"
          >
            Try another
          </button>
        </div>
      </div>

      {detailMessage ? (
        <div className="rounded-2xl bg-bloom-sky/10 p-3 text-xs font-semibold leading-5 text-slate-700">
          {detailMessage}
        </div>
      ) : null}
    </section>
  );
}