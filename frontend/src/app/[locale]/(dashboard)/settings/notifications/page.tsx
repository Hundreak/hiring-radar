'use client';

import {useEffect, useState} from 'react';
import {useParams, useRouter} from 'next/navigation';
import {BellRing, LogOut} from 'lucide-react';

import {SettingsSection} from '@/components/settings/settings-section';
import {FeedbackBanner} from '@/components/ui/feedback-banner';
import {Badge} from '@/components/ui/badge';
import {Button} from '@/components/ui/button';
import {api} from '@/lib/api';
import type {SupportedLocale, UserProfile} from '@/types/user';

const copy: Record<SupportedLocale, {
  title: string;
  description: string;
  digestTitle: string;
  digestBody: string;
  enabled: string;
  disabled: string;
  upcoming: string;
  save: string;
  saving: string;
  saved: string;
  saveError: string;
  signoutTitle: string;
  signoutBody: string;
  signoutButton: string;
  signingOut: string;
  signoutError: string;
  loadingError: string;
}> = {
  tr: {
    title: 'Bildirimler',
    description: 'E-posta akışlarını sade şekilde yönet ve hesabından güvenle çıkış yap.',
    digestTitle: 'Yeni ilan özeti',
    digestBody: 'Sana uygun görünen yeni ilanlar için özet e-postaları aç veya kapat.',
    enabled: 'Açık',
    disabled: 'Kapalı',
    upcoming: 'Sonraki faz',
    save: 'Bildirim tercihlerini kaydet',
    saving: 'Kaydediliyor...',
    saved: 'Bildirim tercihlerin güncellendi.',
    saveError: 'Bildirim tercihleri kaydedilemedi.',
    signoutTitle: 'Oturumu kapat',
    signoutBody: 'Bu cihazdaki oturumunu kapatmak için aşağıdaki butonu kullanabilirsin.',
    signoutButton: 'Çıkış Yap',
    signingOut: 'Çıkış yapılıyor...',
    signoutError: 'Çıkış işlemi tamamlanamadı. Lütfen tekrar dene.',
    loadingError: 'Bildirim ayarları yüklenemedi. Sayfayı yenileyip tekrar dene.',
  },
  en: {
    title: 'Notifications',
    description: 'Manage your email flow and sign out safely from this device.',
    digestTitle: 'New job digest',
    digestBody: 'Turn summary emails for relevant new jobs on or off.',
    enabled: 'Enabled',
    disabled: 'Disabled',
    upcoming: 'Next phase',
    save: 'Save notification settings',
    saving: 'Saving...',
    saved: 'Notification preferences updated.',
    saveError: 'Notification preferences could not be saved.',
    signoutTitle: 'Sign out',
    signoutBody: 'Use the button below to safely sign out of this device.',
    signoutButton: 'Log out',
    signingOut: 'Logging out...',
    signoutError: 'We could not sign you out right now. Please try again.',
    loadingError: 'We could not load your notification settings. Please refresh the page and try again.',
  },
  de: {
    title: 'Benachrichtigungen',
    description: 'Verwalte deinen E-Mail-Fluss und melde dich sicher von diesem Gerät ab.',
    digestTitle: 'Neue Job-Zusammenfassung',
    digestBody: 'Aktiviere oder deaktiviere E-Mail-Zusammenfassungen für passende neue Stellen.',
    enabled: 'Aktiv',
    disabled: 'Inaktiv',
    upcoming: 'Nächste Phase',
    save: 'Benachrichtigungen speichern',
    saving: 'Wird gespeichert...',
    saved: 'Deine Benachrichtigungseinstellungen wurden aktualisiert.',
    saveError: 'Die Einstellungen konnten nicht gespeichert werden.',
    signoutTitle: 'Abmelden',
    signoutBody: 'Mit dem folgenden Button meldest du dich sicher von diesem Gerät ab.',
    signoutButton: 'Abmelden',
    signingOut: 'Abmeldung läuft...',
    signoutError: 'Die Abmeldung konnte nicht abgeschlossen werden. Bitte versuche es erneut.',
    loadingError: 'Deine Benachrichtigungseinstellungen konnten nicht geladen werden. Bitte aktualisiere die Seite und versuche es erneut.',
  },
};

function normalizeLocale(value: string | string[] | undefined): SupportedLocale {
  const resolved = Array.isArray(value) ? value[0] : value;
  if (resolved === 'en' || resolved === 'de') return resolved;
  return 'tr';
}

export default function SettingsNotificationsPage() {
  const params = useParams<{locale: string}>();
  const router = useRouter();
  const locale = normalizeLocale(params?.locale);
  const t = copy[locale];

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [digestEnabled, setDigestEnabled] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);

  useEffect(() => {
    api.getProfile()
      .then((response) => {
        setProfile(response);
        setDigestEnabled(response.digest_enabled);
      })
      .catch(() => setError(t.loadingError));
  }, [t.loadingError]);

  async function saveNotifications() {
    if (!profile) return;

    setStatus(null);
    setError(null);
    setSaving(true);
    try {
      const response = await api.updateProfile({digest_enabled: digestEnabled});
      setProfile(response);
      setStatus(t.saved);
    } catch {
      setError(t.saveError);
    } finally {
      setSaving(false);
    }
  }

  async function signOut() {
    try {
      setLoggingOut(true);
      setError(null);
      await api.logout();
      router.push(`/${locale}/login`);
      router.refresh();
    } catch {
      setError(t.signoutError);
    } finally {
      setLoggingOut(false);
    }
  }

  return (
    <div className="space-y-6">
      <SettingsSection title={t.title} description={t.description}>
        <div className="space-y-4">
          <div className="flex flex-col gap-4 rounded-3xl border border-border bg-surface-muted px-5 py-4 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="font-medium">{t.digestTitle}</div>
              <div className="mt-1 text-sm text-muted-foreground">{t.digestBody}</div>
            </div>
            <label className="inline-flex items-center gap-3 text-sm font-medium text-foreground">
              <input type="checkbox" checked={digestEnabled} onChange={() => setDigestEnabled((value) => !value)} />
              {digestEnabled ? t.enabled : t.disabled}
            </label>
          </div>

          <div className="flex items-center justify-between rounded-3xl border border-border bg-surface-muted px-5 py-4 opacity-70">
            <div className="font-medium">Akıllı bildirim filtreleri</div>
            <Badge>{t.upcoming}</Badge>
          </div>

          <div className="flex items-center justify-between rounded-3xl border border-border bg-surface-muted px-5 py-4 opacity-70">
            <div className="font-medium">Sessiz saatler</div>
            <Badge>{t.upcoming}</Badge>
          </div>
        </div>

        <div className="mt-6 space-y-3">
          <div className="flex flex-wrap items-center gap-3">
            <Button onClick={saveNotifications} disabled={saving || loggingOut}>
              <BellRing className="mr-2 size-4" />
              {saving ? t.saving : t.save}
            </Button>
          </div>
          {status ? (
            <FeedbackBanner tone="success" onDismiss={() => setStatus(null)}>
              {status}
            </FeedbackBanner>
          ) : null}
          {error ? (
            <FeedbackBanner tone="error" onDismiss={() => setError(null)}>
              {error}
            </FeedbackBanner>
          ) : null}
        </div>
      </SettingsSection>

      <SettingsSection title={t.signoutTitle} description={t.signoutBody}>
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-border bg-surface-muted px-5 py-4">
          <div>
            <div className="font-medium">{t.signoutTitle}</div>
            <div className="mt-1 text-sm text-muted-foreground">{t.signoutBody}</div>
          </div>
          <Button
            variant="secondary"
            onClick={() => void signOut()}
            disabled={loggingOut}
            className="border-rose-200 text-rose-600 hover:bg-rose-50 hover:text-rose-700"
          >
            <LogOut className="mr-2 size-4" />
            {loggingOut ? t.signingOut : t.signoutButton}
          </Button>
        </div>
      </SettingsSection>
    </div>
  );
}
