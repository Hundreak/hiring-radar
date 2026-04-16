import {CheckCircle2, CircleDashed} from 'lucide-react';
import {getTranslations} from 'next-intl/server';

import {Card} from '@/components/ui/card';
import {profileChecklist} from '@/lib/demo-data';
import {getProfileCompletion} from '@/lib/profile';
import {formatPercent} from '@/lib/utils';

export async function ProfileCompletionCard({locale}: {locale: string}) {
  const t = await getTranslations({locale, namespace: 'profile'});
  const completion = getProfileCompletion();

  return (
    <Card className="p-6">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <div className="text-sm font-semibold">{t('completion.title')}</div>
          <p className="mt-1 text-sm text-muted-foreground">{t('completion.description')}</p>
        </div>
        <div className="rounded-2xl bg-accent-soft px-3 py-2 text-sm font-bold text-accent">
          {formatPercent(completion)}
        </div>
      </div>

      <div className="mb-5 h-2 overflow-hidden rounded-full bg-surface-strong">
        <div className="h-full rounded-full bg-primary" style={{width: `${completion}%`}} />
      </div>

      <div className="space-y-3">
        {profileChecklist.map((item) => (
          <div key={item.id} className="flex items-center justify-between gap-3 text-sm">
            <span className="text-muted-foreground">{item.label}</span>
            {item.complete ? (
              <CheckCircle2 className="size-4 text-success" />
            ) : (
              <CircleDashed className="size-4 text-warning" />
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}
