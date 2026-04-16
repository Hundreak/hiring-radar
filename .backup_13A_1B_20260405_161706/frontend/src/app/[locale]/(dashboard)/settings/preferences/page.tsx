import {getTranslations} from 'next-intl/server';

import {SettingsField} from '@/components/settings/field';
import {SettingsSection} from '@/components/settings/settings-section';
import {Badge} from '@/components/ui/badge';
import {Button} from '@/components/ui/button';
import {Input} from '@/components/ui/input';

export default async function SettingsPreferencesPage({
  params
}: {
  params: Promise<{locale: string}>;
}) {
  const {locale} = await params;
  const t = await getTranslations({locale, namespace: 'settings.preferences'});

  return (
    <div className="space-y-6">
      <SettingsSection title={t('title')} description={t('description')}>
        <SettingsField label={t('skillsLabel')} hint={t('skillsHint')}>
          <Input placeholder={t('skillsPlaceholder')} />
        </SettingsField>

        <div className="flex flex-wrap gap-2">
          {['React', 'TypeScript', 'FastAPI', 'Python'].map((tag) => (
            <Badge key={tag} tone="accent">
              {tag}
            </Badge>
          ))}
        </div>

        <SettingsField label={t('locationsLabel')}>
          <Input placeholder={t('locationsPlaceholder')} />
        </SettingsField>

        <div className="rounded-3xl border border-border bg-surface-muted p-5 text-sm text-muted-foreground">
          {t('matchingHelp')}
        </div>

        <Button>{t('saveButton')}</Button>
      </SettingsSection>
    </div>
  );
}
