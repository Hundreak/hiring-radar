'use client';

import Link from 'next/link';
import {
  ArrowRight,
  BarChart3,
  Briefcase,
  Building2,
  Clock,
  FileText,
  MapPin,
  Plus,
  Search,
  Sparkles,
  Star,
  TrendingUp,
  Upload,
  UserCheck,
  Users,
  Zap,
} from 'lucide-react';
import {useState} from 'react';

import {Button} from '@/components/ui/button';
import {Badge} from '@/components/ui/badge';
import {cn} from '@/lib/utils';

/* ─── Demo data ─── */
const STATS = [
  {label: 'Aktif İlanlar', value: 12, delta: '+3', positive: true, icon: Briefcase},
  {label: 'Toplam Başvuru', value: 248, delta: '+18', positive: true, icon: Users},
  {label: 'Bekleyen Değerlendirme', value: 36, delta: '-5', positive: true, icon: FileText},
  {label: 'Ort. Eşleşme Skoru', value: '84%', delta: '+2.4%', positive: true, icon: TrendingUp},
];

const RECENT_JOBS = [
  {id: 1, title: 'Senior Frontend Developer', department: 'Engineering', location: 'İstanbul (Hybrid)', applicants: 64, matchAvg: 88, status: 'active', postedAt: '2 gün önce'},
  {id: 2, title: 'Backend Engineer (Go)', department: 'Engineering', location: 'Remote', applicants: 42, matchAvg: 82, status: 'active', postedAt: '5 gün önce'},
  {id: 3, title: 'Product Designer', department: 'Design', location: 'İstanbul (Ofis)', applicants: 31, matchAvg: 76, status: 'active', postedAt: '1 hafta önce'},
  {id: 4, title: 'DevOps Engineer', department: 'Infrastructure', location: 'İzmir (Hybrid)', applicants: 19, matchAvg: 91, status: 'paused', postedAt: '2 hafta önce'},
];

const TOP_CANDIDATES = [
  {id: 1, name: 'Ahmet Yılmaz', initials: 'AY', headline: 'Senior React Developer', experience: 6, location: 'İstanbul', matchScore: 96, skills: ['React', 'TypeScript', 'Node.js', 'GraphQL']},
  {id: 2, name: 'Zeynep Kaya', initials: 'ZK', headline: 'Product Designer (UI/UX)', experience: 5, location: 'Ankara', matchScore: 92, skills: ['Figma', 'Design Systems', 'Prototyping']},
  {id: 3, name: 'Mehmet Demir', initials: 'MD', headline: 'Go Backend Engineer', experience: 7, location: 'İzmir', matchScore: 89, skills: ['Go', 'gRPC', 'PostgreSQL', 'Docker']},
  {id: 4, name: 'Selen Çelik', initials: 'SÇ', headline: 'DevOps / SRE', experience: 4, location: 'İstanbul (Remote)', matchScore: 87, skills: ['Kubernetes', 'Terraform', 'AWS', 'CI/CD']},
];

const ACTIVITIES = [
  {id: 1, type: 'application', icon: Users, text: '3 yeni başvuru: Senior Frontend Developer', time: '15 dk önce', color: 'text-primary'},
  {id: 2, type: 'match', icon: Sparkles, text: '2 yeni yüksek eşleşme bulundu', time: '1 sa önce', color: 'text-accent'},
  {id: 3, type: 'review', icon: UserCheck, text: 'CV değerlendirmesi tamamlandı: 12 aday', time: '3 sa önce', color: 'text-success'},
  {id: 4, type: 'job', icon: Briefcase, text: 'Yeni ilan yayına alındı: Backend Engineer', time: '5 sa önce', color: 'text-primary'},
  {id: 5, type: 'match', icon: Zap, text: 'Eşleşme skoru %85+ aday sayısı: 24', time: '1 gün önce', color: 'text-warning'},
];

/* ─── Helpers ─── */
function scoreColorClass(score: number): string {
  if (score >= 85) return 'high';
  if (score >= 60) return 'mid';
  return 'low';
}

/* ─── Components ─── */
function StatCard({stat, index}: {stat: typeof STATS[0]; index: number}) {
  return (
    <div className="stat-card animate-fade-in-up" style={{animationDelay: `${index * 100}ms`}}>
      <div className="flex items-center justify-between">
        <span className="stat-label">{stat.label}</span>
        <div className="flex size-9 items-center justify-center rounded-xl bg-surface-muted">
          <stat.icon className="size-4 text-muted-foreground" />
        </div>
      </div>
      <div className="stat-value">{stat.value}</div>
      <div className={cn('stat-delta', stat.positive ? 'positive' : 'negative')}>
        <TrendingUp className="size-3" />
        {stat.delta} bu ay
      </div>
    </div>
  );
}

function QuickAction({icon: Icon, label, description, href, tone}: {
  icon: React.ElementType;
  label: string;
  description: string;
  href: string;
  tone: 'primary' | 'accent' | 'success';
}) {
  const toneStyles = {
    primary: 'bg-secondary text-secondary-foreground hover:bg-primary/20',
    accent: 'bg-accent-soft text-accent hover:bg-accent/20',
    success: 'bg-emerald-500/10 text-success hover:bg-emerald-500/20',
  };
  return (
    <Link
      href={href}
      className={cn(
        'flex items-center gap-4 rounded-2xl border border-border bg-surface p-5 transition-all duration-200 hover:-translate-y-1 hover:shadow-lg',
        toneStyles[tone]
      )}
    >
      <div className={cn('flex size-12 items-center justify-center rounded-2xl', toneStyles[tone])}>
        <Icon className="size-6" />
      </div>
      <div>
        <div className="text-sm font-semibold text-foreground">{label}</div>
        <div className="text-xs text-muted-foreground mt-0.5">{description}</div>
      </div>
      <ArrowRight className="size-4 ml-auto text-muted-foreground" />
    </Link>
  );
}

export default function EmployerDashboardPage() {
  return (
    <div className="space-y-6">
      {/* Stats row */}
      <div className="employer-grid-4">
        {STATS.map((stat, i) => (
          <StatCard key={stat.label} stat={stat} index={i} />
        ))}
      </div>

      {/* Quick Actions */}
      <div className="employer-grid-3">
        <QuickAction
          icon={Plus}
          label="Yeni İlan Oluştur"
          description="Birkaç adımda yeni iş ilanı yayınlayın"
          href="#"
          tone="primary"
        />
        <QuickAction
          icon={Upload}
          label="CV Yükle"
          description="Aday CV'lerini toplu olarak yükleyin"
          href="#"
          tone="accent"
        />
        <QuickAction
          icon={Search}
          label="Aday Ara"
          description="Veritabanında yetenek arayın"
          href="#"
          tone="success"
        />
      </div>

      {/* Middle section: Recent Jobs + Top Candidates */}
      <div className="employer-grid-2" style={{gridTemplateColumns: '1fr 1fr', gap: '20px'}}>
        {/* Recent Job Postings */}
        <div className="surface-card p-5">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="text-base font-bold">Son İlanlarım</h2>
              <p className="text-xs text-muted-foreground mt-0.5">Son 30 günde yayınlanan ilanlar</p>
            </div>
            <Link
              href="/tr/employer/jobs"
              className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
            >
              Tümünü gör <ArrowRight className="size-3" />
            </Link>
          </div>

          <div className="space-y-3">
            {RECENT_JOBS.map((job) => (
              <div
                key={job.id}
                className="flex items-center gap-4 rounded-2xl border border-border bg-surface p-4 transition hover:border-border-strong hover:shadow-sm"
              >
                <div className="flex size-10 items-center justify-center rounded-xl bg-secondary text-secondary-foreground shrink-0">
                  <Briefcase className="size-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold truncate">{job.title}</span>
                    <Badge
                      tone={job.status === 'active' ? 'success' : job.status === 'paused' ? 'warning' : 'default'}
                      className="text-[10px] px-2 py-0.5 shrink-0"
                    >
                      {job.status === 'active' ? 'Aktif' : job.status === 'paused' ? 'Duraklatıldı' : 'Kapalı'}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                    <span className="inline-flex items-center gap-1">
                      <MapPin className="size-3" />
                      {job.location}
                    </span>
                    <span className="inline-flex items-center gap-1">
                      <Users className="size-3" />
                      {job.applicants} başvuru
                    </span>
                    <span className="inline-flex items-center gap-1">
                      <Clock className="size-3" />
                      {job.postedAt}
                    </span>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <div className={`text-sm font-bold text-match-${scoreColorClass(job.matchAvg)}`}>
                    %{job.matchAvg}
                  </div>
                  <div className="text-[10px] text-muted-foreground">eşleşme</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Candidates */}
        <div className="surface-card p-5">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="text-base font-bold">Öne Çıkan Adaylar</h2>
              <p className="text-xs text-muted-foreground mt-0.5">En yüksek eşleşme skoruna sahip adaylar</p>
            </div>
            <Link
              href="/tr/employer/candidates"
              className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
            >
              Tümünü gör <ArrowRight className="size-3" />
            </Link>
          </div>

          <div className="space-y-3">
            {TOP_CANDIDATES.map((c) => (
              <Link key={c.id} href={`/tr/employer/candidates/${c.id}`}>
                <div className="candidate-card flex items-center gap-4">
                  <div className="candidate-avatar">{c.initials}</div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold">{c.name}</span>
                    </div>
                    <div className="text-xs text-muted-foreground">{c.headline}</div>
                    <div className="flex flex-wrap gap-1 mt-1.5">
                      {c.skills.slice(0, 3).map((s) => (
                        <span key={s} className="skill-chip match">{s}</span>
                      ))}
                      {c.skills.length > 3 && (
                        <span className="skill-chip text-muted-foreground bg-surface-muted">+{c.skills.length - 3}</span>
                      )}
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <div
                      className={cn(
                        'match-score-ring text-white',
                        scoreColorClass(c.matchScore)
                      )}
                    >
                      <span className="text-white">{c.matchScore}</span>
                    </div>
                    <div className="text-[10px] text-muted-foreground mt-1">skor</div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom section: Activity Timeline + Charts */}
      <div className="employer-grid-2" style={{gridTemplateColumns: '360px minmax(0, 1fr)', gap: '20px'}}>
        {/* Activity Timeline */}
        <div className="surface-card p-5">
          <h2 className="text-base font-bold mb-5">Son Aktiviteler</h2>
          <div>
            {ACTIVITIES.map((a) => (
              <div key={a.id} className="timeline-item">
                <div className="timeline-dot">
                  <a.icon className={cn('size-3.5', a.color)} />
                </div>
                <div className="min-w-0 pt-0.5">
                  <p className="text-[13px] leading-snug text-foreground">{a.text}</p>
                  <p className="text-[11px] text-muted-foreground mt-0.5">{a.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Chart Placeholders */}
        <div className="employer-grid-2" style={{gap: '16px'}}>
          <div className="surface-card p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold">Başvuru Trendi</h3>
              <Badge tone="info" className="text-[10px]">Son 30 gün</Badge>
            </div>
            <div className="chart-placeholder">
              <div className="text-center">
                <BarChart3 className="size-8 text-muted-foreground mx-auto mb-2 opacity-50" />
                <p className="text-xs text-muted-foreground">Grafik alanı — Başvuru trendi</p>
              </div>
            </div>
          </div>

          <div className="surface-card p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold">Pozisyon Bazlı Dağılım</h3>
              <Badge tone="info" className="text-[10px]">Aktif</Badge>
            </div>
            <div className="chart-placeholder">
              <div className="text-center">
                <div className="flex items-end justify-center gap-2 h-16 mb-2">
                  {[40, 65, 35, 80, 55, 70, 45].map((h, i) => (
                    <div
                      key={i}
                      className="w-4 rounded-t-md"
                      style={{
                        height: `${h}%`,
                        background: i === 3 ? 'var(--primary)' : 'var(--surface-strong)',
                        border: `1px solid ${i === 3 ? 'var(--primary)' : 'var(--border)'}`,
                      }}
                    />
                  ))}
                </div>
                <p className="text-xs text-muted-foreground">Pozisyon bazlı başvuru dağılımı</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Match Score Distribution */}
      <div className="surface-card p-5">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-base font-bold">Eşleşme Skoru Dağılımı</h2>
            <p className="text-xs text-muted-foreground mt-0.5">Tüm adayların eşleşme skoru aralıkları</p>
          </div>
          <Link
            href="/tr/employer/matches"
            className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
          >
            Detaylı analiz <ArrowRight className="size-3" />
          </Link>
        </div>
        <div className="grid grid-cols-5 gap-4">
          {[
            {range: '90-100%', count: 12, label: 'Mükemmel', color: 'var(--match-high)'},
            {range: '80-89%', count: 28, label: 'Çok İyi', color: 'var(--match-mid)'},
            {range: '70-79%', count: 45, label: 'İyi', color: 'var(--primary)'},
            {range: '60-69%', count: 38, label: 'Orta', color: 'var(--warning)'},
            {range: '< 60%', count: 125, label: 'Geliştirilebilir', color: 'var(--match-miss)'},
          ].map((d) => (
            <div key={d.range} className="text-center p-4 rounded-2xl border border-border bg-surface-muted transition hover:border-border-strong">
              <div className="text-xl font-bold" style={{color: d.color}}>{d.count}</div>
              <div className="text-[11px] font-semibold text-foreground mt-1">{d.range}</div>
              <div className="text-[10px] text-muted-foreground">{d.label}</div>
              <div className="match-bar-bg mt-3 mx-auto max-w-[80px]">
                <div
                  className="match-bar-fill high"
                  style={{width: `${Math.min(100, (d.count / 45) * 100)}%`, background: d.color}}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
