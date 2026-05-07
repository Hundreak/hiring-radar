'use client';

import {ArrowUp, Loader2} from 'lucide-react';
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
  const canSend = !disabled && value.trim().length > 0;

  async function submit() {
    if (!canSend) return;
    const trimmed = value.trim();
    setValue('');
    await onSend(trimmed);
  }

  return (
    <div className={`rounded-[22px] border bg-[linear-gradient(180deg,rgba(14,24,42,0.97),rgba(8,15,29,0.99))] backdrop-blur-xl transition ${
      disabled ? 'border-white/[0.06]' : 'border-white/[0.10] hover:border-white/[0.15]'
    } ${compact ? 'p-2.5' : 'p-3'}`}>
      <div className="flex items-end gap-2.5">
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={copy.composerPlaceholder}
          rows={compact ? 2 : 3}
          className={`flex-1 resize-none rounded-[16px] border border-white/8 bg-[rgba(255,255,255,0.04)] px-3.5 py-2.5 leading-6 text-white/90 outline-none transition placeholder:text-slate-600 focus:border-violet-500/40 focus:bg-[rgba(255,255,255,0.06)] focus:ring-2 focus:ring-violet-500/10 ${
            compact ? 'min-h-[60px] text-[13px]' : immersive ? 'min-h-[80px] text-[14px]' : 'min-h-[70px] text-[13px]'
          }`}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              void submit();
            }
          }}
          disabled={disabled}
        />
        <button
          type="button"
          onClick={() => void submit()}
          disabled={!canSend}
          aria-label={copy.send}
          className={`inline-flex shrink-0 items-center justify-center rounded-[14px] transition duration-200 ${
            compact ? 'size-[38px]' : 'size-[42px]'
          } ${
            canSend
              ? 'bg-[linear-gradient(135deg,#7c3aed,#6366f1)] text-white shadow-[0_4px_16px_rgba(124,58,237,0.36)] hover:opacity-90 hover:shadow-[0_6px_20px_rgba(124,58,237,0.44)]'
              : 'bg-white/[0.05] text-slate-600 cursor-not-allowed'
          }`}
        >
          {disabled
            ? <Loader2 className="size-4 animate-spin" />
            : <ArrowUp className="size-4" />}
        </button>
      </div>
    </div>
  );
}
