'use client';

import Link from 'next/link';
import {
  ArrowRight,
  ArrowUpDown,
  Award,
  BarChart3,
  Bookmark,
  Briefcase,
  Building2,
  Calendar,
  CheckCircle2,
  ChevronRight,
  Clock,
  FileText,
  Filter,
  GraduationCap,
  MapPin,
  MessageSquare,
  Search,
  Sparkles,
  Star,
  ThumbsUp,
  Users,
  X,
  Zap,
} from 'lucide-react';
import {useState} from 'react';

import {Badge} from '@/components/ui/badge';
import {Button} from '@/components/ui/button';
import {cn} from '@/lib/utils';

interface Match {
  id: number;
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
  breakdown: {component: string; score: number; weight: number}[];
  recommended: boolean;
  saved: boolean;
}

const MATCHES: Match[] = [
  {
    id: 1,
    candidateName: 'Ahmet Yılmaz',
    candidateInitials: 'AY',
    candidateHeadline: 'Senior React Developer',
    candidateExp: 6,
    candidateLocation: 'İstanbul',
    candidateSkills: ['React', 'TypeScript', 'Node.js', 'GraphQL', 'Next.js'],
    jobTitle: 'Senior Frontend Developer',
    jobDepartment: 'Engineering',
    jobLocation: 'İstanbul (Hybrid)',
    matchScore: 96,
    breakdown: [
      {component: 'Beceri Uyumu', score: 98, weight: 35},
      {component: 'Deneyim', score: 95, weight: 25},
      {component: 'Eğitim', score: 92, weight: 15},
      {component: 'Lokasyon', score: 96, weight: 15},
      {component: 'Dil', score: 94, weight: 10},
    ],
    recommended: true,
    saved: false,
  },
  {
    id: 2,
    candidateName: 'Mehmet Demir',
    candidateInitials: 'MD',
    candidateHeadline: 'Go Backend Engineer',
    candidateExp: 7,
    candidateLocation: 'İzmir',
    candidateSkills: ['Go', 'gRPC', 'PostgreSQL', 'Docker', 'Redis'],
    jobTitle: 'Backend Engineer (Go)',
    jobDepartment: 'Engineering',
    jobLocation: 'Remote',
    matchScore: 94,
    breakdown: [
      {component: 'Beceri Uyumu', score: 96, weight: 35},
      {component: 'Deneyim', score: 98, weight: 25},
      {component: 'Eğitim', score: 90, weight: 15},
      {component: 'Lokasyon', score: 95, weight: 15},
      {component: 'Dil', score: 92, weight: 10},
    ],
    recommended: true,
    saved: true,
  },
  {
    id: 3,
    candidateName: 'Zeynep Kaya',
    candidateInitials: 'ZK',
    candidateHeadline: 'Product Designer (UI/UX)',
    candidateExp: 5,
    candidateLocation: 'Ankara',
    candidateSkills: ['Figma', 'Design Systems', 'Prototyping', 'User Research'],
    jobTitle: 'Product Designer',
    jobDepartment: 'Design',
    jobLocation: 'İstanbul (Ofis)',
    matchScore: 92,
    breakdown: [
      {component: 'Beceri Uyumu', score: 95, weight: 35},
      {component: 'Deneyim', score: 88, weight: 25},
      {component: 'Eğitim', score: 90, weight: 15},
      {component: 'Lokasyon', score: 94, weight: 15},
      {component: 'Dil', score: 92, weight: 10},
    ],
    recommended: true,
    saved: false,
  },
  {
    id: 4,
    candidateName: 'Selen Çelik',
    candidateInitials: 'SÇ',
    candidateHeadline: 'DevOps / SRE',
    candidateExp: 4,
    candidateLocation: 'İstanbul (Remote)',
    candidateSkills: ['Kubernetes', 'Terraform', 'AWS', 'CI/CD'],
    jobTitle: 'DevOps Engineer',
    jobDepartment: 'Infrastructure',
    jobLocation: 'İzmir (Hybrid)',
    matchScore: 87,
    breakdown: [
      {component: 'Beceri Uyumu', score: 90, weight: 35},
      {component: 'Deneyim', score: 82, weight: 25},
      {component: 'Eğitim', score: 88, weight: 15},
      {component: 'Lokasyon', score: 84, weight: 15},
      {component: 'Dil', score: 90, weight: 10},
    ],
    recommended: false,
    saved: false,
  },
  {
    id: 5,
    candidateName: 'Murat Tekin',
    candidateInitials: 'MT',
    candidateHeadline: 'Security Engineer',
    candidateExp: 6,
    candidateLocation: 'İstanbul',
    candidateSkills: ['Penetration Testing', 'SIEM', 'Python', 'Cloud Security'],
    jobTitle: 'Senior Frontend Developer',
    jobDepartment: 'Engineering',
    jobLocation: 'İstanbul (Hybrid)',
    matchScore: 88,
    breakdown: [
      {component: 'Beceri Uyumu', score: 86, weight: 35},
      {component: 'Deneyim', score: 92, weight: 25},
      {component: 'Eğitim', score: 88, weight: 15},
      {component: 'Lokasyon', score: 96, weight: 15},
      {component: 'Dil', score: 90, weight: 10},
    ],
    recommended: false,
    saved: false,
  },
  {
    id: 6,
    candidateName: 'Aysel Korkmaz',
    candidateInitials: 'AK',
    candidateHeadline: 'QA Automation Engineer',
    candidateExp: 5,
    candidateLocation: 'İstanbul',
    candidateSkills: ['Selenium', 'Cypress', 'Java', 'CI/CD'],
    jobTitle: 'QA Automation Engineer',
    jobDepartment: 'Engineering',
    jobLocation: 'İstanbul (Ofis)',
    matchScore: 85,
    breakdown: [
      {component: 'Beceri Uyumu', score: 88, weight: 35},
      {component: 'Deneyim', score: 86, weight: 25},
      {component: 'Eğitim', score: 84, weight: 15},
      {component: 'Lokasyon', score: 98, weight: 15},
      {component: 'Dil', score: 86, weight: 10},
    ],
    recommended: false,
    saved: false,
  },
];

function scoreColorClasses(score: number) {
  if (score >= 90) return {text: 'text-match-high', bar: 'match-bar-fill high', ring: 'border-match-high bg-match-high'};
  if (score >= 75) return {text: 'text-match-mid', bar: 'match-bar-fill mid', ring: 'border-match-mid bg-match-mid'};
  return {text: 'text-match-low', bar: 'match-bar-fill low', ring: 'border-match-low bg-match-low'};
}

function MatchScoreRing({score, size = 'md'}: {score: number; size?: 'sm' | 'md' | 'lg'}) {
  const colors = scoreColorClasses(score);
  const sizeClasses = {
    sm: 'size-12 text-[11px] border-[2.5px]',
    md: 'size-16 text-sm border-[3px]',
    lg: 'size-20 text-lg border-4',
  };
  return (
    <div className={cn('flex items-center justify-center rounded-full text-white font-extrabold', sizeClasses[size], colors.ring)}>
      {score}
    </div>
  );
}

function MatchBreakdownBars({breakdown}: {breakdown: Match['breakdown']}) {
  return (
    <div className="space-y-2">
      {breakdown.map((item) => (
        <div key={item.component}>
          <div className="flex items-center justify-between mb-0.5">
            <span className="text-[10px] text-muted-foreground font-medium">{item.component}</span>
            <span className="text-[10px] font-bold text-foreground">{item.score}%</span>
          </div>
          <div className="match-bar-bg">
            <div
              className={cn(
                'match-bar-fill',
                item.score >= 90 ? 'high' : item.score >= 75 ? 'mid' : 'low'
              )}
              style={{width: `${item.score}%`}}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function ComparisonView({match, onClose}: {match: Match; onClose: () => void}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
      <div
        className="relative surface-card w-full max-w-2xl max-h-[85vh] overflow-y-auto p-6 animate-fade-in-up"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute right-4 top-4 flex size-8 items-center justify-center rounded-xl text-muted-foreground hover:bg-surface-muted z-10"
        >
          <X className="size-4" />
        </button>

        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-2 mb-3">
            <MatchScoreRing score={match.matchScore} size="lg" />
          </div>
          <h2 className="text-lg font-bold">Eşleşme Analizi</h2>
          <p className="text-xs text-muted-foreground mt-1">Aday-pozisyon karşılaştırması</p>
        </div>

        {/* Side by side */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="rounded-2xl border border-border bg-surface-muted p-4">
            <div className="flex items-center gap-3 mb-3">
              <div className="candidate-avatar size-12 text-sm">{match.candidateInitials}</div>
              <div>
                <div className="text-sm font-bold">{match.candidateName}</div>
                <div className="text-[11px] text-muted-foreground">{match.candidateHeadline}</div>
              </div>
            </div>
            <div className="space-y-1.5 text-[11px]">
              <div className="flex items-center gap-1.5 text-muted-foreground">
                <Briefcase className="size-3" />
                {match.candidateExp} yıl deneyim
              </div>
              <div className="flex items-center gap-1.5 text-muted-foreground">
                <MapPin className="size-3" />
                {match.candidateLocation}
              </div>
            </div>
            <div className="flex flex-wrap gap-1 mt-3">
              {match.candidateSkills.map((s) => (
                <span key={s} className="skill-chip match text-[10px]">{s}</span>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-surface-muted p-4">
            <div className="flex items-center gap-3 mb-3">
              <div className="flex size-12 items-center justify-center rounded-2xl bg-secondary text-secondary-foreground">
                <Briefcase className="size-5" />
              </div>
              <div>
                <div className="text-sm font-bold">{match.jobTitle}</div>
                <div className="text-[11px] text-muted-foreground">{match.jobDepartment}</div>
              </div>
            </div>
            <div className="space-y-1.5 text-[11px]">
              <div className="flex items-center gap-1.5 text-muted-foreground">
                <Building2 className="size-3" />
                {match.jobDepartment}
              </div>
              <div className="flex items-center gap-1.5 text-muted-foreground">
                <MapPin className="size-3" />
                {match.jobLocation}
              </div>
            </div>
          </div>
        </div>

        {/* Breakdown */}
        <div className="mb-6">
          <h3 className="text-xs font-bold uppercase tracking-wide text-muted-foreground mb-3">Eşleşme Detayları</h3>
          <MatchBreakdownBars breakdown={match.breakdown} />
        </div>

        {/* Recommended Actions */}
        <div className="rounded-2xl border border-primary/20 bg-primary/[0.04] p-4">
          <h3 className="text-xs font-bold uppercase tracking-wide text-primary mb-3 flex items-center gap-2">
            <Zap className="size-3.5" />
            Önerilen Eylemler
          </h3>
          <div className="space-y-2">
            {match.matchScore >= 90 ? (
              <>
                <div className="flex items-center gap-2 text-[13px] text-foreground">
                  <CheckCircle2 className="size-4 text-success shrink-0" />
                  Hemen kısa listeye alın ve mülakat planlayın
                </div>
                <div className="flex items-center gap-2 text-[13px] text-foreground">
                  <MessageSquare className="size-4 text-primary shrink-0" />
                  Adayla hızlıca iletişime geçin
                </div>
              </>
            ) : match.matchScore >= 80 ? (
              <>
                <div className="flex items-center gap-2 text-[13px] text-foreground">
                  <Star className="size-4 text-warning shrink-0" />
                  Kısa listeye alın, teknik mülakata davet edin
                </div>
                <div className="flex items-center gap-2 text-[13px] text-foreground">
                  <FileText className="size-4 text-muted-foreground shrink-0" />
                  CV detaylarını inceleyin
                </div>
              </>
            ) : (
              <>
                <div className="flex items-center gap-2 text-[13px] text-foreground">
                  <FileText className="size-4 text-muted-foreground shrink-0" />
                  Detaylı değerlendirme yapın
                </div>
              </>
            )}
          </div>
        </div>

        <div className="flex gap-3 mt-5">
          <Button className="flex-1">
            <CheckCircle2 className="size-4 mr-2" />
            Kısa Listeye Al
          </Button>
          <Button variant="secondary">
            <Calendar className="size-4 mr-2" />
            Mülakat Planla
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function EmployerMatchesPage() {
  const [matches, setMatches] = useState<Match[]>(MATCHES);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<'score' | 'recent'>('score');
  const [filterRecommended, setFilterRecommended] = useState(false);
  const [selectedMatch, setSelectedMatch] = useState<Match | null>(null);
  const [savedIds, setSavedIds] = useState<Set<number>>(new Set([2]));

  const filtered = matches
    .filter((m) => {
      if (search && !m.candidateName.toLowerCase().includes(search.toLowerCase()) && !m.jobTitle.toLowerCase().includes(search.toLowerCase())) return false;
      if (filterRecommended && !m.recommended) return false;
      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'score') return b.matchScore - a.matchScore;
      return a.id - b.id;
    });

  const toggleSave = (id: number) => {
    setSavedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const excellentCount = matches.filter((m) => m.matchScore >= 90).length;
  const goodCount = matches.filter((m) => m.matchScore >= 75 && m.matchScore < 90).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="employer-page-title">Eşleşmeler</h1>
          <p className="employer-page-desc">Aday-pozisyon eşleşmelerini görüntüleyin ve analiz edin</p>
        </div>
      </div>

      {/* Stats */}
      <div className="employer-grid-4">
        <div className="rounded-2xl border border-border bg-surface p-4">
          <span className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">Toplam Eşleşme</span>
          <div className="text-2xl font-bold mt-1">{matches.length}</div>
        </div>
        <div className="rounded-2xl border border-primary/20 bg-primary/[0.04] p-4">
          <span className="text-xs text-match-high font-semibold uppercase tracking-wider">Mükemmel (90%+)</span>
          <div className="text-2xl font-bold mt-1 text-match-high">{excellentCount}</div>
        </div>
        <div className="rounded-2xl border border-border bg-surface p-4">
          <span className="text-xs text-match-mid font-semibold uppercase tracking-wider">İyi (75-89%)</span>
          <div className="text-2xl font-bold mt-1 text-match-mid">{goodCount}</div>
        </div>
        <div className="rounded-2xl border border-border bg-surface p-4">
          <span className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">Ort. Skor</span>
          <div className="text-2xl font-bold mt-1">
            {Math.round(matches.reduce((s, m) => s + m.matchScore, 0) / matches.length)}%
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Aday veya pozisyon ara..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-10 w-full rounded-2xl border border-border bg-surface pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-4 focus:ring-[var(--ring)]"
          />
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setFilterRecommended(!filterRecommended)}
            className={cn(
              'inline-flex h-10 items-center gap-2 rounded-2xl border px-4 text-sm font-semibold transition',
              filterRecommended
                ? 'border-primary bg-secondary text-secondary-foreground'
                : 'border-border bg-surface text-foreground hover:border-primary/40'
            )}
          >
            <Sparkles className="size-4" />
            AI Önerileri
            {filterRecommended && <span className="text-[10px] bg-primary text-primary-foreground rounded-full px-1.5 py-0.5">{matches.filter(m => m.recommended).length}</span>}
          </button>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
            className="h-10 rounded-2xl border border-border bg-surface px-4 text-sm text-foreground focus:outline-none focus:ring-4 focus:ring-[var(--ring)] cursor-pointer"
          >
            <option value="score">Skor (En yüksek)</option>
            <option value="recent">En yeni</option>
          </select>
        </div>
      </div>

      {/* Match Cards */}
      <div className="space-y-4">
        {filtered.map((match, index) => {
          const colors = scoreColorClasses(match.matchScore);
          const isSaved = savedIds.has(match.id);
          return (
            <div
              key={match.id}
              className="surface-card p-5 animate-fade-in-up"
              style={{animationDelay: `${index * 80}ms`}}
            >
              <div className="flex flex-col lg:flex-row lg:items-center gap-4">
                {/* Score */}
                <div className="flex items-center gap-4 lg:w-64 shrink-0">
                  <MatchScoreRing score={match.matchScore} size="md" />
                  <div>
                    <Link href={`/tr/employer/candidates/${match.id}`} className="text-sm font-bold hover:text-primary transition">
                      {match.candidateName}
                    </Link>
                    <div className="text-xs text-muted-foreground">{match.candidateHeadline}</div>
                    <div className="flex items-center gap-2 mt-1 text-[11px] text-muted-foreground">
                      <span className="inline-flex items-center gap-1">
                        <Briefcase className="size-3" />
                        {match.candidateExp} yıl
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <MapPin className="size-3" />
                        {match.candidateLocation}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Arrow */}
                <div className="hidden lg:flex items-center justify-center shrink-0">
                  <div className="flex size-8 items-center justify-center rounded-full bg-surface-muted">
                    <ArrowRight className="size-4 text-muted-foreground" />
                  </div>
                </div>

                {/* Job */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Briefcase className="size-4 text-muted-foreground" />
                    <span className="text-sm font-semibold">{match.jobTitle}</span>
                    <span className="text-[11px] text-muted-foreground">({match.jobDepartment})</span>
                  </div>
                  <div className="text-[11px] text-muted-foreground mb-2">{match.jobLocation}</div>
                  <div className="flex flex-wrap gap-1">
                    {match.candidateSkills.slice(0, 5).map((skill) => (
                      <span key={skill} className="skill-chip match text-[10px]">{skill}</span>
                    ))}
                  </div>
                </div>

                {/* Breakdown mini */}
                <div className="lg:w-48 shrink-0 hidden md:block">
                  <MatchBreakdownBars breakdown={match.breakdown} />
                </div>

                {/* Actions */}
                <div className="flex lg:flex-col items-center lg:items-end gap-2 shrink-0">
                  <button
                    onClick={() => toggleSave(match.id)}
                    className={cn(
                      'flex size-9 items-center justify-center rounded-xl border transition',
                      isSaved
                        ? 'border-primary/40 bg-primary/20 text-primary'
                        : 'border-border bg-surface-muted text-muted-foreground hover:bg-surface-strong'
                    )}
                  >
                    <Bookmark className={cn('size-4', isSaved && 'fill-primary')} />
                  </button>
                  <Button size="sm" onClick={() => setSelectedMatch(match)}>
                    <BarChart3 className="size-3.5 mr-1.5" />
                    Analiz
                  </Button>
                  <Button size="sm" variant="secondary">
                    <CheckCircle2 className="size-3.5 mr-1.5" />
                    Kısa Liste
                  </Button>
                </div>
              </div>

              {/* Recommended badge */}
              {match.recommended && (
                <div className="mt-3 pt-3 border-t border-primary/10 flex items-center gap-2">
                  <Sparkles className="size-3.5 text-primary" />
                  <span className="text-[11px] font-semibold text-primary">AI tarafından önerildi — Bu eşleşme profil ve pozisyon uyumu çok yüksek</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {filtered.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <Search className="size-12 text-muted-foreground/30 mb-4" />
          <p className="text-sm font-medium text-muted-foreground">Eşleşme bulunamadı</p>
          <p className="text-xs text-muted-foreground mt-1">Farklı arama kriterleri deneyin</p>
        </div>
      )}

      {/* Comparison Modal */}
      {selectedMatch && (
        <ComparisonView match={selectedMatch} onClose={() => setSelectedMatch(null)} />
      )}
    </div>
  );
}
