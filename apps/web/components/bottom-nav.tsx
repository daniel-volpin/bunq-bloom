"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ClipboardList, Home, PlusCircle } from "lucide-react";

const items = [
  { href: "/", label: "Home", icon: Home },
  { href: "/gigs", label: "Gigs", icon: ClipboardList },
  { href: "/parent/gigs/new", label: "New", icon: PlusCircle }
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-20 mx-auto max-w-[430px] px-4 pb-4">
      <div className="grid grid-cols-3 rounded-[2rem] border border-white/70 bg-white/90 p-2 shadow-bloom backdrop-blur">
        {items.map((item) => {
          const Icon = item.icon;
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname === item.href || pathname.startsWith(`${item.href}/`);

          return (
            <Link
              key={`${item.href}-${item.label}`}
              href={item.href}
              className={`tap-target flex flex-col items-center justify-center rounded-3xl px-2 py-2 text-xs font-bold transition ${
                active
                  ? "bg-bloom-ink text-white"
                  : "text-slate-500 hover:bg-bloom-cream"
              }`}
            >
              <Icon size={20} strokeWidth={2.5} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
