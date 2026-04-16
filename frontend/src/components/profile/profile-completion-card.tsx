'use client';

import {CheckCircle2, CircleDashed, CircleDot} from 'lucide-react';
import {useTranslations} from 'next-intl';
import {useEffect, useState} from 'react';

import {Card} from '@/components/ui/card';
import {api} from '@/lib/api';
import {formatPercent} from '@/lib/utils';
import type {ProfileCompletenessSummary, ProfileCompletionSection} from '@/types/profile';

function StatusIcon({status}: {status: ProfileCompletionSection['status']}) {
  if (status === 'done') return <CheckCircle2 className="size-4 text-success" />;
  if (status === 'partial') return <CircleDot className="size-4 text-warning" />;
  return <CircleDashed className="size-4 text-muted-foreground" />;
}

export function ProfileCompletionCard() {
  const t = useTranslations('profile');
  const [completeness, setCompleteness] = useState<ProfileCompletenessSummary | null>(null);

  useEffect(() => {
    let active = true;
    api
      .getUserProfileAggregate()
      .then((res) => {
        if (active) setCompleteness(res.profile.completeness);
      })
      .catch(() => {});
    return () => { active = false; };
  }, []);

  if (!completeness) return null;

  const score = completeness.score;

  return (
    <Card className="p-4">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <div className="text-xs font-semibold">{t('completion.title')}</div>
          <p className="mt-0.5 text-[11px] text-muted-foreground">{t('completion.description')}</p>
        </div>
        <div className="rounded-xl bg-accent-soft px-2.5 py-1.5 text-xs font-bold text-accent">
          {formatPercent(score)}
        </div>
      </div>

      <div className="mb-3 h-1.5 overflow-hidden rounded-full bg-surface-strong">
        <div
          className={`h-full rounded-full transition-all ${
            score >= 80 ? 'bg-success' : score >= 50 ? 'bg-primary' : 'bg-warning'
          }`}
          style={{width: `${score}%`}}
        />
      </div>

      <div className="space-y-2">
        {completeness.sections.map((section) => (
          <div key={section.key} className="flex items-center justify-between gap-2 text-xs">
            <span className="text-muted-foreground">{section.label}</span>
            <StatusIcon status={section.status} />
          </div>
        ))}
      </div>
    </Card>
  );
}
