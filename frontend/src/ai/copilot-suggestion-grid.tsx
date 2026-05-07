'use client';

import type {CopilotDensity, CopilotSuggestion} from '@/lib/copilot-ui';

export function CopilotSuggestionGrid({suggestions, onSelect, density = 'comfortable'}: {suggestions: CopilotSuggestion[]; onSelect: (prompt: string) => void; density?: CopilotDensity}) {
  const compact = density === 'compact';
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {suggestions.map((item) => (
        <button
          key={item.id}
          type="button"
          onClick={() => onSelect(item.prompt)}
          className={`group rounded-[24px] border border-slate-200/90 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(243,247,255,0.98))] text-left shadow-[0_10px_24px_rgba(15,23,42,0.06)] transition duration-300 ease-out hover:-translate-y-0.5 hover:border-violet-300/80 hover:shadow-[0_18px_34px_rgba(15,23,42,0.10)] dark:border-white/10 dark:bg-[linear-gradient(180deg,rgba(16,26,44,0.92),rgba(9,17,30,0.98))] ${compact ? 'p-4' : 'p-5'}`}
        >
          <div className="inline-flex rounded-full bg-violet-100 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-violet-700 dark:bg-violet-500/14 dark:text-violet-300">
            {item.tag}
          </div>
          <div className={`mt-3 font-semibold leading-6 text-slate-900 dark:text-white ${compact ? 'text-[14px]' : 'text-[15px]'}`}>{item.title}</div>
          <div className="mt-3 text-sm text-slate-500 transition group-hover:text-slate-700 dark:text-slate-400 dark:group-hover:text-slate-200">Hızlı başlat</div>
        </button>
      ))}
    </div>
  );
}
