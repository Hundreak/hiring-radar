import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";

type SecurityTone = "strong" | "watch" | "risk";

const toneClasses: Record<
  SecurityTone,
  { ring: string; badge: string; dot: string; glow: string }
> = {
  strong: {
    ring: "border-success/30 bg-success/10 text-success",
    badge: "border-success/25 bg-success/10 text-success",
    dot: "bg-success",
    glow: "from-success/18 via-primary/10 to-transparent",
  },
  watch: {
    ring: "border-primary/30 bg-primary/10 text-primary",
    badge: "border-primary/25 bg-primary/10 text-primary",
    dot: "bg-primary",
    glow: "from-primary/18 via-secondary/10 to-transparent",
  },
  risk: {
    ring: "border-danger/30 bg-danger/10 text-danger",
    badge: "border-danger/25 bg-danger/10 text-danger",
    dot: "bg-danger",
    glow: "from-danger/18 via-primary/10 to-transparent",
  },
};

export function SecurityCenterHero({
  score,
  tone,
  title,
  description,
  scoreLabel,
  checklistLabel,
  items,
}: {
  score: number;
  tone: SecurityTone;
  title: string;
  description: string;
  scoreLabel: string;
  checklistLabel: string;
  items: Array<{ label: string; complete: boolean }>;
}) {
  const classes = toneClasses[tone];
  const safeScore = Math.max(0, Math.min(100, Math.round(score)));

  return (
    <section
      data-security-center="hero"
      className="relative overflow-hidden rounded-[28px] border border-border bg-surface p-6 shadow-sm"
    >
      <div
        className={`pointer-events-none absolute inset-x-0 top-0 h-32 bg-gradient-to-b ${classes.glow}`}
      />
      <div className="relative grid gap-6 lg:grid-cols-[minmax(0,1fr)_220px] lg:items-center">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-border bg-surface-muted px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            <span className={`size-2 rounded-full ${classes.dot}`} />
            {checklistLabel}
          </div>
          <h2 className="mt-4 max-w-2xl text-2xl font-semibold tracking-tight text-foreground">
            {title}
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            {description}
          </p>
          <div className="mt-5 grid gap-2 sm:grid-cols-3">
            {items.map((item) => (
              <div
                key={item.label}
                className="flex items-center gap-2 rounded-2xl border border-border bg-surface-muted px-3 py-2 text-xs text-foreground/80"
              >
                <span
                  className={`size-2 rounded-full ${item.complete ? "bg-success" : "bg-border"}`}
                />
                <span className="truncate">{item.label}</span>
              </div>
            ))}
          </div>
        </div>
        <div
          className={`rounded-[26px] border p-5 text-center ${classes.ring}`}
        >
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] opacity-80">
            {scoreLabel}
          </div>
          <div className="mt-2 text-5xl font-bold tabular-nums">
            {safeScore}
          </div>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-black/10 dark:bg-white/10">
            <div
              className="h-full rounded-full bg-current transition-all"
              style={{ width: `${safeScore}%` }}
            />
          </div>
        </div>
      </div>
    </section>
  );
}

export function SecurityMetricCard({
  label,
  value,
  hint,
  tone = "watch",
}: {
  label: string;
  value: string;
  hint: string;
  tone?: SecurityTone;
}) {
  const classes = toneClasses[tone];
  return (
    <div
      data-security-center="metric"
      className="rounded-3xl border border-border bg-surface p-5 shadow-sm"
    >
      <div
        className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] ${classes.badge}`}
      >
        {label}
      </div>
      <div className="mt-4 text-2xl font-semibold text-foreground">{value}</div>
      <p className="mt-1 text-xs leading-5 text-muted-foreground">{hint}</p>
    </div>
  );
}

export function SecurityActionRail({ children }: { children: ReactNode }) {
  return (
    <div data-security-center="actions" className="grid gap-3 md:grid-cols-3">
      {children}
    </div>
  );
}

export function SecurityActionCard({
  title,
  description,
  buttonLabel,
  onClick,
  tone = "watch",
}: {
  title: string;
  description: string;
  buttonLabel: string;
  onClick: () => void;
  tone?: SecurityTone;
}) {
  const classes = toneClasses[tone];
  return (
    <div className="rounded-3xl border border-border bg-surface p-5 shadow-sm">
      <div className="flex items-start gap-3">
        <span className={`mt-1 size-2.5 rounded-full ${classes.dot}`} />
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-foreground">{title}</h3>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            {description}
          </p>
        </div>
      </div>
      <Button
        type="button"
        variant="outline"
        size="sm"
        className="mt-4 w-full"
        onClick={onClick}
      >
        {buttonLabel}
      </Button>
    </div>
  );
}
