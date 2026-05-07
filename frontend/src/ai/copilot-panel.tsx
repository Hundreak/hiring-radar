'use client';

import {History, Maximize2, Minimize2, PanelRightClose, PanelRightOpen, Plus, Trash2, X} from 'lucide-react';
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
      return {...common, position: 'fixed', inset: 16, zIndex: 70, opacity: expanded ? 1 : 0, pointerEvents: expanded ? 'auto' : 'none', transform: expanded ? 'translateY(0) scale(1)' : 'translateY(12px) scale(0.985)'};
    }
    if (viewMode === 'sidebar') {
      return {...common, position: 'fixed', top: 20, bottom: 20, right: baseRight, width: sidebarWidth, zIndex: 70, opacity: expanded ? 1 : 0, pointerEvents: expanded ? 'auto' : 'none', transform: expanded ? 'translateX(0)' : 'translateX(24px)'};
    }
    return {...common, position: 'fixed', right: baseRight, bottom: 20, width: floatingWidth, height: 'min(740px, calc(100dvh - 40px))', zIndex: 70, opacity: expanded ? 1 : 0, pointerEvents: expanded ? 'auto' : 'none', transform: expanded ? 'translateY(0) scale(1)' : 'translateY(16px) scale(0.985)'};
  }, [viewMode, baseRight, expanded]);

  const historyPanelStyle = useMemo(() => {
    if (!(expanded && showHistory && isDesktop && viewMode !== 'fullscreen')) return undefined;
    const width = 280;
    return {
      position: 'fixed',
      top: viewMode === 'sidebar' ? 20 : 'auto',
      bottom: viewMode === 'sidebar' ? 20 : 20,
      right: baseRight + panelWidth + gap,
      width,
      height: viewMode === 'sidebar' ? 'auto' : 'min(740px, calc(100dvh - 40px))',
      zIndex: 69,
      transition: 'transform 340ms cubic-bezier(0.22,1,0.36,1), opacity 220ms ease, right 320ms cubic-bezier(0.22,1,0.36,1)',
    } as React.CSSProperties;
  }, [expanded, showHistory, isDesktop, viewMode, baseRight, panelWidth]);

  // Shared icon button styles
  const iconBtn = 'inline-flex size-8 items-center justify-center rounded-[10px] border border-white/[0.07] bg-transparent text-slate-500 transition hover:border-white/12 hover:bg-white/[0.05] hover:text-slate-300';
  const activeIconBtn = 'inline-flex size-8 items-center justify-center rounded-[10px] border border-violet-400/35 bg-violet-500/12 text-violet-300 transition';

  return (
    <>
      {/* History sidebar */}
      {expanded && showHistory && isDesktop && viewMode !== 'fullscreen' ? (
        <aside
          className="rounded-[28px] border border-white/8 bg-[linear-gradient(180deg,rgba(10,20,36,0.98),rgba(4,11,22,0.99))] p-4 shadow-[0_20px_48px_rgba(2,6,23,0.26)] backdrop-blur-2xl"
          style={historyPanelStyle}
        >
          <div className="flex items-center justify-between gap-2 pb-3 pt-0.5">
            <div>
              <div className="text-[11px] font-semibold text-white/80">{copy.history}</div>
              <div className="mt-0.5 text-[10px] text-slate-500">{copy.activeConversation}</div>
            </div>
            <button type="button" onClick={onToggleHistory} className={iconBtn} aria-label={copy.close}>
              <X className="size-3.5" />
            </button>
          </div>
          <div className="space-y-1.5 overflow-y-auto pr-0.5">
            {conversations.length > 0
              ? conversations.map((conv) => {
                  const active = conv.id === currentConversationId;
                  return (
                    <div
                      key={conv.id}
                      className={`rounded-[18px] border p-3 transition ${
                        active ? 'border-violet-400/40 bg-violet-500/10' : 'border-white/8 bg-white/[0.03] hover:border-violet-300/25'
                      }`}
                    >
                      <button type="button" onClick={() => onSelectConversation(conv.id)} className="block w-full text-left">
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0 flex-1">
                            <div className="line-clamp-1 text-[13px] font-medium text-white/85">{conv.title}</div>
                            <div className="mt-0.5 text-[10px] text-slate-500">{formatConversationTime(conv.updatedAt, locale)}</div>
                          </div>
                          {active && (
                            <span className="inline-flex shrink-0 rounded-full border border-violet-400/30 bg-violet-500/12 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-violet-300">
                              •
                            </span>
                          )}
                        </div>
                        <div className="mt-1.5 line-clamp-2 text-[11px] leading-[1.5] text-slate-500">{getConversationPreview(conv.messages, locale)}</div>
                      </button>
                      <div className="mt-2.5 flex items-center justify-between gap-2 border-t border-white/6 pt-2">
                        <button type="button" onClick={() => onSelectConversation(conv.id)} className="text-[11px] font-medium text-violet-300/80 transition hover:text-violet-200">
                          {copy.switchConversation}
                        </button>
                        <button type="button" onClick={() => onDeleteConversation(conv.id)} className="inline-flex items-center gap-1 text-[10px] text-slate-500 transition hover:text-rose-400">
                          <Trash2 className="size-3" />
                          {copy.deleteConversation}
                        </button>
                      </div>
                    </div>
                  );
                })
              : <div className="rounded-[16px] border border-dashed border-white/8 px-3 py-4 text-[12px] text-slate-500">{copy.historyEmpty}</div>}
          </div>
        </aside>
      ) : null}

      {/* Main panel */}
      <div className="copilot-panel-shell" style={shellStyle}>
        <div className="relative flex h-full flex-col overflow-hidden rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,rgba(11,20,36,0.98),rgba(5,12,24,0.99))] shadow-[0_32px_72px_rgba(10,15,35,0.38)] backdrop-blur-2xl">
          {/* Ambient glow layer */}
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(120,80,240,0.13),transparent_35%),radial-gradient(ellipse_at_bottom_right,rgba(50,100,230,0.09),transparent_28%)]" />

          {/* ── Header ── */}
          <div className="relative flex shrink-0 items-center gap-3 border-b border-white/[0.07] px-4 py-3.5">
            {/* Brand — left-anchored */}
            <CopilotBrand stacked={false} subtitle={null} />

            {/* Spacer */}
            <div className="flex-1" />

            {/* Control cluster — right-aligned */}
            <div className="flex items-center gap-1.5">
              {/* New conversation — soft violet accent to distinguish from icon buttons */}
              <button
                type="button"
                onClick={onNewConversation}
                className="inline-flex items-center gap-1.5 rounded-xl border border-violet-400/20 bg-violet-500/[0.07] px-3 py-1.5 text-[12px] font-semibold text-violet-200/90 transition hover:border-violet-400/36 hover:bg-violet-500/12 hover:text-violet-100"
              >
                <Plus className="size-3.5" />
                <span className="hidden sm:inline">{copy.newConversation}</span>
              </button>

              {/* Separator */}
              <div className="mx-0.5 h-4 w-px bg-white/[0.08]" />

              {/* History */}
              <button type="button" onClick={onToggleHistory} aria-label={copy.history} className={showHistory ? activeIconBtn : iconBtn}>
                <History className="size-[14px]" />
              </button>

              {/* Dock / sidebar toggle */}
              <button
                type="button"
                onClick={() => onSetViewMode(viewMode === 'sidebar' ? 'floating' : 'sidebar')}
                aria-label={copy.dockRight}
                className={viewMode === 'sidebar' ? activeIconBtn : iconBtn}
              >
                {viewMode === 'sidebar' ? <PanelRightClose className="size-[14px]" /> : <PanelRightOpen className="size-[14px]" />}
              </button>

              {/* Fullscreen toggle */}
              <button
                type="button"
                onClick={() => onSetViewMode(viewMode === 'fullscreen' ? 'floating' : 'fullscreen')}
                aria-label={viewMode === 'fullscreen' ? copy.collapse : copy.expandFull}
                className={viewMode === 'fullscreen' ? activeIconBtn : iconBtn}
              >
                {viewMode === 'fullscreen' ? <Minimize2 className="size-[14px]" /> : <Maximize2 className="size-[14px]" />}
              </button>

              {/* Close */}
              <button type="button" onClick={onClose} aria-label={copy.close} className={iconBtn}>
                <X className="size-[14px]" />
              </button>
            </div>
          </div>

          {/* ── Content ── */}
          <div className="relative min-h-0 flex-1 overflow-hidden px-4 pb-4 pt-3">
            <div className="flex h-full min-h-0 flex-col gap-3">
              {/* Message area */}
              <div className="min-h-0 flex-1 overflow-y-auto pr-0.5">
                {showEmpty ? (
                  <CopilotEmptyState
                    locale={locale}
                    suggestions={suggestions}
                    onSelectSuggestion={onSelectSuggestion}
                    density={anchoredLeftOfRightSurface ? 'compact' : viewMode === 'fullscreen' ? 'immersive' : 'comfortable'}
                  />
                ) : (
                  <div className="rounded-[22px] border border-white/8 bg-[linear-gradient(180deg,rgba(11,21,40,0.96),rgba(6,14,28,0.98))] p-4 shadow-[0_12px_32px_rgba(10,15,35,0.12)]">
                    <CopilotMessageList
                      messages={messages}
                      isThinking={thinking}
                      thinkingLabel={copy.thinking}
                      density={anchoredLeftOfRightSurface ? 'compact' : viewMode === 'fullscreen' ? 'immersive' : 'comfortable'}
                    />
                  </div>
                )}
              </div>

              {/* Composer area */}
              <div className="shrink-0 space-y-2">
                <div className="h-px rounded-full bg-[linear-gradient(90deg,transparent,rgba(150,110,255,0.7),rgba(90,120,255,0.55),transparent)]" />
                <div className="flex items-center gap-2 px-0.5 text-[10px] uppercase tracking-[0.16em] text-slate-500">
                  <span>{copy.quickPromptsLabel}</span>
                  <span className="text-white/15">·</span>
                  <span>{copy.privacyNote}</span>
                </div>
                <CopilotComposer
                  locale={locale}
                  onSend={onSend}
                  disabled={thinking}
                  density={anchoredLeftOfRightSurface ? 'compact' : viewMode === 'fullscreen' ? 'immersive' : 'comfortable'}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
