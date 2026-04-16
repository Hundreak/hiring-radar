'use client';

import {ArrowUpRight, Loader2} from 'lucide-react';
import {useState} from 'react';

import type {CopilotDensity} from '@/lib/copilot-ui';
import {getCopilotCopy} from '@/lib/copilot-ui';

export function CopilotComposer({
  locale,
  onSend,
  disabled = false,
  density = 'comfortable',
}: {
  locale: string;
  onSend: (value: string) => Promise<void> | void;
  disabled?: boolean;
  density?: CopilotDensity;
}) {
  const copy = getCopilotCopy(locale);
  const [value, setValue] = useState('');
  const compact = density === 'compact';
  const immersive = density === 'immersive';

  async function submit() {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    setValue('');
    await onSend(trimmed);
  }

  return (
    <div className={`rounded-[28px] border border-white/60 bg-[linear-gradient(180deg,rgba(255,255,255,0.96),rgba(243,247,255,0.98))] shadow-[0_18px_42px_rgba(15,23,42,0.12)] backdrop-blur-xl dark:border-white/10 dark:bg-[linear-gradient(180deg,rgba(16,26,44,0.94),rgba(8,16,30,0.98))] ${compact ? 'p-3' : immersive ? 'p-4' : 'p-3.5'}`}>
      <div className="flex items-end gap-3">
        <textarea
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder={copy.composerPlaceholder}
          rows={compact ? 2 : 3}
          className={`flex-1 resize-none rounded-[22px] border border-slate-200/90 bg-white px-4 py-3 leading-7 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-violet-300 focus:ring-4 focus:ring-violet-200/60 dark:border-white/10 dark:bg-[#111b31] dark:text-white dark:placeholder:text-slate-500 dark:focus:border-violet-400 dark:focus:ring-violet-500/10 ${compact ? 'min-h-[72px] text-[15px]' : immersive ? 'min-h-[92px] text-base' : 'min-h-[82px] text-sm'}`}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault();
              void submit();
            }
          }}
          disabled={disabled}
        />
        <button
          type="button"
          onClick={() => void submit()}
          disabled={disabled || !value.trim()}
          className={`inline-flex shrink-0 items-center justify-center rounded-[22px] bg-[linear-gradient(135deg,#6d28d9,#7c3aed,#3b82f6)] text-white shadow-[0_18px_32px_rgba(109,40,217,0.28)] transition duration-300 ease-out hover:scale-[1.02] hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-45 ${compact ? 'size-[3.25rem]' : immersive ? 'size-16' : 'size-14'}`}
          aria-label={copy.send}
        >
          {disabled ? <Loader2 className="size-5 animate-spin" /> : <ArrowUpRight className={compact ? 'size-5' : 'size-5'} />}
        </button>
      </div>
    </div>
  );
}
