"use client";

import Link from "next/link";
import { CheckCircle2, X } from "lucide-react";
import type { KidNotification } from "@/lib/types";

export function KidApprovalNotification({
  notification,
  onDismiss
}: {
  notification: KidNotification;
  onDismiss: (notificationId: string) => void;
}) {
  return (
    <section className="px-5 pt-3">
      <div className="relative overflow-hidden rounded-[2rem] bg-bloom-green p-4 text-white shadow-card">
        <div className="absolute -right-8 -top-8 h-24 w-24 rounded-full bg-white/15" />
        <div className="relative flex items-start gap-3">
          <span className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-white/20">
            <CheckCircle2 className="h-6 w-6" />
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-black uppercase tracking-[0.16em] text-white/75">Parent approved</p>
            <h2 className="mt-1 text-lg font-black leading-tight">{notification.title}</h2>
            <p className="mt-1 text-sm font-semibold leading-5 text-white/90">{notification.message}</p>
            {notification.gig_id ? (
              <Link
                href={`/gigs/${notification.gig_id}`}
                className="tap-target mt-3 inline-flex items-center rounded-full bg-white px-4 py-2 text-sm font-black text-bloom-green-deep"
              >
                Start the gig
              </Link>
            ) : null}
          </div>
          <button
            type="button"
            onClick={() => onDismiss(notification.id)}
            aria-label="Dismiss notification"
            className="tap-target grid h-10 w-10 shrink-0 place-items-center rounded-full bg-white/15 text-white"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    </section>
  );
}
