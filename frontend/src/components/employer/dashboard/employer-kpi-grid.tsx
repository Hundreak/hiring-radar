import {BriefcaseBusiness, FileText, TrendingUp, UsersRound, type LucideIcon} from 'lucide-react';

import {MetricCard} from '@/components/employer/ui';
import type {EmployerMetric, EmployerTrendDirection} from '@/types/employer';
import type {EmployerCockpitCopy} from '@/lib/employer-cockpit-copy';

const metricIcons: Record<string, LucideIcon> = {
  briefcase: BriefcaseBusiness,
  users: UsersRound,
  fileText: FileText,
  trendingUp: TrendingUp,
};

function trendToNumber(trend?: EmployerTrendDirection, fallback?: string): number {
  if (!trend || trend === 'flat') return 0;
  const numeric = fallback ? Number.parseFloat(fallback.replace('%', '').replace('+', '')) : 1;
  const safe = Number.isFinite(numeric) ? Math.abs(numeric) : 1;
  return trend === 'up' ? safe : -safe;
}

export function EmployerKpiGrid({metrics, copy}: {metrics: EmployerMetric[]; copy: EmployerCockpitCopy}) {
  return (
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {metrics.map((metric) => {
        const value = metric.unit ? `${metric.value}${metric.unit}` : metric.value;
        return (
          <MetricCard
            key={metric.id}
            label={metric.label}
            value={value}
            description={metric.helperText}
            icon={metricIcons[metric.icon]}
            trend={metric.delta?.includes('%') ? {
              value: trendToNumber(metric.trend, metric.delta),
              label: copy.metricTrend.thisMonth,
              positiveDirection: metric.positive === false ? 'down' : 'up',
            } : undefined}
          />
        );
      })}
    </section>
  );
}
