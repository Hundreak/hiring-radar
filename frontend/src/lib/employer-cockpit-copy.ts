import {normalizeEmployerLanguage} from './employer-copy';
import type {
  EmployerActivity,
  EmployerCandidateOpportunity,
  EmployerJobSummary,
  EmployerMetric,
  EmployerPipelineStage,
  HiringHealthScore,
} from '@/types/employer';

export type EmployerCockpitCopy = ReturnType<typeof getEmployerCockpitCopy>;

export function getEmployerCockpitCopy(locale: string) {
  const lang = normalizeEmployerLanguage(locale);
  return lang === 'tr' ? trCockpitCopy : enCockpitCopy;
}

export function localizeDashboardMetric(metric: EmployerMetric, locale: string): EmployerMetric {
  const copy = getEmployerCockpitCopy(locale).metrics[metric.id];
  if (!copy) return metric;
  return {
    ...metric,
    label: copy.label,
    helperText: copy.helperText,
  };
}

export function localizeHiringHealth(health: HiringHealthScore, locale: string): HiringHealthScore {
  const copy = getEmployerCockpitCopy(locale).hiringHealth;
  return {
    ...health,
    label: copy.label,
    summary: copy.summary,
    change: copy.change,
    drivers: health.drivers.map((driver) => ({
      ...driver,
      label: copy.drivers[driver.id]?.label ?? driver.label,
      description: copy.drivers[driver.id]?.description ?? driver.description,
    })),
  };
}

export function localizePipelineStage(stage: EmployerPipelineStage, locale: string): EmployerPipelineStage {
  const copy = getEmployerCockpitCopy(locale).pipeline.stages[stage.id];
  if (!copy) return stage;
  return {
    ...stage,
    label: copy.label,
    description: copy.description,
  };
}

export function localizeDashboardActivity(activity: EmployerActivity, locale: string): EmployerActivity {
  const copy = getEmployerCockpitCopy(locale).activity.items[activity.id];
  if (!copy) return activity;
  return {
    ...activity,
    title: copy.title,
    description: copy.description,
    time: copy.time,
  };
}

export function localizeDashboardCandidate(candidate: EmployerCandidateOpportunity, locale: string): EmployerCandidateOpportunity {
  const copy = getEmployerCockpitCopy(locale).candidates.items[candidate.publicId] ?? getEmployerCockpitCopy(locale).candidates.items[String(candidate.id)];
  if (!copy) return candidate;
  return {
    ...candidate,
    headline: copy.headline ?? candidate.headline,
    location: copy.location ?? candidate.location,
    recommendedAction: copy.recommendedAction ?? candidate.recommendedAction,
    highlights: copy.highlights ?? candidate.highlights,
    risks: copy.risks ?? candidate.risks,
  };
}

export function localizeDashboardJob(job: EmployerJobSummary, locale: string): EmployerJobSummary {
  const copy = getEmployerCockpitCopy(locale).jobs.items[job.slug];
  if (!copy) return job;
  return {
    ...job,
    department: copy.department ?? job.department,
    location: copy.location ?? job.location,
    postedAt: copy.postedAt ?? job.postedAt,
    riskReasons: copy.riskReasons ?? job.riskReasons,
  };
}

const trCockpitCopy = {
  hero: {
    versionBadge: 'İşveren İşletim Merkezi · Kokpit v1',
    eyebrow: 'Bugünkü işe alım kontrol merkezi',
    titlePrefix: 'İşe alım radarınız bugün',
    titleHighlight: '6 aksiyon',
    titleSuffix: 'öneriyor.',
    description:
      'Kritik adayları, riskteki ilanları ve süreç darboğazlarını tek ekranda görün. Bu panel rapor değil; günün işe alım kararlarını netleştiren operasyon kokpiti.',
  },
  quickActions: {
    'create-job': {
      label: 'Yeni ilan oluştur',
      description: 'Yapay zekâ destekli ilan stüdyosu ile birkaç dakikada yayına çıkın',
    },
    'bulk-cv-upload': {
      label: 'CV yükle',
      description: 'Toplu CV ayrıştırıp otomatik uyum puanı üretin',
    },
    'talent-search': {
      label: 'Aday ara',
      description: 'Yetenek Radarı ile aktif ve pasif adayları keşfedin',
    },
  },
  pulse: {
    eyebrow: 'Haftalık nabız',
    applications: 'başvuru',
    qualified: 'nitelikli aday',
    qualityRate: 'kalite oranı',
    trend: 'son 30 gün',
  },
  metrics: {
    'active-jobs': {label: 'Aktif ilan', helperText: 'Bu ay açılan yeni roller dahil'},
    'total-applications': {label: 'Toplam başvuru', helperText: 'Son 30 gün başvuru hacmi'},
    'pending-review': {label: 'Bekleyen değerlendirme', helperText: '48 saat içinde incelenmeli'},
    'avg-match-score': {label: 'Ortalama uyum puanı', helperText: 'Nitelikli aday ortalaması'},
  } as Record<string, {label: string; helperText: string}>,
  metricTrend: {thisMonth: 'bu ay'},
  hiringHealth: {
    eyebrow: 'İşe alım sağlığı',
    label: 'İyi ama hız riski var',
    summary: 'Aday kalitesi yükseliyor; ancak bekleyen değerlendirmeler ve maaş şeffaflığı iki rolde dönüşümü baskılıyor.',
    change: '+6 puan',
    thisWeek: 'bu hafta',
    drivers: {
      'candidate-quality': {label: 'Aday kalitesi', description: 'Yüksek puanlı aday oranı geçen aya göre arttı.'},
      'review-speed': {label: 'Değerlendirme hızı', description: '36 aday 48 saatten uzun süredir bekliyor.'},
      'job-quality': {label: 'İlan kalitesi', description: 'Maaş şeffaflığı eklenen ilanlarda dönüşüm daha yüksek.'},
    } as Record<string, {label: string; description: string}>,
  },
  ai: {
    eyebrow: 'Yapay zekâ destekli yardımcı',
    confidenceLabel: 'Güven',
    seeRisks: 'Riskleri gör',
    humanApprovalRequired: 'İnsan onayı gerekir',
    insights: {
      'frontend-shortlist-delay': {
        title: 'Senior Frontend rolünde hızlı aksiyon fırsatı',
        description: '3 yüksek puanlı aday 48 saattir bekliyor. Bugün dönüş yapılırsa yanıt olasılığı daha yüksek.',
        actionLabel: 'Kısa listeyi aç',
        evidence: ['3 aday ≥ %92 puan', '2 aday son 24 saatte aktif', 'Maaş beklentileri rol bandına yakın'],
      },
      'salary-transparency-warning': {
        title: 'Maaş bandı görünürlüğü dönüşümü artırabilir',
        description: 'Maaş bandı gizli iki ilanda görüntüleme iyi fakat nitelikli başvuru oranı düşük.',
        actionLabel: 'İlanları iyileştir',
        evidence: ['Senior Frontend kalite puanı: 76', 'Technical Lead kalite puanı: 74', 'Başvuru-kalite farkı %31'],
      },
    } as Record<string, {title: string; description: string; actionLabel: string; evidence: string[]}>,
  },
  jobs: {
    eyebrow: 'Risk ve fırsat',
    title: 'Riskteki ilanlar',
    description: 'Başvuru kalitesi, dönüşüm ve bekleyen aday sinyallerine göre önceliklendirilmiş liste.',
    viewAll: 'Tüm ilanlar',
    applicants: 'Başvuru',
    qualified: 'Nitelikli',
    conversion: 'Dönüşüm',
    quality: 'Kalite',
    avgMatch: 'ort. uyum',
    risks: {
      healthy: 'Sağlıklı',
      watch: 'Takipte',
      risk: 'Riskli',
      critical: 'Kritik',
    },
    items: {
      'senior-frontend-developer': {
        department: 'Mühendislik',
        location: 'İstanbul (Hibrit)',
        postedAt: '2 gün önce',
        riskReasons: ['Maaş bandı gizli', '3 güçlü aday 48 saattir bekliyor', 'Zorunlu kriter sayısı yüksek'],
      },
      'product-designer': {
        department: 'Tasarım',
        location: 'İstanbul (Ofis)',
        postedAt: '1 hafta önce',
        riskReasons: ['Ofis zorunluluğu aday havuzunu daraltıyor', 'Portfolyo beklentisi yeterince açık değil'],
      },
      'devops-engineer': {
        department: 'Altyapı',
        location: 'İzmir (Hibrit)',
        postedAt: '2 hafta önce',
        riskReasons: ['İlan duraklatılmış', 'Aday kalitesi yüksek ama hacim düşük'],
      },
      'technical-lead': {
        department: 'Mühendislik',
        location: 'İstanbul (Hibrit)',
        postedAt: '1 hafta önce',
        riskReasons: ['Liderlik beklentisi ve uygulamalı teknik katkı oranı daha net olmalı'],
      },
    } as Record<string, {department?: string; location?: string; postedAt?: string; riskReasons?: string[]}>,
  },
  candidates: {
    eyebrow: 'Aday fırsatları',
    title: 'Kaçırılmaması gereken adaylar',
    description: 'Aktivite, niyet ve uyum sinyallerine göre bugünkü en güçlü aday fırsatları.',
    viewAll: 'Tüm adaylar',
    match: 'Uyum',
    years: 'yıl',
    recommendedAction: 'Önerilen aksiyon',
    signal: 'Yüksek niyetli adayları 24 saat içinde yanıtlayarak görüşme oranını artırabilirsiniz.',
    signalBadge: 'Sıcak fırsat',
    availability: {
      immediate: 'Hemen',
      two_weeks: '2 hafta',
      one_month: '1 ay',
      passive: 'Pasif',
    },
    items: {
      'cand-ahmet-yilmaz': {
        headline: 'Senior React Developer',
        location: 'İstanbul',
        recommendedAction: 'Bugün teknik ön görüşmeye davet et',
      },
      'cand-zeynep-kaya': {
        headline: 'Ürün Tasarımcısı (UI/UX)',
        location: 'Ankara',
        recommendedAction: 'Uzaktan/hibrit esneklikle görüşmeye al',
      },
      'cand-mehmet-demir': {
        headline: 'Go Backend Engineer',
        location: 'İzmir',
        recommendedAction: 'Backend teknik görüşme setini gönder',
      },
      'cand-selen-celik': {
        headline: 'DevOps / SRE',
        location: 'İstanbul',
        recommendedAction: 'Uzaktan çalışma opsiyonuyla kişiselleştirilmiş davet gönder',
      },
    } as Record<string, {headline?: string; location?: string; recommendedAction?: string; highlights?: string[]; risks?: string[]}>,
  },
  pipeline: {
    eyebrow: 'Süreç',
    title: 'Aday akış özeti',
    description: 'Darboğazları ve geciken adayları aşama bazında yakalayın.',
    openPipeline: 'Süreci aç',
    overdueTitle: (count: number) => `${count} aday hedef sürenin üzerinde bekliyor`,
    overdueDescription: 'Ön eleme ve başvuru aşamalarında hız riski var.',
    slaRisk: 'Hedef süre riski',
    conversion: 'geçiş',
    delayed: 'gecikti',
    stages: {
      applied: {label: 'Başvurdu', description: 'Yeni gelen adaylar'},
      screening: {label: 'Ön eleme', description: 'CV ve profil değerlendirme'},
      interview: {label: 'Görüşme', description: 'Teknik / kültür görüşmesi'},
      offer: {label: 'Teklif', description: 'Teklif süreci'},
      hired: {label: 'İşe alındı', description: 'Tamamlanan işe alımlar'},
    } as Record<string, {label: string; description: string}>,
  },
  activity: {
    eyebrow: 'Aktivite',
    title: 'Son sinyaller',
    description: 'Aday, ilan ve yapay zekâ değerlendirme akışındaki son hareketler.',
    auditNote: 'Yapay zekâ önerileri ve önemli aksiyonlar denetim kaydına yazılacak şekilde tasarlanıyor.',
    auditReady: 'Denetim hazır',
    items: {
      'activity-new-applications': {
        title: '3 yeni başvuru geldi',
        description: 'Senior Frontend Developer rolüne yeni başvurular var.',
        time: '15 dk önce',
      },
      'activity-new-high-matches': {
        title: '2 yeni yüksek uyum bulundu',
        description: 'Yetenek Radarı, Backend Engineer rolü için güçlü adaylar yakaladı.',
        time: '1 sa önce',
      },
      'activity-cv-review-complete': {
        title: 'CV değerlendirmesi tamamlandı',
        description: '12 aday için otomatik özet ve uyum kırılımı hazırlandı.',
        time: '3 sa önce',
      },
      'activity-job-published': {
        title: 'Yeni ilan yayına alındı',
        description: 'Backend Engineer (Go) ilanı yayında.',
        time: '5 sa önce',
      },
      'activity-match-threshold': {
        title: '%85+ uyum eşiği aşıldı',
        description: '24 aday yüksek uyum segmentinde.',
        time: '1 gün önce',
      },
    } as Record<string, {title: string; description: string; time: string}>,
  },
};

const enCockpitCopy = {
  hero: {
    versionBadge: 'Employer Operating System · Cockpit v1',
    eyebrow: 'Today’s hiring command center',
    titlePrefix: 'Your hiring radar recommends',
    titleHighlight: '6 actions',
    titleSuffix: 'today.',
    description:
      'See critical candidates, at-risk jobs and process bottlenecks in one workspace. This is not a report; it is an operating cockpit for today’s hiring decisions.',
  },
  quickActions: {
    'create-job': {
      label: 'Create new job',
      description: 'Launch a role in minutes with the AI-assisted job studio',
    },
    'bulk-cv-upload': {
      label: 'Upload CVs',
      description: 'Parse CVs in bulk and generate automatic fit scores',
    },
    'talent-search': {
      label: 'Search candidates',
      description: 'Discover active and passive candidates with Talent Radar',
    },
  },
  pulse: {
    eyebrow: 'Weekly pulse',
    applications: 'applications',
    qualified: 'qualified candidates',
    qualityRate: 'quality rate',
    trend: 'last 30 days',
  },
  metrics: {
    'active-jobs': {label: 'Active jobs', helperText: 'Including roles opened this month'},
    'total-applications': {label: 'Total applications', helperText: 'Application volume over the last 30 days'},
    'pending-review': {label: 'Pending review', helperText: 'Should be reviewed within 48 hours'},
    'avg-match-score': {label: 'Average fit score', helperText: 'Average across qualified candidates'},
  } as Record<string, {label: string; helperText: string}>,
  metricTrend: {thisMonth: 'this month'},
  hiringHealth: {
    eyebrow: 'Hiring health',
    label: 'Good, but speed risk remains',
    summary: 'Candidate quality is improving, but pending reviews and missing salary transparency are suppressing conversion in two roles.',
    change: '+6 points',
    thisWeek: 'this week',
    drivers: {
      'candidate-quality': {label: 'Candidate quality', description: 'Share of high-scoring candidates increased versus last month.'},
      'review-speed': {label: 'Review speed', description: '36 candidates have been waiting longer than 48 hours.'},
      'job-quality': {label: 'Job quality', description: 'Roles with visible salary ranges convert better.'},
    } as Record<string, {label: string; description: string}>,
  },
  ai: {
    eyebrow: 'AI-assisted copilot',
    confidenceLabel: 'Confidence',
    seeRisks: 'View risks',
    humanApprovalRequired: 'Human approval required',
    insights: {
      'frontend-shortlist-delay': {
        title: 'Fast-action opportunity for the Senior Frontend role',
        description: '3 high-scoring candidates have been waiting for 48 hours. Responding today may improve reply probability.',
        actionLabel: 'Open shortlist',
        evidence: ['3 candidates ≥ 92% score', '2 candidates active in the last 24 hours', 'Salary expectations close to the role band'],
      },
      'salary-transparency-warning': {
        title: 'Salary visibility could improve conversion',
        description: 'Two roles with hidden salary bands have strong views but low qualified application rates.',
        actionLabel: 'Optimize jobs',
        evidence: ['Senior Frontend quality score: 76', 'Technical Lead quality score: 74', 'Application-to-quality gap: 31%'],
      },
    } as Record<string, {title: string; description: string; actionLabel: string; evidence: string[]}>,
  },
  jobs: {
    eyebrow: 'Risk & opportunity',
    title: 'At-risk jobs',
    description: 'Prioritized by application quality, conversion and pending candidate signals.',
    viewAll: 'View all jobs',
    applicants: 'Applicants',
    qualified: 'Qualified',
    conversion: 'Conversion',
    quality: 'Quality',
    avgMatch: 'avg. fit',
    risks: {
      healthy: 'Healthy',
      watch: 'Watch',
      risk: 'At risk',
      critical: 'Critical',
    },
    items: {
      'senior-frontend-developer': {
        department: 'Engineering',
        location: 'Istanbul (Hybrid)',
        postedAt: '2 days ago',
        riskReasons: ['Salary band is hidden', '3 strong candidates have waited for 48 hours', 'Too many must-have criteria'],
      },
      'product-designer': {
        department: 'Design',
        location: 'Istanbul (Office)',
        postedAt: '1 week ago',
        riskReasons: ['Office requirement narrows the talent pool', 'Portfolio expectations are not clear enough'],
      },
      'devops-engineer': {
        department: 'Infrastructure',
        location: 'Izmir (Hybrid)',
        postedAt: '2 weeks ago',
        riskReasons: ['Job is paused', 'Candidate quality is high but volume is low'],
      },
      'technical-lead': {
        department: 'Engineering',
        location: 'Istanbul (Hybrid)',
        postedAt: '1 week ago',
        riskReasons: ['Leadership scope and hands-on technical contribution should be clearer'],
      },
    } as Record<string, {department?: string; location?: string; postedAt?: string; riskReasons?: string[]}>,
  },
  candidates: {
    eyebrow: 'Candidate opportunities',
    title: 'Candidates you should not miss',
    description: 'Today’s strongest opportunities based on activity, intent and fit signals.',
    viewAll: 'View all candidates',
    match: 'Fit',
    years: 'yrs',
    recommendedAction: 'Recommended action',
    signal: 'Replying to high-intent candidates within 24 hours can improve interview conversion.',
    signalBadge: 'Hot opportunity',
    availability: {
      immediate: 'Immediate',
      two_weeks: '2 weeks',
      one_month: '1 month',
      passive: 'Passive',
    },
    items: {
      'cand-ahmet-yilmaz': {
        headline: 'Senior React Developer',
        location: 'Istanbul',
        recommendedAction: 'Invite to a technical intro today',
      },
      'cand-zeynep-kaya': {
        headline: 'Product Designer (UI/UX)',
        location: 'Ankara',
        recommendedAction: 'Move forward with remote/hybrid flexibility',
      },
      'cand-mehmet-demir': {
        headline: 'Go Backend Engineer',
        location: 'Izmir',
        recommendedAction: 'Send the backend technical interview pack',
      },
      'cand-selen-celik': {
        headline: 'DevOps / SRE',
        location: 'Istanbul',
        recommendedAction: 'Send a personalized invite with a remote option',
      },
    } as Record<string, {headline?: string; location?: string; recommendedAction?: string; highlights?: string[]; risks?: string[]}>,
  },
  pipeline: {
    eyebrow: 'Pipeline',
    title: 'Candidate flow summary',
    description: 'Spot bottlenecks and overdue candidates by stage.',
    openPipeline: 'Open pipeline',
    overdueTitle: (count: number) => `${count} candidates are waiting beyond the target time`,
    overdueDescription: 'Screening and application review stages create speed risk.',
    slaRisk: 'SLA risk',
    conversion: 'conversion',
    delayed: 'overdue',
    stages: {
      applied: {label: 'Applied', description: 'New incoming candidates'},
      screening: {label: 'Screening', description: 'CV and profile review'},
      interview: {label: 'Interview', description: 'Technical / culture interview'},
      offer: {label: 'Offer', description: 'Offer process'},
      hired: {label: 'Hired', description: 'Completed hires'},
    } as Record<string, {label: string; description: string}>,
  },
  activity: {
    eyebrow: 'Activity',
    title: 'Latest signals',
    description: 'Recent movement across candidates, jobs and AI-assisted evaluations.',
    auditNote: 'AI recommendations and key actions are designed to be written to the audit log.',
    auditReady: 'Audit ready',
    items: {
      'activity-new-applications': {
        title: '3 new applications received',
        description: 'New applications arrived for the Senior Frontend Developer role.',
        time: '15 min ago',
      },
      'activity-new-high-matches': {
        title: '2 new high-fit candidates found',
        description: 'Talent Radar found strong candidates for the Backend Engineer role.',
        time: '1 hr ago',
      },
      'activity-cv-review-complete': {
        title: 'CV review completed',
        description: 'Automatic summaries and fit breakdowns are ready for 12 candidates.',
        time: '3 hrs ago',
      },
      'activity-job-published': {
        title: 'New job published',
        description: 'Backend Engineer (Go) is now live.',
        time: '5 hrs ago',
      },
      'activity-match-threshold': {
        title: '85%+ fit threshold reached',
        description: '24 candidates are in the high-fit segment.',
        time: '1 day ago',
      },
    } as Record<string, {title: string; description: string; time: string}>,
  },
};
