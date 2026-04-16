import {SlidersHorizontal} from 'lucide-react';
import {getTranslations} from 'next-intl/server';

import {JobCard} from '@/components/jobs/job-card';
import {ProfileCompletionCard} from '@/components/profile/profile-completion-card';
import {Badge} from '@/components/ui/badge';
import {Button} from '@/components/ui/button';
import {Card} from '@/components/ui/card';
import {demoJobs} from '@/lib/demo-data';

export default async function JobsPage({
  params
}: {
  params: Promise<{locale: string}>;
}) {
  const {locale} = await params;
  const t = await getTranslations({locale, namespace: 'jobs'});

  return (
    <div className="grid jobs-grid gap-6">
      <div className="space-y-6">
        <ProfileCompletionCard locale={locale} />
        <Card className="p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-[0.2em] text-muted-foreground">
              {t('filtersTitle')}
            </h2>
            <Button variant="ghost" className="gap-2">
              <SlidersHorizontal className="size-4" />
              {t('resetFilters')}
            </Button>
          </div>
          <div className="space-y-4">
            <div>
              <div className="mb-2 text-sm font-medium">{t('quickFilters')}</div>
              <div className="flex flex-wrap gap-2">
                <Badge tone="accent">{t('matchedOnly')}</Badge>
                <Badge>{t('remote')}</Badge>
                <Badge>{t('engineering')}</Badge>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <div className="space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{t('title')}</h1>
            <p className="mt-1 text-sm text-muted-foreground">{t('description')}</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge tone="success">{t('liveFeed')}</Badge>
            <Badge>{t('resultCount', {count: demoJobs.length})}</Badge>
          </div>
        </div>

        <div className="grid gap-4 xl:grid-cols-2">
          {demoJobs.map((job) => (
            <JobCard key={job.id} job={job} />
          ))}
        </div>
      </div>
    </div>
  );
}
