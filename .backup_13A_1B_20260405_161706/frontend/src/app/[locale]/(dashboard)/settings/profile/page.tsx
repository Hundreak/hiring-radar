import {getTranslations} from 'next-intl/server';

import {SettingsField} from '@/components/settings/field';
import {SettingsSection} from '@/components/settings/settings-section';
import {Button} from '@/components/ui/button';
import {Input} from '@/components/ui/input';

export default async function SettingsProfilePage({
  params
}: {
  params: Promise<{locale: string}>;
}) {
  const {locale} = await params;
  const t = await getTranslations({locale, namespace: 'settings.profile'});

  return (
    <div className="space-y-6">
      <SettingsSection title={t('title')} description={t('description')}>
        <SettingsField label={t('fields.fullName.label')}>
          <Input defaultValue="Remzi Altunay" />
        </SettingsField>
        <SettingsField label={t('fields.email.label')} hint={t('fields.email.hint')}>
          <Input defaultValue="remzialtunay095@gmail.com" disabled />
        </SettingsField>
        <SettingsField label={t('fields.phone.label')} hint={t('fields.phone.hint')}>
          <Input placeholder="+90 5xx xxx xx xx" />
        </SettingsField>
        <SettingsField label={t('fields.headline.label')} hint={t('fields.headline.hint')}>
          <Input placeholder={t('fields.headline.placeholder')} />
        </SettingsField>
      </SettingsSection>

      <SettingsSection title={t('education.title')} description={t('education.description')}>
        <div className="rounded-3xl border border-border bg-surface-muted p-5">
          <div className="font-semibold">B.Sc. Electrical & Electronics Engineering</div>
          <div className="mt-1 text-sm text-muted-foreground">
            Example University · 2020 – 2024
          </div>
        </div>
        <Button variant="secondary">{t('education.add')}</Button>
      </SettingsSection>
    </div>
  );
}
