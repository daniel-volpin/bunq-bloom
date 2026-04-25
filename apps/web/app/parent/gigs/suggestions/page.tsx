"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, ChevronLeft, Inbox, RefreshCcw, Sparkles } from "lucide-react";
import { ApiClientError, apiClient } from "@/lib/api-client";
import type { GigSuggestion } from "@/lib/types";

export default function ParentGigSuggestionsPage() {
  const [suggestions, setSuggestions] = useState<GigSuggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [approvingId, setApprovingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [approvedTitle, setApprovedTitle] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const pendingSuggestions = useMemo(
    () => suggestions.filter((suggestion) => suggestion.status === "pending"),
    [suggestions]
  );

  useEffect(() => {
    let active = true;

    void apiClient.listGigSuggestions().then(
      (response) => {
        if (!active) {
          return;
        }
        setError(null);
        setSuggestions(response.suggestions);
        setLoading(false);
      },
      (caught) => {
        if (!active) {
          return;
        }
        setError(caught instanceof ApiClientError ? caught.message : "Could not load gig ideas.");
        setLoading(false);
      }
    );

    return () => {
      active = false;
    };
  }, [reloadKey]);

  function reload() {
    setLoading(true);
    setError(null);
    setReloadKey((current) => current + 1);
  }

  async function approveSuggestion(suggestion: GigSuggestion) {
    setApprovingId(suggestion.id);
    setError(null);
    setApprovedTitle(null);

    try {
      const response = await apiClient.approveGigSuggestion(suggestion.id);
      setApprovedTitle(response.gig.title);
      reload();
    } catch (caught) {
      setError(caught instanceof ApiClientError ? caught.message : "Could not approve that gig idea.");
    } finally {
      setApprovingId(null);
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
        <div className="min-w-0 flex-1">
          <p className="text-sm font-bold text-muted-foreground">Parent</p>
          <h1 className="text-2xl font-extrabold text-foreground">Kid gig ideas</h1>
        </div>
        <button
          type="button"
          onClick={reload}
          className="tap-target grid h-10 w-10 place-items-center rounded-full bg-card text-bloom-green-deep shadow-card"
          aria-label="Refresh suggestions"
        >
          <RefreshCcw className="h-4 w-4" />
        </button>
      </header>

      <section className="rounded-3xl bg-card p-5 shadow-card">
        <span className="grid h-12 w-12 place-items-center rounded-full bg-petal-green text-bloom-green-deep">
          <Inbox className="h-6 w-6" />
        </span>
        <h2 className="mt-4 text-xl font-extrabold text-foreground">Approve ideas into real gigs</h2>
        <p className="mt-2 text-sm font-semibold leading-6 text-muted-foreground">
          Approval creates a normal open gig and sends the kid an in-app popup.
        </p>
      </section>

      {approvedTitle ? (
        <div className="mt-4 rounded-3xl bg-bloom-green/10 p-4 text-sm font-bold leading-6 text-bloom-green-deep shadow-card">
          Approved: {approvedTitle}. The kid can now start it from their notification.
        </div>
      ) : null}

      {error ? (
        <div className="mt-4 rounded-3xl border border-bloom-coral/20 bg-bloom-coral/10 p-4 text-sm leading-6 text-slate-700 shadow-card">
          {error}
        </div>
      ) : null}

      {loading ? (
        <div className="mt-5 rounded-3xl bg-card p-5 text-sm font-bold text-slate-600 shadow-card">
          Loading kid ideas...
        </div>
      ) : null}

      <div className="mt-5 space-y-3">
        {!loading && pendingSuggestions.length === 0 ? (
          <div className="flex flex-col items-center gap-2 rounded-3xl bg-card p-8 text-center shadow-card">
            <Sparkles className="h-8 w-8 text-bloom-green" />
            <p className="text-sm font-extrabold text-foreground">No pending ideas</p>
            <p className="text-xs font-semibold leading-5 text-muted-foreground">
              Suggestions from the kid form will appear here before they become real gigs.
            </p>
          </div>
        ) : null}

        {pendingSuggestions.map((suggestion) => (
          <article key={suggestion.id} className="rounded-3xl bg-card p-5 shadow-card">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.16em] text-bloom-green-deep/60">
                  Kid suggestion
                </p>
                <h2 className="mt-1 text-xl font-extrabold leading-tight text-foreground">
                  {suggestion.title}
                </h2>
              </div>
              <span className="rounded-full bg-bloom-green/10 px-3 py-1 text-sm font-black text-bloom-green-deep">
                €{suggestion.reward_amount}
              </span>
            </div>
            <p className="mt-3 text-sm font-semibold leading-6 text-muted-foreground">
              {suggestion.description}
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              {suggestion.verification_checklist.map((step) => (
                <span
                  key={step}
                  className="rounded-full bg-muted px-3 py-1 text-xs font-bold text-slate-600"
                >
                  {step}
                </span>
              ))}
            </div>
            <button
              type="button"
              disabled={approvingId === suggestion.id}
              onClick={() => void approveSuggestion(suggestion)}
              className="tap-target mt-5 inline-flex w-full items-center justify-center gap-2 rounded-full bg-bloom-green px-4 py-3 font-black text-white shadow-card disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              <CheckCircle2 className="h-5 w-5" />
              {approvingId === suggestion.id ? "Approving..." : "Approve and notify kid"}
            </button>
          </article>
        ))}
      </div>
    </div>
  );
}
