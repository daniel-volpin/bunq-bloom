"use client";

import Image from "next/image";
import { Camera, RotateCcw } from "lucide-react";
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
            onClick={() => onChange(null)}
            className="tap-target inline-flex w-full items-center justify-center gap-2 rounded-2xl border-2 border-bloom-ink/10 bg-white px-4 py-3 font-black text-bloom-ink"
          >
            <RotateCcw size={18} />
            Retake photo
          </button>
        </div>
      ) : (
        <label className="tap-target flex cursor-pointer flex-col items-center justify-center rounded-[1.5rem] border-2 border-dashed border-bloom-sky/40 bg-bloom-sky/10 px-4 py-8 text-center text-bloom-ink">
          <Camera size={34} strokeWidth={2.5} />
          <span className="mt-3 text-base font-black">Open camera or choose photo</span>
          <span className="mt-1 text-xs font-bold text-slate-500">JPEG, PNG, WebP up to 8 MB</span>
          <input
            className="sr-only"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            capture="environment"
            onChange={handleFileChange}
          />
        </label>
      )}
    </section>
  );
}
