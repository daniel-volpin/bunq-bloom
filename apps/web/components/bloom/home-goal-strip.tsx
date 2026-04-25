import Link from "next/link";
import { ChevronRight, Target } from "lucide-react";
import { formatEuro } from "@/lib/gig-presentation";
import type { SavedGoal } from "@/lib/use-saved-goal";

export function HomeGoalStrip({
  goal,
  balanceAmount,
  connected = false
}: {
  goal: SavedGoal;
  balanceAmount: string;
  connected?: boolean;
}) {
  const targetAmount = Number(goal.amount);
  const currentBalance = Number(balanceAmount);

  if (!Number.isFinite(targetAmount) || targetAmount <= 0 || !Number.isFinite(currentBalance)) {
    return null;
  }

  const remainingAmount = Math.max(0, targetAmount - currentBalance);
  const progressRatio = Math.min(Math.max(currentBalance / targetAmount, 0), 1);

  const strip = (
    <Link
      href="/profile"
      className={`block bg-card px-4 py-4 transition-transform active:scale-[0.99] ${connected ? "border-t border-slate-100/80" : "rounded-3xl shadow-card"}`}
    >
        <div className="flex items-center gap-3">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-bloom-blue/10 text-bloom-blue">
            <Target className="h-4 w-4" />
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-[11px] font-black uppercase tracking-[0.18em] text-bloom-green-deep/70">
              Saving for
            </p>
            <p className="truncate text-sm font-extrabold text-foreground">{goal.label}</p>
          </div>
          <div className="text-right">
            <p className="text-[10px] font-black uppercase tracking-wide text-slate-500">Still need</p>
            <p className="text-sm font-extrabold text-bloom-green-deep">{formatEuro(remainingAmount)}</p>
          </div>
          <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
        </div>

        <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-bloom-green transition-[width]"
            style={{ width: `${Math.max(progressRatio * 100, 6)}%` }}
          />
        </div>
      </Link>
  );

  if (connected) {
    return strip;
  }

  return <section className="px-5 pt-4">{strip}</section>;
}