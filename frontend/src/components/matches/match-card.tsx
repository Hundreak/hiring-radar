'use client';

import {Bookmark} from 'lucide-react';
import {useTranslations} from 'next-intl';

import {Badge} from '@/components/ui/badge';

export type MatchCardModel = {
  id: string;
  title: string;
  company: string;
  location: string;
  matchScore: number;
  postedLabel: string;
  contractType: string;
  matchedKeywords: string[];
  href?: string;
  saved?: boolean;
  onToggleSave?: () => void;
};

function scoreColor(score: number) {
  if (score >= 80) return {ring: 'border-match-high bg-match-high/10', text: 'text-match-high', fill: 'bg-match-high'};
  if (score >= 60) return {ring: 'border-match-mid bg-match-mid/10', text: 'text-match-mid', fill: 'bg-match-mid'};
  return {ring: 'border-match-low bg-match-low/10', text: 'text-match-low', fill: 'bg-match-low'};
}

export function MatchCard({match}: {match: MatchCardModel}) {
  const t = useTranslations('matches');
  const colors = scoreColor(match.matchScore);

  return (
    <div
      className={`flex flex-col rounded-xl border transition cursor-pointer ${
        match.matchScore >= 80
          ? 'border-primary/30 bg-primary/[0.04] hover:border-primary/50'
          : 'border-border bg-surface hover:border-primary/30'
      }`}
    >
      <div className="flex flex-col gap-2.5 p-4">
        {/* Header with score ring */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <div
              className={`flex size-11 shrink-0 items-center justify-center rounded-full border-2 ${colors.ring}`}
            >
              <span className={`text-[13px] font-bold ${colors.text}`}>
                {match.matchScore}%
              </span>
            </div>
            <div className="min-w-0">
              <h3 className="text-[13px] font-medium leading-snug text-foreground">
                {match.title}
              </h3>
              <p className="text-[11px] text-muted-foreground">
                {match.company} · {match.location}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              match.onToggleSave?.();
            }}
            className={`flex size-[26px] shrink-0 items-center justify-center rounded-md border transition ${
              match.saved
                ? 'border-primary/40 bg-primary/20 text-primary'
                : 'border-border bg-surface-muted text-muted-foreground hover:bg-surface-strong'
            }`}
          >
            <Bookmark className="size-3" />
          </button>
        </div>

        {/* Skill bars */}
        {match.matchedKeywords.length > 0 && (
          <div>
            <div className="mb-1 text-[10px] text-muted-foreground">
              {t('skillMatch')}
            </div>
            {match.matchedKeywords.slice(0, 3).map((kw, i) => {
              const pct = Math.max(40, 95 - i * 12);
              const barColor =
                pct >= 80 ? 'bg-match-high' : pct >= 60 ? 'bg-match-mid' : 'bg-match-low';
              return (
                <div key={kw} className="mb-0.5 flex items-center gap-2">
                  <span className="min-w-[72px] shrink-0 text-[11px] text-muted-foreground">
                    {kw}
                  </span>
                  <div className="h-[3px] flex-1 rounded-full bg-border">
                    <div
                      className={`h-[3px] rounded-full ${barColor}`}
                      style={{width: `${pct}%`}}
                    />
                  </div>
                  <span className="min-w-[24px] text-right text-[10px] text-muted-foreground">
                    {pct}%
                  </span>
                </div>
              );
            })}
          </div>
        )}

        {/* Tags */}
        <div className="flex flex-wrap gap-1">
          {match.matchedKeywords.slice(0, 2).map((kw) => (
            <Badge key={kw} tone="matched" className="rounded px-1.5 py-0.5 text-[10px]">
              {kw} {t('skillMatch').toLowerCase().includes('eşleşti') ? '' : '✓'}
            </Badge>
          ))}
          {match.location.toLowerCase().includes('remote') && (
            <Badge tone="remote" className="rounded px-1.5 py-0.5 text-[10px]">
              Remote
            </Badge>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-border/50 pt-2">
          <span className="text-[10px] text-muted-foreground">
            {match.postedLabel}
          </span>
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              className="rounded-md border border-border px-2.5 py-1 text-[11px] text-muted-foreground hover:bg-surface-muted"
            >
              {t('detail')}
            </button>
            {match.href ? (
              <a
                href={match.href}
                target="_blank"
                rel="noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="rounded-md bg-primary px-3 py-1 text-[11px] font-medium text-primary-foreground hover:bg-primary/90"
              >
                {t('apply')}
              </a>
            ) : (
              <button
                type="button"
                className="rounded-md bg-primary px-3 py-1 text-[11px] font-medium text-primary-foreground hover:bg-primary/90"
              >
                {t('apply')}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
