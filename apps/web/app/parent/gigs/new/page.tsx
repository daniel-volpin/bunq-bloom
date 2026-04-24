"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus } from "lucide-react";
import { ApiClientError, apiClient } from "@/lib/api-client";

export default function NewGigPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [rewardAmount, setRewardAmount] = useState("5.00");
  const [checklistText, setChecklistText] = useState("bed made\nfloor clear\ndesk tidy");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submitGig(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const checklist = checklistText
        .split("\n")
        .map((item) => item.trim())
        .filter(Boolean);

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
    <div className="space-y-5">
      <header className="rounded-[2rem] bg-white/90 p-5 shadow-bloom">
        <p className="text-sm font-black uppercase tracking-wide text-bloom-leaf">Parent</p>
        <h1 className="mt-2 text-3xl font-black leading-tight">Create a gig</h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          Keep it clear: what needs doing, what Bloom should check, and what it pays.
        </p>
      </header>

      {error ? (
        <div className="rounded-[1.5rem] border border-bloom-coral/30 bg-bloom-coral/10 p-4 text-sm leading-6 text-red-900">
          {error}
        </div>
      ) : null}

      <form onSubmit={(event) => void submitGig(event)} className="space-y-4">
        <label className="block rounded-[1.5rem] bg-white/90 p-4 shadow">
          <span className="text-sm font-black uppercase tracking-wide text-slate-500">Title</span>
          <input
            required
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Clean your room"
            className="tap-target mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-bloom-sky"
          />
        </label>

        <label className="block rounded-[1.5rem] bg-white/90 p-4 shadow">
          <span className="text-sm font-black uppercase tracking-wide text-slate-500">
            Description
          </span>
          <textarea
            required
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Make the bed, clear the floor, and tidy the desk."
            rows={4}
            className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-bloom-sky"
          />
        </label>

        <label className="block rounded-[1.5rem] bg-white/90 p-4 shadow">
          <span className="text-sm font-black uppercase tracking-wide text-slate-500">
            Reward in EUR
          </span>
          <input
            required
            inputMode="decimal"
            value={rewardAmount}
            onChange={(event) => setRewardAmount(event.target.value)}
            className="tap-target mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-bloom-sky"
          />
        </label>

        <label className="block rounded-[1.5rem] bg-white/90 p-4 shadow">
          <span className="text-sm font-black uppercase tracking-wide text-slate-500">
            Checklist
          </span>
          <textarea
            value={checklistText}
            onChange={(event) => setChecklistText(event.target.value)}
            rows={4}
            className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-bloom-sky"
          />
          <span className="mt-2 block text-xs font-bold text-slate-500">One check per line.</span>
        </label>

        <button
          type="submit"
          disabled={submitting}
          className="tap-target inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-bloom-ink px-5 py-4 text-lg font-black text-white shadow-bloom disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          <Plus size={20} />
          {submitting ? "Creating..." : "Create gig"}
        </button>
      </form>
    </div>
  );
}
