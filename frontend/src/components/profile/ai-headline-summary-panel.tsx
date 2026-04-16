'use client';

import {Loader2, RefreshCw, Sparkles, WandSparkles, X} from 'lucide-react';

import type {AiHeadlineSummaryResponse} from '@/types/ai';

type PanelLocale = 'tr' | 'en' | 'de';

type Labels = {
  title: string;
  body: string;
  close: string;
  regenerate: string;
  generating: string;
  confidence: string;
  warnings: string;
  headlineSection: string;
  summarySection: string;
  applyHeadline: string;
  applySummary: string;
  noSuggestions: string;
};

const copy: Record<PanelLocale, Labels> = {
  tr: {
    title: 'AI ile başlık ve özet önerileri',
    body: 'Mevcut profil bilgilerine göre daha güçlü başlık ve özet önerilerini burada inceleyebilirsin.',
    close: 'Kapat',
    regenerate: 'Yeniden öneri al',
    generating: 'Öneriler hazırlanıyor...',
    confidence: 'Güven seviyesi',
    warnings: 'Dikkat notları',
    headlineSection: 'Başlık önerileri',
    summarySection: 'Özet önerileri',
    applyHeadline: 'Başlığı uygula',
    applySummary: 'Özeti uygula',
    noSuggestions: 'Şu anda öneri üretilemedi.',
  },
  en: {
    title: 'AI headline and summary suggestions',
    body: 'Review stronger headline and summary suggestions generated from your current profile.',
    close: 'Close',
    regenerate: 'Generate again',
    generating: 'Generating suggestions...',
    confidence: 'Confidence',
    warnings: 'Notes',
    headlineSection: 'Headline suggestions',
    summarySection: 'Summary suggestions',
    applyHeadline: 'Apply headline',
    applySummary: 'Apply summary',
    noSuggestions: 'No suggestions are available right now.',
  },
  de: {
    title: 'KI-Vorschläge für Titel und Kurzprofil',
    body: 'Hier kannst du stärkere Titel- und Kurzprofilvorschläge auf Basis deines aktuellen Profils prüfen.',
    close: 'Schließen',
    regenerate: 'Erneut vorschlagen',
    generating: 'Vorschläge werden erstellt...',
    confidence: 'Vertrauen',
    warnings: 'Hinweise',
    headlineSection: 'Titelvorschläge',
    summarySection: 'Kurzprofil-Vorschläge',
    applyHeadline: 'Titel übernehmen',
    applySummary: 'Kurzprofil übernehmen',
    noSuggestions: 'Aktuell konnten keine Vorschläge erstellt werden.',
  },
};

function resolveLocale(locale: string): PanelLocale {
  if (locale === 'en' || locale === 'de') return locale;
  return 'tr';
}

function confidenceLabel(locale: PanelLocale, value: string | null | undefined): string | null {
  if (!value) return null;
  const map: Record<PanelLocale, Record<string, string>> = {
    tr: {low: 'Düşük', medium: 'Orta', high: 'Yüksek'},
    en: {low: 'Low', medium: 'Medium', high: 'High'},
    de: {low: 'Niedrig', medium: 'Mittel', high: 'Hoch'},
  };
  return map[locale][value] ?? value;
}

export function AiHeadlineSummaryPanel({
  locale,
  isLoading,
  errorMessage,
  response,
  onClose,
  onRefresh,
  onApplyHeadline,
  onApplySummary,
  onRejectHeadline,
  onRejectSummary,
}: {
  locale: string;
  isLoading: boolean;
  errorMessage: string | null;
  response: AiHeadlineSummaryResponse | null;
  onClose: () => void;
  onRefresh: () => void;
  onApplyHeadline: (title: string, suggestionIndex?: number) => void | Promise<void>;
  onApplySummary: (summary: string, suggestionIndex?: number) => void | Promise<void>;
  onRejectHeadline?: (title: string, suggestionIndex?: number) => void | Promise<void>;
  onRejectSummary?: (summary: string, suggestionIndex?: number) => void | Promise<void>;
}) {
  const resolvedLocale = resolveLocale(locale);
  const t = copy[resolvedLocale];
  const confidence = confidenceLabel(resolvedLocale, response?.confidence_band);

  return (
    <div className="mt-5 overflow-hidden rounded-[28px] border border-border bg-gradient-to-br from-background via-background to-muted/30 shadow-[0_20px_60px_-36px_rgba(94,92,230,0.45)]">
      <div className="border-b border-border/80 bg-gradient-to-r from-violet-500/10 via-fuchsia-500/8 to-cyan-500/10 px-5 py-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="inline-flex items-center gap-2 rounded-full border border-violet-500/20 bg-violet-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-violet-700 dark:text-violet-200">
              <Sparkles className="size-3.5" />
              CoreSift AI
            </div>
            <h3 className="mt-3 text-lg font-semibold tracking-tight text-foreground">{t.title}</h3>
            <p className="mt-1 max-w-3xl text-sm leading-6 text-muted-foreground">{t.body}</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onRefresh}
              disabled={isLoading}
              className="inline-flex h-10 items-center justify-center gap-2 rounded-2xl border border-border bg-background px-4 text-sm font-medium text-foreground transition hover:bg-muted/50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isLoading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
              {isLoading ? t.generating : t.regenerate}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-border bg-background text-foreground transition hover:bg-muted/50"
              aria-label={t.close}
            >
              <X className="size-4" />
            </button>
          </div>
        </div>
      </div>

      <div className="space-y-5 px-5 py-5">
        {errorMessage ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-100">
            {errorMessage}
          </div>
        ) : null}

        {isLoading ? (
          <div className="rounded-2xl border border-border bg-muted/20 px-4 py-6">
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              {t.generating}
            </div>
          </div>
        ) : null}

        {!isLoading && response ? (
          <>
            <div className="flex flex-wrap items-center gap-3">
              {confidence ? (
                <div className="inline-flex items-center gap-2 rounded-full border border-border bg-muted/30 px-3 py-1 text-xs font-medium text-foreground">
                  <span className="text-muted-foreground">{t.confidence}:</span>
                  <span>{confidence}</span>
                </div>
              ) : null}
              {response.telemetry_ref ? (
                <div className="inline-flex items-center gap-2 rounded-full border border-border bg-muted/30 px-3 py-1 text-xs font-medium text-muted-foreground">
                  {response.telemetry_ref}
                </div>
              ) : null}
            </div>

            {response.warnings.length > 0 ? (
              <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-400/30 dark:bg-amber-400/10 dark:text-amber-100">
                <div className="font-semibold">{t.warnings}</div>
                <ul className="mt-2 space-y-1">
                  {response.warnings.map((warning) => (
                    <li key={warning}>• {warning}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            <div className="grid gap-5 xl:grid-cols-2">
              <section className="space-y-3">
                <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                  <WandSparkles className="size-4 text-violet-500" />
                  {t.headlineSection}
                </div>
                {response.headline_options.length > 0 ? (
                  response.headline_options.map((item, index) => (
                    <div key={`${item.title}-${item.rationale ?? ''}`} className="rounded-2xl border border-border bg-background px-4 py-4 shadow-sm">
                      <div className="text-sm font-semibold text-foreground">{item.title}</div>
                      {item.rationale ? (
                        <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.rationale}</p>
                      ) : null}
                      <div className="mt-4 flex flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={() => void onApplyHeadline(item.title, index)}
                          className="inline-flex h-10 items-center rounded-2xl border border-border bg-muted/30 px-4 text-sm font-medium text-foreground transition hover:bg-muted/50"
                        >
                          {t.applyHeadline}
                        </button>
                        {onRejectHeadline ? (
                          <button
                            type="button"
                            onClick={() => void onRejectHeadline(item.title, index)}
                            className="inline-flex h-10 items-center rounded-2xl border border-border bg-background px-4 text-sm font-medium text-muted-foreground transition hover:bg-muted/30"
                          >
                            {resolvedLocale === 'en' ? 'Reject' : resolvedLocale === 'de' ? 'Ablehnen' : 'Reddet'}
                          </button>
                        ) : null}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="rounded-2xl border border-dashed border-border px-4 py-5 text-sm text-muted-foreground">{t.noSuggestions}</div>
                )}
              </section>

              <section className="space-y-3">
                <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                  <WandSparkles className="size-4 text-cyan-500" />
                  {t.summarySection}
                </div>
                {response.summary_options.length > 0 ? (
                  response.summary_options.map((item, index) => (
                    <div key={`${item.text}-${item.rationale ?? ''}`} className="rounded-2xl border border-border bg-background px-4 py-4 shadow-sm">
                      <div className="text-sm leading-6 text-foreground">{item.text}</div>
                      {item.rationale ? (
                        <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.rationale}</p>
                      ) : null}
                      <div className="mt-4 flex flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={() => void onApplySummary(item.text, index)}
                          className="inline-flex h-10 items-center rounded-2xl border border-border bg-muted/30 px-4 text-sm font-medium text-foreground transition hover:bg-muted/50"
                        >
                          {t.applySummary}
                        </button>
                        {onRejectSummary ? (
                          <button
                            type="button"
                            onClick={() => void onRejectSummary(item.text, index)}
                            className="inline-flex h-10 items-center rounded-2xl border border-border bg-background px-4 text-sm font-medium text-muted-foreground transition hover:bg-muted/30"
                          >
                            {resolvedLocale === 'en' ? 'Reject' : resolvedLocale === 'de' ? 'Ablehnen' : 'Reddet'}
                          </button>
                        ) : null}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="rounded-2xl border border-dashed border-border px-4 py-5 text-sm text-muted-foreground">{t.noSuggestions}</div>
                )}
              </section>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
