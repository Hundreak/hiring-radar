import {LegalSections} from '@/components/marketing/legal-sections';
import {MarketingPageShell} from '@/components/marketing/page-shell';
import {SectionHeading} from '@/components/marketing/section-heading';

const sections = [
  {
    title: '1. Çerez Aydınlatma Metni hakkında',
    paragraphs: [
      'Bu Çerez Aydınlatma Metni, CoreSift tarafından işletilen dijital ürün deneyimi sırasında kullanılan çerezler ve benzeri teknolojilere ilişkin bilgilendirme amacı taşır.',
      'Çerezler; hizmetin çalışmasını sağlamak, oturumları sürdürebilmek, güvenliği artırmak ve kullanıcı deneyimini ölçmek gibi amaçlarla kullanılabilir.'
    ]
  },
  {
    title: '2. Hangi çerez türleri kullanılabilir?',
    bullets: [
      'Zorunlu çerezler: oturum, güvenlik ve temel ürün fonksiyonları için gerekli olabilir.',
      'İşlevsellik çerezleri: dil, tercih ve kullanıcı deneyimini kişiselleştirmek için kullanılabilir.',
      'Analitik çerezler: ürün kullanımının anlaşılması ve performans iyileştirmesi için sınırlı ölçüde değerlendirilebilir.'
    ]
  },
  {
    title: '3. Kullanım amaçları',
    bullets: [
      'Kullanıcı oturumunu sürdürebilmek',
      'Kimlik doğrulama ve güvenlik mekanizmalarını desteklemek',
      'Ürün performansını ve hata davranışlarını anlamak',
      'Kullanıcı deneyimini iyileştirmek ve tercihler hatırlamak'
    ]
  },
  {
    title: '4. Çerez tercihleri',
    paragraphs: [
      'Kullanıcılar tarayıcı ayarları üzerinden çerez tercihlerini yönetebilir, mevcut çerezleri silebilir veya çerez kullanımını sınırlandırabilir. Ancak bazı zorunlu çerezler devre dışı bırakıldığında ürünün belirli bölümleri beklenen şekilde çalışmayabilir.'
    ]
  },
  {
    title: '5. İletişim',
    paragraphs: [
      'Çerezler ve benzeri teknolojiler hakkında daha fazla bilgi veya veri işleme süreçlerine ilişkin talep için destek@coresift.com adresi üzerinden bizimle iletişime geçebilirsiniz.'
    ]
  }
];

export default async function CookiesPage({
  params
}: {
  params: Promise<{locale: string}>;
}) {
  const {locale} = await params;

  return (
    <MarketingPageShell locale={locale}>
      <section className="container-shell py-20">
        <SectionHeading
          eyebrow="Çerez Politikası"
          title="Çerezler ve benzeri teknolojiler hakkında bilgilendirme"
          description="Bu metin, CoreSift hizmetleri kapsamında kullanılabilecek çerezlerin amaçlarını ve kullanıcı tercih alanlarını özetler."
        />

        <div className="mt-12">
          <LegalSections sections={sections} />
        </div>
      </section>
    </MarketingPageShell>
  );
}