'use client';

import Link from 'next/link';
import {ArrowRight, BadgeCheck, Building2, CheckCircle2, Eye, FileText, Gauge, Globe2, LockKeyhole, ShieldCheck, Sparkles, UsersRound} from 'lucide-react';
import {useMemo, useState} from 'react';

import {ScoreBadge, StatusBadge, SurfaceCard} from '@/components/employer/ui';
import {getEmployerCopy} from '@/lib/employer-copy';
import {cn} from '@/lib/utils';

type CompanyBrandPageProps = {
  locale: string;
};

const sectionIcons = {
  profile: Building2,
  preview: Eye,
  process: UsersRound,
  trust: ShieldCheck,
  content: FileText,
} as const;

export function CompanyBrandPage({locale}: CompanyBrandPageProps) {
  const copy = useMemo(() => getEmployerCopy(locale).company, [locale]);
  const scoreLabel = locale === 'tr' ? 'Skor' : 'Score';
  const [activeSection, setActiveSection] = useState<keyof typeof copy.sections>('profile');

  const sections = Object.entries(copy.sections) as Array<[keyof typeof copy.sections, string]>;

  return (
    <div className="space-y-6 pb-10">
      <section className="relative overflow-hidden rounded-[2rem] border border-border bg-[radial-gradient(circle_at_top_left,var(--primary-soft),transparent_32%),linear-gradient(135deg,var(--surface-elevated),var(--surface))] p-5 shadow-2xl shadow-black/10 sm:p-7 lg:p-8">
        <div className="absolute right-8 top-8 hidden rounded-full border border-primary/20 bg-primary/10 p-4 text-primary lg:block">
          <Globe2 className="size-8" />
        </div>
        <div className="max-w-4xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-black uppercase tracking-[0.18em] text-primary">
            <BadgeCheck className="size-3.5" /> {copy.heroEyebrow}
          </div>
          <h2 className="mt-5 max-w-3xl text-3xl font-black tracking-tight text-foreground sm:text-4xl lg:text-5xl">
            {copy.title}
          </h2>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-muted-foreground sm:text-base">
            {copy.description}
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <a
              href="#company-public-preview"
              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-2xl bg-primary px-4 text-sm font-black text-primary-foreground shadow-lg shadow-primary/20 transition hover:-translate-y-0.5 hover:opacity-95 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]"
            >
              {copy.primaryAction} <ArrowRight className="size-4" />
            </a>
            <a
              href="#company-content-quality"
              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-2xl border border-border bg-surface px-4 text-sm font-black text-foreground transition hover:border-primary/35 hover:bg-surface-muted focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]"
            >
              {copy.secondaryAction}
            </a>
          </div>
        </div>
      </section>

      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {copy.metrics.map((metric) => (
          <SurfaceCard key={metric.label} className="p-4">
            <div className="text-xs font-bold text-muted-foreground">{metric.label}</div>
            <div className="mt-2 text-2xl font-black tracking-tight text-foreground">{metric.value}</div>
            <p className="mt-2 text-xs leading-5 text-muted-foreground">{metric.detail}</p>
          </SurfaceCard>
        ))}
      </section>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-6">
          <SurfaceCard className="p-2">
            <div className="grid gap-2 sm:grid-cols-5">
              {sections.map(([key, label]) => {
                const Icon = sectionIcons[key];
                const active = activeSection === key;
                return (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setActiveSection(key)}
                    className={cn(
                      'flex min-h-12 items-center justify-center gap-2 rounded-2xl px-3 text-sm font-black transition focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]',
                      active ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/20' : 'text-muted-foreground hover:bg-surface-muted hover:text-foreground'
                    )}
                  >
                    <Icon className="size-4" /> {label}
                  </button>
                );
              })}
            </div>
          </SurfaceCard>

          {activeSection === 'profile' ? (
            <section className="grid gap-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
              <SurfaceCard className="p-5 sm:p-6">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="text-xl font-black text-foreground">{copy.profileCard.title}</h3>
                    <p className="mt-1 text-sm text-muted-foreground">{copy.profileCard.subtitle}</p>
                  </div>
                  <StatusBadge tone="success">{copy.readinessLabel}</StatusBadge>
                </div>
                <div className="mt-6 grid gap-4 sm:grid-cols-2">
                  {[
                    [copy.profileCard.industryLabel, copy.profileValues.industry],
                    [copy.profileCard.sizeLabel, copy.profileValues.size],
                    [copy.profileCard.locationLabel, copy.profileValues.location],
                    [copy.profileCard.workModelLabel, copy.profileValues.workModel],
                    [copy.profileCard.hiringSpeedLabel, copy.profileValues.hiringSpeed],
                  ].map(([label, value]) => (
                    <div key={label} className="rounded-2xl border border-border bg-surface-muted/60 p-4">
                      <div className="text-[11px] font-black uppercase tracking-[0.16em] text-muted-foreground">{label}</div>
                      <div className="mt-2 text-sm font-bold leading-6 text-foreground">{value}</div>
                    </div>
                  ))}
                </div>
              </SurfaceCard>

              <SurfaceCard className="p-5 sm:p-6">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="text-xl font-black text-foreground">{copy.brandScore.title}</h3>
                    <p className="mt-1 text-sm leading-6 text-muted-foreground">{copy.brandScore.description}</p>
                  </div>
                  <ScoreBadge score={88} label={scoreLabel} size="lg" />
                </div>
                <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
                  <div>
                    <div className="mb-2 text-xs font-black uppercase tracking-[0.16em] text-success">{copy.brandScore.strengthsTitle}</div>
                    <div className="space-y-2">
                      {copy.brandScore.strengths.map((item) => (
                        <div key={item} className="flex gap-2 rounded-2xl border border-success/20 bg-success/10 p-3 text-sm text-foreground">
                          <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" />
                          <span>{item}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <div className="mb-2 text-xs font-black uppercase tracking-[0.16em] text-warning">{copy.brandScore.gapsTitle}</div>
                    <div className="space-y-2">
                      {copy.brandScore.gaps.map((item) => (
                        <div key={item} className="rounded-2xl border border-warning/25 bg-warning/10 p-3 text-sm leading-6 text-foreground">
                          {item}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </SurfaceCard>
            </section>
          ) : null}

          {activeSection === 'preview' ? (
            <SurfaceCard id="company-public-preview" className="overflow-hidden p-0">
              <div className="border-b border-border bg-gradient-to-br from-primary/12 via-accent-soft to-transparent p-6 sm:p-8">
                <div className="inline-flex items-center gap-2 rounded-full border border-success/25 bg-success/10 px-3 py-1 text-xs font-black text-success">
                  <ShieldCheck className="size-3.5" /> {copy.preview.badge}
                </div>
                <h3 className="mt-5 text-3xl font-black tracking-tight text-foreground">{copy.preview.title}</h3>
                <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground sm:text-base">{copy.preview.description}</p>
                <div className="mt-6 flex flex-wrap gap-3">
                  {copy.preview.stats.map((stat) => (
                    <div key={stat.label} className="rounded-2xl border border-border bg-surface/70 px-4 py-3">
                      <div className="text-[11px] font-bold text-muted-foreground">{stat.label}</div>
                      <div className="mt-1 text-sm font-black text-foreground">{stat.value}</div>
                    </div>
                  ))}
                </div>
                <button className="mt-6 inline-flex min-h-11 items-center gap-2 rounded-2xl bg-primary px-4 text-sm font-black text-primary-foreground shadow-lg shadow-primary/20">
                  {copy.preview.cta} <ArrowRight className="size-4" />
                </button>
              </div>
            </SurfaceCard>
          ) : null}

          {activeSection === 'process' ? (
            <SurfaceCard className="p-5 sm:p-6">
              <div className="max-w-2xl">
                <h3 className="text-xl font-black text-foreground">{copy.process.title}</h3>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{copy.process.description}</p>
              </div>
              <div className="mt-6 space-y-3">
                {copy.process.steps.map((step, index) => (
                  <div key={step.title} className="grid gap-4 rounded-3xl border border-border bg-surface-muted/45 p-4 sm:grid-cols-[52px_minmax(0,1fr)_140px] sm:items-center">
                    <div className="flex size-11 items-center justify-center rounded-2xl bg-primary text-sm font-black text-primary-foreground">{index + 1}</div>
                    <div>
                      <div className="text-base font-black text-foreground">{step.title}</div>
                      <p className="mt-1 text-sm leading-6 text-muted-foreground">{step.description}</p>
                    </div>
                    <div className="rounded-2xl border border-border bg-surface px-3 py-2 text-center text-xs font-black text-foreground">{step.duration}</div>
                  </div>
                ))}
              </div>
            </SurfaceCard>
          ) : null}

          {activeSection === 'trust' ? (
            <SurfaceCard className="p-5 sm:p-6">
              <h3 className="text-xl font-black text-foreground">{copy.trust.title}</h3>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{copy.trust.description}</p>
              <div className="mt-6 grid gap-3 md:grid-cols-2">
                {copy.trust.items.map((item) => (
                  <div key={item.title} className="rounded-3xl border border-border bg-surface-muted/45 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="text-base font-black text-foreground">{item.title}</div>
                      <StatusBadge tone={item.status.length > 6 ? 'warning' : 'success'}>{item.status}</StatusBadge>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.description}</p>
                  </div>
                ))}
              </div>
            </SurfaceCard>
          ) : null}

          {activeSection === 'content' ? (
            <SurfaceCard id="company-content-quality" className="p-5 sm:p-6">
              <h3 className="text-xl font-black text-foreground">{copy.content.title}</h3>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{copy.content.description}</p>
              <div className="mt-6 space-y-3">
                {copy.content.items.map((item) => (
                  <div key={item.title} className="rounded-3xl border border-border bg-surface-muted/45 p-4">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <div className="text-base font-black text-foreground">{item.title}</div>
                        <p className="mt-1 text-sm leading-6 text-muted-foreground">{item.description}</p>
                      </div>
                      <ScoreBadge score={item.score} label={scoreLabel} />
                    </div>
                    <div className="mt-4 h-2 overflow-hidden rounded-full bg-surface">
                      <div className="h-full rounded-full bg-primary" style={{width: `${item.score}%`}} />
                    </div>
                  </div>
                ))}
              </div>
            </SurfaceCard>
          ) : null}
        </div>

        <aside className="space-y-4 xl:sticky xl:top-28 xl:self-start">
          <SurfaceCard className="p-5">
            <div className="flex items-center gap-3">
              <div className="flex size-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                <Gauge className="size-5" />
              </div>
              <div>
                <div className="text-sm font-black text-foreground">{copy.sidebar.title}</div>
                <p className="mt-1 text-xs leading-5 text-muted-foreground">{copy.sidebar.description}</p>
              </div>
            </div>
          </SurfaceCard>

          <SurfaceCard className="p-5">
            <div className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">{copy.sidebar.actionsTitle}</div>
            <div className="mt-4 space-y-3">
              {copy.sidebar.actions.map((action) => (
                <div key={action} className="flex gap-3 rounded-2xl border border-border bg-surface-muted/45 p-3 text-sm leading-6 text-foreground">
                  <Sparkles className="mt-1 size-4 shrink-0 text-primary" />
                  <span>{action}</span>
                </div>
              ))}
            </div>
          </SurfaceCard>

          <SurfaceCard className="p-5">
            <div className="flex items-center gap-2 text-sm font-black text-foreground">
              <LockKeyhole className="size-4 text-primary" /> {copy.trustSignals}
            </div>
            <p className="mt-2 text-xs leading-5 text-muted-foreground">
              {copy.trust.description}
            </p>
            <Link href={`/${locale}/employer/settings`} className="mt-4 inline-flex text-sm font-black text-primary hover:underline">
              {copy.sections.profile} <ArrowRight className="ml-1 size-4" />
            </Link>
          </SurfaceCard>
        </aside>
      </div>
    </div>
  );
}
