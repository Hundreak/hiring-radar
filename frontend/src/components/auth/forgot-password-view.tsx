'use client';

import Link from 'next/link';
import {useEffect, useMemo, useState} from 'react';

import {api} from '@/lib/api';
import type {SupportedLocale} from '@/types/user';

type Copy = {
  eyebrow: string;
  title: string;
  subtitle: string;
  emailLabel: string;
  emailPlaceholder: string;
  submit: string;
  submitLoading: string;
  successTitle: string;
  successSubtitle: string;
  resendLocked: string;
  resendReady: string;
  resendButton: string;
  generalError: string;
  backToLogin: string;
  required: string;
};

const copy: Record<SupportedLocale, Copy> = {
  tr: {
    eyebrow: 'Şifremi unuttum',
    title: 'Şifreni güvenli şekilde sıfırla',
    subtitle:
      'Kayıtlı e-posta adresini gir. Hesap uygunsa sana güvenli bir sıfırlama bağlantısı göndereceğiz.',
    emailLabel: 'E-posta',
    emailPlaceholder: 'E-posta adresinizi giriniz',
    submit: 'Sıfırlama bağlantısı gönder',
    submitLoading: 'Gönderiliyor...',
    successTitle: 'Sıfırlama bağlantısı gönderildi',
    successSubtitle:
      'Eğer bu e-posta için uygun bir hesap varsa, şifre sıfırlama bağlantısı e-posta adresine gönderildi.',
    resendLocked: 'E-posta ulaşmadıysa yeniden göndermek için bekleme süresi:',
    resendReady: 'E-posta ulaşmadıysa yeniden gönderebilirsin.',
    resendButton: 'Bağlantıyı yeniden gönder',
    generalError: 'Şu anda işlem tamamlanamadı. Lütfen tekrar dene.',
    backToLogin: 'Giriş ekranına dön',
    required: 'Zorunlu'
  },
  en: {
    eyebrow: 'Forgot password',
    title: 'Reset your password securely',
    subtitle:
      'Enter your registered email address. If the account is eligible, we will send a secure reset link.',
    emailLabel: 'Email',
    emailPlaceholder: 'Enter your email address',
    submit: 'Send reset link',
    submitLoading: 'Sending...',
    successTitle: 'Reset link sent',
    successSubtitle:
      'If this email is eligible, a secure password reset link has been sent to the email address.',
    resendLocked: 'If the email has not arrived, wait before sending again:',
    resendReady: 'If the email has not arrived, you can send it again now.',
    resendButton: 'Send link again',
    generalError: 'We could not complete this request right now. Please try again.',
    backToLogin: 'Back to sign in',
    required: 'Required'
  },
  de: {
    eyebrow: 'Passwort vergessen',
    title: 'Setze dein Passwort sicher zurück',
    subtitle:
      'Gib deine registrierte E-Mail-Adresse ein. Falls das Konto berechtigt ist, senden wir dir einen sicheren Reset-Link.',
    emailLabel: 'E-Mail',
    emailPlaceholder: 'Gib deine E-Mail-Adresse ein',
    submit: 'Reset-Link senden',
    submitLoading: 'Wird gesendet...',
    successTitle: 'Reset-Link gesendet',
    successSubtitle:
      'Falls diese E-Mail-Adresse berechtigt ist, wurde ein sicherer Passwort-Reset-Link an die E-Mail-Adresse gesendet.',
    resendLocked: 'Falls die E-Mail nicht angekommen ist, warte vor dem erneuten Senden:',
    resendReady: 'Falls die E-Mail nicht angekommen ist, kannst du sie jetzt erneut senden.',
    resendButton: 'Link erneut senden',
    generalError:
      'Die Anfrage konnte gerade nicht abgeschlossen werden. Bitte versuche es erneut.',
    backToLogin: 'Zur Anmeldung',
    required: 'Pflichtfeld'
  }
};

const RESEND_SECONDS = 180;

function resolveLocale(locale: string): SupportedLocale {
  if (locale === 'tr' || locale === 'en' || locale === 'de') return locale;
  return 'tr';
}

function formatCountdown(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

export function ForgotPasswordView({locale}: {locale: string}) {
  const safeLocale = useMemo(() => resolveLocale(locale), [locale]);
  const currentCopy = copy[safeLocale];

  const [email, setEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [successVisible, setSuccessVisible] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [remainingSeconds, setRemainingSeconds] = useState(0);

  useEffect(() => {
    if (remainingSeconds <= 0) return;

    const timer = window.setInterval(() => {
      setRemainingSeconds((previous) => {
        if (previous <= 1) {
          window.clearInterval(timer);
          return 0;
        }
        return previous - 1;
      });
    }, 1000);

    return () => window.clearInterval(timer);
  }, [remainingSeconds]);

  async function sendResetLink(forceResend = false): Promise<void> {
    setErrorMessage(null);
    setFieldError(null);

    if (!email.trim()) {
      setFieldError(currentCopy.required);
      return;
    }

    if (!forceResend && successVisible && remainingSeconds > 0) {
      return;
    }

    setSubmitting(true);

    try {
      await api.requestPasswordReset(email.trim());
      setSuccessVisible(true);
      setRemainingSeconds(RESEND_SECONDS);
    } catch (reason) {
      if (reason instanceof Error) {
        setErrorMessage(reason.message || currentCopy.generalError);
      } else {
        setErrorMessage(currentCopy.generalError);
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    await sendResetLink(false);
  }

  const resendLocked = successVisible && remainingSeconds > 0;

  return (
    <div className="container-shell flex min-h-screen items-center justify-center py-10">
      <div className="mx-auto flex w-full max-w-3xl items-center justify-center">
        <section className="w-full rounded-[28px] border border-white/10 bg-[#101828] p-6 shadow-[0_20px_60px_-36px_rgba(15,23,42,0.35)] sm:p-8">
          <div className="space-y-6">
            <div className="space-y-2">
              <div className="inline-flex rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs font-medium uppercase tracking-[0.18em] text-white/60 backdrop-blur">
                {currentCopy.eyebrow}
              </div>
              <h1 className="text-3xl font-semibold tracking-tight text-white">
                {currentCopy.title}
              </h1>
              <p className="text-sm leading-6 text-white/62 sm:text-base">
                {currentCopy.subtitle}
              </p>
            </div>

            <form className="space-y-4" onSubmit={(event) => void handleSubmit(event)}>
              <div className="space-y-2">
                <label htmlFor="forgot-password-email" className="text-sm font-medium text-white">
                  {currentCopy.emailLabel}
                </label>
                <input
                  id="forgot-password-email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => {
                    setEmail(event.target.value);
                    setFieldError(null);
                  }}
                  placeholder={currentCopy.emailPlaceholder}
                  className={`h-12 w-full rounded-2xl border px-4 text-sm text-white outline-none transition ${
                    fieldError
                      ? 'border-rose-400/80 bg-rose-500/10'
                      : 'border-white/10 bg-[#111827] focus:border-[#5b70ff]'
                  }`}
                />
                {fieldError ? (
                  <div className="text-sm font-medium text-rose-300">{fieldError}</div>
                ) : null}
              </div>

              {successVisible ? (
                <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
                  <div className="font-semibold">{currentCopy.successTitle}</div>
                  <div className="mt-1">{currentCopy.successSubtitle}</div>

                  <div className="mt-3 border-t border-emerald-400/10 pt-3">
                    {remainingSeconds > 0 ? (
                      <div className="text-emerald-100/90">
                        {currentCopy.resendLocked}{' '}
                        <span className="font-semibold">{formatCountdown(remainingSeconds)}</span>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <div>{currentCopy.resendReady}</div>
                        <button
                          type="button"
                          onClick={() => void sendResetLink(true)}
                          className="inline-flex rounded-xl border border-emerald-300/20 bg-emerald-500/10 px-4 py-2 text-sm font-semibold text-emerald-100 transition hover:bg-emerald-500/15"
                        >
                          {currentCopy.resendButton}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ) : null}

              {errorMessage ? (
                <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
                  {errorMessage}
                </div>
              ) : null}

              <button
                type="submit"
                disabled={submitting || resendLocked}
                className="inline-flex h-12 w-full items-center justify-center rounded-2xl bg-[#e5e7eb] px-5 text-sm font-medium text-[#1f2937] transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {submitting ? currentCopy.submitLoading : currentCopy.submit}
              </button>
            </form>

            <Link
              href={`/${safeLocale}/login`}
              className="inline-flex text-sm font-medium text-[#8fa0ff] transition hover:text-white"
            >
              {currentCopy.backToLogin}
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}