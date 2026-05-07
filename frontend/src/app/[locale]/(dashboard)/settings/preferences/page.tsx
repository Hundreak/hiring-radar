'use client';

import {useEffect, useMemo, useState} from 'react';
import {useTranslations} from 'next-intl';

import {SettingsField} from '@/components/settings/field';
import {SettingsSection} from '@/components/settings/settings-section';
import {Badge} from '@/components/ui/badge';
import {Button} from '@/components/ui/button';
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

function MatchFieldToggle({checked, onChange, label}: {checked: boolean; onChange: () => void; label: string}) {
  return (
    <label className={`flex cursor-pointer items-center justify-between rounded-xl border px-4 py-3 transition ${checked ? 'border-primary/40 bg-primary/[0.06]' : 'border-border bg-surface-muted/40'}`}>
      <span className={`text-sm font-medium ${checked ? 'text-foreground/80' : 'text-muted-foreground'}`}>{label}</span>
      <span className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full border transition ${checked ? 'border-primary/60 bg-primary/80' : 'border-border bg-surface-strong'}`}>
        <span className={`inline-block h-3.5 w-3.5 rounded-full bg-white shadow transition-transform ${checked ? 'translate-x-[18px]' : 'translate-x-[2px]'}`} />
      </span>
      <input type="checkbox" checked={checked} onChange={onChange} className="sr-only" />
    </label>
  );
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

  const includeTags = useMemo(() => splitKeywords(includeKeywords), [includeKeywords]);
  const excludeTags = useMemo(() => splitKeywords(excludeKeywords), [excludeKeywords]);

  function payload() {
    return {
      include_keywords: includeTags,
      exclude_keywords: excludeTags,
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
      setStatus(t('statusSaved'));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Save failed.');
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
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Preview failed.');
    }
  }

  return (
    <div className="space-y-6">
      {/* Keywords */}
      <SettingsSection title={t('title')} description={t('description')}>
        <SettingsField label={t('skillsLabel')} hint={t('skillsHint')}>
          <textarea
            className="min-h-28 w-full rounded-2xl border border-border bg-surface px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary/15"
            placeholder={t('skillsPlaceholder')}
            value={includeKeywords}
            onChange={(event) => setIncludeKeywords(event.target.value)}
          />
        </SettingsField>

        {includeTags.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {includeTags.map((tag) => (
              <Badge key={tag} tone="accent" className="rounded-lg px-2.5 py-1 text-xs">
                + {tag}
              </Badge>
            ))}
          </div>
        )}

        <SettingsField label={t('excludeKeywordsLabel')}>
          <textarea
            className="min-h-20 w-full rounded-2xl border border-border bg-surface px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary/15"
            placeholder={t('excludeKeywordsPlaceholder')}
            value={excludeKeywords}
            onChange={(event) => setExcludeKeywords(event.target.value)}
          />
        </SettingsField>

        {excludeTags.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {excludeTags.map((tag) => (
              <Badge key={tag} tone="default" className="rounded-lg px-2.5 py-1 text-xs opacity-70">
                − {tag}
              </Badge>
            ))}
          </div>
        )}
      </SettingsSection>

      {/* Match fields */}
      <SettingsSection title={t('matchFieldsTitle')} description={t('matchFieldsDesc')}>
        <div className="grid gap-2 sm:grid-cols-3">
          <MatchFieldToggle checked={matchTitle} onChange={() => setMatchTitle((v) => !v)} label={t('matchFieldTitle')} />
          <MatchFieldToggle checked={matchLocation} onChange={() => setMatchLocation((v) => !v)} label={t('matchFieldLocation')} />
          <MatchFieldToggle checked={matchCompanyName} onChange={() => setMatchCompanyName((v) => !v)} label={t('matchFieldCompanyName')} />
        </div>
      </SettingsSection>

      {/* Preview + save */}
      <SettingsSection title={t('matchingHelp')}>
        {preview && (
          <div className="grid gap-4 rounded-2xl border border-border bg-surface-muted p-5 sm:grid-cols-3">
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">{t('previewPassed')}</div>
              <div className="mt-2 text-2xl font-semibold text-success">{preview.passed_jobs}</div>
            </div>
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">{t('previewRejected')}</div>
              <div className="mt-2 text-2xl font-semibold text-danger">{preview.rejected_jobs}</div>
            </div>
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">{t('previewActiveFields')}</div>
              <div className="mt-2 text-sm font-medium text-foreground/70">
                {preview.active_fields.join(', ') || '—'}
              </div>
            </div>
          </div>
        )}

        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={savePreferences}>{t('saveButton')}</Button>
          <Button variant="secondary" onClick={runPreview}>{t('previewButton')}</Button>
          {status && <span className="text-sm text-success">{status}</span>}
          {error && <span className="text-sm text-danger">{error}</span>}
        </div>

        {preference && (
          <p className="text-xs text-muted-foreground">
            {preference.enabled ? '●' : '○'}{' '}
            {preference.enabled ? (preference.include_keywords.length > 0 ? `${preference.include_keywords.length} include · ${preference.exclude_keywords.length} exclude` : 'No keywords set') : 'Idle'}
          </p>
        )}
      </SettingsSection>
    </div>
  );
}
