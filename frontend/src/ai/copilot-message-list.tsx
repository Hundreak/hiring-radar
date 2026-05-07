'use client';

import {Bot, User2} from 'lucide-react';

import {CopilotMark} from '@/components/ai/copilot-brand';
import {CopilotRichContent} from '@/components/ai/copilot-rich-content';
import type {CopilotDensity, CopilotMessage} from '@/lib/copilot-ui';

export function CopilotMessageList({
  messages,
  isThinking,
  thinkingLabel,
  density = 'comfortable',
}: {
  messages: CopilotMessage[];
  isThinking: boolean;
  thinkingLabel: string;
  density?: CopilotDensity;
}) {
  const compact = density === 'compact';

  return (
    <div className={compact ? 'space-y-3' : 'space-y-4'}>
      {messages.map((message, index) => {
        const assistant = message.role === 'assistant';
        const messageKey = message.id || `${message.role}-${message.timestamp || index}-${index}`;
        return (
          <div key={messageKey} className={`flex gap-3 ${assistant ? 'items-start' : 'flex-row-reverse items-start'}`}>
            <div
              className={[
                'mt-0.5 inline-flex shrink-0 items-center justify-center rounded-[18px] border',
                assistant
                  ? `${compact ? 'size-10' : 'size-11'} border-white/60 bg-white/90 shadow-sm dark:border-white/10 dark:bg-surface/90`
                  : `${compact ? 'size-9' : 'size-10'} border-slate-200 bg-white text-slate-700 dark:border-white/10 dark:bg-surface-muted dark:text-white`,
              ].join(' ')}
            >
              {assistant ? <CopilotMark size={compact ? 'sm' : 'sm'} /> : <User2 className="size-4" />}
            </div>
            <div
              className={[
                compact ? 'max-w-[92%] rounded-[22px] px-4 py-3 text-[15px] leading-7' : 'max-w-[88%] rounded-[24px] px-4 py-3 text-sm leading-7',
                assistant
                  ? 'border border-slate-200/90 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(243,247,255,0.98))] text-slate-900 dark:border-white/10 dark:bg-[linear-gradient(180deg,rgba(16,26,44,0.92),rgba(9,17,30,0.98))] dark:text-white'
                  : 'bg-[linear-gradient(135deg,#5b34f3,#3b82f6)] text-white',
              ].join(' ')}
            >
              {assistant ? (
                <CopilotRichContent content={message.content} className={compact ? 'text-[15px]' : 'text-sm'} />
              ) : (
                <div className="whitespace-pre-wrap">{message.content}</div>
              )}
            </div>
          </div>
        );
      })}

      {isThinking ? (
        <div className="flex items-start gap-3">
          <div className={`mt-0.5 inline-flex ${compact ? 'size-10' : 'size-11'} shrink-0 items-center justify-center rounded-[18px] border border-white/60 bg-white/90 shadow-sm dark:border-white/10 dark:bg-surface/90`}>
            <Bot className="size-4 text-accent" />
          </div>
          <div className={`rounded-[24px] border border-slate-200/90 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(243,247,255,0.98))] px-4 py-3 shadow-sm dark:border-white/10 dark:bg-[linear-gradient(180deg,rgba(16,26,44,0.92),rgba(9,17,30,0.98))] dark:text-slate-300 ${compact ? 'text-[15px] text-slate-600' : 'text-sm text-slate-600'}`}>
            <div className="flex items-center gap-2">
              <span className="inline-flex gap-1">
                <span className="size-2 animate-bounce rounded-full bg-accent [animation-delay:-0.2s]" />
                <span className="size-2 animate-bounce rounded-full bg-accent [animation-delay:-0.1s]" />
                <span className="size-2 animate-bounce rounded-full bg-accent" />
              </span>
              {thinkingLabel}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
