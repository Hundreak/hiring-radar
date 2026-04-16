'use client';

import {usePathname} from 'next/navigation';
import {useCallback, useEffect, useMemo, useRef, useState} from 'react';

import {CopilotLauncher} from '@/components/ai/copilot-launcher';
import {api, ApiError} from '@/lib/api';
import {CopilotPanel} from '@/components/ai/copilot-panel';
import {
  buildInitialAssistantMessage,
  COPILOT_ACTIVE_CONVERSATION_STORAGE_KEY,
  COPILOT_HISTORY_STORAGE_KEY,
  COPILOT_PROMPT_EVENT,
  COPILOT_RIGHT_SURFACE_EVENT,
  createCopilotConversationId,
  createCopilotMessageId,
  detectVisibleRightSurface,
  getCopilotSuggestions,
  normalizeCopilotConversations,
  makeConversationTitle,
  type CopilotConversation,
  type CopilotMessage,
  type CopilotRightSurfaceDetail,
  type CopilotSection,
  type CopilotViewMode,
} from '@/lib/copilot-ui';

function inferSection(pathname: string | null): CopilotSection {
  if (!pathname) return 'default';
  if (pathname.includes('/settings/profile')) return 'profile';
  if (pathname.includes('/matches')) return 'matches';
  if (pathname.includes('/jobs')) return 'jobs';
  return 'default';
}

function buildFreshConversation(locale: string): CopilotConversation {
  const now = new Date().toISOString();
  return {
    id: createCopilotConversationId(),
    title: locale === 'tr' ? 'Yeni sohbet' : locale === 'de' ? 'Neuer Chat' : 'New chat',
    createdAt: now,
    updatedAt: now,
    messages: [buildInitialAssistantMessage(locale)],
  };
}

export function CopilotWidget({locale}: {locale: string}) {
  const pathname = usePathname();
  const section = inferSection(pathname);
  const suggestions = useMemo(() => getCopilotSuggestions(locale, section), [locale, section]);
  const [expanded, setExpanded] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [viewMode, setViewMode] = useState<CopilotViewMode>('floating');
  const [showHistory, setShowHistory] = useState(false);
  const [viewportWidth, setViewportWidth] = useState<number>(1440);
  const [rightSurface, setRightSurface] = useState<CopilotRightSurfaceDetail>({open: false, width: 0});
  const [conversations, setConversations] = useState<CopilotConversation[]>(() => [buildFreshConversation(locale)]);
  const [currentConversationId, setCurrentConversationId] = useState<string>(() => `boot-${Date.now()}`);
  const activeConversationIdRef = useRef(currentConversationId);

  useEffect(() => {
    activeConversationIdRef.current = currentConversationId;
  }, [currentConversationId]);

  useEffect(() => {
    const fresh = buildFreshConversation(locale);
    setConversations((current) => {
      if (current.length > 0 && !current[0].id.startsWith('boot-')) return current;
      return [fresh];
    });
    setCurrentConversationId((current) => (current.startsWith('boot-') ? fresh.id : current));
  }, [locale]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      const raw = window.localStorage.getItem(COPILOT_HISTORY_STORAGE_KEY);
      const activeId = window.localStorage.getItem(COPILOT_ACTIVE_CONVERSATION_STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw) as CopilotConversation[];
      if (Array.isArray(parsed) && parsed.length > 0) {
        const normalized = normalizeCopilotConversations(parsed);
        setConversations(normalized);
        if (activeId && normalized.some((item) => item.id === activeId)) {
          setCurrentConversationId(activeId);
        } else {
          setCurrentConversationId(normalized[0].id);
        }
      }
    } catch {}
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      window.localStorage.setItem(COPILOT_HISTORY_STORAGE_KEY, JSON.stringify(conversations));
    } catch {}
  }, [conversations]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      window.localStorage.setItem(COPILOT_ACTIVE_CONVERSATION_STORAGE_KEY, currentConversationId);
    } catch {}
  }, [currentConversationId]);

  const syncRightSurface = useCallback(() => {
    setRightSurface(detectVisibleRightSurface());
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined' || typeof document === 'undefined') return undefined;

    const handleResize = () => {
      setViewportWidth(window.innerWidth);
      syncRightSurface();
    };

    const handleSurfaceEvent = () => {
      window.requestAnimationFrame(syncRightSurface);
    };

    setViewportWidth(window.innerWidth);
    syncRightSurface();

    const raf = window.requestAnimationFrame(syncRightSurface);
    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.type !== 'attributes') continue;
        const target = mutation.target as HTMLElement;
        if (!target) continue;
        if (
          target.hasAttribute('data-coresift-right-surface') ||
          target.hasAttribute('data-right-drawer') ||
          target.hasAttribute('data-drawer-side') ||
          target.hasAttribute('data-copilot-right-surface') ||
          target.hasAttribute('data-side-panel') ||
          target.hasAttribute('data-state')
        ) {
          window.requestAnimationFrame(syncRightSurface);
          break;
        }
      }
    });
    observer.observe(document.body, {
      attributes: true,
      childList: false,
      subtree: true,
      attributeFilter: ['data-coresift-right-surface', 'data-right-drawer', 'data-drawer-side', 'data-copilot-right-surface', 'data-side-panel', 'data-state'],
    });

    window.addEventListener('resize', handleResize);
    window.addEventListener(COPILOT_RIGHT_SURFACE_EVENT, handleSurfaceEvent as EventListener);

    return () => {
      window.cancelAnimationFrame(raf);
      observer.disconnect();
      window.removeEventListener('resize', handleResize);
      window.removeEventListener(COPILOT_RIGHT_SURFACE_EVENT, handleSurfaceEvent as EventListener);
    };
  }, [syncRightSurface]);

  const pushUserPromptRef = useRef<(prompt: string) => void>(() => {});

  // Listen for external prompts (e.g. interview prep from saved jobs)
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const handler = (e: Event) => {
      const detail = (e as CustomEvent<{prompt: string}>).detail;
      if (detail?.prompt) {
        pushUserPromptRef.current(detail.prompt);
      }
    };
    window.addEventListener(COPILOT_PROMPT_EVENT, handler);
    return () => window.removeEventListener(COPILOT_PROMPT_EVENT, handler);
  }, []);

  const currentConversation = useMemo(() => {
    return conversations.find((item) => item.id === currentConversationId) ?? conversations[0] ?? buildFreshConversation(locale);
  }, [conversations, currentConversationId, locale]);

  const messages = currentConversation.messages;
  const rightOffset = viewMode === 'fullscreen' ? 0 : (rightSurface.open && viewportWidth >= 1280 ? Math.max(0, rightSurface.width + 20) : 0);
  const anchoredLeftOfRightSurface = rightOffset > 0;

  async function pushUserPrompt(prompt: string) {
    const activeId = activeConversationIdRef.current;
    const targetConversation = conversations.find((item) => item.id === activeId);
    const now = new Date().toISOString();
    const userMessage: CopilotMessage = {
      id: createCopilotMessageId('user'),
      role: 'user',
      content: prompt,
      timestamp: now,
    };

    setThinking(true);
    setExpanded(true);

    setConversations((current) => current.map((conversation) => {
      if (conversation.id !== activeId) return conversation;
      const updatedMessages = [...conversation.messages, userMessage];
      return {
        ...conversation,
        messages: updatedMessages,
        updatedAt: now,
        title: makeConversationTitle(updatedMessages, locale),
      };
    }));

    try {
      const response = await api.sendCopilotChat({
        locale,
        message: prompt,
        conversation_id: targetConversation?.backendConversationId ?? null,
      });

      const assistantMessage: CopilotMessage = {
        id: response.message_id || createCopilotMessageId('assistant'),
        role: 'assistant',
        content: response.answer,
        timestamp: new Date().toISOString(),
        sourceBadges: response.sources.map((item) => item.label),
        warnings: response.warnings,
      };

      setConversations((current) => current.map((conversation) => {
        if (conversation.id !== activeId) return conversation;
        const updatedMessages = [...conversation.messages, assistantMessage];
        return {
          ...conversation,
          backendConversationId: response.conversation_id,
          messages: updatedMessages,
          updatedAt: assistantMessage.timestamp,
          title: makeConversationTitle(updatedMessages, locale),
        };
      }));
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.detail
          : error instanceof Error
            ? error.message
            : 'Request failed.';
      const assistantMessage: CopilotMessage = {
        id: createCopilotMessageId('assistant'),
        role: 'assistant',
        content: message,
        timestamp: new Date().toISOString(),
      };
      setConversations((current) => current.map((conversation) => {
        if (conversation.id !== activeId) return conversation;
        const updatedMessages = [...conversation.messages, assistantMessage];
        return {
          ...conversation,
          messages: updatedMessages,
          updatedAt: assistantMessage.timestamp,
          title: makeConversationTitle(updatedMessages, locale),
        };
      }));
    } finally {
      setThinking(false);
    }
  }

  pushUserPromptRef.current = pushUserPrompt;

  function handleNewConversation() {
    const conversation = buildFreshConversation(locale);
    setConversations((current) => [conversation, ...current]);
    setCurrentConversationId(conversation.id);
    setThinking(false);
    setExpanded(true);
    setShowHistory(false);
  }

  function handleDeleteConversation(id: string) {
    setConversations((current) => {
      const next = current.filter((item) => item.id !== id);
      if (next.length === 0) {
        const fallback = buildFreshConversation(locale);
        setCurrentConversationId(fallback.id);
        return [fallback];
      }
      if (activeConversationIdRef.current === id) {
        setCurrentConversationId(next[0].id);
      }
      return next;
    });
  }

  function handleSelectConversation(id: string) {
    setCurrentConversationId(id);
    if (viewportWidth < 1180) {
      setShowHistory(false);
    }
  }

  return (
    <div data-coresift-copilot-root="true">
      <CopilotLauncher onClick={() => setExpanded(true)} expanded={expanded} rightOffset={rightOffset} />
      <CopilotPanel
        locale={locale}
        expanded={expanded}
        viewMode={viewMode}
        showHistory={showHistory}
        currentConversationId={currentConversation.id}
        conversations={conversations}
        messages={messages}
        thinking={thinking}
        suggestions={suggestions}
        rightOffset={rightOffset}
        anchoredLeftOfRightSurface={anchoredLeftOfRightSurface}
        viewportWidth={viewportWidth}
        onClose={() => {
          setExpanded(false);
          setShowHistory(false);
        }}
        onToggleHistory={() => setShowHistory((current) => !current)}
        onSelectConversation={handleSelectConversation}
        onDeleteConversation={handleDeleteConversation}
        onSetViewMode={setViewMode}
        onNewConversation={handleNewConversation}
        onSelectSuggestion={(prompt) => void pushUserPrompt(prompt)}
        onSend={(value) => pushUserPrompt(value)}
      />
    </div>
  );
}
