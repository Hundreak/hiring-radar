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
    title: 'Gizlilik politikası',
    intro:
      'Bu belge, NoyTera platformunun kişisel verilerinizi nasıl topladığını, işlediğini, sakladığını ve koruduğunu açıklar. KVKK ve ilgili mevzuat çerçevesinde hazırlanmıştır.',
    update: 'Son güncelleme: Nisan 2025 · KVKK Uyumlu',
    toc: 'İçindekiler',
    otherTab: 'Kullanım şartları',
    back: 'Kayıt ekranına dön',
    sections: [
      {
        id: 'controller',
        number: '1',
        title: 'Veri sorumlusu',
        body: [
          'Kişisel verilerinizin işlenmesinden sorumlu veri sorumlusu NoyTera’tir. KVKK kapsamındaki taleplerinizi privacy@noytera.com adresine iletebilirsiniz.',
          'NoyTera, verilerinizi yalnızca bu politikada belirtilen amaçlar doğrultusunda işler. Hiçbir koşulda reklam amacıyla üçüncü taraflarla paylaşmaz veya satmaz.'
        ]
      },
      {
        id: 'data-collected',
        number: '2',
        title: 'Toplanan kişisel veriler',
        body: [
          'Doğrudan sağladığınız veriler: ad, soyad, e-posta adresi, CV içeriği, iş deneyimi, eğitim bilgisi, beceriler, sertifikalar, çalışma tercihleri, maaş beklentisi, konum ve pozisyon türü.',
          'Otomatik toplanan veriler: görüntülenen ilanlar, yapılan başvurular, arama sorguları, IP adresi, tarayıcı türü, işletim sistemi, cihaz tipi, giriş zamanı, oturum süresi ve platform içi hareket verileri.'
        ]
      },
      {
        id: 'purposes',
        number: '3',
        title: 'Verilerin işlenme amaçları',
        body: [
          'İş ilanı eşleştirme algoritmasının çalıştırılması ve sonuçların kişiselleştirilmesi, yapay zeka kariyer danışmanı hizmetinin sunulması, hesap oluşturma ve güvenlik süreçlerinin yönetimi, profil tamamlama önerilerinin üretilmesi, platform performansının izlenmesi ve yasal yükümlülüklerin yerine getirilmesi.'
        ]
      },
      {
        id: 'legal-basis',
        number: '4',
        title: 'Hukuki işleme dayanakları',
        body: [
          'Sözleşmenin ifası: hizmet sunumu için zorunlu veriler.',
          'Meşru menfaat: platform güvenliği ve iyileştirme faaliyetleri.',
          'Açık rıza: pazarlama bildirimleri ve isteğe bağlı analitik çerezler.',
          'Yasal yükümlülük: resmi mercilere zorunlu bildirimler.'
        ]
      },
      {
        id: 'sharing',
        number: '5',
        title: 'Veri paylaşımı ve aktarımı',
        body: [
          'Verileriniz; altyapı sağlayıcıları, bulut depolama ve sunucu hizmetleri, e-posta gönderim altyapısı ve yasal zorunluluklar kapsamında sınırlı olarak paylaşılabilir.',
          'Verileriniz hiçbir koşulda reklam ağlarına, veri komisyoncularına veya işe alım ajanslarına izinsiz satılmaz ya da kiralanmaz.'
        ]
      },
      {
        id: 'retention',
        number: '6',
        title: 'Veri saklama süreleri',
        body: [
          'Aktif hesap verileri hesap aktif olduğu sürece saklanır.',
          'Hesap silme sonrası kişisel veriler uygun süreçler çerçevesinde imha edilir.',
          'Finansal kayıtlar vergi mevzuatı gereği ilgili süre kadar saklanabilir.',
          'Log kayıtları güvenlik amacıyla sınırlı sürelerle tutulur.'
        ]
      },
      {
        id: 'cookies',
        number: '7',
        title: 'Çerezler',
        body: [
          'Zorunlu çerezler oturum yönetimi için gereklidir ve devre dışı bırakılamaz.',
          'Analitik çerezler platform kullanımını anlamak için, gerekli olduğu ölçüde ve ilgili onay süreçleriyle çalıştırılır.',
          'Tercih çerezleri dil veya belirli görünüm ayarlarını hatırlamak için kullanılabilir.'
        ]
      },
      {
        id: 'rights',
        number: '8',
        title: 'KVKK kapsamındaki haklarınız',
        body: [
          'Kişisel verilerinizin işlenip işlenmediğini öğrenme, eksik veya yanlış işlenmiş verilerin düzeltilmesini isteme, yasal koşullar çerçevesinde silinmesini veya yok edilmesini isteme, otomatik sistemler aracılığıyla aleyhinize sonuç doğuran kararlara itiraz etme ve kanuna aykırı işleme nedeniyle uğradığınız zararın giderilmesini talep etme haklarına sahipsiniz.',
          'Haklarınızı kullanmak için privacy@noytera.com adresine yazabilirsiniz. Talepler en geç 30 gün içinde yanıtlanır.'
        ]
      },
      {
        id: 'security',
        number: '9',
        title: 'Güvenlik önlemleri',
        body: [
          'Tüm veri iletimi güncel şifreleme protokolleri ile korunur.',
          'Şifreler güçlü hash algoritmaları ile saklanır.',
          'Veritabanı erişimi rol tabanlı yetkilendirme ile sınırlandırılır.',
          'Düzenli güvenlik denetimleri ve sızma testleri uygulanabilir.',
          'Uygun olduğu yerlerde çok faktörlü doğrulama desteği sunulabilir.'
        ]
      },
      {
        id: 'children',
        number: '10',
        title: 'Çocukların gizliliği',
        body: [
          'NoyTera hizmetleri 18 yaşından küçük bireylere yönelik değildir. Platform bilerek 18 yaş altı kullanıcılara ait veri toplamaz.'
        ]
      },
      {
        id: 'contact',
        number: '11',
        title: 'İletişim',
        body: [
          'Gizlilik politikasına ilişkin sorularınız için: privacy@noytera.com',
          'Kişisel Verileri Koruma Kurulu hakkında genel bilgi için resmî kurum kaynakları ayrıca incelenebilir.'
        ]
      }
    ]
  },
  en: {
    title: 'Privacy policy',
    intro:
      'This document explains how the NoyTera platform collects, processes, stores and protects your personal data. It is prepared in line with applicable privacy and data protection obligations.',
    update: 'Last updated: April 2025 · Privacy compliant',
    toc: 'Contents',
    otherTab: 'Terms of use',
    back: 'Back to sign up',
    sections: [
      {
        id: 'controller',
        number: '1',
        title: 'Data controller',
        body: [
          'NoyTera is the data controller responsible for processing your personal data. You may submit privacy-related requests to privacy@noytera.com.',
          'NoyTera processes data only for the purposes described in this policy and does not sell or share personal data for advertising purposes.'
        ]
      },
      {
        id: 'data-collected',
        number: '2',
        title: 'Personal data collected',
        body: [
          'Data you provide directly may include your name, email address, CV content, work history, education, skills, certifications, working preferences, salary expectations, location and position type.',
          'Automatically collected data may include viewed listings, applications, search queries, IP address, browser type, operating system, device type, session times and in-product activity signals.'
        ]
      },
      {
        id: 'purposes',
        number: '3',
        title: 'Purposes of processing',
        body: [
          'Data may be processed to power job matching, personalize results, provide the AI career advisor, manage account security and verification, generate profile completion guidance, improve platform performance and satisfy legal obligations.'
        ]
      },
      {
        id: 'legal-basis',
        number: '4',
        title: 'Legal bases for processing',
        body: [
          'Performance of a contract: data required to deliver the service.',
          'Legitimate interest: security, fraud prevention and product improvement.',
          'Consent: optional marketing communications and certain analytics technologies where required.',
          'Legal obligation: mandatory disclosures to competent authorities.'
        ]
      },
      {
        id: 'sharing',
        number: '5',
        title: 'Data sharing and transfers',
        body: [
          'Your data may be shared on a limited basis with infrastructure providers, cloud hosting services, email delivery vendors and public authorities where legally required.',
          'Your data is never sold or rented to ad networks, data brokers or recruitment agencies without authorization.'
        ]
      },
      {
        id: 'retention',
        number: '6',
        title: 'Data retention periods',
        body: [
          'Active account data is retained for as long as the account remains active.',
          'After account deletion, personal data is removed or anonymized in line with operational and legal requirements.',
          'Certain financial and logging records may be retained for statutory compliance and security purposes for limited periods.'
        ]
      },
      {
        id: 'cookies',
        number: '7',
        title: 'Cookies',
        body: [
          'Strictly necessary cookies are used to manage sessions and core platform operation.',
          'Analytics technologies may be used to understand product usage, subject to applicable consent requirements.',
          'Preference cookies may remember language and selected interface settings.'
        ]
      },
      {
        id: 'rights',
        number: '8',
        title: 'Your privacy rights',
        body: [
          'Subject to applicable law, you may request access to your data, correction of inaccurate information, deletion where legally available, objection to certain automated processing outcomes and compensation where unlawful processing causes damage.',
          'You may send privacy requests to privacy@noytera.com and requests are answered within the legally required timeframe.'
        ]
      },
      {
        id: 'security',
        number: '9',
        title: 'Security measures',
        body: [
          'Data transmission is protected using current encryption standards.',
          'Passwords are stored using strong hashing algorithms.',
          'Database access is restricted using role-based authorization.',
          'Security reviews, monitoring and penetration-testing practices may be applied where appropriate.',
          'Multi-factor authentication support may be offered for sensitive workflows.'
        ]
      },
      {
        id: 'children',
        number: '10',
        title: 'Children’s privacy',
        body: [
          'NoyTera services are not intended for individuals under 18 years of age and the platform does not knowingly collect personal data from children.'
        ]
      },
      {
        id: 'contact',
        number: '11',
        title: 'Contact',
        body: [
          'For privacy-related questions: privacy@noytera.com',
          'Users may also review relevant public authority resources for broader regulatory guidance.'
        ]
      }
    ]
  },
  de: {
    title: 'Datenschutzrichtlinie',
    intro:
      'Dieses Dokument erläutert, wie die NoyTera-Plattform deine personenbezogenen Daten erhebt, verarbeitet, speichert und schützt. Es wurde im Einklang mit geltenden Datenschutzpflichten erstellt.',
    update: 'Zuletzt aktualisiert: April 2025 · Datenschutzkonform',
    toc: 'Inhalt',
    otherTab: 'Nutzungsbedingungen',
    back: 'Zur Registrierung',
    sections: [
      {
        id: 'controller',
        number: '1',
        title: 'Verantwortliche Stelle',
        body: [
          'NoyTera ist die verantwortliche Stelle für die Verarbeitung deiner personenbezogenen Daten. Datenschutzanfragen können an privacy@noytera.com gesendet werden.',
          'NoyTera verarbeitet Daten ausschließlich für die in dieser Richtlinie beschriebenen Zwecke und verkauft oder teilt personenbezogene Daten nicht zu Werbezwecken.'
        ]
      },
      {
        id: 'data-collected',
        number: '2',
        title: 'Erhobene personenbezogene Daten',
        body: [
          'Direkt bereitgestellte Daten können Name, E-Mail-Adresse, Lebenslauf-Inhalte, Berufserfahrung, Ausbildung, Fähigkeiten, Zertifikate, Arbeitspräferenzen, Gehaltsvorstellungen, Standort und Positionstyp umfassen.',
          'Automatisch erhobene Daten können aufgerufene Stellenanzeigen, Bewerbungen, Suchanfragen, IP-Adresse, Browsertyp, Betriebssystem, Gerätetyp, Sitzungszeiten und Nutzungsaktivitäten umfassen.'
        ]
      },
      {
        id: 'purposes',
        number: '3',
        title: 'Zwecke der Verarbeitung',
        body: [
          'Daten können verarbeitet werden, um Job-Matching zu ermöglichen, Ergebnisse zu personalisieren, den KI-Karriereberater bereitzustellen, Kontosicherheit und Verifizierung zu verwalten, Hinweise zur Profilvervollständigung zu erzeugen, die Plattform zu verbessern und gesetzliche Pflichten zu erfüllen.'
        ]
      },
      {
        id: 'legal-basis',
        number: '4',
        title: 'Rechtsgrundlagen der Verarbeitung',
        body: [
          'Vertragserfüllung: Daten, die zur Bereitstellung des Dienstes erforderlich sind.',
          'Berechtigtes Interesse: Sicherheit, Missbrauchsprävention und Produktverbesserung.',
          'Einwilligung: optionale Marketingkommunikation und bestimmte Analyse-Technologien, soweit erforderlich.',
          'Gesetzliche Verpflichtung: vorgeschriebene Offenlegungen gegenüber zuständigen Behörden.'
        ]
      },
      {
        id: 'sharing',
        number: '5',
        title: 'Datenweitergabe und Übermittlung',
        body: [
          'Deine Daten können in begrenztem Umfang mit Infrastruktur-Anbietern, Cloud-Hosting-Diensten, E-Mail-Versanddienstleistern und Behörden geteilt werden, wenn dies rechtlich erforderlich ist.',
          'Deine Daten werden niemals ohne Zustimmung an Werbenetzwerke, Datenhändler oder Vermittlungsagenturen verkauft oder vermietet.'
        ]
      },
      {
        id: 'retention',
        number: '6',
        title: 'Speicherdauer',
        body: [
          'Aktive Kontodaten werden so lange gespeichert, wie das Konto aktiv bleibt.',
          'Nach Kontolöschung werden personenbezogene Daten entsprechend den operativen und gesetzlichen Anforderungen entfernt oder anonymisiert.',
          'Bestimmte Finanz- und Protokolldaten können für gesetzliche Compliance und Sicherheitszwecke für begrenzte Zeiträume gespeichert werden.'
        ]
      },
      {
        id: 'cookies',
        number: '7',
        title: 'Cookies',
        body: [
          'Unbedingt erforderliche Cookies werden für Sitzungsverwaltung und Kernfunktionen der Plattform verwendet.',
          'Analyse-Technologien können eingesetzt werden, um die Produktnutzung zu verstehen, vorbehaltlich anwendbarer Einwilligungspflichten.',
          'Präferenz-Cookies können Sprache und ausgewählte Oberflächeneinstellungen speichern.'
        ]
      },
      {
        id: 'rights',
        number: '8',
        title: 'Deine Datenschutzrechte',
        body: [
          'Je nach geltendem Recht kannst du Zugang zu deinen Daten, Berichtigung unrichtiger Informationen, Löschung, Widerspruch gegen bestimmte automatisierte Entscheidungen und Schadensersatz bei unrechtmäßiger Verarbeitung verlangen.',
          'Datenschutzanfragen können an privacy@noytera.com gerichtet werden und werden innerhalb der gesetzlich vorgesehenen Frist beantwortet.'
        ]
      },
      {
        id: 'security',
        number: '9',
        title: 'Sicherheitsmaßnahmen',
        body: [
          'Die Datenübertragung wird mit aktuellen Verschlüsselungsstandards geschützt.',
          'Passwörter werden mit starken Hash-Verfahren gespeichert.',
          'Der Zugriff auf Datenbanken wird rollenbasiert beschränkt.',
          'Sicherheitsprüfungen, Monitoring und Penetration-Testing können je nach Bedarf durchgeführt werden.',
          'Für sensible Prozesse kann Unterstützung für Mehrfaktor-Authentifizierung angeboten werden.'
        ]
      },
      {
        id: 'children',
        number: '10',
        title: 'Datenschutz von Minderjährigen',
        body: [
          'Die Dienste von NoyTera richten sich nicht an Personen unter 18 Jahren, und die Plattform sammelt wissentlich keine personenbezogenen Daten von Kindern.'
        ]
      },
      {
        id: 'contact',
        number: '11',
        title: 'Kontakt',
        body: [
          'Für Fragen zum Datenschutz: privacy@noytera.com',
          'Zusätzlich können einschlägige öffentliche Quellen zu regulatorischen Anforderungen eingesehen werden.'
        ]
      }
    ]
  }
} as const;

export default async function PrivacyPage({
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
              <Link
                href={`/${locale}/terms`}
                className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm font-medium text-white/72 transition hover:border-[#4b61ff]/40 hover:text-white"
              >
                {t.otherTab}
              </Link>
              <span className="rounded-2xl border border-[#4b61ff]/40 bg-[#14245c] px-4 py-3 text-sm font-medium text-white">
                {t.title}
              </span>
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
