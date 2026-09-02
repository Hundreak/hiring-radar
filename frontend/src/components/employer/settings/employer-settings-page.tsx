'use client';

import {
  Bell,
  Building2,
  ChevronRight,
  CircleAlert,
  Clock3,
  Eye,
  FileKey2,
  Globe2,
  KeyRound,
  Loader2,
  Mail,
  MapPin,
  Palette,
  Plus,
  RefreshCw,
  Save,
  ShieldCheck,
  Sparkles,
  ToggleLeft,
  ToggleRight,
  UsersRound,
  Webhook,
} from 'lucide-react';
import {useMemo, useState} from 'react';

import {StatusBadge, SurfaceCard} from '@/components/employer/ui';
import {Button} from '@/components/ui/button';
import {useEmployerCommunicationPreferencesQuery, useUpdateEmployerCommunicationPreferencesMutation} from '@/hooks/use-api-queries';
import {getEmployerSettingsCopy} from '@/lib/employer-page-copy';
import {cn} from '@/lib/utils';
import type {EmployerCommunicationPreferences} from '@/types/user';

type SettingsTab = 'company' | 'team' | 'security' | 'notifications' | 'brand' | 'integrations' | 'audit';
type StatusTone = 'success' | 'warning' | 'danger' | 'info' | 'ai' | 'neutral';

const tabIcons: Record<SettingsTab, typeof Building2> = {
  company: Building2,
  team: UsersRound,
  security: ShieldCheck,
  notifications: Bell,
  brand: Palette,
  integrations: Webhook,
  audit: FileKey2,
};

const tabOrder: SettingsTab[] = ['company', 'team', 'security', 'notifications', 'brand', 'integrations', 'audit'];

function riskTone(risk: 'low' | 'medium' | 'high'): StatusTone {
  if (risk === 'high') return 'danger';
  if (risk === 'medium') return 'warning';
  return 'success';
}

function statusTone(status: string): StatusTone {
  if (status === 'active' || status === 'connected') return 'success';
  if (status === 'invited' || status === 'available') return 'info';
  if (status === 'needs_review' || status === 'limited') return 'warning';
  return 'neutral';
}

function ToggleRow({title, description, enabled, enabledLabel, disabledLabel}: {title: string; description: string; enabled: boolean; enabledLabel: string; disabledLabel: string}) {
  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-border bg-surface-muted/50 p-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0">
        <p className="text-sm font-black text-foreground">{title}</p>
        <p className="mt-1 text-sm leading-6 text-muted-foreground">{description}</p>
      </div>
      <div className="flex items-center gap-2">
        <StatusBadge tone={enabled ? 'success' : 'neutral'}>{enabled ? enabledLabel : disabledLabel}</StatusBadge>
        {enabled ? <ToggleRight className="size-7 text-success" /> : <ToggleLeft className="size-7 text-muted-foreground" />}
      </div>
    </div>
  );
}

function Field({label, value, onChange, multiline = false}: {label: string; value: string; onChange: (value: string) => void; multiline?: boolean}) {
  if (multiline) {
    return (
      <label className="block space-y-2 md:col-span-2">
        <span className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">{label}</span>
        <textarea
          rows={5}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="w-full rounded-[24px] border border-border bg-surface-elevated p-4 text-sm leading-6 text-foreground shadow-sm outline-none transition placeholder:text-muted-foreground/60 focus:border-primary/45 focus:ring-4 focus:ring-[var(--ring)]"
        />
      </label>
    );
  }

  return (
    <label className="block space-y-2">
      <span className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-12 w-full rounded-2xl border border-border bg-surface-elevated px-4 text-sm font-semibold text-foreground shadow-sm outline-none transition placeholder:text-muted-foreground/60 focus:border-primary/45 focus:ring-4 focus:ring-[var(--ring)]"
      />
    </label>
  );
}

function SectionTitle({eyebrow, title, description}: {eyebrow: string; title: string; description: string}) {
  return (
    <div className="space-y-2">
      <StatusBadge tone="ai">{eyebrow}</StatusBadge>
      <h2 className="text-2xl font-black tracking-[-0.04em] text-foreground">{title}</h2>
      <p className="max-w-3xl text-sm leading-6 text-muted-foreground">{description}</p>
    </div>
  );
}

function SettingsHero({locale, score}: {locale: string; score: number}) {
  const copy = getEmployerSettingsCopy(locale);

  return (
    <SurfaceCard variant="accent" className="relative overflow-hidden p-6 sm:p-7">
      <div className="absolute -right-24 -top-24 size-64 rounded-full bg-primary/10 blur-3xl" />
      <div className="relative grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px] lg:items-center">
        <div className="space-y-5">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge tone="ai">{copy.page.eyebrow}</StatusBadge>
            <StatusBadge tone="success">{copy.page.readiness} {score}/100</StatusBadge>
            <StatusBadge tone="info">{copy.page.roleAccess}</StatusBadge>
          </div>
          <div className="space-y-3">
            <h1 className="max-w-4xl text-3xl font-black tracking-[-0.06em] text-foreground sm:text-4xl lg:text-5xl">{copy.page.title}</h1>
            <p className="max-w-3xl text-sm leading-6 text-muted-foreground sm:text-base">{copy.page.description}</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button type="button" size="lg"><Save className="size-4" />{copy.page.save}</Button>
            <Button type="button" variant="secondary" size="lg"><Plus className="size-4" />{copy.page.invite}</Button>
            <Button type="button" variant="ghost" size="lg"><FileKey2 className="size-4" />{copy.page.exportAudit}</Button>
          </div>
        </div>

        <div className="rounded-[28px] border border-border bg-surface/85 p-5 shadow-2xl backdrop-blur">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.18em] text-muted-foreground">{copy.page.securityPosture}</p>
              <p className="mt-2 text-4xl font-black tracking-[-0.06em] text-foreground">{score}</p>
            </div>
            <div className="flex size-16 items-center justify-center rounded-[24px] border border-primary/20 bg-primary/10 text-primary">
              <ShieldCheck className="size-8" />
            </div>
          </div>
          <div className="mt-5 space-y-3">
            {copy.audit.readiness.slice(0, 3).map((item) => (
              <div key={item.label} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs font-bold text-muted-foreground">
                  <span>{item.label}</span>
                  <span>{item.value}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-surface-muted">
                  <div className="h-full rounded-full bg-primary" style={{width: `${item.value}%`}} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </SurfaceCard>
  );
}

function TabNavigation({locale, activeTab, onChange}: {locale: string; activeTab: SettingsTab; onChange: (tab: SettingsTab) => void}) {
  const copy = getEmployerSettingsCopy(locale);

  return (
    <SurfaceCard className="sticky top-24 p-2 lg:p-3">
      <div className="space-y-1">
        {tabOrder.map((tab) => {
          const Icon = tabIcons[tab];
          const selected = activeTab === tab;
          return (
            <button
              key={tab}
              type="button"
              onClick={() => onChange(tab)}
              className={cn('group flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left transition focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]', selected ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/20' : 'text-muted-foreground hover:bg-surface-muted hover:text-foreground')}
            >
              <span className={cn('flex size-10 shrink-0 items-center justify-center rounded-2xl border', selected ? 'border-white/20 bg-white/15 text-white' : 'border-border bg-surface text-primary')}>
                <Icon className="size-4" />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-sm font-black">{copy.tabs[tab].label}</span>
                <span className={cn('mt-0.5 line-clamp-1 block text-xs', selected ? 'text-primary-foreground/75' : 'text-muted-foreground')}>{copy.tabs[tab].description}</span>
              </span>
              <ChevronRight className={cn('size-4 shrink-0 transition', selected ? 'translate-x-0.5 text-white' : 'opacity-0 group-hover:opacity-100')} />
            </button>
          );
        })}
      </div>
    </SurfaceCard>
  );
}

function CompanySettings({locale}: {locale: string}) {
  const copy = getEmployerSettingsCopy(locale);
  const [companyName, setCompanyName] = useState(copy.company.values.name);
  const [website, setWebsite] = useState(copy.company.values.website);
  const [location, setLocation] = useState(copy.company.values.location);
  const [goal, setGoal] = useState(copy.company.values.goal);
  const [summary, setSummary] = useState(copy.company.values.summary);

  return (
    <div className="space-y-6">
      <SectionTitle eyebrow={copy.company.eyebrow} title={copy.company.title} description={copy.company.description} />
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_340px]">
        <SurfaceCard className="space-y-5">
          <div className="grid gap-4 md:grid-cols-2">
            <Field label={copy.company.fields.name} value={companyName} onChange={setCompanyName} />
            <Field label={copy.company.fields.website} value={website} onChange={setWebsite} />
            <Field label={copy.company.fields.location} value={location} onChange={setLocation} />
            <Field label={copy.company.fields.goal} value={goal} onChange={setGoal} />
            <Field label={copy.company.fields.summary} value={summary} onChange={setSummary} multiline />
          </div>
          <div className="flex flex-wrap gap-3">
            <Button type="button"><Save className="size-4" />{copy.company.actions.save}</Button>
            <Button type="button" variant="secondary"><Eye className="size-4" />{copy.company.actions.preview}</Button>
          </div>
        </SurfaceCard>

        <SurfaceCard variant="elevated" className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="flex size-16 items-center justify-center rounded-[24px] bg-gradient-to-br from-primary to-accent text-xl font-black text-white shadow-lg shadow-primary/20">NT</div>
            <div>
              <h3 className="text-base font-black text-foreground">{copy.company.cardTitle}</h3>
              <p className="text-xs leading-5 text-muted-foreground">{copy.company.cardDescription}</p>
            </div>
          </div>
          <div className="space-y-3 rounded-[24px] border border-border bg-surface-muted/70 p-4">
            <div className="flex items-center gap-2 text-sm font-bold text-foreground"><MapPin className="size-4 text-primary" />{location}</div>
            <div className="flex items-center gap-2 text-sm font-bold text-foreground"><Globe2 className="size-4 text-primary" />{website.replace('https://', '')}</div>
            {copy.company.signals.map((signal) => (
              <div key={signal} className="flex items-center gap-2 text-sm font-bold text-foreground"><Sparkles className="size-4 text-primary" />{signal}</div>
            ))}
          </div>
          <Button type="button" variant="soft" className="w-full"><Palette className="size-4" />{copy.company.actions.editBrand}</Button>
        </SurfaceCard>
      </div>
    </div>
  );
}

function TeamSettings({locale}: {locale: string}) {
  const copy = getEmployerSettingsCopy(locale);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <SectionTitle eyebrow={copy.team.eyebrow} title={copy.team.title} description={copy.team.description} />
        <Button type="button"><Plus className="size-4" />{copy.team.invite}</Button>
      </div>

      <SurfaceCard className="space-y-4">
        <h3 className="text-lg font-black text-foreground">{copy.team.membersTitle}</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="text-xs uppercase tracking-[0.14em] text-muted-foreground">
              <tr>
                <th className="px-3 py-3">{copy.team.columns.member}</th>
                <th className="px-3 py-3">{copy.team.columns.role}</th>
                <th className="px-3 py-3">{copy.team.columns.status}</th>
                <th className="px-3 py-3">{copy.team.columns.scope}</th>
                <th className="px-3 py-3">{copy.team.columns.active}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {copy.team.members.map((member) => (
                <tr key={member.email}>
                  <td className="px-3 py-4">
                    <p className="font-black text-foreground">{member.name}</p>
                    <p className="text-xs text-muted-foreground">{member.email}</p>
                  </td>
                  <td className="px-3 py-4 font-semibold text-foreground">{member.role}</td>
                  <td className="px-3 py-4"><StatusBadge tone={statusTone(member.status)}>{copy.status[member.status as keyof typeof copy.status]}</StatusBadge></td>
                  <td className="px-3 py-4 text-muted-foreground">{member.scope}</td>
                  <td className="px-3 py-4 text-muted-foreground">{member.lastActive}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SurfaceCard>

      <SurfaceCard className="space-y-4">
        <h3 className="text-lg font-black text-foreground">{copy.team.rolesTitle}</h3>
        <div className="grid gap-3 lg:grid-cols-2">
          {copy.team.roles.map((role) => (
            <div key={role.role} className="rounded-2xl border border-border bg-surface-muted/50 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h4 className="text-sm font-black text-foreground">{role.role}</h4>
                  <p className="mt-1 text-xs leading-5 text-muted-foreground">{role.description}</p>
                </div>
                <StatusBadge tone={riskTone(role.risk as 'low' | 'medium' | 'high')}>{copy.risk[role.risk as keyof typeof copy.risk]}</StatusBadge>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {role.permissions.map((permission) => <span key={permission} className="rounded-full bg-surface px-3 py-1 text-xs font-bold text-muted-foreground">{permission}</span>)}
              </div>
            </div>
          ))}
        </div>
      </SurfaceCard>
    </div>
  );
}

function SecuritySettings({locale}: {locale: string}) {
  const copy = getEmployerSettingsCopy(locale);

  return (
    <div className="space-y-6">
      <SectionTitle eyebrow={copy.security.eyebrow} title={copy.security.title} description={copy.security.description} />
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
        <SurfaceCard className="space-y-3">
          {copy.security.items.map((item) => <ToggleRow key={item.title} title={item.title} description={item.description} enabled={item.enabled} enabledLabel={copy.common.enabled} disabledLabel={copy.common.disabled} />)}
        </SurfaceCard>
        <SurfaceCard variant="elevated" className="space-y-4">
          <div className="flex size-12 items-center justify-center rounded-2xl border border-primary/20 bg-primary/10 text-primary"><KeyRound className="size-6" /></div>
          <h3 className="text-lg font-black text-foreground">{copy.security.gapsTitle}</h3>
          <div className="space-y-3">
            {copy.security.gaps.map((gap) => (
              <div key={gap} className="flex items-center gap-3 rounded-2xl border border-border bg-surface-muted/50 p-3 text-sm font-bold text-foreground">
                <CircleAlert className="size-4 text-warning" />
                {gap}
              </div>
            ))}
          </div>
        </SurfaceCard>
      </div>
    </div>
  );
}

type CommunicationPreferenceKey = keyof EmployerCommunicationPreferences;
type CommunicationRouteKey =
  | 'route_overdue_candidates_to'
  | 'route_hot_candidates_to'
  | 'route_campaign_review_to'
  | 'route_weekly_digest_to';

function SelectField({label, value, options, onChange, disabled = false}: {label: string; value: string; options: Record<string, string>; onChange: (value: string) => void; disabled?: boolean}) {
  return (
    <label className="block space-y-2">
      <span className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">{label}</span>
      <select
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        className="h-12 w-full rounded-2xl border border-border bg-surface-elevated px-4 text-sm font-black text-foreground shadow-sm outline-none transition focus:border-primary/45 focus:ring-4 focus:ring-[var(--ring)] disabled:cursor-not-allowed disabled:opacity-60"
      >
        {Object.entries(options).map(([optionValue, optionLabel]) => (
          <option key={optionValue} value={optionValue}>{optionLabel}</option>
        ))}
      </select>
    </label>
  );
}

function TextPreferenceField({label, value, onCommit, disabled = false, help}: {label: string; value: string; onCommit: (value: string) => void; disabled?: boolean; help?: string}) {
  return (
    <label className="block space-y-2">
      <span className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">{label}</span>
      <input
        key={`${label}-${value}`}
        defaultValue={value}
        disabled={disabled}
        onBlur={(event) => {
          const nextValue = event.target.value.trim();
          if (nextValue && nextValue !== value) {
            onCommit(nextValue);
          }
        }}
        className="h-12 w-full rounded-2xl border border-border bg-surface-elevated px-4 text-sm font-semibold text-foreground shadow-sm outline-none transition placeholder:text-muted-foreground/60 focus:border-primary/45 focus:ring-4 focus:ring-[var(--ring)] disabled:cursor-not-allowed disabled:opacity-60"
      />
      {help ? <span className="text-xs leading-5 text-muted-foreground">{help}</span> : null}
    </label>
  );
}

function NotificationToggleRow({
  title,
  description,
  enabled,
  locked = false,
  loading = false,
  onToggle,
  enabledLabel,
  disabledLabel,
  mandatoryLabel,
  savingLabel,
}: {
  title: string;
  description: string;
  enabled: boolean;
  locked?: boolean;
  loading?: boolean;
  onToggle: () => void;
  enabledLabel: string;
  disabledLabel: string;
  mandatoryLabel: string;
  savingLabel: string;
}) {
  return (
    <button
      type="button"
      disabled={locked || loading}
      onClick={onToggle}
      className="flex w-full flex-col gap-4 rounded-2xl border border-border bg-surface-muted/50 p-4 text-left transition hover:border-primary/30 hover:bg-surface-muted focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)] disabled:cursor-not-allowed disabled:opacity-75 sm:flex-row sm:items-center sm:justify-between"
    >
      <span className="min-w-0">
        <span className="block text-sm font-black text-foreground">{title}</span>
        <span className="mt-1 block text-sm leading-6 text-muted-foreground">{description}</span>
      </span>
      <span className="flex shrink-0 items-center gap-2">
        {locked ? <StatusBadge tone="info">{mandatoryLabel}</StatusBadge> : null}
        {loading ? <StatusBadge tone="warning">{savingLabel}</StatusBadge> : null}
        <StatusBadge tone={enabled ? 'success' : 'neutral'}>{enabled ? enabledLabel : disabledLabel}</StatusBadge>
        {loading ? <Loader2 className="size-6 animate-spin text-primary" /> : enabled ? <ToggleRight className="size-7 text-success" /> : <ToggleLeft className="size-7 text-muted-foreground" />}
      </span>
    </button>
  );
}

function NotificationsSettings({locale}: {locale: string}) {
  const copy = getEmployerSettingsCopy(locale);
  const preferencesQuery = useEmployerCommunicationPreferencesQuery();
  const updateMutation = useUpdateEmployerCommunicationPreferencesMutation();
  const preferences = preferencesQuery.data?.preferences;
  const teamSummary = preferencesQuery.data?.team_summary;
  const pending = updateMutation.isPending;

  const updatePreferences = (patch: Partial<EmployerCommunicationPreferences>) => {
    updateMutation.mutate(patch);
  };

  if (preferencesQuery.isLoading) {
    return (
      <div className="space-y-6">
        <SectionTitle eyebrow={copy.notifications.eyebrow} title={copy.notifications.title} description={copy.notifications.description} />
        <SurfaceCard className="flex items-center gap-3 text-sm font-bold text-muted-foreground">
          <Loader2 className="size-5 animate-spin text-primary" />
          {copy.notifications.loading}
        </SurfaceCard>
      </div>
    );
  }

  if (preferencesQuery.isError || !preferences) {
    return (
      <div className="space-y-6">
        <SectionTitle eyebrow={copy.notifications.eyebrow} title={copy.notifications.title} description={copy.notifications.description} />
        <SurfaceCard className="space-y-4">
          <div className="flex items-start gap-3">
            <div className="flex size-11 shrink-0 items-center justify-center rounded-2xl border border-danger/20 bg-danger/10 text-danger">
              <CircleAlert className="size-5" />
            </div>
            <div>
              <h3 className="text-base font-black text-foreground">{copy.notifications.errorTitle}</h3>
              <p className="mt-1 text-sm leading-6 text-muted-foreground">{String(preferencesQuery.error ?? '')}</p>
            </div>
          </div>
          <Button type="button" variant="secondary" onClick={() => void preferencesQuery.refetch()}>
            <RefreshCw className="size-4" />
            {copy.notifications.retry}
          </Button>
        </SurfaceCard>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <SectionTitle eyebrow={copy.notifications.eyebrow} title={copy.notifications.title} description={copy.notifications.description} />

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_340px]">
        <SurfaceCard className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 className="text-lg font-black text-foreground">{copy.notifications.controlsTitle}</h3>
            {preferencesQuery.data?.updated_at ? (
              <span className="text-xs font-bold text-muted-foreground">{copy.notifications.updatedAt}: {new Date(preferencesQuery.data.updated_at).toLocaleString()}</span>
            ) : null}
          </div>
          {copy.notifications.controls.map((item) => {
            const key = item.key as CommunicationPreferenceKey;
            const value = Boolean(preferences[key]);
            return (
              <NotificationToggleRow
                key={item.key}
                title={item.title}
                description={item.description}
                enabled={value}
                locked={Boolean(item.locked)}
                loading={pending}
                onToggle={() => updatePreferences({[key]: !value} as Partial<EmployerCommunicationPreferences>)}
                enabledLabel={copy.common.enabled}
                disabledLabel={copy.common.disabled}
                mandatoryLabel={copy.notifications.mandatory}
                savingLabel={copy.notifications.saving}
              />
            );
          })}
        </SurfaceCard>

        <SurfaceCard variant="elevated" className="space-y-4">
          <div className="flex size-12 items-center justify-center rounded-2xl border border-primary/20 bg-primary/10 text-primary"><UsersRound className="size-6" /></div>
          <h3 className="text-lg font-black text-foreground">{copy.notifications.teamTitle}</h3>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            <div className="rounded-2xl border border-border bg-surface-muted/60 p-4">
              <p className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">{copy.notifications.activeMembers}</p>
              <p className="mt-1 text-3xl font-black text-foreground">{teamSummary?.active_members ?? 0}</p>
            </div>
            <div className="rounded-2xl border border-border bg-surface-muted/60 p-4">
              <p className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">{copy.notifications.invitedMembers}</p>
              <p className="mt-1 text-3xl font-black text-foreground">{teamSummary?.invited_members ?? 0}</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(teamSummary?.roles ?? {}).map(([role, count]) => (
              <span key={role} className="rounded-full bg-surface px-3 py-1 text-xs font-black text-muted-foreground">
                {copy.notifications.routeLabels[role as keyof typeof copy.notifications.routeLabels] ?? role}: {count}
              </span>
            ))}
          </div>
        </SurfaceCard>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <SurfaceCard className="space-y-4">
          <h3 className="text-lg font-black text-foreground">{copy.notifications.routingTitle}</h3>
          <div className="grid gap-4 md:grid-cols-2">
            {Object.entries(copy.notifications.routes).map(([routeKey, routeLabel]) => (
              <SelectField
                key={routeKey}
                label={routeLabel}
                value={String(preferences[routeKey as CommunicationRouteKey])}
                options={copy.notifications.routeLabels}
                disabled={pending}
                onChange={(value) => updatePreferences({[routeKey]: value} as Partial<EmployerCommunicationPreferences>)}
              />
            ))}
          </div>
        </SurfaceCard>

        <SurfaceCard className="space-y-4">
          <h3 className="text-lg font-black text-foreground">{copy.notifications.quietTitle}</h3>
          <div className="grid gap-4 md:grid-cols-2">
            <SelectField
              label={copy.notifications.defaultChannel}
              value={preferences.default_channel}
              options={copy.notifications.channels}
              disabled={pending}
              onChange={(value) => updatePreferences({default_channel: value})}
            />
            <NotificationToggleRow
              title={copy.notifications.quietTitle}
              description={`${copy.notifications.quietStart}: ${preferences.quiet_hours_start} · ${copy.notifications.quietEnd}: ${preferences.quiet_hours_end}`}
              enabled={preferences.quiet_hours_enabled}
              loading={pending}
              onToggle={() => updatePreferences({quiet_hours_enabled: !preferences.quiet_hours_enabled})}
              enabledLabel={copy.common.enabled}
              disabledLabel={copy.common.disabled}
              mandatoryLabel={copy.notifications.mandatory}
              savingLabel={copy.notifications.saving}
            />
            <TextPreferenceField label={copy.notifications.quietStart} value={preferences.quiet_hours_start} disabled={pending} onCommit={(value) => updatePreferences({quiet_hours_start: value})} />
            <TextPreferenceField label={copy.notifications.quietEnd} value={preferences.quiet_hours_end} disabled={pending} onCommit={(value) => updatePreferences({quiet_hours_end: value})} />
            <TextPreferenceField label={copy.notifications.timezone} value={preferences.timezone} disabled={pending} onCommit={(value) => updatePreferences({timezone: value})} />
            <div className="md:col-span-2">
              <TextPreferenceField
                label={copy.notifications.notificationEmails}
                value={preferences.notification_emails.join(', ')}
                disabled={pending}
                help={copy.notifications.notificationEmailsHelp}
                onCommit={(value) => updatePreferences({notification_emails: value.split(',').map((item) => item.trim()).filter(Boolean)})}
              />
            </div>
          </div>
        </SurfaceCard>
      </div>
    </div>
  );
}

function BrandSettings({locale}: {locale: string}) {
  const copy = getEmployerSettingsCopy(locale);
  return (
    <div className="space-y-6">
      <SectionTitle eyebrow={copy.brand.eyebrow} title={copy.brand.title} description={copy.brand.description} />
      <div className="grid gap-4 md:grid-cols-3">
        {copy.brand.cards.map((card) => (
          <SurfaceCard key={card.label} variant="interactive" className="space-y-2">
            <p className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">{card.label}</p>
            <p className="text-2xl font-black tracking-[-0.04em] text-foreground">{card.value}</p>
            <p className="text-sm leading-6 text-muted-foreground">{card.description}</p>
          </SurfaceCard>
        ))}
      </div>
    </div>
  );
}

function IntegrationsSettings({locale}: {locale: string}) {
  const copy = getEmployerSettingsCopy(locale);
  const icons = [Clock3, Mail, Webhook, FileKey2];
  return (
    <div className="space-y-6">
      <SectionTitle eyebrow={copy.integrations.eyebrow} title={copy.integrations.title} description={copy.integrations.description} />
      <div className="grid gap-4 lg:grid-cols-2">
        {copy.integrations.items.map((integration, index) => {
          const Icon = icons[index] ?? Webhook;
          return (
            <SurfaceCard key={integration.name} variant="interactive" className="space-y-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="flex size-12 items-center justify-center rounded-2xl border border-border bg-surface-muted text-primary"><Icon className="size-5" /></div>
                  <div>
                    <h3 className="text-base font-black text-foreground">{integration.name}</h3>
                    <p className="mt-1 text-sm leading-6 text-muted-foreground">{integration.description}</p>
                  </div>
                </div>
                <StatusBadge tone={statusTone(integration.status)}>{copy.status[integration.status as keyof typeof copy.status]}</StatusBadge>
              </div>
              <Button type="button" variant="secondary" size="sm">{integration.status === 'connected' ? copy.common.manage : copy.common.configure}</Button>
            </SurfaceCard>
          );
        })}
      </div>
    </div>
  );
}

function AuditSettings({locale}: {locale: string}) {
  const copy = getEmployerSettingsCopy(locale);
  return (
    <div className="space-y-6">
      <SectionTitle eyebrow={copy.audit.eyebrow} title={copy.audit.title} description={copy.audit.description} />
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_340px]">
        <SurfaceCard className="space-y-3">
          {copy.audit.events.map((event) => (
            <div key={`${event.title}-${event.time}`} className="rounded-2xl border border-border bg-surface-muted/50 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <StatusBadge tone={event.tone as StatusTone}>{event.actor}</StatusBadge>
                  <h3 className="mt-3 text-sm font-black text-foreground">{event.title}</h3>
                  <p className="mt-1 text-sm leading-6 text-muted-foreground">{event.description}</p>
                </div>
                <span className="text-xs font-bold text-muted-foreground">{event.time}</span>
              </div>
            </div>
          ))}
        </SurfaceCard>
        <SurfaceCard variant="elevated" className="space-y-4">
          <StatusBadge tone="info">{copy.audit.coverage}</StatusBadge>
          {copy.audit.readiness.map((item) => (
            <div key={item.label} className="space-y-2">
              <div className="flex items-center justify-between text-xs font-bold text-muted-foreground"><span>{item.label}</span><span>{item.value}%</span></div>
              <div className="h-2 overflow-hidden rounded-full bg-surface-muted"><div className="h-full rounded-full bg-primary" style={{width: `${item.value}%`}} /></div>
            </div>
          ))}
        </SurfaceCard>
      </div>
    </div>
  );
}

export function EmployerSettingsPage({locale = 'tr'}: {locale?: string}) {
  const [activeTab, setActiveTab] = useState<SettingsTab>('company');
  const readinessScore = useMemo(() => Math.round((94 + 88 + 82 + 76) / 4), []);

  return (
    <div className="space-y-6 pb-10">
      <SettingsHero locale={locale} score={readinessScore} />
      <div className="grid gap-6 lg:grid-cols-[300px_minmax(0,1fr)]">
        <aside><TabNavigation locale={locale} activeTab={activeTab} onChange={setActiveTab} /></aside>
        <main className="min-w-0">
          {activeTab === 'company' ? <CompanySettings locale={locale} /> : null}
          {activeTab === 'team' ? <TeamSettings locale={locale} /> : null}
          {activeTab === 'security' ? <SecuritySettings locale={locale} /> : null}
          {activeTab === 'notifications' ? <NotificationsSettings locale={locale} /> : null}
          {activeTab === 'brand' ? <BrandSettings locale={locale} /> : null}
          {activeTab === 'integrations' ? <IntegrationsSettings locale={locale} /> : null}
          {activeTab === 'audit' ? <AuditSettings locale={locale} /> : null}
        </main>
      </div>
    </div>
  );
}
