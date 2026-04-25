"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

const items = [
  { href: "/", label: "Home", icon: "/bloom/tulip-emblem.svg", activeColor: "text-bloom-green" },
  { href: "/gigs", label: "Gigs", icon: "/bloom/search-nav-icon.svg", activeColor: "text-bloom-blue" },
  { href: "/wallet", label: "Wallet", icon: "/bloom/wallet-nav-icon.svg", activeColor: "text-bloom-coral" },
  { href: "/profile", label: "Profile", icon: "/bloom/profile-flower-icon.svg", activeColor: "text-bloom-sun" }
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Primary"
      className="fixed inset-x-3 bottom-3 z-40 mx-auto max-w-[366px] rounded-3xl bg-card shadow-soft"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      <div className="grid grid-cols-4 px-2 py-2">
        {items.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname === item.href || pathname.startsWith(`${item.href}/`);

          return (
            <Link
              key={`${item.href}-${item.label}`}
              href={item.href}
              aria-label={`${item.label} tab`}
              className={`tap-target flex min-h-11 flex-col items-center justify-center gap-0.5 rounded-2xl px-2 py-1.5 text-[11px] leading-none transition-colors ${
                active ? `${item.activeColor} font-extrabold` : "font-semibold text-muted-foreground"
              }`}
            >
              <Image
                src={item.icon}
                alt=""
                width={24}
                height={24}
                className={`h-6 w-6 ${active ? "" : "opacity-60 grayscale"}`}
              />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

