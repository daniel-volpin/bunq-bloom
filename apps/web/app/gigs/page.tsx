"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { RefreshCw } from "lucide-react";
import { GigCard } from "@/components/gig-card";
import { ApiClientError, apiClient } from "@/lib/api-client";
import type { Gig } from "@/lib/types";

export default function GigsPage() {
  const [gigs, setGigs] = useState<Gig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadGigs(options?: { resetState?: boolean }) {
    if (options?.resetState ?? true) {
      setLoading(true);
      setError(null);
    }

    try {
      const response = await apiClient.listGigs();
      setGigs(response.gigs);
    } catch (caught) {
      setError(
        caught instanceof ApiClientError
          ? caught.message
          : "Could not reach the Bloom API. Start the backend or try again."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;

    async function loadInitialGigs() {
      try {
        const response = await apiClient.listGigs();
        if (!active) {
          return;
        }
        setGigs(response.gigs);
      } catch (caught) {
        if (!active) {
          return;
        }
        setError(
          caught instanceof ApiClientError
            ? caught.message
            : "Could not reach the Bloom API. Start the backend or try again."
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadInitialGigs();

    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="space-y-5">
      <header className="rounded-[2rem] bg-bloom-ink p-5 text-white shadow-bloom">
        <p className="text-sm font-bold uppercase tracking-[0.2em] text-bloom-sun">bunq Bloom</p>
        <h1 className="mt-2 text-4xl font-black leading-none">Pick a gig. Earn money.</h1>
        <p className="mt-3 text-sm leading-6 text-white/80">
          Take before and after photos so Bloom can check the work and pay the reward.
        </p>
      </header>

      <div className="flex items-center justify-between">
        <h2 className="text-xl font-black">Available gigs</h2>
        <button
          type="button"
          onClick={() => void loadGigs()}
          className="tap-target inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-black shadow"
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="rounded-[1.5rem] bg-white/80 p-5 text-sm font-bold text-slate-600">
          Loading gigs...
        </div>
      ) : null}

      {error ? (
        <div className="rounded-[1.5rem] border border-bloom-coral/30 bg-bloom-coral/10 p-5 text-sm leading-6 text-red-900">
          {error}
        </div>
      ) : null}

      {!loading && !error && gigs.length === 0 ? (
        <div className="rounded-[1.5rem] bg-white/80 p-5 text-sm leading-6 text-slate-600">
          No gigs yet.{" "}
          <Link href="/parent/gigs/new" className="font-black text-bloom-sky">
            Create one
          </Link>
          .
        </div>
      ) : null}

      <div className="space-y-4">
        {gigs.map((gig) => (
          <GigCard key={gig.id} gig={gig} />
        ))}
      </div>
    </div>
  );
}
