'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import {
  ArrowRight,
  CheckCircle2,
  Sparkles,
  Upload,
  Zap,
  Target,
  TrendingUp,
  Globe
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

const content = {
  tr: {
    badge: 'Yapay zeka destekli iş arama',
    titleLine1: 'Sana uygun',
    titleAccent: 'en iyi',
    titleLine2: 'ilanları bul.',
    description:
      'NoyTera, CV’ni analiz eder, 40+ platformdan ilanları eşleştirir ve başvuru stratejin için AI danışmanlığı sunar.',
    primaryCta: 'Ücretsiz başla',
    secondaryCta: 'Nasıl çalışır?',
    trustCopy: '2.400+ kişi bu hafta iş arama sürecini hızlandırdı',
    uploadTitle: "CV'ni yükle",
    uploadDescription: 'PDF veya Word — sistem otomatik okur',
    uploadButton: 'CV Yükle',
    parsedTitle: 'Çıkarılan sinyaller',
    parsedChips: ['React', 'TypeScript', '5 yıl', 'İstanbul', 'Uzaktan', 'İngilizce'],
    scoreTitle: 'Profil tamamlanma',
    scoreValue: '62%',
    scoreRows: [
      { label: 'Temel bilgiler', status: 'done' },
      { label: 'Beceriler', status: 'done' },
      { label: 'Deneyim', status: 'missing' },
      { label: 'Tercihler', status: 'missing' }
    ],
    jobsTitle: 'Sana özel ilanlar',
    jobsLive: 'Canlı',
    panelNote: 'Profilini geliştirdikçe daha isabetli eşleşmeler üretir.'
  },
  en: {
    badge: 'AI-powered job discovery',
    titleLine1: 'Find the',
    titleAccent: 'best-fit',
    titleLine2: 'opportunities.',
    description:
      'NoyTera analyzes your CV, matches jobs from 40+ platforms, and provides AI advisory for your application strategy.',
    primaryCta: 'Get started free',
    secondaryCta: 'How it works',
    trustCopy: '2,400+ people accelerated their search this week',
    uploadTitle: 'Upload your CV',
    uploadDescription: 'PDF or Word — system reads automatically',
    uploadButton: 'Upload CV',
    parsedTitle: 'Extracted signals',
    parsedChips: ['React', 'TypeScript', '5 years', 'Istanbul', 'Remote', 'English'],
    scoreTitle: 'Profile completion',
    scoreValue: '62%',
    scoreRows: [
      { label: 'Core profile', status: 'done' },
      { label: 'Skills', status: 'done' },
      { label: 'Experience', status: 'missing' },
      { label: 'Preferences', status: 'missing' }
    ],
    jobsTitle: 'Roles for you',
    jobsLive: 'Live',
    panelNote: 'As your profile improves, matches get sharper.'
  },
  de: {
    badge: 'KI-gestützte Jobsuche',
    titleLine1: 'Finde die',
    titleAccent: 'besten',
    titleLine2: 'passenden Stellen.',
    description:
      'NoyTera analysiert deinen Lebenslauf, matched Stellen aus 40+ Quellen und bietet KI-Beratung für deine Bewerbungsstrategie.',
    primaryCta: 'Kostenlos starten',
    secondaryCta: 'So funktioniert es',
    trustCopy: '2.400+ Menschen haben diese Woche ihre Suche beschleunigt',
    uploadTitle: 'Lebenslauf hochladen',
    uploadDescription: 'PDF oder Word — das System liest automatisch',
    uploadButton: 'Hochladen',
    parsedTitle: 'Erkannte Signale',
    parsedChips: ['React', 'TypeScript', '5 Jahre', 'Istanbul', 'Remote', 'Englisch'],
    scoreTitle: 'Profil-Vollständigkeit',
    scoreValue: '62%',
    scoreRows: [
      { label: 'Grunddaten', status: 'done' },
      { label: 'Fähigkeiten', status: 'done' },
      { label: 'Erfahrung', status: 'missing' },
      { label: 'Präferenzen', status: 'missing' }
    ],
    jobsTitle: 'Stellen für dich',
    jobsLive: 'Live',
    panelNote: 'Je stärker dein Profil, desto präziser die Matches.'
  }
};

const featuredJobs = [
  { title: 'Senior Frontend Engineer', company: 'Corelight · İstanbul', match: 92, tags: ['React', 'TypeScript', 'Uzaktan'] },
  { title: 'Platform Engineer', company: 'Trendyol · Ankara', match: 86, tags: ['Kubernetes', 'AWS'] },
  { title: 'Security Engineer', company: 'ScaleOps · Remote', match: 71, tags: ['Python', 'DevSecOps'] }
];

const trustPeople = [
  { label: 'AK', color: 'bg-primary text-primary-foreground' },
  { label: 'MB', color: 'bg-accent text-white' },
  { label: 'CE', color: 'bg-success text-white' },
  { label: 'YD', color: 'bg-warning text-white' }
];

function getCopy(locale: string) {
  if (locale.startsWith('tr')) return content.tr;
  if (locale.startsWith('de')) return content.de;
  return content.en;
}

function AnimatedCounter({ value, suffix = '' }: { value: string; suffix?: string }) {
  const [display, setDisplay] = useState('0');
  const ref = useRef<HTMLSpanElement>(null);
  const hasAnimated = useRef(false);

  useEffect(() => {
    const el = ref.current;
    if (!el || hasAnimated.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !hasAnimated.current) {
            hasAnimated.current = true;
            const numeric = parseInt(value.replace(/\D/g, ''), 10);
            if (isNaN(numeric)) {
              setDisplay(value);
              return;
            }
            const duration = 1500;
            const start = performance.now();
            const animate = (now: number) => {
              const progress = Math.min((now - start) / duration, 1);
              const eased = 1 - Math.pow(1 - progress, 3);
              setDisplay(String(Math.floor(eased * numeric)));
              if (progress < 1) requestAnimationFrame(animate);
            };
            requestAnimationFrame(animate);
          }
        });
      },
      { threshold: 0.5 }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [value]);

  return (
    <span ref={ref}>
      {display}
      {suffix}
    </span>
  );
}

export function LandingHero({ locale }: { locale: string }) {
  const t = getCopy(locale);
  const [isVisible, setIsVisible] = useState(false);
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setIsVisible(true);
        });
      },
      { threshold: 0.1 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <section
      ref={sectionRef}
      className="relative overflow-hidden"
      style={{
        background: 'linear-gradient(180deg, var(--hero-gradient-start) 0%, var(--hero-gradient-end) 100%)'
      }}
    >
      {/* Animated grid background */}
      <div className="pointer-events-none absolute inset-0 grid-bg opacity-40" />

      {/* Floating orbs */}
      <div className="pointer-events-none absolute -left-20 top-20 size-72 rounded-full bg-primary/8 blur-3xl animate-float" />
      <div className="pointer-events-none absolute right-10 top-40 size-56 rounded-full bg-accent/8 blur-3xl animate-float-delay-2" />
      <div className="pointer-events-none absolute bottom-20 left-1/3 size-64 rounded-full bg-primary/6 blur-3xl animate-float-delay-1" />

      <div className="container-shell relative grid gap-10 pb-20 pt-14 lg:grid-cols-[minmax(0,1.08fr)_minmax(360px,480px)] lg:gap-14 lg:pb-24 lg:pt-20">
        {/* Left column */}
        <div className="space-y-8">
          <div
            className={`transition-all duration-700 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-6 opacity-0'}`}
          >
            <Badge
              tone="accent"
              className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-secondary px-4 py-2 text-[13px] font-semibold text-secondary-foreground"
            >
              <span className="relative inline-flex size-2">
                <span className="absolute inline-flex size-full animate-ping rounded-full bg-primary opacity-75" />
                <span className="relative inline-flex size-2 rounded-full bg-primary" />
              </span>
              {t.badge}
            </Badge>
          </div>

          <div
            className={`space-y-6 transition-all duration-700 delay-100 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-6 opacity-0'}`}
          >
            <h1 className="max-w-3xl text-5xl font-bold leading-[0.98] tracking-[-0.04em] md:text-6xl lg:text-7xl">
              {t.titleLine1}{' '}
              <span className="gradient-text">{t.titleAccent}</span>
              <br />
              {t.titleLine2}
            </h1>
            <p className="max-w-xl text-lg leading-8 text-muted-foreground">
              {t.description}
            </p>
          </div>

          <div
            className={`flex flex-wrap items-center gap-3 transition-all duration-700 delay-200 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-6 opacity-0'}`}
          >
            <Link href={`/${locale}/signup`}>
              <Button className="group h-12 rounded-2xl bg-primary px-6 text-primary-foreground shadow-lg shadow-primary/20 transition hover:shadow-xl hover:shadow-primary/30">
                <Sparkles className="mr-2 size-4 transition group-hover:scale-110" />
                {t.primaryCta}
                <ArrowRight className="ml-2 size-4 transition group-hover:translate-x-1" />
              </Button>
            </Link>
            <a href="#how-it-works">
              <Button
                variant="secondary"
                className="h-12 rounded-2xl border border-border bg-surface-elevated px-6 text-foreground transition hover:bg-surface-muted"
              >
                {t.secondaryCta}
              </Button>
            </a>
          </div>

          <div
            className={`flex flex-wrap items-center gap-4 transition-all duration-700 delay-300 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-6 opacity-0'}`}
          >
            <div className="flex items-center">
              {trustPeople.map((person, index) => (
                <div
                  key={person.label}
                  className={`${person.color} flex size-9 items-center justify-center rounded-full border-2 border-background text-[11px] font-semibold ${index === 0 ? 'ml-0' : '-ml-2'} transition hover:scale-110 hover:z-10`}
                >
                  {person.label}
                </div>
              ))}
            </div>
            <p className="text-sm text-muted-foreground">{t.trustCopy}</p>
          </div>

          {/* Jobs preview panel */}
          <div
            className={`glass surface-card overflow-hidden transition-all duration-700 delay-500 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-6 opacity-0'}`}
          >
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <div className="flex items-center gap-2 text-base font-semibold">
                <Zap className="size-4 text-primary" />
                {t.jobsTitle}
              </div>
              <div className="inline-flex items-center gap-2 rounded-full bg-success/10 px-3 py-1 text-[11px] font-semibold text-success">
                <span className="size-2 rounded-full bg-success animate-pulse-dot" />
                {t.jobsLive}
              </div>
            </div>
            <div className="space-y-3 p-5">
              {featuredJobs.map((job, i) => (
                <div
                  key={job.title}
                  className="group rounded-2xl border border-border bg-surface-muted/50 p-4 transition hover:border-primary/30 hover:bg-surface-muted"
                  style={{ animationDelay: `${600 + i * 100}ms` }}
                >
                  <div className="mb-3 flex items-start justify-between gap-3">
                    <div>
                      <div className="text-base font-semibold">{job.title}</div>
                      <div className="text-sm text-muted-foreground">{job.company}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-primary">{job.match}%</div>
                    </div>
                  </div>
                  <div className="mb-3 h-1.5 rounded-full bg-surface-strong">
                    <div
                      className="h-1.5 rounded-full bg-primary transition-all duration-1000"
                      style={{ width: isVisible ? `${job.match}%` : '0%' }}
                    />
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {job.tags.map((tag) => (
                      <span key={tag} className="chip">{tag}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div className="border-t border-border px-5 py-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="size-4 text-success" />
                {t.panelNote}
              </div>
            </div>
          </div>
        </div>

        {/* Right column — CV upload demo */}
        <div
          className={`space-y-4 transition-all duration-700 delay-300 ${isVisible ? 'translate-x-0 opacity-100' : 'translate-x-6 opacity-0'}`}
        >
          <div className="glass surface-card p-5">
            <div className="mb-4 flex size-12 items-center justify-center rounded-2xl bg-secondary text-secondary-foreground">
              <Upload className="size-5" />
            </div>
            <div className="mb-2 text-sm font-semibold">{t.uploadTitle}</div>
            <p className="mb-5 text-sm leading-6 text-muted-foreground">{t.uploadDescription}</p>
            <button className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground shadow-md shadow-primary/20 transition hover:shadow-lg hover:shadow-primary/30">
              <Upload className="size-4" />
              {t.uploadButton}
            </button>
          </div>

          <div className="surface-card p-4">
            <div className="mb-3 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              <Target className="size-3" />
              {t.parsedTitle}
            </div>
            <div className="flex flex-wrap gap-2">
              {t.parsedChips.map((chip) => (
                <span key={chip} className="chip">{chip}</span>
              ))}
            </div>
          </div>

          <div className="surface-card p-4">
            <div className="mb-4 flex items-center justify-between gap-4">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <TrendingUp className="size-4 text-primary" />
                {t.scoreTitle}
              </div>
              <div className="text-2xl font-bold tracking-tight text-primary">{t.scoreValue}</div>
            </div>
            <div className="mb-4 h-2 rounded-full bg-surface-strong">
              <div
                className="h-2 rounded-full bg-primary transition-all duration-1000 delay-500"
                style={{ width: isVisible ? '62%' : '0%' }}
              />
            </div>
            <div className="space-y-2">
              {t.scoreRows.map((row) => (
                <div
                  key={row.label}
                  className="flex items-center justify-between border-b border-border py-2 last:border-b-0"
                >
                  <span className="text-sm text-muted-foreground">{row.label}</span>
                  <span
                    className={`rounded-md px-2.5 py-1 text-[11px] font-semibold ${
                      row.status === 'done'
                        ? 'bg-success/10 text-success'
                        : 'bg-warning/10 text-warning'
                    }`}
                  >
                    {row.status === 'done' ? (
                      <span className="flex items-center gap-1">
                        <CheckCircle2 className="size-3" /> Tamamlandı
                      </span>
                    ) : (
                      'Eksik'
                    )}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Mini map / globe visual */}
          <div className="surface-card flex items-center justify-center p-6">
            <div className="relative flex size-24 items-center justify-center rounded-full border border-border bg-surface-muted">
              <Globe className="size-10 text-primary/60 animate-subtle-rotate" />
              <div className="absolute inset-0 rounded-full border border-primary/20 animate-radar-pulse" />
            </div>
            <div className="ml-4 space-y-1">
              <div className="text-sm font-semibold">40+ kaynak</div>
              <div className="text-xs text-muted-foreground">Tek noktada taranır</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
