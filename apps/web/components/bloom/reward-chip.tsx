import { Coins } from "lucide-react";

function formatReward(amount: string | number): string {
  const numericAmount = typeof amount === "number" ? amount : Number.parseFloat(amount);
  const safeAmount = Number.isFinite(numericAmount) ? numericAmount : 0;
  return safeAmount.toFixed(safeAmount % 1 === 0 ? 0 : 2);
}

export function RewardChip({
  amount,
  size = "md"
}: {
  amount: string | number;
  size?: "sm" | "md" | "lg";
}) {
  const sizes = {
    sm: "h-7 gap-1 px-2.5 text-xs [&>svg]:h-3.5 [&>svg]:w-3.5",
    md: "h-9 gap-1.5 px-3 text-sm [&>svg]:h-4 [&>svg]:w-4",
    lg: "h-11 gap-2 px-4 text-base [&>svg]:h-5 [&>svg]:w-5"
  };

  return (
    <span
      className={`inline-flex items-center rounded-full bg-bloom-green/10 font-extrabold text-bloom-green-deep ${sizes[size]}`}
    >
      <Coins />€{formatReward(amount)}
    </span>
  );
}