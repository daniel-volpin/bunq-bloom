"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { CameraCapture } from "@/components/camera-capture";
import { VerdictScreen } from "@/components/verdict-screen";
import { ApiClientError, apiClient } from "@/lib/api-client";
import type { CompleteGigResponse, Gig } from "@/lib/types";

type FlowStep = "loading" | "claim" | "before" | "after" | "submitting" | "result";

function stepForGig(gig: Gig): FlowStep {
  if (gig.status === "open") return "claim";
  if (gig.status === "claimed") return "before";
  if (gig.status === "awaiting_after_photo" || gig.status === "rejected") return "after";
  if (gig.status === "paid" || gig.status === "payment_failed") return "after";
  return "claim";
}

export default function GigDetailPage() {
  const params = useParams<{ gigId: string }>();
  const gigId = params.gigId;
  const [gig, setGig] = useState<Gig | null>(null);
  const [step, setStep] = useState<FlowStep>("loading");
  const [beforeImage, setBeforeImage] = useState<string | null>(null);
  const [afterImage, setAfterImage] = useState<string | null>(null);
  const [result, setResult] = useState<CompleteGigResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const idempotencyKeyRef = useRef<string | null>(null);

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
      if (!idempotencyKeyRef.current) {
        idempotencyKeyRef.current =
          typeof crypto !== "undefined" && "randomUUID" in crypto
            ? `completion_${crypto.randomUUID()}`
            : `completion_${gigId}`;
      }

      const response = await apiClient.completeGig(gigId, {
        after_image_base64: afterImage,
        idempotency_key: idempotencyKeyRef.current
      });
      setResult(response);
      setStep("result");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not complete this gig.");
      setStep("after");
    }
  }

  if (step === "loading") {
    return <div className="rounded-[1.5rem] bg-white/80 p-5 font-bold">Loading gig...</div>;
  }

  return (
    <div className="space-y-5">
      {gig ? (
        <header className="rounded-[2rem] bg-white/90 p-5 shadow-bloom">
          <p className="text-sm font-black uppercase tracking-wide text-bloom-sky">
            {gig.status.replaceAll("_", " ")}
          </p>
          <h1 className="mt-2 text-3xl font-black leading-tight">{gig.title}</h1>
          <p className="mt-3 text-sm leading-6 text-slate-600">{gig.description}</p>
          <p className="mt-4 inline-flex rounded-2xl bg-bloom-leaf px-4 py-2 font-black text-white">
            Earn {gig.reward_amount} {gig.currency}
          </p>
        </header>
      ) : null}

      {error ? (
        <div className="rounded-[1.5rem] border border-bloom-coral/30 bg-bloom-coral/10 p-4 text-sm leading-6 text-red-900">
          {error}
        </div>
      ) : null}

      {gig?.verification_checklist.length ? (
        <section className="rounded-[1.5rem] bg-white/80 p-4">
          <h2 className="text-sm font-black uppercase tracking-wide text-slate-500">
            Bloom will check
          </h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {gig.verification_checklist.map((item) => (
              <span key={item} className="rounded-full bg-bloom-sun/30 px-3 py-1 text-sm font-bold">
                {item}
              </span>
            ))}
          </div>
        </section>
      ) : null}

      {step === "claim" ? (
        <button
          type="button"
          onClick={() => void claimGig()}
          className="tap-target w-full rounded-2xl bg-bloom-ink px-5 py-4 text-lg font-black text-white shadow-bloom"
        >
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
            className="tap-target w-full rounded-2xl bg-bloom-ink px-5 py-4 text-lg font-black text-white shadow-bloom disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            Save before photo
          </button>
        </>
      ) : null}

      {step === "after" ? (
        <>
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
            className="tap-target w-full rounded-2xl bg-bloom-leaf px-5 py-4 text-lg font-black text-white shadow-bloom disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            Check work and pay
          </button>
        </>
      ) : null}

      {step === "submitting" ? (
        <section className="rounded-[2rem] bg-white/95 p-6 text-center shadow-bloom">
          <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-bloom-sky/20 border-t-bloom-sky" />
          <h2 className="text-2xl font-black">Bloom is checking...</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            First verification, then payment if the gig is approved.
          </p>
        </section>
      ) : null}

      {step === "result" && result ? (
        <VerdictScreen result={result} rewardAmount={gig?.reward_amount} currency={gig?.currency} />
      ) : null}
    </div>
  );
}
