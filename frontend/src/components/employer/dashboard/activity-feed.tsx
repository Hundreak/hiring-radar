import Link from 'next/link';
import {BriefcaseBusiness, FileText, MessageSquare, Sparkles, UserCheck, UsersRound, Zap, type LucideIcon} from 'lucide-react';

import {SectionHeader, StatusBadge, SurfaceCard} from '@/components/employer/ui';
import type {EmployerActivity, EmployerInsightTone} from '@/types/employer';
import type {EmployerCockpitCopy} from '@/lib/employer-cockpit-copy';
import {cn} from '@/lib/utils';

const activityIcons: Record<string, LucideIcon> = {
  users: UsersRound,
  sparkles: Sparkles,
  userCheck: UserCheck,
  briefcase: BriefcaseBusiness,
  zap: Zap,
  fileText: FileText,
  message: MessageSquare,
};

const toneClasses: Record<EmployerInsightTone, string> = {
  ai: 'text-primary bg-primary/10 border-primary/20',
  info: 'text-blue-500 bg-blue-500/10 border-blue-500/20',
  success: 'text-success bg-emerald-500/10 border-emerald-500/20',
  warning: 'text-warning bg-amber-500/10 border-amber-500/20',
  danger: 'text-danger bg-red-500/10 border-red-500/20',
};

export function ActivityFeed({activities, locale, copy}: {activities: EmployerActivity[]; locale: string; copy: EmployerCockpitCopy}) {
  return (
    <SurfaceCard className="space-y-5">
      <SectionHeader eyebrow={copy.activity.eyebrow} title={copy.activity.title} description={copy.activity.description} />

      <div className="space-y-3">
        {activities.slice(0, 5).map((activity) => {
          const Icon = activityIcons[activity.icon] ?? Sparkles;
          const content = (
            <div className="flex gap-3 rounded-[22px] border border-border bg-surface/70 p-3 transition hover:border-primary/25 hover:bg-surface-muted/70">
              <span className={cn('flex size-10 shrink-0 items-center justify-center rounded-2xl border', toneClasses[activity.tone])}>
                <Icon className="size-4" />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm font-bold text-foreground">{activity.title}</p>
                  <span className="shrink-0 text-[11px] font-medium text-muted-foreground">{activity.time}</span>
                </div>
                <p className="mt-1 text-xs leading-5 text-muted-foreground">{activity.description}</p>
              </div>
            </div>
          );

          return activity.href ? (
            <Link key={activity.id} href={localizeActivityHref(activity.href, locale)} className="block focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]">
              {content}
            </Link>
          ) : (
            <div key={activity.id}>{content}</div>
          );
        })}
      </div>

      <div className="flex items-center justify-between rounded-[22px] border border-border bg-surface-muted/70 p-3">
        <p className="text-xs text-muted-foreground">{copy.activity.auditNote}</p>
        <StatusBadge tone="ai">{copy.activity.auditReady}</StatusBadge>
      </div>
    </SurfaceCard>
  );
}

function localizeActivityHref(href: string, locale: string): string {
  if (href.startsWith(`/${locale}/`)) return href;
  if (href.startsWith('/tr/')) return href.replace('/tr/', `/${locale}/`);
  return href;
}
