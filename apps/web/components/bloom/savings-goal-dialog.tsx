"use client";

import { useEffect, useId, useState } from "react";
import { Target, X } from "lucide-react";

const QUICK_PICKS = ["Lego set", "New game", "Bike", "Headphones", "Concert ticket"];

export function SavingsGoalDialog({
  open,
  onOpenChange,
  initialLabel,
  initialAmount,
  onSave
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initialLabel: string;
  initialAmount: string;
  onSave: (goal: { label: string; amount: string }) => void;
}) {
  const labelId = useId();
  const amountId = useId();
  const [label, setLabel] = useState(initialLabel);
  const [amount, setAmount] = useState(initialAmount);

  useEffect(() => {
    if (!open) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onOpenChange(false);
      }
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [onOpenChange, open]);

  const parsedAmount = Math.round(Number(amount) * 100) / 100;
  const canSave = label.trim().length > 0 && Number.isFinite(parsedAmount) && parsedAmount > 0;

  return (
    <div
      aria-hidden={!open}
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-opacity duration-300 ${
        open ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0"
      }`}
    >
      <button
        type="button"
        aria-label="Close savings goal dialog"
        onClick={() => onOpenChange(false)}
        className={`absolute inset-0 bg-slate-950/55 transition-opacity duration-300 ${
          open ? "opacity-100" : "opacity-0"
        }`}
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={`${labelId}-title`}
        className={`relative w-full max-w-[496px] rounded-[36px] bg-white px-7 pb-8 pt-9 shadow-[0_30px_80px_rgba(17,24,39,0.28)] transition-all duration-300 ease-out ${
          open ? "translate-y-0 scale-100 opacity-100" : "translate-y-6 scale-95 opacity-0"
        }`}
      >
        <button
          type="button"
          aria-label="Close dialog"
          onClick={() => onOpenChange(false)}
          className="absolute right-6 top-6 tap-target rounded-full text-slate-500 transition-colors hover:text-slate-700"
        >
          <X className="h-6 w-6" />
        </button>

        <div className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-petal-yellow text-bloom-green-deep">
          <Target className="h-8 w-8" strokeWidth={2.2} />
        </div>

        <div className="mt-4 text-center">
          <h2 id={`${labelId}-title`} className="text-[18px] font-extrabold text-foreground">
            Set a savings goal
          </h2>
          <p className="mt-3 text-[15px] font-medium leading-6 text-muted-foreground">
            Pick something you&apos;re saving up for and how much it costs.
          </p>
        </div>

        <div className="mt-10 space-y-8">
          <div>
            <label
              htmlFor={labelId}
              className="text-[12px] font-extrabold uppercase tracking-[0.08em] text-foreground"
            >
              What are you saving for?
            </label>
            <input
              id={labelId}
              value={label}
              onChange={(event) => setLabel(event.target.value)}
              placeholder="e.g. Lego set"
              maxLength={40}
              className="mt-3 h-16 w-full rounded-[22px] border-2 border-bloom-green/70 bg-white px-5 text-[18px] font-medium text-foreground shadow-[inset_0_0_0_3px_rgba(255,255,255,0.85)] outline-none transition focus:border-bloom-green"
            />
            <div className="mt-3 flex flex-wrap gap-2">
              {QUICK_PICKS.map((pick) => (
                <button
                  key={pick}
                  type="button"
                  onClick={() => setLabel(pick)}
                  className="tap-target rounded-full bg-muted px-4 py-2 text-[12px] font-extrabold text-muted-foreground transition-colors active:bg-bloom-green/10"
                >
                  {pick}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label
              htmlFor={amountId}
              className="text-[12px] font-extrabold uppercase tracking-[0.08em] text-foreground"
            >
              How much does it cost?
            </label>
            <div className="relative mt-3">
              <span className="pointer-events-none absolute left-5 top-1/2 -translate-y-1/2 text-[18px] font-extrabold text-muted-foreground">
                EUR
              </span>
              <input
                id={amountId}
                type="number"
                inputMode="decimal"
                min={1}
                step="0.01"
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
                placeholder="45"
                className="h-14 w-full rounded-[18px] border border-slate-200 bg-white pl-16 pr-5 text-[18px] font-medium text-foreground outline-none transition focus:border-bloom-green focus:ring-2 focus:ring-bloom-green/15"
              />
            </div>
          </div>
        </div>

        <div className="mt-10 flex gap-3">
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            className="tap-target flex h-14 flex-1 items-center justify-center rounded-full bg-muted text-[16px] font-extrabold text-muted-foreground transition active:scale-[0.98]"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={!canSave}
            onClick={() => {
              if (!canSave) {
                return;
              }

              onSave({ label: label.trim(), amount: parsedAmount.toFixed(2) });
              onOpenChange(false);
            }}
            className="tap-target flex h-14 flex-1 items-center justify-center rounded-full bg-bloom-green text-[16px] font-extrabold text-white shadow-card transition active:scale-[0.98] disabled:opacity-50"
          >
            Save goal
          </button>
        </div>
      </div>
    </div>
  );
}