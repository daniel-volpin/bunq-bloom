import Image from "next/image";
import Link from "next/link";

export function Header({
  actionHref = "/parent/gigs/new",
  actionLabel = "New gig"
}: {
  actionHref?: string;
  actionLabel?: string;
}) {
  return (
    <header className="relative flex items-center justify-center px-5 pt-4 pb-1">
      <Link href="/" aria-label="bunq Bloom home">
        <Image
          src="/bloom/logo-wordmark.svg"
          alt="bunq Bloom"
          width={220}
          height={80}
          className="w-[126px]"
          style={{ height: "auto" }}
          priority
        />
      </Link>

      <Link
        href={actionHref}
        aria-label={actionLabel}
        className="tap-target absolute right-5 top-4 grid h-11 w-11 place-items-center rounded-full bg-petal-green shadow-card transition-transform active:scale-95"
      >
        <Image src="/bloom/tulip-emblem.svg" alt="" width={24} height={24} className="h-6 w-6" />
        <span className="sr-only">{actionLabel}</span>
      </Link>
    </header>
  );
}
