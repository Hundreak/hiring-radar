import {FaqAccordion} from '@/components/marketing/faq-accordion';
import {MarketingPageShell} from '@/components/marketing/page-shell';
import {SectionHeading} from '@/components/marketing/section-heading';

const faqItems = [
  {
    question: 'CoreSift tam olarak ne yapar?',
    answer:
      'CoreSift, farklı kaynaklardan iş ilanlarını tarar, profilindeki sinyallerle karşılaştırır ve daha güçlü uyum gösteren fırsatları önceliklendirir. Aynı zamanda eksik profil alanlarını görünür hale getirerek eşleşme kalitesini artırmana yardımcı olur.'
  },
  {
    question: 'CoreSift işe alım garantisi verir mi?',
    answer:
      'Hayır. CoreSift bir sonuç garantisi vermez. Platformun amacı; daha iyi filtreleme, daha kaliteli görünürlük ve daha güçlü karar desteği sağlamaktır. Nihai işe alım kararları her zaman işveren ve ilgili süreçlere aittir.'
  },
  {
    question: 'Eşleşme puanı neye göre oluşur?',
    answer:
      'Uyum puanı; profilindeki beceri, deneyim, tercih, lokasyon ve tamamlanma sinyalleri ile ilan içeriği arasındaki ilişki üzerinden hesaplanır. Buradaki amaç tek sayı üretmek değil, daha açıklanabilir bir önceliklendirme yapmaktır.'
  },
  {
    question: 'CV yüklemeden platformu kullanabilir miyim?',
    answer:
      'Evet. CV yüklemek en hızlı başlangıç yöntemidir; ancak temel profil alanları manuel olarak da girilebilir. Yine de profil ne kadar zenginleşirse sistemin sunduğu eşleşmeler de o kadar güçlenir.'
  },
  {
    question: 'Şifresiz giriş nasıl çalışır?',
    answer:
      'Şifresiz giriş alanına e-posta adresini yazdığında, uygunsa hesabına tek kullanımlık güvenli bir giriş bağlantısı gönderilir. Bu akış, parola ile giriş alanından bağımsız çalışır.'
  },
  {
    question: 'Kayıt sırasında neden doğrulama kodu isteniyor?',
    answer:
      'E-posta doğrulama kodu; hesabın gerçekten sana ait olduğunu doğrulamak, sahte kayıtları azaltmak ve güvenlik katmanını güçlendirmek için kullanılır.'
  },
  {
    question: 'Bu platformda verilerim satılır mı?',
    answer:
      'Hayır. CoreSift kullanıcı verilerini reklam ağına, veri komisyoncularına veya üçüncü taraf pazarlama yapılarına satmaz. Veri işleme çerçevesi gizlilik politikası ve ilgili hukuki metinlerde belirtilir.'
  },
  {
    question: 'Şifrem ne kadar güçlü olmalı?',
    answer:
      'En az 8 karakter, büyük harf, küçük harf, rakam ve özel karakter içeren bir şifre kullanmanı öneriyoruz. Kayıt ekranındaki güç göstergesi bu kurallara göre çalışır.'
  },
  {
    question: 'Destek ekibine nasıl ulaşabilirim?',
    answer:
      'Ürün, hesap, güvenlik, veri erişimi veya geri bildirim başlıklarında doğrudan destek@coresift.com üzerinden bize ulaşabilirsin.'
  },
  {
    question: 'Profil tamamlanma skoru neden önemli?',
    answer:
      'Profil tamamlanma skoru, sistemin seni ne kadar doğru anladığını etkiler. Eksik sinyaller tamamlandıkça eşleşmeler daha doğru ve daha açıklanabilir hale gelir.'
  },
  {
    question: 'Platform ücretli mi?',
    answer:
      'CoreSift temel kullanıcı akışları için ücretsiz kullanım yaklaşımıyla tasarlanmıştır. Gelecekte ek profesyonel katmanlar veya genişletilmiş özellik planları sunulabilir.'
  },
  {
    question: 'Hesabımı silebilir miyim?',
    answer:
      'Evet. Kullanıcılar hesap kapatma ve veri taleplerine ilişkin destek sürecini başlatabilir. Talep niteliğine göre kimlik doğrulaması istenebilir.'
  }
];

export default async function FaqPage({
  params
}: {
  params: Promise<{locale: string}>;
}) {
  const {locale} = await params;

  return (
    <MarketingPageShell locale={locale}>
      <section className="container-shell py-20">
        <SectionHeading
          eyebrow="SSS"
          title="Sık sorulan sorular"
          description="CoreSift’i kullanmadan önce veya kullanırken en çok merak edilen başlıkları burada topladık."
        />

        <div className="mt-12">
          <FaqAccordion items={faqItems} />
        </div>
      </section>
    </MarketingPageShell>
  );
}