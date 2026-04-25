"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { ChevronLeft, RefreshCcw, Send, Sparkles, Wallet } from "lucide-react";
import { GigIcon, accentBg } from "@/components/bloom/gig-icon";
import { RewardChip } from "@/components/bloom/reward-chip";
import { CameraCapture } from "@/components/camera-capture";
import { VerdictScreen } from "@/components/verdict-screen";
import { ApiClientError, apiClient } from "@/lib/api-client";
import { estimateGigDuration, gigAccent, gigIcon } from "@/lib/gig-presentation";
import type { CompleteGigResponse, Gig } from "@/lib/types";

type FlowStep =
  | "loading"
  | "claim"
  | "before"
  | "after"
  | "submitting"
  | "result"
  | "status";

function stepForGig(gig: Gig): FlowStep {
  if (gig.status === "open") return "claim";
  if (gig.status === "claimed") return "before";
  if (gig.status === "awaiting_after_photo" || gig.status === "rejected") return "after";
  if (gig.status === "verifying") return "submitting";
  if (gig.status === "paid" || gig.status === "payment_failed") return "status";
  return "claim";
}

function createIdempotencyKey(prefix: string, gigId: string): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `${prefix}_${crypto.randomUUID()}`;
  }

  return `${prefix}_${gigId}_${Date.now()}`;
}

export default function GigDetailPage() {
  const params = useParams<{ gigId: string }>();
  const gigId = Array.isArray(params.gigId) ? params.gigId[0] : params.gigId;
  const [gig, setGig] = useState<Gig | null>(null);
  const [step, setStep] = useState<FlowStep>("loading");
  const [beforeImage, setBeforeImage] = useState<string | null>(null);
  const [afterImage, setAfterImage] = useState<string | null>(null);
  const [result, setResult] = useState<CompleteGigResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const completionKeyRef = useRef<string | null>(null);
  const retryPaymentKeyRef = useRef<string | null>(null);
  const [retryPending, setRetryPending] = useState(false);

  useEffect(() => {
    async function loadGig() {
      setError(null);
      setStep("loading");

      try {
        const found = await apiClient.getGig(gigId);
        setGig(found);
        setStep(found ? stepForGig(found) : "claim");
        if (!found) setError("This gig was not found.");
      } catch (caught) {
        setError(
          caught instanceof ApiClientError
            ? caught.message
            : "Could not load this gig. Try again."
        );
      }
    }

    void loadGig();
  }, [gigId]);

  async function claimGig() {
    setError(null);
    try {
      await apiClient.claimGig(gigId);
      setGig((current) => (current ? { ...current, status: "claimed" } : current));
      setStep("before");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not claim this gig.");
    }
  }

  async function submitBeforePhoto() {
    if (!beforeImage) {
      setError("Take a before photo first.");
      return;
    }

    setError(null);
    try {
      await apiClient.uploadBeforePhoto(gigId, { image_base64: beforeImage });
      setGig((current) =>
        current ? { ...current, status: "awaiting_after_photo", before_photo_id: "pending" } : current
      );
      setStep("after");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not save the before photo.");
    }
  }

  async function completeGig() {
    if (!afterImage) {
      setError("Take an after photo first.");
      return;
    }

    setError(null);
    setStep("submitting");

    try {
      if (!completionKeyRef.current) {
        completionKeyRef.current = createIdempotencyKey("completion", gigId);
      }

      const response = await apiClient.completeGig(gigId, {
        after_image_base64: afterImage,
        idempotency_key: completionKeyRef.current
      });
      setGig((current) => (current ? { ...current, status: response.gig.status } : current));
      setResult(response);
      setStep("result");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not complete this gig.");
      setStep("after");
    }
  }

  async function retryPayment() {
    if (!gig) {
      return;
    }

    setError(null);
    setRetryPending(true);

    try {
      if (!retryPaymentKeyRef.current) {
        retryPaymentKeyRef.current = createIdempotencyKey("retry_payment", gig.id);
      }

      const response = await apiClient.retryPayment(gig.id, {
        idempotency_key: retryPaymentKeyRef.current
      });
      setGig((current) => (current ? { ...current, status: response.gig.status } : current));
      setResult(response);
      setStep("result");
      retryPaymentKeyRef.current = null;
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not retry payment.");
    } finally {
      setRetryPending(false);
    }
  }

  function retryWork() {
    setResult(null);
    setAfterImage(null);
    completionKeyRef.current = null;
    setStep("after");
  }

  if (step === "loading") {
    return (
      <div className="px-5 pt-8">
        <div className="rounded-3xl bg-card p-5 text-sm font-bold text-slate-600 shadow-card">
          Loading gig...
        </div>
      </div>
    );
  }

  const accent = gig ? gigAccent(gig) : "green";

  return (
    <div className="space-y-5 px-5 pt-6 pb-8">
      <header className="flex items-center gap-2 pb-1">
        <Link
          href="/gigs"
          aria-label="Back to gigs"
          className="tap-target grid h-10 w-10 place-items-center rounded-full bg-card shadow-card"
        >
          <ChevronLeft className="h-5 w-5 text-foreground" />
        </Link>
        <p className="text-sm font-bold text-muted-foreground">Gig</p>
      </header>

      {gig ? (
        <section className="rounded-3xl bg-card p-4 shadow-card">
          <div className="flex items-start gap-3">
            <div className={`grid h-14 w-14 shrink-0 place-items-center rounded-2xl ${accentBg[accent]}`}>
              <GigIcon kind={gigIcon(gig)} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
                    {gig.status.replaceAll("_", " ")}
                  </p>
                  <h1 className="text-xl font-extrabold leading-tight text-foreground">
                    {gig.title}
                  </h1>
                </div>
                <RewardChip amount={gig.reward_amount} />
              </div>
              <p className="mt-1 text-xs font-semibold text-muted-foreground">
                About {estimateGigDuration(gig)} mins
              </p>
            </div>
          </div>

          <p className="mt-3 text-sm font-semibold text-foreground/80">{gig.description}</p>

          {gig.verification_checklist.length > 0 ? (
            <div className="mt-4 flex flex-wrap gap-2">
              {gig.verification_checklist.map((item) => (
                <span
                  key={item}
                  className="rounded-full bg-bloom-green/10 px-3 py-1 text-xs font-extrabold text-bloom-green-deep"
                >
                  {item}
                </span>
              ))}
            </div>
          ) : null}
        </section>
      ) : null}

      {error ? (
        <div className="rounded-3xl border border-bloom-coral/20 bg-bloom-coral/10 p-4 text-sm leading-6 text-slate-700 shadow-card">
          {error}
        </div>
      ) : null}

      {gig && step !== "claim" && step !== "status" && step !== "result" ? (
        <section className="rounded-3xl bg-card p-4 shadow-card">
          <div className="flex items-center justify-between gap-3 text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
            {[
              "Before",
              "After",
              step === "submitting" ? "Checking" : "Result"
            ].map((label, index) => {
              const active =
                (step === "before" && index === 0) ||
                (step === "after" && index === 1) ||
                (step === "submitting" && index === 2);

              return (
                <div key={label} className="flex flex-1 items-center gap-2">
                  <span
                    className={`grid h-7 w-7 place-items-center rounded-full ${
                      active ? "bg-bloom-green text-white" : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {index + 1}
                  </span>
                  <span>{label}</span>
                </div>
              );
            })}
          </div>
        </section>
      ) : null}

      {step === "claim" ? (
        <button
          type="button"
          onClick={() => void claimGig()}
          className="tap-target flex w-full items-center justify-center gap-2 rounded-full bg-bloom-green px-5 py-4 text-lg font-black text-white shadow-card"
        >
          <Sparkles className="h-5 w-5" />
          Claim this gig
        </button>
      ) : null}

      {step === "before" ? (
        <>
          <CameraCapture
            label="Before photo"
            helper="Show what the task looks like before you start."
            previewBase64={beforeImage}
            onChange={setBeforeImage}
          />
          <button
            type="button"
            onClick={() => void submitBeforePhoto()}
            disabled={!beforeImage}
            className="tap-target w-full rounded-full bg-bloom-green px-5 py-4 text-lg font-black text-white shadow-card disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            Save before photo
          </button>
        </>
      ) : null}

      {step === "after" ? (
        <>
          <div className="rounded-3xl bg-card p-4 text-sm font-semibold text-muted-foreground shadow-card">
            {gig?.before_photo_id
              ? "Before photo saved. Now show the finished result so Bloom can verify it."
              : "Take the finished photo when the gig is done."}
          </div>
          <CameraCapture
            label="After photo"
            helper="Show the finished work. Bloom will check this before payment."
            previewBase64={afterImage}
            onChange={setAfterImage}
          />
          <button
            type="button"
            onClick={() => void completeGig()}
            disabled={!afterImage}
            className="tap-target flex w-full items-center justify-center gap-2 rounded-full bg-bloom-green px-5 py-4 text-lg font-black text-white shadow-card disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            <Send className="h-5 w-5" />
            Check work and pay
          </button>

          {gig?.status === "payment_failed" ? (
            <button
              type="button"
              onClick={() => void retryPayment()}
              disabled={retryPending}
              className="tap-target flex w-full items-center justify-center gap-2 rounded-full bg-card px-5 py-4 text-base font-black text-bloom-green-deep shadow-card disabled:cursor-not-allowed disabled:opacity-60"
            >
              <RefreshCcw className="h-5 w-5" />
              {retryPending ? "Retrying payment..." : "Retry payment only"}
            </button>
          ) : null}
        </>
      ) : null}

      {step === "submitting" ? (
        <section className="rounded-3xl bg-card p-5 shadow-card">
          <div className="mb-4 flex items-center gap-3">
            <span className="grid h-12 w-12 place-items-center rounded-full bg-bloom-green/10 text-bloom-green">
              <Sparkles className="h-6 w-6" />
            </span>
            <div>
              <p className="text-base font-extrabold text-foreground">Checking your work</p>
              <p className="text-xs font-semibold text-muted-foreground">Don’t close this screen</p>
            </div>
          </div>

          <div className="space-y-3">
            <div className="rounded-2xl bg-bloom-green/10 p-3 text-sm font-semibold text-bloom-green-deep">
              1. Bloom compares your before and after photos.
            </div>
            <div className="rounded-2xl bg-petal-blue p-3 text-sm font-semibold text-bloom-green-deep">
              2. If approved, the reward payment is prepared right away.
            </div>
            <div className="rounded-2xl bg-card p-3 text-sm font-semibold text-muted-foreground shadow-card">
              <div className="mb-2 flex items-center gap-2">
                <Wallet className="h-4 w-4 text-bloom-green" />
                Payment is only sent after approval.
              </div>
              This can take a few seconds while the backend verifies photos and talks to the payment adapter.
            </div>
          </div>
        </section>
      ) : null}

      {step === "result" && result ? (
        <VerdictScreen
          result={result}
          rewardAmount={gig?.reward_amount}
          currency={gig?.currency}
          onRetryPayment={result.payment?.status === "failed" ? () => void retryPayment() : undefined}
          onRetryWork={!result.verification.approved ? retryWork : undefined}
          retryPending={retryPending}
        />
      ) : null}

      {step === "status" && gig ? (
        <section className="space-y-4 rounded-3xl bg-card p-5 shadow-card">
          <div
            className={`rounded-[1.5rem] p-4 ${
              gig.status === "paid" ? "bg-bloom-green/10 text-bloom-green-deep" : "bg-bloom-coral/10 text-slate-700"
            }`}
          >
            <p className="text-lg font-black">
              {gig.status === "paid" ? "This gig was already paid" : "Payment still needs a retry"}
            </p>
            <p className="mt-2 text-sm leading-6">
              {gig.status === "paid"
                ? "The earning loop already completed for this gig. You can head back to the board or open another gig."
                : "Bloom already approved this gig. You can retry the payment without taking new photos."}
            </p>
          </div>

          {gig.status === "payment_failed" ? (
            <button
              type="button"
              onClick={() => void retryPayment()}
              disabled={retryPending}
              className="tap-target flex w-full items-center justify-center gap-2 rounded-full bg-bloom-green px-5 py-4 text-base font-black text-white shadow-card disabled:cursor-not-allowed disabled:opacity-60"
            >
              <RefreshCcw className="h-5 w-5" />
              {retryPending ? "Retrying payment..." : "Retry payment"}
            </button>
          ) : null}

          <Link
            href="/gigs"
            className="tap-target flex w-full items-center justify-center rounded-full bg-card px-5 py-4 text-base font-black text-bloom-green-deep shadow-card"
          >
            Back to gigs
          </Link>
        </section>
      ) : null}
    </div>
  );
}
