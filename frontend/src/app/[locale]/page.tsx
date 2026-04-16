import {ArrowRight, Clock3, Search, Sparkles, Star, Target} from 'lucide-react';

import {LandingHero} from '@/components/landing/hero';
import {PublicFooter} from '@/components/layout/public-footer';
import {PublicHeader} from '@/components/layout/public-header';
import type {SupportedLocale} from '@/types/user';

function resolveLocale(locale: string): SupportedLocale {
  if (locale === 'tr' || locale === 'en' || locale === 'de') return locale;
  return 'tr';
}

const pageCopy = {
  tr: {
    stats: [
      {value: '12K+', label: 'Aktif ilan'},
      {value: '94%', label: 'Eşleşme doğruluğu'},
      {value: '3×', label: 'Daha hızlı başvuru'},
      {value: '40+', label: 'Platform entegrasyonu'}
    ],
    features: [
      {
        title: 'Tüm platformları tek yerden tara',
        description:
          'LinkedIn, kariyer siteleri ve farklı kaynaklardan gelen ilanları tek üründe birleştir. Ayrı ayrı sekmelerde kaybolmadan tüm fırsatları gör.'
      },
      {
        title: 'Profiline göre akıllı eşleştirme',
        description:
          'CV’ni, becerilerini ve tercihlerini anlayan sistem; uyum puanıyla en güçlü fırsatları öne çıkarır ve odaklanmanı kolaylaştırır.'
      },
      {
        title: 'Eksikleri gör, profili güçlendir',
        description:
          'Hangi bilgi eksik, hangi sinyal zayıf; net biçimde gör. Profil kaliten arttıkça daha güçlü ve daha açıklanabilir eşleşmeler üret.'
      }
    ],
    how: {
      eyebrow: 'Nasıl çalışır?',
      title: '4 adımda işe alım radarın devrede',
      description: 'Profilini oluştur, taramayı başlat, en iyi eşleşmeleri gör ve başvur.',
      steps: [
        {
          title: "CV'ni yükle",
          description: 'PDF veya Word. Sistem tüm verilerini otomatik çeker. 2 dakika yeter.'
        },
        {
          title: 'Profili tamamla',
          description: 'Her eklediğin bilgiyle eşleşme skoru yükselir. Eksik alanlar sana gösterilir.'
        },
        {
          title: 'Eşleşmeleri gör',
          description: '40+ platformdan gelen ilanlar, profilinle kıyaslanıp uyum puanıyla sıralanır.'
        },
        {
          title: 'Tek tıkla başvur',
          description: 'Yapay zeka danışmanınla strateji geliştir, hazır olduğunda başvur.'
        }
      ]
    },
    profileEngine: {
      eyebrow: 'Profil Motoru',
      title: 'Profilini geliştirdikçe, eşleşmeler iyileşir',
      description:
        'Sistem seni ne kadar tanırsa, o kadar isabetli ilanlar gösterir. Eksik alanlarını gör ve doldur.',
      chartTitle: 'Profil tamamlama etkisi — eşleşme kalitesi',
      chartRows: [
        ['Sadece CV yükledim', 55, '%55 ort. uyum'],
        ['Becerilerimi ekledim', 68, '%68 ort. uyum'],
        ['Deneyim detayları girildi', 78, '%78 ort. uyum'],
        ['Tercihlerimi belirttim', 91, '%91 ort. uyum']
      ] as const,
      note:
        'Her eksik alan, sana uygun ilanları kaçırmana neden olabilir. Sistem profilini ne kadar bilirse, o kadar isabetli sıralar.',
      points: [
        {
          title: 'Eksik alanları sana gösterir',
          description: 'Hangi profil alanının eşleşme kaliteni düşürdüğünü net olarak görürsün.'
        },
        {
          title: 'Gerçek zamanlı güncelleme',
          description: 'Yeni bir beceri ekler eklemez eşleşmeler anında yeniden sıralanır.'
        },
        {
          title: 'Profilin ne kadar güçlü?',
          description: 'Tamamlanma skoru ile her adımda ilerlemeyi somut olarak görürsün.'
        }
      ]
    },
    ai: {
      eyebrow: 'Yapay Zeka Desteği',
      title: 'Sadece iş bulma aracı değil, kariyer danışmanın',
      description:
        'CV analizi, strateji geliştirme, başvuru hazırlığı — her şey tek yerde.',
      assistantName: 'CoreSift AI',
      status: 'Aktif',
      inputPlaceholder: 'Bir şey sor…',
      bubbles: [
        {
          role: 'ai',
          text: 'Merhaba! CV’ni analiz ettim. React ve TypeScript tarafında güçlü bir profilin var. Ancak sistem tasarımı deneyimi eklersen öne çıkan mühendislik pozisyonlarında eşleşme skorun ciddi artacak.'
        },
        {
          role: 'user',
          text: 'Hangi pozisyonlara odaklanmalıyım?'
        },
        {
          role: 'ai',
          text: 'Profiline göre en yüksek uyum Senior Frontend ve Full Stack pozisyonlarında. Şu an 3 ilan %85 üzerinde skor gösteriyor — birlikte başvuru stratejisi geliştirelim mi?'
        }
      ],
      features: [
        {
          title: 'CV analizi ve geliştirme önerileri',
          description:
            'Yapay zeka CV’ni okur, güçlü ve zayıf yönlerini belirler. Hangi alanlarda gelişirsen daha fazla ilana uyacağını somut olarak söyler.'
        },
        {
          title: 'Başvuru stratejisi geliştirme',
          description:
            'Hangi pozisyona önce başvurmalısın? Hangi şirketler profiline daha uygun? AI ile konuşarak en doğru adımı belirle.'
        },
        {
          title: 'Mülakat hazırlık desteği',
          description:
            'Başvurduğun pozisyon için olası soruları, şirket bilgilerini ve nasıl hazırlanacağını yapay zekandan anında al.'
        }
      ]
    },
    testimonials: {
      eyebrow: 'Kullanıcı Yorumları',
      title: 'İş arayanlar ne diyor?',
      items: [
        {
          initials: 'AK',
          color: 'bg-[#3b52f0]',
          quote:
            '“CV’mi yükledim, sistem eksik alanlarımı gösterdi. 2 alanı doldurdum ve eşleşme skorumu hemen arttı. 10 günde 3 mülakat aldım.”',
          name: 'Ahmet K.',
          role: 'Frontend Developer'
        },
        {
          initials: 'MB',
          color: 'bg-[#16a34a]',
          quote:
            '“AI danışmanla strateji konuştum, hangi pozisyonlara odaklanacağımı anladım. Daha önce hiç böyle bir araç kullanmamıştım.”',
          name: 'Merve B.',
          role: 'Data Analyst'
        },
        {
          initials: 'CE',
          color: 'bg-[#f59e0b]',
          quote:
            '“Profil skorumu %45’ten %88’e çıkardım. O andan itibaren gelen ilan önerileri tamamen değişti. Çok daha isabetli oldu.”',
          name: 'Can E.',
          role: 'DevOps Engineer'
        }
      ]
    },
    cta: {
      badge: "CV'ni yükle, gerisini biz halledelim",
      titlePrefix: 'İş aramanın yolu',
      titleAccent: 'değişti.',
      description:
        'CV’ni yükle, profilini tamamla ve yapay zeka destekli eşleştirme sistemiyle sana uygun ilanları keşfet.',
      button: "CV'mi yükle ve başla",
      notes: ['Kredi kartı yok', 'Kurulum yok', '2 dakikada hazır']
    }
  },
  en: {
    stats: [
      {value: '12K+', label: 'Active jobs'},
      {value: '94%', label: 'Match accuracy'},
      {value: '3×', label: 'Faster applications'},
      {value: '40+', label: 'Platform integrations'}
    ],
    features: [
      {
        title: 'Search every platform from one place',
        description:
          'Bring LinkedIn, job boards and other sources into one product surface instead of losing time across multiple tabs.'
      },
      {
        title: 'Intelligent profile-based matching',
        description:
          'The system understands your CV, skills and preferences, then surfaces stronger-fit opportunities with a clear score.'
      },
      {
        title: 'See what is missing and strengthen the profile',
        description:
          'Know which signals are incomplete or weak. As your profile improves, the system produces sharper and more explainable matches.'
      }
    ],
    how: {
      eyebrow: 'How it works',
      title: 'Your hiring radar in 4 steps',
      description: 'Build the profile, launch the scan, review the best matches and apply.',
      steps: [
        {
          title: 'Upload your CV',
          description: 'PDF or Word. The system extracts your signals automatically. It takes about 2 minutes.'
        },
        {
          title: 'Complete your profile',
          description: 'Every added signal improves your match score. Missing fields are shown clearly.'
        },
        {
          title: 'Review your matches',
          description: 'Roles from 40+ sources are ranked against your profile with a fit score.'
        },
        {
          title: 'Apply with confidence',
          description: 'Use your AI advisor to shape the strategy, then apply when you are ready.'
        }
      ]
    },
    profileEngine: {
      eyebrow: 'Profile Engine',
      title: 'As your profile improves, your matches get better',
      description:
        'The better the system understands you, the more accurate the role suggestions become.',
      chartTitle: 'Profile completion effect — match quality',
      chartRows: [
        ['Only CV uploaded', 55, '55% avg. fit'],
        ['Skills added', 68, '68% avg. fit'],
        ['Experience detail entered', 78, '78% avg. fit'],
        ['Preferences selected', 91, '91% avg. fit']
      ] as const,
      note:
        'Every missing signal can make you lose relevant opportunities. The more clearly the system knows your profile, the more accurate the ranking becomes.',
      points: [
        {
          title: 'See missing areas clearly',
          description: 'You can understand which profile areas are lowering your match quality.'
        },
        {
          title: 'Real-time updates',
          description: 'The moment you add a new skill, the ranking refreshes immediately.'
        },
        {
          title: 'How strong is your profile?',
          description: 'See your progress step by step through a completion score.'
        }
      ]
    },
    ai: {
      eyebrow: 'AI Support',
      title: 'Not just a job tool, but your career advisor',
      description:
        'CV analysis, strategy guidance and application preparation — everything in one place.',
      assistantName: 'CoreSift AI',
      status: 'Active',
      inputPlaceholder: 'Ask something…',
      bubbles: [
        {
          role: 'ai',
          text: 'Hello! I analyzed your CV. You are strong in React and TypeScript. If you add system design experience, your score for high-signal engineering roles can increase significantly.'
        },
        {
          role: 'user',
          text: 'Which positions should I focus on?'
        },
        {
          role: 'ai',
          text: 'Your strongest fit is currently Senior Frontend and Full Stack roles. Three open positions are already above 85% — would you like to define an application strategy together?'
        }
      ],
      features: [
        {
          title: 'CV analysis and improvement suggestions',
          description:
            'AI reads your CV, identifies strengths and weak areas, and shows which improvements can unlock more relevant roles.'
        },
        {
          title: 'Application strategy guidance',
          description:
            'Which role should you apply to first? Which companies fit you better? Talk to the AI and shape the right next step.'
        },
        {
          title: 'Interview preparation support',
          description:
            'Get likely questions, company context and preparation guidance tailored to the role you plan to pursue.'
        }
      ]
    },
    testimonials: {
      eyebrow: 'User Feedback',
      title: 'What job seekers say',
      items: [
        {
          initials: 'AK',
          color: 'bg-[#3b52f0]',
          quote:
            '“I uploaded my CV, filled the missing fields the system showed me, and my score improved immediately. I got 3 interviews in 10 days.”',
          name: 'Ahmet K.',
          role: 'Frontend Developer'
        },
        {
          initials: 'MB',
          color: 'bg-[#16a34a]',
          quote:
            '“I used the AI advisor to shape my strategy and finally understood where to focus. I had never used a tool like this before.”',
          name: 'Merve B.',
          role: 'Data Analyst'
        },
        {
          initials: 'CE',
          color: 'bg-[#f59e0b]',
          quote:
            '“I increased my profile score from 45% to 88%. After that, the suggested roles changed completely and became far more accurate.”',
          name: 'Can E.',
          role: 'DevOps Engineer'
        }
      ]
    },
    cta: {
      badge: 'Upload your CV, we will handle the rest',
      titlePrefix: 'The way you search for work',
      titleAccent: 'has changed.',
      description:
        'Upload your CV, complete your profile and discover better-fit opportunities with AI-supported matching.',
      button: 'Upload my CV and start',
      notes: ['No credit card', 'No setup', 'Ready in 2 minutes']
    }
  },
  de: {
    stats: [
      {value: '12K+', label: 'Aktive Stellen'},
      {value: '94%', label: 'Matching-Genauigkeit'},
      {value: '3×', label: 'Schnellere Bewerbungen'},
      {value: '40+', label: 'Plattform-Integrationen'}
    ],
    features: [
      {
        title: 'Alle Plattformen an einem Ort durchsuchen',
        description:
          'Bündle LinkedIn, Jobbörsen und weitere Quellen in einer Oberfläche, statt Zeit über viele Tabs zu verlieren.'
      },
      {
        title: 'Intelligentes Matching auf Profilbasis',
        description:
          'Das System versteht deinen Lebenslauf, deine Fähigkeiten und Präferenzen und priorisiert stärkere Chancen mit klarem Score.'
      },
      {
        title: 'Lücken erkennen und Profil stärken',
        description:
          'Sieh sofort, welche Signale fehlen oder schwach sind. Mit einem besseren Profil werden auch die Übereinstimmungen präziser.'
      }
    ],
    how: {
      eyebrow: 'So funktioniert es',
      title: 'Dein Hiring-Radar in 4 Schritten',
      description:
        'Erstelle dein Profil, starte die Suche, prüfe die besten Matches und bewirb dich.',
      steps: [
        {
          title: 'Lebenslauf hochladen',
          description: 'PDF oder Word. Das System extrahiert deine Signale automatisch. Es dauert etwa 2 Minuten.'
        },
        {
          title: 'Profil vervollständigen',
          description: 'Jedes zusätzliche Signal verbessert deinen Match-Score. Fehlende Felder werden klar angezeigt.'
        },
        {
          title: 'Matches prüfen',
          description: 'Rollen aus 40+ Quellen werden mit einem Fit-Score gegen dein Profil priorisiert.'
        },
        {
          title: 'Gezielt bewerben',
          description: 'Nutze deinen KI-Berater für die Strategie und bewirb dich, wenn du bereit bist.'
        }
      ]
    },
    profileEngine: {
      eyebrow: 'Profil-Motor',
      title: 'Je stärker dein Profil, desto besser deine Matches',
      description:
        'Je besser das System dich versteht, desto präziser werden die vorgeschlagenen Rollen.',
      chartTitle: 'Einfluss der Profil-Vervollständigung — Match-Qualität',
      chartRows: [
        ['Nur Lebenslauf hochgeladen', 55, '55% Ø-Fit'],
        ['Fähigkeiten ergänzt', 68, '68% Ø-Fit'],
        ['Erfahrungsdetails ergänzt', 78, '78% Ø-Fit'],
        ['Präferenzen festgelegt', 91, '91% Ø-Fit']
      ] as const,
      note:
        'Jedes fehlende Signal kann dazu führen, dass du relevante Chancen verpasst. Je klarer das System dein Profil kennt, desto präziser wird die Rangfolge.',
      points: [
        {
          title: 'Fehlende Bereiche klar erkennen',
          description: 'Du siehst, welche Profilbereiche deine Match-Qualität senken.'
        },
        {
          title: 'Echtzeit-Aktualisierung',
          description: 'Sobald du eine neue Fähigkeit ergänzt, wird das Ranking sofort aktualisiert.'
        },
        {
          title: 'Wie stark ist dein Profil?',
          description: 'Verfolge deinen Fortschritt Schritt für Schritt über den Profil-Score.'
        }
      ]
    },
    ai: {
      eyebrow: 'KI-Unterstützung',
      title: 'Nicht nur ein Job-Tool, sondern dein Karriereberater',
      description:
        'CV-Analyse, Strategieempfehlungen und Bewerbungsunterstützung — alles an einem Ort.',
      assistantName: 'CoreSift AI',
      status: 'Aktiv',
      inputPlaceholder: 'Stelle eine Frage…',
      bubbles: [
        {
          role: 'ai',
          text: 'Hallo! Ich habe deinen Lebenslauf analysiert. Du bist stark in React und TypeScript. Wenn du zusätzlich Erfahrung im Bereich Systemdesign ergänzt, kann dein Score für hochwertige Engineering-Rollen deutlich steigen.'
        },
        {
          role: 'user',
          text: 'Auf welche Positionen sollte ich mich konzentrieren?'
        },
        {
          role: 'ai',
          text: 'Dein stärkstes Fit liegt aktuell bei Senior Frontend- und Full-Stack-Rollen. Drei offene Positionen liegen bereits über 85% — sollen wir gemeinsam eine Bewerbungsstrategie definieren?'
        }
      ],
      features: [
        {
          title: 'CV-Analyse und Verbesserungsvorschläge',
          description:
            'Die KI liest deinen Lebenslauf, identifiziert Stärken und Schwachstellen und zeigt, welche Verbesserungen mehr passende Rollen erschließen.'
        },
        {
          title: 'Bewerbungsstrategie entwickeln',
          description:
            'Welche Rolle zuerst? Welche Unternehmen passen besser? Sprich mit der KI und forme den richtigen nächsten Schritt.'
        },
        {
          title: 'Unterstützung bei der Interviewvorbereitung',
          description:
            'Erhalte wahrscheinliche Fragen, Unternehmenskontext und Vorbereitungshinweise passend zur Zielrolle.'
        }
      ]
    },
    testimonials: {
      eyebrow: 'Nutzerstimmen',
      title: 'Was Jobsuchende sagen',
      items: [
        {
          initials: 'AK',
          color: 'bg-[#3b52f0]',
          quote:
            '„Ich habe meinen Lebenslauf hochgeladen, fehlende Felder ergänzt und mein Score ist sofort gestiegen. In 10 Tagen hatte ich 3 Interviews.“',
          name: 'Ahmet K.',
          role: 'Frontend Developer'
        },
        {
          initials: 'MB',
          color: 'bg-[#16a34a]',
          quote:
            '„Mit dem KI-Berater konnte ich meine Strategie klären und wusste endlich, worauf ich mich fokussieren sollte.“',
          name: 'Merve B.',
          role: 'Data Analyst'
        },
        {
          initials: 'CE',
          color: 'bg-[#f59e0b]',
          quote:
            '„Ich habe meinen Profil-Score von 45% auf 88% erhöht. Danach wurden die empfohlenen Stellen deutlich passender.“',
          name: 'Can E.',
          role: 'DevOps Engineer'
        }
      ]
    },
    cta: {
      badge: 'Lade deinen Lebenslauf hoch, wir übernehmen den Rest',
      titlePrefix: 'Die Art, Arbeit zu suchen,',
      titleAccent: 'hat sich verändert.',
      description:
        'Lade deinen Lebenslauf hoch, vervollständige dein Profil und entdecke passendere Chancen mit KI-gestütztem Matching.',
      button: 'Lebenslauf hochladen und starten',
      notes: ['Keine Kreditkarte', 'Kein Setup', 'In 2 Minuten bereit']
    }
  }
} as const;

const featureIcons = [Search, Sparkles, Target];
const profileIcons = [Search, Clock3, Target];
const aiIcons = [Search, Sparkles, Target];

export default async function LandingPage({
  params
}: {
  params: Promise<{locale: string}>;
}) {
  const {locale: rawLocale} = await params;
  const locale = resolveLocale(rawLocale);
  const t = pageCopy[locale];

  return (
    <div className="min-h-screen bg-[#07090d] text-white">
      <PublicHeader locale={locale} />
      <LandingHero locale={locale} />

      <section className="bg-[#07090d] py-10">
        <div className="container-shell">
          <div className="overflow-hidden rounded-[28px] border border-white/10 bg-[#0d1117]">
            <div className="grid divide-y divide-white/10 lg:grid-cols-4 lg:divide-x lg:divide-y-0">
              {t.stats.map((stat) => (
                <div key={stat.label} className="px-6 py-10 text-center">
                  <div className="text-4xl font-bold tracking-tight text-white">{stat.value}</div>
                  <div className="mt-2 text-sm text-white/58">{stat.label}</div>
                </div>
              ))}
            </div>

            <div className="grid divide-y divide-white/10 lg:grid-cols-3 lg:divide-x lg:divide-y-0">
              {t.features.map((feature, index) => {
                const Icon = featureIcons[index];
                return (
                  <div key={feature.title} className="px-7 py-10">
                    <div className="mb-6 flex size-12 items-center justify-center rounded-2xl bg-[#eef0ff] text-[#3b52f0]">
                      <Icon className="size-5" />
                    </div>
                    <h2 className="max-w-xs text-[28px] font-semibold leading-tight tracking-tight text-white">
                      {feature.title}
                    </h2>
                    <p className="mt-4 max-w-sm text-base leading-8 text-white/64">
                      {feature.description}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      <section id="how-it-works" className="border-t border-white/10 bg-[#0a0d12] py-20">
        <div className="container-shell">
          <div className="max-w-3xl">
            <div className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-[#4b61ff]">
              {t.how.eyebrow}
            </div>
            <h2 className="text-4xl font-bold tracking-tight text-white md:text-5xl">
              {t.how.title}
            </h2>
            <p className="mt-4 text-lg leading-8 text-white/68">{t.how.description}</p>
          </div>

          <div className="relative mt-14 grid gap-10 lg:grid-cols-4 lg:gap-8">
            <div className="absolute left-[12.5%] right-[12.5%] top-7 hidden border-t border-white/10 lg:block" />
            {t.how.steps.map((step, index) => (
              <div key={step.title} className="relative z-10 text-center">
                <div className="mx-auto mb-6 flex size-14 items-center justify-center rounded-full border border-white/15 bg-[#0d1117] text-xl font-bold text-[#4b61ff]">
                  {index + 1}
                </div>
                <div className="text-xl font-semibold text-white">{step.title}</div>
                <p className="mt-3 text-base leading-7 text-white/62">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-white/10 bg-[#07090d] py-20">
        <div className="container-shell grid gap-12 lg:grid-cols-[minmax(320px,0.88fr)_minmax(0,1fr)] lg:items-center">
          <div>
            <div className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-[#4b61ff]">
              {t.profileEngine.eyebrow}
            </div>
            <h2 className="max-w-2xl text-4xl font-bold tracking-tight text-white md:text-5xl">
              {t.profileEngine.title}
            </h2>
            <p className="mt-5 max-w-2xl text-lg leading-8 text-white/68">
              {t.profileEngine.description}
            </p>

            <div className="mt-8 rounded-[28px] border border-white/10 bg-[#0d1117] p-6">
              <div className="text-base font-semibold text-white">
                {t.profileEngine.chartTitle}
              </div>

              <div className="mt-6 space-y-5">
                {t.profileEngine.chartRows.map(([label, value, metric]) => (
                  <div key={label}>
                    <div className="mb-2 flex items-center justify-between gap-4 text-sm">
                      <span className="text-white/75">{label}</span>
                      <span className="font-semibold text-[#4b61ff]">{metric}</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-white/8">
                      <div
                        className="h-1.5 rounded-full bg-[#4b61ff]"
                        style={{width: `${value}%`}}
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 rounded-2xl bg-[#eef0ff] p-4 text-sm leading-7 text-[#2437b8]">
                {t.profileEngine.note}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            {t.profileEngine.points.map((point, index) => {
              const Icon = profileIcons[index];
              return (
                <div key={point.title} className="flex items-start gap-4">
                  <div className="flex size-12 shrink-0 items-center justify-center rounded-2xl bg-[#eef0ff] text-[#3b52f0]">
                    <Icon className="size-5" />
                  </div>
                  <div>
                    <div className="text-xl font-semibold text-white">{point.title}</div>
                    <p className="mt-2 max-w-xl text-base leading-8 text-white/64">
                      {point.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section className="border-t border-white/10 bg-[#0a0d12] py-20">
        <div className="container-shell">
          <div className="max-w-3xl">
            <div className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-[#4b61ff]">
              {t.ai.eyebrow}
            </div>
            <h2 className="text-4xl font-bold tracking-tight text-white md:text-5xl">
              {t.ai.title}
            </h2>
            <p className="mt-4 text-lg leading-8 text-white/68">{t.ai.description}</p>
          </div>

          <div className="mt-12 grid gap-10 lg:grid-cols-[minmax(320px,0.92fr)_minmax(0,1fr)] lg:items-start">
            <div className="overflow-hidden rounded-[28px] border border-white/10 bg-[#11161d]">
              <div className="flex items-center gap-3 border-b border-white/8 px-5 py-4">
                <div className="flex size-11 items-center justify-center rounded-2xl bg-[#3b52f0] text-white">
                  <Sparkles className="size-5" />
                </div>
                <div>
                  <div className="font-semibold text-white">{t.ai.assistantName}</div>
                  <div className="text-sm text-emerald-300">{t.ai.status}</div>
                </div>
              </div>

              <div className="space-y-4 p-5">
                {t.ai.bubbles.map((bubble, index) => (
                  <div
                    key={`${bubble.role}-${index}`}
                    className={`max-w-[88%] rounded-2xl border px-4 py-3 text-base leading-8 ${
                      bubble.role === 'user'
                        ? 'ml-auto border-[#3b52f0] bg-[#3b52f0] text-white'
                        : 'border-white/10 bg-white/[0.03] text-white/80'
                    }`}
                  >
                    {bubble.text}
                  </div>
                ))}
              </div>

              <div className="border-t border-white/8 px-5 py-4">
                <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-[#0d1117] px-4 py-3 text-sm text-white/45">
                  <span>{t.ai.inputPlaceholder}</span>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              {t.ai.features.map((item, index) => {
                const Icon = aiIcons[index];
                return (
                  <div key={item.title} className="flex items-start gap-4">
                    <div className="flex size-12 shrink-0 items-center justify-center rounded-2xl bg-[#eef0ff] text-[#3b52f0]">
                      <Icon className="size-5" />
                    </div>
                    <div>
                      <div className="text-xl font-semibold text-white">{item.title}</div>
                      <p className="mt-2 max-w-xl text-base leading-8 text-white/64">
                        {item.description}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      <section className="border-t border-white/10 bg-[#07090d] py-20">
        <div className="container-shell">
          <div className="text-center">
            <div className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-[#4b61ff]">
              {t.testimonials.eyebrow}
            </div>
            <h2 className="text-4xl font-bold tracking-tight text-white md:text-5xl">
              {t.testimonials.title}
            </h2>
          </div>

          <div className="mt-12 grid gap-6 lg:grid-cols-3">
            {t.testimonials.items.map((item) => (
              <div
                key={item.name}
                className="rounded-[28px] border border-white/10 bg-[#11161d] p-7 shadow-[0_20px_60px_rgba(0,0,0,0.26)]"
              >
                <div className="mb-5 flex text-[#f59e0b]">
                  {Array.from({length: 5}).map((_, index) => (
                    <Star key={index} className="size-4 fill-current" />
                  ))}
                </div>

                <p className="min-h-28 text-lg leading-8 text-white/72">{item.quote}</p>

                <div className="mt-6 flex items-center gap-4">
                  <div
                    className={`flex size-12 items-center justify-center rounded-full text-sm font-semibold text-white ${item.color}`}
                  >
                    {item.initials}
                  </div>
                  <div>
                    <div className="font-semibold text-white">{item.name}</div>
                    <div className="text-sm text-white/55">{item.role}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-white/10 bg-[#0a0d12] py-24">
        <div className="container-shell">
          <div className="mx-auto max-w-4xl rounded-[36px] border border-white/10 bg-[#11161d] px-8 py-16 text-center shadow-[0_28px_90px_rgba(0,0,0,0.34)] md:px-14">
            <div className="mx-auto inline-flex items-center rounded-full bg-[#eef0ff] px-4 py-2 text-sm font-semibold text-[#3b52f0]">
              {t.cta.badge}
            </div>

            <h2 className="mt-8 text-4xl font-bold leading-tight tracking-tight text-white md:text-6xl">
              {t.cta.titlePrefix}{' '}
              <span className="text-[#4b61ff]">{t.cta.titleAccent}</span>
            </h2>

            <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-white/68">
              {t.cta.description}
            </p>

            <div className="mt-10 flex justify-center">
              <a
                href={`/${locale}/signup`}
                className="inline-flex items-center rounded-2xl border border-white/12 bg-[#3b52f0] px-7 py-4 text-base font-semibold text-white transition hover:bg-[#3147db]"
              >
                {t.cta.button}
                <ArrowRight className="ml-2 size-4" />
              </a>
            </div>

            <div className="mt-5 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-white/48">
              {t.cta.notes.map((note) => (
                <span key={note}>{note}</span>
              ))}
            </div>
          </div>
        </div>
      </section>

      <PublicFooter locale={locale} />
    </div>
  );
}