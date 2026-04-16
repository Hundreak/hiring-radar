import {getTranslations} from 'next-intl/server';

import {JobCard} from '@/components/jobs/job-card';
import {Card} from '@/components/ui/card';
import {demoJobs} from '@/lib/demo-data';

export default async function MatchesPage({
  params
}: {
  params: Promise<{locale: string}>;
}) {
  const {locale} = await params;
  const t = await getTranslations({locale, namespace: 'matches'});
  const matchedJobs = demoJobs.filter((job) => job.matched);

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{t('title')}</h1>
            <p className="mt-1 text-sm text-muted-foreground">{t('description')}</p>
          </div>
          <div className="rounded-2xl bg-accent-soft px-4 py-2 text-sm font-semibold text-accent">
            {t('scoreSummary', {count: matchedJobs.length})}
          </div>
        </div>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        {matchedJobs.map((job) => (
          <JobCard key={job.id} job={job} />
        ))}
      </div>
    </div>
  );
}
