'use client';

import {
  Activity,
  AlertTriangle,
  BarChart3,
  Clock3,
  Gauge,
  MailCheck,
  MessageSquareText,
  Radar,
  ShieldCheck,
  Sparkles,
  Target,
  Users,
  Zap,
  type LucideIcon,
} from 'lucide-react';
import {useMemo} from 'react';

import {ScoreBadge, StatusBadge, SurfaceCard} from '@/components/employer/ui';
import {formatCompactNumber} from '@/lib/employer-format';
import {cn} from '@/lib/utils';
import type {EmployerCandidateOpportunity} from '@/types/employer';
import type {EmployerOutreachCampaign, EmployerSendQueue} from '@/types/employer-outreach';

type AnalyticsQueueItem = {
  candidate: EmployerCandidateOpportunity;
  status: 'ready' | 'review' | 'blocked';
  responseScore: number;
  checks: string[];
};

type CampaignAnalyticsPanelProps = {
  campaign: EmployerOutreachCampaign;
  candidates: EmployerCandidateOpportunity[];
  localQueue: AnalyticsQueueItem[];
  backendQueue: EmployerSendQueue | null;
  locale?: string;
};

type AnalyticsSummary = {
  total: number;
  ready: number;
  review: number;
  blocked: number;
  readyRate: number;
  reviewLoad: number;
  averageResponse: number;
  averageMatch: number;
  averageIntent: number;
  highIntent: number;
  immediate: number;
  channelHealth: number;
  complianceHealth: number;
  campaignHealth: number;
};

const CHANNEL_LABELS: Record<string, string> = {
  email: 'E-posta',
  linkedin: 'LinkedIn',
  whatsapp: 'WhatsApp',
};

const CHANNEL_BENCHMARKS: Record<string, {label: string; expectedReply: number; risk: string; recommendation: string}> = {
  email: {
    label: 'E-posta',
    expectedReply: 38,
    risk: 'Konu satırı, deliverability ve follow-up kalitesi belirleyici.',
    recommendation: 'Konu satırı net, mesaj 120-180 kelime ve tek CTA ile ilerlemeli.',
  },
  linkedin: {
    label: 'LinkedIn',
    expectedReply: 46,
    risk: 'Mesaj uzunluğu ve aşırı satış dili pasif adayda düşüş yaratır.',
    recommendation: 'İlk mesaj 70-120 kelime; teknik kanıt + kısa soru en iyi akış.',
  },
  whatsapp: {
    label: 'WhatsApp',
    expectedReply: 52,
    risk: 'İzin, bağlam ve zamanlama hassas; sıcak adaylarda kullanılmalı.',
    recommendation: 'Kısa, izinli, bağlamlı ve tek aksiyonlu mesaj tercih edilmeli.',
  },
};

function clamp(value: number, min = 0, max = 100) {
  return Math.max(min, Math.min(max, Math.round(value)));
}

function average(values: number[]) {
  if (!values.length) return 0;
  return Math.round(values.reduce((sum, value) => sum + value, 0) / values.length);
}

function getMetadataNumber(campaign: EmployerOutreachCampaign, key: string, fallback: number) {
  const value = campaign.metadata?.[key];
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

function getMetadataString(campaign: EmployerOutreachCampaign, key: string, fallback = '') {
  const value = campaign.metadata?.[key];
  return typeof value === 'string' ? value : fallback;
}

function getWorkflowLabel(value: string) {
  if (value === 'three_day') return '3 gün sonra';
  if (value === 'five_day') return '5 gün sonra';
  if (value === 'none') return 'Takip yok';
  return value || 'Belirtilmedi';
}

function getPersonalizationLabel(value: string) {
  if (value === 'deep') return 'Derin';
  if (value === 'concise') return 'Kısa';
  if (value === 'balanced') return 'Dengeli';
  return value || 'Dengeli';
}

function formatDate(value?: string) {
  if (!value) return 'Tarih yok';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('tr-TR', {day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'}).format(date);
}

function buildSummary(campaign: EmployerOutreachCampaign, queue: AnalyticsQueueItem[]): AnalyticsSummary {
  const total = queue.length;
  const ready = queue.filter((item) => item.status === 'ready').length;
  const review = queue.filter((item) => item.status === 'review').length;
  const blocked = queue.filter((item) => item.status === 'blocked').length;
  const averageResponse = average(queue.map((item) => item.responseScore));
  const averageMatch = average(queue.map((item) => item.candidate.matchScore));
  const averageIntent = average(queue.map((item) => item.candidate.intentScore));
  const highIntent = queue.filter((item) => item.candidate.intentScore >= 78).length;
  const immediate = queue.filter((item) => item.candidate.availability === 'immediate' || item.candidate.availability === 'two_weeks').length;
  const readyRate = total ? clamp((ready / total) * 100) : 0;
  const reviewLoad = total ? clamp(((review + blocked) / total) * 100) : 0;
  const qualityScore = getMetadataNumber(campaign, 'quality_score', averageResponse);
  const readinessScore = getMetadataNumber(campaign, 'readiness_score', Math.round((qualityScore + averageResponse) / 2));
  const channelBenchmark = CHANNEL_BENCHMARKS[campaign.channel]?.expectedReply ?? 40;
  const channelHealth = clamp(62 + (averageResponse - channelBenchmark) * 0.75 + readyRate * 0.18 - blocked * 7);
  const complianceHealth = clamp(92 - blocked * 18 - review * 5 + ready * 2);
  const campaignHealth = clamp(qualityScore * 0.28 + readinessScore * 0.28 + readyRate * 0.18 + averageResponse * 0.16 + complianceHealth * 0.1);

  return {total, ready, review, blocked, readyRate, reviewLoad, averageResponse, averageMatch, averageIntent, highIntent, immediate, channelHealth, complianceHealth, campaignHealth};
}

function getMostCommonChecks(queue: AnalyticsQueueItem[]) {
  const counts = new Map<string, number>();
  queue.forEach((item) => {
    item.checks.forEach((check) => counts.set(check, (counts.get(check) ?? 0) + 1));
  });
  return Array.from(counts.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([label, count]) => ({label, count}));
}

function getTopCandidates(queue: AnalyticsQueueItem[]) {
  return [...queue]
    .sort((a, b) => (b.responseScore + b.candidate.matchScore + b.candidate.intentScore) - (a.responseScore + a.candidate.matchScore + a.candidate.intentScore))
    .slice(0, 4);
}

function getSourceMix(queue: AnalyticsQueueItem[]) {
  const counts = new Map<string, number>();
  queue.forEach((item) => counts.set(item.candidate.source, (counts.get(item.candidate.source) ?? 0) + 1));
  return Array.from(counts.entries())
    .sort((a, b) => b[1] - a[1])
    .map(([source, count]) => ({source, count}));
}

function sourceLabel(source: string) {
  if (source === 'talent_radar') return 'Talent Radar';
  if (source === 'linkedin') return 'LinkedIn';
  if (source === 'referral') return 'Referans';
  if (source === 'application') return 'Başvuru';
  return source.split('_').join(' ');
}

export function CampaignAnalyticsPanel({campaign, candidates, localQueue, backendQueue}: CampaignAnalyticsPanelProps) {
  const queue = useMemo<AnalyticsQueueItem[]>(() => {
    if (!backendQueue?.items?.length) return localQueue;
    return backendQueue.items
      .map((item) => {
        const candidate = candidates.find((candidateItem) => candidateItem.id === item.candidate_id);
        if (!candidate) return null;
        return {
          candidate,
          status: item.status,
          responseScore: item.response_score,
          checks: Array.isArray(item.checks) ? item.checks : [],
        } satisfies AnalyticsQueueItem;
      })
      .filter(Boolean) as AnalyticsQueueItem[];
  }, [backendQueue, candidates, localQueue]);

  const summary = useMemo(() => buildSummary(campaign, queue), [campaign, queue]);
  const commonChecks = useMemo(() => getMostCommonChecks(queue), [queue]);
  const topCandidates = useMemo(() => getTopCandidates(queue), [queue]);
  const sourceMix = useMemo(() => getSourceMix(queue), [queue]);
  const channelBenchmark = CHANNEL_BENCHMARKS[campaign.channel] ?? CHANNEL_BENCHMARKS.email;
  const personalization = getPersonalizationLabel(getMetadataString(campaign, 'personalization_depth', 'balanced'));
  const followUp = getWorkflowLabel(getMetadataString(campaign, 'follow_up_cadence', 'three_day'));
  const backendSynced = Boolean(backendQueue?.items?.length);

  return (
    <div className="space-y-4">
      <SurfaceCard variant="elevated" padding="lg" className="overflow-hidden">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge tone="ai" icon={<BarChart3 className="size-3.5" />}>Campaign Analytics</StatusBadge>
              <StatusBadge tone={backendSynced ? 'success' : 'warning'}>{backendSynced ? 'Backend queue' : 'Taslak simülasyon'}</StatusBadge>
              <StatusBadge tone="info">{CHANNEL_LABELS[campaign.channel] ?? campaign.channel}</StatusBadge>
            </div>
            <h3 className="mt-3 text-2xl font-black tracking-[-0.04em] text-foreground">Kampanya sağlık merkezi</h3>
            <p className="mt-2 max-w-3xl text-sm font-semibold leading-6 text-muted-foreground">
              Hazır/review/bloker dağılımını, kanal kalitesini, aday yanıt potansiyelini ve audit sinyallerini tek ekranda izle. Bu ekran gerçek gönderim entegrasyonundan önce operasyon güvenliği sağlar.
            </p>
          </div>
          <div className="grid min-w-[260px] grid-cols-2 gap-2">
            <ScoreBadge score={summary.campaignHealth} label="Health" className="justify-center" />
            <ScoreBadge score={summary.averageResponse} label="Yanıt" className="justify-center" />
          </div>
        </div>

        <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <AnalyticsMetric icon={Gauge} label="Campaign Health" value={summary.campaignHealth} helper="kalite + readiness" tone={summary.campaignHealth >= 80 ? 'success' : summary.campaignHealth >= 64 ? 'info' : 'warning'} />
          <AnalyticsMetric icon={MailCheck} label="Gönderime hazır" value={`${summary.readyRate}%`} helper={`${summary.ready}/${summary.total} aday`} tone="success" />
          <AnalyticsMetric icon={AlertTriangle} label="Review load" value={`${summary.reviewLoad}%`} helper={`${summary.review + summary.blocked} aday kontrol`} tone={summary.reviewLoad > 35 ? 'warning' : 'info'} />
          <AnalyticsMetric icon={ShieldCheck} label="Compliance" value={summary.complianceHealth} helper="insan kontrol sağlığı" tone={summary.complianceHealth >= 80 ? 'success' : 'warning'} />
        </div>
      </SurfaceCard>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_390px]">
        <div className="space-y-4">
          <SurfaceCard variant="default" padding="lg">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-black text-foreground">Funnel readiness</p>
                <p className="mt-1 text-xs font-semibold text-muted-foreground">Gönderim öncesi aday durum dağılımı</p>
              </div>
              <StatusBadge tone="neutral">{formatCompactNumber(summary.total)} aday</StatusBadge>
            </div>
            <div className="mt-5 space-y-4">
              <StackedStatusBar ready={summary.ready} review={summary.review} blocked={summary.blocked} total={summary.total} />
              <div className="grid gap-3 md:grid-cols-3">
                <StatusStat tone="success" label="Hazır" value={summary.ready} helper="direkt kuyruk" />
                <StatusStat tone="warning" label="Review" value={summary.review} helper="insan kontrol" />
                <StatusStat tone="danger" label="Bloker" value={summary.blocked} helper="gönderme" />
              </div>
            </div>
          </SurfaceCard>

          <SurfaceCard variant="default" padding="lg">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-black text-foreground">Aday potansiyeli</p>
                <p className="mt-1 text-xs font-semibold text-muted-foreground">Yanıt ihtimali, match ve intent sinyalleri</p>
              </div>
              <StatusBadge tone="ai" icon={<Sparkles className="size-3.5" />}>AI decision support</StatusBadge>
            </div>
            <div className="mt-5 grid gap-3 md:grid-cols-3">
              <AnalyticsMetric icon={Target} label="Ortalama match" value={summary.averageMatch} helper="rol uyumu" tone="info" />
              <AnalyticsMetric icon={Zap} label="Ortalama intent" value={summary.averageIntent} helper={`${summary.highIntent} sıcak aday`} tone="ai" />
              <AnalyticsMetric icon={Clock3} label="Hızlı kapanış" value={summary.immediate} helper="hemen / 2 hafta" tone="success" />
            </div>
            <div className="mt-5 space-y-3">
              {topCandidates.map((item, index) => (
                <TopCandidateRow key={item.candidate.id} item={item} rank={index + 1} />
              ))}
            </div>
          </SurfaceCard>

          <SurfaceCard variant="default" padding="lg">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-black text-foreground">Review nedenleri</p>
                <p className="mt-1 text-xs font-semibold text-muted-foreground">En sık kalite kontrol notları</p>
              </div>
              <StatusBadge tone={commonChecks.length ? 'warning' : 'success'}>{commonChecks.length ? `${commonChecks.length} sinyal` : 'Temiz'}</StatusBadge>
            </div>
            <div className="mt-5 space-y-3">
              {commonChecks.length > 0 ? commonChecks.map((item) => (
                <ReasonBar key={item.label} label={item.label} count={item.count} total={summary.total} />
              )) : (
                <div className="rounded-[24px] border border-success/25 bg-success/10 p-4 text-sm font-semibold leading-6 text-success">
                  Kuyrukta tekrar eden ciddi bir guardrail uyarısı görünmüyor.
                </div>
              )}
            </div>
          </SurfaceCard>
        </div>

        <aside className="space-y-4 xl:sticky xl:top-4 xl:self-start">
          <SurfaceCard variant="accent" padding="lg">
            <div className="flex items-center gap-3">
              <span className="flex size-12 items-center justify-center rounded-2xl bg-primary/10 text-primary"><Radar className="size-6" /></span>
              <div>
                <p className="text-sm font-black text-foreground">Kanal zekâsı</p>
                <p className="text-xs font-semibold text-muted-foreground">{channelBenchmark.label} benchmark</p>
              </div>
            </div>
            <div className="mt-5 space-y-4">
              <ScoreLine label="Kanal sağlığı" value={summary.channelHealth} />
              <ScoreLine label="Tahmini yanıt" value={summary.averageResponse} />
              <ScoreLine label="Benchmark" value={channelBenchmark.expectedReply} />
            </div>
            <div className="mt-5 rounded-[24px] border border-border bg-surface/75 p-4">
              <p className="text-xs font-black uppercase tracking-[0.14em] text-muted-foreground">Risk</p>
              <p className="mt-2 text-sm font-semibold leading-6 text-foreground">{channelBenchmark.risk}</p>
              <p className="mt-3 text-xs font-semibold leading-5 text-muted-foreground">{channelBenchmark.recommendation}</p>
            </div>
          </SurfaceCard>

          <SurfaceCard variant="muted" padding="lg">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-black text-foreground">Kampanya konfigürasyonu</p>
                <p className="mt-1 text-xs font-semibold text-muted-foreground">Satışa hazır demo özeti</p>
              </div>
              <MessageSquareText className="size-5 text-primary" />
            </div>
            <div className="mt-4 space-y-2">
              <ConfigRow label="Kanal" value={CHANNEL_LABELS[campaign.channel] ?? campaign.channel} />
              <ConfigRow label="Ton" value={String(campaign.tone)} />
              <ConfigRow label="Şablon" value={String(campaign.template)} />
              <ConfigRow label="Kişiselleştirme" value={personalization} />
              <ConfigRow label="Takip" value={followUp} />
              <ConfigRow label="Oluşturuldu" value={formatDate(campaign.created_at)} />
            </div>
          </SurfaceCard>

          <SurfaceCard variant="default" padding="lg">
            <div className="flex items-center gap-3">
              <Activity className="size-5 text-primary" />
              <div>
                <p className="text-sm font-black text-foreground">Audit trend</p>
                <p className="text-xs font-semibold text-muted-foreground">Kuyruk ve review geçmişi</p>
              </div>
            </div>
            <div className="mt-4 space-y-3">
              {(backendQueue?.audit ?? []).slice(0, 4).map((event) => (
                <div key={event.id} className="rounded-2xl border border-border bg-surface-muted p-3">
                  <p className="text-xs font-black text-foreground">{event.action}</p>
                  <p className="mt-1 text-xs font-semibold leading-5 text-muted-foreground">{event.note}</p>
                  <p className="mt-2 text-[11px] font-bold text-muted-foreground">{event.actor} · {formatDate(event.created_at)}</p>
                </div>
              ))}
              {!(backendQueue?.audit ?? []).length && (
                <div className="rounded-2xl border border-border bg-surface-muted p-3 text-xs font-semibold leading-5 text-muted-foreground">
                  Audit kaydı için önce kuyruğu backend’e hazırla veya Review Board’da aday durumu değiştir.
                </div>
              )}
            </div>
          </SurfaceCard>

          <SurfaceCard variant="default" padding="lg">
            <div className="flex items-center gap-3">
              <Users className="size-5 text-primary" />
              <div>
                <p className="text-sm font-black text-foreground">Kaynak dağılımı</p>
                <p className="text-xs font-semibold text-muted-foreground">Aday havuzu kanalı</p>
              </div>
            </div>
            <div className="mt-4 space-y-3">
              {sourceMix.map((item) => (
                <ReasonBar key={item.source} label={sourceLabel(item.source)} count={item.count} total={summary.total} />
              ))}
            </div>
          </SurfaceCard>
        </aside>
      </div>
    </div>
  );
}

function AnalyticsMetric({icon: Icon, label, value, helper, tone}: {icon: LucideIcon; label: string; value: string | number; helper: string; tone: 'success' | 'warning' | 'danger' | 'info' | 'ai'}) {
  const toneClass = tone === 'success' ? 'bg-success/10 text-success' : tone === 'warning' ? 'bg-warning/10 text-warning' : tone === 'danger' ? 'bg-danger/10 text-danger' : tone === 'ai' ? 'bg-primary/10 text-primary' : 'bg-blue-500/10 text-blue-500';
  return (
    <div className="rounded-[24px] border border-border bg-surface p-4">
      <div className="flex items-center gap-3">
        <span className={cn('flex size-10 items-center justify-center rounded-2xl', toneClass)}><Icon className="size-5" /></span>
        <div className="min-w-0">
          <p className="truncate text-[10px] font-black uppercase tracking-[0.14em] text-muted-foreground">{label}</p>
          <p className="text-2xl font-black tracking-[-0.04em] text-foreground">{value}</p>
          <p className="truncate text-xs font-semibold text-muted-foreground">{helper}</p>
        </div>
      </div>
    </div>
  );
}

function StackedStatusBar({ready, review, blocked, total}: {ready: number; review: number; blocked: number; total: number}) {
  const safeTotal = Math.max(1, total);
  const readyWidth = `${Math.max(4, (ready / safeTotal) * 100)}%`;
  const reviewWidth = `${Math.max(4, (review / safeTotal) * 100)}%`;
  const blockedWidth = `${Math.max(4, (blocked / safeTotal) * 100)}%`;
  return (
    <div className="overflow-hidden rounded-full border border-border bg-surface-muted p-1">
      <div className="flex h-4 overflow-hidden rounded-full">
        {ready > 0 && <div className="bg-success" style={{width: readyWidth}} />}
        {review > 0 && <div className="bg-warning" style={{width: reviewWidth}} />}
        {blocked > 0 && <div className="bg-danger" style={{width: blockedWidth}} />}
        {total === 0 && <div className="w-full bg-surface-muted" />}
      </div>
    </div>
  );
}

function StatusStat({tone, label, value, helper}: {tone: 'success' | 'warning' | 'danger'; label: string; value: number; helper: string}) {
  const toneClass = tone === 'success' ? 'border-success/25 bg-success/10 text-success' : tone === 'warning' ? 'border-warning/25 bg-warning/10 text-warning' : 'border-danger/25 bg-danger/10 text-danger';
  return (
    <div className={cn('rounded-[24px] border p-4', toneClass)}>
      <p className="text-xs font-black uppercase tracking-[0.14em] opacity-80">{label}</p>
      <p className="text-2xl font-black tracking-[-0.04em] text-foreground">{value}</p>
      <p className="text-xs font-semibold opacity-80">{helper}</p>
    </div>
  );
}

function TopCandidateRow({item, rank}: {item: AnalyticsQueueItem; rank: number}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-[24px] border border-border bg-surface p-3">
      <div className="flex min-w-0 items-center gap-3">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-xs font-black text-primary">#{rank}</span>
        <span className="min-w-0">
          <p className="truncate text-sm font-black text-foreground">{item.candidate.name}</p>
          <p className="truncate text-xs font-semibold text-muted-foreground">Match {item.candidate.matchScore} · Intent {item.candidate.intentScore} · {item.candidate.availability}</p>
        </span>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <ScoreBadge score={item.responseScore} label="Yanıt" size="sm" />
        <StatusBadge tone={item.status === 'ready' ? 'success' : item.status === 'review' ? 'warning' : 'danger'}>{item.status === 'ready' ? 'Hazır' : item.status === 'review' ? 'Review' : 'Bloker'}</StatusBadge>
      </div>
    </div>
  );
}

function ReasonBar({label, count, total}: {label: string; count: number; total: number}) {
  const percentage = total ? clamp((count / total) * 100) : 0;
  return (
    <div className="rounded-[22px] border border-border bg-surface p-3">
      <div className="flex items-center justify-between gap-3">
        <p className="line-clamp-1 text-sm font-black text-foreground">{label}</p>
        <p className="text-xs font-black text-muted-foreground">{count} · {percentage}%</p>
      </div>
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-surface-muted">
        <div className="h-full rounded-full bg-primary" style={{width: `${percentage}%`}} />
      </div>
    </div>
  );
}

function ScoreLine({label, value}: {label: string; value: number}) {
  return (
    <div>
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-black text-muted-foreground">{label}</p>
        <p className="text-xs font-black text-foreground">{clamp(value)}</p>
      </div>
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-surface-muted">
        <div className="h-full rounded-full bg-[linear-gradient(90deg,var(--primary),var(--accent))]" style={{width: `${clamp(value)}%`}} />
      </div>
    </div>
  );
}

function ConfigRow({label, value}: {label: string; value: string}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-2xl border border-border bg-surface px-3 py-2">
      <span className="text-xs font-black text-muted-foreground">{label}</span>
      <span className="truncate text-right text-xs font-black text-foreground">{value}</span>
    </div>
  );
}
