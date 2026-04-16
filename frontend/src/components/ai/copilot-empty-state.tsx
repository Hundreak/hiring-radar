'use client';

import {CopilotMark} from '@/components/ai/copilot-brand';
import {CopilotSuggestionGrid} from '@/components/ai/copilot-suggestion-grid';
import type {CopilotDensity, CopilotSuggestion} from '@/lib/copilot-ui';
import {getCopilotCopy} from '@/lib/copilot-ui';

export function CopilotEmptyState({
  locale,
  suggestions,
  onSelectSuggestion,
  density = 'comfortable',
}: {
  locale: string;
  suggestions: CopilotSuggestion[];
  onSelectSuggestion: (prompt: string) => void;
  density?: CopilotDensity;
}) {
  const copy = getCopilotCopy(locale);
  const isCompact = density === 'compact';
  const isImmersive = density === 'immersive';

  return (
    <div className="relative overflow-hidden rounded-[28px] border border-white/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(242,247,255,0.98))] p-5 shadow-[0_18px_42px_rgba(15,23,42,0.10)] dark:border-white/10 dark:bg-[linear-gradient(180deg,rgba(12,23,43,0.96),rgba(6,15,29,0.98))]">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(124,58,237,0.10),transparent_32%),radial-gradient(circle_at_bottom_right,rgba(59,130,246,0.10),transparent_28%)] dark:bg-[radial-gradient(circle_at_top_left,rgba(167,139,250,0.14),transparent_28%),radial-gradient(circle_at_bottom_right,rgba(59,130,246,0.10),transparent_24%)]" />
      <div className="relative">
        <div className="flex items-center gap-3">
          <CopilotMark size={isCompact ? 'sm' : 'md'} />
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.34em] text-accent/90">CoreSift AI</div>
            <div className={`mt-0.5 font-semibold text-slate-900 dark:text-white ${isCompact ? 'text-sm' : 'text-base'}`}>Kariyer asistanın</div>
          </div>
        </div>

        <h3 className={`mt-6 max-w-[14ch] font-semibold tracking-tight text-slate-950 dark:text-white ${isCompact ? 'text-[clamp(2rem,3.4vw,2.75rem)]' : isImmersive ? 'text-[clamp(2.6rem,3.5vw,3.6rem)]' : 'text-[clamp(2.2rem,3.2vw,3.1rem)]'}`}>{copy.title}</h3>
        <p className={`mt-3 max-w-[46ch] leading-7 text-slate-600 dark:text-slate-300 ${isCompact ? 'text-[15px]' : 'text-base'}`}>{copy.subtitle}</p>

        <div className="mt-8">
          <div className={`font-semibold text-slate-900 dark:text-white ${isCompact ? 'text-sm' : 'text-base'}`}>{copy.starterTitle}</div>
          <div className={`mt-1 text-slate-500 dark:text-slate-400 ${isCompact ? 'text-sm' : 'text-[15px]'}`}>{copy.starterSubtitle}</div>
          <div className="mt-4">
            <CopilotSuggestionGrid suggestions={suggestions} onSelect={onSelectSuggestion} density={density} />
          </div>
        </div>
      </div>
    </div>
  );
}
