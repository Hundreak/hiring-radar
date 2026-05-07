'use client';

import Link from 'next/link';
import {useMemo, useState, useCallback} from 'react';
import {usePathname, useRouter, useSearchParams} from 'next/navigation';

import {ApiError, api} from '@/lib/api';
import type {SupportedLocale} from '@/types/user';

type Copy = {
  eyebrow: string;
  title: string;
  subtitle: string;
  panelTitle: string;
  panelSubtitle: string;
  fullNameLabel: string;
  fullNamePlaceholder: string;
  emailLabel: string;
  emailPlaceholder: string;
  passwordLabel: string;
  passwordPlaceholder: string;
  passwordConfirmationLabel: string;
  passwordConfirmationPlaceholder: string;
  requestCode: string;
  requestCodeLoading: string;
  verificationTitle: string;
  verificationSubtitle: string;
  verificationCodeLabel: string;
  verificationCodePlaceholder: string;
  verifyCode: string;
  verifyCodeLoading: string;
  resendCode: string;
  successTitle: string;
  successSubtitle: string;
  generalError: string;
  passwordMismatch: string;
  existingAccount: string;
  alreadyAccountText: string;
  loginLinkText: string;
  backToLogin: string;
  required: string;
  googleButton: string;
  dividerOrEmail: string;
  acceptTerms: string;
  termsLinkText: string;
  privacyLinkText: string;
  tabs: {
    login: string;
    signup: string;
  };
  roleTabs: {
    candidate: string;
    employer: string;
  };
  employer: {
    panelTitle: string;
    panelSubtitle: string;
    companyNameLabel: string;
    companyNamePlaceholder: string;
    companyEmailLabel: string;
    companyEmailPlaceholder: string;
    contactNameLabel: string;
    contactNamePlaceholder: string;
    passwordLabel: string;
    passwordPlaceholder: string;
    passwordConfirmationLabel: string;
    passwordConfirmationPlaceholder: string;
    submit: string;
    submitLoading: string;
    googleButton: string;
    dividerOrEmail: string;
    acceptTerms: string;
  };
  leftSteps: Array<{title: string; description: string}>;
  leftStepsEmployer: Array<{title: string; description: string}>;
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
    eyebrow: 'Kayıt ol',
    title: 'Hesabını profesyonel biçimde oluştur',
    subtitle:
      'Bilgilerini gir, e-postana gelen doğrulama kodunu onayla ve profil alanına güvenli şekilde geç.',
    panelTitle: 'Kayıt ol',
    panelSubtitle: 'Ücretsiz hesap oluştur, kariyer asistanına hemen başla.',
    fullNameLabel: 'Ad Soyad',
    fullNamePlaceholder: 'Adınızı ve soyadınızı giriniz',
    emailLabel: 'E-posta',
    emailPlaceholder: 'E-posta adresinizi giriniz',
    passwordLabel: 'Şifre',
    passwordPlaceholder: 'Güçlü bir şifre oluştur',
    passwordConfirmationLabel: 'Şifre Tekrar',
    passwordConfirmationPlaceholder: 'Şifrenizi yeniden giriniz',
    requestCode: 'Doğrulama kodu gönder',
    requestCodeLoading: 'Kod gönderiliyor...',
    verificationTitle: 'E-postanı doğrula',
    verificationSubtitle:
      'E-postana gönderdiğimiz doğrulama kodunu gir. Kod doğruysa kayıt tamamlanacak ve siteye yönlendirileceksin.',
    verificationCodeLabel: 'Doğrulama Kodu',
    verificationCodePlaceholder: '6 haneli doğrulama kodunu giriniz',
    verifyCode: 'Kaydı tamamla',
    verifyCodeLoading: 'Kayıt tamamlanıyor...',
    resendCode: 'Kodu yeniden gönder',
    successTitle: 'Kayıt başarıyla tamamlandı',
    successSubtitle:
      'Siteye yönlendiriliyorsunuz. Birkaç saniye içinde profil alanın açılacak.',
    generalError: 'İşlem şu anda tamamlanamadı. Lütfen tekrar dene.',
    passwordMismatch: 'Şifre tekrarı eşleşmiyor.',
    existingAccount: 'Bu e-posta sistemde kayıtlıdır. Lütfen giriş yap.',
    alreadyAccountText: 'Zaten hesabın var mı?',
    loginLinkText: 'Giriş yap',
    backToLogin: 'Giriş ekranına dön',
    required: 'Zorunlu',
    googleButton: 'Google ile kayıt ol',
    dividerOrEmail: 'veya e-posta ile kayıt ol',
    acceptTerms: 'Kullanım şartlarını ve gizlilik politikasını okudum, kabul ediyorum.',
    termsLinkText: 'Kullanım şartları',
    privacyLinkText: 'Gizlilik politikası',
    tabs: {
      login: 'Giriş Yap',
      signup: 'Kayıt Ol'
    },
    roleTabs: {
      candidate: 'Aday Kaydı',
      employer: 'İşveren Kaydı'
    },
    employer: {
      panelTitle: 'İşveren Kaydı',
      panelSubtitle: 'Şirket hesabı oluştur, ilan vermeye hemen başla.',
      companyNameLabel: 'Şirket Adı',
      companyNamePlaceholder: 'Şirket adını giriniz',
      companyEmailLabel: 'Şirket E-postası',
      companyEmailPlaceholder: 'Şirket e-posta adresinizi giriniz',
      contactNameLabel: 'Yetkili Adı',
      contactNamePlaceholder: 'Yetkili kişinin adını giriniz',
      passwordLabel: 'Şifre',
      passwordPlaceholder: 'Güçlü bir şifre oluştur',
      passwordConfirmationLabel: 'Şifre Tekrar',
      passwordConfirmationPlaceholder: 'Şifrenizi yeniden giriniz',
      submit: 'Hesap oluştur',
      submitLoading: 'Hesap oluşturuluyor...',
      googleButton: 'Google ile kayıt ol',
      dividerOrEmail: 'veya e-posta ile kayıt ol',
      acceptTerms: 'Kullanım şartlarını ve gizlilik politikasını okudum, kabul ediyorum.'
    },
    leftSteps: [
      {
        title: 'Bilgilerini gir',
        description: 'Ad, e-posta ve güçlü şifre bilgilerini eksiksiz doldur.'
      },
      {
        title: 'E-postanı doğrula',
        description: 'Gönderilen doğrulama kodu ile hesabını güvence altına al.'
      },
      {
        title: "CV'ni yükle",
        description: 'Sistem profilini otomatik doldurur, eşleşmeler başlar.'
      }
    ],
    leftStepsEmployer: [
      {
        title: 'Şirket bilgilerini gir',
        description: 'Şirket adı, e-posta ve yetkili kişi bilgilerini eksiksiz doldur.'
      },
      {
        title: 'E-postanı doğrula',
        description: 'Gönderilen doğrulama kodu ile şirket hesabını güvence altına al.'
      },
      {
        title: 'İlan vermeye başla',
        description: 'İş ilanlarını oluştur, adaylarla eşleşmeleri gör.'
      }
    ],
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
    eyebrow: 'Sign up',
    title: 'Create your account professionally',
    subtitle:
      'Enter your details, verify the code sent to your email and continue securely into your profile area.',
    panelTitle: 'Create account',
    panelSubtitle: 'Start instantly with a free account and your career assistant.',
    fullNameLabel: 'Full Name',
    fullNamePlaceholder: 'Enter your full name',
    emailLabel: 'Email',
    emailPlaceholder: 'Enter your email address',
    passwordLabel: 'Password',
    passwordPlaceholder: 'Create a strong password',
    passwordConfirmationLabel: 'Confirm Password',
    passwordConfirmationPlaceholder: 'Re-enter your password',
    requestCode: 'Send verification code',
    requestCodeLoading: 'Sending code...',
    verificationTitle: 'Verify your email',
    verificationSubtitle:
      'Enter the verification code sent to your email. When the code is correct, your account will be created and you will be redirected.',
    verificationCodeLabel: 'Verification Code',
    verificationCodePlaceholder: 'Enter the 6-digit verification code',
    verifyCode: 'Complete registration',
    verifyCodeLoading: 'Completing registration...',
    resendCode: 'Send code again',
    successTitle: 'Registration completed successfully',
    successSubtitle:
      'You are being redirected now. Your profile area will open in a moment.',
    generalError: 'We could not complete this step right now. Please try again.',
    passwordMismatch: 'Password confirmation does not match.',
    existingAccount: 'This email is already registered. Please sign in.',
    alreadyAccountText: 'Already have an account?',
    loginLinkText: 'Sign in',
    backToLogin: 'Back to sign in',
    required: 'Required',
    googleButton: 'Sign up with Google',
    dividerOrEmail: 'or sign up with email',
    acceptTerms: 'I have read and accept the terms of use and privacy policy.',
    termsLinkText: 'Terms of use',
    privacyLinkText: 'Privacy policy',
    tabs: {
      login: 'Sign In',
      signup: 'Sign Up'
    },
    roleTabs: {
      candidate: 'Candidate Signup',
      employer: 'Employer Signup'
    },
    employer: {
      panelTitle: 'Employer Registration',
      panelSubtitle: 'Create a company account and start posting jobs instantly.',
      companyNameLabel: 'Company Name',
      companyNamePlaceholder: 'Enter your company name',
      companyEmailLabel: 'Company Email',
      companyEmailPlaceholder: 'Enter your company email address',
      contactNameLabel: 'Contact Person Name',
      contactNamePlaceholder: 'Enter the contact person name',
      passwordLabel: 'Password',
      passwordPlaceholder: 'Create a strong password',
      passwordConfirmationLabel: 'Confirm Password',
      passwordConfirmationPlaceholder: 'Re-enter your password',
      submit: 'Create account',
      submitLoading: 'Creating account...',
      googleButton: 'Sign up with Google',
      dividerOrEmail: 'or sign up with email',
      acceptTerms: 'I have read and accept the terms of use and privacy policy.'
    },
    leftSteps: [
      {
        title: 'Enter your details',
        description: 'Provide your name, email address and a strong password.'
      },
      {
        title: 'Verify your email',
        description: 'Secure the account by entering the code sent to your inbox.'
      },
      {
        title: 'Upload your CV',
        description: 'The system starts shaping your profile and matching flow.'
      }
    ],
    leftStepsEmployer: [
      {
        title: 'Enter company details',
        description: 'Provide company name, email, and contact person details.'
      },
      {
        title: 'Verify your email',
        description: 'Secure the company account with the verification code.'
      },
      {
        title: 'Start posting jobs',
        description: 'Create job listings and view candidate matches.'
      }
    ],
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
    eyebrow: 'Registrieren',
    title: 'Erstelle dein Konto professionell',
    subtitle:
      'Gib deine Daten ein, bestätige den Code aus deiner E-Mail und wechsle sicher in deinen Profilbereich.',
    panelTitle: 'Registrieren',
    panelSubtitle: 'Erstelle kostenlos ein Konto und starte sofort mit deinem Karriereassistenten.',
    fullNameLabel: 'Vollständiger Name',
    fullNamePlaceholder: 'Gib deinen vollständigen Namen ein',
    emailLabel: 'E-Mail',
    emailPlaceholder: 'Gib deine E-Mail-Adresse ein',
    passwordLabel: 'Passwort',
    passwordPlaceholder: 'Erstelle ein sicheres Passwort',
    passwordConfirmationLabel: 'Passwort wiederholen',
    passwordConfirmationPlaceholder: 'Gib dein Passwort erneut ein',
    requestCode: 'Bestätigungscode senden',
    requestCodeLoading: 'Code wird gesendet...',
    verificationTitle: 'Bestätige deine E-Mail',
    verificationSubtitle:
      'Gib den Code aus deiner E-Mail ein. Bei korrektem Code wird dein Konto erstellt und du wirst weitergeleitet.',
    verificationCodeLabel: 'Bestätigungscode',
    verificationCodePlaceholder: '6-stelligen Bestätigungscode eingeben',
    verifyCode: 'Registrierung abschließen',
    verifyCodeLoading: 'Registrierung läuft...',
    resendCode: 'Code erneut senden',
    successTitle: 'Registrierung erfolgreich abgeschlossen',
    successSubtitle:
      'Du wirst jetzt weitergeleitet. Dein Profilbereich öffnet sich in einem Moment.',
    generalError:
      'Dieser Schritt konnte gerade nicht abgeschlossen werden. Bitte versuche es erneut.',
    passwordMismatch: 'Die Passwortbestätigung stimmt nicht überein.',
    existingAccount: 'Diese E-Mail-Adresse ist bereits registriert. Bitte melde dich an.',
    alreadyAccountText: 'Du hast schon ein Konto?',
    loginLinkText: 'Anmelden',
    backToLogin: 'Zur Anmeldung',
    required: 'Pflichtfeld',
    googleButton: 'Mit Google registrieren',
    dividerOrEmail: 'oder mit E-Mail registrieren',
    acceptTerms: 'Ich habe die Nutzungsbedingungen und die Datenschutzerklärung gelesen und akzeptiere sie.',
    termsLinkText: 'Nutzungsbedingungen',
    privacyLinkText: 'Datenschutzrichtlinie',
    tabs: {
      login: 'Anmelden',
      signup: 'Registrieren'
    },
    roleTabs: {
      candidate: 'Bewerber-Registrierung',
      employer: 'Arbeitgeber-Registrierung'
    },
    employer: {
      panelTitle: 'Arbeitgeber-Registrierung',
      panelSubtitle: 'Erstelle ein Unternehmenskonto und beginne sofort mit Stellenanzeigen.',
      companyNameLabel: 'Unternehmensname',
      companyNamePlaceholder: 'Gib deinen Unternehmensnamen ein',
      companyEmailLabel: 'Unternehmens-E-Mail',
      companyEmailPlaceholder: 'Gib die Unternehmens-E-Mail ein',
      contactNameLabel: 'Kontaktperson',
      contactNamePlaceholder: 'Gib den Namen der Kontaktperson ein',
      passwordLabel: 'Passwort',
      passwordPlaceholder: 'Erstelle ein sicheres Passwort',
      passwordConfirmationLabel: 'Passwort wiederholen',
      passwordConfirmationPlaceholder: 'Gib dein Passwort erneut ein',
      submit: 'Konto erstellen',
      submitLoading: 'Konto wird erstellt...',
      googleButton: 'Mit Google registrieren',
      dividerOrEmail: 'oder mit E-Mail registrieren',
      acceptTerms: 'Ich habe die Nutzungsbedingungen und die Datenschutzerklärung gelesen und akzeptiere sie.'
    },
    leftSteps: [
      {
        title: 'Daten eingeben',
        description: 'Name, E-Mail-Adresse und ein starkes Passwort angeben.'
      },
      {
        title: 'E-Mail bestätigen',
        description: 'Sichere dein Konto mit dem Bestätigungscode aus deinem Postfach.'
      },
      {
        title: 'Lebenslauf hochladen',
        description: 'Das System strukturiert dein Profil und startet das Matching.'
      }
    ],
    leftStepsEmployer: [
      {
        title: 'Unternehmensdaten eingeben',
        description: 'Unternehmensname, E-Mail und Kontaktperson angeben.'
      },
      {
        title: 'E-Mail bestätigen',
        description: 'Sichere das Unternehmenskonto mit dem Bestätigungscode.'
      },
      {
        title: 'Stellenanzeigen schalten',
        description: 'Erstelle Stellenanzeigen und sieh dir passende Bewerber an.'
      }
    ],
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

type FieldErrors = {
  fullName?: string;
  email?: string;
  password?: string;
  passwordConfirmation?: string;
  verificationCode?: string;
  acceptedTerms?: string;
  companyName?: string;
  companyEmail?: string;
  contactName?: string;
  employerPassword?: string;
  employerPasswordConfirmation?: string;
  employerAcceptedTerms?: string;
};

type SignupRole = 'candidate' | 'employer';

function resolveLocale(locale: string): SupportedLocale {
  if (locale === 'tr' || locale === 'en' || locale === 'de') return locale;
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

function getPasswordStrength(
  password: string,
  currentCopy: Copy
): {score: number; percentage: number; label: string; tone: string} {
  const checks = getPasswordChecks(password);
  const score = Object.values(checks).filter(Boolean).length;
  const percentage = (score / 5) * 100;

  if (score <= 2) {
    return {score, percentage, label: currentCopy.passwordStrengthWeak, tone: 'bg-rose-500'};
  }
  if (score <= 4) {
    return {score, percentage, label: currentCopy.passwordStrengthMedium, tone: 'bg-amber-500'};
  }
  return {score, percentage, label: currentCopy.passwordStrengthStrong, tone: 'bg-emerald-500'};
}

export function SignupView({locale}: {locale: string}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const safeLocale = useMemo(() => resolveLocale(locale), [locale]);
  const currentCopy = copy[safeLocale];

  /* ── role tab state ── */
  const roleFromUrl = searchParams.get('role');
  const initialRole: SignupRole = roleFromUrl === 'employer' ? 'employer' : 'candidate';
  const [activeRole, setActiveRole] = useState<SignupRole>(initialRole);

  const updateRole = useCallback(
    (newRole: SignupRole) => {
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
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirmation, setPasswordConfirmation] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [stage, setStage] = useState<'details' | 'verify' | 'success'>('details');
  const [submitting, setSubmitting] = useState(false);
  const [verifying, setVerifying] = useState(false);

  /* ── employer form state ── */
  const [companyName, setCompanyName] = useState('');
  const [companyEmail, setCompanyEmail] = useState('');
  const [contactName, setContactName] = useState('');
  const [employerPassword, setEmployerPassword] = useState('');
  const [employerPasswordConfirmation, setEmployerPasswordConfirmation] = useState('');
  const [employerAcceptedTerms, setEmployerAcceptedTerms] = useState(false);
  const [employerSubmitting, setEmployerSubmitting] = useState(false);

  const [infoMessage, setInfoMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  const passwordChecks = getPasswordChecks(password);
  const passwordStrength = getPasswordStrength(password, currentCopy);
  const strongPasswordReady = Object.values(passwordChecks).every(Boolean);

  const employerPasswordChecks = getPasswordChecks(employerPassword);
  const employerPasswordStrength = getPasswordStrength(employerPassword, currentCopy);
  const employerStrongPasswordReady = Object.values(employerPasswordChecks).every(Boolean);

  async function requestVerificationCode(event: React.FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setErrorMessage(null);
    setInfoMessage(null);

    const nextErrors: FieldErrors = {};
    if (!fullName.trim()) nextErrors.fullName = currentCopy.required;
    if (!email.trim()) nextErrors.email = currentCopy.required;
    if (!password) nextErrors.password = currentCopy.required;
    if (!passwordConfirmation) nextErrors.passwordConfirmation = currentCopy.required;
    if (!acceptedTerms) nextErrors.acceptedTerms = currentCopy.required;

    if (password && !strongPasswordReady) {
      nextErrors.password = currentCopy.passwordCriteriaTitle;
    }

    if (password && passwordConfirmation && password !== passwordConfirmation) {
      nextErrors.passwordConfirmation = currentCopy.passwordMismatch;
    }

    setFieldErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    setSubmitting(true);

    try {
      const response = await api.requestSignupVerification({
        full_name: fullName.trim(),
        email: email.trim(),
        password,
        password_confirmation: passwordConfirmation
      });

      setStage('verify');
      setInfoMessage(response.message);
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 409) {
        setErrorMessage(currentCopy.existingAccount);
      } else if (reason instanceof Error) {
        setErrorMessage(reason.message || currentCopy.generalError);
      } else {
        setErrorMessage(currentCopy.generalError);
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function verifyCode(event: React.FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setErrorMessage(null);
    setInfoMessage(null);

    const nextErrors: FieldErrors = {};
    if (!verificationCode.trim()) nextErrors.verificationCode = currentCopy.required;

    setFieldErrors((previous) => ({...previous, ...nextErrors}));
    if (Object.keys(nextErrors).length > 0) return;

    setVerifying(true);

    try {
      const response = await api.confirmSignupVerification({
        email: email.trim(),
        verification_code: verificationCode.trim()
      });

      setStage('success');
      setInfoMessage(response.message);
      router.refresh();

      window.setTimeout(() => {
        router.push(`/${safeLocale}/settings/profile`);
      }, 1000);
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 409) {
        setErrorMessage(currentCopy.existingAccount);
      } else if (reason instanceof Error) {
        setErrorMessage(reason.message || currentCopy.generalError);
      } else {
        setErrorMessage(currentCopy.generalError);
      }
    } finally {
      setVerifying(false);
    }
  }

  async function handleEmployerSignup(event: React.FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setErrorMessage(null);
    setInfoMessage(null);

    const nextErrors: FieldErrors = {};
    if (!companyName.trim()) nextErrors.companyName = currentCopy.required;
    if (!companyEmail.trim()) nextErrors.companyEmail = currentCopy.required;
    if (!contactName.trim()) nextErrors.contactName = currentCopy.required;
    if (!employerPassword) nextErrors.employerPassword = currentCopy.required;
    if (!employerPasswordConfirmation) nextErrors.employerPasswordConfirmation = currentCopy.required;
    if (!employerAcceptedTerms) nextErrors.employerAcceptedTerms = currentCopy.required;

    if (employerPassword && !employerStrongPasswordReady) {
      nextErrors.employerPassword = currentCopy.passwordCriteriaTitle;
    }

    if (
      employerPassword &&
      employerPasswordConfirmation &&
      employerPassword !== employerPasswordConfirmation
    ) {
      nextErrors.employerPasswordConfirmation = currentCopy.passwordMismatch;
    }

    setFieldErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    setEmployerSubmitting(true);

    try {
      await api.registerEmployer({
        company_name: companyName.trim(),
        company_email: companyEmail.trim(),
        contact_name: contactName.trim(),
        password: employerPassword,
        password_confirmation: employerPasswordConfirmation
      });

      router.push(`/${safeLocale}/employer/dashboard`);
      router.refresh();
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 409) {
        setErrorMessage(currentCopy.existingAccount);
      } else if (reason instanceof Error) {
        setErrorMessage(reason.message || currentCopy.generalError);
      } else {
        setErrorMessage(currentCopy.generalError);
      }
    } finally {
      setEmployerSubmitting(false);
    }
  }

  const RoleTab = ({role, label}: {role: SignupRole; label: string}) => (
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

  const currentLeftSteps =
    activeRole === 'employer' ? currentCopy.leftStepsEmployer : currentCopy.leftSteps;

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
              {currentLeftSteps.map((item, index) => (
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
              href={`/${safeLocale}/login`}
              className="inline-flex text-sm font-medium text-[#8fa0ff] transition hover:text-white"
            >
              ← {currentCopy.backToLogin}
            </Link>
          </div>
        </section>

        <section className="overflow-hidden rounded-[30px] border border-white/10 bg-[#101828] shadow-[0_26px_100px_-40px_rgba(15,23,42,0.55)]">
          <div className="flex items-center justify-between border-b border-white/8 px-6 py-5">
            <div className="flex gap-3">
              <Link
                href={`/${safeLocale}/login`}
                className="inline-flex rounded-xl border border-transparent px-4 py-2 text-sm font-medium text-white/55 transition hover:border-white/10 hover:bg-white/5 hover:text-white"
              >
                {currentCopy.tabs.login}
              </Link>
              <span className="inline-flex rounded-xl border border-white/10 bg-[#3b52f0] px-4 py-2 text-sm font-medium text-white">
                {currentCopy.tabs.signup}
              </span>
            </div>
          </div>

          <div className="px-6 py-6">
            {/* ── Role tabs ── */}
            <div className="mb-6 flex items-center justify-center">
              <div className="inline-flex items-center gap-1 rounded-full border border-white/8 bg-white/[0.03] p-1.5">
                <RoleTab role="candidate" label={currentCopy.roleTabs.candidate} />
                <RoleTab role="employer" label={currentCopy.roleTabs.employer} />
              </div>
            </div>

            {activeRole === 'candidate' ? (
              <>
                {stage === 'success' ? (
                  <div className="flex min-h-[560px] flex-col items-center justify-center text-center">
                    <div className="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-300">
                      <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        className="h-7 w-7"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 12.5l4.2 4.2L19 7" />
                      </svg>
                    </div>
                    <h2 className="mt-6 text-2xl font-semibold tracking-tight text-white">
                      {currentCopy.successTitle}
                    </h2>
                    <p className="mt-3 max-w-md text-sm leading-7 text-white/62">
                      {infoMessage || currentCopy.successSubtitle}
                    </p>
                  </div>
                ) : stage === 'verify' ? (
                  <form className="space-y-5" onSubmit={(event) => void verifyCode(event)}>
                    <div className="space-y-2">
                      <h2 className="text-2xl font-semibold tracking-tight text-white">
                        {currentCopy.verificationTitle}
                      </h2>
                      <p className="text-sm leading-7 text-white/62">
                        {currentCopy.verificationSubtitle}
                      </p>
                    </div>

                    {errorMessage ? (
                      <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
                        {errorMessage}
                      </div>
                    ) : null}

                    {infoMessage ? (
                      <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
                        {infoMessage}
                      </div>
                    ) : null}

                    <div className="space-y-2">
                      <label
                        htmlFor="signup-verification-code"
                        className="text-xs font-semibold uppercase tracking-[0.12em] text-white/48"
                      >
                        {currentCopy.verificationCodeLabel}
                      </label>
                      <input
                        id="signup-verification-code"
                        type="text"
                        inputMode="numeric"
                        autoComplete="one-time-code"
                        value={verificationCode}
                        onChange={(event) => {
                          setVerificationCode(event.target.value);
                          setFieldErrors((previous) => ({...previous, verificationCode: undefined}));
                        }}
                        placeholder={currentCopy.verificationCodePlaceholder}
                        className={`h-14 w-full rounded-2xl border bg-[#111827] px-4 text-white outline-none transition ${
                          fieldErrors.verificationCode
                            ? 'border-rose-400/80 bg-rose-500/10'
                            : 'border-white/10 focus:border-[#5b70ff]'
                        }`}
                      />
                      {fieldErrors.verificationCode ? (
                        <div className="text-sm font-medium text-rose-300">
                          {fieldErrors.verificationCode}
                        </div>
                      ) : null}
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2">
                      <button
                        type="submit"
                        disabled={verifying}
                        className="inline-flex h-12 items-center justify-center rounded-2xl border border-[#4b61ff] bg-[#3b52f0] px-6 text-sm font-semibold text-white transition hover:bg-[#3348da] disabled:opacity-60"
                      >
                        {verifying ? currentCopy.verifyCodeLoading : currentCopy.verifyCode}
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setStage('details');
                          setInfoMessage(null);
                          setErrorMessage(null);
                        }}
                        className="inline-flex h-12 items-center justify-center rounded-2xl border border-white/12 bg-transparent px-6 text-sm font-semibold text-white transition hover:bg-white/6"
                      >
                        {currentCopy.resendCode}
                      </button>
                    </div>
                  </form>
                ) : (
                  <form className="space-y-5" onSubmit={(event) => void requestVerificationCode(event)}>
                    <div className="space-y-2">
                      <h2 className="text-2xl font-semibold tracking-tight text-white">
                        {currentCopy.panelTitle}
                      </h2>
                      <p className="text-sm leading-7 text-white/62">{currentCopy.panelSubtitle}</p>
                    </div>

                    <a
                      href={`/api/user/auth/google/initiate?redirect_path=${encodeURIComponent('/tr/settings/profile')}`}
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

                    {errorMessage ? (
                      <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
                        {errorMessage}
                      </div>
                    ) : null}

                    <div className="space-y-2">
                      <label
                        htmlFor="signup-full-name"
                        className="text-xs font-semibold uppercase tracking-[0.12em] text-white/48"
                      >
                        {currentCopy.fullNameLabel}
                      </label>
                      <input
                        id="signup-full-name"
                        type="text"
                        autoComplete="name"
                        value={fullName}
                        onChange={(event) => {
                          setFullName(event.target.value);
                          setFieldErrors((previous) => ({...previous, fullName: undefined}));
                        }}
                        placeholder={currentCopy.fullNamePlaceholder}
                        className={`h-14 w-full rounded-2xl border bg-[#111827] px-4 text-white outline-none transition ${
                          fieldErrors.fullName
                            ? 'border-rose-400/80 bg-rose-500/10'
                            : 'border-white/10 focus:border-[#5b70ff]'
                        }`}
                      />
                      {fieldErrors.fullName ? (
                        <div className="text-sm font-medium text-rose-300">{fieldErrors.fullName}</div>
                      ) : null}
                    </div>

                    <div className="space-y-2">
                      <label
                        htmlFor="signup-email"
                        className="text-xs font-semibold uppercase tracking-[0.12em] text-white/48"
                      >
                        {currentCopy.emailLabel}
                      </label>
                      <input
                        id="signup-email"
                        type="email"
                        autoComplete="email"
                        value={email}
                        onChange={(event) => {
                          setEmail(event.target.value);
                          setFieldErrors((previous) => ({...previous, email: undefined}));
                        }}
                        placeholder={currentCopy.emailPlaceholder}
                        className={`h-14 w-full rounded-2xl border bg-[#111827] px-4 text-white outline-none transition ${
                          fieldErrors.email
                            ? 'border-rose-400/80 bg-rose-500/10'
                            : 'border-white/10 focus:border-[#5b70ff]'
                        }`}
                      />
                      {fieldErrors.email ? (
                        <div className="text-sm font-medium text-rose-300">{fieldErrors.email}</div>
                      ) : null}
                    </div>

                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <label
                          htmlFor="signup-password"
                          className="text-xs font-semibold uppercase tracking-[0.12em] text-white/48"
                        >
                          {currentCopy.passwordLabel}
                        </label>
                        <input
                          id="signup-password"
                          type="password"
                          autoComplete="new-password"
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
                      </div>

                      <div className="space-y-2">
                        <label
                          htmlFor="signup-password-confirmation"
                          className="text-xs font-semibold uppercase tracking-[0.12em] text-white/48"
                        >
                          {currentCopy.passwordConfirmationLabel}
                        </label>
                        <input
                          id="signup-password-confirmation"
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
                          className={`h-14 w-full rounded-2xl border bg-[#111827] px-4 text-white outline-none transition ${
                            fieldErrors.passwordConfirmation
                              ? 'border-rose-400/80 bg-rose-500/10'
                              : 'border-white/10 focus:border-[#5b70ff]'
                          }`}
                        />
                        {fieldErrors.passwordConfirmation ? (
                          <div className="text-sm font-medium text-rose-300">
                            {fieldErrors.passwordConfirmation}
                          </div>
                        ) : null}
                      </div>
                    </div>

                    <div className="rounded-[22px] border border-white/8 bg-white/[0.02] p-4">
                      <div className="mb-3 flex items-center justify-between gap-4">
                        <div className="text-sm font-semibold text-white">
                          {currentCopy.passwordCriteriaTitle}
                        </div>
                        <div className="text-sm font-medium text-white/55">
                          {passwordStrength.label}
                        </div>
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

                    <label className="flex items-start gap-3 rounded-[20px] border border-white/8 bg-white/[0.02] p-4">
                      <input
                        type="checkbox"
                        checked={acceptedTerms}
                        onChange={(event) => {
                          setAcceptedTerms(event.target.checked);
                          setFieldErrors((previous) => ({...previous, acceptedTerms: undefined}));
                        }}
                        className="mt-1 size-4 rounded border-white/20 bg-[#111827] text-[#3b52f0]"
                      />
                      <span className="text-sm leading-7 text-white/70">
                        <span>{currentCopy.acceptTerms} </span>
                        <Link
                          href={`/${safeLocale}/terms`}
                          className="font-medium text-[#8fa0ff] hover:text-white"
                        >
                          {currentCopy.termsLinkText}
                        </Link>
                        {' · '}
                        <Link
                          href={`/${safeLocale}/privacy`}
                          className="font-medium text-[#8fa0ff] hover:text-white"
                        >
                          {currentCopy.privacyLinkText}
                        </Link>
                      </span>
                    </label>

                    {fieldErrors.acceptedTerms ? (
                      <div className="text-sm font-medium text-rose-300">
                        {fieldErrors.acceptedTerms}
                      </div>
                    ) : null}

                    <button
                      type="submit"
                      disabled={submitting}
                      className="inline-flex h-12 w-full items-center justify-center rounded-2xl border border-[#4b61ff] bg-transparent px-6 text-sm font-semibold text-white transition hover:bg-white/6 disabled:opacity-60"
                    >
                      {submitting ? currentCopy.requestCodeLoading : currentCopy.requestCode}
                    </button>

                    <div className="text-center text-sm text-white/48">
                      {currentCopy.alreadyAccountText}{' '}
                      <Link
                        href={`/${safeLocale}/login`}
                        className="font-medium text-[#8fa0ff] hover:text-white"
                      >
                        {currentCopy.loginLinkText}
                      </Link>
                    </div>
                  </form>
                )}
              </>
            ) : (
              <>
                {/* ── Employer signup form ── */}
                <form className="space-y-5" onSubmit={(event) => void handleEmployerSignup(event)}>
                  <div className="space-y-2">
                    <h2 className="text-2xl font-semibold tracking-tight text-white">
                      {currentCopy.employer.panelTitle}
                    </h2>
                    <p className="text-sm leading-7 text-white/62">
                      {currentCopy.employer.panelSubtitle}
                    </p>
                  </div>

                  <a
                    href={`/api/user/auth/google/initiate?redirect_path=${encodeURIComponent(`/${safeLocale}/employer/dashboard`)}&role=employer`}
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
                      {currentCopy.employer.dividerOrEmail}
                    </span>
                  </div>

                  {errorMessage ? (
                    <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
                      {errorMessage}
                    </div>
                  ) : null}

                  <div className="space-y-2">
                    <label
                      htmlFor="employer-company-name"
                      className="text-xs font-semibold uppercase tracking-[0.12em] text-white/48"
                    >
                      {currentCopy.employer.companyNameLabel}
                    </label>
                    <input
                      id="employer-company-name"
                      type="text"
                      autoComplete="organization"
                      value={companyName}
                      onChange={(event) => {
                        setCompanyName(event.target.value);
                        setFieldErrors((previous) => ({...previous, companyName: undefined}));
                      }}
                      placeholder={currentCopy.employer.companyNamePlaceholder}
                      className={`h-14 w-full rounded-2xl border bg-[#111827] px-4 text-white outline-none transition ${
                        fieldErrors.companyName
                          ? 'border-rose-400/80 bg-rose-500/10'
                          : 'border-white/10 focus:border-[#5b70ff]'
                      }`}
                    />
                    {fieldErrors.companyName ? (
                      <div className="text-sm font-medium text-rose-300">
                        {fieldErrors.companyName}
                      </div>
                    ) : null}
                  </div>

                  <div className="space-y-2">
                    <label
                      htmlFor="employer-company-email"
                      className="text-xs font-semibold uppercase tracking-[0.12em] text-white/48"
                    >
                      {currentCopy.employer.companyEmailLabel}
                    </label>
                    <input
                      id="employer-company-email"
                      type="email"
                      autoComplete="email"
                      value={companyEmail}
                      onChange={(event) => {
                        setCompanyEmail(event.target.value);
                        setFieldErrors((previous) => ({...previous, companyEmail: undefined}));
                      }}
                      placeholder={currentCopy.employer.companyEmailPlaceholder}
                      className={`h-14 w-full rounded-2xl border bg-[#111827] px-4 text-white outline-none transition ${
                        fieldErrors.companyEmail
                          ? 'border-rose-400/80 bg-rose-500/10'
                          : 'border-white/10 focus:border-[#5b70ff]'
                      }`}
                    />
                    {fieldErrors.companyEmail ? (
                      <div className="text-sm font-medium text-rose-300">
                        {fieldErrors.companyEmail}
                      </div>
                    ) : null}
                  </div>

                  <div className="space-y-2">
                    <label
                      htmlFor="employer-contact-name"
                      className="text-xs font-semibold uppercase tracking-[0.12em] text-white/48"
                    >
                      {currentCopy.employer.contactNameLabel}
                    </label>
                    <input
                      id="employer-contact-name"
                      type="text"
                      autoComplete="name"
                      value={contactName}
                      onChange={(event) => {
                        setContactName(event.target.value);
                        setFieldErrors((previous) => ({...previous, contactName: undefined}));
                      }}
                      placeholder={currentCopy.employer.contactNamePlaceholder}
                      className={`h-14 w-full rounded-2xl border bg-[#111827] px-4 text-white outline-none transition ${
                        fieldErrors.contactName
                          ? 'border-rose-400/80 bg-rose-500/10'
                          : 'border-white/10 focus:border-[#5b70ff]'
                      }`}
                    />
                    {fieldErrors.contactName ? (
                      <div className="text-sm font-medium text-rose-300">
                        {fieldErrors.contactName}
                      </div>
                    ) : null}
                  </div>

                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <label
                        htmlFor="employer-password"
                        className="text-xs font-semibold uppercase tracking-[0.12em] text-white/48"
                      >
                        {currentCopy.employer.passwordLabel}
                      </label>
                      <input
                        id="employer-password"
                        type="password"
                        autoComplete="new-password"
                        value={employerPassword}
                        onChange={(event) => {
                          setEmployerPassword(event.target.value);
                          setFieldErrors((previous) => ({...previous, employerPassword: undefined}));
                        }}
                        placeholder={currentCopy.employer.passwordPlaceholder}
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
                    </div>

                    <div className="space-y-2">
                      <label
                        htmlFor="employer-password-confirmation"
                        className="text-xs font-semibold uppercase tracking-[0.12em] text-white/48"
                      >
                        {currentCopy.employer.passwordConfirmationLabel}
                      </label>
                      <input
                        id="employer-password-confirmation"
                        type="password"
                        autoComplete="new-password"
                        value={employerPasswordConfirmation}
                        onChange={(event) => {
                          setEmployerPasswordConfirmation(event.target.value);
                          setFieldErrors((previous) => ({
                            ...previous,
                            employerPasswordConfirmation: undefined
                          }));
                        }}
                        placeholder={currentCopy.employer.passwordConfirmationPlaceholder}
                        className={`h-14 w-full rounded-2xl border bg-[#111827] px-4 text-white outline-none transition ${
                          fieldErrors.employerPasswordConfirmation
                            ? 'border-rose-400/80 bg-rose-500/10'
                            : 'border-white/10 focus:border-[#5b70ff]'
                        }`}
                      />
                      {fieldErrors.employerPasswordConfirmation ? (
                        <div className="text-sm font-medium text-rose-300">
                          {fieldErrors.employerPasswordConfirmation}
                        </div>
                      ) : null}
                    </div>
                  </div>

                  <div className="rounded-[22px] border border-white/8 bg-white/[0.02] p-4">
                    <div className="mb-3 flex items-center justify-between gap-4">
                      <div className="text-sm font-semibold text-white">
                        {currentCopy.passwordCriteriaTitle}
                      </div>
                      <div className="text-sm font-medium text-white/55">
                        {employerPasswordStrength.label}
                      </div>
                    </div>

                    <div className="h-2 rounded-full bg-white/8">
                      <div
                        className={`h-2 rounded-full ${employerPasswordStrength.tone}`}
                        style={{width: `${employerPasswordStrength.percentage}%`}}
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
                        const passed = employerPasswordChecks[key as keyof typeof employerPasswordChecks];
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

                  <label className="flex items-start gap-3 rounded-[20px] border border-white/8 bg-white/[0.02] p-4">
                    <input
                      type="checkbox"
                      checked={employerAcceptedTerms}
                      onChange={(event) => {
                        setEmployerAcceptedTerms(event.target.checked);
                        setFieldErrors((previous) => ({...previous, employerAcceptedTerms: undefined}));
                      }}
                      className="mt-1 size-4 rounded border-white/20 bg-[#111827] text-[#3b52f0]"
                    />
                    <span className="text-sm leading-7 text-white/70">
                      <span>{currentCopy.employer.acceptTerms} </span>
                      <Link
                        href={`/${safeLocale}/terms`}
                        className="font-medium text-[#8fa0ff] hover:text-white"
                      >
                        {currentCopy.termsLinkText}
                      </Link>
                      {' · '}
                      <Link
                        href={`/${safeLocale}/privacy`}
                        className="font-medium text-[#8fa0ff] hover:text-white"
                      >
                        {currentCopy.privacyLinkText}
                      </Link>
                    </span>
                  </label>

                  {fieldErrors.employerAcceptedTerms ? (
                    <div className="text-sm font-medium text-rose-300">
                      {fieldErrors.employerAcceptedTerms}
                    </div>
                  ) : null}

                  <button
                    type="submit"
                    disabled={employerSubmitting}
                    className="inline-flex h-12 w-full items-center justify-center rounded-2xl border border-[#4b61ff] bg-[#3b52f0] px-6 text-sm font-semibold text-white transition hover:bg-[#3348da] disabled:opacity-60"
                  >
                    {employerSubmitting ? currentCopy.employer.submitLoading : currentCopy.employer.submit}
                  </button>

                  <div className="text-center text-sm text-white/48">
                    {currentCopy.alreadyAccountText}{' '}
                    <Link
                      href={`/${safeLocale}/login?role=employer`}
                      className="font-medium text-[#8fa0ff] hover:text-white"
                    >
                      {currentCopy.loginLinkText}
                    </Link>
                  </div>
                </form>
              </>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
