'use client';

import {Loader2, Sparkles, Wand2} from 'lucide-react';

import {Button} from '@/components/ui/button';
import {FeedbackBanner} from '@/components/ui/feedback-banner';
import type {AiSkillEvidenceResponse} from '@/types/ai';

type Props = {
  locale: string;
  isLoading: boolean;
  errorMessage: string | null;
  response: AiSkillEvidenceResponse | null;
  onClose: () => void;
  onRefresh: () => void;
  onApplyDescription: (value: string, suggestionIndex?: number) => void | Promise<void>;
  onApplyEvidenceNote: (value: string, suggestionIndex?: number) => void | Promise<void>;
  onAppendProofIdeas: (ideas: string[]) => void | Promise<void>;
  onRejectDescription?: (value: string, suggestionIndex?: number) => void | Promise<void>;
  onRejectEvidenceNote?: (value: string, suggestionIndex?: number) => void | Promise<void>;
  onRejectProofIdeas?: (ideas: string[]) => void | Promise<void>;
};

export function AiSkillEvidencePanel({
  locale,
  isLoading,
  errorMessage,
  response,
  onClose,
  onRefresh,
  onApplyDescription,
  onApplyEvidenceNote,
  onAppendProofIdeas,
  onRejectDescription,
  onRejectEvidenceNote,
  onRejectProofIdeas,
}: Props) {
  return (
    <div className="mt-4 rounded-3xl border border-violet-200/70 bg-white/95 p-5 shadow-[0_20px_70px_rgba(91,33,182,0.12)] backdrop-blur dark:border-violet-500/20 dark:bg-slate-950/85">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-xs font-semibold text-violet-700 dark:border-violet-500/20 dark:bg-violet-500/10 dark:text-violet-200">
            <Sparkles className="size-3.5" />
            {locale === 'en' ? 'AI Skill Evidence' : locale === 'de' ? 'KI-Kompetenznachweis' : 'AI Beceri Kanıtı'}
          </div>
          <h3 className="mt-3 text-lg font-semibold tracking-tight text-slate-900 dark:text-slate-100">
            {locale === 'en'
              ? 'Strengthen how this skill is explained'
              : locale === 'de'
                ? 'Stärke, wie diese Kompetenz erklärt wird'
                : 'Bu beceriyi daha güçlü anlat'}
          </h3>
          <p className="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
            {locale === 'en'
              ? 'Use AI to improve the skill explanation, generate stronger proof language, and spot missing credibility signals.'
              : locale === 'de'
                ? 'Nutze KI, um die Kompetenzbeschreibung zu verbessern, stärkere Nachweisformulierung zu erzeugen und fehlende Glaubwürdigkeitssignale zu erkennen.'
                : 'AI ile bu becerinin açıklamasını güçlendir, daha sağlam kanıt dili üret ve eksik güven sinyallerini gör.'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button type="button" variant="secondary" onClick={onRefresh} disabled={isLoading}>
            {isLoading ? <Loader2 className="mr-2 size-4 animate-spin" /> : <Wand2 className="mr-2 size-4" />}
            {locale === 'en' ? 'Refresh' : locale === 'de' ? 'Neu laden' : 'Yeniden öner'}
          </Button>
          <Button type="button" variant="ghost" onClick={onClose}>
            {locale === 'en' ? 'Close' : locale === 'de' ? 'Schließen' : 'Kapat'}
          </Button>
        </div>
      </div>

      {errorMessage ? (
        <div className="mt-4">
          <FeedbackBanner
            tone="error"
            title={locale === 'en' ? 'Could not fetch suggestions' : locale === 'de' ? 'Vorschläge konnten nicht geladen werden' : 'Öneriler alınamadı'}
          >
            {errorMessage}
          </FeedbackBanner>
        </div>
      ) : null}

      {isLoading ? (
        <div className="mt-6 flex min-h-40 items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900/60 dark:text-slate-400">
          <Loader2 className="mr-2 size-4 animate-spin" />
          {locale === 'en'
            ? 'Preparing evidence suggestions...'
            : locale === 'de'
              ? 'Nachweisvorschläge werden vorbereitet...'
              : 'Kanıt önerileri hazırlanıyor...'}
        </div>
      ) : null}

      {!isLoading && response ? (
        <div className="mt-6 space-y-5">
          {response.description_suggestions.length > 0 ? (
            <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4 dark:border-slate-800 dark:bg-slate-900/60">
              <div className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">
                {locale === 'en' ? 'Description suggestions' : locale === 'de' ? 'Beschreibungsvorschläge' : 'Açıklama önerileri'}
              </div>
              <div className="space-y-3">
                {response.description_suggestions.map((item, index) => (
                  <div key={`${item}-${index}`} className="rounded-2xl border border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-950">
                    <p className="text-sm leading-6 text-slate-700 dark:text-slate-200">{item}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Button type="button" variant="secondary" onClick={() => void onApplyDescription(item, index)}>
                        {locale === 'en' ? 'Apply to description' : locale === 'de' ? 'Als Beschreibung anwenden' : 'Açıklamaya uygula'}
                      </Button>
                      {onRejectDescription ? (
                        <Button type="button" variant="ghost" onClick={() => void onRejectDescription(item, index)}>
                          {locale === 'en' ? 'Reject' : locale === 'de' ? 'Ablehnen' : 'Reddet'}
                        </Button>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {response.evidence_note_suggestions.length > 0 ? (
            <div className="rounded-2xl border border-violet-200 bg-violet-50/70 p-4 dark:border-violet-500/15 dark:bg-violet-500/5">
              <div className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">
                {locale === 'en' ? 'Evidence note suggestions' : locale === 'de' ? 'Nachweisnotiz-Vorschläge' : 'Kanıt notu önerileri'}
              </div>
              <div className="space-y-3">
                {response.evidence_note_suggestions.map((item, index) => (
                  <div key={`${item}-${index}`} className="rounded-2xl border border-violet-200 bg-white p-3 dark:border-violet-500/15 dark:bg-slate-950">
                    <p className="text-sm leading-6 text-slate-700 dark:text-slate-200">{item}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Button type="button" onClick={() => void onApplyEvidenceNote(item, index)}>
                        {locale === 'en' ? 'Apply to evidence note' : locale === 'de' ? 'Als Nachweisnotiz anwenden' : 'Kanıt notuna uygula'}
                      </Button>
                      {onRejectEvidenceNote ? (
                        <Button type="button" variant="ghost" onClick={() => void onRejectEvidenceNote(item, index)}>
                          {locale === 'en' ? 'Reject' : locale === 'de' ? 'Ablehnen' : 'Reddet'}
                        </Button>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {response.proof_ideas.length > 0 ? (
            <div className="rounded-2xl border border-sky-200 bg-sky-50/80 p-4 dark:border-sky-500/20 dark:bg-sky-500/5">
              <div className="mb-3 text-sm font-semibold text-sky-900 dark:text-sky-100">
                {locale === 'en' ? 'Proof ideas' : locale === 'de' ? 'Nachweisideen' : 'Kanıt fikirleri'}
              </div>
              <ul className="space-y-2 text-sm leading-6 text-slate-700 dark:text-slate-300">
                {response.proof_ideas.map((item, index) => (
                  <li key={`${item}-${index}`}>• {item}</li>
                ))}
              </ul>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button type="button" variant="secondary" onClick={() => void onAppendProofIdeas(response.proof_ideas)}>
                  {locale === 'en' ? 'Append ideas to evidence note' : locale === 'de' ? 'Ideen an Nachweisnotiz anhängen' : 'Fikirleri kanıt notuna ekle'}
                </Button>
                {onRejectProofIdeas ? (
                  <Button type="button" variant="ghost" onClick={() => void onRejectProofIdeas(response.proof_ideas)}>
                    {locale === 'en' ? 'Reject' : locale === 'de' ? 'Ablehnen' : 'Reddet'}
                  </Button>
                ) : null}
              </div>
            </div>
          ) : null}

          {response.missing_signals.length > 0 ? (
            <div className="rounded-2xl border border-amber-200 bg-amber-50/80 p-4 dark:border-amber-500/20 dark:bg-amber-500/5">
              <div className="mb-3 text-sm font-semibold text-amber-900 dark:text-amber-100">
                {locale === 'en' ? 'Missing signals' : locale === 'de' ? 'Fehlende Signale' : 'Eksik sinyaller'}
              </div>
              <ul className="space-y-2 text-sm leading-6 text-slate-700 dark:text-slate-300">
                {response.missing_signals.map((item, index) => (
                  <li key={`${item}-${index}`}>• {item}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {response.strengthening_note ? (
            <FeedbackBanner tone="info" title={locale === 'en' ? 'Strengthening note' : locale === 'de' ? 'Verstärkungshinweis' : 'Güçlendirme notu'}>
              {response.strengthening_note}
            </FeedbackBanner>
          ) : null}

          {response.warnings.length > 0 ? (
            <FeedbackBanner tone="warning" title={locale === 'en' ? 'Points to review' : locale === 'de' ? 'Zu prüfende Punkte' : 'Dikkat edilmesi gerekenler'}>
              <ul className="space-y-1">
                {response.warnings.map((warning, index) => (
                  <li key={`${warning}-${index}`}>• {warning}</li>
                ))}
              </ul>
            </FeedbackBanner>
          ) : null}

          {response.telemetry_ref ? <div className="text-[11px] text-slate-400 dark:text-slate-500">Telemetry Ref: {response.telemetry_ref}</div> : null}
        </div>
      ) : null}
    </div>
  );
}
