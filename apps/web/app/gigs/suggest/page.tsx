"use client";

import Link from "next/link";
import { useState } from "react";
import { ChevronLeft, MessageSquarePlus, Plus, Send, X } from "lucide-react";
import { ApiClientError, apiClient } from "@/lib/api-client";

type ChecklistStep = {
  id: string;
  value: string;
};

const MAX_CHECKLIST_STEPS = 6;

function newChecklistStep(value = ""): ChecklistStep {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return { id: crypto.randomUUID(), value };
  }

  return { id: `step_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`, value };
}

function normalizeRewardAmount(value: string): string | null {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return null;
  }
  return parsed.toFixed(2);
}

export default function GigSuggestPage() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [rewardAmount, setRewardAmount] = useState("3.00");
  const [steps, setSteps] = useState<ChecklistStep[]>([
    newChecklistStep("show the finished job"),
    newChecklistStep("put supplies away")
  ]);
  const [submitting, setSubmitting] = useState(false);
  const [submittedTitle, setSubmittedTitle] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submitSuggestion(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const normalizedRewardAmount = normalizeRewardAmount(rewardAmount);
      const checklist = steps.map((step) => step.value.trim()).filter(Boolean);

      if (!normalizedRewardAmount) {
        setError("Pick a reward greater than zero.");
        return;
      }
      if (checklist.length === 0) {
        setError("Add at least one photo checklist step.");
        return;
      }

      const response = await apiClient.createGigSuggestion({
        title,
        description,
        reward_amount: normalizedRewardAmount,
        currency: "EUR",
        verification_checklist: checklist
      });

      setSubmittedTitle(response.suggestion.title);
      setTitle("");
      setDescription("");
      setRewardAmount("3.00");
      setSteps([newChecklistStep("show the finished job"), newChecklistStep("put supplies away")]);
    } catch (caught) {
      setError(
        caught instanceof ApiClientError
          ? caught.message
          : "Could not send your gig idea. Check the backend and try again."
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
          <p className="text-sm font-bold text-muted-foreground">Kid idea</p>
          <h1 className="text-2xl font-extrabold text-foreground">Suggest a gig</h1>
        </div>
      </header>

      <section className="rounded-3xl bg-petal-blue p-5 shadow-card">
        <span className="grid h-12 w-12 place-items-center rounded-full bg-white/70 text-bloom-green-deep">
          <MessageSquarePlus className="h-6 w-6" />
        </span>
        <h2 className="mt-4 text-xl font-extrabold text-foreground">Ask Mom or Dad for a new way to earn</h2>
        <p className="mt-2 text-sm font-semibold leading-6 text-slate-700">
          Describe the job, pick a fair reward, and add the photo checklist Bloom should verify later.
        </p>
      </section>

      {submittedTitle ? (
        <div className="mt-4 rounded-3xl bg-bloom-green/10 p-4 text-sm font-bold leading-6 text-bloom-green-deep shadow-card">
          Sent for approval: {submittedTitle}. You will see a popup when it becomes a real gig.
        </div>
      ) : null}

      {error ? (
        <div className="mt-4 rounded-3xl border border-bloom-coral/20 bg-bloom-coral/10 p-4 text-sm leading-6 text-slate-700 shadow-card">
          {error}
        </div>
      ) : null}

      <form onSubmit={(event) => void submitSuggestion(event)} className="mt-5 space-y-4">
        <label className="block rounded-3xl bg-card p-4 shadow-card">
          <span className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Gig idea</span>
          <input
            required
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Water the balcony plants"
            className="tap-target mt-2 w-full rounded-2xl border-0 bg-muted px-4 py-3 font-bold outline-none ring-0"
          />
        </label>

        <label className="block rounded-3xl bg-card p-4 shadow-card">
          <span className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
            Why it helps
          </span>
          <textarea
            required
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="I can water the plants after school so they stay healthy."
            rows={4}
            className="mt-2 w-full rounded-2xl border-0 bg-muted px-4 py-3 font-semibold outline-none ring-0"
          />
        </label>

        <label className="block rounded-3xl bg-card p-4 shadow-card">
          <span className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
            Suggested reward
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
            Photo checklist
          </span>
          <div className="mt-3 space-y-2">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center gap-2">
                <input
                  value={step.value}
                  onChange={(event) => {
                    setSteps((current) =>
                      current.map((currentStep) =>
                        currentStep.id === step.id
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
                    onClick={() => setSteps((current) => current.filter((currentStep) => currentStep.id !== step.id))}
                    aria-label={`Remove step ${index + 1}`}
                    className="tap-target grid h-11 w-11 shrink-0 place-items-center rounded-full bg-muted text-muted-foreground"
                  >
                    <X className="h-4 w-4" />
                  </button>
                ) : null}
              </div>
            ))}
          </div>

          {steps.length < MAX_CHECKLIST_STEPS ? (
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
          <Send size={20} />
          {submitting ? "Sending..." : "Send to parent"}
        </button>
      </form>
    </div>
  );
}
