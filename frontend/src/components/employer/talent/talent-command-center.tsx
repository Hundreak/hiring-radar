"use client";

import Link from "next/link";
import {
  Activity,
  ArrowRight,
  BadgeCheck,
  BarChart3,
  BellRing,
  Briefcase,
  CalendarClock,
  CheckCircle2,
  ChevronDown,
  ClipboardCheck,
  Clock3,
  Command,
  Download,
  Eye,
  LayoutGrid,
  ListChecks,
  LocateFixed,
  MailPlus,
  MapPin,
  MessageSquareText,
  MoreHorizontal,
  MousePointer2,
  PanelRightOpen,
  Radar,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Star,
  Target,
  Upload,
  WandSparkles,
  X,
  Zap,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Candidate360Drawer } from "@/components/employer/talent/candidate-360-drawer";
import { CandidateComparisonMatrixV2 } from "@/components/employer/talent/candidate-comparison-matrix-v2";
import { CandidateWorkflowPanel } from "@/components/employer/talent/candidate-workflow-panel";
import { PipelineKanbanBoard } from "@/components/employer/talent/pipeline-kanban-board";
import { OutreachCampaignPanel } from "@/components/employer/talent/outreach-campaign-panel";
import {
  EmptyState,
  ScoreBadge,
  StatusBadge,
  SurfaceCard,
} from "@/components/employer/ui";
import {
  employerCandidatesMock,
  employerJobsMock,
} from "@/data/employer-mock-data";
import { formatCompactNumber } from "@/lib/employer-format";
import {
  availabilityLabels,
  candidateSourceLabels,
  candidateStatusLabels,
  getEmployerTalentCopy,
  getJobsTalentLanguage,
  workModelLabels,
} from "@/lib/employer-jobs-talent-copy";
import {
  bulkNoteEmployerCandidates,
  bulkTagEmployerCandidates,
  createEmployerOutreachCampaign,
  listEmployerOutreachCampaigns,
  loadEmployerTalentWorkflow,
  removeEmployerCandidateTag,
} from "@/lib/employer-outreach-api";
import { cn } from "@/lib/utils";
import type {
  EmployerCandidateOpportunity,
  EmployerCandidateStatus,
} from "@/types/employer";
import type {
  CandidateWorkflowById,
  CandidateWorkflowNote,
  CandidateWorkflowState,
  EmployerOutreachCampaign,
  EmployerOutreachCampaignCreatePayload,
} from "@/types/employer-outreach";

type TalentView = "radar" | "pipeline" | "compare" | "outreach";
type TalentSort = "recommended" | "match" | "intent" | "recent" | "salary";

type TalentCommandCenterProps = {
  locale: string;
  initialView?: TalentView;
  initialCandidateId?: number | null;
  initialPanel?: "360" | null;
};

type TalentCopy = ReturnType<typeof getEmployerTalentCopy>;
type LocalizedTalentLabels = {
  availability: (typeof availabilityLabels)["tr"];
  status: (typeof candidateStatusLabels)["tr"];
  workModel: (typeof workModelLabels)["tr"];
  source: (typeof candidateSourceLabels)["tr"];
};

const INITIAL_WORKFLOW_TAGS: Record<number, string[]> = {
  1: ["Sıcak aday", "Teknik güçlü", "HM bekliyor"],
  2: ["Design system", "Remote uygun"],
  3: ["Referans", "Backend güçlü"],
  4: ["Hızlı kapanış"],
  5: ["Maaş kontrol"],
};


function isTalentView(value: string | null | undefined): value is TalentView {
  return value === "radar" || value === "pipeline" || value === "compare" || value === "outreach";
}


function createInitialCandidateWorkflow(
  candidates: EmployerCandidateOpportunity[],
  copy: TalentCopy,
): Record<number, CandidateWorkflowState> {
  return candidates.reduce<Record<number, CandidateWorkflowState>>(
    (acc, candidate) => {
      const tags = INITIAL_WORKFLOW_TAGS[candidate.id] ?? [];
      acc[candidate.id] = {
        tags,
        notes: [
          {
            id: `ai-${candidate.id}`,
            author: copy.detail.aiAuthor,
            body: candidate.recommendedAction,
            createdAt: copy.labels.today,
            tone: "ai",
          },
          ...(candidate.risks[0]
            ? [
                {
                  id: `risk-${candidate.id}`,
                  author: copy.detail.opsAuthor,
                  body: `${copy.detail.verifyInInterview}: ${candidate.risks[0]}`,
                  createdAt: copy.labels.yesterday,
                  tone: "warning" as const,
                },
              ]
            : []),
        ],
      };
      return acc;
    },
    {},
  );
}

function createUserNote(
  body: string,
  candidateId: number,
  locale: string,
  copy: TalentCopy,
): CandidateWorkflowNote {
  return {
    id: `note-${candidateId}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    author: copy.detail.you,
    body,
    createdAt: new Intl.DateTimeFormat(locale === "tr" ? "tr-TR" : "en-US", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date()),
    tone: "neutral",
  };
}

function mergeWorkflow(
  current: CandidateWorkflowById,
  incoming: CandidateWorkflowById,
): CandidateWorkflowById {
  if (Object.keys(incoming).length === 0) return current;
  const next: CandidateWorkflowById = { ...current };

  Object.entries(incoming).forEach(([candidateId, incomingState]) => {
    const numericId = Number(candidateId);
    if (!Number.isFinite(numericId)) return;

    const existing = next[numericId] ?? { tags: [], notes: [] };
    const tags = [...existing.tags];
    incomingState.tags.forEach((tag) => {
      if (
        !tags.some(
          (item) =>
            item.toLocaleLowerCase("tr-TR") === tag.toLocaleLowerCase("tr-TR"),
        )
      ) {
        tags.push(tag);
      }
    });

    const noteIds = new Set(existing.notes.map((note) => note.id));
    const notes = [
      ...incomingState.notes.filter((note) => !noteIds.has(note.id)),
      ...existing.notes,
    ];

    next[numericId] = { tags, notes };
  });

  return next;
}

function normalizeTag(tag: string) {
  return tag.trim().replace(/\s+/g, " ");
}

function formatSalary(
  candidate: EmployerCandidateOpportunity,
  copy: TalentCopy,
) {
  if (!candidate.salaryExpectation) return copy.labels.salaryNotSpecified;
  const { min, max, currency } = candidate.salaryExpectation;
  return `${formatCompactNumber(min)}-${formatCompactNumber(max)} ${currency}`;
}

function getStatusTone(
  status: EmployerCandidateStatus,
): "neutral" | "success" | "warning" | "danger" | "info" | "ai" {
  if (status === "hired" || status === "shortlisted" || status === "offer")
    return "success";
  if (status === "interview") return "info";
  if (status === "rejected") return "danger";
  if (status === "new") return "ai";
  return "neutral";
}

function getAvailabilityTone(
  availability: EmployerCandidateOpportunity["availability"],
): "success" | "warning" | "info" | "neutral" {
  if (availability === "immediate") return "success";
  if (availability === "two_weeks") return "info";
  if (availability === "one_month") return "warning";
  return "neutral";
}

function includesText(haystack: string, needle: string, localeCode = "tr-TR") {
  return haystack
    .toLocaleLowerCase(localeCode)
    .includes(needle.toLocaleLowerCase(localeCode));
}

function buildCandidateSearchText(
  candidate: EmployerCandidateOpportunity,
  labels: LocalizedTalentLabels,
) {
  return [
    candidate.name,
    candidate.headline,
    candidate.location,
    candidate.education,
    candidate.targetRole,
    candidate.recommendedAction,
    candidate.highlights.join(" "),
    candidate.risks.join(" "),
    candidate.skills.map((skill) => skill.name).join(" "),
    labels.source[candidate.source],
    labels.workModel[candidate.workPreference],
  ]
    .filter(Boolean)
    .join(" ");
}

export function TalentCommandCenter({
  locale,
  initialView = "radar",
  initialCandidateId = null,
  initialPanel = null,
}: TalentCommandCenterProps) {
  const talentCopy = getEmployerTalentCopy(locale);
  const lang = getJobsTalentLanguage(locale);
  const labels: LocalizedTalentLabels = {
    availability: availabilityLabels[lang],
    status: candidateStatusLabels[lang],
    workModel: workModelLabels[lang],
    source: candidateSourceLabels[lang],
  };
  const localeCode = lang === "tr" ? "tr-TR" : "en-US";

  const [query, setQuery] = useState("");
  const [selectedJob, setSelectedJob] = useState<string>("all");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [selectedSource, setSelectedSource] = useState<string>("all");
  const [selectedAvailability, setSelectedAvailability] =
    useState<string>("all");
  const [minScore, setMinScore] = useState(70);
  const requestedInitialView = isTalentView(initialView) ? initialView : "radar";
  const requestedInitialCandidateId =
    initialCandidateId ?? employerCandidatesMock[0]?.id ?? 1;

  const [sortBy, setSortBy] = useState<TalentSort>("recommended");
  const [view, setView] = useState<TalentView>(requestedInitialView);
  const [selectedCandidateId, setSelectedCandidateId] = useState<number>(
    requestedInitialCandidateId,
  );
  const [stageOverrides, setStageOverrides] = useState<
    Partial<Record<number, EmployerCandidateStatus>>
  >({});
  const [candidate360Open, setCandidate360Open] = useState(initialPanel === "360");
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);
  const [candidateWorkflow, setCandidateWorkflow] = useState<
    Record<number, CandidateWorkflowState>
  >(() => createInitialCandidateWorkflow(employerCandidatesMock, talentCopy));
  const [workflowSyncState, setWorkflowSyncState] = useState<
    "syncing" | "synced" | "offline"
  >("syncing");
  const [campaignDrafts, setCampaignDrafts] = useState<
    EmployerOutreachCampaign[]
  >([]);


  useEffect(() => {
    let mounted = true;

    async function hydrateEmployerWorkflow() {
      try {
        setWorkflowSyncState("syncing");
        const [workflow, campaigns] = await Promise.all([
          loadEmployerTalentWorkflow(),
          listEmployerOutreachCampaigns(),
        ]);
        if (!mounted) return;
        setCandidateWorkflow((current) => mergeWorkflow(current, workflow));
        setCampaignDrafts(campaigns);
        setWorkflowSyncState("synced");
      } catch {
        if (mounted) setWorkflowSyncState("offline");
      }
    }

    void hydrateEmployerWorkflow();
    return () => {
      mounted = false;
    };
  }, []);

  const selectedJobMeta = useMemo(() => {
    if (selectedJob === "all") return null;
    return (
      employerJobsMock.find((job) => String(job.id) === selectedJob) ?? null
    );
  }, [selectedJob]);

  const candidatesWithStage = useMemo(() => {
    return employerCandidatesMock.map((candidate) => ({
      ...candidate,
      status: stageOverrides[candidate.id] ?? candidate.status,
    }));
  }, [stageOverrides]);

  const moveCandidateToStage = (
    candidateId: number,
    status: EmployerCandidateStatus,
  ) => {
    setStageOverrides((current) => ({ ...current, [candidateId]: status }));
    setSelectedCandidateId(candidateId);
  };

  const bulkMoveCandidatesToStage = (
    candidateIds: number[],
    status: EmployerCandidateStatus,
  ) => {
    if (candidateIds.length === 0) return;
    setStageOverrides((current) => {
      const next = { ...current };
      candidateIds.forEach((candidateId) => {
        next[candidateId] = status;
      });
      return next;
    });
    setSelectedCandidateId(candidateIds[0] ?? selectedCandidateId);
  };

  const addTagsToCandidates = (candidateIds: number[], tag: string) => {
    const normalized = normalizeTag(tag);
    if (!normalized || candidateIds.length === 0) return;
    setCandidateWorkflow((current) => {
      const next = { ...current };
      candidateIds.forEach((candidateId) => {
        const existing = next[candidateId] ?? { tags: [], notes: [] };
        next[candidateId] = {
          ...existing,
          tags: existing.tags.some(
            (item) =>
              item.toLocaleLowerCase(localeCode) ===
              normalized.toLocaleLowerCase(localeCode),
          )
            ? existing.tags
            : [...existing.tags, normalized],
        };
      });
      return next;
    });
    void bulkTagEmployerCandidates(candidateIds, normalized)
      .then((workflow) => {
        setWorkflowSyncState("synced");
        setCandidateWorkflow((current) => mergeWorkflow(current, workflow));
      })
      .catch(() => setWorkflowSyncState("offline"));
  };

  const removeTagFromCandidate = (candidateId: number, tag: string) => {
    setCandidateWorkflow((current) => {
      const existing = current[candidateId] ?? { tags: [], notes: [] };
      return {
        ...current,
        [candidateId]: {
          ...existing,
          tags: existing.tags.filter((item) => item !== tag),
        },
      };
    });
    void removeEmployerCandidateTag(candidateId, tag)
      .then((workflow) => {
        setWorkflowSyncState("synced");
        setCandidateWorkflow((current) => mergeWorkflow(current, workflow));
      })
      .catch(() => setWorkflowSyncState("offline"));
  };

  const addNotesToCandidates = (candidateIds: number[], body: string) => {
    const normalized = body.trim();
    if (!normalized || candidateIds.length === 0) return;
    setCandidateWorkflow((current) => {
      const next = { ...current };
      candidateIds.forEach((candidateId) => {
        const existing = next[candidateId] ?? { tags: [], notes: [] };
        next[candidateId] = {
          ...existing,
          notes: [
            createUserNote(normalized, candidateId, locale, talentCopy),
            ...existing.notes,
          ],
        };
      });
      return next;
    });
    void bulkNoteEmployerCandidates(candidateIds, normalized)
      .then((workflow) => {
        setWorkflowSyncState("synced");
        setCandidateWorkflow((current) => mergeWorkflow(current, workflow));
      })
      .catch(() => setWorkflowSyncState("offline"));
  };

  const createOutreachCampaignDraft = async (
    payload: EmployerOutreachCampaignCreatePayload,
  ) => {
    const result = await createEmployerOutreachCampaign(payload);
    setCampaignDrafts((current) => [
      result.campaign,
      ...current.filter((item) => item.id !== result.campaign.id),
    ]);
    setCandidateWorkflow((current) => mergeWorkflow(current, result.workflow));
    setWorkflowSyncState("synced");
  };

  const filteredCandidates = (() => {
    const normalizedQuery = query.trim();
    const selectedJobSkills = selectedJobMeta?.tags ?? [];

    const list = candidatesWithStage.filter((candidate) => {
      if (
        normalizedQuery &&
        !includesText(
          buildCandidateSearchText(candidate, labels),
          normalizedQuery,
          localeCode,
        )
      )
        return false;
      if (selectedStatus !== "all" && candidate.status !== selectedStatus)
        return false;
      if (selectedSource !== "all" && candidate.source !== selectedSource)
        return false;
      if (
        selectedAvailability !== "all" &&
        candidate.availability !== selectedAvailability
      )
        return false;
      if (candidate.matchScore < minScore) return false;
      if (selectedJobMeta && selectedJobSkills.length > 0) {
        const candidateSkills = candidate.skills.map((skill) =>
          skill.name.toLocaleLowerCase(localeCode),
        );
        const hasJobSkill = selectedJobSkills.some((tag) =>
          candidateSkills.includes(tag.toLocaleLowerCase(localeCode)),
        );
        const matchesTargetRole =
          candidate.targetRole &&
          includesText(
            candidate.targetRole,
            selectedJobMeta.title.split(" ")[0] ?? "",
            localeCode,
          );
        if (!hasJobSkill && !matchesTargetRole) return false;
      }
      return true;
    });

    return [...list].sort((a, b) => {
      if (sortBy === "recommended") {
        return (
          b.matchScore +
          b.intentScore * 0.65 -
          (a.matchScore + a.intentScore * 0.65)
        );
      }
      if (sortBy === "match") return b.matchScore - a.matchScore;
      if (sortBy === "intent") return b.intentScore - a.intentScore;
      if (sortBy === "salary")
        return (
          (a.salaryExpectation?.max ?? 0) - (b.salaryExpectation?.max ?? 0)
        );
      return Date.parse(b.lastActiveAtIso) - Date.parse(a.lastActiveAtIso);
    });
  })();

  const selectedCandidate = useMemo(() => {
    return (
      filteredCandidates.find(
        (candidate) => candidate.id === selectedCandidateId,
      ) ??
      filteredCandidates[0] ??
      candidatesWithStage[0]
    );
  }, [candidatesWithStage, filteredCandidates, selectedCandidateId]);

  const candidateTagsById = useMemo(() => {
    return candidatesWithStage.reduce<Record<number, string[]>>(
      (acc, candidate) => {
        acc[candidate.id] = candidateWorkflow[candidate.id]?.tags ?? [];
        return acc;
      },
      {},
    );
  }, [candidateWorkflow, candidatesWithStage]);

  const candidateNoteCountsById = useMemo(() => {
    return candidatesWithStage.reduce<Record<number, number>>(
      (acc, candidate) => {
        acc[candidate.id] = candidateWorkflow[candidate.id]?.notes.length ?? 0;
        return acc;
      },
      {},
    );
  }, [candidateWorkflow, candidatesWithStage]);

  const insights = (() => {
    const all = candidatesWithStage;
    const highMatch = all.filter(
      (candidate) => candidate.matchScore >= 85,
    ).length;
    const immediate = all.filter(
      (candidate) =>
        candidate.availability === "immediate" ||
        candidate.availability === "two_weeks",
    ).length;
    const activeToday = all.filter((candidate) =>
      includesText(candidate.lastActiveAt, talentCopy.labels.today, localeCode),
    ).length;
    const radarSourced = all.filter(
      (candidate) => candidate.source === "talent_radar",
    ).length;
    const avgMatch = Math.round(
      all.reduce((total, candidate) => total + candidate.matchScore, 0) /
        Math.max(all.length, 1),
    );

    return { highMatch, immediate, activeToday, radarSourced, avgMatch };
  })();

  const activeFilters = [
    query ? `${talentCopy.filters.active.search}: ${query}` : null,
    selectedJobMeta
      ? `${talentCopy.filters.active.role}: ${selectedJobMeta.title}`
      : null,
    selectedStatus !== "all"
      ? `${talentCopy.filters.active.status}: ${labels.status[selectedStatus as EmployerCandidateStatus]}`
      : null,
    selectedSource !== "all"
      ? `${talentCopy.filters.active.source}: ${labels.source[selectedSource as EmployerCandidateOpportunity["source"]]}`
      : null,
    selectedAvailability !== "all"
      ? `${talentCopy.filters.active.availability}: ${labels.availability[selectedAvailability as EmployerCandidateOpportunity["availability"]]}`
      : null,
    minScore > 0 ? `${talentCopy.filters.active.score} ≥ ${minScore}` : null,
  ].filter(Boolean) as string[];

  const clearFilters = () => {
    setQuery("");
    setSelectedJob("all");
    setSelectedStatus("all");
    setSelectedSource("all");
    setSelectedAvailability("all");
    setMinScore(70);
    setSortBy("recommended");
  };

  const applyPreset = (presetId: string) => {
    if (presetId === "hot") {
      setMinScore(85);
      setSelectedAvailability("all");
      setSelectedSource("all");
      setSortBy("recommended");
    }
    if (presetId === "fast") {
      setSelectedAvailability("immediate");
      setMinScore(70);
      setSortBy("intent");
    }
    if (presetId === "salary") {
      setMinScore(75);
      setSelectedSource("all");
      setQuery("");
      setSortBy("salary");
    }
    if (presetId === "radar") {
      setSelectedSource("talent_radar");
      setMinScore(70);
      setSortBy("recommended");
    }
  };

  return (
    <div className="space-y-6">
      <TalentHero
        query={query}
        setQuery={setQuery}
        insights={insights}
        resultCount={filteredCandidates.length}
        totalCount={candidatesWithStage.length}
        locale={locale}
        copy={talentCopy}
      />

      <TalentInsightStrip insights={insights} copy={talentCopy} />

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_392px]">
        <div className="space-y-4">
          <SurfaceCard
            variant="elevated"
            padding="none"
            className="overflow-hidden"
          >
            <div className="border-b border-border/80 p-4 sm:p-5">
              <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge tone="ai">
                      {talentCopy.center.badgeRadar}
                    </StatusBadge>
                    <StatusBadge tone="info">
                      {talentCopy.center.badgeExplainable}
                    </StatusBadge>
                    <StatusBadge tone="success">
                      {filteredCandidates.length} {talentCopy.labels.candidates}
                    </StatusBadge>
                  </div>
                  <h2 className="mt-3 text-xl font-black tracking-[-0.03em] text-foreground sm:text-2xl">
                    {talentCopy.center.title}
                  </h2>
                  <p className="mt-1 max-w-3xl text-sm leading-6 text-muted-foreground">
                    {talentCopy.center.description}
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <Button variant="secondary" size="sm" className="gap-2">
                    <Upload className="size-4" />
                    {talentCopy.center.importCv}
                  </Button>
                  <Button
                    variant="soft"
                    size="sm"
                    className="gap-2"
                    onClick={() => setView("outreach")}
                  >
                    <MailPlus className="size-4" />
                    {talentCopy.center.campaign}
                  </Button>
                  <Button size="sm" className="gap-2">
                    <Sparkles className="size-4" />
                    {talentCopy.center.aiShortlist}
                  </Button>
                </div>
              </div>
            </div>

            <div className="border-b border-border/70 bg-surface-muted/35 p-3 sm:p-4">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div className="flex flex-wrap items-center gap-2">
                  <ViewToggle view={view} setView={setView} copy={talentCopy} />
                  <button
                    type="button"
                    className="inline-flex h-10 items-center gap-2 rounded-2xl border border-border bg-surface px-3 text-sm font-bold text-foreground transition hover:border-primary/35 hover:bg-surface-strong lg:hidden"
                    onClick={() => setMobileFiltersOpen((value) => !value)}
                  >
                    <SlidersHorizontal className="size-4" />
                    {talentCopy.center.filters}
                    <ChevronDown
                      className={cn(
                        "size-4 transition",
                        mobileFiltersOpen && "rotate-180",
                      )}
                    />
                  </button>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <select
                    value={sortBy}
                    onChange={(event) =>
                      setSortBy(event.target.value as TalentSort)
                    }
                    className="h-10 rounded-2xl border border-border bg-surface px-3 text-sm font-bold text-foreground outline-none transition focus:ring-4 focus:ring-[var(--ring)]"
                    aria-label={talentCopy.center.sortLabel}
                  >
                    <option value="recommended">
                      {talentCopy.center.sort.recommended}
                    </option>
                    <option value="match">
                      {talentCopy.center.sort.match}
                    </option>
                    <option value="intent">
                      {talentCopy.center.sort.intent}
                    </option>
                    <option value="recent">
                      {talentCopy.center.sort.recent}
                    </option>
                    <option value="salary">
                      {talentCopy.center.sort.salary}
                    </option>
                  </select>
                  <Button variant="ghost" size="sm" className="gap-2">
                    <Download className="size-4" />
                    {talentCopy.center.export}
                  </Button>
                </div>
              </div>
            </div>

            <div className="grid min-h-[720px] lg:grid-cols-[300px_minmax(0,1fr)]">
              <aside
                className={cn(
                  "border-b border-border/70 bg-surface-muted/20 p-4 lg:block lg:border-b-0 lg:border-r",
                  !mobileFiltersOpen && "hidden",
                )}
              >
                <TalentFilters
                  selectedJob={selectedJob}
                  setSelectedJob={setSelectedJob}
                  selectedStatus={selectedStatus}
                  setSelectedStatus={setSelectedStatus}
                  selectedSource={selectedSource}
                  setSelectedSource={setSelectedSource}
                  selectedAvailability={selectedAvailability}
                  setSelectedAvailability={setSelectedAvailability}
                  minScore={minScore}
                  setMinScore={setMinScore}
                  activeFilters={activeFilters}
                  clearFilters={clearFilters}
                  applyPreset={applyPreset}
                  copy={talentCopy}
                  labels={labels}
                />
              </aside>

              <main className="min-w-0 p-4 sm:p-5">
                {activeFilters.length > 0 && (
                  <div className="mb-4 flex flex-wrap items-center gap-2">
                    {activeFilters.map((filter) => (
                      <span
                        key={filter}
                        className="inline-flex items-center gap-2 rounded-full border border-border bg-surface-muted px-3 py-1.5 text-xs font-bold text-muted-foreground"
                      >
                        {filter}
                      </span>
                    ))}
                    <button
                      type="button"
                      onClick={clearFilters}
                      className="text-xs font-bold text-primary hover:underline"
                    >
                      {talentCopy.center.clearAll}
                    </button>
                  </div>
                )}

                {view === "outreach" ? (
                  <OutreachCampaignPanel
                    candidates={filteredCandidates}
                    selectedCandidateId={selectedCandidate?.id}
                    onSelect={setSelectedCandidateId}
                    onOpenProfile={(candidateId) => {
                      setSelectedCandidateId(candidateId);
                      setCandidate360Open(true);
                    }}
                    onTagCandidates={addTagsToCandidates}
                    onNoteCandidates={addNotesToCandidates}
                    onCreateCampaign={createOutreachCampaignDraft}
                    campaignDrafts={campaignDrafts}
                    syncState={workflowSyncState}
                    locale={locale}
                  />
                ) : view === "pipeline" ? (
                  <PipelineKanbanBoard
                    candidates={filteredCandidates}
                    onSelect={setSelectedCandidateId}
                    selectedCandidateId={selectedCandidate?.id}
                    onOpenCandidate={(candidateId) => {
                      setSelectedCandidateId(candidateId);
                      setCandidate360Open(true);
                    }}
                    onMoveCandidate={moveCandidateToStage}
                    onBulkMove={bulkMoveCandidatesToStage}
                    candidateTags={candidateTagsById}
                    candidateNoteCounts={candidateNoteCountsById}
                    onBulkTag={addTagsToCandidates}
                    onBulkNote={addNotesToCandidates}
                    locale={locale}
                  />
                ) : view === "compare" ? (
                  <TalentCompare
                    candidates={filteredCandidates.slice(0, 4)}
                    onSelect={setSelectedCandidateId}
                    onOpenProfile={(candidateId) => {
                      setSelectedCandidateId(candidateId);
                      setCandidate360Open(true);
                    }}
                    locale={locale}
                  />
                ) : filteredCandidates.length > 0 ? (
                  <div className="grid gap-3 2xl:grid-cols-2">
                    {filteredCandidates.map((candidate) => (
                      <CandidateIntelligenceCard
                        key={candidate.id}
                        candidate={candidate}
                        selected={selectedCandidate?.id === candidate.id}
                        onSelect={() => setSelectedCandidateId(candidate.id)}
                        onOpenProfile={() => {
                          setSelectedCandidateId(candidate.id);
                          setCandidate360Open(true);
                        }}
                        locale={locale}
                        tags={candidateTagsById[candidate.id] ?? []}
                        noteCount={candidateNoteCountsById[candidate.id] ?? 0}
                        copy={talentCopy}
                        labels={labels}
                      />
                    ))}
                  </div>
                ) : (
                  <EmptyState
                    icon={Search}
                    title={talentCopy.center.noResultsTitle}
                    description={talentCopy.center.noResultsDesc}
                    action={{
                      label: talentCopy.center.resetFilters,
                      onClick: clearFilters,
                    }}
                    className="min-h-[420px]"
                  />
                )}
              </main>
            </div>
          </SurfaceCard>
        </div>

        <CandidateDetailPanel
          candidate={selectedCandidate}
          locale={locale}
          workflow={
            selectedCandidate
              ? candidateWorkflow[selectedCandidate.id]
              : undefined
          }
          copy={talentCopy}
          labels={labels}
          onOpenDrawer={() => setCandidate360Open(true)}
          onAddTag={(tag) =>
            selectedCandidate &&
            addTagsToCandidates([selectedCandidate.id], tag)
          }
          onRemoveTag={(tag) =>
            selectedCandidate &&
            removeTagFromCandidate(selectedCandidate.id, tag)
          }
          onAddNote={(note) =>
            selectedCandidate &&
            addNotesToCandidates([selectedCandidate.id], note)
          }
          onShortlist={() =>
            selectedCandidate &&
            moveCandidateToStage(selectedCandidate.id, "shortlisted")
          }
          onArchive={() =>
            selectedCandidate &&
            moveCandidateToStage(selectedCandidate.id, "rejected")
          }
        />
      </div>

      <Candidate360Drawer
        candidate={selectedCandidate}
        locale={locale}
        open={candidate360Open}
        onClose={() => setCandidate360Open(false)}
      />
    </div>
  );
}

function TalentHero({
  query,
  setQuery,
  insights,
  resultCount,
  totalCount,
  locale,
  copy,
}: {
  query: string;
  setQuery: (value: string) => void;
  insights: {
    highMatch: number;
    immediate: number;
    activeToday: number;
    radarSourced: number;
    avgMatch: number;
  };
  resultCount: number;
  totalCount: number;
  locale: string;
  copy: TalentCopy;
}) {
  return (
    <SurfaceCard
      variant="accent"
      padding="none"
      className="relative overflow-hidden"
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(56,189,248,0.18),transparent_34%),radial-gradient(circle_at_78%_0%,rgba(99,102,241,0.18),transparent_28%)]" />
      <div className="relative grid gap-6 p-5 sm:p-6 xl:grid-cols-[minmax(0,1fr)_360px] xl:p-7">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge tone="ai" icon={<Command className="size-3.5" />}>
              {copy.hero.badge}
            </StatusBadge>
            <StatusBadge
              tone="success"
              icon={<ShieldCheck className="size-3.5" />}
            >
              {copy.hero.decisionFlow}
            </StatusBadge>
          </div>

          <h1 className="mt-4 max-w-4xl text-3xl font-black tracking-[-0.045em] text-foreground sm:text-4xl xl:text-5xl">
            {copy.hero.title}
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-muted-foreground sm:text-base">
            {copy.hero.description}
          </p>

          <div className="mt-5 rounded-[26px] border border-primary/20 bg-surface/90 p-2 shadow-[0_22px_80px_rgba(15,23,42,0.12)] backdrop-blur-xl">
            <div className="flex flex-col gap-2 lg:flex-row lg:items-center">
              <div className="relative flex-1">
                <Sparkles className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-primary" />
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder={copy.hero.searchPlaceholder}
                  className="h-13 w-full rounded-[22px] border border-transparent bg-surface-muted pl-12 pr-4 text-sm font-semibold text-foreground outline-none transition placeholder:text-muted-foreground focus:border-primary/30 focus:bg-surface focus:ring-4 focus:ring-[var(--ring)]"
                />
              </div>
              <Button className="h-13 shrink-0 gap-2 rounded-[22px] px-5">
                <WandSparkles className="size-4" />
                {locale === "tr"
                  ? `${copy.center.views.radar} ara`
                  : `Search ${copy.center.views.radar}`}
              </Button>
            </div>
            <div className="mt-2 flex flex-wrap gap-2 px-1 pb-1">
              {copy.hero.smartQueries.map((smartQuery) => (
                <button
                  key={smartQuery}
                  type="button"
                  onClick={() => setQuery(smartQuery)}
                  className="rounded-full border border-border bg-surface px-3 py-1.5 text-left text-[11px] font-bold text-muted-foreground transition hover:border-primary/35 hover:text-foreground"
                >
                  {smartQuery}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="rounded-[28px] border border-border/80 bg-surface/80 p-5 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur-xl">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.18em] text-muted-foreground">
                {locale === "tr"
                  ? `${copy.center.badgeRadar} özeti`
                  : `${copy.center.badgeRadar} summary`}
              </p>
              <p className="mt-2 text-3xl font-black tracking-[-0.04em] text-foreground">
                {resultCount}/{totalCount}
              </p>
              <p className="text-sm text-muted-foreground">
                {copy.hero.resultSummary(resultCount, totalCount)}
              </p>
            </div>
            <div className="flex size-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <Radar className="size-6" />
            </div>
          </div>

          <div className="mt-5 space-y-3">
            <RadarStat
              label={copy.insight.highScore}
              value={insights.highMatch}
              helper={`85+ ${copy.labels.match.toLocaleLowerCase(locale === "tr" ? "tr-TR" : "en-US")}`}
            />
            <RadarStat
              label={copy.insight.fastAvailable}
              value={insights.immediate}
              helper={copy.insight.withinTwoWeeks}
            />
            <RadarStat
              label={copy.labels.today}
              value={insights.activeToday}
              helper={copy.insight.waitingAction}
            />
          </div>

          <Link
            href={`/${locale}/employer/matches`}
            className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-2xl border border-primary/20 bg-primary/10 px-4 py-3 text-sm font-black text-primary transition hover:bg-primary/15"
          >
            {copy.hero.openMatchCenter}
            <ArrowRight className="size-4" />
          </Link>
        </div>
      </div>
    </SurfaceCard>
  );
}

function RadarStat({
  label,
  value,
  helper,
}: {
  label: string;
  value: number;
  helper: string;
}) {
  return (
    <div className="flex items-center justify-between rounded-2xl border border-border/70 bg-surface-muted/55 px-4 py-3">
      <div>
        <p className="text-sm font-black text-foreground">{label}</p>
        <p className="text-xs font-semibold text-muted-foreground">{helper}</p>
      </div>
      <span className="text-2xl font-black tracking-[-0.04em] text-foreground">
        {value}
      </span>
    </div>
  );
}

function TalentInsightStrip({
  insights,
  copy,
}: {
  insights: {
    highMatch: number;
    immediate: number;
    activeToday: number;
    radarSourced: number;
    avgMatch: number;
  };
  copy: TalentCopy;
}) {
  const cards = [
    {
      label: copy.insight.avgMatch,
      value: insights.avgMatch,
      suffix: "/100",
      icon: Target,
      tone: "text-primary",
      helper: copy.insight.poolQuality,
    },
    {
      label: copy.insight.highScore,
      value: insights.highMatch,
      suffix: "",
      icon: Star,
      tone: "text-success",
      helper: copy.insight.waitingAction,
    },
    {
      label: copy.insight.fastAvailable,
      value: insights.immediate,
      suffix: "",
      icon: CalendarClock,
      tone: "text-blue-500",
      helper: copy.insight.withinTwoWeeks,
    },
    {
      label: copy.insight.radarSourced,
      value: insights.radarSourced,
      suffix: "",
      icon: Radar,
      tone: "text-warning",
      helper: copy.insight.passiveSourcing,
    },
  ];

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <SurfaceCard
            key={card.label}
            variant="interactive"
            padding="sm"
            className="flex items-center gap-4"
          >
            <div
              className={cn(
                "flex size-12 shrink-0 items-center justify-center rounded-2xl bg-surface-muted",
                card.tone,
              )}
            >
              <Icon className="size-5" />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">
                {card.label}
              </p>
              <p className="mt-1 text-2xl font-black tracking-[-0.04em] text-foreground">
                {card.value}
                <span className="text-sm text-muted-foreground">
                  {card.suffix}
                </span>
              </p>
              <p className="text-xs font-semibold text-muted-foreground">
                {card.helper}
              </p>
            </div>
          </SurfaceCard>
        );
      })}
    </div>
  );
}

function ViewToggle({
  view,
  setView,
  copy,
}: {
  view: TalentView;
  setView: (view: TalentView) => void;
  copy: TalentCopy;
}) {
  const items: Array<{
    id: TalentView;
    label: string;
    icon: typeof LayoutGrid;
  }> = [
    { id: "radar", label: copy.center.views.radar, icon: LayoutGrid },
    { id: "pipeline", label: copy.center.views.pipeline, icon: ListChecks },
    { id: "compare", label: copy.center.views.compare, icon: BarChart3 },
    { id: "outreach", label: copy.center.views.outreach, icon: MailPlus },
  ];

  return (
    <div className="inline-flex rounded-2xl border border-border bg-surface p-1">
      {items.map((item) => {
        const Icon = item.icon;
        const selected = view === item.id;
        return (
          <button
            key={item.id}
            type="button"
            onClick={() => setView(item.id)}
            className={cn(
              "inline-flex h-9 items-center gap-2 rounded-xl px-3 text-xs font-black transition",
              selected
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:bg-surface-muted hover:text-foreground",
            )}
          >
            <Icon className="size-3.5" />
            {item.label}
          </button>
        );
      })}
    </div>
  );
}

function TalentFilters({
  selectedJob,
  setSelectedJob,
  selectedStatus,
  setSelectedStatus,
  selectedSource,
  setSelectedSource,
  selectedAvailability,
  setSelectedAvailability,
  minScore,
  setMinScore,
  activeFilters,
  clearFilters,
  applyPreset,
  copy,
  labels,
}: {
  selectedJob: string;
  setSelectedJob: (value: string) => void;
  selectedStatus: string;
  setSelectedStatus: (value: string) => void;
  selectedSource: string;
  setSelectedSource: (value: string) => void;
  selectedAvailability: string;
  setSelectedAvailability: (value: string) => void;
  minScore: number;
  setMinScore: (value: number) => void;
  activeFilters: string[];
  clearFilters: () => void;
  applyPreset: (presetId: string) => void;
  copy: TalentCopy;
  labels: LocalizedTalentLabels;
}) {
  const presetIconById = {
    hot: Zap,
    fast: Clock3,
    salary: BadgeCheck,
    radar: Radar,
  } as const;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-black text-foreground">
            {copy.filters.title}
          </p>
          <p className="text-xs font-semibold text-muted-foreground">
            {copy.filters.activeSignals(activeFilters.length)}
          </p>
        </div>
        <button
          type="button"
          onClick={clearFilters}
          className="rounded-full p-2 text-muted-foreground transition hover:bg-surface-muted hover:text-foreground"
          aria-label={copy.filters.clear}
        >
          <X className="size-4" />
        </button>
      </div>

      <div className="space-y-2">
        {copy.filters.presets.map((preset) => {
          const Icon =
            presetIconById[preset.id as keyof typeof presetIconById] ?? Zap;
          return (
            <button
              key={preset.id}
              type="button"
              onClick={() => applyPreset(preset.id)}
              className="group w-full rounded-2xl border border-border bg-surface p-3 text-left transition hover:border-primary/30 hover:bg-surface-strong"
            >
              <span className="flex items-start gap-3">
                <span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary transition group-hover:bg-primary group-hover:text-primary-foreground">
                  <Icon className="size-4" />
                </span>
                <span className="min-w-0">
                  <span className="block text-sm font-black text-foreground">
                    {preset.label}
                  </span>
                  <span className="block text-xs font-semibold leading-5 text-muted-foreground">
                    {preset.description}
                  </span>
                </span>
              </span>
            </button>
          );
        })}
      </div>

      <FilterSelect
        label={copy.filters.roleFocus}
        value={selectedJob}
        onChange={setSelectedJob}
        icon={<Briefcase className="size-4" />}
      >
        <option value="all">{copy.filters.allRoles}</option>
        {employerJobsMock
          .filter((job) => job.status !== "closed")
          .map((job) => (
            <option key={job.id} value={String(job.id)}>
              {job.title}
            </option>
          ))}
      </FilterSelect>

      <FilterSelect
        label={copy.filters.status}
        value={selectedStatus}
        onChange={setSelectedStatus}
        icon={<ClipboardCheck className="size-4" />}
      >
        <option value="all">{copy.filters.allStatuses}</option>
        {Object.entries(labels.status).map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </FilterSelect>

      <FilterSelect
        label={copy.filters.source}
        value={selectedSource}
        onChange={setSelectedSource}
        icon={<LocateFixed className="size-4" />}
      >
        <option value="all">{copy.filters.allSources}</option>
        {Object.entries(labels.source).map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </FilterSelect>

      <FilterSelect
        label={copy.filters.availability}
        value={selectedAvailability}
        onChange={setSelectedAvailability}
        icon={<CalendarClock className="size-4" />}
      >
        <option value="all">{copy.filters.allAvailabilities}</option>
        {Object.entries(labels.availability).map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </FilterSelect>

      <div className="rounded-2xl border border-border bg-surface p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-sm font-black text-foreground">
              {copy.filters.minMatch}
            </p>
            <p className="text-xs font-semibold text-muted-foreground">
              {copy.filters.qualityThreshold}
            </p>
          </div>
          <ScoreBadge score={minScore} label="Min" size="sm" />
        </div>
        <input
          type="range"
          min="0"
          max="100"
          step="5"
          value={minScore}
          onChange={(event) => setMinScore(Number(event.target.value))}
          className="mt-4 w-full accent-[var(--primary)]"
          aria-label={copy.filters.minMatch}
        />
        <div className="mt-2 flex justify-between text-[10px] font-bold uppercase tracking-[0.12em] text-muted-foreground">
          <span>{copy.filters.broad}</span>
          <span>{copy.filters.selective}</span>
        </div>
      </div>
    </div>
  );
}

function FilterSelect({
  label,
  value,
  onChange,
  icon,
  children,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <label className="block rounded-2xl border border-border bg-surface p-3">
      <span className="mb-2 flex items-center gap-2 text-xs font-black uppercase tracking-[0.14em] text-muted-foreground">
        {icon}
        {label}
      </span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-10 w-full rounded-xl border border-border bg-surface-muted px-3 text-sm font-bold text-foreground outline-none transition focus:ring-4 focus:ring-[var(--ring)]"
      >
        {children}
      </select>
    </label>
  );
}

function CandidateIntelligenceCard({
  candidate,
  selected,
  onSelect,
  onOpenProfile,
  locale,
  tags,
  noteCount,
  copy,
  labels,
}: {
  candidate: EmployerCandidateOpportunity;
  selected: boolean;
  onSelect: () => void;
  onOpenProfile: () => void;
  locale: string;
  tags: string[];
  noteCount: number;
  copy: TalentCopy;
  labels: LocalizedTalentLabels;
}) {
  const matchedSkills = candidate.skills
    .filter((skill) => skill.matched)
    .slice(0, 4);
  const firstRisk = candidate.risks[0];

  return (
    <article
      onClick={onSelect}
      className={cn(
        "group w-full rounded-[26px] border bg-surface p-4 text-left shadow-[0_18px_60px_rgba(15,23,42,0.08)] transition focus-within:ring-4 focus-within:ring-[var(--ring)]",
        selected
          ? "border-primary/55 ring-4 ring-[var(--ring)]"
          : "border-border hover:-translate-y-0.5 hover:border-primary/30 hover:bg-surface-strong",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          <div className="relative flex size-12 shrink-0 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,var(--primary),var(--accent))] text-sm font-black text-primary-foreground shadow-lg">
            {candidate.initials}
            <span className="absolute -right-1 -top-1 flex size-4 rounded-full border-2 border-surface bg-success" />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="truncate text-base font-black tracking-[-0.02em] text-foreground">
                {candidate.name}
              </h3>
              <StatusBadge
                tone={getStatusTone(candidate.status)}
                className="py-0.5 text-[10px]"
              >
                {labels.status[candidate.status]}
              </StatusBadge>
            </div>
            <p className="mt-1 line-clamp-1 text-sm font-semibold text-muted-foreground">
              {candidate.headline}
            </p>
            <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-semibold text-muted-foreground">
              <span className="inline-flex items-center gap-1">
                <MapPin className="size-3.5" />
                {candidate.location}
              </span>
              <span className="inline-flex items-center gap-1">
                <Briefcase className="size-3.5" />
                {candidate.experience} {copy.labels.years}
              </span>
              <span className="inline-flex items-center gap-1">
                <Activity className="size-3.5" />
                {candidate.lastActiveAt}
              </span>
            </div>
          </div>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-2">
          <ScoreBadge
            score={candidate.matchScore}
            label={copy.labels.match}
            size="sm"
          />
          <span className="rounded-full border border-blue-500/20 bg-blue-500/10 px-2.5 py-1 text-[11px] font-black text-blue-500">
            {copy.labels.intent} {candidate.intentScore}
          </span>
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <SignalPill
          icon={<CalendarClock className="size-3.5" />}
          label={copy.card.availability}
          value={labels.availability[candidate.availability]}
          tone={getAvailabilityTone(candidate.availability)}
        />
        <SignalPill
          icon={<MousePointer2 className="size-3.5" />}
          label={copy.card.source}
          value={labels.source[candidate.source]}
          tone={candidate.source === "talent_radar" ? "info" : "neutral"}
        />
        <SignalPill
          icon={<BadgeCheck className="size-3.5" />}
          label={copy.card.salary}
          value={formatSalary(candidate, copy)}
          tone="neutral"
        />
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {matchedSkills.map((skill) => (
          <span
            key={skill.name}
            className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-[11px] font-black text-success"
          >
            {skill.name}
          </span>
        ))}
        {candidate.skills.length > matchedSkills.length && (
          <span className="rounded-full border border-border bg-surface-muted px-2.5 py-1 text-[11px] font-bold text-muted-foreground">
            {copy.card.moreSkills(
              candidate.skills.length - matchedSkills.length,
            )}
          </span>
        )}
      </div>

      {(tags.length > 0 || noteCount > 0) && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-[11px] font-black text-primary"
            >
              #{tag}
            </span>
          ))}
          {tags.length > 3 && (
            <span className="rounded-full border border-border bg-surface-muted px-2.5 py-1 text-[11px] font-bold text-muted-foreground">
              {copy.card.moreTags(tags.length - 3)}
            </span>
          )}
          {noteCount > 0 && (
            <span className="rounded-full border border-border bg-surface-muted px-2.5 py-1 text-[11px] font-bold text-muted-foreground">
              {copy.card.noteCount(noteCount)}
            </span>
          )}
        </div>
      )}

      <div className="mt-4 rounded-2xl border border-border bg-surface-muted/55 p-3">
        <div className="flex items-start gap-2">
          <Sparkles className="mt-0.5 size-4 shrink-0 text-primary" />
          <div className="min-w-0">
            <p className="text-xs font-black uppercase tracking-[0.14em] text-primary">
              {copy.card.aiSuggestion}
            </p>
            <p className="mt-1 text-sm font-semibold leading-6 text-foreground">
              {candidate.recommendedAction}
            </p>
            {firstRisk && (
              <p className="mt-1 text-xs font-semibold leading-5 text-muted-foreground">
                {copy.card.risk}: {firstRisk}
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-border/70 pt-3">
        <p className="min-w-0 flex-1 text-xs font-semibold text-muted-foreground line-clamp-1">
          {candidate.highlights[0]}
        </p>
        <div className="flex shrink-0 items-center gap-2">
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              onOpenProfile();
            }}
            className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/10 px-3 py-1.5 text-xs font-black text-primary transition hover:bg-primary/15 focus:outline-none focus:ring-4 focus:ring-[var(--ring)]"
          >
            {copy.card.inspect360}
            <PanelRightOpen className="size-3.5" />
          </button>
          <Link
            href={`/${locale}/employer/candidates/${candidate.id}`}
            onClick={(event) => event.stopPropagation()}
            className="inline-flex items-center gap-1.5 text-xs font-black text-primary hover:underline focus:outline-none focus:ring-4 focus:ring-[var(--ring)]"
          >
            {copy.card.profile}
            <ArrowRight className="size-3.5" />
          </Link>
        </div>
      </div>
    </article>
  );
}

function SignalPill({
  icon,
  label,
  value,
  tone,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  tone: "success" | "warning" | "info" | "neutral";
}) {
  const toneClass = {
    success: "border-emerald-500/20 bg-emerald-500/10 text-success",
    warning: "border-amber-500/20 bg-amber-500/10 text-warning",
    info: "border-blue-500/20 bg-blue-500/10 text-blue-500",
    neutral: "border-border bg-surface-muted text-muted-foreground",
  }[tone];

  return (
    <div className={cn("rounded-2xl border px-3 py-2", toneClass)}>
      <p className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-[0.12em] opacity-80">
        {icon}
        {label}
      </p>
      <p className="mt-1 truncate text-xs font-black text-foreground">
        {value}
      </p>
    </div>
  );
}

function CandidateDetailPanel({
  candidate,
  locale,
  workflow,
  copy,
  labels,
  onOpenDrawer,
  onAddTag,
  onRemoveTag,
  onAddNote,
  onArchive,
  onShortlist,
}: {
  candidate?: EmployerCandidateOpportunity;
  locale: string;
  workflow?: CandidateWorkflowState;
  copy: TalentCopy;
  labels: LocalizedTalentLabels;
  onOpenDrawer: () => void;
  onAddTag: (tag: string) => void;
  onRemoveTag: (tag: string) => void;
  onAddNote: (note: string) => void;
  onArchive: () => void;
  onShortlist: () => void;
}) {
  if (!candidate) {
    return (
      <SurfaceCard variant="muted" padding="lg" className="hidden xl:block">
        <EmptyState
          icon={PanelRightOpen}
          title={copy.detail.selectCandidateTitle}
          description={copy.detail.selectCandidateDesc}
        />
      </SurfaceCard>
    );
  }

  const positiveSignals = candidate.highlights.slice(0, 4);
  const riskSignals = candidate.risks.slice(0, 3);

  return (
    <aside className="space-y-4 xl:sticky xl:top-24 xl:self-start">
      <SurfaceCard
        variant="elevated"
        padding="none"
        className="overflow-hidden"
      >
        <div className="relative bg-[linear-gradient(135deg,rgba(99,102,241,0.18),rgba(56,189,248,0.12))] p-5">
          <div className="absolute right-4 top-4 flex gap-2">
            <button
              type="button"
              onClick={onOpenDrawer}
              className="rounded-full border border-border/80 bg-surface/80 p-2 text-muted-foreground transition hover:text-foreground focus:outline-none focus:ring-4 focus:ring-[var(--ring)]"
              aria-label={copy.detail.open360}
            >
              <Eye className="size-4" />
            </button>
            <button
              className="rounded-full border border-border/80 bg-surface/80 p-2 text-muted-foreground transition hover:text-foreground"
              aria-label={copy.detail.more}
            >
              <MoreHorizontal className="size-4" />
            </button>
          </div>
          <div className="flex size-16 items-center justify-center rounded-[24px] bg-[linear-gradient(135deg,var(--primary),var(--accent))] text-xl font-black text-primary-foreground shadow-lg">
            {candidate.initials}
          </div>
          <h2 className="mt-4 text-2xl font-black tracking-[-0.04em] text-foreground">
            {candidate.name}
          </h2>
          <p className="mt-1 text-sm font-semibold text-muted-foreground">
            {candidate.headline}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <ScoreBadge
              score={candidate.matchScore}
              label={copy.labels.match}
            />
            <ScoreBadge
              score={candidate.intentScore}
              label={copy.labels.intent}
            />
          </div>
        </div>

        <div className="p-5">
          <div className="grid grid-cols-2 gap-3">
            <MiniProfileMetric
              icon={<MapPin className="size-4" />}
              label={copy.detail.location}
              value={candidate.location}
            />
            <MiniProfileMetric
              icon={<Briefcase className="size-4" />}
              label={copy.detail.experience}
              value={`${candidate.experience} ${copy.labels.years}`}
            />
            <MiniProfileMetric
              icon={<CalendarClock className="size-4" />}
              label={copy.card.availability}
              value={labels.availability[candidate.availability]}
            />
            <MiniProfileMetric
              icon={<BadgeCheck className="size-4" />}
              label={copy.card.salary}
              value={formatSalary(candidate, copy)}
            />
          </div>

          <div className="mt-5 rounded-2xl border border-primary/20 bg-primary/10 p-4">
            <div className="flex items-start gap-3">
              <Sparkles className="mt-0.5 size-5 shrink-0 text-primary" />
              <div>
                <p className="text-xs font-black uppercase tracking-[0.16em] text-primary">
                  {copy.detail.nextBestAction}
                </p>
                <p className="mt-1 text-sm font-bold leading-6 text-foreground">
                  {candidate.recommendedAction}
                </p>
              </div>
            </div>
          </div>

          <div className="mt-5 space-y-4">
            <EvidenceBlock
              title={copy.detail.positiveSignals}
              tone="success"
              items={positiveSignals}
              icon={<CheckCircle2 className="size-4" />}
            />
            <EvidenceBlock
              title={copy.detail.risksToVerify}
              tone="warning"
              items={riskSignals}
              icon={<BellRing className="size-4" />}
            />
          </div>

          <div className="mt-5">
            <p className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">
              {copy.detail.skillEvidence}
            </p>
            <div className="mt-3 space-y-2">
              {candidate.skills.slice(0, 5).map((skill) => (
                <div
                  key={skill.name}
                  className="rounded-2xl border border-border bg-surface-muted/60 p-3"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-black text-foreground">
                        {skill.name}
                      </p>
                      <p className="text-xs font-semibold text-muted-foreground">
                        {skill.level ?? copy.detail.intermediate} ·{" "}
                        {skill.years ?? 1} {copy.labels.years}
                      </p>
                    </div>
                    <StatusBadge
                      tone={skill.matched ? "success" : "neutral"}
                      className="text-[10px]"
                    >
                      {skill.matched ? copy.detail.matched : copy.detail.extra}
                    </StatusBadge>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-5 grid gap-2 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
            <Button className="gap-2" onClick={onOpenDrawer}>
              <PanelRightOpen className="size-4" /> {copy.detail.candidate360}
            </Button>
            <Button variant="secondary" className="gap-2">
              <CalendarClock className="size-4" />{" "}
              {copy.detail.scheduleInterview}
            </Button>
            <Button variant="soft" className="gap-2">
              <Star className="size-4" /> {copy.detail.shortlist}
            </Button>
            <Link
              href={`/${locale}/employer/candidates/${candidate.id}`}
              className="inline-flex min-h-10 items-center justify-center gap-2 rounded-2xl border border-border bg-surface-elevated px-4 py-2.5 text-sm font-bold text-foreground shadow-sm transition hover:border-primary/35 hover:bg-surface-strong focus:outline-none focus:ring-4 focus:ring-[var(--ring)]"
            >
              <MessageSquareText className="size-4" /> {copy.detail.fullProfile}
            </Link>
          </div>
        </div>
      </SurfaceCard>

      <CandidateWorkflowPanel
        candidate={candidate}
        tags={workflow?.tags ?? []}
        notes={workflow?.notes ?? []}
        onAddTag={onAddTag}
        onRemoveTag={onRemoveTag}
        onAddNote={onAddNote}
        onArchive={onArchive}
        onShortlist={onShortlist}
        locale={locale}
      />

      <SurfaceCard variant="muted" padding="md">
        <div className="flex items-start gap-3">
          <ShieldCheck className="mt-1 size-5 shrink-0 text-success" />
          <div>
            <p className="text-sm font-black text-foreground">
              {copy.detail.explainableTitle}
            </p>
            <p className="mt-1 text-xs font-semibold leading-5 text-muted-foreground">
              {copy.detail.explainableDesc}
            </p>
          </div>
        </div>
      </SurfaceCard>
    </aside>
  );
}

function MiniProfileMetric({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-border bg-surface-muted/65 p-3">
      <p className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-[0.13em] text-muted-foreground">
        {icon}
        {label}
      </p>
      <p className="mt-1 truncate text-sm font-black text-foreground">
        {value}
      </p>
    </div>
  );
}

function EvidenceBlock({
  title,
  items,
  icon,
  tone,
}: {
  title: string;
  items: string[];
  icon: React.ReactNode;
  tone: "success" | "warning";
}) {
  const toneClass =
    tone === "success"
      ? "text-success bg-emerald-500/10 border-emerald-500/20"
      : "text-warning bg-amber-500/10 border-amber-500/20";
  return (
    <div>
      <p className="mb-2 text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">
        {title}
      </p>
      <div className="space-y-2">
        {items.map((item) => (
          <div
            key={item}
            className={cn(
              "flex items-start gap-2 rounded-2xl border p-3 text-sm font-semibold leading-6",
              toneClass,
            )}
          >
            <span className="mt-1 shrink-0">{icon}</span>
            <span className="text-foreground">{item}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function TalentCompare({
  candidates,
  onSelect,
  onOpenProfile,
  locale,
}: {
  candidates: EmployerCandidateOpportunity[];
  onSelect: (id: number) => void;
  onOpenProfile?: (id: number) => void;
  locale: string;
}) {
  return (
    <CandidateComparisonMatrixV2
      candidates={candidates}
      onSelect={onSelect}
      onOpenProfile={onOpenProfile}
      locale={locale}
    />
  );
}
