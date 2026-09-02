import { AlertTriangle, CheckCircle2, Flame, Radar } from "lucide-react";

import type { EmployerRiskLevel } from "@/types/employer";
import { getEmployerRiskLabel } from "@/lib/employer-jobs-talent-copy";
import { cn } from "@/lib/utils";

const riskConfig: Record<
  EmployerRiskLevel,
  { icon: React.ElementType; className: string }
> = {
  healthy: {
    icon: CheckCircle2,
    className: "border-emerald-500/25 bg-emerald-500/10 text-success",
  },
  watch: {
    icon: Radar,
    className: "border-blue-500/25 bg-blue-500/10 text-blue-300",
  },
  risk: {
    icon: AlertTriangle,
    className: "border-amber-500/30 bg-amber-500/10 text-warning",
  },
  critical: {
    icon: Flame,
    className: "border-red-500/30 bg-red-500/10 text-danger",
  },
};

export function JobRiskBadge({
  level,
  locale,
  className,
}: {
  level: EmployerRiskLevel;
  locale: string;
  className?: string;
}) {
  const config = riskConfig[level];
  const Icon = config.icon;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-bold",
        config.className,
        className,
      )}
    >
      <Icon className="size-3.5" />
      {getEmployerRiskLabel(locale, level)}
    </span>
  );
}
