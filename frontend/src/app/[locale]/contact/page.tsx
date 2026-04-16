import {ContactForm} from '@/components/marketing/contact-form';
import {MarketingPageShell} from '@/components/marketing/page-shell';
import {SectionHeading} from '@/components/marketing/section-heading';
import type {SupportedLocale} from '@/types/user';

function resolveLocale(locale: string): SupportedLocale {
  if (locale === 'tr' || locale === 'en' || locale === 'de') return locale;
  return 'tr';
}

const copy = {
  tr: {
    eyebrow: 'İletişim',
    title: 'CoreSift ekibine ulaşın',
    description:
      'Ürün, güvenlik, veri talepleri, iş birliği veya genel geri bildirim konularında bizimle iletişime geçebilirsiniz. Tüm destek süreçlerini yazılı ve izlenebilir bir kanal üzerinden yürütüyoruz.',
    supportTitle: 'Resmî iletişim kanalı',
    supportBody:
      'Hesap sorunları, parola sıfırlama, ürün geri bildirimi, veri talepleri ve kurumsal iletişim konularında tek resmî yazılı iletişim kanalımız bu adrestir.',
    supportNote:
      'Talebinin daha hızlı işlenebilmesi için konu başlığını mümkün olduğunca açık yazmanı ve hesapla ilgili bir talep ise kayıtlı e-posta adresini kullanmanı öneririz.',
    topicsTitle: 'Hangi konularda yazabilirsin?',
    topics: [
      {
        title: 'Hesap ve erişim desteği',
        body:
          'Giriş sorunları, doğrulama e-postası, şifresiz giriş, parola sıfırlama ve oturum güvenliği ile ilgili tüm konular.'
      },
      {
        title: 'Veri ve gizlilik talepleri',
        body:
          'KVKK kapsamındaki başvurular, veri erişimi, düzeltme, silme veya işleme itiraz talepleri.'
      },
      {
        title: 'Ürün geri bildirimi',
        body:
          'Hata bildirimi, UX önerisi, geliştirme talebi veya ürün deneyimine ilişkin yapıcı geri bildirimler.'
      },
      {
        title: 'Kurumsal iş birlikleri',
        body:
          'Ürün ortaklığı, entegrasyon, iş geliştirme veya kurumsal deneme talepleri için ilk temas noktası.'
      }
    ]
  },
  en: {
    eyebrow: 'Contact',
    title: 'Get in touch with the CoreSift team',
    description:
      'You can contact us for product issues, security, privacy requests, partnerships or general feedback. We handle support through a written and traceable channel.',
    supportTitle: 'Official contact channel',
    supportBody:
      'This is our official written channel for account issues, password reset, product feedback, privacy requests and business communication.',
    supportNote:
      'To help us process your request faster, use a clear subject line and your registered email address when the request is account-related.',
    topicsTitle: 'What can you write to us about?',
    topics: [
      {
        title: 'Account and access support',
        body:
          'All topics related to sign-in issues, verification emails, passwordless access, password reset and session security.'
      },
      {
        title: 'Data and privacy requests',
        body:
          'Requests related to data access, correction, deletion or privacy objections under applicable law.'
      },
      {
        title: 'Product feedback',
        body:
          'Bug reports, UX feedback, improvement requests and product experience suggestions.'
      },
      {
        title: 'Business partnerships',
        body:
          'A first contact point for partnerships, integrations, commercial conversations and enterprise trials.'
      }
    ]
  },
  de: {
    eyebrow: 'Kontakt',
    title: 'Kontaktiere das CoreSift-Team',
    description:
      'Du kannst uns zu Produktfragen, Sicherheit, Datenschutzanfragen, Partnerschaften oder allgemeinem Feedback kontaktieren. Wir bearbeiten Anfragen über einen schriftlichen und nachvollziehbaren Kanal.',
    supportTitle: 'Offizieller Kontaktkanal',
    supportBody:
      'Dies ist unser offizieller schriftlicher Kanal für Kontothemen, Passwort-Reset, Produktfeedback, Datenschutzanfragen und geschäftliche Kommunikation.',
    supportNote:
      'Damit wir deine Anfrage schneller bearbeiten können, verwende bitte einen klaren Betreff und bei kontobezogenen Anliegen deine registrierte E-Mail-Adresse.',
    topicsTitle: 'Wozu kannst du uns schreiben?',
    topics: [
      {
        title: 'Konto- und Zugriffs-Support',
        body:
          'Alle Themen rund um Anmeldung, Bestätigungs-E-Mails, passwortlose Anmeldung, Passwort-Reset und Sitzungssicherheit.'
      },
      {
        title: 'Daten- und Datenschutzanfragen',
        body:
          'Anfragen zu Datenzugriff, Berichtigung, Löschung oder datenschutzrechtlichen Einwänden.'
      },
      {
        title: 'Produktfeedback',
        body:
          'Fehlerberichte, UX-Feedback, Verbesserungsvorschläge und Hinweise zur Produkterfahrung.'
      },
      {
        title: 'Geschäftliche Zusammenarbeit',
        body:
          'Erster Kontaktpunkt für Partnerschaften, Integrationen, geschäftliche Gespräche und Enterprise-Testphasen.'
      }
    ]
  }
} as const;

export default async function ContactPage({
  params
}: {
  params: Promise<{locale: string}>;
}) {
  const {locale: rawLocale} = await params;
  const locale = resolveLocale(rawLocale);
  const t = copy[locale];

  return (
    <MarketingPageShell locale={locale}>
      <section className="container-shell py-20">
        <SectionHeading
          eyebrow={t.eyebrow}
          title={t.title}
          description={t.description}
        />

        <div className="mt-12 grid gap-6 lg:grid-cols-[0.88fr_1.12fr] lg:items-start">
          <div className="space-y-6">
            <div className="rounded-[28px] border border-white/10 bg-[#171717] p-8">
              <div className="text-lg font-semibold text-white">{t.supportTitle}</div>
              <a
                href="mailto:destek@coresift.com"
                className="mt-4 block text-2xl font-semibold text-[#8fa0ff]"
              >
                destek@coresift.com
              </a>

              <p className="mt-6 text-base leading-8 text-white/68">{t.supportBody}</p>

              <div className="mt-8 rounded-2xl border border-white/10 bg-[#111111] p-5 text-sm leading-7 text-white/60">
                {t.supportNote}
              </div>
            </div>

            <div className="rounded-[28px] border border-white/10 bg-[#171717] p-8">
              <div className="text-xl font-semibold text-white">{t.topicsTitle}</div>
              <div className="mt-6 space-y-5">
                {t.topics.map((item) => (
                  <div
                    key={item.title}
                    className="rounded-2xl border border-white/8 bg-[#111111] p-5"
                  >
                    <div className="text-lg font-semibold text-white">{item.title}</div>
                    <p className="mt-3 text-base leading-8 text-white/64">{item.body}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <ContactForm locale={locale} />
        </div>
      </section>
    </MarketingPageShell>
  );
}