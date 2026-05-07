'use client';

import Link from 'next/link';
import {useEffect, useMemo, useRef, useState, useCallback} from 'react';
import {usePathname, useRouter, useSearchParams} from 'next/navigation';

import {ApiError, api} from '@/lib/api';
import type {SupportedLocale} from '@/types/user';

type Copy = {
  eyebrow: string;
  title: string;
  subtitle: string;
  emailLabel: string;
  passwordLabel: string;
  emailPlaceholder: string;
  passwordPlaceholder: string;
  submit: string;
  submitLoading: string;
  passwordHelp: string;
  divider: string;
  dividerOrEmail: string;
  googleButton: string;
  magicLinkTitle: string;
  magicLinkDescription: string;
  magicLinkButton: string;
  magicLinkButtonLoading: string;
  magicLinkEmailHelp: string;
  magicLinkSuccess: string;
  magicLinkConsumingTitle: string;
  magicLinkConsumingDescription: string;
  magicLinkInvalid: string;
  forgotPassword: string;
  generalError: string;
  invalidCredentials: string;
  googleAuthError: string;
  backToHome: string;
  required: string;
  tabs: {
    login: string;
    signup: string;
  };
  roleTabs: {
    candidate: string;
    employer: string;
  };
  employer: {
    emailLabel: string;
    emailPlaceholder: string;
    submit: string;
    submitLoading: string;
    forgotPassword: string;
    passwordHelp: string;
    googleButton: string;
  };
  leftSteps: Array<{title: string; description: string}>;
};

const copy: Record<SupportedLocale, Copy> = {
  tr: {
    eyebrow: 'Giriş yap',
    title: 'Hesabını profesyonel biçimde oluştur',
    subtitle:
      'E-posta ve şifrenle giriş yapabilir ya da şifresiz giriş bağlantısı isteyebilirsin. Her iki alan birbirinden bağımsız çalışır.',
    emailLabel: 'E-posta',
    passwordLabel: 'Şifre',
    emailPlaceholder: 'E-posta adresinizi giriniz',
    passwordPlaceholder: 'Şifrenizi giriniz',
    submit: 'Giriş yap',
    submitLoading: 'Giriş yapılıyor...',
    passwordHelp: 'E-posta ve şifrenle doğrudan hesabına giriş yap.',
    divider: 'veya',
    dividerOrEmail: 'veya e-posta ile devam et',
    googleButton: 'Google ile giriş yap',
    magicLinkTitle: 'Giriş linki gönder',
    magicLinkDescription:
      'Şifresiz giriş için yalnızca e-posta adresini yazman yeterli. Güvenli bağlantı e-postana gönderilir.',
    magicLinkButton: 'Giriş linki gönder',
    magicLinkButtonLoading: 'Gönderiliyor...',
    magicLinkEmailHelp: 'Bu alan, giriş formundan bağımsız çalışır.',
    magicLinkSuccess:
      'Eğer bu e-posta için uygun bir hesap varsa, güvenli giriş bağlantısı gönderildi.',
    magicLinkConsumingTitle: 'Güvenli giriş doğrulanıyor',
    magicLinkConsumingDescription:
      'E-postadaki giriş bağlantısı kontrol ediliyor. Doğrulama tamamlanınca hesabına yönlendirileceksin.',
    magicLinkInvalid:
      'Bu giriş bağlantısı geçersiz, süresi dolmuş veya daha önce kullanılmış olabilir. Lütfen yeni bir bağlantı iste ve tekrar dene.',
    forgotPassword: 'Şifremi Unuttum?',
    generalError: 'Şu anda giriş yapılamadı. Lütfen tekrar dene.',
    invalidCredentials: 'E-posta veya şifre hatalı.',
    googleAuthError: 'Google ile giriş sırasında bir sorun oluştu. Lütfen tekrar dene.',
    backToHome: 'Ana sayfaya dön',
    required: 'Zorunlu',
    tabs: {
      login: 'Giriş Yap',
      signup: 'Üye Ol'
    },
    roleTabs: {
      candidate: 'Aday Girişi',
      employer: 'İşveren Girişi'
    },
    employer: {
      emailLabel: 'Şirket E-postası',
      emailPlaceholder: 'Sirket e-posta adresinizi giriniz',
      submit: 'İşveren olarak giriş yap',
      submitLoading: 'Giriş yapılıyor...',
      forgotPassword: 'Şifremi unuttum',
      passwordHelp: 'Şirket e-posta ve şifrenle işveren paneline giriş yap.',
      googleButton: 'Google ile giriş yap'
    },
    leftSteps: [
      {
        title: 'Bilgilerini gir',
        description: 'E-posta ve şifrenle giriş yap veya giriş linki talep et.'
      },
      {
        title: 'Hesabına güvenli eriş',
        description: 'Oturumun doğrulanır ve seni profil alanına yönlendiririz.'
      },
      {
        title: 'Profilini güçlendir',
        description: 'Eşleşme kaliteni artırmak için eksik alanlarını tamamla.'
      }
    ]
  },
  en: {
    eyebrow: 'Sign in',
    title: 'Sign in to your account professionally',
    subtitle:
      'Use your email and password, or request a passwordless sign-in link. Both sections work independently.',
    emailLabel: 'Email',
    passwordLabel: 'Password',
    emailPlaceholder: 'Enter your email address',
    passwordPlaceholder: 'Enter your password',
    submit: 'Sign in',
    submitLoading: 'Signing in...',
    passwordHelp: 'Use your email and password to access your account directly.',
    divider: 'or',
    dividerOrEmail: 'or continue with email',
    googleButton: 'Sign in with Google',
    magicLinkTitle: 'Send sign-in link',
    magicLinkDescription:
      'For passwordless sign-in, simply enter your email address and we will send a secure link.',
    magicLinkButton: 'Send sign-in link',
    magicLinkButtonLoading: 'Sending...',
    magicLinkEmailHelp: 'This area works independently from the password login form.',
    magicLinkSuccess:
      'If this email is eligible, a secure sign-in link has been sent.',
    magicLinkConsumingTitle: 'Verifying secure sign-in',
    magicLinkConsumingDescription:
      'We are validating the sign-in link from your email and will redirect you once it is confirmed.',
    magicLinkInvalid:
      'This sign-in link is invalid, expired, or has already been used. Please request a new one.',
    forgotPassword: 'Forgot password?',
    generalError: 'We could not sign you in right now. Please try again.',
    invalidCredentials: 'Invalid email or password.',
    googleAuthError: 'Something went wrong signing in with Google. Please try again.',
    backToHome: 'Back to home',
    required: 'Required',
    tabs: {
      login: 'Sign In',
      signup: 'Sign Up'
    },
    roleTabs: {
      candidate: 'Candidate Login',
      employer: 'Employer Login'
    },
    employer: {
      emailLabel: 'Company Email',
      emailPlaceholder: 'Enter your company email address',
      submit: 'Login as Employer',
      submitLoading: 'Signing in...',
      forgotPassword: 'Forgot password?',
      passwordHelp: 'Use your company email and password to access the employer panel.',
      googleButton: 'Sign in with Google'
    },
    leftSteps: [
      {
        title: 'Enter your details',
        description: 'Use your email and password or request a one-time sign-in link.'
      },
      {
        title: 'Access your account securely',
        description: 'We verify your session and take you to your profile area.'
      },
      {
        title: 'Strengthen your profile',
        description: 'Complete the missing signals that improve your match quality.'
      }
    ]
  },
  de: {
    eyebrow: 'Anmelden',
    title: 'Melde dich professionell in dein Konto an',
    subtitle:
      'Nutze E-Mail und Passwort oder fordere einen passwortlosen Anmeldelink an. Beide Bereiche funktionieren unabhängig.',
    emailLabel: 'E-Mail',
    passwordLabel: 'Passwort',
    emailPlaceholder: 'Gib deine E-Mail-Adresse ein',
    passwordPlaceholder: 'Gib dein Passwort ein',
    submit: 'Anmelden',
    submitLoading: 'Anmeldung läuft...',
    passwordHelp: 'Nutze E-Mail und Passwort für den direkten Zugriff auf dein Konto.',
    divider: 'oder',
    dividerOrEmail: 'oder mit E-Mail fortfahren',
    googleButton: 'Mit Google anmelden',
    magicLinkTitle: 'Anmeldelink senden',
    magicLinkDescription:
      'Für die Anmeldung ohne Passwort genügt deine E-Mail-Adresse. Wir senden dir einen sicheren Link.',
    magicLinkButton: 'Anmeldelink senden',
    magicLinkButtonLoading: 'Wird gesendet...',
    magicLinkEmailHelp: 'Dieser Bereich funktioniert unabhängig vom Passwort-Login.',
    magicLinkSuccess:
      'Falls diese E-Mail-Adresse berechtigt ist, wurde ein sicherer Anmeldelink gesendet.',
    magicLinkConsumingTitle: 'Sicherer Login wird geprüft',
    magicLinkConsumingDescription:
      'Der Link aus deiner E-Mail wird validiert. Danach wirst du weitergeleitet.',
    magicLinkInvalid:
      'Dieser Anmeldelink ist ungültig, abgelaufen oder wurde bereits verwendet. Bitte fordere einen neuen Link an.',
    forgotPassword: 'Passwort vergessen?',
    generalError:
      'Die Anmeldung konnte gerade nicht abgeschlossen werden. Bitte versuche es erneut.',
    invalidCredentials: 'E-Mail oder Passwort ist nicht korrekt.',
    googleAuthError: 'Bei der Anmeldung mit Google ist ein Problem aufgetreten. Bitte versuche es erneut.',
    backToHome: 'Zur Startseite',
    required: 'Pflichtfeld',
    tabs: {
      login: 'Anmelden',
      signup: 'Registrieren'
    },
    roleTabs: {
      candidate: 'Bewerber-Login',
      employer: 'Arbeitgeber-Login'
    },
    employer: {
      emailLabel: 'Unternehmens-E-Mail',
      emailPlaceholder: 'Geben Sie Ihre Unternehmens-E-Mail ein',
      submit: 'Als Arbeitgeber anmelden',
      submitLoading: 'Anmeldung läuft...',
      forgotPassword: 'Passwort vergessen?',
      passwordHelp: 'Nutze Unternehmens-E-Mail und Passwort für den Arbeitgeber-Zugang.',
      googleButton: 'Mit Google anmelden'
    },
    leftSteps: [
      {
        title: 'Daten eingeben',
        description: 'Nutze E-Mail und Passwort oder fordere einen Einmal-Link an.'
      },
      {
        title: 'Sicher anmelden',
        description: 'Deine Sitzung wird geprüft und du wirst ins Konto geleitet.'
      },
      {
        title: 'Profil stärken',
        description: 'Ergänze fehlende Profilsignale für bessere Übereinstimmungen.'
      }
    ]
  }
};

function resolveLocaleFromPathname(pathname: string | null): SupportedLocale {
  if (!pathname) return 'tr';
  const segment = pathname.split('/').filter(Boolean)[0];
  if (segment === 'tr' || segment === 'en' || segment === 'de') return segment;
  return 'tr';
}

function sanitizeRedirectTarget(value: string | null, locale: SupportedLocale): string {
  if (!value || !value.startsWith('/')) {
    return `/${locale}/settings/profile`;
  }
  if (value.startsWith('//')) {
    return `/${locale}/settings/profile`;
  }
  return value;
}

type FieldErrors = {
  passwordEmail?: string;
  password?: string;
  magicLinkEmail?: string;
  employerEmail?: string;
  employerPassword?: string;
};

type LoginRole = 'candidate' | 'employer';

type LoginViewProps = {
  locale?: string;
};

export function LoginView({locale: localeProp}: LoginViewProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const locale = useMemo<SupportedLocale>(() => {
    if (localeProp === 'tr' || localeProp === 'en' || localeProp === 'de') {
      return localeProp;
    }
    return resolveLocaleFromPathname(pathname);
  }, [localeProp, pathname]);

  const currentCopy = copy[locale];

  /* ── role tab state ── */
  const roleFromUrl = searchParams.get('role');
  const initialRole: LoginRole = roleFromUrl === 'employer' ? 'employer' : 'candidate';
  const [activeRole, setActiveRole] = useState<LoginRole>(initialRole);

  const updateRole = useCallback(
    (newRole: LoginRole) => {
      setActiveRole(newRole);
      const params = new URLSearchParams(searchParams.toString());
      if (newRole === 'employer') {
        params.set('role', 'employer');
      } else {
        params.delete('role');
      }
      router.replace(`${pathname}?${params.toString()}`, {scroll: false});
    },
    [pathname, router, searchParams]
  );

  /* ── candidate form state ── */
  const [passwordEmail, setPasswordEmail] = useState('');
  const [password, setPassword] = useState('');
  const [magicLinkEmail, setMagicLinkEmail] = useState('');
  const [passwordSubmitting, setPasswordSubmitting] = useState(false);
  const [magicLinkSubmitting, setMagicLinkSubmitting] = useState(false);
  const [magicLinkSuccess, setMagicLinkSuccess] = useState<string | null>(null);
  const [magicLinkConsuming, setMagicLinkConsuming] = useState(false);

  /* ── employer form state ── */
  const [employerEmail, setEmployerEmail] = useState('');
  const [employerPassword, setEmployerPassword] = useState('');
  const [employerSubmitting, setEmployerSubmitting] = useState(false);

  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const attemptedMagicToken = useRef<string | null>(null);

  const redirectTarget = sanitizeRedirectTarget(
    searchParams.get('redirect') ?? searchParams.get('next'),
    locale
  );
  const magicToken = searchParams.get('token');
  const magicLinkEmailFromUrl = searchParams.get('email');
  const googleError = searchParams.get('error');

  useEffect(() => {
    if (!magicLinkEmailFromUrl?.trim()) return;
    setMagicLinkEmail((currentValue) => currentValue || magicLinkEmailFromUrl.trim());
  }, [magicLinkEmailFromUrl]);

  useEffect(() => {
    if (
      googleError === 'google_auth_failed' ||
      googleError === 'google_not_configured' ||
      googleError === 'google_auth_cancelled'
    ) {
      if (googleError !== 'google_auth_cancelled') {
        setErrorMessage(currentCopy.googleAuthError);
      }
    }
  }, [googleError, currentCopy.googleAuthError]);

  useEffect(() => {
    if (!magicToken || attemptedMagicToken.current === magicToken) return;

    attemptedMagicToken.current = magicToken;
    setErrorMessage(null);
    setMagicLinkSuccess(null);
    setMagicLinkConsuming(true);

    let active = true;

    void api
      .consumeMagicLink(magicToken)
      .then(() => {
        if (!active) return;
        router.replace(redirectTarget);
        router.refresh();
      })
      .catch((reason) => {
        if (!active) return;
        if (reason instanceof ApiError && reason.status === 400) {
          setErrorMessage(currentCopy.magicLinkInvalid);
        } else if (reason instanceof Error) {
          setErrorMessage(reason.message || currentCopy.generalError);
        } else {
          setErrorMessage(currentCopy.generalError);
        }
      })
      .finally(() => {
        if (active) setMagicLinkConsuming(false);
      });

    return () => {
      active = false;
    };
  }, [currentCopy.generalError, currentCopy.magicLinkInvalid, magicToken, redirectTarget, router]);

  async function handlePasswordSubmit(
    event: React.FormEvent<HTMLFormElement>
  ): Promise<void> {
    event.preventDefault();
    setErrorMessage(null);
    setMagicLinkSuccess(null);

    const nextErrors: FieldErrors = {};
    if (!passwordEmail.trim()) nextErrors.passwordEmail = currentCopy.required;
    if (!password.trim()) nextErrors.password = currentCopy.required;
    setFieldErrors((previous) => ({...previous, ...nextErrors}));

    if (Object.keys(nextErrors).length > 0) return;

    setPasswordSubmitting(true);

    try {
      await api.loginWithPassword({
        email: passwordEmail.trim(),
        password
      });

      router.push(redirectTarget);
      router.refresh();
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 401) {
        setErrorMessage(currentCopy.invalidCredentials);
      } else if (reason instanceof Error) {
        setErrorMessage(reason.message || currentCopy.generalError);
      } else {
        setErrorMessage(currentCopy.generalError);
      }
    } finally {
      setPasswordSubmitting(false);
    }
  }

  async function handleEmployerSubmit(
    event: React.FormEvent<HTMLFormElement>
  ): Promise<void> {
    event.preventDefault();
    setErrorMessage(null);

    const nextErrors: FieldErrors = {};
    if (!employerEmail.trim()) nextErrors.employerEmail = currentCopy.required;
    if (!employerPassword.trim()) nextErrors.employerPassword = currentCopy.required;
    setFieldErrors((previous) => ({...previous, ...nextErrors}));

    if (Object.keys(nextErrors).length > 0) return;

    setEmployerSubmitting(true);

    try {
      await api.loginEmployer({
        email: employerEmail.trim(),
        password: employerPassword
      });

      router.push(`/${locale}/employer/dashboard`);
      router.refresh();
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 401) {
        setErrorMessage(currentCopy.invalidCredentials);
      } else if (reason instanceof Error) {
        setErrorMessage(reason.message || currentCopy.generalError);
      } else {
        setErrorMessage(currentCopy.generalError);
      }
    } finally {
      setEmployerSubmitting(false);
    }
  }

  async function handleMagicLink(): Promise<void> {
    setErrorMessage(null);
    setMagicLinkSuccess(null);

    const nextErrors: FieldErrors = {};
    if (!magicLinkEmail.trim()) nextErrors.magicLinkEmail = currentCopy.required;
    setFieldErrors((previous) => ({...previous, ...nextErrors}));

    if (Object.keys(nextErrors).length > 0) return;

    setMagicLinkSubmitting(true);

    try {
      const response = await api.requestMagicLink(magicLinkEmail.trim(), redirectTarget);
      setMagicLinkSuccess(response.message || currentCopy.magicLinkSuccess);
    } catch (reason) {
      if (reason instanceof Error) {
        setErrorMessage(reason.message || currentCopy.generalError);
      } else {
        setErrorMessage(currentCopy.generalError);
      }
    } finally {
      setMagicLinkSubmitting(false);
    }
  }

  const RoleTab = ({role, label}: {role: LoginRole; label: string}) => (
    <button
      type="button"
      onClick={() => updateRole(role)}
      className={`relative inline-flex items-center justify-center rounded-full px-5 py-2.5 text-sm font-semibold transition-all duration-300 ease-out ${
        activeRole === role
          ? 'text-white'
          : 'text-white/45 hover:text-white/75'
      }`}
    >
      {activeRole === role && (
        <span className="absolute inset-0 rounded-full bg-[#3b52f0] shadow-[0_2px_12px_rgba(59,82,240,0.35)] transition-all duration-300 ease-out" />
      )}
      <span className="relative z-10">{label}</span>
    </button>
  );

  return (
    <div className="container-shell py-12 md:py-16">
      <div className="grid auth-grid w-full gap-6">
        <section className="relative overflow-hidden rounded-[30px] border border-white/10 bg-[#07101d] p-8 shadow-[0_26px_100px_-40px_rgba(15,23,42,0.55)] sm:p-10">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(59,82,240,0.16),transparent_34%),radial-gradient(circle_at_bottom_right,rgba(59,82,240,0.10),transparent_32%)]" />
          <div className="relative space-y-7">
            <div className="inline-flex rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium tracking-[0.18em] text-white/70">
              {currentCopy.eyebrow}
            </div>

            <div className="max-w-xl space-y-3">
              <h1 className="text-4xl font-semibold leading-tight tracking-tight text-white sm:text-5xl">
                {currentCopy.title}
              </h1>
              <p className="text-base leading-7 text-white/62">{currentCopy.subtitle}</p>
            </div>

            <div className="space-y-5">
              {currentCopy.leftSteps.map((item, index) => (
                <div
                  key={item.title}
                  className="flex items-start gap-4 border-b border-white/8 pb-5 last:border-b-0 last:pb-0"
                >
                  <div className="flex size-8 shrink-0 items-center justify-center rounded-full border border-[#4b61ff]/35 text-sm font-semibold text-[#7f90ff]">
                    {index + 1}
                  </div>
                  <div>
                    <div className="text-base font-semibold text-white">{item.title}</div>
                    <div className="mt-1 text-sm leading-6 text-white/58">{item.description}</div>
                  </div>
                </div>
              ))}
            </div>

            <Link
              href={`/${locale}`}
              className="inline-flex text-sm font-medium text-[#8fa0ff] transition hover:text-white"
            >
              ← {currentCopy.backToHome}
            </Link>
          </div>
        </section>

        <section className="overflow-hidden rounded-[30px] border border-white/10 bg-[#101828] shadow-[0_26px_100px_-40px_rgba(15,23,42,0.55)]">
          <div className="flex items-center justify-between border-b border-white/8 px-6 py-5">
            <div className="flex gap-3">
              <span className="inline-flex rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-white">
                {currentCopy.tabs.login}
              </span>
              <Link
                href={`/${locale}/signup`}
                className="inline-flex rounded-xl border border-transparent px-4 py-2 text-sm font-medium text-white/55 transition hover:border-white/10 hover:bg-white/5 hover:text-white"
              >
                {currentCopy.tabs.signup}
              </Link>
            </div>
          </div>

          <div className="space-y-5 px-6 py-6">
            {/* ── Role tabs ── */}
            <div className="flex items-center justify-center">
              <div className="inline-flex items-center gap-1 rounded-full border border-white/8 bg-white/[0.03] p-1.5">
                <RoleTab role="candidate" label={currentCopy.roleTabs.candidate} />
                <RoleTab role="employer" label={currentCopy.roleTabs.employer} />
              </div>
            </div>

            {activeRole === 'candidate' ? (
              <>
                <a
                  href={`/api/user/auth/google/initiate?redirect_path=${encodeURIComponent(redirectTarget)}`}
                  className="inline-flex h-12 w-full items-center justify-center gap-3 rounded-2xl border border-white/12 bg-white/[0.04] px-5 text-sm font-semibold text-white transition hover:border-white/20 hover:bg-white/[0.08]"
                >
                  <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
                    <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
                    <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
                    <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
                    <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.18 1.48-4.97 2.31-8.16 2.31-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
                    <path fill="none" d="M0 0h48v48H0z"/>
                  </svg>
                  {currentCopy.googleButton}
                </a>

                <div className="relative py-1">
                  <div className="absolute inset-x-0 top-1/2 border-t border-white/8" />
                  <span className="relative inline-flex bg-[#101828] pr-4 text-xs font-semibold uppercase tracking-[0.12em] text-white/38">
                    {currentCopy.dividerOrEmail}
                  </span>
                </div>

                {magicLinkConsuming ? (
                  <div className="rounded-2xl border border-[#4b61ff]/20 bg-[#111d35] px-5 py-4">
                    <div className="text-base font-semibold text-white">
                      {currentCopy.magicLinkConsumingTitle}
                    </div>
                    <p className="mt-2 text-sm leading-7 text-white/68">
                      {currentCopy.magicLinkConsumingDescription}
                    </p>
                  </div>
                ) : null}

                {errorMessage ? (
                  <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
                    {errorMessage}
                  </div>
                ) : null}

                {magicLinkSuccess ? (
                  <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
                    {magicLinkSuccess}
                  </div>
                ) : null}

                <form className="space-y-4" onSubmit={handlePasswordSubmit}>
                  <div className="space-y-2">
                    <label
                      htmlFor="login-email"
                      className="text-xs font-semibold uppercase tracking-[0.12em] text-white/48"
                    >
                      {currentCopy.emailLabel}
                    </label>
                    <input
                      id="login-email"
                      type="email"
                      autoComplete="email"
                      value={passwordEmail}
                      onChange={(event) => {
                        setPasswordEmail(event.target.value);
                        setFieldErrors((previous) => ({...previous, passwordEmail: undefined}));
                      }}
                      placeholder={currentCopy.emailPlaceholder}
                      className={`h-14 w-full rounded-2xl border bg-[#111827] px-4 text-white outline-none transition ${
                        fieldErrors.passwordEmail
                          ? 'border-rose-400/80 bg-rose-500/10'
                          : 'border-white/10 focus:border-[#5b70ff]'
                      }`}
                    />
                    {fieldErrors.passwordEmail ? (
                      <div className="text-sm font-medium text-rose-300">
                        {fieldErrors.passwordEmail}
                      </div>
                    ) : null}
                  </div>

                  <div className="space-y-2">
                    <label
                      htmlFor="login-password"
                      className="text-xs font-semibold uppercase tracking-[0.12em] text-white/48"
                    >
                      {currentCopy.passwordLabel}
                    </label>
                    <input
                      id="login-password"
                      type="password"
                      autoComplete="current-password"
                      value={password}
                      onChange={(event) => {
                        setPassword(event.target.value);
                        setFieldErrors((previous) => ({...previous, password: undefined}));
                      }}
                      placeholder={currentCopy.passwordPlaceholder}
                      className={`h-14 w-full rounded-2xl border bg-[#111827] px-4 text-white outline-none transition ${
                        fieldErrors.password
                          ? 'border-rose-400/80 bg-rose-500/10'
                          : 'border-white/10 focus:border-[#5b70ff]'
                      }`}
                    />
                    {fieldErrors.password ? (
                      <div className="text-sm font-medium text-rose-300">{fieldErrors.password}</div>
                    ) : null}

                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm leading-6 text-white/48">{currentCopy.passwordHelp}</p>
                      <Link
                        href={`/${locale}/forgot-password`}
                        className="shrink-0 text-sm font-semibold text-[#8fa0ff] transition hover:text-white"
                      >
                        {currentCopy.forgotPassword}
                      </Link>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={passwordSubmitting}
                    className="inline-flex h-12 w-full items-center justify-center rounded-2xl border border-[#4b61ff] bg-[#3b52f0] px-6 text-sm font-semibold text-white transition hover:bg-[#3348da] disabled:opacity-60"
                  >
                    {passwordSubmitting ? currentCopy.submitLoading : currentCopy.submit}
                  </button>
                </form>

                <div className="space-y-4 rounded-[26px] border border-white/8 bg-white/[0.02] p-5">
                  <div>
                    <div className="text-lg font-semibold text-white">
                      {currentCopy.magicLinkTitle}
                    </div>
                    <p className="mt-2 text-sm leading-7 text-white/60">
                      {currentCopy.magicLinkDescription}
                    </p>
                  </div>

                  <div className="space-y-2">
                    <label
                      htmlFor="magic-link-email"
                      className="text-xs font-semibold uppercase tracking-[0.12em] text-white/48"
                    >
                      {currentCopy.emailLabel}
                    </label>
                    <input
                      id="magic-link-email"
                      type="email"
                      autoComplete="email"
                      value={magicLinkEmail}
                      onChange={(event) => {
                        setMagicLinkEmail(event.target.value);
                        setFieldErrors((previous) => ({...previous, magicLinkEmail: undefined}));
                      }}
                      placeholder={currentCopy.emailPlaceholder}
                      className={`h-14 w-full rounded-2xl border bg-[#111827] px-4 text-white outline-none transition ${
                        fieldErrors.magicLinkEmail
                          ? 'border-rose-400/80 bg-rose-500/10'
                          : 'border-white/10 focus:border-[#5b70ff]'
                      }`}
                    />
                    {fieldErrors.magicLinkEmail ? (
                      <div className="text-sm font-medium text-rose-300">
                        {fieldErrors.magicLinkEmail}
                      </div>
                    ) : null}
                    <p className="text-sm leading-6 text-white/45">
                      {currentCopy.magicLinkEmailHelp}
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => void handleMagicLink()}
                    disabled={magicLinkSubmitting}
                    className="inline-flex h-12 w-full items-center justify-center rounded-2xl border border-white/12 bg-transparent px-6 text-sm font-semibold text-white transition hover:bg-white/6 disabled:opacity-60"
                  >
                    {magicLinkSubmitting
                      ? currentCopy.magicLinkButtonLoading
                      : currentCopy.magicLinkButton}
                  </button>
                </div>
              </>
            ) : (
              <>
                {/* ── Employer login form ── */}
                <a
                  href={`/api/user/auth/google/initiate?redirect_path=${encodeURIComponent(`/${locale}/employer/dashboard`)}&role=employer`}
                  className="inline-flex h-12 w-full items-center justify-center gap-3 rounded-2xl border border-white/12 bg-white/[0.04] px-5 text-sm font-semibold text-white transition hover:border-white/20 hover:bg-white/[0.08]"
                >
                  <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
                    <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
                    <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
                    <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
                    <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.18 1.48-4.97 2.31-8.16 2.31-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
                    <path fill="none" d="M0 0h48v48H0z"/>
                  </svg>
                  {currentCopy.employer.googleButton}
                </a>

                <div className="relative py-1">
                  <div className="absolute inset-x-0 top-1/2 border-t border-white/8" />
                  <span className="relative inline-flex bg-[#101828] pr-4 text-xs font-semibold uppercase tracking-[0.12em] text-white/38">
                    {currentCopy.dividerOrEmail}
                  </span>
                </div>

                {errorMessage ? (
                  <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
                    {errorMessage}
                  </div>
                ) : null}

                <form className="space-y-4" onSubmit={handleEmployerSubmit}>
                  <div className="space-y-2">
                    <label
                      htmlFor="employer-email"
                      className="text-xs font-semibold uppercase tracking-[0.12em] text-white/48"
                    >
                      {currentCopy.employer.emailLabel}
                    </label>
                    <input
                      id="employer-email"
                      type="email"
                      autoComplete="email"
                      value={employerEmail}
                      onChange={(event) => {
                        setEmployerEmail(event.target.value);
                        setFieldErrors((previous) => ({...previous, employerEmail: undefined}));
                      }}
                      placeholder={currentCopy.employer.emailPlaceholder}
                      className={`h-14 w-full rounded-2xl border bg-[#111827] px-4 text-white outline-none transition ${
                        fieldErrors.employerEmail
                          ? 'border-rose-400/80 bg-rose-500/10'
                          : 'border-white/10 focus:border-[#5b70ff]'
                      }`}
                    />
                    {fieldErrors.employerEmail ? (
                      <div className="text-sm font-medium text-rose-300">
                        {fieldErrors.employerEmail}
                      </div>
                    ) : null}
                  </div>

                  <div className="space-y-2">
                    <label
                      htmlFor="employer-password"
                      className="text-xs font-semibold uppercase tracking-[0.12em] text-white/48"
                    >
                      {currentCopy.passwordLabel}
                    </label>
                    <input
                      id="employer-password"
                      type="password"
                      autoComplete="current-password"
                      value={employerPassword}
                      onChange={(event) => {
                        setEmployerPassword(event.target.value);
                        setFieldErrors((previous) => ({...previous, employerPassword: undefined}));
                      }}
                      placeholder={currentCopy.passwordPlaceholder}
                      className={`h-14 w-full rounded-2xl border bg-[#111827] px-4 text-white outline-none transition ${
                        fieldErrors.employerPassword
                          ? 'border-rose-400/80 bg-rose-500/10'
                          : 'border-white/10 focus:border-[#5b70ff]'
                      }`}
                    />
                    {fieldErrors.employerPassword ? (
                      <div className="text-sm font-medium text-rose-300">
                        {fieldErrors.employerPassword}
                      </div>
                    ) : null}

                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm leading-6 text-white/48">{currentCopy.employer.passwordHelp}</p>
                      <Link
                        href={`/${locale}/forgot-password?role=employer`}
                        className="shrink-0 text-sm font-semibold text-[#8fa0ff] transition hover:text-white"
                      >
                        {currentCopy.employer.forgotPassword}
                      </Link>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={employerSubmitting}
                    className="inline-flex h-12 w-full items-center justify-center rounded-2xl border border-[#4b61ff] bg-[#3b52f0] px-6 text-sm font-semibold text-white transition hover:bg-[#3348da] disabled:opacity-60"
                  >
                    {employerSubmitting ? currentCopy.employer.submitLoading : currentCopy.employer.submit}
                  </button>
                </form>
              </>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
