import {MarketingPageShell} from '@/components/marketing/page-shell';
import {SectionHeading} from '@/components/marketing/section-heading';

const principles = [
  {
    title: 'Açıklanabilirlik',
    description:
      'Ürettiğimiz öneriler, eşleşmeler ve yönlendirmeler kullanıcı açısından anlaşılır olmalıdır. NoyTera, siyah kutu deneyimi yerine açıklanabilir karar desteği üretmeyi benimser.'
  },
  {
    title: 'Kalite sinyali odaklılık',
    description:
      'Hacim üretmek tek başına değer değildir. Profil kalitesini, veri doğruluğunu ve karar faydasını artıran sinyallere öncelik veririz.'
  },
  {
    title: 'Kullanıcı güveni',
    description:
      'Kariyer verisi kişisel ve hassastır. Bu nedenle veri güvenliği, minimizasyon, kontrollü erişim ve açık iletişim ilkelerini ürün geliştirme kültürümüzün merkezine koyarız.'
  },
  {
    title: 'Profesyonel tasarım disiplini',
    description:
      'Kullanıcı arayüzü yalnızca estetik değil; karar kalitesini etkileyen operasyonel bir katmandır. Bu yüzden yalın, güven veren ve kurumsal ölçekte kabul görebilecek arayüzler tasarlarız.'
  },
  {
    title: 'Sürekli iyileştirme',
    description:
      'NoyTera statik bir ürün değildir. Geri bildirim, kullanım sinyali, kalite ölçümü ve güvenlik ihtiyaçları doğrultusunda sürekli rafine edilen yaşayan bir sistemdir.'
  },
  {
    title: 'Sadelik ve odak',
    description:
      'Karmaşık problemleri kullanıcı için daha sade akışlara dönüştürmek isteriz. Daha az sürtünme, daha yüksek netlik ve daha güçlü karar hissi üretmek temel hedeflerimizdendir.'
  }
];

export default async function PrinciplesPage({
  params
}: {
  params: Promise<{locale: string}>;
}) {
  const {locale} = await params;

  return (
    <MarketingPageShell locale={locale}>
      <section className="container-shell py-20">
        <SectionHeading
          eyebrow="Çalışma İlkelerimiz"
          title="NoyTera’i yöneten temel prensipler"
          description="Ürün kararlarından kullanıcı deneyimine, veri yönetiminden güvenlik yaklaşımına kadar her katmanda aynı kalite çizgisini korumaya çalışıyoruz."
        />

        <div className="mt-12 grid gap-6 md:grid-cols-2">
          {principles.map((principle) => (
            <div
              key={principle.title}
              className="rounded-[28px] border border-white/10 bg-[#171717] p-8"
            >
              <h2 className="text-2xl font-semibold text-white">{principle.title}</h2>
              <p className="mt-5 text-base leading-8 text-white/68">
                {principle.description}
              </p>
            </div>
          ))}
        </div>
      </section>
    </MarketingPageShell>
  );
}