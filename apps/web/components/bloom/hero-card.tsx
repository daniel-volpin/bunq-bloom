import Image from "next/image";
import { ArrowUpRight } from "lucide-react";
import { formatEuro } from "@/lib/gig-presentation";

export function HeroCard({
  balanceAmount,
  balanceAmountLoading = false,
  earnedThisWeek,
  earnedThisWeekLoading = false,
  childName = "Lotte"
}: {
  balanceAmount: string | number;
  balanceAmountLoading?: boolean;
  earnedThisWeek?: string | number | null;
  earnedThisWeekLoading?: boolean;
  childName?: string;
}) {
  return (
    <section className="px-5 pt-5">
      <div className="relative overflow-hidden rounded-3xl bg-hero-bloom shadow-card">
        <Image
          src="/bloom/hero-hills.svg"
          alt=""
          aria-hidden
          width={390}
          height={160}
          loading="eager"
          className="pointer-events-none absolute inset-x-0 bottom-0 h-auto w-full select-none opacity-70"
        />

        <div className="relative flex items-stretch gap-2 p-5 pb-6">
          <div className="flex flex-1 flex-col justify-between">
            <div>
              <h2 className="text-[22px] font-extrabold leading-tight text-bloom-green-deep">
                Hey {childName}!
              </h2>
              <p className="mt-1 text-xs font-semibold text-bloom-green-deep/70">
                Let&apos;s grow that piggy bank
              </p>
            </div>

            <div className="mt-5">
              {balanceAmountLoading ? (
                <div className="h-12 w-36 animate-pulse rounded-full bg-bloom-green/15" />
              ) : (
                <p className="text-[40px] font-extrabold leading-none text-bloom-green-deep">
                  {formatEuro(balanceAmount).replace(/\.00$/, "")}
                  {formatEuro(balanceAmount).endsWith(".00") ? <span className="text-2xl">.00</span> : null}
                </p>
              )}

              <div className="mt-3 inline-flex items-center gap-2 rounded-full bg-card/80 py-1 pl-1 pr-3 shadow-card backdrop-blur">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-bloom-green text-primary-foreground">
                  <ArrowUpRight className="h-3.5 w-3.5" strokeWidth={3} />
                </span>
                {earnedThisWeekLoading ? (
                  <span className="h-4 w-24 animate-pulse rounded-full bg-bloom-green/15" />
                ) : (
                  <span className="text-xs font-extrabold text-bloom-green-deep">
                    {formatEuro(earnedThisWeek ?? 0)}
                    <span className="ml-1 font-semibold text-bloom-green-deep/70">this week</span>
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="w-[40%] shrink-0" aria-hidden />
        </div>

        <Image
          src="/bloom/mascot-tulip.svg"
          alt="Bloom tulip mascot"
          width={180}
          height={200}
          className="pointer-events-none absolute bottom-0 right-2 h-auto w-[44%] max-w-[180px] select-none"
          priority
        />
      </div>
    </section>
  );
}