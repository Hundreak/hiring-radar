import {MarketingPageShell} from '@/components/marketing/page-shell';
import {SectionHeading} from '@/components/marketing/section-heading';

export default async function SupportPage({
  params
}: {
  params: Promise<{locale: string}>;
}) {
  const {locale} = await params;

  return (
    <MarketingPageShell locale={locale}>
      <section className="container-shell py-20">
        <SectionHeading
          eyebrow="Destek"
          title="Destek ve kullanıcı yardımı"
          description="NoyTera ile ilgili teknik veya operasyonel bir konuda yardıma ihtiyacın varsa, destek süreçlerimizi buradan inceleyebilirsin."
        />

        <div className="mt-12 grid gap-6 lg:grid-cols-3">
          {[
            {
              title: 'Hesap ve erişim',
              body:
                'Giriş, şifre sıfırlama, doğrulama e-postası veya oturum problemlerinde destek@noytera.com üzerinden bizimle iletişime geçebilirsin.'
            },
            {
              title: 'Ürün geri bildirimi',
              body:
                'Hatalı davranış, UX önerisi veya yeni özellik talebi paylaşımlarını yazılı biçimde topluyoruz. Bu sayede talepler daha net önceliklendiriliyor.'
            },
            {
              title: 'Veri ve gizlilik talepleri',
              body:
                'KVKK, gizlilik, veri erişimi, düzeltme veya silme talepleri için yine aynı e-posta kanalını kullanabilirsin. Talep doğrulaması gerekebilir.'
            }
          ].map((item) => (
            <div key={item.title} className="rounded-[28px] border border-white/10 bg-[#171717] p-8">
              <h2 className="text-2xl font-semibold text-white">{item.title}</h2>
              <p className="mt-5 text-base leading-8 text-white/68">{item.body}</p>
            </div>
          ))}
        </div>

        <div className="mt-6 rounded-[30px] border border-white/10 bg-[#151515] p-8">
          <div className="text-xl font-semibold text-white">Yanıt süreci</div>
          <p className="mt-5 max-w-3xl text-base leading-8 text-white/68">
            Destek talepleri yoğunluk durumuna göre önceliklendirilir. Güvenlik, erişim ve
            hesap bütünlüğü başlıkları öncelikli değerlendirilir. Resmî dönüş kanalı yalnızca
            e-posta üzerinden yürütülür: destek@noytera.com
          </p>
        </div>
      </section>
    </MarketingPageShell>
  );
}