import {normalizeEmployerLanguage, type EmployerLanguage} from '@/lib/employer-copy';

export type QaSeverity = 'pass' | 'warning' | 'fail' | 'manual';

export type QaRoute = {
  id: string;
  label: string;
  description: string;
  path: string;
  status: QaSeverity;
  owner: string;
  checks: string[];
};

export type QaChecklistItem = {
  id: string;
  label: string;
  description: string;
  status: QaSeverity;
};

export type QaEndpoint = {
  id: string;
  label: string;
  path: string;
  method: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  description: string;
  expected: string;
};

export type QaCommand = {
  label: string;
  command: string;
  description: string;
};

export type EmployerProductionQaCopy = {
  lang: EmployerLanguage;
  hero: {
    eyebrow: string;
    title: string;
    description: string;
    primaryAction: string;
    secondaryAction: string;
  };
  nav: {
    routes: string;
    language: string;
    backend: string;
    checklist: string;
    commands: string;
  };
  labels: {
    routeMatrix: string;
    languageMatrix: string;
    backendHealth: string;
    smokeChecklist: string;
    commandCenter: string;
    status: Record<QaSeverity, string>;
    live: string;
    checked: string;
    open: string;
    copy: string;
    copied: string;
    retry: string;
    passCount: string;
    manualCount: string;
    warningCount: string;
    failCount: string;
    route: string;
    owner: string;
    checks: string;
    expected: string;
    endpoint: string;
    method: string;
    result: string;
  };
  metrics: Array<{label: string; value: string; detail: string; status: QaSeverity}>;
  routes: QaRoute[];
  languageChecks: QaChecklistItem[];
  smokeChecklist: QaChecklistItem[];
  endpoints: QaEndpoint[];
  commands: QaCommand[];
  releaseGate: {
    title: string;
    description: string;
    ready: string;
    blocked: string;
    manual: string;
  };
};

function localizedPath(locale: string, path: string) {
  return `/${locale}/employer${path}`;
}

export function getEmployerProductionQaCopy(locale: string): EmployerProductionQaCopy {
  const lang = normalizeEmployerLanguage(locale);

  if (lang === 'tr') {
    return {
      lang,
      hero: {
        eyebrow: 'Üretim hazırlığı',
        title: 'İşveren alanı kalite kontrol merkezi',
        description:
          'Tüm işveren rotalarını, Türkçe/İngilizce dil tutarlılığını, backend bağlantılarını, derin bağlantıları ve yayın öncesi manuel kontrolleri tek yerden izle.',
        primaryAction: 'Rota kontrolünü aç',
        secondaryAction: 'Duman testi komutları',
      },
      nav: {
        routes: 'Rotalar',
        language: 'Dil kalitesi',
        backend: 'Backend',
        checklist: 'Kontrol listesi',
        commands: 'Komutlar',
      },
      labels: {
        routeMatrix: 'Rota matrisi',
        languageMatrix: 'Dil ve metin kalite matrisi',
        backendHealth: 'Backend bağlantı durumu',
        smokeChecklist: 'Yayın öncesi duman testi',
        commandCenter: 'Yerel test komutları',
        status: {pass: 'Geçti', warning: 'Uyarı', fail: 'Başarısız', manual: 'Manuel'},
        live: 'Canlı kontrol',
        checked: 'Kontrol edildi',
        open: 'Aç',
        copy: 'Kopyala',
        copied: 'Kopyalandı',
        retry: 'Yeniden dene',
        passCount: 'Geçen',
        manualCount: 'Manuel',
        warningCount: 'Uyarı',
        failCount: 'Hata',
        route: 'Rota',
        owner: 'Sahip',
        checks: 'Kontroller',
        expected: 'Beklenen',
        endpoint: 'Uç nokta',
        method: 'Metot',
        result: 'Sonuç',
      },
      metrics: [
        {label: 'İşveren rotaları', value: '14', detail: 'Kokpit, ilanlar, adaylar, kampanyalar, analitik ve ayarlar', status: 'pass'},
        {label: 'Dil desteği', value: 'TR / EN', detail: 'Türkçe ve İngilizce ayrı ürün diliyle izleniyor', status: 'pass'},
        {label: 'Backend kapısı', value: '/api', detail: 'Sağlık ve kampanya uç noktaları canlı kontrol edilir', status: 'manual'},
        {label: 'Yayın kapısı', value: 'Elle onay', detail: 'Görsel, erişilebilirlik ve veri akışı son kontrol ister', status: 'warning'},
      ],
      routes: [
        {id: 'cockpit', label: 'Kokpit', description: 'Yönetici işe alım kontrol merkezi', path: localizedPath(locale, ''), status: 'pass', owner: 'Ürün / Ön yüz', checks: ['İşe alım sağlığı görünür', 'Yapay zekâ metni Türkçe', 'Aksiyon kartları bağlantılı']},
        {id: 'jobs', label: 'İlanlar', description: 'İlan kalite skoru ve risk yönetimi', path: localizedPath(locale, '/jobs'), status: 'pass', owner: 'Ön yüz', checks: ['İlan kalitesi Türkçe', 'Risk rozetleri okunabilir', 'Filtreler çalışır']},
        {id: 'talent', label: 'Yetenek Radarı', description: 'Aday keşfi ve derin bağlantı hedefi', path: localizedPath(locale, '/talent'), status: 'pass', owner: 'Ön yüz', checks: ['Radar görünümü açılır', 'Aday 360 açılır', 'Davet sekmesi çalışır']},
        {id: 'candidates', label: 'Adaylar', description: 'Aday havuzu, süreç ve karşılaştırma', path: localizedPath(locale, '/candidates'), status: 'pass', owner: 'Ön yüz', checks: ['Süreç panosu', 'Karşılaştırma', 'Not ve etiketler']},
        {id: 'candidate-deep-link', label: 'Aday derin bağlantısı', description: 'Eski aday detay rotası yeni 360 akışına gider', path: localizedPath(locale, '/candidates?candidate=1&panel=360'), status: 'pass', owner: 'Ön yüz', checks: ['Aday seçilir', 'Aday 360 drawer açılır', 'Geri dönüş kırılmaz']},
        {id: 'campaigns', label: 'Kampanyalar', description: 'Davet kampanyaları ve gönderim kuyruğu', path: localizedPath(locale, '/campaigns'), status: 'pass', owner: 'Ön yüz / Backend', checks: ['Kampanya listesi', 'Detay drawer', 'Review board']},
        {id: 'analytics', label: 'Analitik', description: 'Yönetici işe alım zekâsı', path: localizedPath(locale, '/analytics'), status: 'pass', owner: 'Ön yüz', checks: ['Lens seçimi', 'Kaynak kalitesi', 'Yönetim özeti']},
        {id: 'company', label: 'Şirket', description: 'İşveren markası ve aday görünümü', path: localizedPath(locale, '/company'), status: 'pass', owner: 'Ön yüz', checks: ['Marka hazırlığı', 'Aday süreci', 'Güven sinyalleri']},
        {id: 'settings', label: 'Ayarlar', description: 'Ekip, yetki, güvenlik ve marka ayarları', path: localizedPath(locale, '/settings'), status: 'pass', owner: 'Ön yüz', checks: ['Ekip rolleri', 'Güvenlik', 'Denetim']},
        {id: 'localization', label: 'Dil ve yerelleştirme', description: 'Türkçe/İngilizce kalite politikası', path: localizedPath(locale, '/localization'), status: 'pass', owner: 'Ürün dili', checks: ['Terim sözlüğü', 'Kapsama oranı', 'Dil riskleri']},
        {id: 'interviews', label: 'Görüşmeler', description: 'Henüz üretime hazırlanıyor sayfası', path: localizedPath(locale, '/interviews'), status: 'manual', owner: 'Ürün', checks: ['404 vermez', 'Türkçe metin', 'Gelecek adımlar açık']},
        {id: 'compliance', label: 'Uyumluluk', description: 'Henüz üretime hazırlanıyor sayfası', path: localizedPath(locale, '/compliance'), status: 'manual', owner: 'Güvenlik / Hukuk', checks: ['404 vermez', 'KVKK ve yapay zekâ vurgusu', 'Manuel onay notu']},
        {id: 'support', label: 'Destek', description: 'Henüz üretime hazırlanıyor sayfası', path: localizedPath(locale, '/support'), status: 'manual', owner: 'Müşteri başarısı', checks: ['404 vermez', 'Yönlendirme net', 'Dil tutarlı']},
      ],
      languageChecks: [
        {id: 'tr-only', label: 'Türkçe rotalarda İngilizce ürün terimi kullanılmaz', description: 'Pipeline, Shortlist, Match, Intent, Workspace gibi terimler Türkçeleştirilir.', status: 'warning'},
        {id: 'en-only', label: 'İngilizce rotalarda Türkçe kırıntı kalmaz', description: 'Kampanya, aday, ilan gibi Türkçe kelimeler /en rotalarında görünmemelidir.', status: 'warning'},
        {id: 'aria', label: 'Erişilebilirlik metinleri çevrilir', description: 'aria-label, buton açıklaması ve boş durum metinleri iki dilde tutulur.', status: 'manual'},
        {id: 'numbers', label: 'Tarih, yüzde ve sayı formatı yerel dile uyar', description: 'Türkçe tarih formatı ve İngilizce kısa tarih formatı ayrı kullanılmalıdır.', status: 'manual'},
      ],
      smokeChecklist: [
        {id: 'backend', label: 'Backend çalışıyor', description: 'http://127.0.0.1:8000/api/health başarılı dönmeli.', status: 'manual'},
        {id: 'frontend', label: 'Frontend çalışıyor', description: 'http://localhost:3000/tr/employer ve /en/employer açılmalı.', status: 'manual'},
        {id: 'campaign', label: 'Kampanya akışı kalıcı', description: 'Davet kampanyası oluştur, kuyruğu hazırla, sayfayı yenile, verinin geri geldiğini kontrol et.', status: 'manual'},
        {id: 'drawer', label: 'Drawer ve derin bağlantılar', description: 'Aday 360 ve kampanya detay drawer mobil ve masaüstünde kapanıp açılmalı.', status: 'manual'},
        {id: 'responsive', label: 'Mobil kırılma yok', description: '375px, 768px ve 1440px genişliklerinde sidebar, topbar ve kartlar taşmamalı.', status: 'manual'},
        {id: 'console', label: 'Konsol temiz', description: 'Hydration, nested anchor, unresolved module veya runtime error olmamalı.', status: 'manual'},
      ],
      endpoints: [
        {id: 'health', label: 'Sistem sağlığı', method: 'GET', path: '/api/health', description: 'Backend ayakta mı?', expected: '200 OK'},
        {id: 'system', label: 'Sistem detay sağlığı', method: 'GET', path: '/api/health/system', description: 'Temel servis bilgileri', expected: '200 OK'},
        {id: 'campaigns', label: 'Kampanya listesi', method: 'GET', path: '/api/employer/outreach/campaigns', description: 'Davet kampanyaları yüklenir', expected: '200 OK veya yetki uyarısı'},
        {id: 'workflow', label: 'Aday çalışma akışı', method: 'GET', path: '/api/employer/talent/workflow', description: 'Not ve etiketler yüklenir', expected: '200 OK'},
      ],
      commands: [
        {label: 'Backend başlat', command: 'cd ~/projects/hiring-radar && PYTHONPATH=src python -m uvicorn hiring_radar.api.app:app --host 127.0.0.1 --port 8000 --reload', description: 'FastAPI backend geliştirme sunucusu'},
        {label: 'Frontend başlat', command: 'cd ~/projects/hiring-radar/frontend && npm run dev', description: 'Next.js frontend geliştirme sunucusu'},
        {label: 'Backend testleri', command: 'cd ~/projects/hiring-radar && PYTHONPATH=src pytest -q tests/test_api_health.py tests/test_employer_matching.py', description: 'Temel backend duman testleri'},
        {label: 'Frontend lint', command: 'cd ~/projects/hiring-radar/frontend && npm run lint', description: 'Ön yüz statik kontrolü'},
      ],
      releaseGate: {
        title: 'Yayın kapısı',
        description: 'Bu ekran otomatik kontrol ve manuel kontrolü birlikte izler. Uyarılar kapanmadan üretime çıkma.',
        ready: 'Kritik akışlar gösterilebilir durumda.',
        blocked: 'Başarısız canlı kontrol varsa backend/frontend yeniden başlatılmalı.',
        manual: 'Görsel kalite, mobil kırılım ve dil kaçakları insan gözüyle onaylanmalı.',
      },
    };
  }

  return {
    lang,
    hero: {
      eyebrow: 'Production readiness',
      title: 'Employer quality control center',
      description:
        'Track employer routes, Turkish/English language consistency, backend connectivity, deep links and pre-release manual checks from one place.',
      primaryAction: 'Open route checks',
      secondaryAction: 'Smoke test commands',
    },
    nav: {routes: 'Routes', language: 'Language quality', backend: 'Backend', checklist: 'Checklist', commands: 'Commands'},
    labels: {
      routeMatrix: 'Route matrix',
      languageMatrix: 'Language and copy quality matrix',
      backendHealth: 'Backend connectivity',
      smokeChecklist: 'Pre-release smoke checklist',
      commandCenter: 'Local test commands',
      status: {pass: 'Pass', warning: 'Warning', fail: 'Fail', manual: 'Manual'},
      live: 'Live check',
      checked: 'Checked',
      open: 'Open',
      copy: 'Copy',
      copied: 'Copied',
      retry: 'Retry',
      passCount: 'Passing',
      manualCount: 'Manual',
      warningCount: 'Warnings',
      failCount: 'Failures',
      route: 'Route',
      owner: 'Owner',
      checks: 'Checks',
      expected: 'Expected',
      endpoint: 'Endpoint',
      method: 'Method',
      result: 'Result',
    },
    metrics: [
      {label: 'Employer routes', value: '14', detail: 'Cockpit, jobs, candidates, campaigns, analytics and settings', status: 'pass'},
      {label: 'Language support', value: 'TR / EN', detail: 'Turkish and English are tracked as separate product languages', status: 'pass'},
      {label: 'Backend gateway', value: '/api', detail: 'Health and campaign endpoints can be checked live', status: 'manual'},
      {label: 'Release gate', value: 'Human approval', detail: 'Visual, accessibility and data-flow checks still need final review', status: 'warning'},
    ],
    routes: [
      {id: 'cockpit', label: 'Cockpit', description: 'Executive hiring control center', path: localizedPath(locale, ''), status: 'pass', owner: 'Product / Frontend', checks: ['Hiring health visible', 'AI copy is English', 'Action cards are linked']},
      {id: 'jobs', label: 'Jobs', description: 'Job quality score and risk management', path: localizedPath(locale, '/jobs'), status: 'pass', owner: 'Frontend', checks: ['Job quality visible', 'Risk badges readable', 'Filters work']},
      {id: 'talent', label: 'Talent Radar', description: 'Candidate discovery and deep-link target', path: localizedPath(locale, '/talent'), status: 'pass', owner: 'Frontend', checks: ['Radar view opens', 'Candidate 360 opens', 'Invite tab works']},
      {id: 'candidates', label: 'Candidates', description: 'Talent pool, pipeline and comparison', path: localizedPath(locale, '/candidates'), status: 'pass', owner: 'Frontend', checks: ['Pipeline board', 'Comparison', 'Notes and tags']},
      {id: 'candidate-deep-link', label: 'Candidate deep link', description: 'Legacy candidate detail route targets the new 360 flow', path: localizedPath(locale, '/candidates?candidate=1&panel=360'), status: 'pass', owner: 'Frontend', checks: ['Candidate selected', 'Candidate 360 drawer opens', 'Back navigation remains safe']},
      {id: 'campaigns', label: 'Campaigns', description: 'Invite campaigns and send queue', path: localizedPath(locale, '/campaigns'), status: 'pass', owner: 'Frontend / Backend', checks: ['Campaign list', 'Detail drawer', 'Review board']},
      {id: 'analytics', label: 'Analytics', description: 'Executive hiring intelligence', path: localizedPath(locale, '/analytics'), status: 'pass', owner: 'Frontend', checks: ['Lens selector', 'Source quality', 'Board pack']},
      {id: 'company', label: 'Company', description: 'Employer brand and candidate preview', path: localizedPath(locale, '/company'), status: 'pass', owner: 'Frontend', checks: ['Brand readiness', 'Candidate process', 'Trust signals']},
      {id: 'settings', label: 'Settings', description: 'Team, permissions, security and brand settings', path: localizedPath(locale, '/settings'), status: 'pass', owner: 'Frontend', checks: ['Team roles', 'Security', 'Audit']},
      {id: 'localization', label: 'Language & localization', description: 'Turkish/English quality policy', path: localizedPath(locale, '/localization'), status: 'pass', owner: 'Product language', checks: ['Glossary', 'Coverage score', 'Language risks']},
      {id: 'interviews', label: 'Interviews', description: 'Production-ready placeholder', path: localizedPath(locale, '/interviews'), status: 'manual', owner: 'Product', checks: ['No 404', 'English copy', 'Next steps visible']},
      {id: 'compliance', label: 'Compliance', description: 'Production-ready placeholder', path: localizedPath(locale, '/compliance'), status: 'manual', owner: 'Security / Legal', checks: ['No 404', 'AI and privacy note', 'Manual approval note']},
      {id: 'support', label: 'Support', description: 'Production-ready placeholder', path: localizedPath(locale, '/support'), status: 'manual', owner: 'Customer success', checks: ['No 404', 'Clear direction', 'Language consistent']},
    ],
    languageChecks: [
      {id: 'tr-only', label: 'Turkish routes do not leak English product terms', description: 'Pipeline, Shortlist, Match, Intent and Workspace must be localized in /tr.', status: 'warning'},
      {id: 'en-only', label: 'English routes do not leak Turkish fragments', description: 'Kampanya, aday and ilan should not appear in /en routes.', status: 'warning'},
      {id: 'aria', label: 'Accessibility copy is localized', description: 'aria-label, button descriptions and empty states must be bilingual.', status: 'manual'},
      {id: 'numbers', label: 'Date, percentage and number formats are localized', description: 'Turkish and English date formats should be handled separately.', status: 'manual'},
    ],
    smokeChecklist: [
      {id: 'backend', label: 'Backend is running', description: 'http://127.0.0.1:8000/api/health should return successfully.', status: 'manual'},
      {id: 'frontend', label: 'Frontend is running', description: 'http://localhost:3000/tr/employer and /en/employer should open.', status: 'manual'},
      {id: 'campaign', label: 'Campaign flow persists', description: 'Create an invite campaign, prepare queue, refresh, and confirm data comes back.', status: 'manual'},
      {id: 'drawer', label: 'Drawers and deep links', description: 'Candidate 360 and campaign detail drawers should open and close on desktop and mobile.', status: 'manual'},
      {id: 'responsive', label: 'No mobile breakage', description: 'Sidebar, topbar and cards should not overflow at 375px, 768px and 1440px.', status: 'manual'},
      {id: 'console', label: 'Console is clean', description: 'No hydration, nested anchor, unresolved module or runtime errors.', status: 'manual'},
    ],
    endpoints: [
      {id: 'health', label: 'System health', method: 'GET', path: '/api/health', description: 'Is the backend up?', expected: '200 OK'},
      {id: 'system', label: 'System detail health', method: 'GET', path: '/api/health/system', description: 'Core service information', expected: '200 OK'},
      {id: 'campaigns', label: 'Campaign list', method: 'GET', path: '/api/employer/outreach/campaigns', description: 'Invite campaigns load', expected: '200 OK or auth warning'},
      {id: 'workflow', label: 'Talent workflow', method: 'GET', path: '/api/employer/talent/workflow', description: 'Notes and tags load', expected: '200 OK'},
    ],
    commands: [
      {label: 'Start backend', command: 'cd ~/projects/hiring-radar && PYTHONPATH=src python -m uvicorn hiring_radar.api.app:app --host 127.0.0.1 --port 8000 --reload', description: 'FastAPI backend development server'},
      {label: 'Start frontend', command: 'cd ~/projects/hiring-radar/frontend && npm run dev', description: 'Next.js frontend development server'},
      {label: 'Backend tests', command: 'cd ~/projects/hiring-radar && PYTHONPATH=src pytest -q tests/test_api_health.py tests/test_employer_matching.py', description: 'Core backend smoke tests'},
      {label: 'Frontend lint', command: 'cd ~/projects/hiring-radar/frontend && npm run lint', description: 'Frontend static checks'},
    ],
    releaseGate: {
      title: 'Release gate',
      description: 'This page combines automated checks and manual review. Do not ship while warnings remain unresolved.',
      ready: 'Critical flows are demoable and reviewable.',
      blocked: 'If a live check fails, restart backend/frontend and test the endpoint directly.',
      manual: 'Visual quality, responsive layout and language leaks still require human approval.',
    },
  };
}
