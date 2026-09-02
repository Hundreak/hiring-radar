'use client';

import {useEffect, useMemo, useState} from 'react';
import {useParams} from 'next/navigation';
import {BellRing, BriefcaseBusiness, Clock3, MailCheck, Megaphone, ShieldCheck, type LucideIcon} from 'lucide-react';

import {SettingsSection} from '@/components/settings/settings-section';
import {FeedbackBanner} from '@/components/ui/feedback-banner';
import {Badge} from '@/components/ui/badge';
import {Button} from '@/components/ui/button';
import {api, ApiError} from '@/lib/api';
import type {SupportedLocale, UpdateUserNotificationPreferenceRequest, UserNotificationPreference} from '@/types/user';

type ChannelKey = 'job_digest_enabled' | 'employer_messages_enabled' | 'product_updates_enabled' | 'security_alerts_enabled';

type NotificationDraft = {
  job_digest_enabled: boolean;
  product_updates_enabled: boolean;
  employer_messages_enabled: boolean;
  security_alerts_enabled: boolean;
  quiet_hours_enabled: boolean;
  quiet_hours_start: string;
  quiet_hours_end: string;
  timezone: string;
};

const defaultDraft: NotificationDraft = {
  job_digest_enabled: true,
  product_updates_enabled: false,
  employer_messages_enabled: true,
  security_alerts_enabled: true,
  quiet_hours_enabled: false,
  quiet_hours_start: '22:00',
  quiet_hours_end: '08:00',
  timezone: 'Europe/Istanbul',
};

const copy: Record<SupportedLocale, {
  title: string;
  description: string;
  centerEyebrow: string;
  centerTitle: string;
  centerBody: string;
  enabled: string;
  disabled: string;
  locked: string;
  save: string;
  saving: string;
  saved: string;
  saveError: string;
  loading: string;
  loadingError: string;
  retry: string;
  quietTitle: string;
  quietBody: string;
  quietStart: string;
  quietEnd: string;
  timezone: string;
  digestTitle: string;
  digestBody: string;
  employerTitle: string;
  employerBody: string;
  productTitle: string;
  productBody: string;
  securityTitle: string;
  securityBody: string;
  summaryTitle: string;
  activeChannels: string;
  mutedChannels: string;
  quietSummary: string;
  alwaysOn: string;
}> = {
  tr: {
    title: 'Bildirimler',
    description: 'İş eşleşmesi, işveren mesajları, ürün duyuruları ve güvenlik iletişimlerini tek merkezden yönet.',
    centerEyebrow: 'İletişim kontrol merkezi',
    centerTitle: 'Hangi mesajı ne zaman almak istediğine sen karar ver.',
    centerBody: 'Güvenlik uyarıları kritik hesap olayları için açık kalır; diğer kanalları ihtiyacına göre sadeleştirebilirsin.',
    enabled: 'Açık',
    disabled: 'Kapalı',
    locked: 'Zorunlu',
    save: 'Tercihleri kaydet',
    saving: 'Kaydediliyor...',
    saved: 'Bildirim tercihlerin güncellendi.',
    saveError: 'Bildirim tercihleri kaydedilemedi.',
    loading: 'Bildirim tercihlerin yükleniyor...',
    loadingError: 'Bildirim tercihleri yüklenemedi.',
    retry: 'Tekrar dene',
    quietTitle: 'Sessiz saatler',
    quietBody: 'Sessiz saatlerde ürün ve iş akışı bildirimleri ertelenir; güvenlik uyarıları gecikmez.',
    quietStart: 'Başlangıç',
    quietEnd: 'Bitiş',
    timezone: 'Saat dilimi',
    digestTitle: 'Yeni ilan özeti',
    digestBody: 'Profiline ve filtrelerine uygun yeni ilanlar için özet e-posta al.',
    employerTitle: 'İşveren mesajları',
    employerBody: 'İşveren ilgisi, aday havuzu güncellemeleri ve pipeline mesajları.',
    productTitle: 'Ürün duyuruları',
    productBody: 'Yeni özellikler, iyileştirmeler ve önemli platform haberleri.',
    securityTitle: 'Güvenlik uyarıları',
    securityBody: 'Yeni giriş, şifre değişimi ve kritik hesap güvenliği olayları.',
    summaryTitle: 'Tercih özeti',
    activeChannels: 'aktif kanal',
    mutedChannels: 'kapalı kanal',
    quietSummary: 'sessiz saat açık',
    alwaysOn: 'her zaman açık',
  },
  en: {
    title: 'Notifications',
    description: 'Control job-match, employer-message, product and security communications from one place.',
    centerEyebrow: 'Communication control center',
    centerTitle: 'Choose which messages deserve your attention and when.',
    centerBody: 'Security alerts stay on for critical account events; the other channels can be tuned to your workflow.',
    enabled: 'Enabled',
    disabled: 'Disabled',
    locked: 'Required',
    save: 'Save preferences',
    saving: 'Saving...',
    saved: 'Notification preferences updated.',
    saveError: 'Notification preferences could not be saved.',
    loading: 'Loading notification preferences...',
    loadingError: 'We could not load your notification preferences.',
    retry: 'Try again',
    quietTitle: 'Quiet hours',
    quietBody: 'Product and workflow notifications are deferred during quiet hours; security alerts are not delayed.',
    quietStart: 'Start',
    quietEnd: 'End',
    timezone: 'Timezone',
    digestTitle: 'New job digest',
    digestBody: 'Receive summary emails for new jobs that fit your profile and filters.',
    employerTitle: 'Employer messages',
    employerBody: 'Employer interest, talent-pool updates and pipeline messages.',
    productTitle: 'Product updates',
    productBody: 'New features, improvements and important platform announcements.',
    securityTitle: 'Security alerts',
    securityBody: 'New sign-ins, password changes and critical account security events.',
    summaryTitle: 'Preference summary',
    activeChannels: 'active channels',
    mutedChannels: 'muted channels',
    quietSummary: 'quiet hours on',
    alwaysOn: 'always on',
  },
  de: {
    title: 'Benachrichtigungen',
    description: 'Steuere Job-Matches, Arbeitgeber-Nachrichten, Produkt- und Sicherheitskommunikation an einem Ort.',
    centerEyebrow: 'Kommunikationszentrale',
    centerTitle: 'Entscheide, welche Nachrichten deine Aufmerksamkeit verdienen und wann.',
    centerBody: 'Sicherheitswarnungen bleiben für kritische Kontoereignisse aktiv; andere Kanäle kannst du anpassen.',
    enabled: 'Aktiv',
    disabled: 'Inaktiv',
    locked: 'Pflicht',
    save: 'Einstellungen speichern',
    saving: 'Wird gespeichert...',
    saved: 'Benachrichtigungseinstellungen aktualisiert.',
    saveError: 'Benachrichtigungseinstellungen konnten nicht gespeichert werden.',
    loading: 'Benachrichtigungseinstellungen werden geladen...',
    loadingError: 'Benachrichtigungseinstellungen konnten nicht geladen werden.',
    retry: 'Erneut versuchen',
    quietTitle: 'Ruhezeiten',
    quietBody: 'Produkt- und Workflow-Benachrichtigungen werden in Ruhezeiten verzögert; Sicherheitswarnungen nicht.',
    quietStart: 'Start',
    quietEnd: 'Ende',
    timezone: 'Zeitzone',
    digestTitle: 'Neue Job-Zusammenfassung',
    digestBody: 'Erhalte E-Mail-Zusammenfassungen für passende neue Stellen.',
    employerTitle: 'Arbeitgeber-Nachrichten',
    employerBody: 'Arbeitgeberinteresse, Talentpool-Updates und Pipeline-Nachrichten.',
    productTitle: 'Produkt-Updates',
    productBody: 'Neue Funktionen, Verbesserungen und wichtige Plattformmeldungen.',
    securityTitle: 'Sicherheitswarnungen',
    securityBody: 'Neue Anmeldungen, Passwortänderungen und kritische Kontosicherheitsereignisse.',
    summaryTitle: 'Zusammenfassung',
    activeChannels: 'aktive Kanäle',
    mutedChannels: 'stumme Kanäle',
    quietSummary: 'Ruhezeiten aktiv',
    alwaysOn: 'immer aktiv',
  },
};

function normalizeLocale(value: string | string[] | undefined): SupportedLocale {
  const resolved = Array.isArray(value) ? value[0] : value;
  if (resolved === 'en' || resolved === 'de') return resolved;
  return 'tr';
}

function toDraft(preference: UserNotificationPreference): NotificationDraft {
  return {
    job_digest_enabled: preference.job_digest_enabled,
    product_updates_enabled: preference.product_updates_enabled,
    employer_messages_enabled: preference.employer_messages_enabled,
    security_alerts_enabled: preference.security_alerts_enabled,
    quiet_hours_enabled: preference.quiet_hours_enabled,
    quiet_hours_start: preference.quiet_hours_start,
    quiet_hours_end: preference.quiet_hours_end,
    timezone: preference.timezone,
  };
}

function ToggleRow({
  title,
  body,
  icon: Icon,
  enabled,
  disabled,
  locked,
  enabledLabel,
  disabledLabel,
  lockedLabel,
  onToggle,
}: {
  title: string;
  body: string;
  icon: LucideIcon;
  enabled: boolean;
  disabled?: boolean;
  locked?: boolean;
  enabledLabel: string;
  disabledLabel: string;
  lockedLabel: string;
  onToggle: () => void;
}) {
  return (
    <div className="flex flex-col gap-4 rounded-3xl border border-border bg-surface-muted px-5 py-4 md:flex-row md:items-center md:justify-between">
      <div className="flex gap-4">
        <span className="inline-flex size-11 shrink-0 items-center justify-center rounded-2xl border border-border bg-background text-primary">
          <Icon className="size-5" />
        </span>
        <div>
          <div className="flex flex-wrap items-center gap-2 font-medium text-foreground">
            {title}
            {locked ? <Badge>{lockedLabel}</Badge> : null}
          </div>
          <div className="mt-1 text-sm text-muted-foreground">{body}</div>
        </div>
      </div>
      <button
        type="button"
        onClick={onToggle}
        disabled={disabled || locked}
        className={`inline-flex items-center justify-between gap-3 rounded-full border px-3 py-2 text-sm font-medium transition ${enabled ? 'border-primary/40 bg-primary/[0.08] text-foreground' : 'border-border bg-background text-muted-foreground'} disabled:cursor-not-allowed disabled:opacity-70`}
      >
        <span>{enabled ? enabledLabel : disabledLabel}</span>
        <span className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition ${enabled ? 'bg-primary/80' : 'bg-muted-foreground/30'}`}>
          <span className={`inline-block size-3.5 rounded-full bg-white shadow transition-transform ${enabled ? 'translate-x-[18px]' : 'translate-x-[2px]'}`} />
        </span>
      </button>
    </div>
  );
}

export default function SettingsNotificationsPage() {
  const params = useParams<{locale: string}>();
  const locale = normalizeLocale(params?.locale);
  const t = copy[locale];

  const [preference, setPreference] = useState<UserNotificationPreference | null>(null);
  const [draft, setDraft] = useState<NotificationDraft>(defaultDraft);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  async function loadPreferences() {
    setLoading(true);
    setError(null);
    try {
      const response = await api.getUserNotificationPreferences();
      setPreference(response);
      setDraft(toDraft(response));
    } catch (requestError) {
      const requestId = requestError instanceof ApiError && requestError.requestId ? ` (${requestError.requestId})` : '';
      setError(`${t.loadingError}${requestId}`);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadPreferences();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locale]);

  const activeChannelCount = useMemo(() => {
    return [draft.job_digest_enabled, draft.employer_messages_enabled, draft.product_updates_enabled, draft.security_alerts_enabled]
      .filter(Boolean)
      .length;
  }, [draft]);

  function toggleChannel(key: ChannelKey) {
    if (key === 'security_alerts_enabled') return;
    setDraft((current) => ({...current, [key]: !current[key]}));
  }

  async function saveNotifications() {
    setStatus(null);
    setError(null);
    setSaving(true);
    try {
      const payload: UpdateUserNotificationPreferenceRequest = {
        ...draft,
        security_alerts_enabled: true,
      };
      const response = await api.updateUserNotificationPreferences(payload);
      setPreference(response);
      setDraft(toDraft(response));
      setStatus(t.saved);
    } catch (requestError) {
      const requestId = requestError instanceof ApiError && requestError.requestId ? ` (${requestError.requestId})` : '';
      setError(`${t.saveError}${requestId}`);
    } finally {
      setSaving(false);
    }
  }

  const channels: Array<{key: ChannelKey; title: string; body: string; icon: LucideIcon; locked?: boolean}> = [
    {key: 'job_digest_enabled', title: t.digestTitle, body: t.digestBody, icon: MailCheck},
    {key: 'employer_messages_enabled', title: t.employerTitle, body: t.employerBody, icon: BriefcaseBusiness},
    {key: 'product_updates_enabled', title: t.productTitle, body: t.productBody, icon: Megaphone},
    {key: 'security_alerts_enabled', title: t.securityTitle, body: t.securityBody, icon: ShieldCheck, locked: true},
  ];

  if (loading) {
    return (
      <SettingsSection title={t.title} description={t.description}>
        <div className="rounded-3xl border border-border bg-surface-muted p-6 text-sm text-muted-foreground">{t.loading}</div>
      </SettingsSection>
    );
  }

  return (
    <div className="space-y-6">
      <SettingsSection title={t.title} description={t.description}>
        <div className="rounded-[32px] border border-border bg-gradient-to-br from-primary/[0.09] via-surface-muted to-background p-6">
          <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary">{t.centerEyebrow}</div>
          <div className="mt-3 max-w-2xl text-2xl font-semibold text-foreground">{t.centerTitle}</div>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">{t.centerBody}</p>
          <div className="mt-5 flex flex-wrap gap-2">
            <Badge>{activeChannelCount} {t.activeChannels}</Badge>
            <Badge>{4 - activeChannelCount} {t.mutedChannels}</Badge>
            <Badge>{draft.quiet_hours_enabled ? t.quietSummary : t.alwaysOn}</Badge>
          </div>
        </div>
      </SettingsSection>

      <SettingsSection title={t.summaryTitle} description={preference?.updated_at ? preference.updated_at : undefined}>
        <div className="space-y-4">
          {channels.map((item) => (
            <ToggleRow
              key={item.key}
              title={item.title}
              body={item.body}
              icon={item.icon}
              enabled={draft[item.key]}
              locked={item.locked}
              disabled={saving}
              enabledLabel={t.enabled}
              disabledLabel={t.disabled}
              lockedLabel={t.locked}
              onToggle={() => toggleChannel(item.key)}
            />
          ))}
        </div>
      </SettingsSection>

      <SettingsSection title={t.quietTitle} description={t.quietBody}>
        <div className="grid gap-4 rounded-3xl border border-border bg-surface-muted p-5 md:grid-cols-[1.2fr_1fr_1fr_1.2fr] md:items-end">
          <label className="flex items-center justify-between gap-3 rounded-2xl border border-border bg-background px-4 py-3 text-sm font-medium">
            <span className="inline-flex items-center gap-2"><Clock3 className="size-4 text-primary" /> {t.quietTitle}</span>
            <input
              type="checkbox"
              checked={draft.quiet_hours_enabled}
              onChange={() => setDraft((current) => ({...current, quiet_hours_enabled: !current.quiet_hours_enabled}))}
            />
          </label>
          <label className="space-y-2 text-sm">
            <span className="font-medium text-foreground">{t.quietStart}</span>
            <input
              type="time"
              value={draft.quiet_hours_start}
              onChange={(event) => setDraft((current) => ({...current, quiet_hours_start: event.target.value}))}
              className="w-full rounded-2xl border border-border bg-background px-4 py-3 text-sm outline-none focus:border-primary/60"
            />
          </label>
          <label className="space-y-2 text-sm">
            <span className="font-medium text-foreground">{t.quietEnd}</span>
            <input
              type="time"
              value={draft.quiet_hours_end}
              onChange={(event) => setDraft((current) => ({...current, quiet_hours_end: event.target.value}))}
              className="w-full rounded-2xl border border-border bg-background px-4 py-3 text-sm outline-none focus:border-primary/60"
            />
          </label>
          <label className="space-y-2 text-sm">
            <span className="font-medium text-foreground">{t.timezone}</span>
            <input
              type="text"
              value={draft.timezone}
              onChange={(event) => setDraft((current) => ({...current, timezone: event.target.value}))}
              className="w-full rounded-2xl border border-border bg-background px-4 py-3 text-sm outline-none focus:border-primary/60"
            />
          </label>
        </div>

        <div className="mt-6 space-y-3">
          <Button onClick={saveNotifications} disabled={saving}>
            <BellRing className="mr-2 size-4" />
            {saving ? t.saving : t.save}
          </Button>
          {status ? (
            <FeedbackBanner tone="success" onDismiss={() => setStatus(null)}>
              {status}
            </FeedbackBanner>
          ) : null}
          {error ? (
            <FeedbackBanner tone="error" onDismiss={() => setError(null)}>
              <span className="mr-3">{error}</span>
              <button type="button" className="font-semibold underline" onClick={() => void loadPreferences()}>
                {t.retry}
              </button>
            </FeedbackBanner>
          ) : null}
        </div>
      </SettingsSection>
    </div>
  );
}
