'use client';

import {
  AlertTriangle,
  BadgeCheck,
  CheckCircle2,
  ClipboardCopy,
  Eye,
  Lock,
  MailCheck,
  MessageSquareWarning,
  Search,
  ShieldCheck,
  Sparkles,
  TimerReset,
  type LucideIcon,
} from 'lucide-react';
import {useMemo, useState} from 'react';

import {ScoreBadge, StatusBadge, SurfaceCard} from '@/components/employer/ui';
import {Button} from '@/components/ui/button';
import {updateEmployerCampaignSendQueueItem} from '@/lib/employer-outreach-api';
import {cn} from '@/lib/utils';
import type {EmployerCandidateOpportunity} from '@/types/employer';
import type {EmployerSendQueue, EmployerSendQueueItem, EmployerSendQueueItemStatus} from '@/types/employer-outreach';

export type ReviewBoardLocalItem = {
  candidate: EmployerCandidateOpportunity;
  subject: string;
  message: string;
  responseScore: number;
  status: EmployerSendQueueItemStatus;
  checks: string[];
};

type ReviewItem = ReviewBoardLocalItem & {
  id?: string;
  status: EmployerSendQueueItemStatus;
  checks: string[];
  updatedAt?: string;
  persisted: boolean;
};

type SendQueueReviewBoardProps = {
  campaignId: string;
  localItems: ReviewBoardLocalItem[];
  backendQueue: EmployerSendQueue | null;
  onQueueChange: (queue: EmployerSendQueue) => void;
  onOpenCandidate?: (candidateId: number) => void;
  locale?: string;
};

const STATUS_META: Record<EmployerSendQueueItemStatus, {label: string; helper: string; tone: 'success' | 'warning' | 'danger'; icon: LucideIcon}> = {
  ready: {
    label: 'Hazır',
    helper: 'Gönderim için güvenli',
    tone: 'success',
    icon: CheckCircle2,
  },
  review: {
    label: 'Review',
    helper: 'İnsan kontrolü istiyor',
    tone: 'warning',
    icon: MessageSquareWarning,
  },
  blocked: {
    label: 'Bloker',
    helper: 'Gönderimden önce düzeltilmeli',
    tone: 'danger',
    icon: AlertTriangle,
  },
};

const REVIEW_COLUMNS: Array<{id: EmployerSendQueueItemStatus; title: string; description: string}> = [
  {id: 'ready', title: 'Gönderime hazır', description: 'Kontroller temiz, sadece son onay bekler.'},
  {id: 'review', title: 'Review gerekiyor', description: 'Metin, kanal veya aday sinyali manuel kontrol ister.'},
  {id: 'blocked', title: 'Bloker var', description: 'Kampanyaya alınmadan önce düzeltilmeli.'},
];

function mergeQueueItems(localItems: ReviewBoardLocalItem[], backendQueue: EmployerSendQueue | null): ReviewItem[] {
  const backendByCandidateId = new Map<number, EmployerSendQueueItem>();
  backendQueue?.items?.forEach((item) => backendByCandidateId.set(item.candidate_id, item));

  return localItems.map((localItem) => {
    const backendItem = backendByCandidateId.get(localItem.candidate.id);
    return {
      ...localItem,
      id: backendItem?.id,
      subject: backendItem?.subject || localItem.subject,
      message: backendItem?.message || localItem.message,
      responseScore: typeof backendItem?.response_score === 'number' ? backendItem.response_score : localItem.responseScore,
      status: backendItem?.status ?? localItem.status,
      checks: backendItem?.checks?.length ? backendItem.checks : localItem.checks,
      updatedAt: backendItem?.updated_at,
      persisted: Boolean(backendItem?.id),
    };
  });
}

function formatDate(value?: string) {
  if (!value) return 'Henüz güncellenmedi';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('tr-TR', {day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'}).format(date);
}

export function SendQueueReviewBoard({campaignId, localItems, backendQueue, onQueueChange, onOpenCandidate}: SendQueueReviewBoardProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCandidateId, setSelectedCandidateId] = useState<number | null>(null);
  const [updatingItemId, setUpdatingItemId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const items = useMemo(() => mergeQueueItems(localItems, backendQueue), [backendQueue, localItems]);
  const filteredItems = useMemo(() => {
    const query = searchQuery.trim().toLocaleLowerCase('tr-TR');
    if (!query) return items;
    return items.filter((item) => {
      const haystack = [
        item.candidate.name,
        item.candidate.targetRole,
        item.subject,
        item.message,
        ...item.checks,
        ...item.candidate.skills.map((skill) => skill.name),
      ].join(' ').toLocaleLowerCase('tr-TR');
      return haystack.includes(query);
    });
  }, [items, searchQuery]);

  const selectedItem = useMemo(() => {
    if (selectedCandidateId) {
      const found = filteredItems.find((item) => item.candidate.id === selectedCandidateId);
      if (found) return found;
    }
    return filteredItems[0] ?? items[0] ?? null;
  }, [filteredItems, items, selectedCandidateId]);

  const summary = useMemo(() => {
    const ready = items.filter((item) => item.status === 'ready').length;
    const review = items.filter((item) => item.status === 'review').length;
    const blocked = items.filter((item) => item.status === 'blocked').length;
    const persisted = items.filter((item) => item.persisted).length;
    return {ready, review, blocked, persisted};
  }, [items]);

  const updateStatus = async (item: ReviewItem, status: EmployerSendQueueItemStatus) => {
    if (!item.id) {
      setError('Önce “Gönderim kuyruğunu hazırla” ile bu kampanyayı backend kuyruğuna kaydetmelisin.');
      return;
    }
    setUpdatingItemId(item.id);
    setError(null);
    try {
      const nextChecks = status === 'ready' ? ['İnsan review tamamlandı; gönderime hazır.'] : item.checks;
      const queue = await updateEmployerCampaignSendQueueItem(campaignId, item.id, {
        status,
        checks: nextChecks,
        actor: 'Sen',
        note: `${item.candidate.name} için kuyruk durumu “${STATUS_META[status].label}” olarak güncellendi.`,
      });
      onQueueChange(queue);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Kuyruk öğesi güncellenemedi.');
    } finally {
      setUpdatingItemId(null);
    }
  };

  return (
    <div className="space-y-4">
      <SurfaceCard variant="elevated" padding="lg" className="overflow-hidden">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-black text-primary">
              <ShieldCheck className="size-3.5" />
              Send Queue Review Board
            </div>
            <h3 className="mt-3 text-2xl font-black tracking-[-0.04em] text-foreground">Gönderim öncesi son insan kontrolü</h3>
            <p className="mt-2 max-w-3xl text-sm font-semibold leading-6 text-muted-foreground">
              Hazır, review ve bloker adayları tek ekranda yönet. Bu panodaki durum değişiklikleri backend send queue API’ye kaydedilir ve audit trail’e düşer.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <ReviewMetric label="Hazır" value={summary.ready} tone="success" />
            <ReviewMetric label="Review" value={summary.review} tone="warning" />
            <ReviewMetric label="Bloker" value={summary.blocked} tone="danger" />
            <ReviewMetric label="Kalıcı" value={`${summary.persisted}/${items.length}`} tone="info" />
          </div>
        </div>

        <div className="mt-5 flex flex-col gap-3 rounded-[24px] border border-border bg-surface-muted/40 p-3 lg:flex-row lg:items-center lg:justify-between">
          <label className="relative block min-w-0 flex-1">
            <Search className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <input
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Aday, beceri, konu veya kontrol notu ara..."
              className="h-12 w-full rounded-2xl border border-border bg-surface pl-11 pr-4 text-sm font-semibold text-foreground outline-none transition placeholder:text-muted-foreground/70 focus:border-primary/55 focus:ring-4 focus:ring-[var(--ring)]"
            />
          </label>
          {!backendQueue && (
            <div className="inline-flex items-center gap-2 rounded-2xl border border-warning/25 bg-warning/10 px-3 py-2 text-xs font-black text-warning">
              <Lock className="size-4" />
              Durum güncellemek için önce kuyruğu hazırla
            </div>
          )}
          {backendQueue && (
            <div className="inline-flex items-center gap-2 rounded-2xl border border-success/25 bg-success/10 px-3 py-2 text-xs font-black text-success">
              <BadgeCheck className="size-4" />
              Backend senkron · Audit {backendQueue.audit?.length ?? 0}
            </div>
          )}
        </div>

        {error && (
          <div className="mt-4 rounded-[22px] border border-danger/25 bg-danger/10 p-3 text-sm font-bold leading-6 text-danger">
            {error}
          </div>
        )}
      </SurfaceCard>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_380px]">
        <div className="grid gap-4 lg:grid-cols-3">
          {REVIEW_COLUMNS.map((column) => {
            const meta = STATUS_META[column.id];
            const Icon = meta.icon;
            const columnItems = filteredItems.filter((item) => item.status === column.id);
            return (
              <section key={column.id} className="min-w-0 rounded-[28px] border border-border bg-surface-muted/35 p-3">
                <div className="mb-3 rounded-[22px] border border-border bg-surface p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <Icon className={cn('size-4', meta.tone === 'success' ? 'text-success' : meta.tone === 'warning' ? 'text-warning' : 'text-danger')} />
                        <h4 className="text-sm font-black text-foreground">{column.title}</h4>
                      </div>
                      <p className="mt-1 text-xs font-semibold leading-5 text-muted-foreground">{column.description}</p>
                    </div>
                    <span className="rounded-full border border-border bg-surface-muted px-2.5 py-1 text-xs font-black text-foreground">{columnItems.length}</span>
                  </div>
                </div>

                <div className="space-y-3">
                  {columnItems.map((item) => (
                    <ReviewCandidateCard
                      key={item.candidate.id}
                      item={item}
                      selected={selectedItem?.candidate.id === item.candidate.id}
                      updating={updatingItemId === item.id}
                      onSelect={() => setSelectedCandidateId(item.candidate.id)}
                      onOpenCandidate={() => onOpenCandidate?.(item.candidate.id)}
                      onUpdateStatus={(status) => void updateStatus(item, status)}
                    />
                  ))}
                  {columnItems.length === 0 && (
                    <div className="rounded-[22px] border border-dashed border-border bg-surface/70 p-4 text-center text-xs font-bold leading-5 text-muted-foreground">
                      Bu statüde aday yok.
                    </div>
                  )}
                </div>
              </section>
            );
          })}
        </div>

        <ReviewInspector
          item={selectedItem}
          backendQueue={backendQueue}
          updating={Boolean(selectedItem?.id && updatingItemId === selectedItem.id)}
          onOpenCandidate={() => selectedItem && onOpenCandidate?.(selectedItem.candidate.id)}
          onUpdateStatus={(status) => selectedItem && void updateStatus(selectedItem, status)}
        />
      </div>
    </div>
  );
}

function ReviewMetric({label, value, tone}: {label: string; value: string | number; tone: 'success' | 'warning' | 'danger' | 'info'}) {
  const toneClass = tone === 'success'
    ? 'border-success/25 bg-success/10 text-success'
    : tone === 'warning'
      ? 'border-warning/25 bg-warning/10 text-warning'
      : tone === 'danger'
        ? 'border-danger/25 bg-danger/10 text-danger'
        : 'border-primary/20 bg-primary/10 text-primary';
  return (
    <div className={cn('rounded-2xl border px-3 py-2 text-right', toneClass)}>
      <p className="text-[10px] font-black uppercase tracking-[0.14em] opacity-80">{label}</p>
      <p className="text-xl font-black tracking-[-0.04em]">{value}</p>
    </div>
  );
}

function ReviewCandidateCard({item, selected, updating, onSelect, onOpenCandidate, onUpdateStatus}: {item: ReviewItem; selected: boolean; updating: boolean; onSelect: () => void; onOpenCandidate: () => void; onUpdateStatus: (status: EmployerSendQueueItemStatus) => void}) {
  const meta = STATUS_META[item.status];
  return (
    <article className={cn('rounded-[24px] border bg-surface p-3 shadow-sm transition', selected ? 'border-primary/50 ring-4 ring-[var(--ring)]' : 'border-border hover:border-primary/35 hover:bg-surface-strong')}>
      <button type="button" onClick={onSelect} className="w-full text-left focus:outline-none">
        <div className="flex items-start gap-3">
          <span className="flex size-10 shrink-0 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,var(--primary),var(--accent))] text-xs font-black text-primary-foreground">
            {item.candidate.initials}
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="truncate text-sm font-black text-foreground">{item.candidate.name}</p>
                <p className="mt-0.5 line-clamp-1 text-xs font-semibold text-muted-foreground">{item.subject}</p>
              </div>
              <StatusBadge tone={meta.tone}>{meta.label}</StatusBadge>
            </div>
            <div className="mt-3 flex flex-wrap gap-1.5">
              <MiniSignal label={`Yanıt ${item.responseScore}%`} />
              <MiniSignal label={`Match ${item.candidate.matchScore}`} />
              {!item.persisted && <MiniSignal label="Taslak" muted />}
            </div>
          </div>
        </div>
      </button>

      {item.checks.length > 0 && (
        <div className="mt-3 space-y-1">
          {item.checks.slice(0, 2).map((check) => (
            <p key={check} className="line-clamp-1 rounded-xl border border-border bg-surface-muted/60 px-2.5 py-1.5 text-[11px] font-bold text-muted-foreground">
              {check}
            </p>
          ))}
        </div>
      )}

      <div className="mt-3 flex flex-wrap gap-1.5">
        <MiniStatusButton label="Hazır" disabled={updating || item.status === 'ready'} onClick={() => onUpdateStatus('ready')} />
        <MiniStatusButton label="Review" disabled={updating || item.status === 'review'} onClick={() => onUpdateStatus('review')} />
        <MiniStatusButton label="Bloker" disabled={updating || item.status === 'blocked'} onClick={() => onUpdateStatus('blocked')} danger />
        <button type="button" onClick={onOpenCandidate} className="ml-auto inline-flex items-center gap-1 rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-[11px] font-black text-primary transition hover:bg-primary/15">
          360 <Eye className="size-3.5" />
        </button>
      </div>
    </article>
  );
}

function MiniSignal({label, muted}: {label: string; muted?: boolean}) {
  return <span className={cn('rounded-full border px-2 py-0.5 text-[10px] font-black', muted ? 'border-border bg-surface-muted text-muted-foreground' : 'border-primary/15 bg-primary/10 text-primary')}>{label}</span>;
}

function MiniStatusButton({label, disabled, danger, onClick}: {label: string; disabled: boolean; danger?: boolean; onClick: () => void}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={cn(
        'rounded-full border px-2.5 py-1 text-[11px] font-black transition focus:outline-none focus:ring-4 focus:ring-[var(--ring)] disabled:cursor-not-allowed disabled:opacity-45',
        danger ? 'border-danger/20 bg-danger/10 text-danger hover:bg-danger/15' : 'border-border bg-surface-muted text-foreground hover:border-primary/30 hover:bg-primary/10 hover:text-primary'
      )}
    >
      {label}
    </button>
  );
}

function ReviewInspector({item, backendQueue, updating, onOpenCandidate, onUpdateStatus}: {item: ReviewItem | null; backendQueue: EmployerSendQueue | null; updating: boolean; onOpenCandidate: () => void; onUpdateStatus: (status: EmployerSendQueueItemStatus) => void}) {
  if (!item) {
    return (
      <SurfaceCard variant="muted" padding="lg" className="xl:sticky xl:top-4 xl:self-start">
        <p className="text-sm font-black text-foreground">Aday seç</p>
        <p className="mt-2 text-sm font-semibold leading-6 text-muted-foreground">Kuyrukta incelenecek aday yok.</p>
      </SurfaceCard>
    );
  }

  const meta = STATUS_META[item.status];
  const StatusIcon = meta.icon;
  const latestAudit = backendQueue?.audit?.slice(0, 4) ?? [];

  return (
    <SurfaceCard variant="elevated" padding="none" className="overflow-hidden xl:sticky xl:top-4 xl:self-start">
      <div className="border-b border-border p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge tone={meta.tone} icon={<StatusIcon className="size-3.5" />}>{meta.label}</StatusBadge>
              <span className="text-xs font-bold text-muted-foreground">{formatDate(item.updatedAt)}</span>
            </div>
            <p className="mt-2 truncate text-lg font-black text-foreground">{item.candidate.name}</p>
            <p className="mt-1 text-xs font-semibold text-muted-foreground">{meta.helper}</p>
          </div>
          <ScoreBadge score={item.responseScore} label="Yanıt" />
        </div>
      </div>

      <div className="space-y-4 p-4">
        <div className="rounded-[24px] border border-border bg-surface-muted/45 p-4">
          <p className="text-xs font-black uppercase tracking-[0.14em] text-muted-foreground">Konu</p>
          <p className="mt-2 text-sm font-black leading-6 text-foreground">{item.subject}</p>
        </div>

        <div className="rounded-[24px] border border-border bg-surface p-4">
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs font-black uppercase tracking-[0.14em] text-muted-foreground">Mesaj</p>
            <button type="button" onClick={() => void navigator.clipboard?.writeText(item.message)} className="inline-flex items-center gap-1 text-xs font-black text-primary hover:text-primary/80">
              <ClipboardCopy className="size-3.5" /> Kopyala
            </button>
          </div>
          <p className="mt-3 max-h-56 overflow-y-auto whitespace-pre-wrap pr-1 text-sm font-semibold leading-7 text-foreground">{item.message}</p>
        </div>

        <div className="rounded-[24px] border border-border bg-surface-muted/45 p-4">
          <p className="text-xs font-black uppercase tracking-[0.14em] text-muted-foreground">Kontrol notları</p>
          <div className="mt-3 space-y-2">
            {item.checks.map((check) => <p key={check} className="rounded-2xl border border-border bg-surface px-3 py-2 text-xs font-bold leading-5 text-muted-foreground">{check}</p>)}
          </div>
        </div>

        <div className="grid gap-2 sm:grid-cols-3 xl:grid-cols-1 2xl:grid-cols-3">
          <Button disabled={updating || item.status === 'ready' || !item.id} className="gap-2" onClick={() => onUpdateStatus('ready')}><CheckCircle2 className="size-4" />Hazır</Button>
          <Button disabled={updating || item.status === 'review' || !item.id} variant="secondary" className="gap-2" onClick={() => onUpdateStatus('review')}><MessageSquareWarning className="size-4" />Review</Button>
          <Button disabled={updating || item.status === 'blocked' || !item.id} variant="danger" className="gap-2" onClick={() => onUpdateStatus('blocked')}><AlertTriangle className="size-4" />Bloker</Button>
        </div>
        {!item.id && <p className="rounded-2xl border border-warning/25 bg-warning/10 p-3 text-xs font-black leading-5 text-warning">Bu aday henüz backend kuyruğunda değil. Önce Kuyruk sekmesinden gönderim kuyruğunu hazırla.</p>}
        {updating && <p className="inline-flex items-center gap-2 text-xs font-black text-muted-foreground"><TimerReset className="size-3.5 animate-spin" />Durum kaydediliyor...</p>}

        <Button variant="ghost" className="w-full gap-2" onClick={onOpenCandidate}><Eye className="size-4" />Candidate 360 aç</Button>

        {latestAudit.length > 0 && (
          <div className="rounded-[24px] border border-border bg-surface p-4">
            <div className="flex items-center gap-2">
              <MailCheck className="size-4 text-primary" />
              <p className="text-sm font-black text-foreground">Audit trail</p>
            </div>
            <div className="mt-3 space-y-2">
              {latestAudit.map((event) => (
                <div key={event.id} className="rounded-2xl border border-border bg-surface-muted/40 p-3">
                  <p className="text-xs font-black text-foreground">{event.note}</p>
                  <p className="mt-1 text-[11px] font-bold text-muted-foreground">{event.actor} · {formatDate(event.created_at)}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="rounded-[24px] border border-primary/20 bg-primary/10 p-4">
          <div className="flex items-start gap-3">
            <Sparkles className="mt-0.5 size-5 shrink-0 text-primary" />
            <p className="text-xs font-bold leading-5 text-primary">
              Bu board gerçek gönderim yapmaz; sadece insan review kararını kalıcı kuyruğa işler. Gönderim sağlayıcısı entegrasyonu bir sonraki katmanda açılmalı.
            </p>
          </div>
        </div>
      </div>
    </SurfaceCard>
  );
}
