'use client';

import {useMemo, useState} from 'react';
import {Mail, Send} from 'lucide-react';

import type {SupportedLocale} from '@/types/user';

type Copy = {
  title: string;
  subtitle: string;
  firstName: string;
  lastName: string;
  email: string;
  subject: string;
  message: string;
  firstNamePlaceholder: string;
  lastNamePlaceholder: string;
  emailPlaceholder: string;
  subjectPlaceholder: string;
  messagePlaceholder: string;
  submit: string;
  success: string;
  timelineTitle: string;
  timelineBody: string;
  noteTitle: string;
  noteBody: string;
  required: string;
};

const copy: Record<SupportedLocale, Copy> = {
  tr: {
    title: 'İletişim Formu',
    subtitle: 'Destek ekibimize doğrudan yazın. Talebiniz kayıt altına alınır.',
    firstName: 'Ad',
    lastName: 'Soyad',
    email: 'E-posta',
    subject: 'Başlık',
    message: 'Mesaj',
    firstNamePlaceholder: 'Adınızı giriniz',
    lastNamePlaceholder: 'Soyadınızı giriniz',
    emailPlaceholder: 'E-posta adresinizi giriniz',
    subjectPlaceholder: 'Durumla ilgili kısa bir başlık yazınız',
    messagePlaceholder: 'Mesajınızı yazınız',
    submit: 'Gönder',
    success:
      'Mesajın alındı. Canlı destek işleme hattı bağlandığında ekip bu talebi kayıt üzerinden değerlendirecek.',
    timelineTitle: 'Sonraki adım ne olacak?',
    timelineBody:
      'Talebin konu başlığı, mesaj içeriği ve iletişim bilgilerinle birlikte tek bir destek kaydı olarak değerlendirilir. Güvenlik ve hesap erişimi talepleri daha yüksek öncelikle ele alınır.',
    noteTitle: 'Daha hızlı dönüş için',
    noteBody:
      'Hesapla ilgili bir konuysa kayıtlı e-posta adresini kullanmanı ve başlık kısmını mümkün olduğunca net yazmanı öneririz.',
    required: 'Zorunlu'
  },
  en: {
    title: 'Contact Form',
    subtitle: 'Write directly to our support team. Your request will be recorded clearly.',
    firstName: 'First Name',
    lastName: 'Last Name',
    email: 'Email',
    subject: 'Subject',
    message: 'Message',
    firstNamePlaceholder: 'Enter your first name',
    lastNamePlaceholder: 'Enter your last name',
    emailPlaceholder: 'Enter your email address',
    subjectPlaceholder: 'Write a short subject about the issue',
    messagePlaceholder: 'Write your message',
    submit: 'Send',
    success:
      'Your message has been received. Once the live support processing line is connected, the team will review it through the support record.',
    timelineTitle: 'What happens next?',
    timelineBody:
      'Your request is evaluated as a single support record with the subject, message body and contact information you provide. Security and account-access issues are prioritized.',
    noteTitle: 'For a faster response',
    noteBody:
      'If the issue is account-related, use your registered email address and keep the subject line as clear as possible.',
    required: 'Required'
  },
  de: {
    title: 'Kontaktformular',
    subtitle: 'Schreibe direkt an unser Support-Team. Deine Anfrage wird sauber erfasst.',
    firstName: 'Vorname',
    lastName: 'Nachname',
    email: 'E-Mail',
    subject: 'Betreff',
    message: 'Nachricht',
    firstNamePlaceholder: 'Gib deinen Vornamen ein',
    lastNamePlaceholder: 'Gib deinen Nachnamen ein',
    emailPlaceholder: 'Gib deine E-Mail-Adresse ein',
    subjectPlaceholder: 'Schreibe einen kurzen Betreff zum Anliegen',
    messagePlaceholder: 'Schreibe deine Nachricht',
    submit: 'Senden',
    success:
      'Deine Nachricht wurde empfangen. Sobald die Live-Support-Verarbeitung verbunden ist, prüft das Team die Anfrage über den Support-Eintrag.',
    timelineTitle: 'Wie geht es weiter?',
    timelineBody:
      'Deine Anfrage wird mit Betreff, Nachricht und Kontaktdaten als ein strukturierter Support-Fall geprüft. Sicherheits- und Kontozugriffsanliegen erhalten höhere Priorität.',
    noteTitle: 'Für eine schnellere Rückmeldung',
    noteBody:
      'Wenn es um dein Konto geht, nutze bitte deine registrierte E-Mail-Adresse und formuliere den Betreff so klar wie möglich.',
    required: 'Pflichtfeld'
  }
};

type Props = {
  locale: SupportedLocale;
};

type Errors = {
  firstName?: string;
  email?: string;
  subject?: string;
  message?: string;
};

export function ContactForm({locale}: Props) {
  const t = useMemo(() => copy[locale], [locale]);

  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [errors, setErrors] = useState<Errors>({});

  function validate(): boolean {
    const nextErrors: Errors = {};
    if (!firstName.trim()) nextErrors.firstName = t.required;
    if (!email.trim()) nextErrors.email = t.required;
    if (!subject.trim()) nextErrors.subject = t.required;
    if (!message.trim()) nextErrors.message = t.required;
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!validate()) return;
    setSubmitted(true);
  }

  return (
    <div className="space-y-6">
      <div className="rounded-[28px] border border-white/10 bg-[#171717] p-6 md:p-8">
        <div className="mb-6 flex items-center gap-3">
          <div className="flex size-12 items-center justify-center rounded-2xl bg-[#eef0ff] text-[#3b52f0]">
            <Mail className="size-5" />
          </div>
          <div>
            <div className="text-lg font-semibold text-white">{t.title}</div>
            <div className="text-sm text-white/55">{t.subtitle}</div>
          </div>
        </div>

        {submitted ? (
          <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 px-5 py-4 text-sm leading-7 text-emerald-200">
            {t.success}
          </div>
        ) : (
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-[0.12em] text-white/48">
                  {t.firstName}
                </label>
                <input
                  value={firstName}
                  onChange={(event) => {
                    setFirstName(event.target.value);
                    setErrors((previous) => ({...previous, firstName: undefined}));
                  }}
                  placeholder={t.firstNamePlaceholder}
                  className={`h-14 w-full rounded-2xl border px-4 text-white placeholder:text-white/30 outline-none transition ${
                    errors.firstName
                      ? 'border-rose-400/80 bg-rose-500/10'
                      : 'border-white/10 bg-[#111111] focus:border-[#6175ff]'
                  }`}
                />
                {errors.firstName ? (
                  <div className="text-sm font-medium text-rose-300">{errors.firstName}</div>
                ) : null}
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-[0.12em] text-white/48">
                  {t.lastName}
                </label>
                <input
                  value={lastName}
                  onChange={(event) => setLastName(event.target.value)}
                  placeholder={t.lastNamePlaceholder}
                  className="h-14 w-full rounded-2xl border border-white/10 bg-[#111111] px-4 text-white placeholder:text-white/30 outline-none transition focus:border-[#6175ff]"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-[0.12em] text-white/48">
                {t.email}
              </label>
              <input
                value={email}
                onChange={(event) => {
                  setEmail(event.target.value);
                  setErrors((previous) => ({...previous, email: undefined}));
                }}
                type="email"
                placeholder={t.emailPlaceholder}
                className={`h-14 w-full rounded-2xl border px-4 text-white placeholder:text-white/30 outline-none transition ${
                  errors.email
                    ? 'border-rose-400/80 bg-rose-500/10'
                    : 'border-white/10 bg-[#111111] focus:border-[#6175ff]'
                }`}
              />
              {errors.email ? (
                <div className="text-sm font-medium text-rose-300">{errors.email}</div>
              ) : null}
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-[0.12em] text-white/48">
                {t.subject}
              </label>
              <input
                value={subject}
                onChange={(event) => {
                  setSubject(event.target.value);
                  setErrors((previous) => ({...previous, subject: undefined}));
                }}
                placeholder={t.subjectPlaceholder}
                className={`h-14 w-full rounded-2xl border px-4 text-white placeholder:text-white/30 outline-none transition ${
                  errors.subject
                    ? 'border-rose-400/80 bg-rose-500/10'
                    : 'border-white/10 bg-[#111111] focus:border-[#6175ff]'
                }`}
              />
              {errors.subject ? (
                <div className="text-sm font-medium text-rose-300">{errors.subject}</div>
              ) : null}
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-[0.12em] text-white/48">
                {t.message}
              </label>
              <textarea
                value={message}
                onChange={(event) => {
                  setMessage(event.target.value);
                  setErrors((previous) => ({...previous, message: undefined}));
                }}
                rows={7}
                placeholder={t.messagePlaceholder}
                className={`w-full rounded-2xl border px-4 py-4 text-white placeholder:text-white/30 outline-none transition ${
                  errors.message
                    ? 'border-rose-400/80 bg-rose-500/10'
                    : 'border-white/10 bg-[#111111] focus:border-[#6175ff]'
                }`}
              />
              {errors.message ? (
                <div className="text-sm font-medium text-rose-300">{errors.message}</div>
              ) : null}
            </div>

            <button
              type="submit"
              className="inline-flex items-center rounded-2xl bg-[#3b52f0] px-6 py-3 text-sm font-semibold text-white transition hover:bg-[#3147db]"
            >
              {t.submit}
              <Send className="ml-2 size-4" />
            </button>
          </form>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-[24px] border border-white/10 bg-[#171717] p-6">
          <div className="text-base font-semibold text-white">{t.timelineTitle}</div>
          <p className="mt-3 text-sm leading-7 text-white/62">{t.timelineBody}</p>
        </div>

        <div className="rounded-[24px] border border-white/10 bg-[#171717] p-6">
          <div className="text-base font-semibold text-white">{t.noteTitle}</div>
          <p className="mt-3 text-sm leading-7 text-white/62">{t.noteBody}</p>
        </div>
      </div>
    </div>
  );
}