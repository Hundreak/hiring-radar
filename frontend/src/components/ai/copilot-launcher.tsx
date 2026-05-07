'use client';

import {CopilotMark} from '@/components/ai/copilot-brand';

const launcherSubtitles: Record<string, string> = {
  tr: 'Yerel AI kariyer asistanın',
  en: 'Your local AI career assistant',
  de: 'Dein lokaler KI-Karriere-Assistent',
};

export function CopilotLauncher({
  onClick,
  expanded,
  rightOffset = 0,
  locale = 'en',
}: {
  onClick: () => void;
  expanded: boolean;
  rightOffset?: number;
  locale?: string;
}) {
  const subtitle = launcherSubtitles[locale] ?? launcherSubtitles.en;

  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Open CoreSift AI"
      style={{right: `${Math.max(24, rightOffset + 24)}px`}}
      className={[
        'copilot-launcher fixed bottom-6 z-[60] flex items-center gap-2.5 rounded-full border px-3.5 py-2.5 shadow-[0_16px_40px_rgba(10,15,35,0.24)] backdrop-blur-2xl transition-[transform,opacity,right,box-shadow] duration-500 ease-[cubic-bezier(0.22,1,0.36,1)]',
        expanded
          ? 'pointer-events-none translate-y-2 scale-95 opacity-0'
          : 'border-white/55 bg-[linear-gradient(180deg,rgba(255,255,255,0.96),rgba(241,245,255,0.97))] text-slate-900 hover:-translate-y-0.5 hover:shadow-[0_22px_52px_rgba(10,15,35,0.30)] dark:border-white/[0.10] dark:bg-[linear-gradient(180deg,rgba(13,21,38,0.97),rgba(6,12,24,0.99))] dark:text-white',
      ].join(' ')}
    >
      <CopilotMark size="sm" />
      <span className="hidden pr-0.5 text-left sm:block">
        <span className="block text-[13px] font-semibold leading-tight tracking-[-0.01em] text-inherit">CoreSift AI</span>
        <span className="block text-[11px] leading-tight text-slate-500 dark:text-slate-400">{subtitle}</span>
      </span>
    </button>
  );
}
