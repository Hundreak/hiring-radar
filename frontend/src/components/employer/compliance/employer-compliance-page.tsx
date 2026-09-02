'use client';

import {Download, FileJson2, Filter, KeyRound, RefreshCw, Search, ShieldCheck, TimerReset} from 'lucide-react';
import {useMemo, useState} from 'react';

import {StatusBadge, SurfaceCard} from '@/components/employer/ui';
import {Button} from '@/components/ui/button';
import {RecoverableDataState} from '@/components/ui/recoverable-data-state';
import {useEmployerAuditEventsQuery, getQueryErrorRecovery} from '@/hooks/use-api-queries';
import {api} from '@/lib/api';
import type {EmployerAuditEvent, EmployerAuditSensitivity} from '@/types/user';

type Copy = {
  eyebrow: string;
  title: string;
  description: string;
  total: string;
  highRisk: string;
  exportCsv: string;
  exportJson: string;
  refresh: string;
  filters: string;
  eventType: string;
  resourceType: string;
  resourceId: string;
  searchPlaceholder: string;
  empty: string;
  loading: string;
  timeline: string;
  metadata: string;
  actor: string;
  systemActor: string;
  sensitivity: Record<EmployerAuditSensitivity, string>;
  page: string;
};

const COPY: Record<'tr' | 'en', Copy> = {
  tr: {
    eyebrow: 'Uyumluluk ve kanıt paketi',
    title: 'İşveren denetim kayıtlarını izleyin ve dışa aktarın.',
    description:
      'Ekip, ayar, aday, kampanya ve export işlemlerinin tamamı şirket kapsamına göre listelenir. Owner/admin rolleri kanıt paketini CSV veya JSON olarak alabilir.',
    total: 'Toplam olay',
    highRisk: 'Yüksek hassasiyet',
    exportCsv: 'CSV dışa aktar',
    exportJson: 'JSON kanıt paketi',
    refresh: 'Yenile',
    filters: 'Filtreler',
    eventType: 'Olay tipi',
    resourceType: 'Kaynak tipi',
    resourceId: 'Kaynak ID',
    searchPlaceholder: 'Örn. employer.settings.communication_preferences.updated',
    empty: 'Bu filtrelerle denetim kaydı bulunamadı.',
    loading: 'Denetim kayıtları yükleniyor...',
    timeline: 'Denetim zaman çizelgesi',
    metadata: 'Metadata',
    actor: 'Aktör',
    systemActor: 'Sistem',
    sensitivity: {low: 'Düşük', medium: 'Orta', high: 'Yüksek'},
    page: 'Sayfa',
  },
  en: {
    eyebrow: 'Compliance evidence pack',
    title: 'Review and export employer audit records.',
    description:
      'Team, settings, candidate, campaign and export events are listed within the company scope. Owner/admin roles can download evidence packs as CSV or JSON.',
    total: 'Total events',
    highRisk: 'High sensitivity',
    exportCsv: 'Export CSV',
    exportJson: 'JSON evidence pack',
    refresh: 'Refresh',
    filters: 'Filters',
    eventType: 'Event type',
    resourceType: 'Resource type',
    resourceId: 'Resource ID',
    searchPlaceholder: 'e.g. employer.settings.communication_preferences.updated',
    empty: 'No audit records match these filters.',
    loading: 'Loading audit records...',
    timeline: 'Audit timeline',
    metadata: 'Metadata',
    actor: 'Actor',
    systemActor: 'System',
    sensitivity: {low: 'Low', medium: 'Medium', high: 'High'},
    page: 'Page',
  },
};

function language(locale: string): 'tr' | 'en' {
  return locale.toLowerCase().startsWith('tr') ? 'tr' : 'en';
}

function sensitivityTone(value: EmployerAuditSensitivity): 'success' | 'warning' | 'danger' {
  if (value === 'high') return 'danger';
  if (value === 'medium') return 'warning';
  return 'success';
}

function formatDate(value: string, locale: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(locale === 'tr' ? 'tr-TR' : 'en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

function compactJson(value: Record<string, unknown>) {
  const entries = Object.entries(value);
  if (!entries.length) return '{}';
  return JSON.stringify(value, null, 2);
}

function Field({label, value, placeholder, onChange}: {label: string; value: string; placeholder?: string; onChange: (value: string) => void}) {
  return (
    <label className="block space-y-2">
      <span className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">{label}</span>
      <input
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
        className="h-11 w-full rounded-2xl border border-border bg-surface-elevated px-4 text-sm font-semibold text-foreground shadow-sm outline-none transition placeholder:text-muted-foreground/55 focus:border-primary/45 focus:ring-4 focus:ring-[var(--ring)]"
      />
    </label>
  );
}

function AuditEventCard({event, copy, locale}: {event: EmployerAuditEvent; copy: Copy; locale: string}) {
  const actor = event.actor.name || event.actor.email || copy.systemActor;
  const metadata = compactJson(event.metadata);

  return (
    <SurfaceCard variant="interactive" className="space-y-4 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge tone={sensitivityTone(event.sensitivity)}>{copy.sensitivity[event.sensitivity]}</StatusBadge>
            <StatusBadge tone="info">{event.resource_type}</StatusBadge>
          </div>
          <h3 className="break-words text-base font-black tracking-[-0.02em] text-foreground">{event.event_type}</h3>
          <p className="text-sm font-semibold text-muted-foreground">{event.resource_id}</p>
        </div>
        <div className="text-right text-xs font-bold text-muted-foreground">
          <p>{formatDate(event.created_at, locale)}</p>
          <p className="mt-1">#{event.id}</p>
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-[220px_minmax(0,1fr)]">
        <div className="rounded-2xl border border-border bg-surface-muted/55 p-3">
          <p className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">{copy.actor}</p>
          <p className="mt-2 text-sm font-black text-foreground">{actor}</p>
          {event.actor.email ? <p className="mt-1 truncate text-xs text-muted-foreground">{event.actor.email}</p> : null}
        </div>
        <pre className="max-h-36 overflow-auto rounded-2xl border border-border bg-surface-muted/55 p-3 text-xs leading-5 text-muted-foreground">
          {metadata}
        </pre>
      </div>
    </SurfaceCard>
  );
}

export function EmployerCompliancePage({locale = 'tr'}: {locale?: string}) {
  const copy = COPY[language(locale)];
  const [page, setPage] = useState(1);
  const [eventType, setEventType] = useState('');
  const [resourceType, setResourceType] = useState('');
  const [resourceId, setResourceId] = useState('');
  const queryParams = useMemo(
    () => ({page, pageSize: 25, eventType, resourceType, resourceId}),
    [eventType, page, resourceId, resourceType]
  );
  const query = useEmployerAuditEventsQuery(queryParams);
  const error = getQueryErrorRecovery(query.error);
  const items = query.data?.items ?? [];
  const highRisk = items.filter((item) => item.sensitivity === 'high').length;

  const exportCsv = () => {
    const params = new URLSearchParams({format: 'csv'});
    if (eventType.trim()) params.set('event_type', eventType.trim());
    if (resourceType.trim()) params.set('resource_type', resourceType.trim());
    if (resourceId.trim()) params.set('resource_id', resourceId.trim());
    window.open(`/api/employer/compliance/audit-events/export?${params.toString()}`, '_blank', 'noopener,noreferrer');
  };

  const exportJson = async () => {
    await api.exportEmployerAuditEvents({...queryParams, format: 'json'});
    await query.refetch();
  };

  return (
    <main className="space-y-6 pb-10" aria-labelledby="employer-compliance-title">
      <SurfaceCard variant="accent" className="overflow-hidden p-6 sm:p-7">
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px] lg:items-center">
          <div className="space-y-5">
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge tone="ai"><ShieldCheck className="mr-1 size-3.5" />{copy.eyebrow}</StatusBadge>
              <StatusBadge tone="success"><KeyRound className="mr-1 size-3.5" />Owner/Admin</StatusBadge>
            </div>
            <div className="space-y-3">
              <h1 id="employer-compliance-title" className="max-w-4xl text-3xl font-black tracking-[-0.05em] text-foreground sm:text-4xl lg:text-5xl">
                {copy.title}
              </h1>
              <p className="max-w-3xl text-sm leading-6 text-muted-foreground sm:text-base">{copy.description}</p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button type="button" onClick={exportCsv}><Download className="size-4" />{copy.exportCsv}</Button>
              <Button type="button" variant="secondary" onClick={() => void exportJson()}><FileJson2 className="size-4" />{copy.exportJson}</Button>
              <Button type="button" variant="ghost" onClick={() => void query.refetch()}><RefreshCw className="size-4" />{copy.refresh}</Button>
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
            <SurfaceCard variant="elevated" className="p-5">
              <p className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">{copy.total}</p>
              <p className="mt-2 text-4xl font-black tracking-[-0.06em] text-foreground">{query.data?.total_items ?? 0}</p>
            </SurfaceCard>
            <SurfaceCard variant="elevated" className="p-5">
              <p className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">{copy.highRisk}</p>
              <p className="mt-2 text-4xl font-black tracking-[-0.06em] text-foreground">{highRisk}</p>
            </SurfaceCard>
          </div>
        </div>
      </SurfaceCard>

      <div className="grid gap-6 lg:grid-cols-[320px_minmax(0,1fr)]">
        <SurfaceCard className="h-fit space-y-4 p-5">
          <div className="flex items-center gap-2">
            <Filter className="size-4 text-primary" />
            <h2 className="text-base font-black text-foreground">{copy.filters}</h2>
          </div>
          <Field label={copy.eventType} value={eventType} placeholder={copy.searchPlaceholder} onChange={(value) => { setEventType(value); setPage(1); }} />
          <Field label={copy.resourceType} value={resourceType} onChange={(value) => { setResourceType(value); setPage(1); }} />
          <Field label={copy.resourceId} value={resourceId} onChange={(value) => { setResourceId(value); setPage(1); }} />
          <Button type="button" variant="secondary" className="w-full" onClick={() => void query.refetch()}>
            <Search className="size-4" />{copy.refresh}
          </Button>
        </SurfaceCard>

        <section className="space-y-4" aria-label={copy.timeline}>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-black tracking-[-0.04em] text-foreground">{copy.timeline}</h2>
              <p className="mt-1 text-sm text-muted-foreground">{copy.page} {query.data?.page ?? page} / {query.data?.total_pages ?? 1}</p>
            </div>
            <div className="flex items-center gap-2">
              <Button type="button" variant="ghost" disabled={page <= 1} onClick={() => setPage((current) => Math.max(1, current - 1))}>←</Button>
              <Button type="button" variant="ghost" disabled={!!query.data && page >= query.data.total_pages} onClick={() => setPage((current) => current + 1)}>→</Button>
            </div>
          </div>

          {query.isLoading ? (
            <SurfaceCard className="flex min-h-44 items-center justify-center p-8 text-sm font-bold text-muted-foreground">
              <TimerReset className="mr-2 size-4 animate-spin" />{copy.loading}
            </SurfaceCard>
          ) : error ? (
            <RecoverableDataState error={error} onRetry={() => void query.refetch()} retrying={query.isFetching} />
          ) : items.length ? (
            <div className="space-y-3">
              {items.map((event) => <AuditEventCard key={event.id} event={event} copy={copy} locale={locale} />)}
            </div>
          ) : (
            <SurfaceCard className="p-8 text-center text-sm font-bold text-muted-foreground">{copy.empty}</SurfaceCard>
          )}
        </section>
      </div>
    </main>
  );
}
