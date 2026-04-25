"use client";

import { useState } from "react";
import Image from "next/image";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Bell,
  Camera,
  CheckCircle2,
  ChevronRight,
  Coins,
  Flame,
  LogOut,
  Target,
  Users,
  Volume2
} from "lucide-react";
import { Header } from "@/components/bloom/header";
import { SavingsGoalDialog } from "@/components/bloom/savings-goal-dialog";
import { useBloomSummary } from "@/lib/use-bloom-summary";
import { useSavedGoal } from "@/lib/use-saved-goal";
import { Switch } from "@/components/ui/switch";

function ProfileStat({
  icon,
  value,
  label,
  accent
}: {
  icon: React.ReactNode;
  value: React.ReactNode;
  label: string;
  accent: string;
}) {
  return (
    <div className="flex flex-col items-center gap-1.5 rounded-2xl bg-card p-3 shadow-card">
      <span className={`grid h-9 w-9 place-items-center rounded-full ${accent}`}>{icon}</span>
      <span className="text-base font-extrabold leading-none text-bloom-green-deep">{value}</span>
      <span className="text-[10px] font-bold uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
    </div>
  );
}

const ProfileRow = ({ icon, label, trailing, onClick, showChevron = false }: {
  icon: React.ReactNode;
  label: string;
  trailing?: React.ReactNode;
  onClick?: () => void;
  showChevron?: boolean;
}) => {
  const Tag = onClick ? "button" : "div";

  return (
    <Tag
      type={onClick ? "button" : undefined}
      onClick={onClick}
      className={`flex w-full items-center gap-3 rounded-2xl bg-card px-4 py-3 text-left shadow-card ${
        onClick ? "transition-transform active:scale-[0.99]" : ""
      }`}
    >
      <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-bloom-green/10 text-bloom-green-deep">
        {icon}
      </span>
      <span className="flex-1 text-sm font-extrabold text-foreground">{label}</span>
      {trailing && (
        <span className="text-xs font-semibold text-muted-foreground">{trailing}</span>
      )}
      {showChevron && <ChevronRight className="h-4 w-4 text-muted-foreground" />}
    </Tag>
  );
};

function calculateStreakDays(updatedAtValues: Array<string | undefined>) {
  const uniqueDays = [...new Set(updatedAtValues.filter(Boolean).map((value) => value!.slice(0, 10)))].sort(
    (left, right) => right.localeCompare(left)
  );

  if (uniqueDays.length === 0) {
    return 0;
  }

  let streak = 1;
  let cursor = new Date(`${uniqueDays[0]}T00:00:00Z`);

  for (let index = 1; index < uniqueDays.length; index += 1) {
    const nextDay = new Date(cursor);
    nextDay.setUTCDate(nextDay.getUTCDate() - 1);

    const expected = nextDay.toISOString().slice(0, 10);

    if (uniqueDays[index] !== expected) {
      break;
    }

    streak += 1;
    cursor = nextDay;
  }

  return streak;
}

export default function ProfilePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { report, paidGigs, fallbackMode } = useBloomSummary();
  const { savedGoal, setSavedGoal } = useSavedGoal();
  const [goalOpen, setGoalOpen] = useState(false);
  const [goalState, setGoalState] = useState({
    label: savedGoal?.label ?? report?.highlights[0]?.title ?? "",
    amount: savedGoal?.amount ?? "45.00"
  });
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [soundsEnabled, setSoundsEnabled] = useState(true);

  const streakDays = calculateStreakDays(paidGigs.map((gig) => gig.updated_at));
  const weeklyEarnings = report?.stats.money_earned.amount ?? "0.00";
  const goalSummary = goalState.label || report?.highlights[0]?.title || "Not set";
  const snapGoalLabel = searchParams.get("label")?.trim() ?? "";
  const snapGoalAmount = searchParams.get("amount")?.trim() ?? "";
  const hasSnapGoalPrefill =
    searchParams.get("openGoal") === "1" && snapGoalLabel.length > 0 && snapGoalAmount.length > 0;
  const dialogOpen = goalOpen || hasSnapGoalPrefill;
  const goalInitialLabel = hasSnapGoalPrefill
    ? snapGoalLabel
    : goalState.label || report?.highlights[0]?.title || "";
  const goalInitialAmount = hasSnapGoalPrefill ? snapGoalAmount : goalState.amount;

  function handleGoalOpenChange(open: boolean) {
    setGoalOpen(open);

    if (!open && hasSnapGoalPrefill) {
      router.replace("/profile", { scroll: false });
    }
  }

  function handleGoalSave(goal: { label: string; amount: string }) {
    setGoalState(goal);
    setSavedGoal(goal);

    if (hasSnapGoalPrefill) {
      router.replace("/profile", { scroll: false });
    }
  }

  return (
    <div className="pb-8">
      <Header actionHref="/wallet" actionLabel="Wallet" />

      <main className="px-5 pt-2">
        <section className="flex flex-col items-center text-center">
          <div className="grid h-24 w-24 place-items-center rounded-full bg-petal-yellow shadow-card">
            <Image
              src="/bloom/profile-flower-icon.svg"
              alt="Lotte"
              width={72}
              height={72}
              className="h-[72px] w-[72px] p-3"
            />
          </div>
          <h1 className="mt-3 text-2xl font-extrabold text-foreground">Lotte</h1>
          <span className="mt-1 inline-flex items-center rounded-full bg-bloom-green/10 px-3 py-1 text-[11px] font-extrabold uppercase tracking-wide text-bloom-green-deep">
            Kid account
          </span>
          <p className="mt-2 text-xs font-semibold text-muted-foreground">
            Bloom family · Member since Apr 2026
          </p>
        </section>

        <section className="mt-6 grid grid-cols-3 gap-2">
          <ProfileStat
            icon={<CheckCircle2 className="h-4 w-4 text-bloom-green-deep" strokeWidth={2.2} />}
            accent="bg-petal-green"
            value={paidGigs.length}
            label="Gigs done"
          />
          <ProfileStat
            icon={<Flame className="h-4 w-4 text-bloom-coral" strokeWidth={2.2} />}
            accent="bg-petal-coral"
            value={`${streakDays}d`}
            label="Streak"
          />
          <ProfileStat
            icon={<Coins className="h-4 w-4 text-bloom-green-deep" strokeWidth={2.2} />}
            accent="bg-petal-yellow"
            value={`€${weeklyEarnings}`}
            label="This week"
          />
        </section>

        <section className="mt-6">
          <h2 className="mb-2 px-1 text-[11px] font-extrabold uppercase tracking-wide text-muted-foreground">
            Account
          </h2>
          <div className="space-y-2">
            <ProfileRow
              icon={<Target className="h-4 w-4" strokeWidth={2.2} />}
              label="Savings goal"
              trailing={goalSummary}
              showChevron
              onClick={() => setGoalOpen(true)}
            />
            <ProfileRow
              icon={<Users className="h-4 w-4" strokeWidth={2.2} />}
              label="Linked parent"
              trailing="Mom"
            />
            <ProfileRow
              icon={<Camera className="h-4 w-4" strokeWidth={2.2} />}
              label="Snap & Learn"
              trailing="Photo goal"
              showChevron
              onClick={() => router.push("/snap-and-learn")}
            />
            <ProfileRow
              icon={<Bell className="h-4 w-4" strokeWidth={2.2} />}
              label="Notifications"
              trailing={
                <Switch
                  checked={notificationsEnabled}
                  onCheckedChange={setNotificationsEnabled}
                  aria-label="Toggle notifications"
                />
              }
            />
            <ProfileRow
              icon={<Volume2 className="h-4 w-4" strokeWidth={2.2} />}
              label="Sounds"
              trailing={
                <Switch
                  checked={soundsEnabled}
                  onCheckedChange={setSoundsEnabled}
                  aria-label="Toggle sounds"
                />
              }
            />
          </div>
        </section>

        {fallbackMode ? (
          <section className="mt-6 rounded-3xl bg-bloom-sky/10 p-4 text-sm leading-6 text-slate-700 shadow-card">
            Demo fallback is active, so this profile is showing backend-safe summary data rather than pretending unavailable integrations worked.
          </section>
        ) : null}

        <section className="mt-8 flex flex-col items-center gap-3">
          <button
            type="button"
            className="tap-target inline-flex h-11 items-center gap-1.5 rounded-full bg-muted px-5 text-sm font-extrabold text-muted-foreground active:scale-95"
          >
            <LogOut className="h-4 w-4" strokeWidth={2.2} />
            Sign out
          </button>
          <p className="text-[10px] font-semibold text-muted-foreground">Bloom v0.1</p>
        </section>
      </main>

      <SavingsGoalDialog
        key={`${goalOpen}-${goalState.label || report?.highlights[0]?.title || ""}-${goalState.amount}`}
        open={dialogOpen}
        onOpenChange={handleGoalOpenChange}
        initialLabel={goalInitialLabel}
        initialAmount={goalInitialAmount}
        onSave={handleGoalSave}
      />
    </div>
  );
}

