'use client';

import {AlertTriangle, CheckCircle2, FileText, Globe2, Languages, SearchCheck, ShieldCheck, Sparkles} from 'lucide-react';

import {StatusBadge, SurfaceCard} from '@/components/employer/ui';
import {Button} from '@/components/ui/button';
import {getEmployerLocalizationCopy, type LocalizationRisk} from '@/lib/employer-localization-copy';

function riskTone(severity: LocalizationRisk['severity']) {
  if (severity === 'high') return 'danger';
  if (severity === 'medium') return 'warning';
  return 'info';
}

function ProgressRow({label, value, detail}: {label: string; value: number; detail: string}) {
  return (
    <div className="rounded-2xl border border-border bg-surface-muted/45 p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-sm font-black text-foreground">{label}</p>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">{detail}</p>
        </div>
        <span className="rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-sm font-black text-primary">{value}%</span>
      </div>
      <div className="mt-4 h-2 overflow-hidden rounded-full bg-surface-muted">
        <div className="h-full rounded-full bg-primary" style={{width: `${value}%`}} />
      </div>
    </div>
  );
}

export function EmployerLocalizationPage({locale}: {locale: string}) {
  const copy = getEmployerLocalizationCopy(locale);
  const isTurkish = copy.lang === 'tr';

  return (
    <div className="space-y-6 pb-10">
      <SurfaceCard variant="accent" className="relative overflow-hidden p-6 sm:p-8">
        <div className="absolute -right-24 -top-24 size-72 rounded-full bg-primary/10 blur-3xl" />
        <div className="relative grid gap-7 xl:grid-cols-[minmax(0,1fr)_360px] xl:items-center">
          <div className="space-y-5">
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge tone="ai"><Languages className="size-3.5" />{copy.page.eyebrow}</StatusBadge>
              <StatusBadge tone="success"><ShieldCheck className="size-3.5" />{copy.page.activePolicy}</StatusBadge>
            </div>
            <div className="space-y-3">
              <h1 className="max-w-5xl text-3xl font-black tracking-[-0.06em] text-foreground sm:text-4xl lg:text-5xl">{copy.page.title}</h1>
              <p className="max-w-3xl text-sm leading-6 text-muted-foreground sm:text-base">{copy.page.description}</p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button type="button" size="lg"><SearchCheck className="size-4" />{copy.page.primaryAction}</Button>
              <Button type="button" variant="secondary" size="lg"><FileText className="size-4" />{copy.page.secondaryAction}</Button>
            </div>
          </div>

          <div className="rounded-[28px] border border-border bg-surface/90 p-5 shadow-2xl backdrop-blur">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.18em] text-muted-foreground">{copy.page.productLanguage}</p>
                <p className="mt-2 text-2xl font-black tracking-[-0.04em] text-foreground">{isTurkish ? 'Türkçe' : 'English'}</p>
              </div>
              <div className="flex size-14 items-center justify-center rounded-[22px] border border-primary/20 bg-primary/10 text-primary">
                <Globe2 className="size-7" />
              </div>
            </div>
            <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
              <div className="rounded-2xl border border-border bg-surface-muted/45 p-4">
                <p className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">TR</p>
                <p className="mt-1 text-sm font-black text-foreground">{copy.page.strictTurkish}</p>
              </div>
              <div className="rounded-2xl border border-border bg-surface-muted/45 p-4">
                <p className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">EN</p>
                <p className="mt-1 text-sm font-black text-foreground">{copy.page.strictEnglish}</p>
              </div>
            </div>
          </div>
        </div>
      </SurfaceCard>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {copy.metrics.map((metric) => <ProgressRow key={metric.label} {...metric} />)}
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
        <div className="space-y-6">
          <SurfaceCard className="p-5 sm:p-6">
            <div className="mb-5 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <StatusBadge tone="ai"><Sparkles className="size-3.5" />{copy.sections.glossary}</StatusBadge>
                <h2 className="mt-3 text-2xl font-black tracking-[-0.04em] text-foreground">{copy.sections.glossary}</h2>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">{copy.sections.glossaryDesc}</p>
              </div>
            </div>
            <div className="overflow-hidden rounded-[24px] border border-border">
              <div className="grid grid-cols-[1fr_1fr_1fr] bg-surface-muted px-4 py-3 text-xs font-black uppercase tracking-[0.15em] text-muted-foreground">
                <span>Concept</span>
                <span>TR</span>
                <span>EN</span>
              </div>
              <div className="divide-y divide-border">
                {copy.glossary.map((term) => (
                  <div key={term.concept} className="grid gap-3 px-4 py-4 text-sm md:grid-cols-[1fr_1fr_1fr]">
                    <div>
                      <p className="font-black text-foreground">{term.concept}</p>
                      <p className="mt-1 text-xs leading-5 text-muted-foreground md:max-w-xs">{term.note}</p>
                    </div>
                    <p className="font-bold text-foreground">{term.tr}</p>
                    <p className="font-bold text-foreground">{term.en}</p>
                  </div>
                ))}
              </div>
            </div>
          </SurfaceCard>

          <SurfaceCard className="p-5 sm:p-6">
            <StatusBadge tone="warning"><AlertTriangle className="size-3.5" />{copy.sections.risks}</StatusBadge>
            <h2 className="mt-3 text-2xl font-black tracking-[-0.04em] text-foreground">{copy.sections.risks}</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">{copy.sections.risksDesc}</p>
            <div className="mt-5 grid gap-3">
              {copy.risks.map((risk) => (
                <div key={`${risk.term}-${risk.replacement}`} className="rounded-2xl border border-border bg-surface-muted/45 p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge tone={riskTone(risk.severity)}>{copy.severity[risk.severity]}</StatusBadge>
                    <span className="text-sm font-black text-foreground">{risk.term}</span>
                    <span className="text-sm font-bold text-muted-foreground">→</span>
                    <span className="text-sm font-black text-primary">{risk.replacement}</span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">{risk.reason}</p>
                </div>
              ))}
            </div>
          </SurfaceCard>
        </div>

        <div className="space-y-6">
          <SurfaceCard className="p-5 sm:p-6">
            <StatusBadge tone="info"><ShieldCheck className="size-3.5" />{copy.sections.policy}</StatusBadge>
            <h2 className="mt-3 text-2xl font-black tracking-[-0.04em] text-foreground">{copy.sections.policy}</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">{copy.sections.policyDesc}</p>
            <div className="mt-5 space-y-3">
              {copy.policies.map((policy) => (
                <div key={policy.title} className="rounded-2xl border border-border bg-surface-muted/45 p-4">
                  <p className="font-black text-foreground">{policy.title}</p>
                  <p className="mt-1 text-sm leading-6 text-muted-foreground">{policy.detail}</p>
                </div>
              ))}
            </div>
          </SurfaceCard>

          <SurfaceCard className="p-5 sm:p-6">
            <StatusBadge tone="success"><CheckCircle2 className="size-3.5" />{copy.sections.checklist}</StatusBadge>
            <div className="mt-5 space-y-3">
              {copy.checklist.map((item) => (
                <div key={item} className="flex gap-3 rounded-2xl border border-border bg-surface-muted/45 p-4">
                  <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" />
                  <p className="text-sm font-semibold leading-6 text-foreground">{item}</p>
                </div>
              ))}
            </div>
          </SurfaceCard>
        </div>
      </div>
    </div>
  );
}
