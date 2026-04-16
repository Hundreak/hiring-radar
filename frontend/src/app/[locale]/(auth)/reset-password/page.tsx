'use client';

import Link from 'next/link';
import {Suspense, useMemo, useState} from 'react';
import {usePathname, useRouter, useSearchParams} from 'next/navigation';

import {api} from '@/lib/api';
import type {SupportedLocale} from '@/types/user';

type Copy = {
  eyebrow: string;
  title: string;
  subtitle: string;
  passwordLabel: string;
  passwordPlaceholder: string;
  passwordConfirmationLabel: string;
  passwordConfirmationPlaceholder: string;
  submit: string;
  submitLoading: string;
  successTitle: string;
  successSubtitle: string;
  invalidLink: string;
  generalError: string;
  backToLogin: string;
  required: string;
  passwordMismatch: string;
  passwordCriteriaTitle: string;
  passwordStrengthWeak: string;
  passwordStrengthMedium: string;
  passwordStrengthStrong: string;
  passwordCriteria: {
    min: string;
    upper: string;
    lower: string;
    digit: string;
    special: string;
  };
};

const copy: Record<SupportedLocale, Copy> = {
  tr: {
    eyebrow: 'Şifre sıfırla',
    title: 'Yeni şifreni belirle',
    subtitle:
      'E-postadaki güvenli bağlantı doğrulandıysa yeni şifreni buradan oluşturabilirsin.',
    passwordLabel: 'Yeni şifre',
    passwordPlaceholder: 'Yeni şifrenizi giriniz',
    passwordConfirmationLabel: 'Yeni şifre tekrar',
    passwordConfirmationPlaceholder: 'Yeni şifrenizi yeniden giriniz',
    submit: 'Şifreyi güncelle',
    submitLoading: 'Güncelleniyor...',
    successTitle: 'Şifre güncellendi',
    successSubtitle:
      'Şifren başarıyla güncellendi. Şimdi güvenli şekilde giriş yapabilirsin.',
    invalidLink:
      'Şifre sıfırlama bağlantısı eksik, süresi dolmuş veya geçersiz görünüyor. Lütfen yeni bir bağlantı iste.',
    generalError: 'Şifre şu anda güncellenemedi. Lütfen tekrar dene.',
    backToLogin: 'Giriş ekranına dön',
    required: 'Zorunlu',
    passwordMismatch: 'Şifre tekrarı eşleşmiyor.',
    passwordCriteriaTitle: 'Şifre gereksinimleri',
    passwordStrengthWeak: 'Zayıf',
    passwordStrengthMedium: 'Orta',
    passwordStrengthStrong: 'Güçlü',
    passwordCriteria: {
      min: 'En az 8 karakter',
      upper: 'En az 1 büyük harf',
      lower: 'En az 1 küçük harf',
      digit: 'En az 1 rakam',
      special: 'En az 1 noktalama / özel karakter'
    }
  },
  en: {
    eyebrow: 'Reset password',
    title: 'Set your new password',
    subtitle:
      'If the secure link from your email is valid, you can create your new password here.',
    passwordLabel: 'New password',
    passwordPlaceholder: 'Enter your new password',
    passwordConfirmationLabel: 'Confirm new password',
    passwordConfirmationPlaceholder: 'Re-enter your new password',
    submit: 'Update password',
    submitLoading: 'Updating...',
    successTitle: 'Password updated',
    successSubtitle:
      'Your password has been updated successfully. You can now sign in securely.',
    invalidLink:
      'The password reset link appears to be missing, expired or invalid. Please request a new link.',
    generalError: 'We could not update your password right now. Please try again.',
    backToLogin: 'Back to sign in',
    required: 'Required',
    passwordMismatch: 'Password confirmation does not match.',
    passwordCriteriaTitle: 'Password requirements',
    passwordStrengthWeak: 'Weak',
    passwordStrengthMedium: 'Medium',
    passwordStrengthStrong: 'Strong',
    passwordCriteria: {
      min: 'At least 8 characters',
      upper: 'At least 1 uppercase letter',
      lower: 'At least 1 lowercase letter',
      digit: 'At least 1 number',
      special: 'At least 1 symbol / punctuation mark'
    }
  },
  de: {
    eyebrow: 'Passwort zurücksetzen',
    title: 'Lege dein neues Passwort fest',
    subtitle:
      'Wenn der sichere Link aus deiner E-Mail gültig ist, kannst du hier dein neues Passwort erstellen.',
    passwordLabel: 'Neues Passwort',
    passwordPlaceholder: 'Gib dein neues Passwort ein',
    passwordConfirmationLabel: 'Neues Passwort wiederholen',
    passwordConfirmationPlaceholder: 'Gib dein neues Passwort erneut ein',
    submit: 'Passwort aktualisieren',
    submitLoading: 'Wird aktualisiert...',
    successTitle: 'Passwort aktualisiert',
    successSubtitle:
      'Dein Passwort wurde erfolgreich aktualisiert. Du kannst dich jetzt sicher anmelden.',
    invalidLink:
      'Der Passwort-Reset-Link scheint zu fehlen, abgelaufen oder ungültig zu sein. Bitte fordere einen neuen Link an.',
    generalError: 'Das Passwort konnte gerade nicht aktualisiert werden. Bitte versuche es erneut.',
    backToLogin: 'Zur Anmeldung',
    required: 'Pflichtfeld',
    passwordMismatch: 'Die Passwortbestätigung stimmt nicht überein.',
    passwordCriteriaTitle: 'Passwortanforderungen',
    passwordStrengthWeak: 'Schwach',
    passwordStrengthMedium: 'Mittel',
    passwordStrengthStrong: 'Stark',
    passwordCriteria: {
      min: 'Mindestens 8 Zeichen',
      upper: 'Mindestens 1 Großbuchstabe',
      lower: 'Mindestens 1 Kleinbuchstabe',
      digit: 'Mindestens 1 Zahl',
      special: 'Mindestens 1 Sonderzeichen'
    }
  }
};

function resolveLocaleFromPathname(pathname: string | null): SupportedLocale {
  if (!pathname) return 'tr';
  const segment = pathname.split('/').filter(Boolean)[0];
  if (segment === 'tr' || segment === 'en' || segment === 'de') return segment;
  return 'tr';
}

function getPasswordChecks(password: string) {
  return {
    min: password.length >= 8,
    upper: /[A-ZÇĞİÖŞÜ]/.test(password),
    lower: /[a-zçğıöşü]/.test(password),
    digit: /\d/.test(password),
    special: /[^A-Za-z0-9çğıöşüÇĞİÖŞÜ]/.test(password)
  };
}

function getPasswordStrength(password: string, currentCopy: Copy) {
  const checks = getPasswordChecks(password);
  const score = Object.values(checks).filter(Boolean).length;
  const percentage = (score / 5) * 100;

  if (score <= 2) {
    return {label: currentCopy.passwordStrengthWeak, percentage, tone: 'bg-rose-500'};
  }
  if (score <= 4) {
    return {label: currentCopy.passwordStrengthMedium, percentage, tone: 'bg-amber-500'};
  }
  return {label: currentCopy.passwordStrengthStrong, percentage, tone: 'bg-emerald-500'};
}

function ResetPasswordPageContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const locale = useMemo(() => resolveLocaleFromPathname(pathname), [pathname]);
  const currentCopy = copy[locale];

  const token = searchParams.get('token')?.trim() ?? '';

  const [password, setPassword] = useState('');
  const [passwordConfirmation, setPasswordConfirmation] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [successVisible, setSuccessVisible] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{
    password?: string;
    passwordConfirmation?: string;
  }>({});

  const hasToken = token.length >= 8;
  const passwordChecks = getPasswordChecks(password);
  const passwordStrength = getPasswordStrength(password, currentCopy);
  const strongPasswordReady = Object.values(passwordChecks).every(Boolean);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    if (!hasToken) {
      setErrorMessage(currentCopy.invalidLink);
      return;
    }

    const nextErrors: {password?: string; passwordConfirmation?: string} = {};
    if (!password) nextErrors.password = currentCopy.required;
    if (!passwordConfirmation) nextErrors.passwordConfirmation = currentCopy.required;
    if (password && !strongPasswordReady) nextErrors.password = currentCopy.passwordCriteriaTitle;
    if (password && passwordConfirmation && password !== passwordConfirmation) {
      nextErrors.passwordConfirmation = currentCopy.passwordMismatch;
    }

    setFieldErrors(nextErrors);
    setErrorMessage(null);

    if (Object.keys(nextErrors).length > 0) return;

    setSubmitting(true);

    try {
      await api.confirmPasswordReset({
        token,
        password,
        password_confirmation: passwordConfirmation
      });

      setSuccessVisible(true);
      router.refresh();

      window.setTimeout(() => {
        router.push(`/${locale}/login`);
      }, 1200);
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

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-3xl items-center justify-center px-4 py-10 sm:px-6 lg:px-8">
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

          {!hasToken ? (
            <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
              {currentCopy.invalidLink}
            </div>
          ) : (
            <form className="space-y-4" onSubmit={(event) => void handleSubmit(event)}>
              <div className="space-y-2">
                <label htmlFor="reset-password" className="text-sm font-medium text-white">
                  {currentCopy.passwordLabel}
                </label>
                <input
                  id="reset-password"
                  type="password"
                  autoComplete="new-password"
                  value={password}
                  onChange={(event) => {
                    setPassword(event.target.value);
                    setFieldErrors((previous) => ({...previous, password: undefined}));
                  }}
                  placeholder={currentCopy.passwordPlaceholder}
                  className={`h-12 w-full rounded-2xl border px-4 text-sm text-white outline-none transition ${
                    fieldErrors.password
                      ? 'border-rose-400/80 bg-rose-500/10'
                      : 'border-white/10 bg-[#111827] focus:border-[#5b70ff]'
                  }`}
                />
                {fieldErrors.password ? (
                  <div className="text-sm font-medium text-rose-300">{fieldErrors.password}</div>
                ) : null}
              </div>

              <div className="space-y-2">
                <label
                  htmlFor="reset-password-confirmation"
                  className="text-sm font-medium text-white"
                >
                  {currentCopy.passwordConfirmationLabel}
                </label>
                <input
                  id="reset-password-confirmation"
                  type="password"
                  autoComplete="new-password"
                  value={passwordConfirmation}
                  onChange={(event) => {
                    setPasswordConfirmation(event.target.value);
                    setFieldErrors((previous) => ({
                      ...previous,
                      passwordConfirmation: undefined
                    }));
                  }}
                  placeholder={currentCopy.passwordConfirmationPlaceholder}
                  className={`h-12 w-full rounded-2xl border px-4 text-sm text-white outline-none transition ${
                    fieldErrors.passwordConfirmation
                      ? 'border-rose-400/80 bg-rose-500/10'
                      : 'border-white/10 bg-[#111827] focus:border-[#5b70ff]'
                  }`}
                />
                {fieldErrors.passwordConfirmation ? (
                  <div className="text-sm font-medium text-rose-300">
                    {fieldErrors.passwordConfirmation}
                  </div>
                ) : null}
              </div>

              <div className="rounded-[22px] border border-white/8 bg-white/[0.02] p-4">
                <div className="mb-3 flex items-center justify-between gap-4">
                  <div className="text-sm font-semibold text-white">
                    {currentCopy.passwordCriteriaTitle}
                  </div>
                  <div className="text-sm font-medium text-white/55">{passwordStrength.label}</div>
                </div>

                <div className="h-2 rounded-full bg-white/8">
                  <div
                    className={`h-2 rounded-full ${passwordStrength.tone}`}
                    style={{width: `${passwordStrength.percentage}%`}}
                  />
                </div>

                <div className="mt-4 grid gap-2 text-sm md:grid-cols-2">
                  {[
                    ['min', currentCopy.passwordCriteria.min],
                    ['upper', currentCopy.passwordCriteria.upper],
                    ['lower', currentCopy.passwordCriteria.lower],
                    ['digit', currentCopy.passwordCriteria.digit],
                    ['special', currentCopy.passwordCriteria.special]
                  ].map(([key, label]) => {
                    const passed = passwordChecks[key as keyof typeof passwordChecks];
                    return (
                      <div
                        key={key}
                        className={`rounded-xl px-3 py-2 ${
                          passed
                            ? 'bg-emerald-500/10 text-emerald-200'
                            : 'bg-white/[0.03] text-white/55'
                        }`}
                      >
                        {label}
                      </div>
                    );
                  })}
                </div>
              </div>

              {successVisible ? (
                <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
                  <div className="font-semibold">{currentCopy.successTitle}</div>
                  <div className="mt-1">{currentCopy.successSubtitle}</div>
                </div>
              ) : null}

              {errorMessage ? (
                <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
                  {errorMessage}
                </div>
              ) : null}

              <button
                type="submit"
                disabled={submitting}
                className="inline-flex h-12 w-full items-center justify-center rounded-2xl bg-[#3b52f0] px-5 text-sm font-medium text-white transition hover:bg-[#3348da] disabled:opacity-60"
              >
                {submitting ? currentCopy.submitLoading : currentCopy.submit}
              </button>
            </form>
          )}

          <Link
            href={`/${locale}/login`}
            className="inline-flex text-sm font-medium text-[#8fa0ff] transition hover:text-white"
          >
            {currentCopy.backToLogin}
          </Link>
        </div>
      </section>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="min-h-screen bg-[#07090d] text-white">
      <Suspense fallback={<div className="min-h-screen bg-[#07090d]" />}>
        <ResetPasswordPageContent />
      </Suspense>
    </div>
  );
}