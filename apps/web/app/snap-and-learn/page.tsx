"use client";

import Link from "next/link";
import { useState } from "react";
import { ChevronLeft, Search, Sparkles } from "lucide-react";
import { CameraCapture } from "@/components/camera-capture";
import { SnapAndLearnResult } from "@/components/bloom/snap-and-learn-result";
import { ApiClientError, apiClient } from "@/lib/api-client";
import { useBloomSummary } from "@/lib/use-bloom-summary";
import type { SnapAndLearnResponse } from "@/lib/types";

export default function SnapAndLearnPage() {
  const { report, reportLoading } = useBloomSummary();
  const [imageBase64, setImageBase64] = useState<string | null>(null);
  const [result, setResult] = useState<SnapAndLearnResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  async function analyzeItem() {
    if (!imageBase64) {
      setError("Take a photo first.");
      return;
    }

    setError(null);
    setIsAnalyzing(true);

    try {
      const response = await apiClient.analyzeSnap({ image_base64: imageBase64 });
      setResult(response);
    } catch (caught) {
      setError(
        caught instanceof ApiClientError
          ? caught.message
          : "Bloom could not analyze that item. Try another photo."
      );
    } finally {
      setIsAnalyzing(false);
    }
  }

  function resetFlow() {
    setImageBase64(null);
    setResult(null);
    setError(null);
  }

  return (
    <div className="space-y-5 px-5 pt-6 pb-8">
      <header className="flex items-center gap-2 pb-1">
        <Link
          href="/wallet"
          aria-label="Back to wallet"
          className="tap-target grid h-10 w-10 place-items-center rounded-full bg-card shadow-card"
        >
          <ChevronLeft className="h-5 w-5 text-foreground" />
        </Link>
        <p className="text-sm font-bold text-muted-foreground">Snap & Learn</p>
      </header>

      <section className="rounded-3xl bg-card p-5 shadow-card">
        <div className="mb-3 flex items-center gap-3">
          <span className="grid h-12 w-12 place-items-center rounded-full bg-bloom-blue/10 text-bloom-blue">
            <Search className="h-6 w-6" />
          </span>
          <div>
            <h1 className="text-2xl font-extrabold text-foreground">Snap something you want</h1>
            <p className="text-sm font-semibold leading-6 text-muted-foreground">
              Bloom will estimate the price, compare it with your balance, and turn it into a savings goal.
            </p>
          </div>
        </div>

        <div className="rounded-2xl bg-bloom-sky/10 p-4 text-sm leading-6 text-slate-700">
          One clear step: take a photo of a toy, book, game, or gadget you want to save for.
        </div>
      </section>

      {error ? (
        <div className="rounded-3xl border border-bloom-coral/20 bg-bloom-coral/10 p-4 text-sm leading-6 text-slate-700 shadow-card">
          {error}
        </div>
      ) : null}

      {!result ? (
        <>
          <CameraCapture
            label="Item photo"
            helper="Show the item clearly so Bloom can estimate what it is and what it might cost."
            previewBase64={imageBase64}
            onChange={(nextImage) => {
              setImageBase64(nextImage);
              setError(null);
            }}
          />

          <button
            type="button"
            onClick={() => void analyzeItem()}
            disabled={!imageBase64 || isAnalyzing}
            className="tap-target flex w-full items-center justify-center gap-2 rounded-full bg-bloom-green px-5 py-4 text-lg font-black text-white shadow-card disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            <Sparkles className="h-5 w-5" />
            {isAnalyzing ? "Looking at your item..." : "Analyze item"}
          </button>

          {isAnalyzing ? (
            <section className="rounded-3xl bg-card p-5 shadow-card">
              <div className="mb-4 flex items-center gap-3">
                <span className="grid h-12 w-12 place-items-center rounded-full bg-bloom-green/10 text-bloom-green">
                  <Sparkles className="h-6 w-6" />
                </span>
                <div>
                  <p className="text-base font-extrabold text-foreground">Building a savings idea</p>
                  <p className="text-xs font-semibold text-muted-foreground">Bloom is estimating the item and checking your balance</p>
                </div>
              </div>
              <div className="space-y-3">
                <div className="rounded-2xl bg-bloom-green/10 p-3 text-sm font-semibold text-bloom-green-deep">
                  1. Bloom looks at the photo and guesses the item.
                </div>
                <div className="rounded-2xl bg-petal-blue p-3 text-sm font-semibold text-bloom-green-deep">
                  2. Bloom compares the estimate with your current balance.
                </div>
                <div className="rounded-2xl bg-card p-3 text-sm font-semibold text-muted-foreground shadow-card">
                  3. You get a simple goal in gigs, not a confusing money chart.
                </div>
              </div>
            </section>
          ) : null}
        </>
      ) : (
        <SnapAndLearnResult
          result={result}
          report={report}
          reportLoading={reportLoading}
          onTryAnother={resetFlow}
        />
      )}
    </div>
  );
}