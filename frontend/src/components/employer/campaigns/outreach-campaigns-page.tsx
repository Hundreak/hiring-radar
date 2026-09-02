'use client';

import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  CalendarClock,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Gauge,
  Inbox,
  Mail,
  MessageCircle,
  MousePointerClick,
  Plus,
  RefreshCw,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
  UsersRound,
  Zap,
  type LucideIcon,
} from 'lucide-react';
import Link from 'next/link';
import {useEffect, useMemo, useState} from 'react';

import {CampaignDetailDrawer} from '@/components/employer/talent/campaign-detail-drawer';
import {MetricCard, ScoreBadge, StatusBadge, SurfaceCard} from '@/components/employer/ui';
import {Button} from '@/components/ui/button';
import {employerCandidatesMock} from '@/data/employer-candidates.mock';
import {listEmployerOutreachCampaigns} from '@/lib/employer-outreach-api';
import {formatCompactNumber} from '@/lib/employer-format';
import {cn} from '@/lib/utils';
import type {EmployerCandidateOpportunity} from '@/types/employer';
import type {EmployerOutreachCampaign, EmployerOutreachChannel} from '@/types/employer-outreach';

type OutreachCampaignsPageProps = {
  locale: string;
};

type CampaignFilter = 'all' | 'draft' | 'queued' | 'sent' | 'needs-review';

type CampaignChannelMeta = {
  label: string;
  helper: string;
  icon: LucideIcon;
  tone: 'info' | 'success' | 'warning' | 'ai';
};

const CHANNEL_META: Record<EmployerOutreachChannel, CampaignChannelMeta> = {
  email: {label: 'E-posta', helper: 'Konu + takip akışı', icon: Mail, tone: 'info'},
  linkedin: {label: 'LinkedIn', helper: 'Pasif aday teması', icon: Target, tone: 'ai'},
  whatsapp: {label: 'WhatsApp', helper: 'Hızlı sıcak temas', icon: MessageCircle, tone: 'success'},
};

const FILTERS: Array<{id: CampaignFilter; label: string; icon: LucideIcon}> = [
  {id: 'all', label: 'Tümü', icon: Inbox},
  {id: 'draft', label: 'Taslak', icon: Clock3},
  {id: 'queued', label: 'Kuyruk', icon: Send},
  {id: 'sent', label: 'Gönderildi', icon: CheckCircle2},
  {id: 'needs-review', label: 'Review', icon: AlertTriangle},
];

function getMetadataNumber(campaign: EmployerOutreachCampaign, key: string, fallback: number) {
  const value = campaign.metadata?.[key];
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

function getMetadataString(campaign: EmployerOutreachCampaign, key: string, fallback = '') {
  const value = campaign.metadata?.[key];
  return typeof value === 'string' ? value : fallback;
}

function getMetadataArray<T>(campaign: EmployerOutreachCampaign, key: string): T[] {
  const value = campaign.metadata?.[key];
  return Array.isArray(value) ? value as T[] : [];
}

function getCampaignQuality(campaign: EmployerOutreachCampaign) {
  return getMetadataNumber(campaign, 'quality_score', Math.max(45, Math.min(96, campaign.response_rate + 12)));
}

function getCampaignReadiness(campaign: EmployerOutreachCampaign) {
  return getMetadataNumber(campaign, 'readiness_score', Math.round((getCampaignQuality(campaign) + campaign.response_rate) / 2));
}

function getCampaignWarnings(campaign: EmployerOutreachCampaign) {
  return getMetadataArray<string>(campaign, 'warnings');
}

function getCampaignBlockers(campaign: EmployerOutreachCampaign) {
  return getMetadataArray<string>(campaign, 'blockers');
}

function getCampaignStatusLabel(status: string) {
  if (status === 'draft') return 'Taslak';
  if (status === 'queued') return 'Kuyrukta';
  if (status === 'sent') return 'Gönderildi';
  return status;
}

function getCampaignStatusTone(status: string): 'info' | 'success' | 'warning' | 'danger' | 'neutral' {
  if (status === 'sent') return 'success';
  if (status === 'queued') return 'info';
  if (status === 'draft') return 'warning';
  return 'neutral';
}

function formatDate(value?: string) {
  if (!value) return 'Tarih yok';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('tr-TR', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

function getCandidateById(candidates: EmployerCandidateOpportunity[], candidateId: number) {
  return candidates.find((candidate) => candidate.id === candidateId);
}

function getCampaignCandidates(campaign: EmployerOutreachCampaign, candidates: EmployerCandidateOpportunity[]) {
  return campaign.candidate_ids
    .map((candidateId) => getCandidateById(candidates, candidateId))
    .filter(Boolean) as EmployerCandidateOpportunity[];
}

function getAverageCandidateScore(campaign: EmployerOutreachCampaign, candidates: EmployerCandidateOpportunity[]) {
  const items = getCampaignCandidates(campaign, candidates);
  if (!items.length) return 0;
  return Math.round(items.reduce((total, candidate) => total + candidate.matchScore, 0) / items.length);
}

function campaignNeedsReview(campaign: EmployerOutreachCampaign) {
  return getCampaignWarnings(campaign).length > 0 || getCampaignBlockers(campaign).length > 0 || getCampaignReadiness(campaign) < 70;
}

function matchesFilter(campaign: EmployerOutreachCampaign, filter: CampaignFilter) {
  if (filter === 'all') return true;
  if (filter === 'needs-review') return campaignNeedsReview(campaign);
  return campaign.status === filter;
}

function getCampaignSearchText(campaign: EmployerOutreachCampaign) {
  const values = [
    campaign.name,
    campaign.channel,
    campaign.tone,
    campaign.template,
    campaign.message_preview,
    getMetadataString(campaign, 'subject_preview'),
  ];
  return values.join(' ').toLocaleLowerCase('tr-TR');
}

function getTopCampaign(campaigns: EmployerOutreachCampaign[]) {
  return [...campaigns].sort((a, b) => {
    const bScore = getCampaignReadiness(b) + b.response_rate + getCampaignQuality(b);
    const aScore = getCampaignReadiness(a) + a.response_rate + getCampaignQuality(a);
    return bScore - aScore;
  })[0] ?? null;
}

function getChannelMix(campaigns: EmployerOutreachCampaign[]) {
  return (Object.keys(CHANNEL_META) as EmployerOutreachChannel[]).map((channel) => ({
    channel,
    count: campaigns.filter((campaign) => campaign.channel === channel).length,
  }));
}

export function OutreachCampaignsPage({locale}: OutreachCampaignsPageProps) {
  const [campaigns, setCampaigns] = useState<EmployerOutreachCampaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState<CampaignFilter>('all');
  const [channelFilter, setChannelFilter] = useState<'all' | EmployerOutreachChannel>('all');
  const [selectedCampaign, setSelectedCampaign] = useState<EmployerOutreachCampaign | null>(null);

  const candidates = employerCandidatesMock;

  const refreshCampaigns = async () => {
    setLoading(true);
    setError(null);
    try {
      const items = await listEmployerOutreachCampaigns();
      setCampaigns(items);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Kampanya listesi yüklenemedi.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refreshCampaigns();
  }, []);

  const filteredCampaigns = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase('tr-TR');
    return campaigns
      .filter((campaign) => matchesFilter(campaign, filter))
      .filter((campaign) => channelFilter === 'all' ? true : campaign.channel === channelFilter)
      .filter((campaign) => normalizedQuery ? getCampaignSearchText(campaign).includes(normalizedQuery) : true)
      .sort((a, b) => new Date(b.updated_at ?? b.created_at).getTime() - new Date(a.updated_at ?? a.created_at).getTime());
  }, [campaigns, channelFilter, filter, query]);

  const summary = useMemo(() => {
    const totalCandidates = campaigns.reduce((total, campaign) => total + campaign.candidate_ids.length, 0);
    const avgResponse = campaigns.length ? Math.round(campaigns.reduce((total, campaign) => total + campaign.response_rate, 0) / campaigns.length) : 0;
    const avgReadiness = campaigns.length ? Math.round(campaigns.reduce((total, campaign) => total + getCampaignReadiness(campaign), 0) / campaigns.length) : 0;
    const reviewCount = campaigns.filter(campaignNeedsReview).length;
    const queuedCount = campaigns.filter((campaign) => campaign.status === 'queued').length;
    return {totalCandidates, avgResponse, avgReadiness, reviewCount, queuedCount};
  }, [campaigns]);

  const topCampaign = useMemo(() => getTopCampaign(campaigns), [campaigns]);
  const channelMix = useMemo(() => getChannelMix(campaigns), [campaigns]);

  const selectedCampaignCandidates = selectedCampaign ? getCampaignCandidates(selectedCampaign, candidates) : [];

  return (
    <div className="space-y-6">
      <section className="relative overflow-hidden rounded-[34px] border border-border bg-[radial-gradient(circle_at_top_left,color-mix(in_srgb,var(--primary)_18%,transparent),transparent_34%),linear-gradient(135deg,var(--surface),var(--surface-muted))] p-5 shadow-[0_28px_90px_rgba(15,23,42,0.16)] sm:p-6 lg:p-7">
        <div className="absolute right-8 top-8 hidden h-28 w-28 rounded-full bg-primary/15 blur-3xl lg:block" />
        <div className="relative grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px] xl:items-end">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge tone="ai" icon={<Sparkles className="size-3.5" />}>Campaign OS</StatusBadge>
              <StatusBadge tone="info" icon={<ShieldCheck className="size-3.5" />}>Human-reviewed outreach</StatusBadge>
            </div>
            <h1 className="mt-4 max-w-4xl text-3xl font-black tracking-[-0.055em] text-foreground sm:text-4xl xl:text-5xl">
              Outreach kampanyalarını tek merkezden yönet.
            </h1>
            <p className="mt-3 max-w-3xl text-sm font-semibold leading-7 text-muted-foreground sm:text-base">
              Aday davet taslaklarını, gönderim hazırlığını, review yükünü ve kanal performansını tek bir kampanya komuta merkezinde izle.
            </p>
            <div className="mt-5 flex flex-wrap gap-2">
              <Link href={`/${locale}/employer/candidates`} className="inline-flex min-h-10 items-center justify-center gap-2 rounded-2xl border border-primary/20 bg-primary px-4 py-2.5 text-sm font-bold text-primary-foreground shadow-[0_12px_28px_color-mix(in_srgb,var(--primary)_24%,transparent)] transition hover:-translate-y-0.5 hover:shadow-[0_16px_36px_color-mix(in_srgb,var(--primary)_30%,transparent)] focus:outline-none focus:ring-4 focus:ring-[var(--ring)]">
                <Plus className="size-4" />
                Yeni kampanya oluştur
              </Link>
              <Button variant="secondary" className="gap-2" onClick={() => void refreshCampaigns()} disabled={loading}>
                <RefreshCw className={cn('size-4', loading && 'animate-spin')} />
                Yenile
              </Button>
            </div>
          </div>

          <SurfaceCard className="bg-background/70 p-4 backdrop-blur-xl">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.24em] text-muted-foreground">En güçlü kampanya</p>
                <h2 className="mt-2 line-clamp-2 text-lg font-black tracking-[-0.035em] text-foreground">
                  {topCampaign?.name ?? 'Henüz kampanya yok'}
                </h2>
              </div>
              <div className="rounded-2xl bg-primary/10 p-3 text-primary">
                <TrendingUp className="size-5" />
              </div>
            </div>
            {topCampaign ? (
              <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                <MiniStat label="Readiness" value={`${getCampaignReadiness(topCampaign)}`} />
                <MiniStat label="Yanıt" value={`${topCampaign.response_rate}%`} />
                <MiniStat label="Aday" value={topCampaign.candidate_ids.length} />
              </div>
            ) : (
              <p className="mt-4 text-sm font-semibold text-muted-foreground">Davet modundan ilk taslağı oluşturunca burada kampanya sağlığı görünür.</p>
            )}
          </SurfaceCard>
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <MetricCard icon={Send} label="Kampanya" value={campaigns.length} description="taslak + kuyruk" />
        <MetricCard icon={UsersRound} label="Aday teması" value={formatCompactNumber(summary.totalCandidates)} description="kampanya kapsamı" />
        <MetricCard icon={MousePointerClick} label="Yanıt tahmini" value={`${summary.avgResponse}%`} description="ortalama kampanya" />
        <MetricCard icon={Gauge} label="Readiness" value={`${summary.avgReadiness}`} description="hazırlık skoru" />
        <MetricCard icon={AlertTriangle} label="Review" value={summary.reviewCount} description={`${summary.queuedCount} kuyrukta`} />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-4">
          <SurfaceCard className="p-3 sm:p-4">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div className="relative min-w-0 flex-1">
                <Search className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Kampanya, kanal, şablon veya mesaj içinde ara..."
                  className="h-11 w-full rounded-2xl border border-border bg-surface-muted pl-11 pr-4 text-sm font-semibold text-foreground outline-none transition placeholder:text-muted-foreground/70 focus:border-primary/50 focus:bg-background focus:ring-4 focus:ring-[var(--ring)]"
                />
              </div>
              <div className="flex flex-wrap gap-2">
                <select
                  value={channelFilter}
                  onChange={(event) => setChannelFilter(event.target.value as typeof channelFilter)}
                  className="h-11 rounded-2xl border border-border bg-surface px-3 text-sm font-bold text-foreground outline-none focus:border-primary/50 focus:ring-4 focus:ring-[var(--ring)]"
                >
                  <option value="all">Tüm kanallar</option>
                  <option value="email">E-posta</option>
                  <option value="linkedin">LinkedIn</option>
                  <option value="whatsapp">WhatsApp</option>
                </select>
              </div>
            </div>

            <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
              {FILTERS.map((item) => {
                const Icon = item.icon;
                const count = campaigns.filter((campaign) => matchesFilter(campaign, item.id)).length;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setFilter(item.id)}
                    className={cn(
                      'inline-flex shrink-0 items-center gap-2 rounded-2xl border px-3.5 py-2 text-xs font-black transition focus:outline-none focus:ring-4 focus:ring-[var(--ring)]',
                      filter === item.id
                        ? 'border-primary/45 bg-primary text-primary-foreground shadow-sm'
                        : 'border-border bg-surface text-muted-foreground hover:border-primary/35 hover:bg-surface-strong hover:text-foreground'
                    )}
                  >
                    <Icon className="size-4" />
                    {item.label}
                    <span className="rounded-full bg-background/20 px-1.5 py-0.5 text-[10px]">{count}</span>
                  </button>
                );
              })}
            </div>
          </SurfaceCard>

          {error && (
            <SurfaceCard className="border-danger/25 bg-red-500/5 p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="mt-0.5 size-5 text-danger" />
                <div>
                  <p className="text-sm font-black text-foreground">Kampanyalar yüklenemedi</p>
                  <p className="mt-1 text-sm font-semibold text-muted-foreground">{error}</p>
                </div>
              </div>
            </SurfaceCard>
          )}

          {loading ? (
            <CampaignSkeletonList />
          ) : filteredCampaigns.length > 0 ? (
            <div className="space-y-3">
              {filteredCampaigns.map((campaign) => (
                <CampaignCard
                  key={campaign.id}
                  campaign={campaign}
                  candidates={candidates}
                  onOpen={() => setSelectedCampaign(campaign)}
                />
              ))}
            </div>
          ) : (
            <SurfaceCard className="p-8 text-center">
              <div className="mx-auto flex size-14 items-center justify-center rounded-3xl bg-primary/10 text-primary">
                <Send className="size-6" />
              </div>
              <h2 className="mt-4 text-xl font-black tracking-[-0.035em] text-foreground">Kampanya bulunamadı</h2>
              <p className="mx-auto mt-2 max-w-lg text-sm font-semibold leading-6 text-muted-foreground">
                Filtreleri temizleyebilir veya Talent ekranındaki Davet modundan yeni bir kampanya taslağı oluşturabilirsin.
              </p>
              <div className="mt-5 flex justify-center gap-2">
                <Button variant="secondary" onClick={() => {setQuery(''); setFilter('all'); setChannelFilter('all');}}>Filtreleri temizle</Button>
                <Link href={`/${locale}/employer/candidates`} className="inline-flex min-h-10 items-center justify-center rounded-2xl border border-primary/20 bg-primary px-4 py-2.5 text-sm font-bold text-primary-foreground shadow-[0_12px_28px_color-mix(in_srgb,var(--primary)_24%,transparent)] transition hover:-translate-y-0.5 focus:outline-none focus:ring-4 focus:ring-[var(--ring)]">Davet moduna git</Link>
              </div>
            </SurfaceCard>
          )}
        </div>

        <aside className="space-y-4 xl:sticky xl:top-24 xl:self-start">
          <ChannelMixPanel channelMix={channelMix} total={campaigns.length} />
          <OutreachOpsPanel campaigns={campaigns} />
        </aside>
      </div>

      <CampaignDetailDrawer
        campaign={selectedCampaign}
        candidates={selectedCampaignCandidates.length ? selectedCampaignCandidates : candidates}
        open={Boolean(selectedCampaign)}
        onClose={() => setSelectedCampaign(null)}
        onOpenCandidate={(candidateId) => {
          window.location.href = `/${locale}/employer/candidates/${candidateId}`;
        }}
        locale={locale}
      />
    </div>
  );
}

function MiniStat({label, value}: {label: string; value: string | number}) {
  return (
    <div className="rounded-2xl border border-border bg-surface-muted p-2">
      <p className="text-lg font-black text-foreground">{value}</p>
      <p className="mt-0.5 text-[10px] font-black uppercase tracking-[0.18em] text-muted-foreground">{label}</p>
    </div>
  );
}

function CampaignCard({campaign, candidates, onOpen}: {campaign: EmployerOutreachCampaign; candidates: EmployerCandidateOpportunity[]; onOpen: () => void}) {
  const channel = CHANNEL_META[campaign.channel] ?? CHANNEL_META.email;
  const ChannelIcon = channel.icon;
  const readiness = getCampaignReadiness(campaign);
  const quality = getCampaignQuality(campaign);
  const warnings = getCampaignWarnings(campaign);
  const blockers = getCampaignBlockers(campaign);
  const avgCandidateScore = getAverageCandidateScore(campaign, candidates);
  const campaignCandidates = getCampaignCandidates(campaign, candidates);
  const subject = getMetadataString(campaign, 'subject_preview', 'Konu satırı kaydedilmedi');

  return (
    <button
      type="button"
      onClick={onOpen}
      className="group w-full rounded-[28px] border border-border bg-surface p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-primary/35 hover:bg-surface-strong hover:shadow-[0_24px_60px_rgba(15,23,42,0.14)] focus:outline-none focus:ring-4 focus:ring-[var(--ring)] sm:p-5"
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge tone={getCampaignStatusTone(campaign.status)}>{getCampaignStatusLabel(campaign.status)}</StatusBadge>
            <StatusBadge tone={channel.tone} icon={<ChannelIcon className="size-3.5" />}>{channel.label}</StatusBadge>
            {blockers.length > 0 ? <StatusBadge tone="danger">{blockers.length} bloker</StatusBadge> : null}
            {warnings.length > 0 ? <StatusBadge tone="warning">{warnings.length} uyarı</StatusBadge> : null}
          </div>

          <div className="mt-3 flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h3 className="truncate text-lg font-black tracking-[-0.035em] text-foreground sm:text-xl">{campaign.name}</h3>
              <p className="mt-1 line-clamp-1 text-sm font-bold text-muted-foreground">{subject}</p>
            </div>
            <ChevronRight className="mt-1 size-5 shrink-0 text-muted-foreground transition group-hover:translate-x-1 group-hover:text-primary" />
          </div>

          <p className="mt-3 line-clamp-2 text-sm font-semibold leading-6 text-muted-foreground">
            {campaign.message_preview || 'Bu kampanya için mesaj önizlemesi henüz oluşturulmadı.'}
          </p>

          <div className="mt-4 flex flex-wrap gap-2">
            {campaignCandidates.slice(0, 4).map((candidate) => (
              <span key={candidate.id} className="inline-flex items-center gap-2 rounded-full border border-border bg-background/70 px-2.5 py-1 text-xs font-black text-foreground">
                <span className="flex size-5 items-center justify-center rounded-full bg-primary/10 text-[10px] text-primary">{candidate.initials}</span>
                {candidate.name}
              </span>
            ))}
            {campaign.candidate_ids.length > 4 ? (
              <span className="rounded-full border border-border bg-background/70 px-2.5 py-1 text-xs font-black text-muted-foreground">+{campaign.candidate_ids.length - 4} aday</span>
            ) : null}
          </div>
        </div>

        <div className="grid min-w-[280px] gap-3 sm:grid-cols-4 lg:max-w-[460px]">
          <CampaignMiniMetric label="Readiness" value={readiness} icon={Gauge} />
          <CampaignMiniMetric label="Kalite" value={quality} icon={ShieldCheck} />
          <CampaignMiniMetric label="Yanıt" value={`${campaign.response_rate}%`} icon={MousePointerClick} />
          <CampaignMiniMetric label="Match" value={avgCandidateScore || '—'} icon={Zap} />
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-border pt-3 text-xs font-bold text-muted-foreground">
        <span className="inline-flex items-center gap-2"><CalendarClock className="size-4" /> Güncellendi: {formatDate(campaign.updated_at ?? campaign.created_at)}</span>
        <span className="inline-flex items-center gap-2 text-primary">Detayları aç <ArrowRight className="size-4" /></span>
      </div>
    </button>
  );
}

function CampaignMiniMetric({label, value, icon: Icon}: {label: string; value: string | number; icon: LucideIcon}) {
  return (
    <div className="rounded-2xl border border-border bg-background/70 p-3 text-center">
      <Icon className="mx-auto size-4 text-primary" />
      <p className="mt-1 text-base font-black text-foreground">{value}</p>
      <p className="mt-0.5 text-[10px] font-black uppercase tracking-[0.18em] text-muted-foreground">{label}</p>
    </div>
  );
}

function ChannelMixPanel({channelMix, total}: {channelMix: Array<{channel: EmployerOutreachChannel; count: number}>; total: number}) {
  return (
    <SurfaceCard className="p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.22em] text-muted-foreground">Kanal karması</p>
          <h2 className="mt-1 text-lg font-black tracking-[-0.035em] text-foreground">Nereden temas ediyoruz?</h2>
        </div>
        <div className="rounded-2xl bg-primary/10 p-3 text-primary"><BarChart3 className="size-5" /></div>
      </div>
      <div className="mt-4 space-y-3">
        {channelMix.map(({channel, count}) => {
          const meta = CHANNEL_META[channel];
          const Icon = meta.icon;
          const ratio = total ? Math.round((count / total) * 100) : 0;
          return (
            <div key={channel}>
              <div className="flex items-center justify-between gap-3 text-sm font-bold">
                <span className="inline-flex items-center gap-2 text-foreground"><Icon className="size-4 text-primary" /> {meta.label}</span>
                <span className="text-muted-foreground">{count} · {ratio}%</span>
              </div>
              <div className="mt-2 h-2 rounded-full bg-surface-muted">
                <div className="h-full rounded-full bg-primary" style={{width: `${ratio}%`}} />
              </div>
              <p className="mt-1 text-xs font-semibold text-muted-foreground">{meta.helper}</p>
            </div>
          );
        })}
      </div>
    </SurfaceCard>
  );
}

function OutreachOpsPanel({campaigns}: {campaigns: EmployerOutreachCampaign[]}) {
  const needsReview = campaigns.filter(campaignNeedsReview);
  const avgQuality = campaigns.length ? Math.round(campaigns.reduce((total, campaign) => total + getCampaignQuality(campaign), 0) / campaigns.length) : 0;
  const avgResponse = campaigns.length ? Math.round(campaigns.reduce((total, campaign) => total + campaign.response_rate, 0) / campaigns.length) : 0;

  return (
    <SurfaceCard className="p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.22em] text-muted-foreground">Operasyon zekâsı</p>
          <h2 className="mt-1 text-lg font-black tracking-[-0.035em] text-foreground">Bugün neye bakmalı?</h2>
        </div>
        <ScoreBadge score={avgQuality || 0} size="sm" />
      </div>

      <div className="mt-4 space-y-3">
        <OpsRow icon={AlertTriangle} label="Review bekleyen kampanya" value={needsReview.length} tone={needsReview.length ? 'warning' : 'success'} />
        <OpsRow icon={MousePointerClick} label="Ortalama yanıt tahmini" value={`${avgResponse}%`} tone="info" />
        <OpsRow icon={ShieldCheck} label="Ortalama kalite skoru" value={avgQuality || '—'} tone="ai" />
      </div>

      <div className="mt-4 rounded-3xl border border-primary/15 bg-primary/10 p-4">
        <p className="text-sm font-black text-foreground">Önerilen aksiyon</p>
        <p className="mt-1 text-sm font-semibold leading-6 text-muted-foreground">
          {needsReview.length > 0
            ? `${needsReview[0]?.name} kampanyasında review/bloker sinyali var. Detay drawer’dan Review Board’a girip gönderime hazır adayları temizle.`
            : campaigns.length > 0
              ? 'Kampanyalar sağlıklı görünüyor. En yüksek yanıt potansiyelli taslağı kuyruğa hazırlayabilirsin.'
              : 'İlk kampanyayı Talent ekranındaki Davet modundan oluştur. Sistem otomatik kalite ve readiness sinyali üretecek.'}
        </p>
      </div>
    </SurfaceCard>
  );
}

function OpsRow({icon: Icon, label, value, tone}: {icon: LucideIcon; label: string; value: string | number; tone: 'warning' | 'success' | 'info' | 'ai'}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-2xl border border-border bg-background/70 p-3">
      <div className="flex items-center gap-3">
        <div className={cn('flex size-9 items-center justify-center rounded-2xl', tone === 'warning' ? 'bg-amber-500/10 text-amber-600' : tone === 'success' ? 'bg-emerald-500/10 text-emerald-600' : 'bg-primary/10 text-primary')}>
          <Icon className="size-4" />
        </div>
        <span className="text-sm font-bold text-foreground">{label}</span>
      </div>
      <span className="text-sm font-black text-foreground">{value}</span>
    </div>
  );
}

function CampaignSkeletonList() {
  return (
    <div className="space-y-3">
      {Array.from({length: 3}).map((_, index) => (
        <SurfaceCard key={index} className="p-5">
          <div className="animate-pulse space-y-4">
            <div className="h-4 w-32 rounded-full bg-surface-muted" />
            <div className="h-6 w-2/3 rounded-full bg-surface-muted" />
            <div className="h-4 w-full rounded-full bg-surface-muted" />
            <div className="grid gap-3 sm:grid-cols-4">
              <div className="h-20 rounded-2xl bg-surface-muted" />
              <div className="h-20 rounded-2xl bg-surface-muted" />
              <div className="h-20 rounded-2xl bg-surface-muted" />
              <div className="h-20 rounded-2xl bg-surface-muted" />
            </div>
          </div>
        </SurfaceCard>
      ))}
    </div>
  );
}
