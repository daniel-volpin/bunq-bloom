"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, Plus, Sparkles, X } from "lucide-react";
import { ApiClientError, apiClient } from "@/lib/api-client";

type ChecklistStep = {
  id: string;
  value: string;
};

function newChecklistStep(value = ""): ChecklistStep {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return { id: crypto.randomUUID(), value };
  }

  return { id: `step_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`, value };
}

export default function NewGigPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [rewardAmount, setRewardAmount] = useState("5.00");
  const [steps, setSteps] = useState<ChecklistStep[]>([
    newChecklistStep("bed made"),
    newChecklistStep("floor clear"),
    newChecklistStep("desk tidy")
  ]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submitGig(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const checklist = steps.map((item) => item.value.trim()).filter(Boolean);

      await apiClient.createGig({
        title,
        description,
        reward_amount: rewardAmount,
        currency: "EUR",
        verification_checklist: checklist
      });
      router.push("/gigs");
    } catch (caught) {
      setError(
        caught instanceof ApiClientError
          ? caught.message
          : "Could not create that gig. Check the backend and try again."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="px-5 pt-6 pb-8">
      <header className="flex items-center gap-2 pb-3">
        <Link
          href="/gigs"
          aria-label="Back to gigs"
          className="tap-target grid h-10 w-10 place-items-center rounded-full bg-card shadow-card"
        >
          <ChevronLeft className="h-5 w-5 text-foreground" />
        </Link>
        <div>
          <p className="text-sm font-bold text-muted-foreground">Parent</p>
          <h1 className="text-2xl font-extrabold text-foreground">Post a gig</h1>
        </div>
      </header>

      <p className="text-sm font-semibold text-muted-foreground">
        Add something that helps the family. Keep the reward fair and the checklist clear.
      </p>

      {error ? (
        <div className="mt-4 rounded-3xl border border-bloom-coral/20 bg-bloom-coral/10 p-4 text-sm leading-6 text-slate-700 shadow-card">
          {error}
        </div>
      ) : null}

      <form onSubmit={(event) => void submitGig(event)} className="mt-5 space-y-4">
        <label className="block rounded-3xl bg-card p-4 shadow-card">
          <span className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Title</span>
          <input
            required
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Clean your room"
            className="tap-target mt-2 w-full rounded-2xl border-0 bg-muted px-4 py-3 font-bold outline-none ring-0"
          />
        </label>

        <label className="block rounded-3xl bg-card p-4 shadow-card">
          <span className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
            Description
          </span>
          <textarea
            required
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Make the bed, clear the floor, and tidy the desk."
            rows={4}
            className="mt-2 w-full rounded-2xl border-0 bg-muted px-4 py-3 font-semibold outline-none ring-0"
          />
        </label>

        <label className="block rounded-3xl bg-card p-4 shadow-card">
          <span className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
            Reward in EUR
          </span>
          <div className="mt-2 flex items-center gap-2 rounded-2xl bg-bloom-green/10 px-4 py-3">
            <span className="text-2xl font-extrabold text-bloom-green-deep">€</span>
            <input
              required
              inputMode="decimal"
              value={rewardAmount}
              onChange={(event) => setRewardAmount(event.target.value)}
              className="tap-target w-full bg-transparent text-2xl font-extrabold text-bloom-green-deep outline-none"
            />
          </div>
        </label>

        <section className="rounded-3xl bg-card p-4 shadow-card">
          <span className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
            Checklist
          </span>
          <div className="mt-3 space-y-2">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center gap-2">
                <input
                  value={step.value}
                  onChange={(event) => {
                    setSteps((current) =>
                      current.map((currentStep, currentIndex) =>
                        currentIndex === index
                          ? { ...currentStep, value: event.target.value }
                          : currentStep
                      )
                    );
                  }}
                  placeholder={`Step ${index + 1}`}
                  className="tap-target w-full rounded-full border-0 bg-muted px-4 py-3 text-sm font-semibold outline-none"
                />
                {steps.length > 1 ? (
                  <button
                    type="button"
                    onClick={() =>
                      setSteps((current) => current.filter((_, currentIndex) => currentIndex !== index))
                    }
                    aria-label={`Remove step ${index + 1}`}
                    className="tap-target grid h-11 w-11 shrink-0 place-items-center rounded-full bg-muted text-muted-foreground"
                  >
                    <X className="h-4 w-4" />
                  </button>
                ) : null}
              </div>
            ))}
          </div>

          {steps.length < 6 ? (
            <button
              type="button"
              onClick={() => setSteps((current) => [...current, newChecklistStep()])}
              className="tap-target mt-3 inline-flex items-center gap-1.5 rounded-full bg-bloom-green/10 px-4 py-2 text-sm font-bold text-bloom-green-deep"
            >
              <Plus className="h-4 w-4" />
              Add step
            </button>
          ) : null}
        </section>

        <button
          type="submit"
          disabled={submitting}
          className="tap-target inline-flex w-full items-center justify-center gap-2 rounded-full bg-bloom-green px-5 py-4 text-lg font-black text-white shadow-card disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          <Sparkles size={20} />
          {submitting ? "Creating..." : "Create gig"}
        </button>
      </form>
    </div>
  );
}
