import { CheckCircle2, Coins, Flame, Sparkles } from "lucide-react";
import type { BloomReportResponse } from "@/lib/types";

function Tile({
  icon,
  label,
  value,
  accent
}: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
  accent: string;
}) {
  return (
    <div className="flex flex-col items-center gap-1 rounded-2xl bg-card p-3 shadow-card">
      <span className={`grid h-9 w-9 place-items-center rounded-full ${accent}`}>{icon}</span>
      <p className="text-base font-extrabold leading-none text-foreground">{value}</p>
      <p className="text-[10px] font-bold uppercase tracking-wide text-muted-foreground">{label}</p>
    </div>
  );
}

export function WeeklyStats({ report }: { report: BloomReportResponse }) {
  return (
    <div>
      <div className="mb-2 flex items-center gap-2 px-1">
        <Sparkles className="h-4 w-4 text-bloom-green" />
        <h3 className="text-sm font-extrabold text-foreground">This week</h3>
      </div>
      <div className="grid grid-cols-3 gap-2">
        <Tile
          icon={<Coins className="h-4 w-4 text-bloom-green-deep" />}
          accent="bg-petal-green"
          label="Earned"
          value={`€${report.stats.money_earned.amount}`}
        />
        <Tile
          icon={<CheckCircle2 className="h-4 w-4 text-bloom-blue" />}
          accent="bg-petal-blue"
          label="Gigs"
          value={report.stats.gigs_completed}
        />
        <Tile
          icon={<Flame className="h-4 w-4 text-bloom-coral" />}
          accent="bg-petal-coral"
          label="Avg"
          value={`€${report.stats.average_reward.amount}`}
        />
      </div>
      {report.highlights[0] ? (
        <p className="mt-2 px-1 text-xs font-extrabold text-bloom-green-deep">
          {report.highlights[0].detail}
        </p>
      ) : null}
    </div>
  );
}