'use client';

import {
  AlertTriangle,
  ArrowRight,
  BadgeCheck,
  BellRing,
  CheckCircle2,
  Clock3,
  GripVertical,
  Layers3,
  NotebookPen,
  PanelRightOpen,
  Tag,
  TimerReset,
  UsersRound,
  Zap,
} from 'lucide-react';
import {useMemo, useState, type DragEvent} from 'react';

import {Button} from '@/components/ui/button';
import {ScoreBadge, StatusBadge} from '@/components/employer/ui';
import {getTalentWorkflowCopy, getTalentWorkflowLanguage, workflowAvailabilityLabels, workflowCandidateStatusLabels, workflowSourceLabels} from '@/lib/employer-talent-workflow-copy';
import {cn} from '@/lib/utils';
import type {EmployerCandidateOpportunity, EmployerCandidateStatus} from '@/types/employer';

type PipelineKanbanBoardProps = {
  candidates: EmployerCandidateOpportunity[];
  selectedCandidateId?: number;
  onSelect: (id: number) => void;
  onOpenCandidate: (id: number) => void;
  onMoveCandidate: (id: number, status: EmployerCandidateStatus) => void;
  onBulkMove: (ids: number[], status: EmployerCandidateStatus) => void;
  candidateTags?: Record<number, string[]>;
  candidateNoteCounts?: Record<number, number>;
  onBulkTag?: (ids: number[], tag: string) => void;
  onBulkNote?: (ids: number[], note: string) => void;
  locale: string;
};

type StageDefinition = {
  id: EmployerCandidateStatus;
  label: string;
  helper: string;
  targetDays: number;
  tone: 'neutral' | 'info' | 'success' | 'warning' | 'danger' | 'ai';
};

function getPipelineStages(locale: string): StageDefinition[] {
  const tr = locale.startsWith('tr');
  return [
    {id: 'new', label: tr ? 'Yeni' : 'New', helper: tr ? 'İlk temas bekliyor' : 'Waiting for first touch', targetDays: 1, tone: 'ai'},
    {id: 'reviewed', label: tr ? 'İncelendi' : 'Reviewed', helper: tr ? 'Ön eleme / uygunluk' : 'Screening / fit', targetDays: 2, tone: 'info'},
    {id: 'shortlisted', label: tr ? 'Kısa liste' : 'Shortlist', helper: tr ? 'Yönetici kararı' : 'Hiring manager decision', targetDays: 3, tone: 'success'},
    {id: 'interview', label: tr ? 'Görüşme' : 'Interview', helper: tr ? 'Takvim ve geri bildirim' : 'Schedule and feedback', targetDays: 4, tone: 'warning'},
    {id: 'offer', label: tr ? 'Teklif' : 'Offer', helper: tr ? 'Kapanış ve pazarlık' : 'Close and negotiation', targetDays: 2, tone: 'success'},
  ];
}

const NEXT_STAGE: Partial<Record<EmployerCandidateStatus, EmployerCandidateStatus>> = {
  new: 'reviewed',
  reviewed: 'shortlisted',
  shortlisted: 'interview',
  interview: 'offer',
  offer: 'hired',
};

function getWonLostStages(locale: string): StageDefinition[] {
  const tr = locale.startsWith('tr');
  return [
    {id: 'hired', label: tr ? 'İşe alındı' : 'Hired', helper: tr ? 'Başarıyla kapandı' : 'Closed successfully', targetDays: 0, tone: 'success'},
    {id: 'rejected', label: tr ? 'Arşiv' : 'Archive', helper: tr ? 'Reddedildi / uygun değil' : 'Rejected / not a fit', targetDays: 0, tone: 'danger'},
  ];
}

function daysSince(dateIso: string) {
  const date = new Date(dateIso);
  if (Number.isNaN(date.getTime())) return 0;
  const diff = Date.now() - date.getTime();
  return Math.max(0, Math.floor(diff / 86_400_000));
}

function getStageAge(candidate: EmployerCandidateOpportunity) {
  // Mock data has no stage timestamp yet; use the most relevant available event as a first UI approximation.
  return Math.max(1, daysSince(candidate.appliedAtIso));
}

function getStageSummary(candidates: EmployerCandidateOpportunity[], stage: StageDefinition) {
  const stageCandidates = candidates.filter((candidate) => candidate.status === stage.id);
  const count = stageCandidates.length;
  const averageMatch = count > 0 ? Math.round(stageCandidates.reduce((total, candidate) => total + candidate.matchScore, 0) / count) : 0;
  const overdueCount = stage.targetDays > 0 ? stageCandidates.filter((candidate) => getStageAge(candidate) > stage.targetDays).length : 0;
  const highIntentCount = stageCandidates.filter((candidate) => candidate.intentScore >= 75).length;
  return {stageCandidates, count, averageMatch, overdueCount, highIntentCount};
}

function getPipelineInsights(candidates: EmployerCandidateOpportunity[], stages: StageDefinition[]) {
  const active = candidates.filter((candidate) => !['hired', 'rejected'].includes(candidate.status));
  const overdue = active.filter((candidate) => {
    const stage = stages.find((item) => item.id === candidate.status);
    return stage && getStageAge(candidate) > stage.targetDays;
  });
  const hot = active.filter((candidate) => candidate.matchScore >= 85 && candidate.intentScore >= 75);
  const needsFeedback = active.filter((candidate) => candidate.status === 'interview' || candidate.status === 'shortlisted');
  const avgMatch = active.length > 0 ? Math.round(active.reduce((total, candidate) => total + candidate.matchScore, 0) / active.length) : 0;
  return {active, overdue, hot, needsFeedback, avgMatch};
}

export function PipelineKanbanBoard({
  candidates,
  selectedCandidateId,
  onSelect,
  onOpenCandidate,
  onMoveCandidate,
  onBulkMove,
  candidateTags = {},
  candidateNoteCounts = {},
  onBulkTag,
  onBulkNote,
  locale,
}: PipelineKanbanBoardProps) {
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [draggedCandidateId, setDraggedCandidateId] = useState<number | null>(null);
  const [dragOverStage, setDragOverStage] = useState<EmployerCandidateStatus | null>(null);
  const [bulkStage, setBulkStage] = useState<EmployerCandidateStatus>('shortlisted');
  const copy = getTalentWorkflowCopy(locale);
  const pipelineStages = useMemo(() => getPipelineStages(locale), [locale]);
  const wonLostStages = useMemo(() => getWonLostStages(locale), [locale]);
  const [bulkTag, setBulkTag] = useState(copy.workflow.quickTags[1]);
  const [bulkNote, setBulkNote] = useState('');

  const insights = useMemo(() => getPipelineInsights(candidates, pipelineStages), [candidates, pipelineStages]);

  const toggleSelected = (id: number) => {
    setSelectedIds((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]));
  };

  const clearSelected = () => setSelectedIds([]);

  const handleDrop = (event: DragEvent<HTMLDivElement>, stageId: EmployerCandidateStatus) => {
    event.preventDefault();
    const idFromPayload = Number(event.dataTransfer.getData('text/plain'));
    const candidateId = draggedCandidateId ?? idFromPayload;
    if (candidateId) {
      onMoveCandidate(candidateId, stageId);
      onSelect(candidateId);
    }
    setDraggedCandidateId(null);
    setDragOverStage(null);
  };

  const handleBulkMove = () => {
    if (selectedIds.length === 0) return;
    onBulkMove(selectedIds, bulkStage);
    setSelectedIds([]);
  };


  const handleBulkTag = () => {
    if (selectedIds.length === 0 || !bulkTag.trim()) return;
    onBulkTag?.(selectedIds, bulkTag);
  };

  const handleBulkNote = () => {
    if (selectedIds.length === 0 || !bulkNote.trim()) return;
    onBulkNote?.(selectedIds, bulkNote);
    setBulkNote('');
  };

  const handleBulkArchive = () => {
    if (selectedIds.length === 0) return;
    onBulkMove(selectedIds, 'rejected');
    onBulkTag?.(selectedIds, locale.startsWith('tr') ? 'Arşivlendi' : 'Archived');
    onBulkNote?.(selectedIds, locale.startsWith('tr') ? 'Toplu aksiyon ile arşive alındı.' : 'Archived via bulk action.');
    setSelectedIds([]);
  };

  return (
    <div className="space-y-4">
      <PipelineCommandBar
        insights={insights}
        locale={locale}
        stages={pipelineStages}
        selectedCount={selectedIds.length}
        bulkStage={bulkStage}
        setBulkStage={setBulkStage}
        onBulkMove={handleBulkMove}
        onBulkTag={handleBulkTag}
        onBulkNote={handleBulkNote}
        onBulkArchive={handleBulkArchive}
        onClearSelected={clearSelected}
        bulkTag={bulkTag}
        setBulkTag={setBulkTag}
        bulkNote={bulkNote}
        setBulkNote={setBulkNote}
      />

      <div className="grid gap-3 xl:grid-cols-5">
        {pipelineStages.map((stage) => {
          const summary = getStageSummary(candidates, stage);
          return (
            <PipelineStageColumn
              key={stage.id}
              stage={stage}
              candidates={summary.stageCandidates}
              selectedCandidateId={selectedCandidateId}
              selectedIds={selectedIds}
              averageMatch={summary.averageMatch}
              overdueCount={summary.overdueCount}
              highIntentCount={summary.highIntentCount}
              dragOver={dragOverStage === stage.id}
              onSelect={onSelect}
              onOpenCandidate={onOpenCandidate}
              onMoveCandidate={onMoveCandidate}
              onToggleSelected={toggleSelected}
              onDragStart={(candidateId) => setDraggedCandidateId(candidateId)}
              onDragOver={(event) => {
                event.preventDefault();
                setDragOverStage(stage.id);
              }}
              onDragLeave={() => setDragOverStage(null)}
              onDrop={(event) => handleDrop(event, stage.id)}
              candidateTags={candidateTags}
              candidateNoteCounts={candidateNoteCounts}
              locale={locale}
            />
          );
        })}
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        {wonLostStages.map((stage) => {
          const summary = getStageSummary(candidates, stage);
          return (
            <PipelineClosedStage
              key={stage.id}
              stage={stage}
              candidates={summary.stageCandidates}
              selectedCandidateId={selectedCandidateId}
              onSelect={onSelect}
              onOpenCandidate={onOpenCandidate}
              onMoveCandidate={onMoveCandidate}
              locale={locale}
            />
          );
        })}
      </div>
    </div>
  );
}

function PipelineCommandBar({
  insights,
  locale,
  stages,
  selectedCount,
  bulkStage,
  setBulkStage,
  onBulkMove,
  onBulkTag,
  onBulkNote,
  onBulkArchive,
  onClearSelected,
  bulkTag,
  setBulkTag,
  bulkNote,
  setBulkNote,
}: {
  insights: ReturnType<typeof getPipelineInsights>;
  locale: string;
  stages: StageDefinition[];
  selectedCount: number;
  bulkStage: EmployerCandidateStatus;
  setBulkStage: (stage: EmployerCandidateStatus) => void;
  onBulkMove: () => void;
  onBulkTag: () => void;
  onBulkNote: () => void;
  onBulkArchive: () => void;
  onClearSelected: () => void;
  bulkTag: string;
  setBulkTag: (tag: string) => void;
  bulkNote: string;
  setBulkNote: (note: string) => void;
}) {
  const copy = getTalentWorkflowCopy(locale);
  const statusLabels = workflowCandidateStatusLabels[getTalentWorkflowLanguage(locale)];
  const primaryInsight = insights.overdue.length > 0
    ? locale.startsWith('tr') ? `${insights.overdue.length} aday hedef süre dışında bekliyor. Öncelik: kısa liste ve görüşme aşamalarını temizle.` : `${insights.overdue.length} candidates are outside target time. Prioritize shortlist and interview stages.`
    : locale.startsWith('tr') ? `${insights.hot.length} yüksek niyetli aday hızlı aksiyon bekliyor. Bugün davet mesajı göndermek için iyi zaman.` : `${insights.hot.length} high-intent candidates need fast action. Today is a good time to send invites.`;

  return (
    <div className="rounded-[26px] border border-border bg-surface p-4 shadow-[0_18px_60px_rgba(15,23,42,0.07)]">
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_auto] xl:items-center">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge tone="ai" icon={<Layers3 className="size-3.5" />}>{copy.pipeline.title}</StatusBadge>
            <StatusBadge tone={insights.overdue.length > 0 ? 'warning' : 'success'} icon={<TimerReset className="size-3.5" />}>
              {insights.overdue.length > 0 ? `${insights.overdue.length} ${locale.startsWith('tr') ? 'geciken aday' : 'overdue candidates'}` : (locale.startsWith('tr') ? 'Hedef süre sağlıklı' : 'Target time healthy')}
            </StatusBadge>
            <StatusBadge tone="info" icon={<BadgeCheck className="size-3.5" />}>{copy.pipeline.avgMatch} {insights.avgMatch}</StatusBadge>
          </div>
          <h3 className="mt-3 text-lg font-black tracking-[-0.03em] text-foreground">{copy.pipeline.title}</h3>
          <p className="mt-1 max-w-3xl text-sm font-semibold leading-6 text-muted-foreground">{primaryInsight}</p>
        </div>

        <div className="min-w-0 rounded-2xl border border-border bg-surface-muted/55 p-3">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0 text-sm font-black text-foreground">
              {selectedCount > 0 ? `${selectedCount} ${copy.common.candidates} ${copy.pipeline.selected}` : (locale.startsWith('tr') ? 'Toplu aksiyon merkezi' : 'Bulk action center')}
              <p className="mt-0.5 text-xs font-semibold text-muted-foreground">{locale.startsWith('tr') ? 'Aşama, etiket, not ve arşiv aksiyonlarını tek seferde uygulayın.' : 'Apply stage, tag, note and archive actions in one pass.'}</p>
            </div>
            {selectedCount > 0 && (
              <Button size="sm" variant="ghost" onClick={onClearSelected}>
                {copy.common.clear}
              </Button>
            )}
          </div>

          <div className="mt-3 grid gap-2 lg:grid-cols-[minmax(150px,1fr)_auto]">
            <select
              value={bulkStage}
              onChange={(event) => setBulkStage(event.target.value as EmployerCandidateStatus)}
              className="h-10 rounded-2xl border border-border bg-surface px-3 text-xs font-black text-foreground outline-none focus:ring-4 focus:ring-[var(--ring)]"
              aria-label={copy.pipeline.bulkMove}
            >
              {stages.map((stage) => (
                <option key={stage.id} value={stage.id}>{stage.label}</option>
              ))}
              <option value="hired">{statusLabels.hired}</option>
              <option value="rejected">{locale.startsWith('tr') ? 'Arşiv' : 'Archive'}</option>
            </select>
            <Button size="sm" variant="secondary" disabled={selectedCount === 0} onClick={onBulkMove}>
              {copy.pipeline.move}
            </Button>
          </div>

          <div className="mt-2 grid gap-2 lg:grid-cols-[minmax(150px,1fr)_auto]">
            <input
              value={bulkTag}
              onChange={(event) => setBulkTag(event.target.value)}
              placeholder={copy.pipeline.tagPlaceholder}
              className="h-10 rounded-2xl border border-border bg-surface px-3 text-xs font-black text-foreground outline-none placeholder:text-muted-foreground focus:ring-4 focus:ring-[var(--ring)]"
            />
            <Button size="sm" variant="soft" disabled={selectedCount === 0 || !bulkTag.trim()} onClick={onBulkTag} className="gap-2">
              <Tag className="size-4" /> {copy.pipeline.addTag}
            </Button>
          </div>

          <div className="mt-2 grid gap-2 lg:grid-cols-[minmax(180px,1fr)_auto]">
            <input
              value={bulkNote}
              onChange={(event) => setBulkNote(event.target.value)}
              placeholder={copy.pipeline.notePlaceholder}
              className="h-10 rounded-2xl border border-border bg-surface px-3 text-xs font-black text-foreground outline-none placeholder:text-muted-foreground focus:ring-4 focus:ring-[var(--ring)]"
            />
            <Button size="sm" variant="outline" disabled={selectedCount === 0 || !bulkNote.trim()} onClick={onBulkNote} className="gap-2">
              <NotebookPen className="size-4" /> {copy.pipeline.addNote}
            </Button>
          </div>

          <div className="mt-2 flex flex-wrap gap-2">
            <Button size="sm" variant="ghost" disabled={selectedCount === 0} onClick={onBulkArchive} className="gap-2 text-muted-foreground hover:text-destructive">
              {copy.workflow.archive}
            </Button>
          </div>
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <PipelineInsightMetric icon={<UsersRound className="size-4" />} label={copy.pipeline.activeCandidates} value={insights.active.length} helper={locale.startsWith('tr') ? 'süreç içinde' : 'in pipeline'} />
        <PipelineInsightMetric icon={<Zap className="size-4" />} label={copy.pipeline.hotOpportunities} value={insights.hot.length} helper={`85+ ${copy.common.match} & 75+ ${copy.common.intent}`} />
        <PipelineInsightMetric icon={<BellRing className="size-4" />} label={copy.pipeline.waitingFeedback} value={insights.needsFeedback.length} helper={locale.startsWith('tr') ? 'kısa liste/görüşme' : 'shortlist/interview'} />
        <PipelineInsightMetric icon={<AlertTriangle className="size-4" />} label={copy.pipeline.overdue} value={insights.overdue.length} helper={locale.startsWith('tr') ? 'aksiyon gecikti' : 'action delayed'} tone={insights.overdue.length > 0 ? 'warning' : 'success'} />
      </div>
    </div>
  );
}

function PipelineInsightMetric({
  icon,
  label,
  value,
  helper,
  tone = 'neutral',
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  helper: string;
  tone?: 'neutral' | 'warning' | 'success';
}) {
  return (
    <div className="rounded-2xl border border-border bg-surface-muted/45 p-3">
      <div className={cn(
        'mb-2 flex size-9 items-center justify-center rounded-xl',
        tone === 'warning' ? 'bg-amber-500/10 text-warning' : tone === 'success' ? 'bg-emerald-500/10 text-success' : 'bg-primary/10 text-primary'
      )}>
        {icon}
      </div>
      <div className="flex items-end justify-between gap-2">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.14em] text-muted-foreground">{label}</p>
          <p className="mt-1 text-xs font-semibold text-muted-foreground">{helper}</p>
        </div>
        <p className="text-2xl font-black tracking-[-0.04em] text-foreground">{value}</p>
      </div>
    </div>
  );
}

function PipelineStageColumn({
  stage,
  candidates,
  selectedCandidateId,
  selectedIds,
  averageMatch,
  overdueCount,
  highIntentCount,
  dragOver,
  onSelect,
  onOpenCandidate,
  onMoveCandidate,
  onToggleSelected,
  onDragStart,
  onDragOver,
  onDragLeave,
  onDrop,
  candidateTags,
  candidateNoteCounts,
  locale,
}: {
  stage: StageDefinition;
  candidates: EmployerCandidateOpportunity[];
  selectedCandidateId?: number;
  selectedIds: number[];
  averageMatch: number;
  overdueCount: number;
  highIntentCount: number;
  dragOver: boolean;
  onSelect: (id: number) => void;
  onOpenCandidate: (id: number) => void;
  onMoveCandidate: (id: number, status: EmployerCandidateStatus) => void;
  onToggleSelected: (id: number) => void;
  onDragStart: (id: number) => void;
  onDragOver: (event: DragEvent<HTMLDivElement>) => void;
  onDragLeave: () => void;
  onDrop: (event: DragEvent<HTMLDivElement>) => void;
  candidateTags: Record<number, string[]>;
  candidateNoteCounts: Record<number, number>;
  locale: string;
}) {
  const copy = getTalentWorkflowCopy(locale);
  return (
    <section
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      className={cn(
        'min-h-[560px] rounded-[28px] border bg-surface-muted/45 p-3 transition',
        dragOver ? 'border-primary/55 bg-primary/10 ring-4 ring-[var(--ring)]' : 'border-border'
      )}
    >
      <div className="mb-3 rounded-[22px] border border-border bg-surface p-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-sm font-black text-foreground">{stage.label}</h3>
              <StatusBadge tone={stage.tone} className="py-0.5 text-[10px]">{candidates.length}</StatusBadge>
            </div>
            <p className="mt-1 text-xs font-semibold text-muted-foreground">{stage.helper}</p>
          </div>
          <div className="flex size-10 items-center justify-center rounded-2xl bg-primary/10 text-primary">
            <Layers3 className="size-5" />
          </div>
        </div>

        <div className="mt-3 grid grid-cols-3 gap-2">
          <StageMiniMetric label={copy.common.match} value={averageMatch || '—'} />
          <StageMiniMetric label={copy.common.intent} value={highIntentCount} />
          <StageMiniMetric label={locale.startsWith('tr') ? 'Hedef' : 'Target'} value={overdueCount} danger={overdueCount > 0} />
        </div>
      </div>

      <div className="space-y-2">
        {candidates.length > 0 ? candidates.map((candidate) => (
          <PipelineCandidateCard
            key={candidate.id}
            candidate={candidate}
            stage={stage}
            selected={selectedCandidateId === candidate.id}
            checked={selectedIds.includes(candidate.id)}
            onSelect={() => onSelect(candidate.id)}
            onOpenCandidate={() => onOpenCandidate(candidate.id)}
            onToggleSelected={() => onToggleSelected(candidate.id)}
            onDragStart={() => onDragStart(candidate.id)}
            onMoveCandidate={(status) => onMoveCandidate(candidate.id, status)}
            tags={candidateTags[candidate.id] ?? []}
            noteCount={candidateNoteCounts[candidate.id] ?? 0}
            locale={locale}
          />
        )) : (
          <div className="flex min-h-[220px] items-center justify-center rounded-[22px] border border-dashed border-border bg-surface/45 p-4 text-center">
            <div>
              <UsersRound className="mx-auto size-7 text-muted-foreground/70" />
              <p className="mt-3 text-xs font-black text-foreground">{copy.pipeline.stageEmpty}</p>
              <p className="mt-1 text-xs font-semibold leading-5 text-muted-foreground">{copy.pipeline.dragHere}</p>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

function StageMiniMetric({label, value, danger}: {label: string; value: number | string; danger?: boolean}) {
  return (
    <div className={cn('rounded-xl border px-2 py-2 text-center', danger ? 'border-amber-500/25 bg-amber-500/10' : 'border-border bg-surface-muted/55')}>
      <p className="text-[10px] font-black uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
      <p className={cn('mt-0.5 text-sm font-black', danger ? 'text-warning' : 'text-foreground')}>{value}</p>
    </div>
  );
}

function PipelineCandidateCard({
  candidate,
  stage,
  selected,
  checked,
  onSelect,
  onOpenCandidate,
  onToggleSelected,
  onDragStart,
  onMoveCandidate,
  tags,
  noteCount,
  locale,
}: {
  candidate: EmployerCandidateOpportunity;
  stage: StageDefinition;
  selected: boolean;
  checked: boolean;
  onSelect: () => void;
  onOpenCandidate: () => void;
  onToggleSelected: () => void;
  onDragStart: () => void;
  onMoveCandidate: (status: EmployerCandidateStatus) => void;
  tags: string[];
  noteCount: number;
  locale: string;
}) {
  const copy = getTalentWorkflowCopy(locale);
  const lang = getTalentWorkflowLanguage(locale);
  const sourceLabels = workflowSourceLabels[lang];
  const availabilityLabels = workflowAvailabilityLabels[lang];
  const age = getStageAge(candidate);
  const overdue = stage.targetDays > 0 && age > stage.targetDays;
  const nextStage = NEXT_STAGE[candidate.status];

  return (
    <article
      draggable
      onDragStart={(event) => {
        event.dataTransfer.effectAllowed = 'move';
        event.dataTransfer.setData('text/plain', String(candidate.id));
        onDragStart();
      }}
      onClick={onSelect}
      className={cn(
        'group rounded-[22px] border bg-surface p-3 text-left shadow-[0_14px_44px_rgba(15,23,42,0.07)] transition hover:-translate-y-0.5 hover:border-primary/35 hover:bg-surface-strong focus-within:ring-4 focus-within:ring-[var(--ring)]',
        selected ? 'border-primary/55 ring-4 ring-[var(--ring)]' : 'border-border',
        overdue && 'border-amber-500/35'
      )}
    >
      <div className="flex items-start gap-2">
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            onToggleSelected();
          }}
          className={cn(
            'mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-md border transition focus:outline-none focus:ring-4 focus:ring-[var(--ring)]',
            checked ? 'border-primary bg-primary text-primary-foreground' : 'border-border bg-surface-muted text-transparent hover:border-primary/45'
          )}
          aria-label={`${candidate.name} ${locale.startsWith('tr') ? 'adayını seç' : 'select candidate'}`}
          aria-pressed={checked}
        >
          <CheckCircle2 className="size-3.5" />
        </button>

        <div className="flex min-w-0 flex-1 items-start gap-2">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,var(--primary),var(--accent))] text-xs font-black text-primary-foreground shadow-sm">
            {candidate.initials}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="truncate text-sm font-black text-foreground">{candidate.name}</p>
                <p className="mt-0.5 line-clamp-1 text-xs font-semibold text-muted-foreground">{candidate.headline}</p>
              </div>
              <GripVertical className="mt-1 size-4 shrink-0 text-muted-foreground/50" />
            </div>

            <div className="mt-3 flex flex-wrap gap-1.5">
              <ScoreBadge score={candidate.matchScore} label={copy.common.match} size="sm" />
              <span className="rounded-full border border-blue-500/20 bg-blue-500/10 px-2 py-1 text-[10px] font-black text-blue-500">{copy.common.intent} {candidate.intentScore}</span>
              {overdue && <span className="rounded-full border border-amber-500/25 bg-amber-500/10 px-2 py-1 text-[10px] font-black text-warning">{copy.pipeline.slaLate(age - stage.targetDays)}</span>}
            </div>
          </div>
        </div>
      </div>

      {(tags.length > 0 || noteCount > 0) && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {tags.slice(0, 2).map((tag) => (
            <span key={tag} className="rounded-full border border-primary/20 bg-primary/10 px-2 py-1 text-[10px] font-black text-primary">#{tag}</span>
          ))}
          {tags.length > 2 && (
            <span className="rounded-full border border-border bg-surface-muted px-2 py-1 text-[10px] font-bold text-muted-foreground">+{tags.length - 2}</span>
          )}
          {noteCount > 0 && (
            <span className="rounded-full border border-border bg-surface-muted px-2 py-1 text-[10px] font-bold text-muted-foreground">{noteCount} {copy.common.notes}</span>
          )}
        </div>
      )}

      <div className="mt-3 grid grid-cols-2 gap-2 text-[11px] font-bold text-muted-foreground">
        <div className="rounded-xl border border-border bg-surface-muted/55 px-2 py-1.5">
          <span className="block text-[10px] font-black uppercase tracking-[0.12em] text-muted-foreground/80">{copy.common.source}</span>
          {sourceLabels[candidate.source]}
        </div>
        <div className="rounded-xl border border-border bg-surface-muted/55 px-2 py-1.5">
          <span className="block text-[10px] font-black uppercase tracking-[0.12em] text-muted-foreground/80">{copy.common.availability}</span>
          {availabilityLabels[candidate.availability]}
        </div>
      </div>

      <div className="mt-3 rounded-2xl border border-border bg-surface-muted/45 p-2.5">
        <p className="line-clamp-2 text-[11px] font-semibold leading-5 text-muted-foreground">{candidate.recommendedAction}</p>
      </div>

      <div className="mt-3 flex items-center justify-between gap-2 border-t border-border/70 pt-3">
        <span className="inline-flex items-center gap-1 text-[11px] font-bold text-muted-foreground">
          <Clock3 className="size-3.5" /> {copy.pipeline.daysInStage(age)}
        </span>
        <div className="flex shrink-0 items-center gap-1.5">
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              onOpenCandidate();
            }}
            className="inline-flex size-8 items-center justify-center rounded-full border border-border bg-surface text-muted-foreground transition hover:border-primary/35 hover:text-primary focus:outline-none focus:ring-4 focus:ring-[var(--ring)]"
            aria-label={`${candidate.name} ${copy.common.profile360}`}
          >
            <PanelRightOpen className="size-4" />
          </button>
          {nextStage && (
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation();
                onMoveCandidate(nextStage);
              }}
              className="inline-flex size-8 items-center justify-center rounded-full border border-primary/20 bg-primary/10 text-primary transition hover:bg-primary/15 focus:outline-none focus:ring-4 focus:ring-[var(--ring)]"
              aria-label={`${candidate.name} ${copy.pipeline.nextStage}`}
            >
              <ArrowRight className="size-4" />
            </button>
          )}
        </div>
      </div>
    </article>
  );
}

function PipelineClosedStage({
  stage,
  candidates,
  selectedCandidateId,
  onSelect,
  onOpenCandidate,
  onMoveCandidate,
  locale,
}: {
  stage: StageDefinition;
  candidates: EmployerCandidateOpportunity[];
  selectedCandidateId?: number;
  onSelect: (id: number) => void;
  onOpenCandidate: (id: number) => void;
  onMoveCandidate: (id: number, status: EmployerCandidateStatus) => void;
  locale: string;
}) {
  const copy = getTalentWorkflowCopy(locale);
  return (
    <section className="rounded-[26px] border border-border bg-surface-muted/35 p-3">
      <div className="mb-3 flex items-center justify-between gap-3 rounded-2xl border border-border bg-surface px-4 py-3">
        <div>
          <p className="text-sm font-black text-foreground">{stage.label}</p>
          <p className="text-xs font-semibold text-muted-foreground">{stage.helper}</p>
        </div>
        <StatusBadge tone={stage.tone}>{candidates.length}</StatusBadge>
      </div>
      {candidates.length > 0 ? (
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
          {candidates.map((candidate) => (
            <button
              key={candidate.id}
              type="button"
              onClick={() => onSelect(candidate.id)}
              className={cn('rounded-2xl border bg-surface p-3 text-left transition hover:border-primary/35 hover:bg-surface-strong', selectedCandidateId === candidate.id ? 'border-primary/55 ring-4 ring-[var(--ring)]' : 'border-border')}
            >
              <div className="flex items-center justify-between gap-2">
                <p className="truncate text-sm font-black text-foreground">{candidate.name}</p>
                <span className="text-xs font-black text-primary">{candidate.matchScore}</span>
              </div>
              <p className="mt-1 line-clamp-1 text-xs font-semibold text-muted-foreground">{candidate.headline}</p>
              <div className="mt-3 flex flex-wrap gap-1.5">
                <button
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    onOpenCandidate(candidate.id);
                  }}
                  className="rounded-full border border-border bg-surface-muted px-2.5 py-1 text-[10px] font-black text-muted-foreground transition hover:text-primary"
                >
                  360
                </button>
                <button
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    onMoveCandidate(candidate.id, 'reviewed');
                  }}
                  className="rounded-full border border-border bg-surface-muted px-2.5 py-1 text-[10px] font-black text-muted-foreground transition hover:text-primary"
                >
                  {locale.startsWith('tr') ? 'Geri al' : 'Move back'}
                </button>
              </div>
            </button>
          ))}
        </div>
      ) : (
        <p className="rounded-2xl border border-dashed border-border bg-surface/45 p-4 text-center text-xs font-semibold text-muted-foreground">{copy.pipeline.stageEmpty}</p>
      )}
    </section>
  );
}
