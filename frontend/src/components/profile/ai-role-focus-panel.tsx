'use client';

import {Loader2, RefreshCw, Sparkles, Target, X} from 'lucide-react';

import type {AiRoleFocusResponse} from '@/types/ai';

type PanelLocale = 'tr' | 'en' | 'de';

type Labels = {
  title: string;
  body: string;
  close: string;
  regenerate: string;
  generating: string;
  confidence: string;
  warnings: string;
  suggestions: string;
  missingSignals: string;
  applyRole: string;
  applyAll: string;
  noSuggestions: string;
  priority: string;
};

const copy: Record<PanelLocale, Labels> = {
  tr: {
    title: 'AI ile rol odağı önerileri',
    body: 'Mevcut profil bilgilerine göre daha güçlü hedef roller ve eksik sinyaller burada listelenir.',
    close: 'Kapat',
    regenerate: 'Yeniden öneri al',
    generating: 'Rol önerileri hazırlanıyor...',
    confidence: 'Güven seviyesi',
    warnings: 'Dikkat notları',
    suggestions: 'Rol odağı önerileri',
    missingSignals: 'Eksik sinyaller',
    applyRole: 'Bu rolü ekle',
    applyAll: 'Tüm rolleri uygula',
    noSuggestions: 'Şu anda rol önerisi üretilemedi.',
    priority: 'Öncelik',
  },
  en: {
    title: 'AI role focus suggestions',
    body: 'Review stronger target role directions and missing signals inferred from your profile.',
    close: 'Close',
    regenerate: 'Generate again',
    generating: 'Generating role suggestions...',
    confidence: 'Confidence',
    warnings: 'Notes',
    suggestions: 'Role focus suggestions',
    missingSignals: 'Missing signals',
    applyRole: 'Apply this role',
    applyAll: 'Apply all roles',
    noSuggestions: 'No role suggestions are available right now.',
    priority: 'Priority',
  },
  de: {
    title: 'KI-Vorschläge für Rollenfokus',
    body: 'Hier kannst du stärkere Zielrollen und fehlende Signale auf Basis deines Profils prüfen.',
    close: 'Schließen',
    regenerate: 'Erneut vorschlagen',
    generating: 'Rollenvorschläge werden erstellt...',
    confidence: 'Vertrauen',
    warnings: 'Hinweise',
    suggestions: 'Rollenfokus-Vorschläge',
    missingSignals: 'Fehlende Signale',
    applyRole: 'Diese Rolle übernehmen',
    applyAll: 'Alle Rollen übernehmen',
    noSuggestions: 'Aktuell konnten keine Rollenvorschläge erstellt werden.',
    priority: 'Priorität',
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

export function AiRoleFocusPanel({
  locale,
  isLoading,
  errorMessage,
  response,
  onClose,
  onRefresh,
  onApplyRole,
  onApplyAll,
  onRejectRole,
}: {
  locale: string;
  isLoading: boolean;
  errorMessage: string | null;
  response: AiRoleFocusResponse | null;
  onClose: () => void;
  onRefresh: () => void;
  onApplyRole: (roleName: string, suggestionIndex?: number) => void | Promise<void>;
  onApplyAll: (roleNames: string[]) => void | Promise<void>;
  onRejectRole?: (roleName: string, suggestionIndex?: number) => void | Promise<void>;
}) {
  const resolvedLocale = resolveLocale(locale);
  const t = copy[resolvedLocale];
  const confidence = confidenceLabel(resolvedLocale, response?.confidence_band);
  const roleNames = response?.role_suggestions.map((item) => item.role_name) ?? [];

  return (
    <div className="mt-5 overflow-hidden rounded-[28px] border border-border bg-gradient-to-br from-background via-background to-muted/30 shadow-[0_20px_60px_-36px_rgba(34,197,94,0.28)]">
      <div className="border-b border-border/80 bg-gradient-to-r from-emerald-500/10 via-cyan-500/8 to-violet-500/10 px-5 py-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald-700 dark:text-emerald-200">
              <Sparkles className="size-3.5" />
              CoreSift AI
            </div>
            <h3 className="mt-3 text-lg font-semibold tracking-tight text-foreground">{t.title}</h3>
            <p className="mt-1 max-w-3xl text-sm leading-6 text-muted-foreground">{t.body}</p>
          </div>
          <div className="flex items-center gap-2">
            {roleNames.length > 0 ? (
              <button
                type="button"
                onClick={() => onApplyAll(roleNames)}
                className="inline-flex h-10 items-center justify-center gap-2 rounded-2xl border border-border bg-background px-4 text-sm font-medium text-foreground transition hover:bg-muted/50"
              >
                <Target className="size-4" />
                {t.applyAll}
              </button>
            ) : null}
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

            <section className="space-y-3">
              <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                <Target className="size-4 text-emerald-500" />
                {t.suggestions}
              </div>
              {response.role_suggestions.length > 0 ? (
                response.role_suggestions.map((item, index) => (
                  <div key={`${item.role_name}-${item.priority}`} className="rounded-2xl border border-border bg-background px-4 py-4 shadow-sm">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <div className="text-base font-semibold text-foreground">{item.role_name}</div>
                        <div className="mt-1 inline-flex rounded-full border border-border bg-muted/30 px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                          {t.priority}: {item.priority}
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={() => void onApplyRole(item.role_name, index)}
                          className="inline-flex h-10 items-center rounded-2xl border border-border bg-muted/30 px-4 text-sm font-medium text-foreground transition hover:bg-muted/50"
                        >
                          {t.applyRole}
                        </button>
                        {onRejectRole ? (
                          <button
                            type="button"
                            onClick={() => void onRejectRole(item.role_name, index)}
                            className="inline-flex h-10 items-center rounded-2xl border border-border bg-background px-4 text-sm font-medium text-muted-foreground transition hover:bg-muted/30"
                          >
                            {resolvedLocale === 'en' ? 'Reject' : resolvedLocale === 'de' ? 'Ablehnen' : 'Reddet'}
                          </button>
                        ) : null}
                      </div>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-muted-foreground">{item.fit_reason}</p>
                    {item.missing_signals.length > 0 ? (
                      <div className="mt-4 rounded-2xl border border-dashed border-border px-4 py-3">
                        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">{t.missingSignals}</div>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {item.missing_signals.map((signal) => (
                            <span key={`${item.role_name}-${signal}`} className="inline-flex rounded-full border border-border bg-muted/30 px-3 py-1 text-xs font-medium text-foreground">
                              {signal}
                            </span>
                          ))}
                        </div>
                      </div>
                    ) : null}
                  </div>
                ))
              ) : (
                <div className="rounded-2xl border border-dashed border-border px-4 py-5 text-sm text-muted-foreground">{t.noSuggestions}</div>
              )}
            </section>
          </>
        ) : null}
      </div>
    </div>
  );
}
