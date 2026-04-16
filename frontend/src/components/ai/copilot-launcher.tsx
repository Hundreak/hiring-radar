'use client';

import {CopilotMark} from '@/components/ai/copilot-brand';

export function CopilotLauncher({onClick, expanded, rightOffset = 0}: {onClick: () => void; expanded: boolean; rightOffset?: number}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Open CoreSift AI"
      style={{right: `${Math.max(24, rightOffset + 24)}px`}}
      className={[
        'copilot-launcher group fixed bottom-6 z-[60] flex items-center gap-3 rounded-full border border-white/70 px-4 py-3 shadow-[0_22px_44px_rgba(15,23,42,0.18)] backdrop-blur-2xl transition-[transform,opacity,right] duration-500 ease-[cubic-bezier(0.22,1,0.36,1)]',
        expanded
          ? 'pointer-events-none translate-y-2 scale-95 opacity-0'
          : 'bg-[linear-gradient(180deg,rgba(255,255,255,0.95),rgba(243,247,255,0.98))] text-slate-900 hover:-translate-y-0.5 hover:shadow-[0_28px_54px_rgba(15,23,42,0.22)] dark:border-white/10 dark:bg-[linear-gradient(180deg,rgba(17,27,43,0.96),rgba(8,16,30,0.98))] dark:text-white',
      ].join(' ')}
    >
      <CopilotMark size="sm" />
      <span className="hidden pr-1 text-left sm:block">
        <span className="block text-sm font-semibold text-inherit">CoreSift AI</span>
        <span className="block text-xs text-slate-500 dark:text-slate-400">Profilini güçlendiren yerel yardımcı</span>
      </span>
    </button>
  );
}
