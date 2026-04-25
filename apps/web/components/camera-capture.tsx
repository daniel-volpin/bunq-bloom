"use client";

import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { Camera, ImagePlus, RotateCcw, X } from "lucide-react";
import { fileToBase64, validateImageFile } from "@/lib/images";

type CameraCaptureProps = {
  label: string;
  helper: string;
  previewBase64: string | null;
  onChange: (imageBase64: string | null) => void;
};

export function CameraCapture({
  label,
  helper,
  previewBase64,
  onChange
}: CameraCaptureProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [isStartingCamera, setIsStartingCamera] = useState(false);

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  useEffect(() => {
    const video = videoRef.current;
    const stream = streamRef.current;

    if (!isCameraOpen || !video || !stream) {
      return;
    }

    video.srcObject = stream;
    void video.play().catch(() => {
      setCameraError("Camera preview could not start. You can still choose a photo instead.");
    });

    return () => {
      if (video.srcObject === stream) {
        video.srcObject = null;
      }
    };
  }, [isCameraOpen]);

  function stopCamera() {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsCameraOpen(false);
    setIsStartingCamera(false);
  }

  async function startCamera() {
    if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      setCameraError("This browser cannot open the camera here. Choose a photo instead.");
      return;
    }

    setCameraError(null);
    setIsStartingCamera(true);

    try {
      stopCamera();

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: "environment" }
        },
        audio: false
      });

      streamRef.current = stream;
      setIsCameraOpen(true);
      setIsStartingCamera(false);
    } catch {
      setCameraError("Camera access was blocked. You can still choose a photo from your device.");
      setIsStartingCamera(false);
      stopCamera();
    }
  }

  async function capturePhoto() {
    const video = videoRef.current;
    if (!video || video.videoWidth === 0 || video.videoHeight === 0) {
      setCameraError("The camera is not ready yet. Try again in a second.");
      return;
    }

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const context = canvas.getContext("2d");
    if (!context) {
      setCameraError("Could not capture that photo. Try again.");
      return;
    }

    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const blob = await new Promise<Blob | null>((resolve) => {
      canvas.toBlob(resolve, "image/jpeg", 0.92);
    });

    if (!blob) {
      setCameraError("Could not capture that photo. Try again.");
      return;
    }

    const file = new File([blob], `${label.toLowerCase().replace(/\s+/g, "-")}.jpg`, {
      type: "image/jpeg"
    });

    const validationMessage = validateImageFile(file);
    if (validationMessage) {
      setCameraError(validationMessage);
      return;
    }

    const base64 = await fileToBase64(file);
    onChange(base64);
    stopCamera();
  }

  function openPhotoLibrary() {
    fileInputRef.current?.click();
  }

  async function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    const validationMessage = validateImageFile(file);
    if (validationMessage) {
      window.alert(validationMessage);
      event.target.value = "";
      return;
    }

    const base64 = await fileToBase64(file);
    setCameraError(null);
    onChange(base64);
  }

  return (
    <section className="rounded-[2rem] border border-white/70 bg-white/90 p-4 shadow-bloom">
      <div className="mb-4">
        <h2 className="text-lg font-black text-bloom-ink">{label}</h2>
        <p className="mt-1 text-sm leading-6 text-slate-600">{helper}</p>
      </div>

      {previewBase64 ? (
        <div className="space-y-3">
          <div className="relative aspect-[4/3] overflow-hidden rounded-[1.5rem] bg-slate-100">
            <Image
              src={previewBase64}
              alt={`${label} preview`}
              fill
              className="object-cover"
              unoptimized
            />
          </div>
          <button
            type="button"
            onClick={() => {
              onChange(null);
              setCameraError(null);
            }}
            className="tap-target inline-flex w-full items-center justify-center gap-2 rounded-2xl border-2 border-bloom-ink/10 bg-white px-4 py-3 font-black text-bloom-ink"
          >
            <RotateCcw size={18} />
            Retake photo
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="rounded-[1.5rem] border-2 border-dashed border-bloom-sky/40 bg-bloom-sky/10 px-4 py-6 text-center text-bloom-ink">
            {isCameraOpen ? (
              <div className="space-y-3">
                <div className="relative aspect-[4/3] overflow-hidden rounded-[1.25rem] bg-slate-950">
                  <video
                    ref={videoRef}
                    className="h-full w-full object-cover"
                    autoPlay
                    muted
                    playsInline
                  />
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <button
                    type="button"
                    onClick={() => void capturePhoto()}
                    className="tap-target inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-bloom-green px-4 py-3 font-black text-white"
                  >
                    <Camera size={18} />
                    Take photo
                  </button>
                  <button
                    type="button"
                    onClick={stopCamera}
                    className="tap-target inline-flex w-full items-center justify-center gap-2 rounded-2xl border-2 border-bloom-ink/10 bg-white px-4 py-3 font-black text-bloom-ink"
                  >
                    <X size={18} />
                    Close camera
                  </button>
                </div>
              </div>
            ) : (
              <>
                <Camera size={34} strokeWidth={2.5} className="mx-auto" />
                <span className="mt-3 block text-base font-black">Open camera first</span>
                <span className="mt-1 block text-xs font-bold text-slate-500">
                  Use the live camera here or pick a saved photo.
                </span>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <button
                    type="button"
                    onClick={() => void startCamera()}
                    disabled={isStartingCamera}
                    className="tap-target inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-bloom-green px-4 py-3 font-black text-white disabled:cursor-not-allowed disabled:bg-slate-300"
                  >
                    <Camera size={18} />
                    {isStartingCamera ? "Opening camera..." : "Open camera"}
                  </button>
                  <button
                    type="button"
                    onClick={openPhotoLibrary}
                    className="tap-target inline-flex w-full items-center justify-center gap-2 rounded-2xl border-2 border-bloom-ink/10 bg-white px-4 py-3 font-black text-bloom-ink"
                  >
                    <ImagePlus size={18} />
                    Choose photo
                  </button>
                </div>
              </>
            )}
          </div>

          {cameraError ? (
            <p className="rounded-2xl border border-bloom-coral/20 bg-bloom-coral/10 px-4 py-3 text-sm font-semibold text-slate-700">
              {cameraError}
            </p>
          ) : null}

          <input
            ref={fileInputRef}
            className="sr-only"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            capture="environment"
            onChange={handleFileChange}
          />
        </div>
      )}
    </section>
  );
}
