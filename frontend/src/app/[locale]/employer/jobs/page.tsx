'use client';

import {
  ArrowUpDown,
  BarChart3,
  Briefcase,
  ChevronLeft,
  ChevronRight,
  Clock,
  Edit3,
  Eye,
  MapPin,
  MoreHorizontal,
  Pause,
  Play,
  Plus,
  Search,
  Trash2,
  Users,
  X,
} from 'lucide-react';
import {useState} from 'react';

import {Badge} from '@/components/ui/badge';
import {Button} from '@/components/ui/button';
import {cn} from '@/lib/utils';

type JobStatus = 'active' | 'paused' | 'closed';

interface Job {
  id: number;
  title: string;
  department: string;
  location: string;
  status: JobStatus;
  applicants: number;
  matchAvg: number;
  postedAt: string;
  views: number;
}

const INITIAL_JOBS: Job[] = [
  {id: 1, title: 'Senior Frontend Developer', department: 'Engineering', location: 'İstanbul (Hybrid)', status: 'active', applicants: 64, matchAvg: 88, postedAt: '2 gün önce', views: 342},
  {id: 2, title: 'Backend Engineer (Go)', department: 'Engineering', location: 'Remote', status: 'active', applicants: 42, matchAvg: 82, postedAt: '5 gün önce', views: 218},
  {id: 3, title: 'Product Designer', department: 'Design', location: 'İstanbul (Ofis)', status: 'active', applicants: 31, matchAvg: 76, postedAt: '1 hafta önce', views: 156},
  {id: 4, title: 'DevOps Engineer', department: 'Infrastructure', location: 'İzmir (Hybrid)', status: 'paused', applicants: 19, matchAvg: 91, postedAt: '2 hafta önce', views: 98},
  {id: 5, title: 'Mobile Developer (React Native)', department: 'Engineering', location: 'Ankara (Remote)', status: 'active', applicants: 27, matchAvg: 79, postedAt: '3 hafta önce', views: 187},
  {id: 6, title: 'Data Scientist', department: 'Data', location: 'İstanbul (Hybrid)', status: 'closed', applicants: 53, matchAvg: 73, postedAt: '1 ay önce', views: 412},
  {id: 7, title: 'QA Automation Engineer', department: 'Engineering', location: 'İstanbul (Ofis)', status: 'active', applicants: 15, matchAvg: 85, postedAt: '4 gün önce', views: 76},
  {id: 8, title: 'Technical Lead', department: 'Engineering', location: 'İstanbul (Hybrid)', status: 'active', applicants: 38, matchAvg: 80, postedAt: '1 hafta önce', views: 245},
];

function StatusToggle({status, onChange}: {status: JobStatus; onChange: (s: JobStatus) => void}) {
  const options: {value: JobStatus; label: string; icon: React.ElementType; tone: string}[] = [
    {value: 'active', label: 'Aktif', icon: Play, tone: 'text-success'},
    {value: 'paused', label: 'Duraklat', icon: Pause, tone: 'text-warning'},
    {value: 'closed', label: 'Kapat', icon: X, tone: 'text-danger'},
  ];
  return (
    <div className="inline-flex items-center gap-1 rounded-xl bg-surface-muted p-1">
      {options.map((opt) => {
        const active = status === opt.value;
        return (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            className={cn(
              'inline-flex items-center gap-1 rounded-lg px-2.5 py-1 text-[11px] font-semibold transition',
              active ? 'bg-surface text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
            )}
            title={opt.label}
          >
            <opt.icon className={cn('size-3', active && opt.tone)} />
            <span className="hidden sm:inline">{opt.label}</span>
          </button>
        );
      })}
    </div>
  );
}

function StatusBadge({status}: {status: JobStatus}) {
  const map = {
    active: {tone: 'success' as const, label: 'Aktif'},
    paused: {tone: 'warning' as const, label: 'Duraklatıldı'},
    closed: {tone: 'default' as const, label: 'Kapandı'},
  };
  const m = map[status];
  return <Badge tone={m.tone} className="text-[11px] font-semibold">{m.label}</Badge>;
}

export default function EmployerJobsPage() {
  const [jobs, setJobs] = useState<Job[]>(INITIAL_JOBS);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<JobStatus | 'all'>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);

  const filtered = jobs.filter((j) => {
    const matchesSearch = !search || j.title.toLowerCase().includes(search.toLowerCase()) || j.department.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'all' || j.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const activeCount = jobs.filter((j) => j.status === 'active').length;
  const pausedCount = jobs.filter((j) => j.status === 'paused').length;
  const closedCount = jobs.filter((j) => j.status === 'closed').length;

  function handleStatusChange(id: number, newStatus: JobStatus) {
    setJobs((prev) => prev.map((j) => (j.id === id ? {...j, status: newStatus} : j)));
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="employer-page-title">İlanlarım</h1>
          <p className="employer-page-desc">Tüm iş ilanlarınızı yönetin ve takip edin</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="size-4 mr-2" />
          Yeni İlan Oluştur
        </Button>
      </div>

      {/* Summary cards */}
      <div className="employer-grid-4">
        {[
          {label: 'Aktif', count: activeCount, color: 'text-success', bg: 'bg-emerald-500/10'},
          {label: 'Duraklatıldı', count: pausedCount, color: 'text-warning', bg: 'bg-amber-500/10'},
          {label: 'Kapandı', count: closedCount, color: 'text-danger', bg: 'bg-red-500/10'},
          {label: 'Toplam', count: jobs.length, color: 'text-primary', bg: 'bg-secondary'},
        ].map((s) => (
          <button
            key={s.label}
            onClick={() => setStatusFilter(s.label === 'Toplam' ? 'all' : s.label === 'Aktif' ? 'active' : s.label === 'Duraklatıldı' ? 'paused' : 'closed')}
            className={cn(
              'rounded-2xl border border-border bg-surface p-4 text-left transition hover:border-border-strong hover:shadow-sm',
              statusFilter === (s.label === 'Toplam' ? 'all' : s.label === 'Aktif' ? 'active' : s.label === 'Duraklatıldı' ? 'paused' : 'closed') && 'ring-2 ring-primary/20'
            )}
          >
            <span className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">{s.label}</span>
            <div className={cn('text-2xl font-bold mt-1', s.color)}>{s.count}</div>
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="İlan veya departman ara..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-10 w-full rounded-2xl border border-border bg-surface pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-4 focus:ring-[var(--ring)]"
          />
        </div>
      </div>

      {/* Table */}
      <div className="surface-card overflow-hidden">
        <table className="data-table">
          <thead>
            <tr>
              <th>Pozisyon</th>
              <th className="hidden md:table-cell">Departman</th>
              <th className="hidden lg:table-cell">Lokasyon</th>
              <th>Durum</th>
              <th className="hidden sm:table-cell">Başvuru</th>
              <th className="hidden md:table-cell">Eşleşme</th>
              <th className="hidden lg:table-cell">Tarih</th>
              <th className="text-right">İşlemler</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((job) => (
              <tr key={job.id}>
                <td>
                  <div className="flex items-center gap-3">
                    <div className="hidden sm:flex size-9 items-center justify-center rounded-xl bg-secondary text-secondary-foreground">
                      <Briefcase className="size-4" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold">{job.title}</div>
                      <div className="text-[11px] text-muted-foreground md:hidden">{job.department}</div>
                    </div>
                  </div>
                </td>
                <td className="hidden md:table-cell text-muted-foreground">{job.department}</td>
                <td className="hidden lg:table-cell">
                  <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                    <MapPin className="size-3" />
                    {job.location}
                  </span>
                </td>
                <td>
                  <StatusBadge status={job.status} />
                </td>
                <td className="hidden sm:table-cell">
                  <span className="inline-flex items-center gap-1 text-sm font-semibold">
                    <Users className="size-3.5 text-muted-foreground" />
                    {job.applicants}
                  </span>
                </td>
                <td className="hidden md:table-cell">
                  <span className={cn(
                    'text-sm font-bold',
                    job.matchAvg >= 85 ? 'text-match-high' : job.matchAvg >= 70 ? 'text-match-mid' : 'text-match-low'
                  )}>
                    %{job.matchAvg}
                  </span>
                </td>
                <td className="hidden lg:table-cell text-muted-foreground">
                  <span className="inline-flex items-center gap-1 text-xs">
                    <Clock className="size-3" />
                    {job.postedAt}
                  </span>
                </td>
                <td className="text-right">
                  <StatusToggle status={job.status} onChange={(s) => handleStatusChange(job.id, s)} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <Search className="size-10 text-muted-foreground/40 mb-3" />
            <p className="text-sm font-medium text-muted-foreground">Sonuç bulunamadı</p>
            <p className="text-xs text-muted-foreground mt-1">Farklı bir arama terimi deneyin</p>
          </div>
        )}
      </div>

      {/* Create Job Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={() => setShowCreateModal(false)}>
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
          <div
            className="relative surface-card w-full max-w-lg p-6 animate-fade-in-up"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setShowCreateModal(false)}
              className="absolute right-4 top-4 flex size-8 items-center justify-center rounded-xl text-muted-foreground hover:bg-surface-muted"
            >
              <X className="size-4" />
            </button>
            <div className="flex items-center gap-3 mb-6">
              <div className="flex size-11 items-center justify-center rounded-2xl bg-secondary text-secondary-foreground">
                <Plus className="size-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold">Yeni İlan Oluştur</h2>
                <p className="text-xs text-muted-foreground">Yeni bir iş ilanı yayınlamak için formu doldurun</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-muted-foreground mb-1.5">Pozisyon Adı</label>
                <input
                  type="text"
                  placeholder="örn. Senior Frontend Developer"
                  className="h-10 w-full rounded-2xl border border-border bg-surface px-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-4 focus:ring-[var(--ring)]"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-muted-foreground mb-1.5">Departman</label>
                  <input
                    type="text"
                    placeholder="örn. Engineering"
                    className="h-10 w-full rounded-2xl border border-border bg-surface px-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-4 focus:ring-[var(--ring)]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-muted-foreground mb-1.5">Lokasyon</label>
                  <input
                    type="text"
                    placeholder="örn. İstanbul (Hybrid)"
                    className="h-10 w-full rounded-2xl border border-border bg-surface px-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-4 focus:ring-[var(--ring)]"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-muted-foreground mb-1.5">İş Açıklaması</label>
                <textarea
                  rows={4}
                  placeholder="Pozisyonun sorumlulukları, gereksinimleri ve beklentileri..."
                  className="w-full rounded-2xl border border-border bg-surface p-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-4 focus:ring-[var(--ring)] resize-none"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <Button className="flex-1" onClick={() => setShowCreateModal(false)}>Oluştur ve Yayınla</Button>
                <Button variant="secondary" onClick={() => setShowCreateModal(false)}>Taslak Kaydet</Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
