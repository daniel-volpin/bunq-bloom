import Image from "next/image";
import { BookOpen, Dog, Sparkles, Trophy } from "lucide-react";
import type { GigAccent, GigIconKind } from "@/lib/gig-presentation";

export const accentBg: Record<GigAccent, string> = {
  green: "bg-petal-green",
  blue: "bg-petal-blue",
  yellow: "bg-petal-yellow",
  coral: "bg-petal-coral"
};

const iconColor = "hsl(var(--bloom-green-deep))";

function AssetIcon({ src, className }: { src: string; className: string }) {
  return <Image src={src} alt="" width={28} height={28} className={className} />;
}

export function GigIcon({
  kind,
  className = "h-7 w-7"
}: {
  kind: GigIconKind;
  className?: string;
}) {
  const props = { className, strokeWidth: 2.2, color: iconColor } as const;

  switch (kind) {
    case "dog":
      return <Dog {...props} />;
    case "plant":
      return <AssetIcon src="/bloom/plant-gig-icon.svg" className={className} />;
    case "box":
      return <AssetIcon src="/bloom/box-gig-icon.svg" className={className} />;
    case "book":
      return <BookOpen {...props} />;
    case "trophy":
      return <Trophy {...props} />;
    case "sparkle":
    default:
      return <Sparkles {...props} />;
  }
}