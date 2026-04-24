"use client";

import { BottomNav } from "@/components/bottom-nav";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto flex min-h-screen w-full max-w-[430px] flex-col px-4">
      <main className="flex-1 pb-28 pt-5">{children}</main>
      <BottomNav />
    </div>
  );
}
