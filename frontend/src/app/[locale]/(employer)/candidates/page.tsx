'use client';

import Link from 'next/link';
import {
  ArrowUpDown,
  Briefcase,
  ChevronDown,
  Download,
  Filter,
  GraduationCap,
  MapPin,
  Search,
  SlidersHorizontal,
  Star,
  Upload,
  X,
} from 'lucide-react';
import {useState, useMemo} from 'react';

import {Badge} from '@/components/ui/badge';
import {Button} from '@/components/ui/button';
import {cn} from '@/lib/utils';

interface Candidate {
  id: number;
  name: string;
  initials: string;
  headline: string;
  experience: number;
  location: string;
  matchScore: number;
  skills: string[];
  education: string;
  status: 'new' | 'reviewed' | 'shortlisted' | 'rejected';
  appliedAt: string;
}

const CANDIDATES: Candidate[] = [
  {id: 1, name: 'Ahmet Yılmaz', initials: 'AY', headline: 'Senior React Developer', experience: 6, location: 'İstanbul', matchScore: 96, skills: ['React', 'TypeScript', 'Node.js', 'GraphQL', 'Next.js'], education: 'Bilgisayar Mühendisliği', status: 'shortlisted', appliedAt: '2 gün önce'},
  {id: 2, name: 'Zeynep Kaya', initials: 'ZK', headline: 'Product Designer (UI/UX)', experience: 5, location: 'Ankara', matchScore: 92, skills: ['Figma', 'Design Systems', 'Prototyping', 'User Research'], education: 'Grafik Tasarım', status: 'new', appliedAt: '3 gün önce'},
  {id: 3, name: 'Mehmet Demir', initials: 'MD', headline: 'Go Backend Engineer', experience: 7, location: 'İzmir', matchScore: 89, skills: ['Go', 'gRPC', 'PostgreSQL', 'Docker', 'Redis'], education: 'Yazılım Mühendisliği', status: 'reviewed', appliedAt: '5 gün önce'},
  {id: 4, name: 'Selen Çelik', initials: 'SÇ', headline: 'DevOps / SRE', experience: 4, location: 'İstanbul', matchScore: 87, skills: ['Kubernetes', 'Terraform', 'AWS', 'CI/CD'], education: 'Bilgisayar Mühendisliği', status: 'new', appliedAt: '1 hafta önce'},
  {id: 5, name: 'Burak Şahin', initials: 'BŞ', headline: 'Full Stack Developer', experience: 5, location: 'Antalya', matchScore: 84, skills: ['React', 'Python', 'Django', 'AWS'], education: 'Bilgisayar Mühendisliği', status: 'shortlisted', appliedAt: '4 gün önce'},
  {id: 6, name: 'Elif Yıldız', initials: 'EY', headline: 'Data Scientist', experience: 3, location: 'İstanbul', matchScore: 81, skills: ['Python', 'TensorFlow', 'SQL', 'Pandas'], education: 'İstatistik', status: 'reviewed', appliedAt: '6 gün önce'},
  {id: 7, name: 'Can Özdemir', initials: 'CÖ', headline: 'Mobile Developer (React Native)', experience: 4, location: 'Bursa', matchScore: 79, skills: ['React Native', 'TypeScript', 'Firebase'], education: 'Bilgisayar Mühendisliği', status: 'new', appliedAt: '1 hafta önce'},
  {id: 8, name: 'Aysel Korkmaz', initials: 'AK', headline: 'QA Automation Engineer', experience: 5, location: 'İstanbul', matchScore: 85, skills: ['Selenium', 'Cypress', 'Java', 'CI/CD'], education: 'Yazılım Mühendisliği', status: 'reviewed', appliedAt: '3 gün önce'},
  {id: 9, name: 'Emre Aydın', initials: 'EA', headline: 'Technical Lead', experience: 8, location: 'İzmir', matchScore: 78, skills: ['Java', 'Spring Boot', 'Microservices', 'Kafka'], education: 'Bilgisayar Mühendisliği', status: 'shortlisted', appliedAt: '5 gün önce'},
  {id: 10, name: 'Deniz Karaca', initials: 'DK', headline: 'Frontend Engineer (Vue.js)', experience: 4, location: 'Ankara', matchScore: 74, skills: ['Vue.js', 'JavaScript', 'CSS', 'Tailwind'], education: 'Bilgisayar Mühendisliği', status: 'new', appliedAt: '2 hafta önce'},
  {id: 11, name: 'Fatma Gül', initials: 'FG', headline: 'Machine Learning Engineer', experience: 3, location: 'İstanbul', matchScore: 72, skills: ['Python', 'PyTorch', 'NLP', 'MLOps'], education: 'Yapay Zeka', status: 'reviewed', appliedAt: '1 hafta önce'},
  {id: 12, name: 'Murat Tekin', initials: 'MT', headline: 'Security Engineer', experience: 6, location: 'İstanbul', matchScore: 88, skills: ['Penetration Testing', 'SIEM', 'Python', 'Cloud Security'], education: 'Siber Güvenlik', status: 'new', appliedAt: '4 gün önce'},
];

const SKILL_OPTIONS = ['React', 'TypeScript', 'Node.js', 'Python', 'Go', 'AWS', 'Docker', 'Kubernetes', 'Figma', 'Java'];
const LOCATION_OPTIONS = ['İstanbul', 'Ankara', 'İzmir', 'Antalya', 'Bursa', 'Remote'];
const EXPERIENCE_OPTIONS = [
  {label: '0-2 yıl', min: 0, max: 2},
  {label: '3-5 yıl', min: 3, max: 5},
  {label: '6-10 yıl', min: 6, max: 10},
  {label: '10+ yıl', min: 10, max: 99},
];

function scoreColor(score: number) {
  if (score >= 85) return {text: 'text-match-high', bar: 'match-bar-fill high', ring: 'border-match-high bg-match-high'};
  if (score >= 70) return {text: 'text-match-mid', bar: 'match-bar-fill mid', ring: 'border-match-mid bg-match-mid'};
  return {text: 'text-match-low', bar: 'match-bar-fill low', ring: 'border-match-low bg-match-low'};
}

function CandidateCard({candidate}: {candidate: Candidate}) {
  const colors = scoreColor(candidate.matchScore);
  const statusMap = {
    new: {tone: 'new' as const, label: 'Yeni'},
    reviewed: {tone: 'default' as const, label: 'İncelendi'},
    shortlisted: {tone: 'success' as const, label: 'Kısa Liste'},
    rejected: {tone: 'danger' as const, label: 'Reddedildi'},
  };
  const s = statusMap[candidate.status];

  return (
    <Link href={`/tr/employer/candidates/${candidate.id}`}>
      <div className="candidate-card h-full flex flex-col">
        <div className="flex items-start justify-between mb-3">
          <div className="candidate-avatar text-sm">{candidate.initials}</div>
          <div className="flex items-center gap-2">
            <Badge tone={s.tone} className="text-[10px]">{s.label}</Badge>
            <div
              className={cn(
                'flex size-10 items-center justify-center rounded-full border-2 text-[12px] font-bold text-white',
                colors.ring
              )}
            >
              <span>{candidate.matchScore}</span>
            </div>
          </div>
        </div>

        <h3 className="text-sm font-bold text-foreground mb-0.5">{candidate.name}</h3>
        <p className="text-xs text-muted-foreground mb-2">{candidate.headline}</p>

        <div className="match-bar-bg mb-3">
          <div
            className={cn('match-bar-fill', colors.bar.split(' ')[1])}
            style={{width: `${candidate.matchScore}%`}}
          />
        </div>

        <div className="flex items-center gap-3 text-[11px] text-muted-foreground mb-3">
          <span className="inline-flex items-center gap-1">
            <Briefcase className="size-3" />
            {candidate.experience} yıl
          </span>
          <span className="inline-flex items-center gap-1">
            <MapPin className="size-3" />
            {candidate.location}
          </span>
        </div>

        <div className="flex flex-wrap gap-1 mt-auto">
          {candidate.skills.slice(0, 4).map((skill) => (
            <span key={skill} className="skill-chip match">{skill}</span>
          ))}
          {candidate.skills.length > 4 && (
            <span className="skill-chip text-muted-foreground bg-surface-muted">+{candidate.skills.length - 4}</span>
          )}
        </div>

        <div className="flex items-center gap-1 text-[10px] text-muted-foreground mt-3 pt-3 border-t border-border">
          <GraduationCap className="size-3" />
          {candidate.education}
        </div>
      </div>
    </Link>
  );
}

export default function EmployerCandidatesPage() {
  const [search, setSearch] = useState('');
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [selectedLocations, setSelectedLocations] = useState<string[]>([]);
  const [selectedExp, setSelectedExp] = useState<string[]>([]);
  const [minScore, setMinScore] = useState(0);
  const [sortBy, setSortBy] = useState<'match' | 'name' | 'experience' | 'recent'>('match');
  const [showFilters, setShowFilters] = useState(false);

  const toggleSkill = (skill: string) =>
    setSelectedSkills((prev) => prev.includes(skill) ? prev.filter((s) => s !== skill) : [...prev, skill]);

  const toggleLocation = (loc: string) =>
    setSelectedLocations((prev) => prev.includes(loc) ? prev.filter((l) => l !== loc) : [...prev, loc]);

  const toggleExp = (exp: string) =>
    setSelectedExp((prev) => prev.includes(exp) ? prev.filter((e) => e !== exp) : [...prev, exp]);

  const clearFilters = () => {
    setSelectedSkills([]);
    setSelectedLocations([]);
    setSelectedExp([]);
    setMinScore(0);
    setSearch('');
  };

  const filtered = useMemo(() => {
    let list = CANDIDATES.filter((c) => {
      if (search && !c.name.toLowerCase().includes(search.toLowerCase()) && !c.headline.toLowerCase().includes(search.toLowerCase())) return false;
      if (selectedSkills.length > 0 && !selectedSkills.some((s) => c.skills.includes(s))) return false;
      if (selectedLocations.length > 0 && !selectedLocations.includes(c.location)) return false;
      if (selectedExp.length > 0) {
        const match = EXPERIENCE_OPTIONS.filter((e) => selectedExp.includes(e.label));
        if (!match.some((e) => c.experience >= e.min && c.experience <= e.max)) return false;
      }
      if (c.matchScore < minScore) return false;
      return true;
    });

    switch (sortBy) {
      case 'match': list.sort((a, b) => b.matchScore - a.matchScore); break;
      case 'name': list.sort((a, b) => a.name.localeCompare(b.name)); break;
      case 'experience': list.sort((a, b) => b.experience - a.experience); break;
      case 'recent': list.sort((a, b) => a.appliedAt.localeCompare(b.appliedAt)); break;
    }
    return list;
  }, [search, selectedSkills, selectedLocations, selectedExp, minScore, sortBy]);

  const hasFilters = selectedSkills.length > 0 || selectedLocations.length > 0 || selectedExp.length > 0 || minScore > 0 || search.length > 0;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="employer-page-title">Adaylar</h1>
          <p className="employer-page-desc">Tüm adayları inceleyin, filtreleyin ve yönetin</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" className="hidden sm:flex items-center gap-2">
            <Upload className="size-4" />
            CV Yükle
          </Button>
          <Button>
            <Search className="size-4 mr-2" />
            Aday Ara
          </Button>
        </div>
      </div>

      {/* Upload area */}
      <div className="rounded-2xl border-2 border-dashed border-border-strong bg-surface-muted p-8 text-center transition hover:border-primary/40 hover:bg-surface">
        <div className="flex size-14 items-center justify-center rounded-2xl bg-secondary text-secondary-foreground mx-auto mb-3">
          <Upload className="size-6" />
        </div>
        <h3 className="text-sm font-semibold mb-1">CV Dosyalarını Sürükleyin veya Yükleyin</h3>
        <p className="text-xs text-muted-foreground mb-4">PDF, DOCX formatları desteklenir. Toplu yükleme yapabilirsiniz.</p>
        <Button size="sm" variant="secondary">Dosya Seç</Button>
      </div>

      {/* Search + Sort + Filter Toggle */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Aday adı veya pozisyon ara..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-10 w-full rounded-2xl border border-border bg-surface pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-4 focus:ring-[var(--ring)]"
          />
        </div>
        <div className="flex items-center gap-2">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
            className="h-10 rounded-2xl border border-border bg-surface px-4 text-sm text-foreground focus:outline-none focus:ring-4 focus:ring-[var(--ring)] cursor-pointer"
          >
            <option value="match">Eşleşme (En yüksek)</option>
            <option value="name">İsim (A-Z)</option>
            <option value="experience">Deneyim</option>
            <option value="recent">En yeni</option>
          </select>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              'inline-flex h-10 items-center gap-2 rounded-2xl border px-4 text-sm font-semibold transition',
              showFilters || hasFilters
                ? 'border-primary bg-secondary text-secondary-foreground'
                : 'border-border bg-surface text-foreground hover:border-primary/40'
            )}
          >
            <Filter className="size-4" />
            Filtreler
            {hasFilters && (
              <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-bold text-primary-foreground">
                {selectedSkills.length + selectedLocations.length + selectedExp.length + (minScore > 0 ? 1 : 0)}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Filter Panel (expandable) */}
      {showFilters && (
        <div className="rounded-2xl border border-border bg-surface p-5 animate-fade-in-up">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold">Filtreler</h3>
            {hasFilters && (
              <button onClick={clearFilters} className="text-xs font-semibold text-danger flex items-center gap-1 hover:underline">
                <X className="size-3" />
                Temizle
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {/* Skills */}
            <div>
              <h4 className="filter-section-title">Yetenekler</h4>
              <div className="space-y-1">
                {SKILL_OPTIONS.map((skill) => (
                  <label key={skill} className="filter-option">
                    <input
                      type="checkbox"
                      checked={selectedSkills.includes(skill)}
                      onChange={() => toggleSkill(skill)}
                      className="size-4 rounded accent-primary"
                    />
                    <span>{skill}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Location */}
            <div>
              <h4 className="filter-section-title">Lokasyon</h4>
              <div className="space-y-1">
                {LOCATION_OPTIONS.map((loc) => (
                  <label key={loc} className="filter-option">
                    <input
                      type="checkbox"
                      checked={selectedLocations.includes(loc)}
                      onChange={() => toggleLocation(loc)}
                      className="size-4 rounded accent-primary"
                    />
                    <span>{loc}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Experience */}
            <div>
              <h4 className="filter-section-title">Deneyim</h4>
              <div className="space-y-1">
                {EXPERIENCE_OPTIONS.map((exp) => (
                  <label key={exp.label} className="filter-option">
                    <input
                      type="checkbox"
                      checked={selectedExp.includes(exp.label)}
                      onChange={() => toggleExp(exp.label)}
                      className="size-4 rounded accent-primary"
                    />
                    <span>{exp.label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Match Score */}
            <div>
              <h4 className="filter-section-title">Min. Eşleşme Skoru: {minScore}%</h4>
              <input
                type="range"
                min={0}
                max={100}
                value={minScore}
                onChange={(e) => setMinScore(Number(e.target.value))}
                className="w-full accent-primary cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-muted-foreground mt-1">
                <span>0%</span>
                <span>50%</span>
                <span>100%</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Results count */}
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground font-medium">
          <span className="text-foreground font-bold">{filtered.length}</span> aday gösteriliyor
          {hasFilters && ' (filtreli)'}
        </p>
      </div>

      {/* Candidate Grid */}
      {filtered.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filtered.map((candidate) => (
            <CandidateCard key={candidate.id} candidate={candidate} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <Search className="size-12 text-muted-foreground/30 mb-4" />
          <p className="text-sm font-medium text-muted-foreground">Filtrelere uygun aday bulunamadı</p>
          <p className="text-xs text-muted-foreground mt-1">Farklı filtreler deneyin</p>
          <Button variant="secondary" className="mt-4" onClick={clearFilters}>Filtreleri Temizle</Button>
        </div>
      )}
    </div>
  );
}
