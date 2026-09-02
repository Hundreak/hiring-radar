'use client';

import {
  AlertTriangle,
  BarChart3,
  BadgeCheck,
  CalendarClock,
  CheckCircle2,
  ClipboardCopy,
  Eye,
  Gauge,
  Mail,
  MessageCircle,
  PanelRightClose,
  Send,
  ShieldCheck,
  Sparkles,
  Target,
  TimerReset,
  Users,
  Zap,
  type LucideIcon,
} from 'lucide-react';
import {useEffect, useMemo, useState} from 'react';

import {ScoreBadge, StatusBadge, SurfaceCard} from '@/components/employer/ui';
import {Button} from '@/components/ui/button';
import {CampaignAnalyticsPanel} from '@/components/employer/talent/campaign-analytics-panel';
import {SendQueueReviewBoard} from '@/components/employer/talent/send-queue-review-board';
import {loadEmployerCampaignSendQueue, prepareEmployerCampaignSendQueue} from '@/lib/employer-outreach-api';
import {getTalentWorkflowCopy} from '@/lib/employer-talent-workflow-copy';
import {cn} from '@/lib/utils';
import type {EmployerCandidateOpportunity} from '@/types/employer';
import type {EmployerOutreachCampaign, EmployerSendQueue} from '@/types/employer-outreach';

type CampaignDetailDrawerProps = {
  campaign?: EmployerOutreachCampaign | null;
  candidates: EmployerCandidateOpportunity[];
  open: boolean;
  onClose: () => void;
  onOpenCandidate?: (candidateId: number) => void;
  locale: string;
};

type CandidateMessageVariant = {
  candidate_id: number;
  subject?: string;
  message?: string;
  response_score?: number;
};

type QueueStatus = 'ready' | 'review' | 'blocked';

type SendQueueItem = {
  candidate: EmployerCandidateOpportunity;
  subject: string;
  message: string;
  responseScore: number;
  status: QueueStatus;
  checks: string[];
};

const CHANNEL_LABELS: Record<string, {label: string; icon: LucideIcon; helper: string}> = {
  email: {label: 'E-posta', icon: Mail, helper: 'Konu satırı + ölçülebilir takip'},
  linkedin: {label: 'LinkedIn', icon: Target, helper: 'Kısa ve sıcak pasif aday teması'},
  whatsapp: {label: 'WhatsApp', icon: MessageCircle, helper: 'İzinli, bağlamlı ve hızlı temas'},
};

function getMetadataArray<T>(campaign: EmployerOutreachCampaign | null | undefined, key: string): T[] {
  const value = campaign?.metadata?.[key];
  return Array.isArray(value) ? value as T[] : [];
}

function getMetadataNumber(campaign: EmployerOutreachCampaign | null | undefined, key: string, fallback: number) {
  const value = campaign?.metadata?.[key];
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

function getMetadataString(campaign: EmployerOutreachCampaign | null | undefined, key: string, fallback = '') {
  const value = campaign?.metadata?.[key];
  return typeof value === 'string' ? value : fallback;
}

function getCandidateName(candidate: EmployerCandidateOpportunity) {
  return candidate.name.split(' ')[0] ?? candidate.name;
}

function getFallbackSubject(campaign: EmployerOutreachCampaign, candidate: EmployerCandidateOpportunity) {
  const subjectPreview = getMetadataString(campaign, 'subject_preview');
  if (subjectPreview) return subjectPreview;
  const primarySkill = candidate.skills.find((skill) => skill.matched)?.name ?? candidate.skills[0]?.name ?? candidate.targetRole ?? 'rol';
  return `${primarySkill} deneyiminiz için kısa bir rol paylaşımı`;
}

function getFallbackMessage(campaign: EmployerOutreachCampaign, candidate: EmployerCandidateOpportunity) {
  if (campaign.message_preview) return campaign.message_preview;
  const skills = candidate.skills.filter((skill) => skill.matched).slice(0, 3).map((skill) => skill.name).join(', ');
  return `Merhaba ${getCandidateName(candidate)},\n\nProfilinizde ${skills || candidate.targetRole || 'rol odağı'} tarafında güçlü bir uyum görüyoruz. Açık rolümüzün kapsamını, ekip yapısını ve süreci kısa bir görüşmede paylaşmak isteriz.\n\nİlgilenir misiniz?`;
}

function evaluateQueueItem({candidate, subject, message, responseScore, campaign}: {candidate: EmployerCandidateOpportunity; subject: string; message: string; responseScore: number; campaign: EmployerOutreachCampaign}): {status: QueueStatus; checks: string[]} {
  const checks: string[] = [];
  const wordCount = message.trim().split(/\s+/).filter(Boolean).length;
  const campaignBlockers = getMetadataArray<string>(campaign, 'blockers');

  if (campaign.channel === 'email' && subject.trim().length < 12) checks.push('Konu satırı zayıf');
  if (wordCount < 35) checks.push('Mesaj kısa; aday seçilme gerekçesi eksik');
  if (campaign.channel === 'linkedin' && wordCount > 145) checks.push('LinkedIn için uzun');
  if (campaign.channel === 'whatsapp' && wordCount > 95) checks.push('WhatsApp için uzun');
  if (!/[?？]/.test(message)) checks.push('Net CTA/soru yok');
  if (candidate.intentScore < 62) checks.push('Intent düşük; mesajı daha yumuşak aç');
  if (campaignBlockers.length > 0) checks.push(...campaignBlockers);

  if (checks.some((item) => item.toLocaleLowerCase('tr-TR').includes('konu') || item.toLocaleLowerCase('tr-TR').includes('blocker'))) return {status: 'blocked', checks};
  if (checks.length > 0 || responseScore < 62) return {status: 'review', checks};
  return {status: 'ready', checks: ['Gönderime hazır']};
}

function buildSendQueue(campaign: EmployerOutreachCampaign, candidates: EmployerCandidateOpportunity[]): SendQueueItem[] {
  const variants = getMetadataArray<CandidateMessageVariant>(campaign, 'candidate_messages');
  const variantByCandidateId = new Map<number, CandidateMessageVariant>();
  variants.forEach((variant) => {
    if (typeof variant.candidate_id === 'number') variantByCandidateId.set(variant.candidate_id, variant);
  });

  return campaign.candidate_ids
    .map((candidateId) => {
      const candidate = candidates.find((item) => item.id === candidateId);
      if (!candidate) return null;
      const variant = variantByCandidateId.get(candidate.id);
      const subject = variant?.subject || getFallbackSubject(campaign, candidate);
      const message = variant?.message || getFallbackMessage(campaign, candidate);
      const responseScore = typeof variant?.response_score === 'number' ? variant.response_score : campaign.response_rate;
      const status = evaluateQueueItem({candidate, subject, message, responseScore, campaign});
      return {candidate, subject, message, responseScore, ...status};
    })
    .filter(Boolean) as SendQueueItem[];
}

function getStatusTone(status: QueueStatus): 'success' | 'warning' | 'danger' {
  if (status === 'ready') return 'success';
  if (status === 'review') return 'warning';
  return 'danger';
}

function getStatusLabel(status: QueueStatus) {
  if (status === 'ready') return 'Hazır';
  if (status === 'review') return 'Review';
  return 'Bloker';
}

function formatDate(value?: string) {
  if (!value) return 'Tarih yok';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('tr-TR', {day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'}).format(date);
}

export function CampaignDetailDrawer({campaign, candidates, open, onClose, onOpenCandidate, locale}: CampaignDetailDrawerProps) {
  const copy = getTalentWorkflowCopy(locale);
  const [tab, setTab] = useState<'queue' | 'review' | 'analytics' | 'messages' | 'qa'>('queue');
  const [activeCandidateId, setActiveCandidateId] = useState<number | null>(null);
  const [queued, setQueued] = useState(false);
  const [backendQueue, setBackendQueue] = useState<EmployerSendQueue | null>(null);
  const [queueSaving, setQueueSaving] = useState(false);
  const [queueError, setQueueError] = useState<string | null>(null);

  const queue = useMemo(() => campaign ? buildSendQueue(campaign, candidates) : [], [campaign, candidates]);
  const activeItem = useMemo(() => {
    return queue.find((item) => item.candidate.id === activeCandidateId) ?? queue[0] ?? null;
  }, [activeCandidateId, queue]);

  useEffect(() => {
    if (!open || !campaign) return;
    let cancelled = false;
    setActiveCandidateId(null);
    setQueued(false);
    setBackendQueue(null);
    setQueueError(null);

    loadEmployerCampaignSendQueue(campaign.id)
      .then((queuePayload) => {
        if (cancelled) return;
        setBackendQueue(queuePayload);
        setQueued(Boolean(queuePayload));
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setQueueError(error instanceof Error ? error.message : 'Gönderim kuyruğu yüklenemedi.');
      });

    return () => {
      cancelled = true;
    };
  }, [campaign, open]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [onClose, open]);

  if (!open || !campaign) return null;

  const channelMeta = CHANNEL_LABELS[campaign.channel] ?? CHANNEL_LABELS.email;
  const ChannelIcon = channelMeta.icon;
  const qualityScore = getMetadataNumber(campaign, 'quality_score', campaign.response_rate);
  const readinessScore = getMetadataNumber(campaign, 'readiness_score', Math.round((qualityScore + campaign.response_rate) / 2));
  const warnings = getMetadataArray<string>(campaign, 'warnings');
  const blockers = getMetadataArray<string>(campaign, 'blockers');
  const readyCount = queue.filter((item) => item.status === 'ready').length;
  const reviewCount = queue.filter((item) => item.status === 'review').length;
  const blockedCount = queue.filter((item) => item.status === 'blocked').length;
  const estimatedReadyRate = queue.length ? Math.round((readyCount / queue.length) * 100) : 0;

  const prepareQueue = async () => {
    if (!campaign || blockedCount > 0 || queue.length === 0) return;
    setQueueSaving(true);
    setQueueError(null);
    try {
      const preparedQueue = await prepareEmployerCampaignSendQueue(campaign.id, {
        actor: 'Sen',
        note: `${campaign.name} için ${queue.length} adaylık gönderim kuyruğu hazırlandı.`,
        items: queue.map((item) => ({
          candidate_id: item.candidate.id,
          subject: item.subject,
          message: item.message,
          response_score: item.responseScore,
          status: item.status,
          checks: item.checks,
          metadata: {
            candidate_name: item.candidate.name,
            match_score: item.candidate.matchScore,
            intent_score: item.candidate.intentScore,
            availability: item.candidate.availability,
          },
        })),
      });
      setBackendQueue(preparedQueue);
      setQueued(true);
      setTab('review');
    } catch (error) {
      setQueueError(error instanceof Error ? error.message : 'Gönderim kuyruğu kaydedilemedi.');
    } finally {
      setQueueSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[90] flex justify-end">
      <button type="button" aria-label="Kampanya detayını kapat" className="absolute inset-0 bg-slate-950/55 backdrop-blur-sm" onClick={onClose} />
      <aside className="relative z-10 flex h-full w-full max-w-6xl flex-col overflow-hidden border-l border-border bg-background shadow-[0_32px_120px_rgba(15,23,42,0.45)] xl:rounded-l-[34px]">
        <div className="border-b border-border bg-surface/95 p-4 backdrop-blur-xl sm:p-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <StatusBadge tone="ai" icon={<Send className="size-3.5" />}>Send Queue Stub</StatusBadge>
                <StatusBadge tone={campaign.status === 'draft' ? 'warning' : 'success'}>{campaign.status}</StatusBadge>
                <StatusBadge tone="info" icon={<ChannelIcon className="size-3.5" />}>{channelMeta.label}</StatusBadge>
              </div>
              <h2 className="mt-3 max-w-3xl truncate text-2xl font-black tracking-[-0.04em] text-foreground sm:text-3xl">{campaign.name}</h2>
              <p className="mt-2 max-w-3xl text-sm font-semibold leading-6 text-muted-foreground">
                Aday bazlı mesaj varyantlarını, kalite kontrollerini ve gönderim kuyruğunu gerçek entegrasyon öncesi tek ekranda yönet.
              </p>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <Button variant="secondary" size="sm" className="gap-2" onClick={() => activeItem && void navigator.clipboard?.writeText(activeItem.message)}>
                <ClipboardCopy className="size-4" />
                Aktif mesajı kopyala
              </Button>
              <button type="button" onClick={onClose} className="inline-flex size-10 items-center justify-center rounded-2xl border border-border bg-surface text-muted-foreground transition hover:bg-surface-strong hover:text-foreground focus:outline-none focus:ring-4 focus:ring-[var(--ring)]" aria-label="Kapat">
                <PanelRightClose className="size-5" />
              </button>
            </div>
          </div>

          <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
            <QueueMetric icon={Users} label={copy.common.candidate} value={queue.length} helper={locale.startsWith('tr') ? 'kampanya kapsamı' : 'campaign scope'} />
            <QueueMetric icon={Gauge} label={copy.common.readiness} value={`${Math.min(99, readinessScore)}`} helper={locale.startsWith('tr') ? 'kalite + yanıt' : 'quality + response'} />
            <QueueMetric icon={MousePointerIcon} label={copy.campaignDetail.responseEstimate} value={`${campaign.response_rate}%`} helper={channelMeta.helper} />
            <QueueMetric icon={CheckCircle2} label={copy.common.ready} value={`${readyCount}`} helper={`${estimatedReadyRate}% ${copy.common.queue}`} />
            <QueueMetric icon={AlertTriangle} label="Kontrol" value={reviewCount + blockedCount} helper={`${blockedCount} ${copy.common.blockers}`} />
          </div>
        </div>

        <div className="border-b border-border bg-surface-muted/35 px-4 py-3 sm:px-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="inline-flex rounded-2xl border border-border bg-surface p-1">
              {[
                ['queue', copy.campaignDetail.tabs.queue, Send],
                ['review', copy.campaignDetail.tabs.review, BadgeCheck],
                ['analytics', copy.campaignDetail.tabs.analytics, BarChart3],
                ['messages', copy.campaignDetail.tabs.messages, Mail],
                ['qa', copy.campaignDetail.tabs.guardrails, ShieldCheck],
              ].map(([id, label, Icon]) => (
                <button
                  key={id as string}
                  type="button"
                  onClick={() => setTab(id as typeof tab)}
                  className={cn(
                    'inline-flex h-9 items-center gap-2 rounded-xl px-3 text-xs font-black transition focus:outline-none focus:ring-4 focus:ring-[var(--ring)]',
                    tab === id ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground hover:bg-surface-muted hover:text-foreground'
                  )}
                >
                  <Icon className="size-4" />
                  {label as string}
                </button>
              ))}
            </div>
            <div className="flex flex-wrap items-center gap-2 text-xs font-bold text-muted-foreground">
              <span>Oluşturuldu: {formatDate(campaign.created_at)}</span>
              <span className="hidden sm:inline">·</span>
              <span>Güncellendi: {formatDate(campaign.updated_at ?? campaign.created_at)}</span>
            </div>
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto p-4 sm:p-5">
          {tab === 'queue' && (
            <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_380px]">
              <div className="space-y-3">
                {queue.map((item) => (
                  <QueueCandidateRow
                    key={item.candidate.id}
                    item={item}
                    selected={activeItem?.candidate.id === item.candidate.id}
                    onSelect={() => setActiveCandidateId(item.candidate.id)}
                    onOpenCandidate={() => onOpenCandidate?.(item.candidate.id)}
                  />
                ))}
              </div>
              <SendQueuePanel
                locale={locale}
                readyCount={readyCount}
                reviewCount={reviewCount}
                blockedCount={blockedCount}
                queued={queued}
                backendQueue={backendQueue}
                saving={queueSaving}
                error={queueError}
                disabled={blockedCount > 0 || queue.length === 0 || queueSaving}
                onQueue={() => void prepareQueue()}
              />
            </div>
          )}

          {tab === 'review' && (
            <SendQueueReviewBoard
              campaignId={campaign.id}
              localItems={queue.map((item) => ({
                candidate: item.candidate,
                subject: item.subject,
                message: item.message,
                responseScore: item.responseScore,
                status: item.status,
                checks: item.checks,
              }))}
              backendQueue={backendQueue}
              onQueueChange={(nextQueue) => {
                setBackendQueue(nextQueue);
                setQueued(true);
              }}
              onOpenCandidate={onOpenCandidate}
              locale={locale}
            />
          )}

          {tab === 'analytics' && (
            <CampaignAnalyticsPanel
              campaign={campaign}
              candidates={candidates}
              locale={locale}
              localQueue={queue.map((item) => ({
                candidate: item.candidate,
                status: item.status,
                responseScore: item.responseScore,
                checks: item.checks,
              }))}
              backendQueue={backendQueue}
            />
          )}

          {tab === 'messages' && (
            <div className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
              <div className="space-y-2">
                {queue.map((item) => (
                  <button
                    key={item.candidate.id}
                    type="button"
                    onClick={() => setActiveCandidateId(item.candidate.id)}
                    className={cn(
                      'w-full rounded-[22px] border p-3 text-left transition focus:outline-none focus:ring-4 focus:ring-[var(--ring)]',
                      activeItem?.candidate.id === item.candidate.id ? 'border-primary/50 bg-primary/10' : 'border-border bg-surface hover:border-primary/30 hover:bg-surface-strong'
                    )}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-black text-foreground">{item.candidate.name}</p>
                        <p className="mt-1 line-clamp-1 text-xs font-semibold text-muted-foreground">{item.subject}</p>
                      </div>
                      <StatusBadge tone={getStatusTone(item.status)}>{getStatusLabel(item.status)}</StatusBadge>
                    </div>
                  </button>
                ))}
              </div>
              {activeItem && <MessagePreview item={activeItem} onOpenCandidate={() => onOpenCandidate?.(activeItem.candidate.id)} />}
            </div>
          )}

          {tab === 'qa' && (
            <CampaignQualityPanel
              qualityScore={qualityScore}
              readinessScore={readinessScore}
              warnings={warnings}
              blockers={blockers}
              queue={queue}
              campaign={campaign}
            />
          )}
        </div>
      </aside>
    </div>
  );
}

function QueueMetric({icon: Icon, label, value, helper}: {icon: LucideIcon; label: string; value: string | number; helper: string}) {
  return (
    <div className="rounded-[24px] border border-border bg-surface p-4 shadow-sm">
      <div className="flex items-center gap-3">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary"><Icon className="size-5" /></span>
        <div className="min-w-0">
          <p className="truncate text-[10px] font-black uppercase tracking-[0.14em] text-muted-foreground">{label}</p>
          <p className="text-2xl font-black tracking-[-0.04em] text-foreground">{value}</p>
          <p className="truncate text-xs font-semibold text-muted-foreground">{helper}</p>
        </div>
      </div>
    </div>
  );
}

function QueueCandidateRow({item, selected, onSelect, onOpenCandidate}: {item: SendQueueItem; selected: boolean; onSelect: () => void; onOpenCandidate: () => void}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        'w-full rounded-[26px] border bg-surface p-4 text-left transition hover:border-primary/35 hover:bg-surface-strong focus:outline-none focus:ring-4 focus:ring-[var(--ring)]',
        selected && 'border-primary/55 ring-4 ring-[var(--ring)]'
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex min-w-0 items-start gap-3">
          <span className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,var(--primary),var(--accent))] text-xs font-black text-primary-foreground">
            {item.candidate.initials}
          </span>
          <span className="min-w-0">
            <span className="flex flex-wrap items-center gap-2">
              <span className="truncate text-sm font-black text-foreground">{item.candidate.name}</span>
              <StatusBadge tone={getStatusTone(item.status)}>{getStatusLabel(item.status)}</StatusBadge>
            </span>
            <span className="mt-1 line-clamp-1 text-xs font-semibold text-muted-foreground">{item.subject}</span>
            <span className="mt-2 flex flex-wrap gap-2">
              <MiniPill icon={Zap} label={`Yanıt ${item.responseScore}%`} />
              <MiniPill icon={Target} label={`Match ${item.candidate.matchScore}`} />
              <MiniPill icon={CalendarClock} label={item.candidate.availability === 'immediate' ? 'Hemen' : item.candidate.availability === 'two_weeks' ? '2 hafta' : item.candidate.availability === 'one_month' ? '1 ay' : 'Pasif'} />
            </span>
          </span>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-2">
          <ScoreBadge score={item.responseScore} label="Yanıt" size="sm" />
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              onOpenCandidate();
            }}
            className="inline-flex items-center gap-1 rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-[11px] font-black text-primary transition hover:bg-primary/15"
          >
            360 <Eye className="size-3.5" />
          </button>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-2 border-t border-border/70 pt-3">
        {item.checks.slice(0, 3).map((check) => (
          <span key={check} className={cn('rounded-full border px-2.5 py-1 text-[11px] font-black', item.status === 'ready' ? 'border-success/20 bg-success/10 text-success' : item.status === 'review' ? 'border-warning/20 bg-warning/10 text-warning' : 'border-danger/20 bg-danger/10 text-danger')}>
            {check}
          </span>
        ))}
      </div>
    </button>
  );
}

function MiniPill({icon: Icon, label}: {icon: LucideIcon; label: string}) {
  return <span className="inline-flex items-center gap-1 rounded-full border border-border bg-surface-muted px-2.5 py-1 text-[11px] font-bold text-muted-foreground"><Icon className="size-3.5" />{label}</span>;
}

function SendQueuePanel({locale, readyCount, reviewCount, blockedCount, queued, backendQueue, saving, error, disabled, onQueue}: {locale: string; readyCount: number; reviewCount: number; blockedCount: number; queued: boolean; backendQueue: EmployerSendQueue | null; saving: boolean; error: string | null; disabled: boolean; onQueue: () => void}) {
  const copy = getTalentWorkflowCopy(locale);
  return (
    <SurfaceCard variant="elevated" padding="none" className="overflow-hidden xl:sticky xl:top-4 xl:self-start">
      <div className="border-b border-border p-4">
        <p className="text-sm font-black text-foreground">{copy.campaignDetail.sendQueue}</p>
        <p className="mt-1 text-xs font-semibold text-muted-foreground">{locale.startsWith('tr') ? 'Kuyruk arka uca kaydedilir; gerçek e-posta/LinkedIn/WhatsApp gönderimi sonraki entegrasyon katmanında açılır.' : 'The queue is saved to the backend; real email/LinkedIn/WhatsApp sending opens in the next integration layer.'}</p>
      </div>
      <div className="space-y-3 p-4">
        <QueueStateRow tone="success" label={copy.campaignDetail.readyToSend} value={readyCount} />
        <QueueStateRow tone="warning" label={copy.campaignDetail.needsReview} value={reviewCount} />
        <QueueStateRow tone="danger" label={copy.campaignDetail.hasBlocker} value={blockedCount} />
        <div className="rounded-[24px] border border-primary/20 bg-primary/10 p-4">
          <div className="flex items-start gap-3">
            <Sparkles className="mt-0.5 size-5 shrink-0 text-primary" />
            <div>
              <p className="text-sm font-black text-foreground">{locale.startsWith('tr') ? 'Sonraki arka uç adımı' : 'Next backend step'}</p>
              <p className="mt-1 text-xs font-semibold leading-5 text-muted-foreground">{locale.startsWith('tr') ? 'Bu kuyruk ileride e-posta sağlayıcısı, LinkedIn manuel görevleri ve WhatsApp izinli mesaj akışına bağlanacak.' : 'This queue can later connect to email providers, LinkedIn manual tasks and consent-based WhatsApp messaging.'}</p>
            </div>
          </div>
        </div>
        {queued && backendQueue && (
          <div className="rounded-2xl border border-success/25 bg-success/10 p-3 text-sm font-semibold leading-6 text-success">
            {locale.startsWith('tr') ? 'Kuyruk arka uca kaydedildi.' : 'Queue saved to backend.'} {backendQueue.ready_count} {locale.startsWith('tr') ? 'hazır,' : 'ready,'} {backendQueue.review_count} {locale.startsWith('tr') ? 'kontrol,' : 'review,'} {backendQueue.blocked_count} {locale.startsWith('tr') ? 'engel.' : 'blocked.'} {copy.common.audit}: {backendQueue.audit?.length ?? 0} kayıt.
          </div>
        )}
        {queued && !backendQueue && (
          <div className="rounded-2xl border border-success/25 bg-success/10 p-3 text-sm font-semibold leading-6 text-success">
            {locale.startsWith('tr') ? 'Kuyruk hazırlandı. Arka uç senkronizasyonu bekleniyor.' : 'Queue prepared. Waiting for backend sync.'}
          </div>
        )}
        {error && (
          <div className="rounded-2xl border border-warning/25 bg-warning/10 p-3 text-sm font-semibold leading-6 text-warning">
            {error}
          </div>
        )}
        <Button className="h-12 w-full gap-2 rounded-[22px]" disabled={disabled} onClick={onQueue}>
          {saving ? <TimerReset className="size-4 animate-spin" /> : blockedCount > 0 ? <AlertTriangle className="size-4" /> : <Send className="size-4" />}
          {saving ? (locale.startsWith('tr') ? 'Kuyruk kaydediliyor...' : 'Saving queue...') : blockedCount > 0 ? (locale.startsWith('tr') ? 'Engelleri temizle' : 'Clear blockers') : backendQueue ? (locale.startsWith('tr') ? 'Kuyruğu yeniden hazırla' : 'Prepare queue again') : copy.campaignDetail.prepareQueue}
        </Button>
      </div>
    </SurfaceCard>
  );
}

function QueueStateRow({tone, label, value}: {tone: 'success' | 'warning' | 'danger'; label: string; value: number}) {
  const toneClass = tone === 'success' ? 'bg-success/10 text-success border-success/20' : tone === 'warning' ? 'bg-warning/10 text-warning border-warning/20' : 'bg-danger/10 text-danger border-danger/20';
  return (
    <div className={cn('flex items-center justify-between rounded-2xl border px-3 py-2', toneClass)}>
      <span className="text-sm font-black">{label}</span>
      <span className="text-lg font-black">{value}</span>
    </div>
  );
}

function MessagePreview({item, onOpenCandidate}: {item: SendQueueItem; onOpenCandidate: () => void}) {
  return (
    <SurfaceCard variant="elevated" padding="none" className="overflow-hidden">
      <div className="border-b border-border p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-sm font-black text-foreground">{item.candidate.name}</p>
            <p className="mt-1 text-xs font-semibold text-muted-foreground">Aday bazlı mesaj varyantı</p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" className="gap-2" onClick={() => void navigator.clipboard?.writeText(item.message)}><ClipboardCopy className="size-4" />Kopyala</Button>
            <Button variant="ghost" size="sm" className="gap-2" onClick={onOpenCandidate}><Eye className="size-4" />360</Button>
          </div>
        </div>
      </div>
      <div className="space-y-4 p-4">
        <div className="rounded-[24px] border border-border bg-surface-muted/40 p-4">
          <p className="text-xs font-black uppercase tracking-[0.14em] text-muted-foreground">Konu</p>
          <p className="mt-2 text-base font-black text-foreground">{item.subject}</p>
        </div>
        <div className="rounded-[24px] border border-border bg-surface p-4">
          <p className="text-xs font-black uppercase tracking-[0.14em] text-muted-foreground">Mesaj</p>
          <p className="mt-3 whitespace-pre-wrap text-sm font-semibold leading-7 text-foreground">{item.message}</p>
        </div>
      </div>
    </SurfaceCard>
  );
}

function CampaignQualityPanel({qualityScore, readinessScore, warnings, blockers, queue, campaign}: {qualityScore: number; readinessScore: number; warnings: string[]; blockers: string[]; queue: SendQueueItem[]; campaign: EmployerOutreachCampaign}) {
  const personalization = getMetadataString(campaign, 'personalization_depth', 'balanced');
  const followUp = getMetadataString(campaign, 'follow_up_cadence', 'three_day');
  const readyCount = queue.filter((item) => item.status === 'ready').length;
  const reviewCount = queue.filter((item) => item.status !== 'ready').length;

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_380px]">
      <div className="space-y-4">
        <SurfaceCard variant="elevated" padding="lg">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-black text-foreground">Kampanya kalite raporu</p>
              <p className="mt-1 max-w-2xl text-sm font-semibold leading-6 text-muted-foreground">Bu rapor gönderimden önce mesaj kalitesi, kanal riski, kişiselleştirme ve aday bazlı readiness sinyallerini kontrol eder.</p>
            </div>
            <div className="flex gap-2">
              <ScoreBadge score={qualityScore} label="Kalite" />
              <ScoreBadge score={readinessScore} label="Ready" />
            </div>
          </div>
          <div className="mt-5 grid gap-3 md:grid-cols-3">
            <QualityMetric icon={Users} label="Hazır aday" value={readyCount} helper="güvenli kuyruk" />
            <QualityMetric icon={AlertTriangle} label="Kontrol" value={reviewCount} helper="manuel kontrol" />
            <QualityMetric icon={TimerReset} label="Takip" value={followUp === 'none' ? 'Yok' : followUp === 'three_day' ? '3 gün' : '5 gün'} helper="cadence" />
          </div>
        </SurfaceCard>

        {blockers.length > 0 && <FindingBlock tone="danger" title="Blokerler" items={blockers} />}
        {warnings.length > 0 && <FindingBlock tone="warning" title="İyileştirme önerileri" items={warnings} />}
        {blockers.length === 0 && warnings.length === 0 && (
          <FindingBlock tone="success" title="Gönderim kalitesi iyi" items={['Kampanya mesajları kanal ve kişiselleştirme açısından temiz görünüyor.', 'Gerçek gönderim entegrasyonu eklenince bu taslak güvenli kuyruğa alınabilir.']} />
        )}
      </div>

      <SurfaceCard variant="muted" padding="lg" className="xl:sticky xl:top-4 xl:self-start">
        <div className="flex items-center gap-3">
          <span className="flex size-11 items-center justify-center rounded-2xl bg-primary/10 text-primary"><ShieldCheck className="size-5" /></span>
          <div>
            <p className="text-sm font-black text-foreground">Compliance notu</p>
            <p className="text-xs font-semibold text-muted-foreground">Human-in-the-loop outreach</p>
          </div>
        </div>
        <div className="mt-4 space-y-3 text-sm font-semibold leading-6 text-muted-foreground">
          <p>Mesajlar yalnızca beceri, rol uyumu, müsaitlik ve açık iş bilgileri üzerinden hazırlanır.</p>
          <p>Hassas özellik, varsayım veya ayrımcı kriter kullanılmamalı. WhatsApp gibi doğrudan kanallarda izin ve bağlam ayrıca doğrulanmalı.</p>
          <p className="rounded-2xl border border-border bg-surface p-3 text-xs font-black text-foreground">Kişiselleştirme: {personalization} · Kanal: {campaign.channel} · Şablon: {campaign.template}</p>
        </div>
      </SurfaceCard>
    </div>
  );
}

function QualityMetric({icon: Icon, label, value, helper}: {icon: LucideIcon; label: string; value: string | number; helper: string}) {
  return (
    <div className="rounded-[24px] border border-border bg-surface p-4">
      <Icon className="size-5 text-primary" />
      <p className="mt-3 text-xs font-black uppercase tracking-[0.14em] text-muted-foreground">{label}</p>
      <p className="text-2xl font-black tracking-[-0.04em] text-foreground">{value}</p>
      <p className="text-xs font-semibold text-muted-foreground">{helper}</p>
    </div>
  );
}

function FindingBlock({tone, title, items}: {tone: 'success' | 'warning' | 'danger'; title: string; items: string[]}) {
  const toneClass = tone === 'success' ? 'border-success/25 bg-success/10 text-success' : tone === 'warning' ? 'border-warning/25 bg-warning/10 text-warning' : 'border-danger/25 bg-danger/10 text-danger';
  return (
    <div className={cn('rounded-[28px] border p-5', toneClass)}>
      <p className="text-sm font-black text-foreground">{title}</p>
      <ul className="mt-3 space-y-2 text-sm font-semibold leading-6">
        {items.map((item) => <li key={item}>• {item}</li>)}
      </ul>
    </div>
  );
}

const MousePointerIcon = Zap;
