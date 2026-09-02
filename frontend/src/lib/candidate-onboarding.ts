import type {ProfileCompletionSection, UserProfileAggregateResponse} from '@/types/profile';

export type CandidateOnboardingStepKey =
  | 'cv'
  | 'basics'
  | 'preferences'
  | 'skills'
  | 'experience'
  | 'saved'
  | 'review';

export type CandidateOnboardingStepStatus = 'done' | 'current' | 'todo';

export type CandidateOnboardingStep = {
  key: CandidateOnboardingStepKey;
  title: string;
  description: string;
  href: string;
  status: CandidateOnboardingStepStatus;
};

export type CandidateOnboardingAction = {
  title: string;
  description: string;
  cta: string;
  href: string;
};

export type CandidateOnboardingModel = {
  title: string;
  description: string;
  progressPercent: number;
  progressLabel: string;
  nextAction: CandidateOnboardingAction;
  steps: CandidateOnboardingStep[];
};

type Copy = {
  eyebrow: string;
  progressLabel: string;
  dismissLabel: string;
  readyTitle: string;
  activeTitle: string;
  readyDescription: string;
  activeDescription: string;
  doneTemplate: string;
  steps: Record<CandidateOnboardingStepKey, Omit<CandidateOnboardingStep, 'status'>>;
  actions: Record<CandidateOnboardingStepKey, CandidateOnboardingAction>;
};

const copies: Record<'tr' | 'en' | 'de', Copy> = {
  tr: {
    eyebrow: 'Aday başlangıç akışı',
    progressLabel: 'Hazırlık skoru',
    dismissLabel: 'Bugün gizle',
    readyTitle: 'Başvuru merkezi hazır görünüyor',
    activeTitle: 'Profilini eşleşme motoru için güçlendirelim',
    readyDescription: 'Temel hazırlıklar tamam. Artık eşleşmeleri inceleyip kaydettiğin ilanları başvuru hattına taşıyabilirsin.',
    activeDescription: 'En iyi eşleşmeleri almak için önce CV, profil sinyalleri ve ilk kaydedilen ilan adımlarını tamamla.',
    doneTemplate: '{done}/{total} adım tamamlandı',
    steps: {
      cv: {
        key: 'cv',
        title: 'CV yükle',
        description: 'CV parser profil alanlarını ve AI önerilerini besler.',
        href: '/settings/profile',
      },
      basics: {
        key: 'basics',
        title: 'Özet & başlık',
        description: 'Başlık ve kısa özet profilin ilk kalite sinyalidir.',
        href: '/settings/profile',
      },
      preferences: {
        key: 'preferences',
        title: 'Hedef roller',
        description: 'Hedef rol ve çalışma tercihleri eşleşme kalitesini belirler.',
        href: '/settings/profile',
      },
      skills: {
        key: 'skills',
        title: 'Beceriler',
        description: 'Beceriler iş ilanı açıklamalarıyla doğrudan eşleştirilir.',
        href: '/settings/profile',
      },
      experience: {
        key: 'experience',
        title: 'Deneyim',
        description: 'En az bir deneyim kaydı güven ve seviye sinyali verir.',
        href: '/settings/profile',
      },
      saved: {
        key: 'saved',
        title: 'İlk ilanı kaydet',
        description: 'Kaydedilen ilanlar başvuru pipeline’ını başlatır.',
        href: '/jobs',
      },
      review: {
        key: 'review',
        title: 'Eşleşmeleri incele',
        description: 'Profil hazır olduğunda en alakalı işleri karşılaştır.',
        href: '/matches',
      },
    },
    actions: {
      cv: {
        title: 'Önce CV ile profili besle',
        description: 'CV yüklemek başlık, deneyim, eğitim ve beceri alanlarını hızlıca doldurmanın en güvenli yolu.',
        cta: 'CV alanına git',
        href: '/settings/profile',
      },
      basics: {
        title: 'Başlık ve kısa özeti netleştir',
        description: 'AI eşleşme motoru profilini yorumlarken ilk olarak bu iki alanı okur.',
        cta: 'Profili tamamla',
        href: '/settings/profile',
      },
      preferences: {
        title: 'Hedef rolünü ve çalışma şeklini seç',
        description: 'Hedef roller olmadan eşleşmeler geniş kalır; net tercihler daha güçlü öneri üretir.',
        cta: 'Tercihleri aç',
        href: '/settings/profile',
      },
      skills: {
        title: 'Becerilerini görünür hale getir',
        description: 'En az 5 güçlü beceri eklemek match skorlarının açıklanabilirliğini artırır.',
        cta: 'Beceri ekle',
        href: '/settings/profile',
      },
      experience: {
        title: 'Deneyim sinyalini ekle',
        description: 'Bir deneyim kaydı bile seviye, sektör ve rol bağlamını ciddi biçimde netleştirir.',
        cta: 'Deneyim ekle',
        href: '/settings/profile',
      },
      saved: {
        title: 'İlk uygun ilanı kaydet',
        description: 'Kaydettiğin ilanlar sonra başvuru, görüşme ve not akışına taşınabilir.',
        cta: 'İlanları tara',
        href: '/jobs',
      },
      review: {
        title: 'Eşleşmeleri karşılaştır',
        description: 'Hazır profil ile match skorlarını, eksik becerileri ve güçlü yönleri birlikte incele.',
        cta: 'Eşleşmelere git',
        href: '/matches',
      },
    },
  },
  en: {
    eyebrow: 'Candidate launch flow',
    progressLabel: 'Readiness score',
    dismissLabel: 'Hide for today',
    readyTitle: 'Your application cockpit is ready',
    activeTitle: 'Let’s strengthen your profile for the matching engine',
    readyDescription: 'The core setup is done. You can now review matches and move saved jobs into the application pipeline.',
    activeDescription: 'Complete CV, profile signals, and your first saved job to unlock higher-quality recommendations.',
    doneTemplate: '{done}/{total} steps complete',
    steps: {
      cv: {
        key: 'cv',
        title: 'Upload CV',
        description: 'The CV parser powers profile fields and AI suggestions.',
        href: '/settings/profile',
      },
      basics: {
        key: 'basics',
        title: 'Headline & summary',
        description: 'Headline and summary are the first profile quality signals.',
        href: '/settings/profile',
      },
      preferences: {
        key: 'preferences',
        title: 'Target roles',
        description: 'Role and work preferences tune match quality.',
        href: '/settings/profile',
      },
      skills: {
        key: 'skills',
        title: 'Skills',
        description: 'Skills are matched directly against job descriptions.',
        href: '/settings/profile',
      },
      experience: {
        key: 'experience',
        title: 'Experience',
        description: 'At least one experience adds trust and seniority signals.',
        href: '/settings/profile',
      },
      saved: {
        key: 'saved',
        title: 'Save first job',
        description: 'Saved jobs start the application pipeline.',
        href: '/jobs',
      },
      review: {
        key: 'review',
        title: 'Review matches',
        description: 'Compare the most relevant roles once your profile is ready.',
        href: '/matches',
      },
    },
    actions: {
      cv: {
        title: 'Start by feeding the profile with a CV',
        description: 'Uploading a CV is the fastest safe path to fill headline, experience, education, and skills.',
        cta: 'Go to CV area',
        href: '/settings/profile',
      },
      basics: {
        title: 'Clarify headline and summary',
        description: 'The matching engine reads these fields first when interpreting your profile.',
        cta: 'Complete profile',
        href: '/settings/profile',
      },
      preferences: {
        title: 'Pick target roles and work style',
        description: 'Without target roles, recommendations stay broad; clear preferences sharpen matches.',
        cta: 'Open preferences',
        href: '/settings/profile',
      },
      skills: {
        title: 'Make your skills visible',
        description: 'At least five strong skills improve explainability for match scores.',
        cta: 'Add skills',
        href: '/settings/profile',
      },
      experience: {
        title: 'Add experience signals',
        description: 'Even one experience entry clarifies level, industry, and role context.',
        cta: 'Add experience',
        href: '/settings/profile',
      },
      saved: {
        title: 'Save the first relevant job',
        description: 'Saved jobs can later move through application, interview, and note workflows.',
        cta: 'Browse jobs',
        href: '/jobs',
      },
      review: {
        title: 'Compare your matches',
        description: 'With a ready profile, review match scores, gaps, and strengths together.',
        cta: 'Open matches',
        href: '/matches',
      },
    },
  },
  de: {
    eyebrow: 'Kandidaten-Startflow',
    progressLabel: 'Bereitschaftsscore',
    dismissLabel: 'Heute ausblenden',
    readyTitle: 'Dein Bewerbungs-Cockpit ist bereit',
    activeTitle: 'Stärken wir dein Profil für die Matching-Engine',
    readyDescription: 'Die wichtigsten Schritte sind erledigt. Du kannst Matches prüfen und gespeicherte Jobs in die Bewerbungspipeline übernehmen.',
    activeDescription: 'Schließe CV, Profilsignale und den ersten gespeicherten Job ab, um bessere Empfehlungen zu erhalten.',
    doneTemplate: '{done}/{total} Schritte erledigt',
    steps: {
      cv: {
        key: 'cv',
        title: 'CV hochladen',
        description: 'Der CV-Parser speist Profilfelder und KI-Vorschläge.',
        href: '/settings/profile',
      },
      basics: {
        key: 'basics',
        title: 'Titel & Kurzprofil',
        description: 'Titel und Kurzprofil sind die ersten Qualitätssignale.',
        href: '/settings/profile',
      },
      preferences: {
        key: 'preferences',
        title: 'Zielrollen',
        description: 'Rollen- und Arbeitspräferenzen steuern die Match-Qualität.',
        href: '/settings/profile',
      },
      skills: {
        key: 'skills',
        title: 'Skills',
        description: 'Skills werden direkt mit Stellenbeschreibungen abgeglichen.',
        href: '/settings/profile',
      },
      experience: {
        key: 'experience',
        title: 'Erfahrung',
        description: 'Mindestens ein Eintrag liefert Vertrauen und Senioritätssignale.',
        href: '/settings/profile',
      },
      saved: {
        key: 'saved',
        title: 'Ersten Job speichern',
        description: 'Gespeicherte Jobs starten die Bewerbungspipeline.',
        href: '/jobs',
      },
      review: {
        key: 'review',
        title: 'Matches prüfen',
        description: 'Vergleiche relevante Rollen, sobald dein Profil bereit ist.',
        href: '/matches',
      },
    },
    actions: {
      cv: {
        title: 'Beginne mit dem CV als Profilsignal',
        description: 'Ein CV füllt Titel, Erfahrung, Ausbildung und Skills am schnellsten sicher vor.',
        cta: 'Zum CV-Bereich',
        href: '/settings/profile',
      },
      basics: {
        title: 'Titel und Kurzprofil schärfen',
        description: 'Die Matching-Engine liest diese Felder zuerst, wenn sie dein Profil interpretiert.',
        cta: 'Profil vervollständigen',
        href: '/settings/profile',
      },
      preferences: {
        title: 'Zielrollen und Arbeitsstil wählen',
        description: 'Klare Präferenzen machen Empfehlungen deutlich präziser.',
        cta: 'Präferenzen öffnen',
        href: '/settings/profile',
      },
      skills: {
        title: 'Skills sichtbar machen',
        description: 'Mindestens fünf starke Skills verbessern erklärbare Match-Scores.',
        cta: 'Skills ergänzen',
        href: '/settings/profile',
      },
      experience: {
        title: 'Erfahrungssignale ergänzen',
        description: 'Schon ein Eintrag klärt Level, Branche und Rollenkontext.',
        cta: 'Erfahrung ergänzen',
        href: '/settings/profile',
      },
      saved: {
        title: 'Ersten passenden Job speichern',
        description: 'Gespeicherte Jobs können später durch Bewerbung, Interview und Notizen laufen.',
        cta: 'Jobs ansehen',
        href: '/jobs',
      },
      review: {
        title: 'Matches vergleichen',
        description: 'Mit bereitem Profil kannst du Scores, Lücken und Stärken zusammen prüfen.',
        cta: 'Matches öffnen',
        href: '/matches',
      },
    },
  },
};

function normalizeLocale(locale: string): 'tr' | 'en' | 'de' {
  if (locale === 'en' || locale === 'de') return locale;
  return 'tr';
}

function sectionStatus(
  sections: ProfileCompletionSection[],
  key: string
): ProfileCompletionSection['status'] | null {
  return sections.find((section) => section.key === key)?.status ?? null;
}

function isDone(
  sections: ProfileCompletionSection[],
  key: string
): boolean {
  return sectionStatus(sections, key) === 'done';
}

function hasUploadedCv(aggregate: UserProfileAggregateResponse): boolean {
  const lastParse = aggregate.profile.last_cv_parse;
  return Boolean(
    lastParse?.parse_run_id ||
      lastParse?.source_file_name ||
      lastParse?.parsed_at
  );
}

function buildStatuses(
  aggregate: UserProfileAggregateResponse,
  savedJobCount: number
): Record<CandidateOnboardingStepKey, boolean> {
  const sections = aggregate.profile.completeness.sections;
  const basicsDone = isDone(sections, 'basic_info') && isDone(sections, 'summary');
  const preferencesDone = isDone(sections, 'preferences');
  const skillsDone = isDone(sections, 'skills');
  const experienceDone = isDone(sections, 'experiences');
  const cvDone = hasUploadedCv(aggregate);
  const savedDone = savedJobCount > 0;
  const reviewDone =
    aggregate.profile.completeness.score >= 85 &&
    cvDone &&
    basicsDone &&
    preferencesDone &&
    skillsDone &&
    experienceDone &&
    savedDone;

  return {
    cv: cvDone,
    basics: basicsDone,
    preferences: preferencesDone,
    skills: skillsDone,
    experience: experienceDone,
    saved: savedDone,
    review: reviewDone,
  };
}

export function getCandidateOnboardingCopy(locale: string): Copy {
  return copies[normalizeLocale(locale)];
}

export function buildCandidateOnboardingModel({
  aggregate,
  savedJobCount,
  locale,
}: {
  aggregate: UserProfileAggregateResponse | null;
  savedJobCount: number;
  locale: string;
}): CandidateOnboardingModel | null {
  if (!aggregate) return null;

  const copy = getCandidateOnboardingCopy(locale);
  const doneMap = buildStatuses(aggregate, savedJobCount);
  const orderedKeys: CandidateOnboardingStepKey[] = [
    'cv',
    'basics',
    'preferences',
    'skills',
    'experience',
    'saved',
    'review',
  ];
  const currentKey = orderedKeys.find((key) => !doneMap[key]) ?? 'review';
  const doneCount = orderedKeys.filter((key) => doneMap[key]).length;
  const progressPercent = Math.round((doneCount / orderedKeys.length) * 100);
  const allDone = doneCount === orderedKeys.length;

  return {
    title: allDone ? copy.readyTitle : copy.activeTitle,
    description: allDone ? copy.readyDescription : copy.activeDescription,
    progressPercent,
    progressLabel: copy.doneTemplate
      .replace('{done}', String(doneCount))
      .replace('{total}', String(orderedKeys.length)),
    nextAction: copy.actions[currentKey],
    steps: orderedKeys.map((key) => ({
      ...copy.steps[key],
      status: doneMap[key] ? 'done' : key === currentKey ? 'current' : 'todo',
    })),
  };
}
