import type {SavedJob, SavedJobStatus} from '@/types/saved';

// Kanban sutunlari. 'archived' bilerek disarida: arsiv aktif pipeline degildir,
// kendi sekmesinden gorulur.
export const SAVED_PIPELINE_STATUSES = ['reviewing', 'applied', 'interview', 'offer', 'rejected'] as const;

export type SavedPipelineStatus = (typeof SAVED_PIPELINE_STATUSES)[number];

export type SavedJobTabKey = 'all' | SavedJobStatus;

export type SavedJobSortKey = 'activity' | 'deadline' | 'score';

export type SavedPipelineCounts = Record<SavedJobTabKey, number>;

const PIPELINE_STATUS_SET: ReadonlySet<string> = new Set(SAVED_PIPELINE_STATUSES);

// Teklif orani, sonuclanma yoluna girmis basvurular uzerinden hesaplanir;
// henuz degerlendirme asamasindaki kayitlar paydayi sismanlatmasin diye
// 'reviewing' disarida birakilir.
const OUTCOME_STATUSES: readonly SavedJobStatus[] = ['applied', 'interview', 'offer', 'rejected'];

export function isSavedPipelineStatus(status: string): status is SavedPipelineStatus {
  return PIPELINE_STATUS_SET.has(status);
}

export function countSavedJobsByStatus(jobs: SavedJob[]): SavedPipelineCounts {
  const counts: SavedPipelineCounts = {
    all: jobs.length,
    reviewing: 0,
    applied: 0,
    interview: 0,
    offer: 0,
    rejected: 0,
    archived: 0,
  };

  for (const job of jobs) {
    counts[job.status] += 1;
  }

  return counts;
}

export function groupSavedJobsByStatus(jobs: SavedJob[]): Record<SavedPipelineStatus, SavedJob[]> {
  const groups: Record<SavedPipelineStatus, SavedJob[]> = {
    reviewing: [],
    applied: [],
    interview: [],
    offer: [],
    rejected: [],
  };

  for (const job of jobs) {
    if (isSavedPipelineStatus(job.status)) {
      groups[job.status].push(job);
    }
  }

  return groups;
}

export function countActivePipeline(counts: SavedPipelineCounts): number {
  return counts.reviewing + counts.applied + counts.interview;
}

export function calculateOfferRate(jobs: SavedJob[]): number | null {
  const decided = jobs.filter((job) => OUTCOME_STATUSES.includes(job.status));
  if (decided.length === 0) {
    return null;
  }

  const offers = decided.filter((job) => job.status === 'offer').length;
  return Math.round((offers / decided.length) * 100);
}

function lastActivityAt(job: SavedJob): string {
  return job.updated_at ?? job.created_at ?? '';
}

function matchesQuery(job: SavedJob, needle: string): boolean {
  const haystack = [
    job.title,
    job.company_name,
    job.location ?? '',
    job.source_name,
    ...job.matched_keywords,
    ...job.notes.map((note) => note.content),
  ];

  return haystack.some((value) => value.toLowerCase().includes(needle));
}

// Bos degerler her zaman listenin sonuna dusmelidir: tarihsiz ya da skorsuz bir
// kayit, siralama yonu ne olursa olsun listenin basini kapatmamalidir.
function compareBySortKey(left: SavedJob, right: SavedJob, sortKey: SavedJobSortKey): number {
  if (sortKey === 'deadline') {
    if (!left.deadline_at && !right.deadline_at) return 0;
    if (!left.deadline_at) return 1;
    if (!right.deadline_at) return -1;
    return left.deadline_at.localeCompare(right.deadline_at);
  }

  if (sortKey === 'score') {
    const leftScore = left.match_score;
    const rightScore = right.match_score;
    if (leftScore === null && rightScore === null) return 0;
    if (leftScore === null) return 1;
    if (rightScore === null) return -1;
    return rightScore - leftScore;
  }

  return lastActivityAt(right).localeCompare(lastActivityAt(left));
}

export function filterAndSortSavedJobs({
  jobs,
  tab,
  query,
  sortKey,
}: {
  jobs: SavedJob[];
  tab: SavedJobTabKey;
  query: string;
  sortKey: SavedJobSortKey;
}): SavedJob[] {
  const needle = query.trim().toLowerCase();

  return jobs
    .filter((job) => (tab === 'all' ? true : job.status === tab))
    .filter((job) => (needle ? matchesQuery(job, needle) : true))
    .slice()
    .sort((left, right) => compareBySortKey(left, right, sortKey));
}
