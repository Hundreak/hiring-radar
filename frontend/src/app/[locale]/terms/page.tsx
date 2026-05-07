import Link from 'next/link';

import {BrandLogo} from '@/components/brand/brand-logo';
import {MarketingPageShell} from '@/components/marketing/page-shell';
import type {SupportedLocale} from '@/types/user';

function resolveLocale(locale: string): SupportedLocale {
  if (locale === 'tr' || locale === 'en' || locale === 'de') return locale;
  return 'tr';
}

const copy = {
  tr: {
    title: 'Kullanım şartları',
    intro:
      'Bu belge, NoyTera platformunu kullanan tüm kişiler için bağlayıcıdır. Kayıt olarak veya platforma erişerek bu şartları okuduğunuzu, anladığınızı ve kabul ettiğinizi beyan etmiş olursunuz.',
    update: 'Son güncelleme: Nisan 2025 · Versiyon 1.2',
    toc: 'İçindekiler',
    otherTab: 'Gizlilik politikası',
    back: 'Kayıt ekranına dön',
    sections: [
      {
        id: 'parties',
        number: '1',
        title: 'Taraflar ve kapsam',
        body: [
          'Bu Kullanım Şartları; NoyTera platformunu işleten şirket (“NoyTera”) ile platforma kayıt olan veya herhangi bir şekilde erişen gerçek kişi kullanıcılar (“Kullanıcı”) arasındaki ilişkiyi düzenler.',
          'Şartlar; web sitesi, mobil uygulama ve API dâhil olmak üzere NoyTera’in sunduğu tüm dijital hizmetleri kapsar.',
          'Önemli: 18 yaşından küçük bireyler platforma kayıt olamaz.'
        ]
      },
      {
        id: 'service',
        number: '2',
        title: 'Hizmet tanımı',
        body: [
          'NoyTera; iş arayanlar için yapay zeka destekli iş ilanı keşif ve eşleştirme hizmeti sunan bir kariyer platformudur.',
          'Platformun temel hizmetleri şunları içerir: CV yükleme ve analiz, çoklu platform tarama, yapay zeka eşleştirme, AI kariyer danışmanı ve profil tamamlama skoru.',
          'NoyTera, ilanları doğrudan yayınlayan bir istihdam ajansı değildir. İlanlar üçüncü taraf platformlardan derlenir; güncellik veya doğruluk konusunda garanti verilemez.'
        ]
      },
      {
        id: 'account-security',
        number: '3',
        title: 'Hesap oluşturma ve güvenlik',
        body: [
          'Platforma erişmek için geçerli bir e-posta adresiyle kayıt olmanız ve e-posta doğrulamasını tamamlamanız gerekmektedir. Her gerçek kişi yalnızca bir hesap oluşturabilir.',
          'Kullanıcının sorumluluğundaki güvenlik önlemleri: şifresini kimseyle paylaşmamak, güçlü bir şifre seçmek, yetkisiz erişim fark ettiğinde derhal NoyTera’i bilgilendirmek, başkasına ait bilgilerle hesap açmamak ve ortak cihazlarda oturumu kapatmak.',
          'Hesabınız üzerinden gerçekleştirilen tüm işlemlerden siz sorumlusunuz.'
        ]
      },
      {
        id: 'usage-rules',
        number: '4',
        title: 'Kullanım kuralları ve yasaklar',
        body: [
          'Platform yalnızca kişisel iş arama amaçlı kullanılabilir.',
          'Aşağıdaki kullanımlar kesinlikle yasaktır: sahte veya başkasına ait bilgilerle profil oluşturmak, otomatik botlarla toplu istek göndermek, platform verilerini izinsiz kazımak veya kopyalamak, diğer kullanıcıların hesaplarına erişmeye çalışmak, sistemi yavaşlatacak veya çökertecek nitelikte işlem yapmak, spam veya ticari reklam iletmek.',
          'Kurallara aykırı davranış tespit edildiğinde hesap uyarısız askıya alınabilir ve gerektiğinde yasal süreç başlatılabilir.'
        ]
      },
      {
        id: 'billing',
        number: '5',
        title: 'Ücretlendirme ve abonelik',
        body: [
          'NoyTera’in temel özellikleri ücretsiz olarak sunulabilir. Gelişmiş özellikler için ücretli planlar tanımlanabilir.',
          'Temel plan; standart eşleştirme ve sınırlı AI danışman erişimi sunabilir. Profesyonel planlar; genişletilmiş eşleşmeler, tam AI danışman erişimi veya öncelikli deneyim katmanları içerebilir.',
          'Abonelik ücretleri aylık veya yıllık olabilir. İptal talepleri bir sonraki dönem için geçerli olur. Aksi belirtilmedikçe kısmi iade yapılmaz.'
        ]
      },
      {
        id: 'ip',
        number: '6',
        title: 'Fikri mülkiyet hakları',
        body: [
          'Platform üzerindeki tüm içerik, tasarım, yazılım kodu, algoritma, logo ve marka unsurları NoyTera’in münhasır mülkiyetindedir ve ilgili fikri mülkiyet mevzuatı kapsamında korunur.',
          'Kullanıcılar platforma yükledikleri CV ve profil bilgilerinin sahibi olmaya devam eder. NoyTera, bu verileri yalnızca hizmeti sunmak amacıyla işleme hakkına sahiptir.',
          'Platformdan elde edilen içeriklerin ticari amaçla yeniden yayımlanması, satılması veya lisanslanması açıkça yasaktır.'
        ]
      },
      {
        id: 'liability',
        number: '7',
        title: 'Sorumluluk sınırı',
        body: [
          'NoyTera; üçüncü taraf platformlardan derlenen ilanların doğruluğu veya güncelliği, işveren kararları, başvuru sonuçları veya işe alım süreçleri, kullanıcının kendi hatasından kaynaklanan veri kayıpları, internet bağlantısı kaynaklı erişim sorunları ve mücbir sebep halleri bakımından sorumluluk kabul etmez.'
        ]
      },
      {
        id: 'termination',
        number: '8',
        title: 'Hesap askıya alma ve sonlandırma',
        body: [
          'NoyTera, kullanım şartlarına aykırı davranış, sahte veya yanıltıcı bilgi girişi, diğer kullanıcılara veya sisteme zarar verme girişimi ya da ödeme yükümlülüklerinin yerine getirilmemesi gibi durumlarda hesabı uyarısız askıya alabilir veya kalıcı olarak silebilir.',
          'Kullanıcı da hesabını destek süreci veya uygun profil ayarları üzerinden sonlandırabilir. Hesap kapatma sonrası veri süreçleri ilgili gizlilik politikası ve yasal gerekliliklere göre yürütülür.'
        ]
      },
      {
        id: 'disputes',
        number: '9',
        title: 'Uyuşmazlık çözümü',
        body: [
          'Bu şartlardan doğan uyuşmazlıklarda öncelikle müzakere yoluyla çözüm aranır. Müzakere sonuçsuz kalırsa Türkiye Cumhuriyeti mahkemeleri yetkilidir ve Türk hukuku uygulanır.'
        ]
      },
      {
        id: 'changes',
        number: '10',
        title: 'Şartlardaki değişiklikler',
        body: [
          'NoyTera bu şartları gerektiğinde güncelleme hakkını saklı tutar. Önemli değişiklikler e-posta veya platform bildirimi yoluyla kullanıcılara duyurulabilir.'
        ]
      },
      {
        id: 'contact',
        number: '11',
        title: 'İletişim',
        body: ['Kullanım şartlarına ilişkin sorularınız için: legal@noytera.com']
      }
    ]
  },
  en: {
    title: 'Terms of use',
    intro:
      'This document is binding for all users of the NoyTera platform. By registering or accessing the platform, you declare that you have read, understood and accepted these terms.',
    update: 'Last updated: April 2025 · Version 1.2',
    toc: 'Contents',
    otherTab: 'Privacy policy',
    back: 'Back to sign up',
    sections: [
      {
        id: 'parties',
        number: '1',
        title: 'Parties and scope',
        body: [
          'These Terms of Use govern the relationship between NoyTera, the company operating the platform, and the individual users who register for or access the platform in any way.',
          'The terms cover all digital services provided by NoyTera, including the website, mobile applications and API surfaces.',
          'Important: Individuals under the age of 18 may not register for the platform.'
        ]
      },
      {
        id: 'service',
        number: '2',
        title: 'Service definition',
        body: [
          'NoyTera is a career platform that provides AI-supported job discovery and matching for job seekers.',
          'Core platform services include CV upload and parsing, multi-platform job aggregation, AI-based matching, an AI career advisor and a profile completion score.',
          'NoyTera is not an employment agency that directly publishes jobs. Roles are aggregated from third-party sources and their accuracy or freshness cannot be guaranteed.'
        ]
      },
      {
        id: 'account-security',
        number: '3',
        title: 'Account creation and security',
        body: [
          'To access the platform, users must register with a valid email address and complete email verification. Each individual may create only one account.',
          'Users are responsible for protecting their credentials, choosing a strong password, reporting unauthorized access immediately, avoiding the use of someone else’s identity and signing out from shared devices.',
          'All actions performed through your account are your responsibility.'
        ]
      },
      {
        id: 'usage-rules',
        number: '4',
        title: 'Usage rules and prohibited conduct',
        body: [
          'The platform may only be used for personal job-search purposes.',
          'The following are strictly prohibited: creating fake profiles, using automated bots to send bulk requests, scraping or copying platform data without authorization, attempting to access other accounts, performing actions that degrade service stability or sending spam and commercial advertising.',
          'Accounts may be suspended without notice and legal action may be pursued where misuse is identified.'
        ]
      },
      {
        id: 'billing',
        number: '5',
        title: 'Pricing and subscriptions',
        body: [
          'NoyTera may offer core features free of charge. Advanced capabilities may be available under paid plans.',
          'A basic plan may provide standard matching and limited AI advisor access. Professional plans may include broader match visibility, deeper AI access or higher-priority usage layers.',
          'Subscription billing may be monthly or yearly. Cancellation becomes effective in the next billing cycle unless otherwise stated. Partial refunds are not provided unless explicitly required.'
        ]
      },
      {
        id: 'ip',
        number: '6',
        title: 'Intellectual property rights',
        body: [
          'All content, design elements, software code, algorithms, logos and brand assets on the platform are the exclusive property of NoyTera and are protected under applicable intellectual property laws.',
          'Users retain ownership of the CV and profile information they upload. NoyTera may process such data only to provide the service.',
          'Commercial redistribution, resale or relicensing of platform-derived content is strictly prohibited.'
        ]
      },
      {
        id: 'liability',
        number: '7',
        title: 'Limitation of liability',
        body: [
          'NoyTera does not accept liability for the accuracy or freshness of listings collected from third-party platforms, employer decisions, application outcomes, losses caused by user error, connectivity problems or force majeure events.'
        ]
      },
      {
        id: 'termination',
        number: '8',
        title: 'Account suspension and termination',
        body: [
          'NoyTera may suspend or permanently remove an account without notice in cases such as breach of these terms, false or misleading information, attempts to harm other users or the platform, or non-compliance with payment obligations.',
          'Users may also terminate their account through support or relevant profile settings. Data handling after closure follows the privacy policy and applicable legal requirements.'
        ]
      },
      {
        id: 'disputes',
        number: '9',
        title: 'Dispute resolution',
        body: [
          'Disputes arising from these terms should first be addressed through good-faith negotiation. If unresolved, the courts of the Republic of Türkiye and Turkish law shall apply.'
        ]
      },
      {
        id: 'changes',
        number: '10',
        title: 'Changes to the terms',
        body: [
          'NoyTera reserves the right to update these terms when necessary. Material changes may be communicated through email or platform notifications.'
        ]
      },
      {
        id: 'contact',
        number: '11',
        title: 'Contact',
        body: ['For questions regarding these terms: legal@noytera.com']
      }
    ]
  },
  de: {
    title: 'Nutzungsbedingungen',
    intro:
      'Dieses Dokument ist für alle Nutzer der NoyTera-Plattform verbindlich. Durch Registrierung oder Zugriff erklärst du, dass du diese Bedingungen gelesen, verstanden und akzeptiert hast.',
    update: 'Zuletzt aktualisiert: April 2025 · Version 1.2',
    toc: 'Inhalt',
    otherTab: 'Datenschutzrichtlinie',
    back: 'Zur Registrierung',
    sections: [
      {
        id: 'parties',
        number: '1',
        title: 'Parteien und Geltungsbereich',
        body: [
          'Diese Nutzungsbedingungen regeln das Verhältnis zwischen NoyTera, dem Unternehmen hinter der Plattform, und den natürlichen Personen, die sich registrieren oder die Plattform auf andere Weise nutzen.',
          'Die Bedingungen gelten für alle digitalen Dienste von NoyTera, einschließlich Website, mobiler Anwendungen und API-Oberflächen.',
          'Wichtig: Personen unter 18 Jahren dürfen sich nicht für die Plattform registrieren.'
        ]
      },
      {
        id: 'service',
        number: '2',
        title: 'Leistungsbeschreibung',
        body: [
          'NoyTera ist eine Karriereplattform, die KI-gestützte Jobentdeckung und Matching-Funktionen für Jobsuchende anbietet.',
          'Zu den Kernfunktionen gehören CV-Upload und Analyse, plattformübergreifende Stellenaggregation, KI-basiertes Matching, ein KI-Karriereberater und ein Profil-Vervollständigungs-Score.',
          'NoyTera ist keine Personalvermittlung, die Stellen direkt veröffentlicht. Positionen werden von Drittplattformen aggregiert; Aktualität und Richtigkeit können nicht garantiert werden.'
        ]
      },
      {
        id: 'account-security',
        number: '3',
        title: 'Kontoerstellung und Sicherheit',
        body: [
          'Für den Zugriff auf die Plattform ist eine Registrierung mit gültiger E-Mail-Adresse und abgeschlossener E-Mail-Bestätigung erforderlich. Jede natürliche Person darf nur ein Konto anlegen.',
          'Nutzer sind verantwortlich für den Schutz ihrer Zugangsdaten, die Wahl eines starken Passworts, die sofortige Meldung unbefugter Zugriffe, die Nichtverwendung fremder Identitäten und das Abmelden auf gemeinsam genutzten Geräten.',
          'Alle Aktivitäten über dein Konto liegen in deiner Verantwortung.'
        ]
      },
      {
        id: 'usage-rules',
        number: '4',
        title: 'Nutzungsregeln und verbotene Handlungen',
        body: [
          'Die Plattform darf ausschließlich für persönliche Jobsuche genutzt werden.',
          'Streng untersagt sind unter anderem: das Erstellen gefälschter Profile, automatisierte Massenanfragen durch Bots, unbefugtes Scraping oder Kopieren von Plattformdaten, Zugriffsversuche auf andere Konten, Handlungen zur Beeinträchtigung der Stabilität sowie Spam oder kommerzielle Werbung.',
          'Konten können bei Missbrauch ohne Vorankündigung gesperrt werden; bei Bedarf können rechtliche Schritte eingeleitet werden.'
        ]
      },
      {
        id: 'billing',
        number: '5',
        title: 'Preise und Abonnements',
        body: [
          'NoyTera kann Kernfunktionen kostenlos anbieten. Erweiterte Funktionen können in kostenpflichtigen Tarifen enthalten sein.',
          'Ein Basisplan kann Standard-Matching und begrenzten KI-Berater-Zugang umfassen. Professionelle Tarife können breitere Match-Sichtbarkeit, tiefere KI-Nutzung oder priorisierte Nutzungsebenen bieten.',
          'Abrechnungen können monatlich oder jährlich erfolgen. Kündigungen wirken zum nächsten Abrechnungszeitraum, sofern nichts anderes angegeben ist. Teilrückerstattungen erfolgen nur, wenn dies ausdrücklich vorgesehen ist.'
        ]
      },
      {
        id: 'ip',
        number: '6',
        title: 'Rechte am geistigen Eigentum',
        body: [
          'Sämtliche Inhalte, Designs, Softwarebestandteile, Algorithmen, Logos und Marken auf der Plattform sind ausschließliches Eigentum von NoyTera und durch geltende Schutzrechte abgesichert.',
          'Nutzer behalten das Eigentum an den hochgeladenen Lebensläufen und Profildaten. NoyTera darf diese Daten nur zum Zweck der Leistungserbringung verarbeiten.',
          'Die kommerzielle Weiterveröffentlichung, der Weiterverkauf oder die Weiterlizenzierung von Plattforminhalten ist ausdrücklich untersagt.'
        ]
      },
      {
        id: 'liability',
        number: '7',
        title: 'Haftungsbeschränkung',
        body: [
          'NoyTera übernimmt keine Haftung für Richtigkeit oder Aktualität von Stellenanzeigen aus Drittquellen, Entscheidungen von Arbeitgebern, Bewerbungsergebnisse, durch Nutzerfehler verursachte Verluste, Verbindungsprobleme oder Fälle höherer Gewalt.'
        ]
      },
      {
        id: 'termination',
        number: '8',
        title: 'Sperrung und Beendigung von Konten',
        body: [
          'NoyTera kann Konten ohne Vorankündigung sperren oder dauerhaft löschen, etwa bei Verstößen gegen diese Bedingungen, falschen Angaben, Schädigungsversuchen gegenüber anderen Nutzern oder der Plattform oder bei Nichterfüllung von Zahlungspflichten.',
          'Nutzer können ihr Konto ebenfalls über den Support oder passende Profileinstellungen beenden. Die Datenverarbeitung nach der Schließung richtet sich nach der Datenschutzrichtlinie und den geltenden gesetzlichen Anforderungen.'
        ]
      },
      {
        id: 'disputes',
        number: '9',
        title: 'Streitbeilegung',
        body: [
          'Streitigkeiten aus diesen Bedingungen sollen zunächst im Wege einer einvernehmlichen Verhandlung gelöst werden. Bleibt dies erfolglos, gelten die Gerichte der Republik Türkei und türkisches Recht.'
        ]
      },
      {
        id: 'changes',
        number: '10',
        title: 'Änderungen der Bedingungen',
        body: [
          'NoyTera behält sich das Recht vor, diese Bedingungen bei Bedarf zu aktualisieren. Wesentliche Änderungen können per E-Mail oder über Plattformhinweise kommuniziert werden.'
        ]
      },
      {
        id: 'contact',
        number: '11',
        title: 'Kontakt',
        body: ['Fragen zu diesen Bedingungen: legal@noytera.com']
      }
    ]
  }
} as const;

export default async function TermsPage({
  params
}: {
  params: Promise<{locale: string}>;
}) {
  const {locale: rawLocale} = await params;
  const locale = resolveLocale(rawLocale);
  const t = copy[locale];

  return (
    <MarketingPageShell locale={locale}>
      <section className="container-shell py-16">
        <div className="overflow-hidden rounded-[32px] border border-white/10 bg-[#101828] shadow-[0_24px_90px_rgba(0,0,0,0.28)]">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/8 px-6 py-5">
            <BrandLogo locale={locale} size="md" />

            <div className="flex gap-3">
              <span className="rounded-2xl border border-[#4b61ff]/40 bg-[#14245c] px-4 py-3 text-sm font-medium text-white">
                {t.title}
              </span>
              <Link
                href={`/${locale}/privacy`}
                className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm font-medium text-white/72 transition hover:border-[#4b61ff]/40 hover:text-white"
              >
                {t.otherTab}
              </Link>
            </div>
          </div>

          <div className="grid lg:grid-cols-[300px_minmax(0,1fr)]">
            <aside className="border-r border-white/8 bg-[#0f1727] p-5">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-white/35">
                {t.toc}
              </div>

              <nav className="mt-4 space-y-1">
                {t.sections.map((section) => (
                  <a
                    key={section.id}
                    href={`#${section.id}`}
                    className="flex items-center gap-3 rounded-xl px-3 py-2 text-sm text-white/68 transition hover:bg-white/5 hover:text-white"
                  >
                    <span className="inline-flex size-6 items-center justify-center rounded-md bg-[#1a2d72] text-xs font-semibold text-white">
                      {section.number}
                    </span>
                    <span>{section.title}</span>
                  </a>
                ))}
              </nav>
            </aside>

            <div className="p-6 md:p-8">
              <div className="inline-flex rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm text-white/58">
                {t.update}
              </div>

              <h1 className="mt-6 text-4xl font-semibold tracking-tight text-white">{t.title}</h1>
              <p className="mt-4 max-w-3xl text-base leading-8 text-white/64">{t.intro}</p>

              <div className="mt-10 space-y-10">
                {t.sections.map((section) => (
                  <section
                    key={section.id}
                    id={section.id}
                    className="border-b border-white/8 pb-10 last:border-b-0 last:pb-0"
                  >
                    <div className="mb-4 inline-flex size-7 items-center justify-center rounded-md bg-[#1a2d72] text-sm font-semibold text-white">
                      {section.number}
                    </div>
                    <h2 className="text-2xl font-semibold text-white">{section.title}</h2>
                    <div className="mt-4 space-y-4">
                      {section.body.map((paragraph) => (
                        <p key={paragraph} className="text-base leading-8 text-white/64">
                          {paragraph}
                        </p>
                      ))}
                    </div>
                  </section>
                ))}
              </div>

              <div className="mt-10 flex justify-end">
                <Link
                  href={`/${locale}/signup`}
                  className="inline-flex items-center rounded-2xl border border-white/12 bg-[#3b52f0] px-6 py-3 text-sm font-semibold text-white transition hover:bg-[#3348da]"
                >
                  {t.back}
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </MarketingPageShell>
  );
}
