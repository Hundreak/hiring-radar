import {getTranslations} from 'next-intl/server';

import {SettingsSection} from '@/components/settings/settings-section';
import {Badge} from '@/components/ui/badge';
import {Button} from '@/components/ui/button';

export default async function SettingsNotificationsPage({
  params
}: {
  params: Promise<{locale: string}>;
}) {
  const {locale} = await params;
  const t = await getTranslations({locale, namespace: 'settings.notifications'});

  return (
    <div className="space-y-6">
      <SettingsSection title={t('title')} description={t('description')}>
        <div className="space-y-4">
          {[
            t('digest'),
            t('matches'),
            t('quietHours')
          ].map((label, index) => (
            <div
              key={label}
              className="flex items-center justify-between rounded-3xl border border-border bg-surface-muted px-5 py-4"
            >
              <div className="font-medium">{label}</div>
              <Badge tone={index === 2 ? 'default' : 'success'}>
                {index === 2 ? '22:00 – 08:00' : 'Enabled'}
              </Badge>
            </div>
          ))}
        </div>
        <Button>{t('saveButton')}</Button>
      </SettingsSection>
    </div>
  );
}
