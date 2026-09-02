import type {LucideIcon} from 'lucide-react';
import {
  BarChart3,
  BriefcaseBusiness,
  Building2,
  CalendarDays,
  ClipboardCheck,
  Gauge,
  Languages,
  LifeBuoy,
  Megaphone,
  Radar,
  Scale,
  Settings,
  ShieldCheck,
  Sparkles,
  UsersRound,
} from 'lucide-react';

export type EmployerLanguage = 'tr' | 'en';

export type EmployerNavItem = {
  label: string;
  description: string;
  href: string;
  icon: LucideIcon;
  badge?: string;
  disabled?: boolean;
};

export type EmployerNavSection = {
  title: string;
  items: EmployerNavItem[];
};

type QuickAction = {
  label: string;
  description: string;
  href: string;
  icon: LucideIcon;
};

type CompanyProfileCopy = {
  heroEyebrow: string;
  title: string;
  description: string;
  primaryAction: string;
  secondaryAction: string;
  readinessLabel: string;
  publicPreview: string;
  trustSignals: string;
  contentQuality: string;
  candidateExperience: string;
  sections: {
    profile: string;
    preview: string;
    process: string;
    trust: string;
    content: string;
  };
  metrics: Array<{label: string; value: string; detail: string}>;
  profileCard: {
    title: string;
    subtitle: string;
    industryLabel: string;
    sizeLabel: string;
    locationLabel: string;
    workModelLabel: string;
    hiringSpeedLabel: string;
  };
  profileValues: {
    industry: string;
    size: string;
    location: string;
    workModel: string;
    hiringSpeed: string;
  };
  brandScore: {
    title: string;
    description: string;
    strengthsTitle: string;
    gapsTitle: string;
    strengths: string[];
    gaps: string[];
  };
  preview: {
    badge: string;
    title: string;
    description: string;
    stats: Array<{label: string; value: string}>;
    cta: string;
  };
  process: {
    title: string;
    description: string;
    steps: Array<{title: string; duration: string; description: string}>;
  };
  trust: {
    title: string;
    description: string;
    items: Array<{title: string; description: string; status: string}>;
  };
  content: {
    title: string;
    description: string;
    items: Array<{title: string; score: number; description: string}>;
  };
  sidebar: {
    title: string;
    description: string;
    actionsTitle: string;
    actions: string[];
  };
};

type EmployerCopy = {
  shell: {
    skipToContent: string;
    productName: string;
    productLabel: string;
    sidebarCollapseSoon: string;
    sidebarClose: string;
    sidebarNavigation: string;
    moduleNavigation: string;
    qualityBadge: string;
    qualityTitle: string;
    qualityDescription: string;
  };
  topbar: {
    mobileMenu: string;
    breadcrumbRoot: string;
    searchLabel: string;
    searchPlaceholder: string;
    mobileSearchLabel: string;
    mobileSearchPlaceholder: string;
    newJob: string;
    newJobAria: string;
    aiSuggestions: string;
    notifications: string;
  };
  userMenu: {
    ariaLabel: string;
    profile: string;
    workspaceSettings: string;
    theme: string;
    notifications: string;
    logout: string;
    owner: string;
  };
  companySwitcher: {
    verifiedCompany: string;
    workspace: string;
    companies: Array<{id: string; name: string; plan: string; initials: string; verified: boolean}>;
  };
  nav: {
    sections: EmployerNavSection[];
    quickActions: QuickAction[];
  };
  badges: {
    new: string;
    ai: string;
    soon: string;
  };
  company: CompanyProfileCopy;
};

export function normalizeEmployerLanguage(locale: string): EmployerLanguage {
  return locale === 'tr' ? 'tr' : 'en';
}

function hrefs(locale: string) {
  const base = `/${locale}/employer`;
  return {
    base,
    jobs: `${base}/jobs`,
    matches: `${base}/talent`,
    candidates: `${base}/candidates`,
    campaigns: `${base}/campaigns`,
    interviews: `${base}/interviews`,
    analytics: `${base}/analytics`,
    company: `${base}/company`,
    compliance: `${base}/compliance`,
    settings: `${base}/settings`,
    localization: `${base}/localization`,
    quality: `${base}/quality`,
    support: `${base}/support`,
    newJob: `${base}/jobs?new=1`,
  };
}

export function getEmployerCopy(locale: string): EmployerCopy {
  const lang = normalizeEmployerLanguage(locale);
  const h = hrefs(locale);

  if (lang === 'tr') {
    const badges = {new: 'Yeni', ai: 'Yapay zekâ', soon: 'Yakında'};
    return {
      badges,
      shell: {
        skipToContent: 'İçeriğe geç',
        productName: 'Hiring Radar',
        productLabel: 'İşveren İşletim Merkezi',
        sidebarCollapseSoon: 'Menüyü daraltma yakında',
        sidebarClose: 'Menüyü kapat',
        sidebarNavigation: 'İşveren navigasyonu',
        moduleNavigation: 'İşveren modülleri',
        qualityBadge: 'Üretim kalitesi',
        qualityTitle: 'Okunabilirlik ve erişilebilirlik aktif',
        qualityDescription: 'Bu bölümde net Türkçe metin, güçlü odak durumları ve mobil uyumlu işe alım akışları kullanılır.',
      },
      topbar: {
        mobileMenu: 'İşveren menüsünü aç',
        breadcrumbRoot: 'İşveren Merkezi',
        searchLabel: 'İşveren panelinde ara',
        searchPlaceholder: 'Aday, ilan, beceri veya komut ara...',
        mobileSearchLabel: 'Mobil işveren araması',
        mobileSearchPlaceholder: 'Aday, ilan veya komut ara...',
        newJob: 'Yeni ilan',
        newJobAria: 'Yeni ilan oluştur',
        aiSuggestions: 'Yapay zekâ önerileri',
        notifications: 'Bildirimler',
      },
      userMenu: {
        ariaLabel: 'İşveren kullanıcı menüsü',
        profile: 'Profil',
        workspaceSettings: 'Çalışma alanı ayarları',
        theme: 'Tema',
        notifications: 'Bildirimler',
        logout: 'Çıkış yap',
        owner: 'Sahip',
      },
      companySwitcher: {
        verifiedCompany: 'Doğrulanmış şirket',
        workspace: 'Çalışma alanı',
        companies: [
          {id: 'noytera', name: 'NoyTera Teknoloji', plan: 'Büyüme planı çalışma alanı', initials: 'NT', verified: true},
          {id: 'operations', name: 'Operasyon İşe Alım Ekibi', plan: 'Aday havuzu yönetimi', initials: 'OE', verified: false},
        ],
      },
      nav: {
        sections: [
          {
            title: 'Operasyon',
            items: [
              {label: 'Kokpit', description: 'Bugünün işe alım kontrol merkezi', href: h.base, icon: Gauge},
              {label: 'İlanlar', description: 'İlanlar, kalite skoru ve performans', href: h.jobs, icon: BriefcaseBusiness},
              {label: 'Yetenek Radarı', description: 'Eşleşme ve aday fırsatları', href: h.matches, icon: Radar, badge: badges.ai},
              {label: 'Adaylar', description: 'Aday havuzu ve kısa liste', href: h.candidates, icon: UsersRound},
              {label: 'Kampanyalar', description: 'Davet kampanyaları ve gönderim kuyruğu', href: h.campaigns, icon: Megaphone, badge: badges.new},
            ],
          },
          {
            title: 'Ölçekleme',
            items: [
              {label: 'Görüşmeler', description: 'Planlama ve değerlendirme kartları', href: h.interviews, icon: CalendarDays, badge: badges.soon, disabled: true},
              {label: 'Analitik', description: 'Huni, kaynak kalitesi ve işe alım hızı', href: h.analytics, icon: BarChart3},
              {label: 'Şirket', description: 'İşveren markası ve aday görünümü', href: h.company, icon: Building2},
              {label: 'Uyumluluk', description: 'Yapay zekâ denetimi, KVKK ve yetki kontrolleri', href: h.compliance, icon: ShieldCheck, badge: badges.soon, disabled: true},
            ],
          },
          {
            title: 'Çalışma Alanı',
            items: [
              {label: 'Ayarlar', description: 'Şirket, bildirim ve güvenlik ayarları', href: h.settings, icon: Settings},
              {label: 'Dil ve yerelleştirme', description: 'Türkçe/İngilizce ürün dili ve kalite kontrolü', href: h.localization, icon: Languages},
              {label: 'Kalite kontrol', description: 'Rotalar, backend ve yayın öncesi duman testleri', href: h.quality, icon: ClipboardCheck, badge: badges.new},
              {label: 'Destek', description: 'Yardım, başlangıç ve satış desteği', href: h.support, icon: LifeBuoy, badge: badges.soon, disabled: true},
            ],
          },
        ],
        quickActions: [
          {label: 'Yeni ilan', description: 'Yapay zekâ destekli ilan stüdyosu', href: h.newJob, icon: Sparkles},
          {label: 'Aday ara', description: 'Yetenek Radarı kaynak bulma akışı', href: h.matches, icon: Radar},
          {label: 'Kampanya', description: 'Davet kampanyası merkezi', href: h.campaigns, icon: Megaphone},
          {label: 'Riskleri gör', description: 'Açık pozisyon sağlık kontrolü', href: h.analytics, icon: Scale},
        ],
      },
      company: {
        heroEyebrow: 'İşveren markası',
        title: 'Adayların güveneceği şirket profilini yönet',
        description: 'Şirket anlatımı, işe alım süreci, şeffaflık sinyalleri ve aday deneyimi tek merkezde. Bu sayfa adayın gördüğü marka algısını üretim kalitesinde yönetmek için tasarlandı.',
        primaryAction: 'Genel profili önizle',
        secondaryAction: 'İçerik kalitesini incele',
        readinessLabel: 'Marka hazırlığı',
        publicPreview: 'Aday görünümü',
        trustSignals: 'Güven sinyalleri',
        contentQuality: 'İçerik kalitesi',
        candidateExperience: 'Aday deneyimi',
        sections: {profile: 'Profil', preview: 'Önizleme', process: 'Süreç', trust: 'Güven', content: 'İçerik'},
        metrics: [
          {label: 'Profil tamlığı', value: '92%', detail: 'Adayların görmesi gereken temel bilgiler hazır'},
          {label: 'Yanıt sözü', value: '72 saat', detail: 'Başvuran adaylara dönüş taahhüdü'},
          {label: 'Süreç şeffaflığı', value: '4 aşama', detail: 'Adayın bekleyeceği adımlar net'},
          {label: 'Marka skoru', value: '88/100', detail: 'Güven, açıklık ve ikna gücü dengeli'},
        ],
        profileCard: {
          title: 'Şirket kimliği', subtitle: 'Adaya gösterilecek temel işveren bilgileri', industryLabel: 'Sektör', sizeLabel: 'Ekip büyüklüğü', locationLabel: 'Merkez', workModelLabel: 'Çalışma modeli', hiringSpeedLabel: 'Ortalama süreç',
        },
        profileValues: {industry: 'Yapay zekâ destekli işe alım teknolojileri', size: '51-200 çalışan', location: 'İstanbul, Türkiye', workModel: 'Hibrit ve uzaktan çalışma uyumlu', hiringSpeed: 'Başvurudan teklife 14-21 gün'},
        brandScore: {
          title: 'Marka skoru', description: 'Aday dönüşümünü etkileyen açıklık, güven ve süreç kalitesi sinyalleri.', strengthsTitle: 'Güçlü alanlar', gapsTitle: 'Geliştirilecek alanlar',
          strengths: ['İşe alım süreci net anlatılıyor', 'Yanıt süresi taahhüdü güven veriyor', 'Teknoloji ve ürün odağı açık'],
          gaps: ['Maaş bandı her ilanda zorunlu hale getirilmeli', 'Ekip fotoğrafları ve çalışan hikayeleri eklenmeli'],
        },
        preview: {
          badge: 'Doğrulanmış işveren', title: 'NoyTera Teknoloji', description: 'İşe alım ekipleri için açıklanabilir yapay zeka, aday zekası ve operasyon kokpiti geliştiren ürün ekibi.', cta: 'Açık rolleri gör',
          stats: [{label: 'Yanıt süresi', value: '72 saat'}, {label: 'Çalışma modeli', value: 'Hibrit'}, {label: 'Süreç', value: '4 aşama'}],
        },
        process: {
          title: 'Aday süreci', description: 'Adayların ne bekleyeceğini net şekilde görmesi başvuru kalitesini artırır.',
          steps: [
            {title: 'Ön değerlendirme', duration: '1-2 gün', description: 'Profil, rol uyumu ve temel beklentiler incelenir.'},
            {title: 'Tanışma görüşmesi', duration: '30 dakika', description: 'Rol, ekip ve çalışma modeli karşılıklı netleştirilir.'},
            {title: 'Teknik / vaka görüşmesi', duration: '60 dakika', description: 'Rolün gerektirdiği pratik yetkinlikler değerlendirilir.'},
            {title: 'Teklif ve kapanış', duration: '2-3 gün', description: 'Ücret, yan haklar ve başlangıç planı yazılı paylaşılır.'},
          ],
        },
        trust: {
          title: 'Güven ve şeffaflık', description: 'Adayların başvuru kararını etkileyen güven sinyalleri.',
          items: [
            {title: 'Doğrulanmış şirket profili', description: 'Şirket bilgileri ve alan adı doğrulaması tamamlandı.', status: 'Aktif'},
            {title: 'Yanıt süresi taahhüdü', description: 'Başvurulara en geç 72 saat içinde durum bilgisi verilir.', status: 'Aktif'},
            {title: 'Maaş şeffaflığı politikası', description: 'Kritik rollerde ücret aralığı yayınlama standardı uygulanır.', status: 'Gelişiyor'},
            {title: 'Yapay zekâ açıklama notu', description: 'Aday değerlendirmelerinde insan onayı ve açıklanabilirlik ilkesi gösterilir.', status: 'Aktif'},
          ],
        },
        content: {
          title: 'İçerik kalite kontrolü', description: 'Adaya gösterilecek metinlerin açıklık ve ikna gücü.',
          items: [
            {title: 'Şirket hikayesi', score: 91, description: 'Ürün odağı ve pazar problemi net anlatılıyor.'},
            {title: 'Değer önerisi', score: 84, description: 'Adayın neden başvurması gerektiği açık.'},
            {title: 'Süreç açıklığı', score: 96, description: 'Görüşme adımları ve süreler anlaşılır.'},
            {title: 'Maaş ve yan haklar', score: 72, description: 'Bazı rollerde daha fazla şeffaflık gerekiyor.'},
          ],
        },
        sidebar: {
          title: 'Üretim notu', description: 'Bu sayfa sabit metin gösterimi değil; şirket profilini, aday güvenini ve ilan dönüşümünü yöneten bir marka kontrol merkezidir.', actionsTitle: 'Sonraki üretim adımları',
          actions: ['Şirket profilini backend ayarlarına bağla', 'Adaya açık profil sayfasını yayınla', 'Her ilanda marka ve süreç sinyallerini göster', 'Maaş şeffaflığı politikasını rol bazında zorunlu kıl'],
        },
      },
    };
  }

  const badges = {new: 'New', ai: 'AI', soon: 'Soon'};
  return {
    badges,
    shell: {
      skipToContent: 'Skip to content', productName: 'Hiring Radar', productLabel: 'Employer Operating Center', sidebarCollapseSoon: 'Sidebar collapse coming soon', sidebarClose: 'Close menu', sidebarNavigation: 'Employer navigation', moduleNavigation: 'Employer modules', qualityBadge: 'Production quality', qualityTitle: 'Readability and accessibility are active', qualityDescription: 'This workspace uses clear English copy, strong focus states and responsive hiring workflows.',
    },
    topbar: {
      mobileMenu: 'Open employer menu', breadcrumbRoot: 'Employer Center', searchLabel: 'Search employer workspace', searchPlaceholder: 'Search candidates, jobs, skills or commands...', mobileSearchLabel: 'Mobile employer search', mobileSearchPlaceholder: 'Search candidates, jobs or commands...', newJob: 'New job', newJobAria: 'Create a new job', aiSuggestions: 'AI suggestions', notifications: 'Notifications',
    },
    userMenu: {ariaLabel: 'Employer user menu', profile: 'Profile', workspaceSettings: 'Workspace settings', theme: 'Theme', notifications: 'Notifications', logout: 'Log out', owner: 'Owner'},
    companySwitcher: {
      verifiedCompany: 'Verified company', workspace: 'Workspace',
      companies: [
        {id: 'noytera', name: 'NoyTera Technology', plan: 'Growth workspace', initials: 'NT', verified: true},
        {id: 'operations', name: 'Operations Hiring Team', plan: 'Talent pool management', initials: 'OH', verified: false},
      ],
    },
    nav: {
      sections: [
        {title: 'Operate', items: [
          {label: 'Cockpit', description: 'Today’s hiring control center', href: h.base, icon: Gauge},
          {label: 'Jobs', description: 'Job posts, quality score and performance', href: h.jobs, icon: BriefcaseBusiness},
          {label: 'Talent Radar', description: 'Matching and candidate opportunities', href: h.matches, icon: Radar, badge: badges.ai},
          {label: 'Candidates', description: 'Talent pool and shortlist', href: h.candidates, icon: UsersRound},
          {label: 'Campaigns', description: 'Invite campaigns and send queue', href: h.campaigns, icon: Megaphone, badge: badges.new},
        ]},
        {title: 'Scale', items: [
          {label: 'Interviews', description: 'Scheduling and scorecard workflows', href: h.interviews, icon: CalendarDays, badge: badges.soon, disabled: true},
          {label: 'Analytics', description: 'Funnel, source quality and hiring velocity', href: h.analytics, icon: BarChart3},
          {label: 'Company', description: 'Employer brand and candidate-facing profile', href: h.company, icon: Building2},
          {label: 'Compliance', description: 'AI audit, privacy and permission controls', href: h.compliance, icon: ShieldCheck, badge: badges.soon, disabled: true},
        ]},
        {title: 'Workspace', items: [
          {label: 'Settings', description: 'Company, notification and security settings', href: h.settings, icon: Settings},
          {label: 'Language & localization', description: 'Product language, glossary and quality checks', href: h.localization, icon: Languages},
          {label: 'Quality control', description: 'Routes, backend and pre-release smoke checks', href: h.quality, icon: ClipboardCheck, badge: badges.new},
          {label: 'Support', description: 'Help, onboarding and sales support', href: h.support, icon: LifeBuoy, badge: badges.soon, disabled: true},
        ]},
      ],
      quickActions: [
        {label: 'New job', description: 'AI-assisted job studio', href: h.newJob, icon: Sparkles},
        {label: 'Find talent', description: 'Talent Radar sourcing flow', href: h.matches, icon: Radar},
        {label: 'Campaign', description: 'Invite campaign center', href: h.campaigns, icon: Megaphone},
        {label: 'See risks', description: 'Open role health check', href: h.analytics, icon: Scale},
      ],
    },
    company: {
      heroEyebrow: 'Employer brand', title: 'Manage the company profile candidates can trust', description: 'Company story, hiring process, transparency signals and candidate experience live in one place. This page is designed to manage candidate-facing brand perception at production quality.', primaryAction: 'Preview public profile', secondaryAction: 'Review content quality', readinessLabel: 'Brand readiness', publicPreview: 'Candidate preview', trustSignals: 'Trust signals', contentQuality: 'Content quality', candidateExperience: 'Candidate experience', sections: {profile: 'Profile', preview: 'Preview', process: 'Process', trust: 'Trust', content: 'Content'},
      metrics: [
        {label: 'Profile completeness', value: '92%', detail: 'Core candidate-facing information is ready'},
        {label: 'Response promise', value: '72h', detail: 'Committed response time for applicants'},
        {label: 'Process clarity', value: '4 stages', detail: 'The candidate knows what to expect'},
        {label: 'Brand score', value: '88/100', detail: 'Trust, clarity and persuasion are balanced'},
      ],
      profileCard: {title: 'Company identity', subtitle: 'Core employer information shown to candidates', industryLabel: 'Industry', sizeLabel: 'Team size', locationLabel: 'Headquarters', workModelLabel: 'Work model', hiringSpeedLabel: 'Average process'},
      profileValues: {industry: 'AI-powered hiring technology', size: '51-200 employees', location: 'Istanbul, Türkiye', workModel: 'Hybrid and remote-friendly', hiringSpeed: '14-21 days from application to offer'},
      brandScore: {title: 'Brand score', description: 'Clarity, trust and process-quality signals that influence candidate conversion.', strengthsTitle: 'Strengths', gapsTitle: 'Improvement areas', strengths: ['Hiring process is explained clearly', 'Response-time promise builds trust', 'Technology and product focus are clear'], gaps: ['Salary range should be mandatory for every role', 'Add team photos and employee stories']},
      preview: {badge: 'Verified employer', title: 'NoyTera Technology', description: 'A product team building explainable AI, candidate intelligence and operating cockpits for hiring teams.', cta: 'View open roles', stats: [{label: 'Response time', value: '72h'}, {label: 'Work model', value: 'Hybrid'}, {label: 'Process', value: '4 stages'}]},
      process: {title: 'Candidate process', description: 'Showing candidates exactly what to expect improves application quality.', steps: [
        {title: 'Initial review', duration: '1-2 days', description: 'Profile, role fit and core expectations are reviewed.'},
        {title: 'Intro call', duration: '30 minutes', description: 'Role, team and work model are clarified together.'},
        {title: 'Technical / case interview', duration: '60 minutes', description: 'Practical role-specific capabilities are evaluated.'},
        {title: 'Offer and close', duration: '2-3 days', description: 'Compensation, benefits and start plan are shared in writing.'},
      ]},
      trust: {title: 'Trust and transparency', description: 'Trust signals that shape a candidate’s decision to apply.', items: [
        {title: 'Verified company profile', description: 'Company information and domain verification are complete.', status: 'Active'},
        {title: 'Response-time promise', description: 'Applicants receive a status update within 72 hours.', status: 'Active'},
        {title: 'Salary transparency policy', description: 'Critical roles follow a salary-range publishing standard.', status: 'Improving'},
        {title: 'AI explanation note', description: 'Human review and explainability principles are shown for candidate evaluation.', status: 'Active'},
      ]},
      content: {title: 'Content quality check', description: 'Clarity and persuasion of candidate-facing content.', items: [
        {title: 'Company story', score: 91, description: 'Product focus and market problem are clear.'},
        {title: 'Value proposition', score: 84, description: 'Why a candidate should apply is clear.'},
        {title: 'Process clarity', score: 96, description: 'Interview stages and timelines are understandable.'},
        {title: 'Compensation and benefits', score: 72, description: 'Some roles need more transparency.'},
      ]},
      sidebar: {title: 'Production note', description: 'This page is not a static demo. It is a brand control center for company profile, candidate trust and job conversion.', actionsTitle: 'Next production steps', actions: ['Connect the company profile to backend settings', 'Publish the candidate-facing company page', 'Show brand and process signals on every job post', 'Make salary transparency rules configurable by role']},
    },
  };
}
