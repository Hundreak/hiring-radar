export type CopilotSection = 'profile' | 'jobs' | 'matches' | 'default';
export type CopilotViewMode = 'floating' | 'sidebar' | 'fullscreen';
export type CopilotDensity = 'compact' | 'comfortable' | 'immersive';

export type CopilotMessage = {
  id: string;
  role: 'assistant' | 'user';
  content: string;
  timestamp: string;
  sourceBadges?: string[];
  warnings?: string[];
};

export type CopilotConversation = {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: CopilotMessage[];
  backendConversationId?: string | null;
};

export type CopilotSuggestion = {
  id: string;
  tag: string;
  title: string;
  prompt: string;
};

export type CopilotPromptJobAnalysisContext = {
  apiJobId: number;
  sourceSurface: 'jobs' | 'matches' | 'saved';
  title?: string;
  companyName?: string;
};

export type CopilotPromptEventDetail = {
  prompt: string;
  displayPrompt?: string;
  dedupeKey?: string;
  jobAnalysisContext?: CopilotPromptJobAnalysisContext;
};

export type CopilotCopy = {
  title: string;
  subtitle: string;
  starterTitle: string;
  starterSubtitle: string;
  composerPlaceholder: string;
  send: string;
  newConversation: string;
  close: string;
  thinking: string;
  welcomeAssistant: string;
  privacyNote: string;
  history: string;
  historyEmpty: string;
  deleteConversation: string;
  sidebarMode: string;
  floatingMode: string;
  fullscreenMode: string;
  dockRight: string;
  expandFull: string;
  collapse: string;
  quickPromptsLabel: string;
  activeConversation: string;
  switchConversation: string;
};

export const COPILOT_RIGHT_SURFACE_EVENT = 'coresift:right-surface';
export const COPILOT_PROMPT_EVENT = 'coresift:copilot-prompt';
export const COPILOT_HISTORY_STORAGE_KEY = 'coresift:copilot-history:v3';
export const COPILOT_ACTIVE_CONVERSATION_STORAGE_KEY = 'coresift:copilot-active-conversation:v3';
export const COPILOT_ROOT_SELECTOR = '[data-coresift-copilot-root="true"]';

export function dispatchCopilotPrompt(detail: string | CopilotPromptEventDetail) {
  if (typeof window === 'undefined') return;
  const normalized: CopilotPromptEventDetail =
    typeof detail === 'string' ? {prompt: detail} : detail;
  if (!normalized.prompt.trim()) return;
  window.dispatchEvent(
    new CustomEvent<CopilotPromptEventDetail>(COPILOT_PROMPT_EVENT, {detail: normalized})
  );
}

export type CopilotRightSurfaceDetail = {
  open: boolean;
  width: number;
  source?: string;
};

function parsePx(raw: string): number {
  const parsed = Number.parseFloat(raw.replace('px', '').trim());
  return Number.isFinite(parsed) ? parsed : 0;
}

export function readRightSurfaceWidth(): number {
  if (typeof document === 'undefined') return 0;
  return parsePx(getComputedStyle(document.documentElement).getPropertyValue('--coresift-right-surface-width').trim());
}

export function publishRightSurface(detail: CopilotRightSurfaceDetail) {
  if (typeof window === 'undefined' || typeof document === 'undefined') return;
  const width = detail.open ? Math.max(0, Math.round(detail.width)) : 0;
  document.documentElement.style.setProperty('--coresift-right-surface-width', `${width}px`);
  document.documentElement.dataset.coresiftRightSurface = detail.open ? 'open' : 'closed';
  window.dispatchEvent(new CustomEvent<CopilotRightSurfaceDetail>(COPILOT_RIGHT_SURFACE_EVENT, {detail: {...detail, width}}));
}

function isVisibleElement(element: HTMLElement, viewportWidth: number): {visible: boolean; footprint: number} {
  const rect = element.getBoundingClientRect();
  const style = window.getComputedStyle(element);
  const visible =
    rect.width > 0 &&
    rect.height > 0 &&
    style.display !== 'none' &&
    style.visibility !== 'hidden' &&
    Number.parseFloat(style.opacity || '1') > 0.01;

  if (!visible) {
    return {visible: false, footprint: 0};
  }

  const footprint = Math.max(rect.width, viewportWidth - rect.left);
  return {visible: true, footprint};
}

function measureRightSurface(node: HTMLElement, viewportWidth: number): number {
  const {visible, footprint} = isVisibleElement(node, viewportWidth);
  if (!visible) return 0;

  const rect = node.getBoundingClientRect();
  const style = window.getComputedStyle(node);
  if (node.closest(COPILOT_ROOT_SELECTOR)) return 0;
  if (!['fixed', 'sticky'].includes(style.position)) return 0;
  if (rect.width < 260 || rect.height < 220) return 0;
  if (rect.width >= viewportWidth * 0.72) return 0;
  if (rect.right < viewportWidth - 24) return 0;
  if (rect.left < viewportWidth * 0.5) return 0;

  return Math.max(rect.width, footprint);
}

export function detectVisibleRightSurface(): CopilotRightSurfaceDetail {
  if (typeof document === 'undefined' || typeof window === 'undefined') {
    return {open: false, width: 0};
  }

  const viewportWidth = window.innerWidth;
  if (viewportWidth < 1100) {
    return {open: false, width: 0};
  }

  const explicitSelectors = [
    '[data-coresift-right-surface="open"]',
    '[data-right-drawer="open"]',
    '[data-drawer-side="right"][data-state="open"]',
    '[data-copilot-right-surface="open"]',
    '[data-side-panel="right"][data-state="open"]',
  ];

  let width = 0;
  let source: string | undefined;

  const cssWidth = readRightSurfaceWidth();
  if (cssWidth > 0) {
    width = cssWidth;
    source = 'css-var';
  }

  for (const selector of explicitSelectors) {
    const nodes = Array.from(document.querySelectorAll<HTMLElement>(selector));
    for (const node of nodes) {
      const measured = measureRightSurface(node, viewportWidth);
      if (measured > width) {
        width = measured;
        source = selector;
      }
    }
  }

  return {open: width > 0, width, source};
}

const copyByLocale: Record<string, CopilotCopy> = {
  tr: {
    title: 'Bugün profilini nasıl güçlendirelim?',
    subtitle: 'Profilini, CV’ni ve hedef rollerini daha güçlü hale getirmek için sana net öneriler sunarım.',
    starterTitle: 'Senin için hızlı başlangıçlar',
    starterSubtitle: 'Boş bir sohbet yerine işe yarayan önerilerle başla.',
    composerPlaceholder: 'Profilin, CV’n veya hedef rollerin hakkında bir şey sor…',
    send: 'Gönder',
    newConversation: 'Yeni sohbet',
    close: 'Kapat',
    thinking: 'CoreSift AI düşünüyor…',
    welcomeAssistant: 'Merhaba, ben CoreSift AI. Profilini daha net, güçlü ve profesyonel hale getirmen için sana yardımcı olurum.',
    privacyNote: 'Yanıtlar burada yalnızca ürün içi yardımcı deneyimi için gösterilir.',
    history: 'Geçmiş sohbetler',
    historyEmpty: 'Henüz kaydedilmiş bir sohbet yok.',
    deleteConversation: 'Sohbeti sil',
    sidebarMode: 'Sağ panel',
    floatingMode: 'Serbest panel',
    fullscreenMode: 'Tam ekran',
    dockRight: 'Sağa sabitle',
    expandFull: 'Tam ekran aç',
    collapse: 'Küçült',
    quickPromptsLabel: 'Hızlı aksiyonlar',
    activeConversation: 'Aktif sohbet',
    switchConversation: 'Sohbete geç',
  },
  en: {
    title: 'How should we strengthen your profile today?',
    subtitle: 'I can help you make your profile, CV, and target roles clearer and stronger.',
    starterTitle: 'Quick starts for you',
    starterSubtitle: 'Start with prompts that move the product forward.',
    composerPlaceholder: 'Ask about your profile, CV, or target roles…',
    send: 'Send',
    newConversation: 'New chat',
    close: 'Close',
    thinking: 'CoreSift AI is thinking…',
    welcomeAssistant: 'Hello, I’m CoreSift AI. I can help you make your profile clearer, stronger, and more professional.',
    privacyNote: 'Responses shown here are for the in-product assistant experience only.',
    history: 'Past chats',
    historyEmpty: 'No saved chats yet.',
    deleteConversation: 'Delete chat',
    sidebarMode: 'Right panel',
    floatingMode: 'Floating panel',
    fullscreenMode: 'Fullscreen',
    dockRight: 'Dock right',
    expandFull: 'Open fullscreen',
    collapse: 'Minimize',
    quickPromptsLabel: 'Quick actions',
    activeConversation: 'Active chat',
    switchConversation: 'Open chat',
  },
  de: {
    title: 'Wie sollen wir dein Profil heute stärken?',
    subtitle: 'Ich helfe dir dabei, dein Profil, deinen Lebenslauf und deine Zielrollen klarer und stärker zu machen.',
    starterTitle: 'Schnelle Einstiege für dich',
    starterSubtitle: 'Starte mit Vorschlägen, die direkt weiterhelfen.',
    composerPlaceholder: 'Frage etwas zu deinem Profil, CV oder deinen Zielrollen…',
    send: 'Senden',
    newConversation: 'Neuer Chat',
    close: 'Schließen',
    thinking: 'CoreSift AI denkt nach…',
    welcomeAssistant: 'Hallo, ich bin CoreSift AI. Ich unterstütze dich dabei, dein Profil klarer, stärker und professioneller zu machen.',
    privacyNote: 'Antworten werden hier nur für das produktinterne Assistenz-Erlebnis angezeigt.',
    history: 'Chatverlauf',
    historyEmpty: 'Noch keine gespeicherten Gespräche.',
    deleteConversation: 'Gespräch löschen',
    sidebarMode: 'Rechte Seitenleiste',
    floatingMode: 'Schwebendes Panel',
    fullscreenMode: 'Vollbild',
    dockRight: 'Rechts andocken',
    expandFull: 'Vollbild',
    collapse: 'Verkleinern',
    quickPromptsLabel: 'Schnellaktionen',
    activeConversation: 'Aktiver Chat',
    switchConversation: 'Chat öffnen',
  },
};

const suggestionsByLocale: Record<string, Record<CopilotSection, CopilotSuggestion[]>> = {
  tr: {
    default: [
      {id: 'headline', tag: 'Profil', title: 'Profil başlığımı güçlendir', prompt: 'Profil başlığımı daha güçlü ve profesyonel hale getirmek için ne önerirsin?'},
      {id: 'summary', tag: 'Özet', title: 'Kısa özetimi yeniden yaz', prompt: 'Kısa özetimi daha profesyonel, net ve etkili olacak şekilde nasıl yeniden yazabiliriz?'},
      {id: 'roles', tag: 'Yön', title: 'Hangi rollere daha uygunum?', prompt: 'Mevcut profilime göre hangi teknik rollere daha yakın duruyorum?'},
      {id: 'skills', tag: 'Beceri', title: 'Becerilerimi daha iyi grupla', prompt: 'Beceri alanımı daha profesyonel ve düzenli göstermek için nasıl gruplayabilirim?'},
    ],
    profile: [
      {id: 'headline', tag: 'Profil', title: 'Profil başlığımı güçlendir', prompt: 'Profil başlığımı daha güçlü ve profesyonel hale getirmek için ne önerirsin?'},
      {id: 'summary', tag: 'Özet', title: 'Kısa özetimi yeniden yaz', prompt: 'Kısa özetimi daha profesyonel, net ve etkili olacak şekilde nasıl yeniden yazabiliriz?'},
      {id: 'gaps', tag: 'Sağlık', title: 'Eksik alanlarımı söyle', prompt: 'Profilimde eksik veya zayıf kalan alanlar neler olabilir?'},
      {id: 'roles', tag: 'Yön', title: 'Hedef rollerimi netleştir', prompt: 'Mevcut profilime göre hangi rollere odaklanmam daha mantıklı olur?'},
    ],
    jobs: [
      {id: 'fit', tag: 'Eşleşme', title: 'Bu rollere nasıl yaklaşmalıyım?', prompt: 'Benim profiline yakın rollere yaklaşırken hangi güçlü yönlerimi öne çıkarmalıyım?'},
      {id: 'cv', tag: 'CV', title: 'CV’mi başvurular için düzenle', prompt: 'Başvurular için CV’mi daha etkili göstermek adına hangi bölümleri öne çıkarmalıyım?'},
      {id: 'salary', tag: 'Pazar', title: 'Maaş araştırmasına nasıl yaklaşayım?', prompt: 'Teknik roller için maaş araştırmasını nasıl daha doğru yapabilirim?'},
      {id: 'cover', tag: 'Başvuru', title: 'Ön yazı stratejisi ver', prompt: 'Başvuru yaparken ön yazı kullanacaksam bunu nasıl daha kısa ve etkili yapabilirim?'},
    ],
    matches: [
      {id: 'match', tag: 'Eşleşme', title: 'Eşleşmemi nasıl artırırım?', prompt: 'Eşleşme kalitemi artırmak için profilimde hangi alanları güçlendirmeliyim?'},
      {id: 'gaps', tag: 'Eksik', title: 'Hangi sinyaller eksik kalıyor?', prompt: 'Teknik eşleşmelerde genelde hangi sinyaller eksik kaldığında görünürlüğüm düşer?'},
      {id: 'skills', tag: 'Beceri', title: 'Becerilerimi nasıl görünür yaparım?', prompt: 'Becerilerimi daha görünür ve daha etkili göstermek için nasıl bir yapı kullanmalıyım?'},
      {id: 'direction', tag: 'Strateji', title: 'Hangi rolleri öne almalıyım?', prompt: 'Benim profilim için hangi roller öncelikli hedef olarak daha mantıklı görünüyor?'},
    ],
  },
  en: {} as Record<CopilotSection, CopilotSuggestion[]>,
  de: {} as Record<CopilotSection, CopilotSuggestion[]>,
};
suggestionsByLocale.en = suggestionsByLocale.tr as unknown as Record<CopilotSection, CopilotSuggestion[]>;
suggestionsByLocale.de = suggestionsByLocale.tr as unknown as Record<CopilotSection, CopilotSuggestion[]>;

export function getCopilotCopy(locale: string): CopilotCopy {
  return copyByLocale[locale] ?? copyByLocale.en;
}

export function getCopilotSuggestions(locale: string, section: CopilotSection): CopilotSuggestion[] {
  const local = suggestionsByLocale[locale] ?? suggestionsByLocale.en;
  return local[section] ?? local.default;
}


function createEntropyId(prefix: string): string {
  if (typeof globalThis !== 'undefined' && 'crypto' in globalThis && typeof globalThis.crypto?.randomUUID === 'function') {
    return `${prefix}-${globalThis.crypto.randomUUID()}`
  }

  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}

export function createCopilotConversationId(): string {
  return createEntropyId('conversation')
}

export function createCopilotMessageId(role: CopilotMessage['role']): string {
  return createEntropyId(role)
}

export function normalizeCopilotMessages(messages: CopilotMessage[]): CopilotMessage[] {
  const seen = new Set<string>()

  return messages.map((message) => {
    let nextId = typeof message.id === 'string' ? message.id.trim() : ''

    if (!nextId || seen.has(nextId)) {
      nextId = createCopilotMessageId(message.role)
    }

    seen.add(nextId)

    return {
      ...message,
      id: nextId,
    }
  })
}

export function normalizeCopilotConversation(conversation: CopilotConversation): CopilotConversation {
  return {
    ...conversation,
    id: typeof conversation.id === 'string' && conversation.id.trim() ? conversation.id : createCopilotConversationId(),
    messages: normalizeCopilotMessages(Array.isArray(conversation.messages) ? conversation.messages : []),
  }
}

export function normalizeCopilotConversations(conversations: CopilotConversation[]): CopilotConversation[] {
  const seen = new Set<string>()

  return conversations.map((conversation) => {
    const normalized = normalizeCopilotConversation(conversation)
    let nextId = normalized.id

    if (seen.has(nextId)) {
      nextId = createCopilotConversationId()
    }

    seen.add(nextId)

    return {
      ...normalized,
      id: nextId,
    }
  })
}

export function buildInitialAssistantMessage(locale: string): CopilotMessage {
  return {
    id: createCopilotMessageId('assistant'),
    role: 'assistant',
    content: getCopilotCopy(locale).welcomeAssistant,
    timestamp: new Date().toISOString(),
  };
}

export function createMockAssistantReply(locale: string, prompt: string): string {
  const lower = prompt.toLocaleLowerCase(locale);
  if (lower.includes('başlık') || lower.includes('headline')) {
    return locale === 'tr'
      ? 'İlk izlenimi güçlendirmek için başlığını rol + uzmanlık + odak yapısıyla kurmak iyi olur. Örneğin: “Embedded Systems & Electronics Engineer | Product-Focused Hardware & Firmware Development”.'
      : 'A stronger first impression usually comes from a role + expertise + focus structure.';
  }
  if (lower.includes('özet') || lower.includes('summary')) {
    return locale === 'tr'
      ? 'Kısa özetinde hangi alanlarda çalıştığını, hangi problemleri çözdüğünü ve hangi rolleri hedeflediğini netleştirmen daha güçlü görünür.'
      : 'Your short summary gets stronger when it clearly states your focus, your problem-solving value, and your target roles.';
  }
  if (lower.includes('rol') || lower.includes('role')) {
    return locale === 'tr'
      ? 'Mevcut profil yapına göre teknik derinlik ve ürün odağını birlikte anlatan roller daha mantıklı görünüyor. İlk aşamada 2–3 net role odaklanman daha iyi olur.'
      : 'Roles that combine technical depth with product orientation look more aligned to your current profile.';
  }
  if (lower.includes('beceri') || lower.includes('skill')) {
    return locale === 'tr'
      ? 'Becerileri tek liste yerine kümeler halinde vermek daha profesyonel görünür. Gömülü Sistemler, Elektronik Tasarım, Firmware ve Araçlar gibi gruplar kullanabilirsin.'
      : 'Grouping skills into meaningful clusters usually looks more professional than a single long list.';
  }
  return locale === 'tr'
    ? 'Bu panel henüz yerel modele bağlı değil; ama bir sonraki adımda doğrudan profilini güçlendiren local AI akışına dönüşecek. Şu anda başlık, özet, hedef roller veya beceri yapısı üzerine odaklanabiliriz.'
    : 'This panel is not connected to the local model yet, but it is prepared for the next local AI step.';
}

export function makeConversationTitle(messages: CopilotMessage[], locale: string): string {
  const firstUser = messages.find((item) => item.role === 'user');
  if (firstUser) {
    return firstUser.content.length > 32 ? `${firstUser.content.slice(0, 32).trim()}…` : firstUser.content;
  }
  return getCopilotCopy(locale).newConversation;
}

export function formatConversationTime(value: string, locale: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return new Intl.DateTimeFormat(locale === 'tr' ? 'tr-TR' : locale === 'de' ? 'de-DE' : 'en-US', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

export function getConversationPreview(messages: CopilotMessage[], locale: string): string {
  const firstUser = messages.find((item) => item.role === 'user');
  const text = firstUser?.content ?? messages.find((item) => item.role === 'assistant')?.content ?? '';
  if (!text) return getCopilotCopy(locale).historyEmpty;
  return text.length > 64 ? `${text.slice(0, 64).trim()}…` : text;
}
