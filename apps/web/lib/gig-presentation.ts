import type { Gig, GigStatus } from "@/lib/types";

export type GigAccent = "green" | "blue" | "yellow" | "coral";
export type GigIconKind = "dog" | "plant" | "box" | "book" | "sparkle" | "trophy";
export type GigBucket = "available" | "in-progress" | "done";

function parseAmount(value: string | number): number {
  if (typeof value === "number") {
    return value;
  }

  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function formatEuro(value: string | number): string {
  return new Intl.NumberFormat("en-NL", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(parseAmount(value));
}

export function estimateGigDuration(gig: Gig): number {
  const checklistWeight = Math.max(gig.verification_checklist.length, 1);
  const raw = 8 + checklistWeight * 6;
  return Math.max(10, Math.round(raw / 5) * 5);
}

export function gigBucket(status: GigStatus): GigBucket {
  if (status === "open") {
    return "available";
  }

  if (status === "paid") {
    return "done";
  }

  return "in-progress";
}

export function nextGigActionLabel(status: GigStatus): string {
  switch (status) {
    case "open":
      return "Claim gig";
    case "claimed":
      return "Take before photo";
    case "awaiting_after_photo":
      return "Take after photo";
    case "verifying":
      return "Bloom is checking";
    case "rejected":
      return "Try another photo";
    case "payment_failed":
      return "Retry payment";
    case "paid":
      return "View result";
    default:
      return "Open gig";
  }
}

export function statusLabel(status: GigStatus): string {
  return status.replaceAll("_", " ");
}

export function gigAccent(gig: Gig): GigAccent {
  const text = `${gig.title} ${gig.description}`.toLowerCase();

  if (/(dog|pet|walk)/.test(text)) {
    return "green";
  }

  if (/(plant|water|garden|flower)/.test(text)) {
    return "blue";
  }

  if (/(learn|study|read|homework|school)/.test(text)) {
    return "yellow";
  }

  const palette: GigAccent[] = ["green", "blue", "yellow", "coral"];
  const hash = [...gig.id].reduce((sum, char) => sum + char.charCodeAt(0), 0);
  return palette[hash % palette.length];
}

export function gigIcon(gig: Gig): GigIconKind {
  const text = `${gig.title} ${gig.description}`.toLowerCase();

  if (gig.status === "paid") {
    return "trophy";
  }

  if (/(dog|pet|walk)/.test(text)) {
    return "dog";
  }

  if (/(plant|water|garden|flower)/.test(text)) {
    return "plant";
  }

  if (/(learn|study|read|homework|school)/.test(text)) {
    return "book";
  }

  if (/(clean|tidy|room|desk|laundry|box|organi)/.test(text)) {
    return "box";
  }

  return "sparkle";
}