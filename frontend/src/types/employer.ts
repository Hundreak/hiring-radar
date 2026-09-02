export type EmployerJobStatus = 'active' | 'paused' | 'closed' | 'draft';
export type EmployerCandidateStatus = 'new' | 'reviewed' | 'shortlisted' | 'interview' | 'offer' | 'hired' | 'rejected';
export type EmployerPriority = 'low' | 'medium' | 'high' | 'critical';
export type EmployerTrendDirection = 'up' | 'down' | 'flat';
export type EmployerRiskLevel = 'healthy' | 'watch' | 'risk' | 'critical';
export type EmployerInsightTone = 'info' | 'success' | 'warning' | 'danger' | 'ai';
export type EmployerWorkModel = 'office' | 'hybrid' | 'remote';
export type EmployerSeniority = 'junior' | 'mid' | 'senior' | 'lead' | 'principal';
export type EmployerSourceKey = 'direct' | 'linkedin' | 'referral' | 'job_board' | 'talent_radar' | 'agency' | 'other';

export interface EmployerMetric {
  id: string;
  label: string;
  value: string | number;
  unit?: string;
  helperText?: string;
  delta?: string;
  trend?: EmployerTrendDirection;
  positive?: boolean;
  icon: string;
}

export interface EmployerQuickAction {
  id: string;
  label: string;
  description: string;
  href: string;
  icon: string;
  tone: 'primary' | 'accent' | 'success' | 'warning';
}

export interface HiringHealthScore {
  score: number;
  label: string;
  trend: EmployerTrendDirection;
  change: string;
  summary: string;
  drivers: Array<{
    id: string;
    label: string;
    value: number;
    tone: EmployerInsightTone;
    description: string;
  }>;
}

export interface EmployerInsight {
  id: string;
  title: string;
  description: string;
  tone: EmployerInsightTone;
  priority: EmployerPriority;
  actionLabel?: string;
  actionHref?: string;
  evidence?: string[];
  createdAt: string;
}

export interface EmployerDashboardStats {
  metrics: EmployerMetric[];
  quickActions: EmployerQuickAction[];
  hiringHealth: HiringHealthScore;
  insights: EmployerInsight[];
}

export interface EmployerJobQualityFactor {
  id: string;
  label: string;
  score: number;
  status: EmployerRiskLevel;
  description: string;
  recommendation?: string;
}

export interface EmployerJobSummary {
  id: number;
  slug: string;
  title: string;
  department: string;
  location: string;
  workModel: EmployerWorkModel;
  status: EmployerJobStatus;
  seniority: EmployerSeniority;
  applicants: number;
  qualifiedApplicants: number;
  matchAvg: number;
  qualityScore: number;
  views: number;
  conversionRate: number;
  postedAt: string;
  postedAtIso: string;
  updatedAtIso: string;
  salaryRange?: {
    min: number;
    max: number;
    currency: 'TRY' | 'USD' | 'EUR';
    period: 'monthly' | 'yearly';
    visible: boolean;
  };
  riskLevel: EmployerRiskLevel;
  riskReasons: string[];
  qualityFactors: EmployerJobQualityFactor[];
  tags: string[];
}

export interface EmployerCandidateSkill {
  name: string;
  level?: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  years?: number;
  matched?: boolean;
}

export interface EmployerCandidateOpportunity {
  id: number;
  publicId: string;
  name: string;
  initials: string;
  headline: string;
  experience: number;
  location: string;
  workPreference: EmployerWorkModel | 'flexible';
  matchScore: number;
  intentScore: number;
  availability: 'immediate' | 'two_weeks' | 'one_month' | 'passive';
  status: EmployerCandidateStatus;
  appliedAt: string;
  appliedAtIso: string;
  lastActiveAt: string;
  lastActiveAtIso: string;
  education: string;
  skills: EmployerCandidateSkill[];
  targetRole?: string;
  salaryExpectation?: {
    min: number;
    max: number;
    currency: 'TRY' | 'USD' | 'EUR';
  };
  highlights: string[];
  risks: string[];
  source: EmployerSourceKey;
  recommendedAction: string;
}

export interface EmployerPipelineStage {
  id: string;
  label: string;
  description: string;
  count: number;
  targetDays: number;
  overdueCount: number;
  conversionRate?: number;
  tone: EmployerInsightTone;
}

export interface EmployerActivity {
  id: string;
  type: 'application' | 'match' | 'review' | 'job' | 'message' | 'interview' | 'system';
  title: string;
  description: string;
  time: string;
  timestamp: string;
  icon: string;
  tone: EmployerInsightTone;
  href?: string;
}

export interface EmployerAnalyticsMetric {
  id: string;
  label: string;
  value: number | string;
  change: string;
  positive: boolean;
  icon: string;
  description?: string;
}

export interface EmployerPositionPerformance {
  jobId: number;
  position: string;
  applicants: number;
  qualifiedApplicants: number;
  views: number;
  matchAvg: number;
  conversion: number;
  trend: EmployerTrendDirection;
  riskLevel: EmployerRiskLevel;
}

export interface EmployerSourceBreakdown {
  source: string;
  key: EmployerSourceKey;
  count: number;
  percentage: number;
  qualityScore: number;
}

export interface EmployerWeeklyApplicationPoint {
  day: string;
  count: number;
  qualified: number;
}

export interface EmployerAnalyticsSnapshot {
  period: '7d' | '30d' | '90d';
  metrics: EmployerAnalyticsMetric[];
  positionPerformance: EmployerPositionPerformance[];
  sourceBreakdown: EmployerSourceBreakdown[];
  weeklyApplications: EmployerWeeklyApplicationPoint[];
}

export interface EmployerMatchBreakdownItem {
  component: string;
  score: number;
  weight: number;
  evidence: string;
}

export interface EmployerCandidateMatch {
  id: number;
  candidateId: number;
  jobId: number;
  candidateName: string;
  candidateInitials: string;
  candidateHeadline: string;
  candidateExp: number;
  candidateLocation: string;
  candidateSkills: string[];
  jobTitle: string;
  jobDepartment: string;
  jobLocation: string;
  matchScore: number;
  breakdown: EmployerMatchBreakdownItem[];
  recommended: boolean;
  saved: boolean;
  explanationSummary: string;
  nextBestAction: string;
}

export interface EmployerFilterOption {
  label: string;
  value: string;
}

export interface EmployerExperienceFilterOption extends EmployerFilterOption {
  min: number;
  max: number;
}
