import Image from "next/image";
import { TrendingUp } from "lucide-react";
import { formatEuro } from "@/lib/gig-presentation";

export function WalletHero({
  balanceAmount,
  earnedThisWeek
}: {
  balanceAmount: string | number;
  earnedThisWeek: string | number;
}) {
  return (
    <div className="relative overflow-hidden rounded-3xl bg-hero-bloom p-5 shadow-card">
      <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-white/40 blur-xl" />
      <div className="relative flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-bold uppercase tracking-wide text-bloom-green-deep/70">
            My balance
          </p>
          <p className="mt-1 text-4xl font-extrabold leading-none text-bloom-green-deep">
            {formatEuro(balanceAmount)}
          </p>
          <p className="mt-2 text-xs font-semibold text-bloom-green-deep/70">
            Available to spend or save
          </p>
        </div>

        <Image src="/bloom/tulip-emblem.svg" alt="" width={48} height={48} className="h-12 w-12" />
      </div>

      <div className="mt-4 inline-flex items-center gap-1.5 rounded-full bg-card/80 px-3 py-1.5 text-xs font-extrabold text-bloom-green-deep shadow-card backdrop-blur">
        <TrendingUp className="h-3.5 w-3.5" />
        {formatEuro(earnedThisWeek)} this week
      </div>
    </div>
  );
}