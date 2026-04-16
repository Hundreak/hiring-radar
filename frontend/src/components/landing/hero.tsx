import Link from 'next/link';
import {ArrowRight, CheckCircle2, Upload} from 'lucide-react';

import {Badge} from '@/components/ui/badge';
import {Button} from '@/components/ui/button';

const content = {
  tr: {
    badge: 'Yapay zeka destekli iş arama',
    titlePrefix: 'Sana uygun ilanları',
    titleAccent: 'otomatik bul.',
    description:
      'CoreSift, tüm iş platformlarını tarar, profilinle karşılaştırır ve en yüksek uyumlu fırsatları sana önce gösterir. Başvurularını daha net, daha hızlı ve daha stratejik yönet.',
    primaryCta: 'Ücretsiz başla',
    secondaryCta: 'Nasıl çalışır?',
    trustCopy: '2.400+ kişi bu hafta iş arama sürecini hızlandırdı',
    uploadTitle: "CV'ni buraya yükle",
    uploadDescription:
      'PDF veya Word — sistem otomatik okur, profilini yapılandırır ve daha güçlü eşleşmeler üretir.',
    uploadButton: 'CV Yükle',
    parsedTitle: 'Profilinden çekilen veriler',
    parsedChips: ['React', 'TypeScript', '5 yıl deneyim', 'İstanbul', 'Uzaktan', 'İngilizce'],
    scoreTitle: 'Profil tamamlanma skoru',
    scoreRows: {
      identity: 'Temel bilgiler',
      skills: 'Beceriler',
      experience: 'Deneyim detayları',
      preferences: 'Beklentiler & tercihler'
    },
    scoreStatus: {
      done: 'Tamamlandı',
      missing: 'Eksik'
    },
    jobsTitle: 'Senin için önerilen ilanlar',
    jobsLive: 'Canlı',
    panelNote: 'Profilini geliştirdikçe sistem daha isabetli eşleşmeler üretir.'
  },
  en: {
    badge: 'AI-powered job discovery',
    titlePrefix: 'Find the right opportunities',
    titleAccent: 'automatically.',
    description:
      'CoreSift scans the market, compares roles against your profile and brings the strongest-fit opportunities to the front.',
    primaryCta: 'Get started free',
    secondaryCta: 'How it works',
    trustCopy: '2,400+ people accelerated their search this week',
    uploadTitle: 'Upload your CV',
    uploadDescription:
      'PDF or Word — the system reads it, structures your profile and improves match quality.',
    uploadButton: 'Upload CV',
    parsedTitle: 'Signals extracted from your profile',
    parsedChips: ['React', 'TypeScript', '5 years experience', 'Istanbul', 'Remote', 'English'],
    scoreTitle: 'Profile completion score',
    scoreRows: {
      identity: 'Core profile',
      skills: 'Skills',
      experience: 'Experience detail',
      preferences: 'Preferences'
    },
    scoreStatus: {
      done: 'Complete',
      missing: 'Missing'
    },
    jobsTitle: 'Roles suggested for you',
    jobsLive: 'Live',
    panelNote: 'As your profile improves, the system produces sharper matches.'
  },
  de: {
    badge: 'KI-gestützte Jobsuche',
    titlePrefix: 'Finde passende Stellen',
    titleAccent: 'automatisch.',
    description:
      'CoreSift scannt den Markt, vergleicht Rollen mit deinem Profil und bringt die stärksten Chancen nach vorne.',
    primaryCta: 'Kostenlos starten',
    secondaryCta: 'So funktioniert es',
    trustCopy: '2.400+ Menschen haben diese Woche ihre Suche beschleunigt',
    uploadTitle: 'Lade deinen Lebenslauf hoch',
    uploadDescription:
      'PDF oder Word — das System liest ihn, strukturiert dein Profil und verbessert die Match-Qualität.',
    uploadButton: 'Lebenslauf hochladen',
    parsedTitle: 'Aus deinem Profil erkannte Signale',
    parsedChips: ['React', 'TypeScript', '5 Jahre Erfahrung', 'Istanbul', 'Remote', 'Englisch'],
    scoreTitle: 'Profil-Vollständigkeit',
    scoreRows: {
      identity: 'Grunddaten',
      skills: 'Fähigkeiten',
      experience: 'Erfahrungsdetails',
      preferences: 'Präferenzen'
    },
    scoreStatus: {
      done: 'Fertig',
      missing: 'Fehlt'
    },
    jobsTitle: 'Empfohlene Stellen',
    jobsLive: 'Live',
    panelNote: 'Je stärker dein Profil, desto präziser werden die Übereinstimmungen.'
  }
} as const;

const featuredJobs = [
  {
    title: 'Senior Frontend Engineer',
    company: 'Corelight · İstanbul',
    match: 92,
    tags: ['React', 'TypeScript', 'Uzaktan']
  },
  {
    title: 'Platform Engineer',
    company: 'Trendyol · Ankara',
    match: 86,
    tags: ['Kubernetes', 'AWS']
  },
  {
    title: 'Security Engineer',
    company: 'ScaleOps · Remote',
    match: 71,
    tags: ['Python', 'DevSecOps']
  }
];

const trustPeople = [
  {label: 'AK', color: 'bg-[#3b52f0]'},
  {label: 'MB', color: 'bg-[#7b6ff5]'},
  {label: 'CE', color: 'bg-[#16a34a]'},
  {label: 'YD', color: 'bg-[#f59e0b]'}
];

function getCopy(locale: string) {
  if (locale.startsWith('tr')) return content.tr;
  if (locale.startsWith('de')) return content.de;
  return content.en;
}

export function LandingHero({locale}: {locale: string}) {
  const t = getCopy(locale);

  return (
    <section className="border-b border-white/10 bg-[radial-gradient(circle_at_top_right,_rgba(59,82,240,0.18),_transparent_28%),linear-gradient(180deg,#06080b_0%,#0a0d12_100%)]">
      <div className="container-shell grid gap-10 pb-16 pt-14 lg:grid-cols-[minmax(0,1.08fr)_minmax(360px,480px)] lg:gap-14 lg:pb-20 lg:pt-20">
        <div className="space-y-8">
          <Badge
            tone="accent"
            className="rounded-full border border-[#5d70ff]/20 bg-[#eef0ff] px-4 py-2 text-[13px] font-semibold text-[#3b52f0]"
          >
            <span className="mr-2 inline-block size-2 rounded-full bg-[#3b52f0]" />
            {t.badge}
          </Badge>

          <div className="space-y-6">
            <h1 className="max-w-3xl text-5xl font-bold leading-[0.96] tracking-[-0.05em] text-white md:text-6xl lg:text-7xl">
              {t.titlePrefix}{' '}
              <span className="text-[#4b61ff]">{t.titleAccent}</span>
            </h1>

            <p className="max-w-xl text-lg leading-8 text-white/70">{t.description}</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Link href={`/${locale}/signup`}>
              <Button className="h-12 rounded-2xl bg-[#3b52f0] px-6 text-white hover:bg-[#3147db]">
                {t.primaryCta}
                <ArrowRight className="ml-2 size-4" />
              </Button>
            </Link>

            <a href="#how-it-works">
              <Button
                variant="secondary"
                className="h-12 rounded-2xl border border-white/12 bg-transparent px-6 text-white hover:bg-white/6"
              >
                {t.secondaryCta}
              </Button>
            </a>
          </div>

          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center">
              {trustPeople.map((person, index) => (
                <div
                  key={person.label}
                  className={`${
                    person.color
                  } flex size-9 items-center justify-center rounded-full border-2 border-[#0a0d12] text-[11px] font-semibold text-white ${
                    index === 0 ? 'ml-0' : '-ml-2'
                  }`}
                >
                  {person.label}
                </div>
              ))}
            </div>

            <p className="text-sm text-white/65">{t.trustCopy}</p>
          </div>

          <div className="rounded-[28px] border border-white/10 bg-white/[0.03] shadow-[0_24px_80px_rgba(0,0,0,0.26)]">
            <div className="flex items-center justify-between border-b border-white/8 px-5 py-4">
              <div className="text-base font-semibold text-white">{t.jobsTitle}</div>
              <div className="inline-flex items-center gap-2 rounded-full bg-emerald-500/10 px-3 py-1 text-[11px] font-semibold text-emerald-300">
                <span className="size-2 rounded-full bg-emerald-400" />
                {t.jobsLive}
              </div>
            </div>

            <div className="space-y-4 p-5">
              {featuredJobs.map((job) => (
                <div key={job.title} className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                  <div className="mb-3 flex items-start justify-between gap-3">
                    <div>
                      <div className="text-base font-semibold text-white">{job.title}</div>
                      <div className="text-sm text-white/55">{job.company}</div>
                    </div>
                    <div className="text-right text-lg font-bold text-[#4b61ff]">{job.match}%</div>
                  </div>

                  <div className="mb-3 h-1.5 rounded-full bg-white/8">
                    <div
                      className="h-1.5 rounded-full bg-[#6f80ff]"
                      style={{width: `${job.match}%`}}
                    />
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {job.tags.map((tag) => (
                      <span
                        key={tag}
                        className="rounded-md bg-[#eef0ff] px-2.5 py-1 text-[11px] font-medium text-[#3b52f0]"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="border-t border-white/8 px-5 py-4 text-sm text-white/58">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="size-4 text-emerald-400" />
                {t.panelNote}
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-4 rounded-[32px] border border-white/10 bg-white/[0.03] p-5 shadow-[0_28px_100px_rgba(0,0,0,0.35)]">
          <div className="rounded-[24px] border border-dashed border-white/12 bg-[#0f1319] p-5">
            <div className="mb-4 flex size-12 items-center justify-center rounded-2xl bg-[#eef0ff] text-[#3b52f0]">
              <Upload className="size-5" />
            </div>

            <div className="mb-2 text-sm font-semibold text-white">{t.uploadTitle}</div>
            <p className="mb-5 text-sm leading-6 text-white/60">{t.uploadDescription}</p>

            <button className="inline-flex items-center rounded-xl bg-[#3b52f0] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[#3348da]">
              {t.uploadButton}
            </button>
          </div>

          <div className="rounded-[24px] border border-white/8 bg-[#0f1319] p-4">
            <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-white/45">
              {t.parsedTitle}
            </div>
            <div className="flex flex-wrap gap-2">
              {t.parsedChips.map((chip) => (
                <span
                  key={chip}
                  className="rounded-lg border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-white/85"
                >
                  {chip}
                </span>
              ))}
            </div>
          </div>

          <div className="rounded-[24px] border border-white/8 bg-[#0f1319] p-4">
            <div className="mb-4 flex items-center justify-between gap-4">
              <div className="text-sm font-semibold text-white">{t.scoreTitle}</div>
              <div className="text-2xl font-bold tracking-tight text-[#4b61ff]">62%</div>
            </div>

            <div className="mb-4 h-2 rounded-full bg-white/8">
              <div className="h-2 w-[62%] rounded-full bg-[#4b61ff]" />
            </div>

            <div className="space-y-2">
              {[
                {label: t.scoreRows.identity, status: t.scoreStatus.done, tone: 'bg-emerald-500/12 text-emerald-300'},
                {label: t.scoreRows.skills, status: t.scoreStatus.done, tone: 'bg-emerald-500/12 text-emerald-300'},
                {label: t.scoreRows.experience, status: t.scoreStatus.missing, tone: 'bg-amber-500/12 text-amber-300'},
                {label: t.scoreRows.preferences, status: t.scoreStatus.missing, tone: 'bg-amber-500/12 text-amber-300'}
              ].map((row) => (
                <div
                  key={row.label}
                  className="flex items-center justify-between border-b border-white/6 py-2 last:border-b-0"
                >
                  <span className="text-sm text-white/68">{row.label}</span>
                  <span className={`rounded-md px-2.5 py-1 text-[11px] font-semibold ${row.tone}`}>
                    {row.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}