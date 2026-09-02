import Link from 'next/link';
import {ArrowRight, CheckCircle2, Clock3, Construction, ShieldCheck, Sparkles} from 'lucide-react';

import {StatusBadge, SurfaceCard} from '@/components/employer/ui';
import {getEmployerCopy, normalizeEmployerLanguage} from '@/lib/employer-copy';
import {cn} from '@/lib/utils';

type ComingSoonKind = 'interviews' | 'compliance' | 'support';

type EmployerComingSoonPageProps = {
  locale: string;
  kind: ComingSoonKind;
};

type ComingSoonCopy = {
  eyebrow: string;
  badge: string;
  title: string;
  description: string;
  primaryAction: string;
  secondaryAction: string;
  availabilityTitle: string;
  productionTitle: string;
  checklistTitle: string;
  nextTitle: string;
  items: Array<{title: string; description: string; status: string}>;
  checklist: string[];
  nextSteps: string[];
};

const TR_COPY: Record<ComingSoonKind, ComingSoonCopy> = {
  interviews: {
    eyebrow: 'Görüşme merkezi',
    badge: 'Üretime hazırlanıyor',
    title: 'Görüşme planlama ve değerlendirme merkezi yakında',
    description:
      'Bu alan takvim uygunluğu, görüşme kartları, yapılandırılmış değerlendirme formları ve işe alım yöneticisi geri bildirimlerini tek merkezde yönetecek. Şimdilik aday sürecini Yetenek Radarı ve Kampanyalar üzerinden yönetebilirsin.',
    primaryAction: 'Adayları yönet',
    secondaryAction: 'Analitiği incele',
    availabilityTitle: 'Planlanan kapsam',
    productionTitle: 'Üretim kalitesi notu',
    checklistTitle: 'Yayın öncesi kontrol listesi',
    nextTitle: 'Sonraki teknik adımlar',
    items: [
      {title: 'Takvim entegrasyonu', description: 'Google Calendar ve uygun saat önerileri.', status: 'Sırada'},
      {title: 'Değerlendirme kartları', description: 'Rol bazlı puanlama kriterleri ve görüşme notları.', status: 'Tasarlanıyor'},
      {title: 'Geri bildirim takibi', description: 'Bekleyen yorumlar, hedef süre uyarıları ve karar özeti.', status: 'Hazırlanıyor'},
    ],
    checklist: ['Saat dilimi ve dil desteği', 'İnsan onaylı değerlendirme akışı', 'Erişilebilir form alanları', 'Denetim kaydı'],
    nextSteps: ['Görüşme veri modelini ekle', 'Takvim sağlayıcı bağlantısını soyutla', 'Değerlendirme formu bileşenlerini çıkar'],
  },
  compliance: {
    eyebrow: 'Uyumluluk merkezi',
    badge: 'Güvenlik tasarımı',
    title: 'Yapay zekâ denetimi, KVKK ve izin kontrolleri yakında',
    description:
      'Bu alan yapay zekâ önerilerinin açıklanabilirliğini, insan denetimini, veri saklama kurallarını ve rol tabanlı erişim kontrollerini yönetecek. Kurumsal satış için kritik güven katmanı burada toplanacak.',
    primaryAction: 'Ayarları aç',
    secondaryAction: 'Dil kalitesini incele',
    availabilityTitle: 'Planlanan kapsam',
    productionTitle: 'Üretim kalitesi notu',
    checklistTitle: 'Yayın öncesi kontrol listesi',
    nextTitle: 'Sonraki teknik adımlar',
    items: [
      {title: 'Yapay zekâ denetim kaydı', description: 'Öneri, insan onayı ve değişiklik geçmişi.', status: 'Hazırlanıyor'},
      {title: 'Veri saklama politikası', description: 'Aday verisi için süre, silme ve dışa aktarma kuralları.', status: 'Sırada'},
      {title: 'Yetki kapsamı', description: 'Rol bazlı görünürlük ve hassas alan maskeleme.', status: 'Temel atıldı'},
    ],
    checklist: ['KVKK/GDPR metinleri', 'İnsan denetimi zorunluluğu', 'Hassas veri maskeleme', 'Dışa aktarılabilir kayıtlar'],
    nextSteps: ['Denetim olay modelini backend’e taşı', 'Veri saklama ayarlarını kalıcı yap', 'Rol tabanlı görünürlük kontrollerini API’ye bağla'],
  },
  support: {
    eyebrow: 'Destek merkezi',
    badge: 'Müşteri başarısı',
    title: 'Yardım, başlangıç ve satış destek merkezi yakında',
    description:
      'Bu alan ürün turu, kurulum kontrol listesi, satış destek materyalleri ve müşteri başarı akışlarını tek merkezde toplayacak. Şimdilik destek gerektiren noktaları Ayarlar ve Dil Merkezi üzerinden kontrol edebilirsin.',
    primaryAction: 'Ayarları aç',
    secondaryAction: 'Şirket profilini düzenle',
    availabilityTitle: 'Planlanan kapsam',
    productionTitle: 'Üretim kalitesi notu',
    checklistTitle: 'Yayın öncesi kontrol listesi',
    nextTitle: 'Sonraki teknik adımlar',
    items: [
      {title: 'Başlangıç kontrol listesi', description: 'İlk ilan, aday havuzu ve kampanya kurulumu.', status: 'Sırada'},
      {title: 'Ürün turu', description: 'Rol bazlı rehberli ekran akışları.', status: 'Tasarlanıyor'},
      {title: 'Satış destek paketi', description: 'ROI özeti, kullanım kanıtı ve hesap sağlığı.', status: 'Hazırlanıyor'},
    ],
    checklist: ['Türkçe/İngilizce yardım metinleri', 'Erişilebilir yönlendirme', 'Boş durum rehberliği', 'Müşteri başarı sinyalleri'],
    nextSteps: ['Onboarding olaylarını tanımla', 'Yardım içeriği modelini kur', 'Demo/satış paketini gerçek metriklere bağla'],
  },
};

const EN_COPY: Record<ComingSoonKind, ComingSoonCopy> = {
  interviews: {
    eyebrow: 'Interview center',
    badge: 'Production-ready design in progress',
    title: 'Interview scheduling and structured feedback are coming soon',
    description:
      'This area will manage calendar availability, interview kits, structured scorecards and hiring-manager feedback in one place. For now, manage candidates through Talent Radar and Campaigns.',
    primaryAction: 'Manage candidates',
    secondaryAction: 'Review analytics',
    availabilityTitle: 'Planned scope',
    productionTitle: 'Production quality note',
    checklistTitle: 'Pre-release checklist',
    nextTitle: 'Next technical steps',
    items: [
      {title: 'Calendar integration', description: 'Google Calendar and suggested availability slots.', status: 'Next'},
      {title: 'Scorecards', description: 'Role-specific evaluation criteria and interview notes.', status: 'In design'},
      {title: 'Feedback tracking', description: 'Pending reviews, target-time alerts and decision summary.', status: 'In preparation'},
    ],
    checklist: ['Timezone and language support', 'Human-reviewed evaluation flow', 'Accessible form fields', 'Audit trail'],
    nextSteps: ['Add the interview data model', 'Abstract calendar-provider integration', 'Extract scorecard components'],
  },
  compliance: {
    eyebrow: 'Compliance center',
    badge: 'Security design',
    title: 'AI audit, privacy and permission controls are coming soon',
    description:
      'This area will manage explainability of AI recommendations, human oversight, data-retention rules and role-based access controls. It will become the trust layer for enterprise sales.',
    primaryAction: 'Open settings',
    secondaryAction: 'Review language quality',
    availabilityTitle: 'Planned scope',
    productionTitle: 'Production quality note',
    checklistTitle: 'Pre-release checklist',
    nextTitle: 'Next technical steps',
    items: [
      {title: 'AI audit trail', description: 'Recommendation, human approval and change history.', status: 'In preparation'},
      {title: 'Data retention policy', description: 'Candidate-data retention, deletion and export rules.', status: 'Next'},
      {title: 'Permission scope', description: 'Role-based visibility and sensitive-field masking.', status: 'Foundation ready'},
    ],
    checklist: ['KVKK/GDPR copy', 'Human oversight requirement', 'Sensitive-data masking', 'Exportable records'],
    nextSteps: ['Move audit events to the backend', 'Persist retention settings', 'Connect role-scoped visibility to the API'],
  },
  support: {
    eyebrow: 'Support center',
    badge: 'Customer success',
    title: 'Help, onboarding and sales support are coming soon',
    description:
      'This area will collect product tours, setup checklists, sales enablement assets and customer-success workflows in one place. For now, use Settings and the Localization Center for quality controls.',
    primaryAction: 'Open settings',
    secondaryAction: 'Edit company profile',
    availabilityTitle: 'Planned scope',
    productionTitle: 'Production quality note',
    checklistTitle: 'Pre-release checklist',
    nextTitle: 'Next technical steps',
    items: [
      {title: 'Onboarding checklist', description: 'First job, talent pool and campaign setup.', status: 'Next'},
      {title: 'Product tour', description: 'Role-based guided walkthroughs.', status: 'In design'},
      {title: 'Sales support pack', description: 'ROI summary, usage proof and account health.', status: 'In preparation'},
    ],
    checklist: ['Turkish/English help copy', 'Accessible guidance', 'Empty-state guidance', 'Customer-success signals'],
    nextSteps: ['Define onboarding events', 'Create the help-content model', 'Connect the demo/sales pack to real metrics'],
  },
};

function getCopy(locale: string, kind: ComingSoonKind) {
  return normalizeEmployerLanguage(locale) === 'tr' ? TR_COPY[kind] : EN_COPY[kind];
}

function actionHrefs(locale: string, kind: ComingSoonKind) {
  const base = `/${locale}/employer`;
  if (kind === 'interviews') return {primary: `${base}/candidates?view=pipeline`, secondary: `${base}/analytics`};
  if (kind === 'compliance') return {primary: `${base}/settings`, secondary: `${base}/localization`};
  return {primary: `${base}/settings`, secondary: `${base}/company`};
}

export function EmployerComingSoonPage({locale, kind}: EmployerComingSoonPageProps) {
  const copy = getCopy(locale, kind);
  const shellCopy = getEmployerCopy(locale);
  const hrefs = actionHrefs(locale, kind);

  return (
    <main className="space-y-6" aria-labelledby="coming-soon-title">
      <SurfaceCard variant="accent" padding="lg" className="overflow-hidden">
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px] lg:items-center">
          <div className="space-y-5">
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge tone="ai" icon={<Sparkles className="size-3.5" />}>{copy.eyebrow}</StatusBadge>
              <StatusBadge tone="warning" icon={<Clock3 className="size-3.5" />}>{copy.badge}</StatusBadge>
            </div>
            <div className="space-y-3">
              <h1 id="coming-soon-title" className="max-w-4xl text-3xl font-black tracking-[-0.04em] text-foreground sm:text-4xl lg:text-5xl">
                {copy.title}
              </h1>
              <p className="max-w-3xl text-base leading-7 text-muted-foreground sm:text-lg">
                {copy.description}
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <Link href={hrefs.primary} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-2xl border border-primary/20 bg-primary px-4 py-2.5 text-sm font-black text-primary-foreground shadow-[0_18px_42px_color-mix(in_srgb,var(--primary)_28%,transparent)] transition hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]">
                {copy.primaryAction}
                <ArrowRight className="size-4" />
              </Link>
              <Link href={hrefs.secondary} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-2xl border border-border bg-surface-elevated px-4 py-2.5 text-sm font-black text-foreground shadow-sm transition hover:-translate-y-0.5 hover:border-primary/35 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]">
                {copy.secondaryAction}
              </Link>
            </div>
          </div>

          <SurfaceCard variant="elevated" padding="md" className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex size-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                <Construction className="size-5" />
              </div>
              <div>
                <p className="text-sm font-black text-foreground">{copy.productionTitle}</p>
                <p className="text-xs leading-5 text-muted-foreground">{shellCopy.shell.qualityDescription}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {copy.checklist.slice(0, 4).map((item) => (
                <div key={item} className="rounded-2xl border border-border/80 bg-surface-muted/60 p-3 text-xs font-bold leading-5 text-foreground">
                  <CheckCircle2 className="mb-2 size-4 text-success" />
                  {item}
                </div>
              ))}
            </div>
          </SurfaceCard>
        </div>
      </SurfaceCard>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <SurfaceCard variant="default" padding="lg" className="space-y-4">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.18em] text-primary">{copy.availabilityTitle}</p>
            <h2 className="mt-2 text-2xl font-black tracking-[-0.03em] text-foreground">{copy.availabilityTitle}</h2>
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            {copy.items.map((item) => (
              <div key={item.title} className="rounded-3xl border border-border bg-surface-muted/55 p-4">
                <div className="mb-4 flex items-center justify-between gap-3">
                  <div className="flex size-10 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                    <ShieldCheck className="size-4" />
                  </div>
                  <span className="rounded-full border border-primary/15 bg-primary/10 px-2.5 py-1 text-[11px] font-black text-primary">{item.status}</span>
                </div>
                <h3 className="text-sm font-black text-foreground">{item.title}</h3>
                <p className="mt-2 text-xs leading-5 text-muted-foreground">{item.description}</p>
              </div>
            ))}
          </div>
        </SurfaceCard>

        <SurfaceCard variant="muted" padding="lg" className="space-y-5">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.18em] text-primary">{copy.nextTitle}</p>
            <h2 className="mt-2 text-xl font-black tracking-[-0.03em] text-foreground">{copy.checklistTitle}</h2>
          </div>
          <div className="space-y-3">
            {copy.nextSteps.map((step, index) => (
              <div key={step} className={cn('flex gap-3 rounded-2xl border border-border bg-surface/70 p-3', index === 0 && 'border-primary/30 bg-primary/[0.04]')}>
                <span className="flex size-7 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-xs font-black text-primary">{index + 1}</span>
                <p className="text-sm font-bold leading-6 text-foreground">{step}</p>
              </div>
            ))}
          </div>
        </SurfaceCard>
      </div>
    </main>
  );
}
