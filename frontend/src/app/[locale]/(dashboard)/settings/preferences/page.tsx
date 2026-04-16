'use client';

import {useEffect, useMemo, useState} from 'react';
import {useTranslations} from 'next-intl';

import {SettingsField} from '@/components/settings/field';
import {SettingsSection} from '@/components/settings/settings-section';
import {Badge} from '@/components/ui/badge';
import {Button} from '@/components/ui/button';
import {Input} from '@/components/ui/input';
import {api} from '@/lib/api';
import type {
  KeywordPreferencePreviewResponse,
  UserKeywordPreference
} from '@/types/user';

function splitKeywords(value: string) {
  return value
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function SettingsPreferencesPage() {
  const t = useTranslations('settings.preferences');
  const [preference, setPreference] = useState<UserKeywordPreference | null>(null);
  const [includeKeywords, setIncludeKeywords] = useState('');
  const [excludeKeywords, setExcludeKeywords] = useState('');
  const [matchTitle, setMatchTitle] = useState(true);
  const [matchLocation, setMatchLocation] = useState(true);
  const [matchCompanyName, setMatchCompanyName] = useState(true);
  const [preview, setPreview] = useState<KeywordPreferencePreviewResponse | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getKeywordPreferences()
      .then((response) => {
        setPreference(response);
        setIncludeKeywords(response.include_keywords.join('\n'));
        setExcludeKeywords(response.exclude_keywords.join('\n'));
        setMatchTitle(response.match_title);
        setMatchLocation(response.match_location);
        setMatchCompanyName(response.match_company_name);
      })
      .catch((reason: Error) => setError(reason.message));
  }, []);

  const keywordTags = useMemo(() => {
    return [
      ...splitKeywords(includeKeywords).map((value) => ({
        tone: 'accent' as const,
        label: `+ ${value}`
      })),
      ...splitKeywords(excludeKeywords).map((value) => ({
        tone: 'default' as const,
        label: `- ${value}`
      }))
    ];
  }, [excludeKeywords, includeKeywords]);

  function payload() {
    return {
      include_keywords: splitKeywords(includeKeywords),
      exclude_keywords: splitKeywords(excludeKeywords),
      match_title: matchTitle,
      match_location: matchLocation,
      match_company_name: matchCompanyName
    };
  }

  async function savePreferences() {
    setStatus(null);
    setError(null);

    try {
      const response = await api.updateKeywordPreferences(payload());
      setPreference(response);
      setStatus('Matching preferences saved successfully.');
    } catch (reason) {
      const message = reason instanceof Error ? reason.message : 'Save failed.';
      setError(message);
    }
  }

  async function runPreview() {
    setStatus(null);
    setError(null);

    try {
      const response = await api.previewKeywordPreferences({
        keyword_preference: payload(),
        active_only: true,
        sample_limit: 5
      });
      setPreview(response);
      setStatus('Preview refreshed.');
    } catch (reason) {
      const message = reason instanceof Error ? reason.message : 'Preview failed.';
      setError(message);
    }
  }

  return (
    <div className="space-y-6">
      <SettingsSection title={t('title')} description={t('description')}>
        <SettingsField label={t('skillsLabel')} hint={t('skillsHint')}>
          <textarea
            className="min-h-28 w-full rounded-2xl border border-border bg-surface px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary/15"
            placeholder={t('skillsPlaceholder')}
            value={includeKeywords}
            onChange={(event) => setIncludeKeywords(event.target.value)}
          />
        </SettingsField>

        <SettingsField label="Exclude keywords">
          <textarea
            className="min-h-28 w-full rounded-2xl border border-border bg-surface px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary/15"
            placeholder="intern, sales, onsite only"
            value={excludeKeywords}
            onChange={(event) => setExcludeKeywords(event.target.value)}
          />
        </SettingsField>

        <div className="flex flex-wrap gap-2">
          {keywordTags.length ? (
            keywordTags.map((tag) => (
              <Badge key={tag.label} tone={tag.tone}>
                {tag.label}
              </Badge>
            ))
          ) : (
            <Badge>No saved keywords yet</Badge>
          )}
        </div>

        <div className="grid gap-3 rounded-3xl border border-border bg-surface-muted p-5 text-sm text-muted-foreground md:grid-cols-3">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={matchTitle}
              onChange={() => setMatchTitle((value) => !value)}
            />
            Title
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={matchLocation}
              onChange={() => setMatchLocation((value) => !value)}
            />
            Location
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={matchCompanyName}
              onChange={() => setMatchCompanyName((value) => !value)}
            />
            Company name
          </label>
        </div>

        <SettingsField label={t('locationsLabel')}>
          <Input placeholder={t('locationsPlaceholder')} disabled />
        </SettingsField>

        <div className="rounded-3xl border border-border bg-surface-muted p-5 text-sm text-muted-foreground">
          {t('matchingHelp')}
        </div>

        {preview ? (
          <div className="grid gap-4 rounded-3xl border border-border bg-surface-muted p-5 md:grid-cols-3">
            <div>
              <div className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                Passed
              </div>
              <div className="mt-2 text-2xl font-semibold">{preview.passed_jobs}</div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                Rejected
              </div>
              <div className="mt-2 text-2xl font-semibold">{preview.rejected_jobs}</div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                Active fields
              </div>
              <div className="mt-2 text-sm font-medium">
                {preview.active_fields.join(', ') || '—'}
              </div>
            </div>
          </div>
        ) : null}

        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={savePreferences}>{t('saveButton')}</Button>
          <Button variant="secondary" onClick={runPreview}>
            Preview matches
          </Button>
          {status ? <span className="text-sm text-emerald-600">{status}</span> : null}
          {error ? <span className="text-sm text-rose-600">{error}</span> : null}
        </div>

        {preference ? (
          <div className="text-xs text-muted-foreground">
            Current profile status: {preference.enabled ? 'Active' : 'Idle'}
          </div>
        ) : null}
      </SettingsSection>
    </div>
  );
}
