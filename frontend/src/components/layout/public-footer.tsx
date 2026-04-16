import Link from 'next/link';

import {BrandLogo} from '@/components/brand/brand-logo';
import type {SupportedLocale} from '@/types/user';

type PublicFooterProps = {
  locale: string;
};

const copy = {
  tr: {
    description:
      'CoreSift, adayları daha güçlü profil sinyalleriyle daha doğru fırsatlarla buluşturmaya yardımcı olan modern bir kariyer platformudur.',
    company: 'Kurumsal',
    policies: 'Politikalar',
    support: 'Destek',
    about: 'Hakkımızda',
    principles: 'Çalışma İlkelerimiz',
    faq: 'Sıkça Sorulan Sorular',
    contact: 'İletişim',
    privacy: 'KVKK & Gizlilik',
    terms: 'Kullanım Şartları',
    cookies: 'Çerez Politikası',
    supportTitle: 'Destek e-posta adresi',
    supportBody: 'Hesap, ürün, veri talepleri ve kurumsal iletişim için resmî destek kanalımız.',
    rights: 'Tüm hakları saklıdır.',
    legalLine1: 'Kurumsal güvenlik yaklaşımı',
    legalLine2: 'Gizlilik odaklı ürün deneyimi',
    supportLine: 'Resmî destek kanalı:'
  },
  en: {
    description:
      'CoreSift is a modern career platform that helps candidates discover more relevant opportunities through stronger profile signals.',
    company: 'Company',
    policies: 'Policies',
    support: 'Support',
    about: 'About',
    principles: 'Principles',
    faq: 'FAQ',
    contact: 'Contact',
    privacy: 'Privacy',
    terms: 'Terms of use',
    cookies: 'Cookie policy',
    supportTitle: 'Support email address',
    supportBody: 'Our official support channel for account, product, privacy and business requests.',
    rights: 'All rights reserved.',
    legalLine1: 'Enterprise-minded security posture',
    legalLine2: 'Privacy-first product experience',
    supportLine: 'Official support channel:'
  },
  de: {
    description:
      'CoreSift ist eine moderne Karriereplattform, die Kandidaten mit stärkeren Profilsignalen zu passenderen Chancen führt.',
    company: 'Unternehmen',
    policies: 'Richtlinien',
    support: 'Support',
    about: 'Über uns',
    principles: 'Grundsätze',
    faq: 'FAQ',
    contact: 'Kontakt',
    privacy: 'Datenschutz',
    terms: 'Nutzungsbedingungen',
    cookies: 'Cookie-Richtlinie',
    supportTitle: 'Support-E-Mail-Adresse',
    supportBody: 'Unser offizieller Support-Kanal für Konto-, Produkt-, Datenschutz- und Geschäftsanfragen.',
    rights: 'Alle Rechte vorbehalten.',
    legalLine1: 'Unternehmensgerechter Sicherheitsansatz',
    legalLine2: 'Datenschutzorientiertes Produkterlebnis',
    supportLine: 'Offizieller Support-Kanal:'
  }
} as const;

function resolveLocale(locale: string): SupportedLocale {
  if (locale === 'tr' || locale === 'en' || locale === 'de') return locale;
  return 'tr';
}

export function PublicFooter({locale}: PublicFooterProps) {
  const safeLocale = resolveLocale(locale);
  const t = copy[safeLocale];

  return (
    <footer className="border-t border-white/8 bg-[#07090d]">
      <div className="container-shell py-14">
        <div className="grid gap-10 lg:grid-cols-[1.15fr_0.8fr_0.8fr_1fr]">
          <div>
            <BrandLogo locale={safeLocale} size="lg" showSubtitle={false} />
            <p className="mt-6 max-w-sm text-lg leading-9 text-white/62">{t.description}</p>
          </div>

          <div>
            <div className="text-sm font-semibold uppercase tracking-[0.18em] text-white/35">
              {t.company}
            </div>
            <div className="mt-6 space-y-4 text-lg text-white/82">
              <Link href={`/${safeLocale}/about`} className="block transition hover:text-[#8fa0ff]">
                {t.about}
              </Link>
              <Link href={`/${safeLocale}/principles`} className="block transition hover:text-[#8fa0ff]">
                {t.principles}
              </Link>
              <Link href={`/${safeLocale}/faq`} className="block transition hover:text-[#8fa0ff]">
                {t.faq}
              </Link>
              <Link href={`/${safeLocale}/contact`} className="block transition hover:text-[#8fa0ff]">
                {t.contact}
              </Link>
            </div>
          </div>

          <div>
            <div className="text-sm font-semibold uppercase tracking-[0.18em] text-white/35">
              {t.policies}
            </div>
            <div className="mt-6 space-y-4 text-lg text-white/82">
              <Link href={`/${safeLocale}/privacy`} className="block transition hover:text-[#8fa0ff]">
                {t.privacy}
              </Link>
              <Link href={`/${safeLocale}/terms`} className="block transition hover:text-[#8fa0ff]">
                {t.terms}
              </Link>
              <Link href={`/${safeLocale}/cookies`} className="block transition hover:text-[#8fa0ff]">
                {t.cookies}
              </Link>
            </div>
          </div>

          <div>
            <div className="text-sm font-semibold uppercase tracking-[0.18em] text-white/35">
              {t.support}
            </div>
            <div className="mt-6 rounded-[28px] border border-white/10 bg-[#0d1117] p-6 shadow-[0_20px_60px_rgba(0,0,0,0.24)]">
              <div className="flex size-12 items-center justify-center rounded-2xl bg-[#eef0ff] text-[#4b61ff]">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="size-5">
                  <circle cx="12" cy="12" r="8" />
                  <path d="M8.5 12.5l2.1 2.1 4.9-5.1" />
                </svg>
              </div>
              <div className="mt-5 text-2xl font-semibold text-white">{t.supportTitle}</div>
              <p className="mt-4 text-base leading-8 text-white/60">{t.supportBody}</p>
              <a
                href="mailto:destek@coresift.com"
                className="mt-5 inline-flex items-center gap-2 text-lg font-semibold text-white transition hover:text-[#8fa0ff]"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="size-5">
                  <path d="M4 7h16v10H4z" />
                  <path d="M4 8l8 6 8-6" />
                </svg>
                destek@coresift.com
              </a>
            </div>
          </div>
        </div>

        <div className="mt-12 flex flex-col gap-4 border-t border-white/8 pt-8 text-sm text-white/42 lg:flex-row lg:items-center lg:justify-between">
          <div>© 2026 CoreSift. {t.rights}</div>
          <div className="flex flex-wrap gap-x-6 gap-y-2">
            <span>{t.legalLine1}</span>
            <span>{t.legalLine2}</span>
            <span>
              {t.supportLine} <a href="mailto:destek@coresift.com" className="hover:text-white">destek@coresift.com</a>
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default PublicFooter;
