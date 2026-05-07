'use client';

import {
  BarChart3,
  Briefcase,
  Clock,
  Eye,
  MapPin,
  TrendingUp,
  Users,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import {useState} from 'react';

import {Badge} from '@/components/ui/badge';
import {Button} from '@/components/ui/button';
import {cn} from '@/lib/utils';

const ANALYTICS_DATA = {
  totalApplicants: 248,
  applicantsChange: '+18%',
  applicantsPositive: true,
  avgMatchScore: 84,
  matchChange: '+2.4%',
  matchPositive: true,
  timeToHire: 18,
  timeChange: '-3 gün',
  timePositive: true,
  conversionRate: 12.5,
  conversionChange: '+1.2%',
  conversionPositive: true,
};

const POSITION_PERFORMANCE = [
  {position: 'Senior Frontend Developer', applicants: 64, views: 342, matchAvg: 88, conversion: 15.6, trend: 'up'},
  {position: 'Backend Engineer (Go)', applicants: 42, views: 218, matchAvg: 82, conversion: 11.9, trend: 'up'},
  {position: 'Product Designer', applicants: 31, views: 156, matchAvg: 76, conversion: 9.7, trend: 'down'},
  {position: 'DevOps Engineer', applicants: 19, views: 98, matchAvg: 91, conversion: 21.1, trend: 'up'},
  {position: 'QA Automation Engineer', applicants: 15, views: 76, matchAvg: 85, conversion: 13.3, trend: 'up'},
];

const SOURCE_BREAKDOWN = [
  {source: 'Doğrudan Başvuru', count: 98, percentage: 39.5, color: 'var(--primary)'},
  {source: 'LinkedIn', count: 62, percentage: 25.0, color: 'var(--accent)'},
  {source: 'Referans', count: 38, percentage: 15.3, color: 'var(--success)'},
  {source: 'İş İlanı Platformu', count: 32, percentage: 12.9, color: 'var(--warning)'},
  {source: 'Diğer', count: 18, percentage: 7.3, color: 'var(--muted-foreground)'},
];

const WEEKLY_APPLICATIONS = [32, 45, 38, 52, 41, 28, 12]; // Mon-Sun

function StatCard({label, value, change, positive, icon: Icon, delay}: {
  label: string; value: string; change: string; positive: boolean; icon: React.ElementType; delay: number;
}) {
  return (
    <div className="stat-card animate-fade-in-up" style={{animationDelay: `${delay}ms`}}>
      <div className="flex items-center justify-between mb-3">
        <span className="stat-label">{label}</span>
        <div className="flex size-9 items-center justify-center rounded-xl bg-surface-muted">
          <Icon className="size-4 text-muted-foreground" />
        </div>
      </div>
      <div className="stat-value">{value}</div>
      <div className={cn('stat-delta', positive ? 'positive' : 'negative')}>
        {positive ? <ArrowUpRight className="size-3" /> : <ArrowDownRight className="size-3" />}
        {change} bu ay
      </div>
    </div>
  );
}

export default function EmployerAnalyticsPage() {
  const [period, setPeriod] = useState<'7d' | '30d' | '90d'>('30d');

  const periodLabels = { '7d': 'Son 7 Gün', '30d': 'Son 30 Gün', '90d': 'Son 90 Gün' };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="employer-page-title">Analiz</h1>
          <p className="employer-page-desc">İşveren performans metrikleri ve detaylı analizler</p>
        </div>
        <div className="inline-flex items-center gap-1 rounded-xl border border-border bg-surface p-1">
          {(['7d', '30d', '90d'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={cn(
                'rounded-lg px-3 py-1.5 text-xs font-semibold transition',
                period === p ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'
              )}
            >
              {periodLabels[p]}
            </button>
          ))}
        </div>
      </div>

      {/* Stat cards */}
      <div className="employer-grid-4">
        <StatCard label="Toplam Başvuru" value={String(ANALYTICS_DATA.totalApplicants)} change={ANALYTICS_DATA.applicantsChange} positive={ANALYTICS_DATA.applicantsPositive} icon={Users} delay={0} />
        <StatCard label="Ort. Eşleşme Skoru" value={`%${ANALYTICS_DATA.avgMatchScore}`} change={ANALYTICS_DATA.matchChange} positive={ANALYTICS_DATA.matchPositive} icon={TrendingUp} delay={100} />
        <StatCard label="Ort. İşe Alım Süresi" value={`${ANALYTICS_DATA.timeToHire} gün`} change={ANALYTICS_DATA.timeChange} positive={ANALYTICS_DATA.timePositive} icon={Clock} delay={200} />
        <StatCard label="Dönüşüm Oranı" value={`%${ANALYTICS_DATA.conversionRate}`} change={ANALYTICS_DATA.conversionChange} positive={ANALYTICS_DATA.conversionPositive} icon={BarChart3} delay={300} />
      </div>

      {/* Charts row */}
      <div className="employer-grid-2" style={{gap: '20px'}}>
        {/* Weekly bar chart */}
        <div className="surface-card p-5">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="text-sm font-bold">Haftalık Başvurular</h2>
              <p className="text-xs text-muted-foreground mt-0.5">Son 7 gün başvuru akışı</p>
            </div>
            <Badge tone="info" className="text-[10px]">{periodLabels[period]}</Badge>
          </div>
          <div className="flex items-end justify-between gap-2 h-48 pt-4">
            {WEEKLY_APPLICATIONS.map((count, i) => {
              const max = Math.max(...WEEKLY_APPLICATIONS);
              const height = (count / max) * 100;
              const days = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'];
              return (
                <div key={i} className="flex flex-col items-center flex-1 gap-2">
                  <span className="text-[11px] font-bold text-foreground">{count}</span>
                  <div className="w-full flex items-end justify-center" style={{height: '120px'}}>
                    <div
                      className="w-full max-w-[40px] rounded-t-lg transition-all duration-500"
                      style={{
                        height: `${height}%`,
                        background: i === 3
                          ? 'linear-gradient(180deg, var(--primary), var(--accent))'
                          : 'var(--surface-strong)',
                        border: `1px solid ${i === 3 ? 'transparent' : 'var(--border)'}`,
                      }}
                    />
                  </div>
                  <span className="text-[10px] text-muted-foreground font-medium">{days[i]}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Source Breakdown */}
        <div className="surface-card p-5">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="text-sm font-bold">Başvuru Kaynakları</h2>
              <p className="text-xs text-muted-foreground mt-0.5">Adayların başvuru kanalları</p>
            </div>
          </div>
          <div className="space-y-3">
            {SOURCE_BREAKDOWN.map((source) => (
              <div key={source.source}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[12px] font-medium text-foreground">{source.source}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-bold">{source.count}</span>
                    <span className="text-[10px] text-muted-foreground">({source.percentage}%)</span>
                  </div>
                </div>
                <div className="match-bar-bg">
                  <div
                    className="match-bar-fill high"
                    style={{width: `${source.percentage}%`, background: source.color}}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Position Performance Table */}
      <div className="surface-card p-5">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-sm font-bold">Pozisyon Performansı</h2>
            <p className="text-xs text-muted-foreground mt-0.5">İlan bazlı başvuru ve dönüşüm metrikleri</p>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Pozisyon</th>
                <th className="text-right">Başvuru</th>
                <th className="text-right">Görüntülenme</th>
                <th className="text-right">Eşleşme</th>
                <th className="text-right">Dönüşüm</th>
                <th className="text-right">Trend</th>
              </tr>
            </thead>
            <tbody>
              {POSITION_PERFORMANCE.map((pos) => (
                <tr key={pos.position}>
                  <td>
                    <div className="flex items-center gap-3">
                      <div className="flex size-9 items-center justify-center rounded-xl bg-secondary text-secondary-foreground">
                        <Briefcase className="size-4" />
                      </div>
                      <span className="text-sm font-semibold">{pos.position}</span>
                    </div>
                  </td>
                  <td className="text-right text-sm font-bold">{pos.applicants}</td>
                  <td className="text-right text-sm text-muted-foreground">
                    <span className="inline-flex items-center gap-1">
                      <Eye className="size-3" />
                      {pos.views}
                    </span>
                  </td>
                  <td className="text-right">
                    <span className={cn(
                      'text-sm font-bold',
                      pos.matchAvg >= 85 ? 'text-match-high' : pos.matchAvg >= 75 ? 'text-match-mid' : 'text-match-low'
                    )}>
                      %{pos.matchAvg}
                    </span>
                  </td>
                  <td className="text-right text-sm font-medium">%{pos.conversion}</td>
                  <td className="text-right">
                    {pos.trend === 'up' ? (
                      <span className="inline-flex items-center gap-1 text-xs text-success font-semibold">
                        <TrendingUp className="size-3" />
                        Yükseliş
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-xs text-warning font-semibold">
                        <TrendingUp className="size-3 rotate-180" />
                        Düşüş
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Match Score Distribution mini */}
      <div className="surface-card p-5">
        <h2 className="text-sm font-bold mb-4">Eşleşme Skoru Dağılımı</h2>
        <div className="grid grid-cols-5 gap-4">
          {[
            {range: '90-100%', count: 12, color: 'var(--match-high)'},
            {range: '80-89%', count: 28, color: 'var(--match-mid)'},
            {range: '70-79%', count: 45, color: 'var(--primary)'},
            {range: '60-69%', count: 38, color: 'var(--warning)'},
            {range: '< 60%', count: 125, color: 'var(--match-miss)'},
          ].map((d) => (
            <div key={d.range} className="text-center p-4 rounded-2xl border border-border bg-surface-muted">
              <div className="text-xl font-bold" style={{color: d.color}}>{d.count}</div>
              <div className="text-[11px] font-semibold text-foreground mt-1">{d.range}</div>
              <div className="match-bar-bg mt-3 mx-auto max-w-[60px]">
                <div className="match-bar-fill high" style={{width: `${Math.min(100, (d.count / 45) * 100)}%`, background: d.color}} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
