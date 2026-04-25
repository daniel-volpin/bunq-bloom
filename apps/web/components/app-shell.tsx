"use client";

import { BottomNav } from "@/components/bottom-nav";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto min-h-screen w-full max-w-[390px] px-0">
      <main className="min-h-screen pb-32">{children}</main>
      <BottomNav />
    </div>
  );
}
