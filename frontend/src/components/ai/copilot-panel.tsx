'use client';

import {History, Maximize2, Minimize2, PanelRightClose, PanelRightOpen, Trash2, X} from 'lucide-react';
import {useMemo} from 'react';
import type {CSSProperties} from 'react';

import {CopilotBrand} from '@/components/ai/copilot-brand';
import {CopilotComposer} from '@/components/ai/copilot-composer';
import {CopilotEmptyState} from '@/components/ai/copilot-empty-state';
import {CopilotMessageList} from '@/components/ai/copilot-message-list';
import type {CopilotConversation, CopilotMessage, CopilotSuggestion, CopilotViewMode} from '@/lib/copilot-ui';
import {formatConversationTime, getConversationPreview, getCopilotCopy} from '@/lib/copilot-ui';

export function CopilotPanel({
  locale,
  expanded,
  viewMode,
  showHistory,
  currentConversationId,
  conversations,
  messages,
  thinking,
  suggestions,
  rightOffset,
  anchoredLeftOfRightSurface,
  viewportWidth,
  onClose,
  onToggleHistory,
  onSelectConversation,
  onDeleteConversation,
  onSetViewMode,
  onNewConversation,
  onSelectSuggestion,
  onSend,
}: {
  locale: string;
  expanded: boolean;
  viewMode: CopilotViewMode;
  showHistory: boolean;
  currentConversationId: string;
  conversations: CopilotConversation[];
  messages: CopilotMessage[];
  thinking: boolean;
  suggestions: CopilotSuggestion[];
  rightOffset: number;
  anchoredLeftOfRightSurface: boolean;
  viewportWidth: number;
  onClose: () => void;
  onToggleHistory: () => void;
  onSelectConversation: (id: string) => void;
  onDeleteConversation: (id: string) => void;
  onSetViewMode: (mode: CopilotViewMode) => void;
  onNewConversation: () => void;
  onSelectSuggestion: (prompt: string) => void;
  onSend: (value: string) => Promise<void> | void;
}) {
  const copy = getCopilotCopy(locale);
  const showEmpty = messages.length <= 1;
  const isDesktop = viewportWidth >= 1180;
  const floatingWidth = 440;
  const sidebarWidth = 420;
  const panelWidth = viewMode === 'sidebar' ? sidebarWidth : floatingWidth;
  const gap = 20;
  const baseRight = Math.max(24, rightOffset + 24);

  const shellStyle = useMemo<CSSProperties>(() => {
    const common = {transition: 'transform 340ms cubic-bezier(0.22,1,0.36,1), opacity 220ms ease, width 320ms cubic-bezier(0.22,1,0.36,1), height 320ms cubic-bezier(0.22,1,0.36,1), left 320ms cubic-bezier(0.22,1,0.36,1), right 320ms cubic-bezier(0.22,1,0.36,1)'} as React.CSSProperties;
    if (viewMode === 'fullscreen') {
      return {...common, position: 'fixed', inset: 20, zIndex: 70, opacity: expanded ? 1 : 0, pointerEvents: expanded ? 'auto' : 'none', transform: expanded ? 'translateY(0) scale(1)' : 'translateY(12px) scale(0.985)'};
    }
    if (viewMode === 'sidebar') {
      return {...common, position: 'fixed', top: 24, bottom: 24, right: baseRight, width: sidebarWidth, zIndex: 70, opacity: expanded ? 1 : 0, pointerEvents: expanded ? 'auto' : 'none', transform: expanded ? 'translateX(0)' : 'translateX(24px)'};
    }
    return {...common, position: 'fixed', right: baseRight, bottom: 24, width: floatingWidth, height: 'min(760px, calc(100dvh - 48px))', zIndex: 70, opacity: expanded ? 1 : 0, pointerEvents: expanded ? 'auto' : 'none', transform: expanded ? 'translateY(0) scale(1)' : 'translateY(16px) scale(0.985)'};
  }, [viewMode, baseRight, expanded]);

  const historyPanelStyle = useMemo(() => {
    if (!(expanded && showHistory && isDesktop && viewMode !== 'fullscreen')) return undefined;
    const width = 296;
    return {
      position: 'fixed',
      top: viewMode === 'sidebar' ? 24 : 'auto',
      bottom: viewMode === 'sidebar' ? 24 : 24,
      right: baseRight + panelWidth + gap,
      width,
      height: viewMode === 'sidebar' ? 'auto' : 'min(760px, calc(100dvh - 48px))',
      zIndex: 69,
      transition: 'transform 340ms cubic-bezier(0.22,1,0.36,1), opacity 220ms ease, right 320ms cubic-bezier(0.22,1,0.36,1)',
    } as React.CSSProperties;
  }, [expanded, showHistory, isDesktop, viewMode, baseRight, panelWidth]);

  const iconButtonClass = 'inline-flex h-12 w-12 items-center justify-center rounded-[18px] border border-white/10 bg-white/5 text-slate-300 transition hover:text-white';
  const activeIconButtonClass = 'inline-flex h-12 w-12 items-center justify-center rounded-[18px] border border-violet-400/40 bg-violet-500/14 text-violet-300 transition';

  return (
    <>
      {expanded && showHistory && isDesktop && viewMode !== 'fullscreen' ? (
        <aside className="rounded-[30px] border border-white/10 bg-[linear-gradient(180deg,rgba(10,20,36,0.98),rgba(4,11,22,0.99))] p-4 shadow-[0_24px_54px_rgba(2,6,23,0.28)] backdrop-blur-2xl" style={historyPanelStyle}>
          <div className="flex items-center justify-between gap-3 px-1 pb-3 pt-1">
            <div>
              <div className="text-sm font-semibold text-white">{copy.history}</div>
              <div className="mt-1 text-xs text-slate-400">{copy.activeConversation}</div>
            </div>
            <button type="button" onClick={onToggleHistory} className="inline-flex size-9 items-center justify-center rounded-2xl border border-white/10 bg-white/5 text-slate-300 transition hover:text-white" aria-label={copy.close}>
              <X className="size-4" />
            </button>
          </div>
          <div className="space-y-2 overflow-y-auto pr-1">
            {conversations.length > 0 ? conversations.map((conversation) => {
              const active = conversation.id === currentConversationId;
              return (
                <div key={conversation.id} className={`rounded-[22px] border p-3 transition ${active ? 'border-violet-400/45 bg-violet-500/12 shadow-[0_0_0_1px_rgba(167,139,250,0.16)]' : 'border-white/10 bg-white/5 hover:border-violet-300/30'}`}>
                  <button type="button" onClick={() => onSelectConversation(conversation.id)} className="block w-full text-left">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <div className="line-clamp-2 text-sm font-semibold text-white">{conversation.title}</div>
                        <div className="mt-1 text-xs text-slate-400">{formatConversationTime(conversation.updatedAt, locale)}</div>
                      </div>
                      {active ? <span className="inline-flex rounded-full border border-violet-400/30 bg-violet-500/14 px-2 py-1 text-[10px] font-medium uppercase tracking-[0.14em] text-violet-200">Aktif</span> : null}
                    </div>
                    <div className="mt-2 line-clamp-3 text-xs leading-5 text-slate-400">{getConversationPreview(conversation.messages, locale)}</div>
                  </button>
                  <div className="mt-3 flex items-center justify-between gap-3">
                    <button type="button" onClick={() => onSelectConversation(conversation.id)} className="text-xs font-medium text-violet-200 transition hover:text-white">{copy.switchConversation}</button>
                    <button type="button" onClick={() => onDeleteConversation(conversation.id)} className="inline-flex items-center gap-2 text-xs text-slate-400 transition hover:text-rose-400">
                      <Trash2 className="size-3.5" />
                      {copy.deleteConversation}
                    </button>
                  </div>
                </div>
              );
            }) : <div className="rounded-[20px] border border-dashed border-white/10 px-4 py-5 text-sm text-slate-400">{copy.historyEmpty}</div>}
          </div>
        </aside>
      ) : null}

      <div className="copilot-panel-shell" style={shellStyle}>
        <div className="relative flex h-full flex-col overflow-hidden rounded-[34px] border border-white/10 bg-[linear-gradient(180deg,rgba(12,22,39,0.98),rgba(5,13,25,0.99))] shadow-[0_34px_84px_rgba(15,23,42,0.32)] backdrop-blur-2xl">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(139,92,246,0.16),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(59,130,246,0.10),transparent_24%)]" />

          <div className="relative flex items-center justify-between gap-4 border-b border-white/8 px-5 py-4">
            <div className="shrink-0">
              <CopilotBrand stacked subtitle={null} />
            </div>
            <div className="flex min-w-0 items-center justify-end gap-2.5">
              <button type="button" onClick={onToggleHistory} aria-label={copy.history} className={showHistory ? activeIconButtonClass : iconButtonClass}>
                <History className="size-[18px]" />
              </button>
              <button type="button" onClick={onNewConversation} className="inline-flex h-12 min-w-[144px] items-center justify-center whitespace-nowrap rounded-[18px] border border-white/10 bg-white/5 px-6 text-[15px] font-semibold leading-none text-white transition hover:bg-violet-500/14">{copy.newConversation}</button>
              <button type="button" onClick={() => onSetViewMode(viewMode === 'sidebar' ? 'floating' : 'sidebar')} aria-label={copy.dockRight} className={viewMode === 'sidebar' ? activeIconButtonClass : iconButtonClass}>
                {viewMode === 'sidebar' ? <PanelRightClose className="size-[18px]" /> : <PanelRightOpen className="size-[18px]" />}
              </button>
              <button type="button" onClick={() => onSetViewMode(viewMode === 'fullscreen' ? 'floating' : 'fullscreen')} aria-label={viewMode === 'fullscreen' ? copy.collapse : copy.expandFull} className={viewMode === 'fullscreen' ? activeIconButtonClass : iconButtonClass}>
                {viewMode === 'fullscreen' ? <Minimize2 className="size-[18px]" /> : <Maximize2 className="size-[18px]" />}
              </button>
              <button type="button" onClick={onClose} aria-label={copy.close} className={iconButtonClass}>
                <X className="size-[18px]" />
              </button>
            </div>
          </div>

          <div className="relative min-h-0 flex-1 px-5 pb-5 pt-4">
            <div className="relative flex h-full min-h-0 flex-col">
              <div className="min-h-0 flex-1 overflow-y-auto pr-1">
                {showEmpty ? (
                  <CopilotEmptyState locale={locale} suggestions={suggestions} onSelectSuggestion={onSelectSuggestion} density={anchoredLeftOfRightSurface ? 'compact' : viewMode === 'fullscreen' ? 'immersive' : 'comfortable'} />
                ) : (
                  <div className="rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,rgba(12,23,43,0.96),rgba(6,15,29,0.98))] p-4 shadow-[0_18px_42px_rgba(15,23,42,0.10)]">
                    <CopilotMessageList messages={messages} isThinking={thinking} thinkingLabel={copy.thinking} density={anchoredLeftOfRightSurface ? 'compact' : viewMode === 'fullscreen' ? 'immersive' : 'comfortable'} />
                  </div>
                )}
              </div>

              <div className="mt-4 space-y-3">
                <div className="h-[3px] rounded-full bg-[linear-gradient(90deg,transparent,rgba(167,139,250,0.98),rgba(99,102,241,0.82),rgba(59,130,246,0.72),transparent)] shadow-[0_0_22px_rgba(139,92,246,0.48)]" />
                <div className="flex flex-wrap gap-2 px-1 text-[11px] uppercase tracking-[0.18em] text-slate-400">
                  <span>{copy.quickPromptsLabel}</span>
                  <span className="text-white/20">•</span>
                  <span>{copy.privacyNote}</span>
                </div>
                <CopilotComposer locale={locale} onSend={onSend} disabled={thinking} density={anchoredLeftOfRightSurface ? 'compact' : viewMode === 'fullscreen' ? 'immersive' : 'comfortable'} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
