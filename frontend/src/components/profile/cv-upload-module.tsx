'use client';

import {
  type ChangeEvent,
  type DragEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import {FeedbackBanner} from '@/components/ui/feedback-banner';
import {ApiError, api} from '@/lib/api';
import {publishRightSurface} from '@/lib/copilot-ui';
import type {
  SupportedLocale,
  UserCvApplySelectedRequest,
  UserCvDraftEducationEntry,
  UserCvDraftExperienceEntry,
  UserCvDraftLanguageEntry,
  UserCvProfileApplyPlan,
  UserCvWorkspaceProfile,
  UserEducationEntry,
  UserExperienceEntry,
  UserLanguageEntry,
} from '@/types/user';
import type {ProfileSuggestionsBundle} from '@/types/profile';

type CvUploadModuleProps = {
  locale: SupportedLocale;
  profile: UserCvWorkspaceProfile;
  suggestions?: ProfileSuggestionsBundle | null;
  onWorkspaceRefresh?: () => Promise<unknown> | unknown;
};

type CopyShape = {
  eyebrow: string;
  title: string;
  subtitle: string;
  progressLabel: string;
  progressDescription: string;
  uploadReadyBadge: string;
  uploadMissingBadge: string;
  uploadCardTitle: string;
  uploadCardSubtitle: string;
  uploadCardSupport: string;
  uploadButton: string;
  replaceButton: string;
  dragHint: string;
  supportedFormats: string;
  uploadLoadingTitle: string;
  uploadLoadingSubtitle: string;
  uploadSuccessTitle: string;
  uploadSuccessSubtitle: string;
  analysisButton: string;
  analysisButtonEmpty: string;
  healthButton: string;
  analysisDrawerTitle: string;
  analysisDrawerSubtitle: string;
  analysisDrawerEmpty: string;
  analysisDrawerLoading: string;
  applyButton: string;
  applyButtonLoading: string;
  applySuccess: string;
  applyEmpty: string;
  uploadRefreshWarning: string;
  applyRefreshWarning: string;
  close: string;
  selectedCountLabel: string;
  summaryTitle: string;
  summarySubtitle: string;
  profileCardTitle: string;
  contactCardTitle: string;
  skillsCardTitle: string;
  experienceCardTitle: string;
  languageCardTitle: string;
  certificatesCardTitle: string;
  noSummaryYet: string;
  noSkillsYet: string;
  noExperienceYet: string;
  noLanguagesYet: string;
  noCertificatesYet: string;
  preferredLocationsLabel: string;
  remotePreferenceLabel: string;
  currentRoleLabel: string;
  updatedFromCvLabel: string;
  helperReviewTitle: string;
  helperReviewBody: string;
  helperReviewCheckbox: string;
  analysisHighlightsTitle: string;
  analysisRecommendationsTitle: string;
  analysisNotesTitle: string;
  headlineSuggestionLabel: string;
  summarySuggestionLabel: string;
  remotePreferenceSuggestionLabel: string;
  listSuggestionLabel: Record<'skills' | 'target_roles' | 'preferred_locations', string>;
  entrySuggestionLabel: Record<'education' | 'experience' | 'language', string>;
  suggestionPreviewTitle: string;
  suggestionCurrentLabel: string;
  suggestionProposedLabel: string;
  suggestionAddedItemsLabel: string;
  recommendationTone: {
    soft: string;
    actionable: string;
  };
  quickStatLabels: {
    ats: string;
    anonymousReview: string;
    reuse: string;
  };
  quickStatValues: {
    ready: string;
    improving: string;
    available: string;
    notAvailable: string;
    reused: string;
    fresh: string;
  };
  recommendationTemplates: {
    missingSummary: string;
    strongerHeadline: string;
    skillsBoost: string;
    roleClarity: string;
    locationReview: string;
    experienceReview: string;
    languageReview: string;
  };
  remotePreferenceValues: Record<'remote' | 'hybrid' | 'onsite', string>;
};

const copy: Record<SupportedLocale, CopyShape> = {
  tr: {
    eyebrow: 'CV Asistanı',
    title: 'CV’ni ekle, profilin akıcı şekilde dolsun',
    subtitle:
      'Teknik detaylarla uğraşmadan profilinin güçlü yanlarını öne çıkaralım. Yüklediğin CV’den temiz bir özet çıkarır, istersen birkaç nazik öneriyle profiline son dokunuşları yaparız.',
    progressLabel: 'Profil doluluk oranı',
    progressDescription:
      'Temel bilgilerin ne kadar tamamlandığını tek bakışta gör.',
    uploadReadyBadge: 'CV yüklendi',
    uploadMissingBadge: 'CV bekleniyor',
    uploadCardTitle: 'CV yükleme alanı',
    uploadCardSubtitle:
      'PDF, DOCX veya görsel formatındaki CV’ni ekle. Geri kalanını biz senin için toparlayalım.',
    uploadCardSupport:
      'Dosyan yüklendiğinde profil özeti otomatik olarak güncellenir ve istersen öneri panelinden son dokunuşları birlikte yapabiliriz.',
    uploadButton: 'CV yükle',
    replaceButton: 'CV’yi değiştir',
    dragHint: 'Dosyanı buraya sürükleyip bırakabilir veya seçebilirsin.',
    supportedFormats: 'Desteklenen formatlar: PDF, DOCX, PNG, JPG, JPEG',
    uploadLoadingTitle: 'CV inceleniyor',
    uploadLoadingSubtitle:
      'Profilinde dolacak alanları hazırlıyoruz. Bu işlem birkaç saniye sürebilir.',
    uploadSuccessTitle: 'CV’in hazır',
    uploadSuccessSubtitle:
      'Profil özetin güncellendi. İstersen bir sonraki adımda sana özel önerileri de birlikte gözden geçirelim.',
    analysisButton: 'CV’n için özel analiz ve önerileri gör',
    analysisButtonEmpty: 'Önerileri görmek için önce CV yükle',
    healthButton: 'CV Sağlığını İncele',
    analysisDrawerTitle: 'Senin için hazırladığımız nazik öneriler',
    analysisDrawerSubtitle:
      'Buradaki öneriler profilini daha güçlü ve daha net anlatmana yardımcı olmak için hazırlanır. İstersen seçtiklerini tek adımda uygularız.',
    analysisDrawerEmpty:
      'Şimdilik ek öneri görünmüyor. Profilin oldukça düzenli görünüyor.',
    analysisDrawerLoading:
      'Sana en uygun önerileri hazırlıyoruz. Birkaç saniye içinde burada olacak.',
    applyButton: 'Seçtiklerimi uygula',
    applyButtonLoading: 'Uygulanıyor...',
    applySuccess:
      'Harika. Seçtiğin güncellemeler profiline eklendi.',
    applyEmpty: 'Henüz seçili öneri yok.',
    uploadRefreshWarning: 'CV yüklendi. Son bilgileri yenilemek için sayfayı bir kez daha açman gerekebilir.',
    applyRefreshWarning: 'Güncellemeler kaydedildi. Son görünümü yenilemek için sayfayı tekrar açabilirsin.',
    close: 'Kapat',
    selectedCountLabel: 'Seçilen öneri',
    summaryTitle: 'CV özeti',
    summarySubtitle:
      'Ana ekranda yalnızca profilini güçlendiren temiz bir özet gösteriyoruz.',
    profileCardTitle: 'Profil özeti',
    contactCardTitle: 'İletişim',
    skillsCardTitle: 'Beceriler',
    experienceCardTitle: 'Son deneyimler',
    languageCardTitle: 'Diller',
    certificatesCardTitle: 'Sertifikalar',
    noSummaryYet: 'Henüz özet bilgisi görünmüyor.',
    noSkillsYet: 'Beceri bilgisi henüz eklenmedi.',
    noExperienceYet: 'Deneyim bilgisi henüz eklenmedi.',
    noLanguagesYet: 'Dil bilgisi henüz eklenmedi.',
    noCertificatesYet: 'Sertifika bilgisi henüz eklenmedi.',
    preferredLocationsLabel: 'Tercih edilen lokasyonlar',
    remotePreferenceLabel: 'Çalışma tercihi',
    currentRoleLabel: 'Profil başlığı',
    updatedFromCvLabel: 'Son güncelleme',
    helperReviewTitle: 'Birlikte hızlıca göz atalım',
    helperReviewBody:
      'Dosya yapısından dolayı birkaç alanı senin teyidinle ilerletmek daha iyi olabilir. Rahatça gözden geçirip yalnızca istediklerini uygulayabilirsin.',
    helperReviewCheckbox: 'Önerileri kontrol ettim, seçtiklerimi uygulayabiliriz.',
    analysisHighlightsTitle: 'Sence güzel duran noktalar',
    analysisRecommendationsTitle: 'Hızlı dokunuş önerileri',
    analysisNotesTitle: 'Kısa notlar',
    headlineSuggestionLabel: 'Daha net profil başlığı',
    summarySuggestionLabel: 'Daha güçlü özet',
    remotePreferenceSuggestionLabel: 'Çalışma tercihi',
    listSuggestionLabel: {
      skills: 'Becerilerine eklenebilecek alanlar',
      target_roles: 'Sana uygun rol önerileri',
      preferred_locations: 'Lokasyon tercihleri',
    },
    entrySuggestionLabel: {
      education: 'Eğitim geçmişine eklenebilecek satır',
      experience: 'Deneyim geçmişine eklenebilecek satır',
      language: 'Dil bilgilerine eklenebilecek satır',
    },
    suggestionPreviewTitle: 'Öneri önizlemesi',
    suggestionCurrentLabel: 'Şu an',
    suggestionProposedLabel: 'Önerilen',
    suggestionAddedItemsLabel: 'Eklenecek alanlar',
    recommendationTone: {
      soft: 'Bu bölüm zaten iyi görünüyor; küçük bir dokunuşla daha da netleşebilir.',
      actionable:
        'Buradaki öneri profilini daha hızlı anlaşılır ve daha güçlü hale getirebilir.',
    },
    quickStatLabels: {
      ats: 'Okunabilirlik',
      anonymousReview: 'Anonim inceleme',
      reuse: 'Yeniden kullanım',
    },
    quickStatValues: {
      ready: 'Hazır',
      improving: 'Geliştirilebilir',
      available: 'Hazır',
      notAvailable: 'Henüz yok',
      reused: 'Hızlı işlendi',
      fresh: 'Yeni işlendi',
    },
    recommendationTemplates: {
      missingSummary:
        'Kısa bir özet eklemek profilini birkaç saniyede çok daha güçlü gösterebilir.',
      strongerHeadline:
        'Başlığını biraz daha netleştirmek seni doğru fırsatlarla daha hızlı eşleştirir.',
      skillsBoost:
        'Beceri listen birkaç güçlü anahtar kelimeyle daha etkileyici hale gelebilir.',
      roleClarity:
        'Hedef rol tercihlerini görünür kılmak profilinin odak noktasını netleştirir.',
      locationReview:
        'Lokasyon tercihini netleştirmek daha uygun fırsatları öne çıkarabilir.',
      experienceReview:
        'Deneyim satırlarını eklemek profilinin güven duygusunu artırır.',
      languageReview:
        'Dil bilgilerini eklemek uluslararası fırsatlarda profilini güçlendirir.',
    },
    remotePreferenceValues: {
      remote: 'Uzaktan',
      hybrid: 'Hibrit',
      onsite: 'Ofisten',
    },
  },
  en: {
    eyebrow: 'CV Assistant',
    title: 'Upload your CV and let your profile come together smoothly',
    subtitle:
      'No technical noise, no cold system language. We turn your CV into a clean profile summary and, if you want, guide you with a few thoughtful recommendations.',
    progressLabel: 'Profile completion',
    progressDescription:
      'See how complete your core profile is at a glance.',
    uploadReadyBadge: 'CV uploaded',
    uploadMissingBadge: 'Awaiting CV',
    uploadCardTitle: 'CV upload area',
    uploadCardSubtitle:
      'Add your PDF, DOCX, or image CV and let us prepare the structured profile for you.',
    uploadCardSupport:
      'Once your file is uploaded, your profile summary updates automatically and you can review optional recommendations in the side panel.',
    uploadButton: 'Upload CV',
    replaceButton: 'Replace CV',
    dragHint: 'Drag and drop your file here or choose it from your device.',
    supportedFormats: 'Supported formats: PDF, DOCX, PNG, JPG, JPEG',
    uploadLoadingTitle: 'Reviewing your CV',
    uploadLoadingSubtitle:
      'We are preparing the profile sections that can be filled from your file. This usually takes a few seconds.',
    uploadSuccessTitle: 'Your CV is ready',
    uploadSuccessSubtitle:
      'Your profile summary has been refreshed. If you want, we can now look at a few tailored recommendations together.',
    analysisButton: 'View CV recommendations',
    analysisButtonEmpty: 'Upload a CV to unlock recommendations',
    healthButton: 'Review CV health',
    analysisDrawerTitle: 'A few thoughtful suggestions for your profile',
    analysisDrawerSubtitle:
      'These recommendations are designed to help your profile sound clearer, stronger, and more complete. You can apply only the ones you like.',
    analysisDrawerEmpty:
      'There are no extra suggestions for now. Your profile already looks tidy.',
    analysisDrawerLoading:
      'We are preparing a focused set of suggestions for you. They will appear here shortly.',
    applyButton: 'Apply selected suggestions',
    applyButtonLoading: 'Applying...',
    applySuccess:
      'Great. Your selected updates have been added to the profile.',
    applyEmpty: 'There are no selected suggestions yet.',
    uploadRefreshWarning: 'Your CV was uploaded, but you may need to reopen this page to refresh the latest view.',
    applyRefreshWarning: 'Your updates were saved, but you may need to reopen this page to refresh the latest view.',
    close: 'Close',
    selectedCountLabel: 'Selected suggestions',
    summaryTitle: 'CV summary',
    summarySubtitle:
      'The main screen stays clean and focused, showing only the most useful parts of your profile.',
    profileCardTitle: 'Profile summary',
    contactCardTitle: 'Contact',
    skillsCardTitle: 'Skills',
    experienceCardTitle: 'Recent experience',
    languageCardTitle: 'Languages',
    certificatesCardTitle: 'Certificates',
    noSummaryYet: 'No profile summary is visible yet.',
    noSkillsYet: 'No skills have been added yet.',
    noExperienceYet: 'No experience has been added yet.',
    noLanguagesYet: 'No languages have been added yet.',
    noCertificatesYet: 'No certificates have been added yet.',
    preferredLocationsLabel: 'Preferred locations',
    remotePreferenceLabel: 'Work preference',
    currentRoleLabel: 'Profile headline',
    updatedFromCvLabel: 'Updated from CV',
    helperReviewTitle: 'A quick review together',
    helperReviewBody:
      'A few fields may benefit from your quick confirmation because of the file structure. You can calmly review only the suggestions you want to keep.',
    helperReviewCheckbox:
      'I reviewed the suggestions and I am ready to apply the selected ones.',
    analysisHighlightsTitle: 'What already looks strong',
    analysisRecommendationsTitle: 'Quick improvement ideas',
    analysisNotesTitle: 'Helpful notes',
    headlineSuggestionLabel: 'Clearer profile headline',
    summarySuggestionLabel: 'Stronger profile summary',
    remotePreferenceSuggestionLabel: 'Work preference',
    listSuggestionLabel: {
      skills: 'Skills worth adding',
      target_roles: 'Role ideas that fit you',
      preferred_locations: 'Location preferences',
    },
    entrySuggestionLabel: {
      education: 'Education item to add',
      experience: 'Experience item to add',
      language: 'Language item to add',
    },
    suggestionPreviewTitle: 'Suggestion preview',
    suggestionCurrentLabel: 'Current',
    suggestionProposedLabel: 'Suggested',
    suggestionAddedItemsLabel: 'Items to add',
    recommendationTone: {
      soft: 'This part already feels solid; a small refinement could make it even clearer.',
      actionable:
        'This suggestion can make your profile easier to understand and stronger in seconds.',
    },
    quickStatLabels: {
      ats: 'Readability',
      anonymousReview: 'Anonymous review',
      reuse: 'Processing speed',
    },
    quickStatValues: {
      ready: 'Ready',
      improving: 'Can improve',
      available: 'Available',
      notAvailable: 'Not yet',
      reused: 'Reused',
      fresh: 'Fresh parse',
    },
    recommendationTemplates: {
      missingSummary:
        'A short summary can make your profile feel stronger in just a few lines.',
      strongerHeadline:
        'A clearer headline can help your profile match the right opportunities faster.',
      skillsBoost:
        'A few additional skill keywords can make your profile more persuasive.',
      roleClarity:
        'Making your target roles visible helps clarify your focus.',
      locationReview:
        'Clarifying location preferences can surface more relevant opportunities.',
      experienceReview:
        'Adding experience entries can strengthen the credibility of your profile.',
      languageReview:
        'Adding language details can make your profile more complete for international roles.',
    },
    remotePreferenceValues: {
      remote: 'Remote',
      hybrid: 'Hybrid',
      onsite: 'On-site',
    },
  },
  de: {
    eyebrow: 'CV-Assistent',
    title: 'Lade deinen CV hoch und lass dein Profil flüssig entstehen',
    subtitle:
      'Ohne technische Hürden und ohne kalte Systemtexte. Wir bereiten eine klare Profilübersicht vor und zeigen dir auf Wunsch einige hilfreiche Empfehlungen.',
    progressLabel: 'Profil-Vollständigkeit',
    progressDescription:
      'Sieh auf einen Blick, wie vollständig dein Kernprofil bereits ist.',
    uploadReadyBadge: 'CV hochgeladen',
    uploadMissingBadge: 'CV fehlt noch',
    uploadCardTitle: 'CV-Upload',
    uploadCardSubtitle:
      'Lade deinen CV als PDF, DOCX oder Bild hoch und wir strukturieren die wichtigsten Profildaten für dich.',
    uploadCardSupport:
      'Nach dem Upload wird deine Profilübersicht automatisch aktualisiert. Zusätzliche Empfehlungen kannst du danach im rechten Panel ansehen.',
    uploadButton: 'CV hochladen',
    replaceButton: 'CV ersetzen',
    dragHint: 'Ziehe deine Datei hierher oder wähle sie direkt von deinem Gerät aus.',
    supportedFormats: 'Unterstützte Formate: PDF, DOCX, PNG, JPG, JPEG',
    uploadLoadingTitle: 'Dein CV wird geprüft',
    uploadLoadingSubtitle:
      'Wir bereiten gerade die Profilbereiche vor, die wir für dich befüllen können. Das dauert meist nur wenige Sekunden.',
    uploadSuccessTitle: 'Dein CV ist bereit',
    uploadSuccessSubtitle:
      'Deine Profilübersicht wurde aktualisiert. Wenn du möchtest, schauen wir uns jetzt noch ein paar persönliche Empfehlungen an.',
    analysisButton: 'CV-Empfehlungen ansehen',
    analysisButtonEmpty: 'Lade zuerst einen CV hoch, um Empfehlungen zu sehen',
    healthButton: 'CV-Gesundheit prüfen',
    analysisDrawerTitle: 'Ein paar durchdachte Empfehlungen für dich',
    analysisDrawerSubtitle:
      'Diese Vorschläge helfen dabei, dein Profil klarer, stärker und vollständiger wirken zu lassen. Du kannst nur das übernehmen, was dir sinnvoll erscheint.',
    analysisDrawerEmpty:
      'Im Moment gibt es keine zusätzlichen Empfehlungen. Dein Profil wirkt bereits ordentlich.',
    analysisDrawerLoading:
      'Wir bereiten gerade passende Empfehlungen für dich vor. Sie erscheinen gleich hier.',
    applyButton: 'Ausgewählte Empfehlungen übernehmen',
    applyButtonLoading: 'Wird übernommen...',
    applySuccess:
      'Perfekt. Deine ausgewählten Änderungen wurden in das Profil übernommen.',
    applyEmpty: 'Noch keine Empfehlung ausgewählt.',
    uploadRefreshWarning: 'Dein CV wurde hochgeladen. Eventuell musst du die Seite neu öffnen, um die neuesten Inhalte zu sehen.',
    applyRefreshWarning: 'Deine Änderungen wurden gespeichert. Eventuell musst du die Seite neu öffnen, um die neuesten Inhalte zu sehen.',
    close: 'Schließen',
    selectedCountLabel: 'Ausgewählte Empfehlungen',
    summaryTitle: 'CV-Übersicht',
    summarySubtitle:
      'Die Hauptansicht bleibt bewusst ruhig und zeigt nur die relevanten Profilinformationen.',
    profileCardTitle: 'Profilübersicht',
    contactCardTitle: 'Kontakt',
    skillsCardTitle: 'Kompetenzen',
    experienceCardTitle: 'Letzte Erfahrungen',
    languageCardTitle: 'Sprachen',
    certificatesCardTitle: 'Zertifikate',
    noSummaryYet: 'Noch keine Profilzusammenfassung sichtbar.',
    noSkillsYet: 'Noch keine Kompetenzen vorhanden.',
    noExperienceYet: 'Noch keine Erfahrungen vorhanden.',
    noLanguagesYet: 'Noch keine Sprachen vorhanden.',
    noCertificatesYet: 'Noch keine Zertifikate vorhanden.',
    preferredLocationsLabel: 'Bevorzugte Standorte',
    remotePreferenceLabel: 'Arbeitspräferenz',
    currentRoleLabel: 'Profilüberschrift',
    updatedFromCvLabel: 'Aktualisiert aus CV',
    helperReviewTitle: 'Kurz gemeinsam prüfen',
    helperReviewBody:
      'Einige Felder profitieren wegen der Dateistruktur von einer kurzen Bestätigung durch dich. Schau einfach in Ruhe nur auf die Vorschläge, die du übernehmen möchtest.',
    helperReviewCheckbox:
      'Ich habe die Vorschläge geprüft und kann die ausgewählten Änderungen übernehmen.',
    analysisHighlightsTitle: 'Was bereits stark wirkt',
    analysisRecommendationsTitle: 'Schnelle Verbesserungsideen',
    analysisNotesTitle: 'Hilfreiche Hinweise',
    headlineSuggestionLabel: 'Klarere Profilüberschrift',
    summarySuggestionLabel: 'Stärkeres Profil-Abstract',
    remotePreferenceSuggestionLabel: 'Arbeitspräferenz',
    listSuggestionLabel: {
      skills: 'Kompetenzen, die du ergänzen könntest',
      target_roles: 'Passende Rollenideen',
      preferred_locations: 'Standortpräferenzen',
    },
    entrySuggestionLabel: {
      education: 'Ausbildungs-Eintrag zum Ergänzen',
      experience: 'Berufserfahrung zum Ergänzen',
      language: 'Sprach-Eintrag zum Ergänzen',
    },
    suggestionPreviewTitle: 'Vorschau',
    suggestionCurrentLabel: 'Aktuell',
    suggestionProposedLabel: 'Vorgeschlagen',
    suggestionAddedItemsLabel: 'Ergänzungen',
    recommendationTone: {
      soft: 'Dieser Bereich wirkt bereits gut; eine kleine Verfeinerung könnte ihn noch klarer machen.',
      actionable:
        'Dieser Vorschlag kann dein Profil schneller verständlich und stärker wirken lassen.',
    },
    quickStatLabels: {
      ats: 'Lesbarkeit',
      anonymousReview: 'Anonyme Prüfung',
      reuse: 'Verarbeitung',
    },
    quickStatValues: {
      ready: 'Bereit',
      improving: 'Verbesserbar',
      available: 'Verfügbar',
      notAvailable: 'Noch nicht',
      reused: 'Wiederverwendet',
      fresh: 'Neu verarbeitet',
    },
    recommendationTemplates: {
      missingSummary:
        'Eine kurze Zusammenfassung kann dein Profil in wenigen Zeilen deutlich stärken.',
      strongerHeadline:
        'Eine klarere Überschrift kann dein Profil schneller mit den richtigen Chancen verbinden.',
      skillsBoost:
        'Ein paar zusätzliche Kompetenz-Begriffe können dein Profil überzeugender machen.',
      roleClarity:
        'Sichtbare Zielrollen helfen, deinen Fokus klarer zu zeigen.',
      locationReview:
        'Klare Standortwünsche können relevantere Chancen hervorheben.',
      experienceReview:
        'Ergänzte Berufserfahrung kann die Wirkung deines Profils stärken.',
      languageReview:
        'Sprachangaben machen dein Profil für internationale Rollen vollständiger.',
    },
    remotePreferenceValues: {
      remote: 'Remote',
      hybrid: 'Hybrid',
      onsite: 'Vor Ort',
    },
  },
};

type SuggestionCard =
  | {
      id: string;
      category: 'scalar';
      title: string;
      description: string;
      fieldName: string;
      selected: boolean;
      currentValue: string | null;
      suggestedValue: string | null;
    }
  | {
      id: string;
      category: 'list';
      title: string;
      description: string;
      fieldName: string;
      selected: boolean;
      currentValue: string[];
      suggestedItems: string[];
      addedItems: string[];
    }
  | {
      id: string;
      category: 'education' | 'experience' | 'language';
      title: string;
      description: string;
      index: number;
      selected: boolean;
      currentValue: string | null;
      suggestedValue: string;
    };

function formatDateLabel(value: string | null): string | null {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat('tr-TR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(parsed);
}

function uniquePush(values: string[], item: string): string[] {
  if (values.includes(item)) {
    return values;
  }
  return [...values, item];
}

function uniqueRemove(values: string[], item: string): string[] {
  return values.filter((value) => value !== item);
}

function uniquePushNumber(values: number[], item: number): number[] {
  if (values.includes(item)) {
    return values;
  }
  return [...values, item];
}

function uniqueRemoveNumber(values: number[], item: number): number[] {
  return values.filter((value) => value !== item);
}

function buildDefaultSelection(
  plan: UserCvProfileApplyPlan
): UserCvApplySelectedRequest {
  return {
    parse_run_id: plan.parse_run_id,
    scalar_fields: [plan.headline, plan.summary, plan.remote_preference]
      .filter((item) => item.default_selected)
      .map((item) => item.field_name),
    list_fields: [plan.skills, plan.target_roles, plan.preferred_locations]
      .filter((item) => item.default_selected)
      .map((item) => item.field_name),
    education_entry_indexes: plan.education_entries
      .map((item, index) => ({item, index}))
      .filter(({item}) => item.default_selected)
      .map(({index}) => index),
    experience_entry_indexes: plan.experience_entries
      .map((item, index) => ({item, index}))
      .filter(({item}) => item.default_selected)
      .map(({index}) => index),
    language_entry_indexes: plan.language_entries
      .map((item, index) => ({item, index}))
      .filter(({item}) => item.default_selected)
      .map(({index}) => index),
    manual_review_acknowledged: false,
  };
}

function countSelectedSuggestions(selection: UserCvApplySelectedRequest | null): number {
  if (!selection) {
    return 0;
  }

  return (
    selection.scalar_fields.length +
    selection.list_fields.length +
    selection.education_entry_indexes.length +
    selection.experience_entry_indexes.length +
    selection.language_entry_indexes.length
  );
}

function joinOrFallback(values: string[], fallback: string): string {
  if (values.length === 0) {
    return fallback;
  }
  return values.join(', ');
}

function formatEducationEntry(entry: UserCvDraftEducationEntry | UserEducationEntry): string {
  const parts = [entry.school_name, entry.degree_name, entry.field_of_study].filter(
    Boolean
  ) as string[];
  const yearRange =
    entry.start_year || entry.end_year
      ? [entry.start_year, entry.end_year].filter(Boolean).join(' – ')
      : null;

  if (yearRange) {
    parts.push(yearRange);
  }

  return parts.join(' · ');
}

function formatExperienceEntry(
  entry: UserCvDraftExperienceEntry | UserExperienceEntry
): string {
  const parts = [entry.title, entry.company_name].filter(Boolean) as string[];
  const yearRange =
    entry.start_year || entry.end_year
      ? [entry.start_year, entry.end_year].filter(Boolean).join(' – ')
      : null;

  if (yearRange) {
    parts.push(yearRange);
  }

  if (entry.summary) {
    parts.push(entry.summary);
  }

  return parts.join(' · ');
}

function formatLanguageEntry(
  entry: UserCvDraftLanguageEntry | UserLanguageEntry
): string {
  const parts = [entry.language_name, entry.proficiency_level, entry.notes].filter(
    Boolean
  ) as string[];
  return parts.join(' · ');
}

function resolveRemotePreferenceLabel(
  value: string | null,
  currentCopy: CopyShape
): string | null {
  if (!value) {
    return null;
  }

  if (value === 'remote' || value === 'hybrid' || value === 'onsite') {
    return currentCopy.remotePreferenceValues[value];
  }

  return value;
}

function buildHighlights(
  profile: UserCvWorkspaceProfile,
  currentCopy: CopyShape
): string[] {
  const highlights: string[] = [];

  if (profile.headline) {
    highlights.push(`• ${profile.headline}`);
  }
  if (profile.skills.length >= 5) {
    highlights.push(`• ${profile.skills.length} ${currentCopy.skillsCardTitle.toLowerCase()} alanı görünür durumda`);
  }
  if (profile.experience_entries.length > 0) {
    highlights.push(`• ${profile.experience_entries.length} ${currentCopy.experienceCardTitle.toLowerCase()} bilgisi eklenmiş`);
  }
  if (profile.language_entries.length > 0) {
    highlights.push(`• ${profile.language_entries.length} ${currentCopy.languageCardTitle.toLowerCase()} profilde yer alıyor`);
  }

  return highlights.slice(0, 3);
}

function buildFriendlyNotes(
  plan: UserCvProfileApplyPlan,
  currentCopy: CopyShape
): string[] {
  const notes: string[] = [];

  if (plan.summary.action !== 'noop') {
    notes.push(currentCopy.recommendationTemplates.missingSummary);
  }
  if (plan.headline.action !== 'noop') {
    notes.push(currentCopy.recommendationTemplates.strongerHeadline);
  }
  if (plan.skills.action !== 'noop') {
    notes.push(currentCopy.recommendationTemplates.skillsBoost);
  }
  if (plan.target_roles.action !== 'noop') {
    notes.push(currentCopy.recommendationTemplates.roleClarity);
  }
  if (plan.preferred_locations.action !== 'noop') {
    notes.push(currentCopy.recommendationTemplates.locationReview);
  }
  if (plan.experience_entries.some((entry) => entry.action !== 'noop')) {
    notes.push(currentCopy.recommendationTemplates.experienceReview);
  }
  if (plan.language_entries.some((entry) => entry.action !== 'noop')) {
    notes.push(currentCopy.recommendationTemplates.languageReview);
  }

  return notes.slice(0, 4);
}

function buildSuggestionCards(
  plan: UserCvProfileApplyPlan,
  selection: UserCvApplySelectedRequest | null,
  currentCopy: CopyShape
): SuggestionCard[] {
  const cards: SuggestionCard[] = [];

  const scalarSuggestions = [
    {
      suggestion: plan.headline,
      title: currentCopy.headlineSuggestionLabel,
      description: currentCopy.recommendationTone.actionable,
    },
    {
      suggestion: plan.summary,
      title: currentCopy.summarySuggestionLabel,
      description: currentCopy.recommendationTone.actionable,
    },
    {
      suggestion: plan.remote_preference,
      title: currentCopy.remotePreferenceSuggestionLabel,
      description: currentCopy.recommendationTone.soft,
    },
  ];

  for (const item of scalarSuggestions) {
    if (item.suggestion.action === 'noop') {
      continue;
    }

    cards.push({
      id: `scalar:${item.suggestion.field_name}`,
      category: 'scalar',
      title: item.title,
      description: item.description,
      fieldName: item.suggestion.field_name,
      selected: selection?.scalar_fields.includes(item.suggestion.field_name) ?? false,
      currentValue: item.suggestion.current_value,
      suggestedValue: item.suggestion.suggested_value,
    });
  }

  const listSuggestions = [
    {
      suggestion: plan.skills,
      title: currentCopy.listSuggestionLabel.skills,
      description: currentCopy.recommendationTone.actionable,
    },
    {
      suggestion: plan.target_roles,
      title: currentCopy.listSuggestionLabel.target_roles,
      description: currentCopy.recommendationTone.soft,
    },
    {
      suggestion: plan.preferred_locations,
      title: currentCopy.listSuggestionLabel.preferred_locations,
      description: currentCopy.recommendationTone.soft,
    },
  ];

  for (const item of listSuggestions) {
    if (item.suggestion.action === 'noop') {
      continue;
    }

    cards.push({
      id: `list:${item.suggestion.field_name}`,
      category: 'list',
      title: item.title,
      description: item.description,
      fieldName: item.suggestion.field_name,
      selected: selection?.list_fields.includes(item.suggestion.field_name) ?? false,
      currentValue: item.suggestion.current_items,
      suggestedItems: item.suggestion.suggested_items,
      addedItems: item.suggestion.items_to_add,
    });
  }

  for (const [index, item] of plan.education_entries.entries()) {
    if (item.action === 'noop') {
      continue;
    }

    cards.push({
      id: `education:${index}`,
      category: 'education',
      title: currentCopy.entrySuggestionLabel.education,
      description: currentCopy.recommendationTone.soft,
      index,
      selected: selection?.education_entry_indexes.includes(index) ?? false,
      currentValue: null,
      suggestedValue: formatEducationEntry(item.draft_entry),
    });
  }

  for (const [index, item] of plan.experience_entries.entries()) {
    if (item.action === 'noop') {
      continue;
    }

    cards.push({
      id: `experience:${index}`,
      category: 'experience',
      title: currentCopy.entrySuggestionLabel.experience,
      description: currentCopy.recommendationTone.actionable,
      index,
      selected: selection?.experience_entry_indexes.includes(index) ?? false,
      currentValue: null,
      suggestedValue: formatExperienceEntry(item.draft_entry),
    });
  }

  for (const [index, item] of plan.language_entries.entries()) {
    if (item.action === 'noop') {
      continue;
    }

    cards.push({
      id: `language:${index}`,
      category: 'language',
      title: currentCopy.entrySuggestionLabel.language,
      description: currentCopy.recommendationTone.soft,
      index,
      selected: selection?.language_entry_indexes.includes(index) ?? false,
      currentValue: null,
      suggestedValue: formatLanguageEntry(item.draft_entry),
    });
  }

  return cards;
}

function QuickStat({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-[24px] border border-border bg-background/80 p-4 shadow-sm backdrop-blur">
      <div className="flex items-start justify-between gap-3">
        <div className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
          {label}
        </div>
        <div className="rounded-full border border-border bg-background px-3 py-1 text-xs font-medium text-foreground">
          {value}
        </div>
      </div>
    </div>
  );
}

function SummaryCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-[20px] border border-border bg-background p-5 shadow-[0_16px_40px_-30px_rgba(15,23,42,0.28)]">
      <div className="text-sm font-semibold text-foreground">{title}</div>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function DrawerSkeleton() {
  return (
    <div className="space-y-4">
      <div className="rounded-3xl border border-border bg-background p-5">
        <div className="h-4 w-40 animate-pulse rounded-full bg-muted" />
        <div className="mt-3 h-3 w-full animate-pulse rounded-full bg-muted" />
        <div className="mt-2 h-3 w-5/6 animate-pulse rounded-full bg-muted" />
      </div>
      {[0, 1, 2].map((item) => (
        <div
          key={item}
          className="rounded-3xl border border-border bg-background p-5"
        >
          <div className="h-4 w-32 animate-pulse rounded-full bg-muted" />
          <div className="mt-4 h-3 w-full animate-pulse rounded-full bg-muted" />
          <div className="mt-2 h-3 w-4/5 animate-pulse rounded-full bg-muted" />
          <div className="mt-5 h-10 w-full animate-pulse rounded-2xl bg-muted" />
        </div>
      ))}
    </div>
  );
}

export function CvUploadModule({
  locale,
  profile,
  suggestions = null,
  onWorkspaceRefresh,
}: CvUploadModuleProps) {
  const currentCopy = copy[locale];
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const drawerRef = useRef<HTMLElement | null>(null);

  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerView, setDrawerView] = useState<'overview' | 'health'>('overview');
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [uploadMessageTone, setUploadMessageTone] = useState<'success' | 'warning'>('success');
  const [drawerLoading, setDrawerLoading] = useState(false);
  const [drawerError, setDrawerError] = useState<string | null>(null);
  const [plan, setPlan] = useState<UserCvProfileApplyPlan | null>(null);
  const [selection, setSelection] = useState<UserCvApplySelectedRequest | null>(null);
  const [applyLoading, setApplyLoading] = useState(false);
  const [applyMessage, setApplyMessage] = useState<string | null>(null);
  const [applyMessageTone, setApplyMessageTone] = useState<'success' | 'warning'>('success');
  const [manualReviewAcknowledged, setManualReviewAcknowledged] = useState(false);

  const latestCv = profile.latest_cv_upload;

  const refreshProfile = useCallback(async () => {
    const result = await onWorkspaceRefresh?.();
    return result !== null;
  }, [onWorkspaceRefresh]);

  const resolveUiErrorMessage = useCallback((reason: unknown, fallback: string) => {
    if (reason instanceof ApiError) {
      return reason.detail || reason.message || fallback;
    }

    if (reason instanceof Error) {
      return reason.message || fallback;
    }

    return fallback;
  }, []);

  const refreshPlan = useCallback(async (): Promise<boolean> => {
    setDrawerLoading(true);
    setDrawerError(null);

    try {
      const response = await api.getLatestCvProfileApplyPlan();
      setPlan(response);
      setSelection(response ? buildDefaultSelection(response) : null);
      setManualReviewAcknowledged(
        response?.extraction_metadata.needs_manual_review ? false : true
      );
      return true;
    } catch (reason) {
      setDrawerError(resolveUiErrorMessage(reason, currentCopy.analysisDrawerEmpty));
    } finally {
      setDrawerLoading(false);
    }

    return false;
  }, [currentCopy.analysisDrawerEmpty, resolveUiErrorMessage]);

  useEffect(() => {
    if (drawerOpen && plan === null && !drawerLoading && latestCv) {
      void refreshPlan();
    }
  }, [drawerLoading, drawerOpen, latestCv, plan, refreshPlan]);

  useEffect(() => {
    if (typeof window === 'undefined') return undefined;

    const emitSurfaceState = () => {
      const width = drawerOpen && drawerRef.current ? drawerRef.current.getBoundingClientRect().width : 0;
      publishRightSurface({open: drawerOpen, width, source: 'cv-upload-module'});
    };

    emitSurfaceState();
    if (!drawerOpen) {
      return () => publishRightSurface({open: false, width: 0, source: 'cv-upload-module'});
    }

    const frame = window.requestAnimationFrame(emitSurfaceState);
    const observer = new ResizeObserver(() => emitSurfaceState());
    if (drawerRef.current) observer.observe(drawerRef.current);
    window.addEventListener('resize', emitSurfaceState);

    return () => {
      window.cancelAnimationFrame(frame);
      observer.disconnect();
      window.removeEventListener('resize', emitSurfaceState);
      publishRightSurface({open: false, width: 0, source: 'cv-upload-module'});
    };
  }, [drawerOpen]);

  useEffect(() => {
    setPlan(null);
    setSelection(null);
    setApplyMessage(null);
    setDrawerError(null);
    setManualReviewAcknowledged(false);
  }, [latestCv?.id]);

  const completionScore = profile.completeness.score;
  const progressWidth = `${Math.min(Math.max(completionScore, 0), 100)}%`;

  const quickStats = useMemo(() => {
    const atsScore = latestCv?.enterprise_metadata?.ats.score ?? null;
    const atsValue =
      atsScore === null
        ? currentCopy.quickStatValues.improving
        : `${atsScore}/100`;

    const redactionValue =
      latestCv?.enterprise_metadata?.redaction.available
        ? currentCopy.quickStatValues.available
        : currentCopy.quickStatValues.notAvailable;

    const reuseValue =
      latestCv?.enterprise_metadata?.cache.exact_reusable ||
      latestCv?.enterprise_metadata?.cache.partial_reusable ||
      latestCv?.enterprise_metadata?.cache.status === 'exact_hit' ||
      latestCv?.enterprise_metadata?.cache.status === 'partial_reuse'
        ? currentCopy.quickStatValues.reused
        : currentCopy.quickStatValues.fresh;

    return [
      {
        label: currentCopy.quickStatLabels.ats,
        value: atsValue,
      },
      {
        label: currentCopy.quickStatLabels.anonymousReview,
        value: redactionValue,
      },
      {
        label: currentCopy.quickStatLabels.reuse,
        value: reuseValue,
      },
    ];
  }, [currentCopy, latestCv]);

  const highlights = useMemo(
    () => buildHighlights(profile, currentCopy),
    [currentCopy, profile]
  );

  const notes = useMemo(
    () => (plan ? buildFriendlyNotes(plan, currentCopy) : []),
    [currentCopy, plan]
  );

  const suggestionCards = useMemo(
    () => (plan ? buildSuggestionCards(plan, selection, currentCopy) : []),
    [currentCopy, plan, selection]
  );

  const selectedCount = countSelectedSuggestions(selection);

  const healthSections = useMemo(() => {
    return [
      {
        title: locale === 'tr' ? 'Güçlü yönler' : locale === 'de' ? 'Starke Seiten' : 'Strong areas',
        items: suggestions?.highlights ?? [],
      },
      {
        title: locale === 'tr' ? 'Geliştirilmesi iyi olacak alanlar' : locale === 'de' ? 'Bereiche mit Potenzial' : 'Areas to strengthen',
        items: suggestions?.critical_gaps ?? [],
      },
      {
        title: locale === 'tr' ? 'Hızlı iyileştirmeler' : locale === 'de' ? 'Schnelle Verbesserungen' : 'Quick improvements',
        items: suggestions?.quick_wins ?? [],
      },
    ];
  }, [locale, suggestions]);

  async function handleFileUpload(file: File): Promise<void> {
    setUploading(true);
    setUploadMessage(null);
    setDrawerError(null);
    setApplyMessage(null);

    try {
      await api.uploadCv(file);
      const refreshed = await refreshProfile();
      setUploadMessageTone(refreshed ? 'success' : 'warning');
      setUploadMessage(
        refreshed
          ? currentCopy.uploadSuccessSubtitle
          : currentCopy.uploadRefreshWarning
      );
    } catch (reason) {
      if (reason instanceof ApiError) {
        setDrawerError(reason.detail || reason.message || currentCopy.analysisDrawerEmpty);
      } else if (reason instanceof Error) {
        setDrawerError(reason.message || currentCopy.analysisDrawerEmpty);
      } else {
        setDrawerError(currentCopy.analysisDrawerEmpty);
      }
    } finally {
      setUploading(false);
    }
  }

  function handleFileInputChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    void handleFileUpload(file);
    event.target.value = '';
  }

  function handleDragEnter(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    setDragActive(true);
  }

  function handleDragLeave(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    setDragActive(false);
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    setDragActive(true);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    setDragActive(false);

    const file = event.dataTransfer.files?.[0];
    if (!file) {
      return;
    }

    void handleFileUpload(file);
  }

  function toggleScalarField(fieldName: string) {
    setSelection((current) => {
      if (!current) {
        return current;
      }

      const selected = current.scalar_fields.includes(fieldName);
      return {
        ...current,
        scalar_fields: selected
          ? uniqueRemove(current.scalar_fields, fieldName)
          : uniquePush(current.scalar_fields, fieldName),
      };
    });
  }

  function toggleListField(fieldName: string) {
    setSelection((current) => {
      if (!current) {
        return current;
      }

      const selected = current.list_fields.includes(fieldName);
      return {
        ...current,
        list_fields: selected
          ? uniqueRemove(current.list_fields, fieldName)
          : uniquePush(current.list_fields, fieldName),
      };
    });
  }

  function toggleIndexedField(
    kind: 'education' | 'experience' | 'language',
    index: number
  ) {
    setSelection((current) => {
      if (!current) {
        return current;
      }

      if (kind === 'education') {
        const selected = current.education_entry_indexes.includes(index);
        return {
          ...current,
          education_entry_indexes: selected
            ? uniqueRemoveNumber(current.education_entry_indexes, index)
            : uniquePushNumber(current.education_entry_indexes, index),
        };
      }

      if (kind === 'experience') {
        const selected = current.experience_entry_indexes.includes(index);
        return {
          ...current,
          experience_entry_indexes: selected
            ? uniqueRemoveNumber(current.experience_entry_indexes, index)
            : uniquePushNumber(current.experience_entry_indexes, index),
        };
      }

      const selected = current.language_entry_indexes.includes(index);
      return {
        ...current,
        language_entry_indexes: selected
          ? uniqueRemoveNumber(current.language_entry_indexes, index)
          : uniquePushNumber(current.language_entry_indexes, index),
      };
    });
  }

  async function handleApplySelected() {
    if (!selection) {
      return;
    }

    setApplyLoading(true);
    setApplyMessage(null);
    setDrawerError(null);

    try {
      const response = await api.applySelectedCvProfileOperations({
        ...selection,
        manual_review_acknowledged: manualReviewAcknowledged,
      });
      let refreshed = true;
      if (response.workspace_refresh_required) {
        refreshed = await refreshProfile();
      }
      await refreshPlan();
      setApplyMessageTone(refreshed ? 'success' : 'warning');
      setApplyMessage(refreshed ? currentCopy.applySuccess : currentCopy.applyRefreshWarning);
    } catch (reason) {
      if (reason instanceof Error) {
        setDrawerError(reason.message || currentCopy.applyEmpty);
      } else {
        setDrawerError(currentCopy.applyEmpty);
      }
    } finally {
      setApplyLoading(false);
    }
  }

  const profileSummaryLines = [
    profile.headline || currentCopy.noSummaryYet,
    profile.summary || '',
  ].filter(Boolean);

  return (
    <>
      <div className="space-y-6">
        <section className="relative overflow-hidden rounded-[28px] border border-border bg-gradient-to-br from-foreground/[0.04] via-background to-background p-6 shadow-[0_20px_80px_-40px_rgba(15,23,42,0.35)] sm:p-8">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(59,130,246,0.08),transparent_35%),radial-gradient(circle_at_bottom_left,rgba(16,185,129,0.08),transparent_30%)]" />
          <div className="relative grid gap-6 xl:grid-cols-[minmax(0,1.08fr)_360px]">
            <div className="space-y-5">
              <div className="inline-flex rounded-full border border-border bg-background/80 px-3 py-1 text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground backdrop-blur">
                {currentCopy.eyebrow}
              </div>

              <div className="space-y-3">
                <h2 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
                  {currentCopy.title}
                </h2>
                <p className="max-w-2xl text-sm leading-7 text-muted-foreground sm:text-base">
                  {currentCopy.subtitle}
                </p>
              </div>

              <div className="rounded-[24px] border border-border bg-background/80 p-5 shadow-sm backdrop-blur">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="text-sm font-semibold text-foreground">
                      {currentCopy.progressLabel}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {currentCopy.progressDescription}
                    </p>
                  </div>
                  <div className="rounded-full border border-border bg-background px-3 py-1 text-sm font-semibold text-foreground">
                    %{completionScore}
                  </div>
                </div>

                <div className="mt-4 h-3 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-foreground transition-all duration-500"
                    style={{width: progressWidth}}
                  />
                </div>
              </div>

              <div
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                className={[
                  'rounded-[26px] border border-dashed p-5 transition-all duration-200',
                  dragActive
                    ? 'border-foreground/40 bg-foreground/[0.04] shadow-[0_18px_50px_-36px_rgba(15,23,42,0.45)]'
                    : 'border-border bg-background/80 shadow-sm backdrop-blur',
                ].join(' ')}
              >
                {uploading ? (
                  <div className="space-y-4">
                    <div className="h-4 w-36 animate-pulse rounded-full bg-muted" />
                    <div className="h-3 w-full animate-pulse rounded-full bg-muted" />
                    <div className="h-3 w-4/5 animate-pulse rounded-full bg-muted" />
                    <div className="h-11 w-40 animate-pulse rounded-2xl bg-muted" />
                    <div className="text-sm text-muted-foreground">
                      {currentCopy.uploadLoadingTitle}
                    </div>
                    <p className="text-sm leading-6 text-muted-foreground">
                      {currentCopy.uploadLoadingSubtitle}
                    </p>
                  </div>
                ) : (
                  <div className="space-y-5">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="space-y-1">
                        <div className="text-base font-semibold text-foreground">
                          {currentCopy.uploadCardTitle}
                        </div>
                        <p className="text-sm leading-6 text-muted-foreground">
                          {currentCopy.uploadCardSubtitle}
                        </p>
                      </div>

                      <div
                        className={[
                          'inline-flex rounded-full px-3 py-1 text-xs font-medium',
                          latestCv
                            ? 'bg-emerald-500/10 text-emerald-700'
                            : 'bg-muted text-muted-foreground',
                        ].join(' ')}
                      >
                        {latestCv
                          ? currentCopy.uploadReadyBadge
                          : currentCopy.uploadMissingBadge}
                      </div>
                    </div>

                    <p className="text-sm leading-6 text-muted-foreground">
                      {currentCopy.uploadCardSupport}
                    </p>

                    <div className="rounded-2xl border border-border bg-background p-4">
                      <p className="text-sm text-foreground">
                        {currentCopy.dragHint}
                      </p>
                      <p className="mt-2 text-xs text-muted-foreground">
                        {currentCopy.supportedFormats}
                      </p>
                    </div>

                    <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="inline-flex h-11 items-center justify-center rounded-2xl bg-foreground px-5 text-sm font-medium text-background transition hover:opacity-95 sm:justify-center"
                      >
                        {latestCv
                          ? currentCopy.replaceButton
                          : currentCopy.uploadButton}
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setDrawerView('overview');
                          setDrawerOpen(true);
                        }}
                        disabled={!latestCv || uploading || applyLoading}
                        className="inline-flex h-11 items-center justify-center rounded-2xl border border-border bg-background px-5 text-sm font-medium text-foreground transition hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50 sm:justify-center"
                      >
                        {latestCv
                          ? currentCopy.analysisButton
                          : currentCopy.analysisButtonEmpty}
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setDrawerView('health');
                          setDrawerOpen(true);
                        }}
                        disabled={!latestCv || uploading || applyLoading}
                        className="inline-flex h-11 items-center justify-center rounded-2xl border border-border bg-background px-5 text-sm font-medium text-foreground transition hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50 sm:justify-center"
                      >
                        {currentCopy.healthButton}
                      </button>
                    </div>

                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,.doc,.docx,.png,.jpg,.jpeg"
                      onChange={handleFileInputChange}
                      className="hidden"
                    />

                    {uploadMessage ? (
                      <FeedbackBanner
                        tone={uploadMessageTone}
                        title={uploadMessageTone === 'success' ? currentCopy.uploadSuccessTitle : currentCopy.uploadSuccessTitle}
                        onDismiss={() => setUploadMessage(null)}
                      >
                        {uploadMessage}
                      </FeedbackBanner>
                    ) : null}

                    {drawerError && !drawerOpen ? (
                      <FeedbackBanner tone="error" onDismiss={() => setDrawerError(null)}>
                        {drawerError}
                      </FeedbackBanner>
                    ) : null}
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-4">
              {quickStats.map((item) => (
                <QuickStat key={item.label} label={item.label} value={item.value} />
              ))}

              <div className="rounded-[24px] border border-border bg-background/80 p-5 shadow-sm backdrop-blur">
                <div className="text-sm font-semibold text-foreground">
                  {currentCopy.updatedFromCvLabel}
                </div>
                <div className="mt-2 text-sm text-muted-foreground">
                  {latestCv?.parsed_at
                    ? formatDateLabel(latestCv.parsed_at)
                    : currentCopy.uploadMissingBadge}
                </div>
                {highlights.length > 0 ? (
                  <ul className="mt-4 space-y-2 text-sm leading-6 text-muted-foreground">
                    {highlights.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            </div>
          </div>
        </section>

        <section className="space-y-3">
          <div>
            <h3 className="text-lg font-semibold tracking-tight text-foreground">
              {currentCopy.summaryTitle}
            </h3>
            <p className="mt-1 text-sm leading-6 text-muted-foreground">
              {currentCopy.summarySubtitle}
            </p>
          </div>

          <div className="grid gap-4 xl:grid-cols-2">
            <SummaryCard title={currentCopy.profileCardTitle}>
              <div className="space-y-3">
                {profileSummaryLines.length > 0 ? (
                  profileSummaryLines.map((line) => (
                    <p key={line} className="text-sm leading-7 text-muted-foreground">
                      {line}
                    </p>
                  ))
                ) : (
                  <p className="text-sm leading-6 text-muted-foreground">
                    {currentCopy.noSummaryYet}
                  </p>
                )}
              </div>
            </SummaryCard>

            <SummaryCard title={currentCopy.contactCardTitle}>
              <div className="space-y-3 text-sm text-muted-foreground">
                <div>
                  <span className="font-medium text-foreground">{profile.full_name || '—'}</span>
                </div>
                <div>{profile.email}</div>
                <div>{profile.phone || '—'}</div>
                <div>
                  <span className="font-medium text-foreground">
                    {currentCopy.preferredLocationsLabel}:{' '}
                  </span>
                  {joinOrFallback(profile.preferred_locations, '—')}
                </div>
                <div>
                  <span className="font-medium text-foreground">
                    {currentCopy.remotePreferenceLabel}:{' '}
                  </span>
                  {resolveRemotePreferenceLabel(
                    profile.remote_preference,
                    currentCopy
                  ) || '—'}
                </div>
              </div>
            </SummaryCard>

            <SummaryCard title={currentCopy.skillsCardTitle}>
              {profile.skills.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {profile.skills.slice(0, 16).map((skill) => (
                    <span
                      key={skill}
                      className="rounded-full border border-border bg-muted/40 px-3 py-1 text-sm text-foreground"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-sm leading-6 text-muted-foreground">
                  {currentCopy.noSkillsYet}
                </p>
              )}
            </SummaryCard>

            <SummaryCard title={currentCopy.experienceCardTitle}>
              {profile.experience_entries.length > 0 ? (
                <div className="space-y-3">
                  {profile.experience_entries.slice(0, 3).map((entry) => (
                    <div
                      key={`${entry.title}-${entry.company_name}-${entry.display_order}`}
                      className="rounded-2xl border border-border bg-muted/20 p-4"
                    >
                      <div className="text-sm font-medium text-foreground">
                        {entry.title}
                      </div>
                      <div className="mt-1 text-sm text-muted-foreground">
                        {joinOrFallback(
                          [entry.company_name || '', [entry.start_year, entry.end_year].filter(Boolean).join(' – ')].filter(Boolean),
                          '—'
                        )}
                      </div>
                      {entry.summary ? (
                        <p className="mt-2 text-sm leading-6 text-muted-foreground">
                          {entry.summary}
                        </p>
                      ) : null}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm leading-6 text-muted-foreground">
                  {currentCopy.noExperienceYet}
                </p>
              )}
            </SummaryCard>

            <SummaryCard title={currentCopy.languageCardTitle}>
              {profile.language_entries.length > 0 ? (
                <div className="space-y-3">
                  {profile.language_entries.slice(0, 4).map((entry) => (
                    <div
                      key={`${entry.language_name}-${entry.display_order}`}
                      className="rounded-2xl border border-border bg-muted/20 p-4"
                    >
                      <div className="text-sm font-medium text-foreground">
                        {entry.language_name}
                      </div>
                      <div className="mt-1 text-sm text-muted-foreground">
                        {joinOrFallback(
                          [entry.proficiency_level || '', entry.notes || ''].filter(Boolean),
                          '—'
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm leading-6 text-muted-foreground">
                  {currentCopy.noLanguagesYet}
                </p>
              )}
            </SummaryCard>

            <SummaryCard title={currentCopy.certificatesCardTitle}>
              {profile.language_certificates.length > 0 ? (
                <div className="space-y-3">
                  {profile.language_certificates.slice(0, 4).map((certificate) => (
                    <div
                      key={`${certificate.certificate_name}-${certificate.id ?? certificate.file_name ?? 'certificate'}`}
                      className="rounded-2xl border border-border bg-muted/20 p-4"
                    >
                      <div className="text-sm font-medium text-foreground">
                        {certificate.certificate_name}
                      </div>
                      <div className="mt-1 text-sm text-muted-foreground">
                        {certificate.issuer_name || '—'}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm leading-6 text-muted-foreground">
                  {currentCopy.noCertificatesYet}
                </p>
              )}
            </SummaryCard>
          </div>
        </section>
      </div>

      <div
        className={[
          'fixed inset-0 z-40 transition-all duration-300',
          drawerOpen
            ? 'pointer-events-auto bg-black/20 backdrop-blur-[3px]'
            : 'pointer-events-none bg-transparent backdrop-blur-none',
        ].join(' ')}
        onClick={() => setDrawerOpen(false)}
      />

      <aside
        ref={drawerRef}
        data-coresift-right-surface={drawerOpen ? 'open' : 'closed'}
        data-right-drawer={drawerOpen ? 'open' : 'closed'}
        data-drawer-side="right"
        data-state={drawerOpen ? 'open' : 'closed'}
        className={[
          'fixed right-0 top-0 z-50 h-full w-full max-w-xl transform border-l border-border bg-background shadow-[0_30px_80px_-40px_rgba(15,23,42,0.5)] transition-transform duration-300',
          drawerOpen ? 'translate-x-0' : 'translate-x-full',
        ].join(' ')}
        aria-hidden={!drawerOpen}
      >
        <div className="flex h-full flex-col">
          <div className="flex items-start justify-between gap-4 border-b border-border px-6 py-5">
            <div className="space-y-1">
              <h3 className="text-lg font-semibold tracking-tight text-foreground">
                {currentCopy.analysisDrawerTitle}
              </h3>
              <p className="text-sm leading-6 text-muted-foreground">
                {currentCopy.analysisDrawerSubtitle}
              </p>
            </div>

            <button
              type="button"
              onClick={() => setDrawerOpen(false)}
              className="inline-flex h-10 items-center justify-center rounded-2xl border border-border bg-background px-4 text-sm font-medium text-foreground transition hover:bg-muted"
            >
              {currentCopy.close}
            </button>
          </div>

          <div className="border-b border-border px-6 py-4">
            <div className="inline-flex rounded-full border border-border bg-muted/20 p-1">
              <button
                type="button"
                onClick={() => setDrawerView('overview')}
                className={`rounded-full px-4 py-2 text-sm font-medium transition ${drawerView === 'overview' ? 'bg-foreground text-background' : 'text-muted-foreground hover:text-foreground'}`}
              >
                {currentCopy.analysisButton}
              </button>
              <button
                type="button"
                onClick={() => setDrawerView('health')}
                className={`rounded-full px-4 py-2 text-sm font-medium transition ${drawerView === 'health' ? 'bg-foreground text-background' : 'text-muted-foreground hover:text-foreground'}`}
              >
                {currentCopy.healthButton}
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto px-6 py-6">
            {drawerView === 'health' ? (
              <div className="space-y-5">
                <section className="rounded-3xl border border-border bg-background p-5">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <div className="text-sm font-semibold text-foreground">
                        {locale === 'tr' ? 'CV ve profil sağlığı' : locale === 'de' ? 'CV- und Profilgesundheit' : 'CV and profile health'}
                      </div>
                      <p className="mt-1 text-sm leading-6 text-muted-foreground">
                        {locale === 'tr' ? 'Eksik alanları, güçlü yönleri ve hızlı iyileştirme fırsatlarını tek panelde gör.' : locale === 'de' ? 'Sieh fehlende Bereiche, starke Seiten und schnelle Verbesserungen in einem Panel.' : 'See missing areas, strong points, and quick improvements in one panel.'}
                      </p>
                    </div>
                    <div className="rounded-full border border-border bg-muted/30 px-4 py-2 text-sm font-semibold text-foreground">
                      %{Math.round(completionScore)}
                    </div>
                  </div>

                  <div className="mt-4 grid gap-3 md:grid-cols-2">
                    <div className="rounded-2xl border border-border bg-muted/20 p-4">
                      <div className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                        {locale === 'tr' ? 'Tamamlanan alanlar' : locale === 'de' ? 'Erledigte Bereiche' : 'Completed areas'}
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {profile.completeness.completed_items.length > 0 ? profile.completeness.completed_items.map((item) => (
                          <span key={item} className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
                            {item}
                          </span>
                        )) : (
                          <span className="text-sm text-muted-foreground">{currentCopy.analysisDrawerEmpty}</span>
                        )}
                      </div>
                    </div>

                    <div className="rounded-2xl border border-border bg-muted/20 p-4">
                      <div className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                        {locale === 'tr' ? 'Güçlendirilecek alanlar' : locale === 'de' ? 'Zu stärkende Bereiche' : 'Areas to strengthen'}
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {profile.completeness.missing_items.length > 0 ? profile.completeness.missing_items.map((item) => (
                          <span key={item} className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">
                            {item}
                          </span>
                        )) : (
                          <span className="text-sm text-muted-foreground">{locale === 'tr' ? 'Belirgin bir eksik alan görünmüyor.' : locale === 'de' ? 'Aktuell sind keine klaren Lücken sichtbar.' : 'No major missing area is visible right now.'}</span>
                        )}
                      </div>
                    </div>
                  </div>
                </section>

                {healthSections.map((section) => (
                  <section key={section.title} className="rounded-3xl border border-border bg-background p-5">
                    <div className="text-sm font-semibold text-foreground">{section.title}</div>
                    <div className="mt-4 space-y-3">
                      {section.items.length > 0 ? section.items.map((item) => (
                        <div key={item.id} className="rounded-2xl border border-border bg-muted/20 p-4">
                          <div className="text-sm font-semibold text-foreground">{item.title}</div>
                          <p className="mt-1 text-sm leading-6 text-muted-foreground">{item.description}</p>
                        </div>
                      )) : (
                        <div className="rounded-2xl border border-dashed border-border px-4 py-4 text-sm text-muted-foreground">
                          {currentCopy.analysisDrawerEmpty}
                        </div>
                      )}
                    </div>
                  </section>
                ))}
              </div>
            ) : drawerLoading ? (
              <DrawerSkeleton />
            ) : !plan ? (
              <div className="rounded-3xl border border-border bg-background p-5 text-sm leading-6 text-muted-foreground">
                {currentCopy.analysisDrawerEmpty}
              </div>
            ) : (
              <div className="space-y-5">
                {plan.extraction_metadata.needs_manual_review ? (
                  <div className="rounded-3xl border border-amber-200 bg-amber-50 p-5">
                    <div className="text-sm font-semibold text-amber-900">
                      {currentCopy.helperReviewTitle}
                    </div>
                    <p className="mt-2 text-sm leading-6 text-amber-800">
                      {currentCopy.helperReviewBody}
                    </p>
                    <label className="mt-4 flex items-start gap-3 text-sm text-amber-900">
                      <input
                        type="checkbox"
                        checked={manualReviewAcknowledged}
                        onChange={(event) =>
                          setManualReviewAcknowledged(event.target.checked)
                        }
                        className="mt-1 h-4 w-4 rounded border-amber-300"
                      />
                      <span>{currentCopy.helperReviewCheckbox}</span>
                    </label>
                  </div>
                ) : null}

                {highlights.length > 0 ? (
                  <section className="rounded-3xl border border-border bg-background p-5">
                    <div className="text-sm font-semibold text-foreground">
                      {currentCopy.analysisHighlightsTitle}
                    </div>
                    <ul className="mt-3 space-y-2 text-sm leading-6 text-muted-foreground">
                      {highlights.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </section>
                ) : null}

                {notes.length > 0 ? (
                  <section className="rounded-3xl border border-border bg-background p-5">
                    <div className="text-sm font-semibold text-foreground">
                      {currentCopy.analysisNotesTitle}
                    </div>
                    <ul className="mt-3 space-y-2 text-sm leading-6 text-muted-foreground">
                      {notes.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </section>
                ) : null}

                <section className="rounded-3xl border border-border bg-background p-5">
                  <div className="flex items-center justify-between gap-4">
                    <div className="text-sm font-semibold text-foreground">
                      {currentCopy.analysisRecommendationsTitle}
                    </div>
                    <div className="rounded-full border border-border bg-muted/30 px-3 py-1 text-xs font-medium text-muted-foreground">
                      {currentCopy.selectedCountLabel}: {selectedCount}
                    </div>
                  </div>

                  <div className="mt-4 space-y-4">
                    {suggestionCards.length === 0 ? (
                      <div className="rounded-2xl border border-border bg-muted/20 px-4 py-4 text-sm text-muted-foreground">
                        {currentCopy.analysisDrawerEmpty}
                      </div>
                    ) : (
                      suggestionCards.map((card) => (
                        <div
                          key={card.id}
                          className={[
                            'rounded-3xl border p-5 transition-all duration-200',
                            card.selected
                              ? 'border-foreground/20 bg-foreground/[0.03] shadow-[0_16px_40px_-32px_rgba(15,23,42,0.35)]'
                              : 'border-border bg-background hover:border-foreground/15 hover:bg-muted/[0.18]',
                          ].join(' ')}
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div className="space-y-1">
                              <div className="text-sm font-semibold text-foreground">
                                {card.title}
                              </div>
                              <p className="text-sm leading-6 text-muted-foreground">
                                {card.description}
                              </p>
                            </div>

                            <input
                              type="checkbox"
                              checked={card.selected}
                              onChange={() => {
                                if (card.category === 'scalar') {
                                  toggleScalarField(card.fieldName);
                                  return;
                                }
                                if (card.category === 'list') {
                                  toggleListField(card.fieldName);
                                  return;
                                }
                                if (card.category === 'education') {
                                  toggleIndexedField('education', card.index);
                                  return;
                                }
                                if (card.category === 'experience') {
                                  toggleIndexedField('experience', card.index);
                                  return;
                                }
                                toggleIndexedField('language', card.index);
                              }}
                              className="mt-1 h-4 w-4 rounded border-border"
                            />
                          </div>

                          <div className="mt-4 rounded-2xl border border-border bg-muted/20 p-4">
                            <div className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                              {currentCopy.suggestionPreviewTitle}
                            </div>

                            {card.category === 'scalar' ? (
                              <div className="mt-3 grid gap-3">
                                <div>
                                  <div className="text-xs font-medium text-muted-foreground">
                                    {currentCopy.suggestionCurrentLabel}
                                  </div>
                                  <div className="mt-1 text-sm text-foreground">
                                    {card.currentValue || '—'}
                                  </div>
                                </div>
                                <div>
                                  <div className="text-xs font-medium text-muted-foreground">
                                    {currentCopy.suggestionProposedLabel}
                                  </div>
                                  <div className="mt-1 text-sm text-foreground">
                                    {card.suggestedValue || '—'}
                                  </div>
                                </div>
                              </div>
                            ) : null}

                            {card.category === 'list' ? (
                              <div className="mt-3 grid gap-3">
                                <div>
                                  <div className="text-xs font-medium text-muted-foreground">
                                    {currentCopy.suggestionCurrentLabel}
                                  </div>
                                  <div className="mt-1 text-sm text-foreground">
                                    {joinOrFallback(card.currentValue, '—')}
                                  </div>
                                </div>
                                <div>
                                  <div className="text-xs font-medium text-muted-foreground">
                                    {currentCopy.suggestionAddedItemsLabel}
                                  </div>
                                  <div className="mt-1 text-sm text-foreground">
                                    {joinOrFallback(card.addedItems, '—')}
                                  </div>
                                </div>
                              </div>
                            ) : null}

                            {card.category === 'education' ||
                            card.category === 'experience' ||
                            card.category === 'language' ? (
                              <div className="mt-3 grid gap-3">
                                <div>
                                  <div className="text-xs font-medium text-muted-foreground">
                                    {currentCopy.suggestionCurrentLabel}
                                  </div>
                                  <div className="mt-1 text-sm text-foreground">
                                    {card.currentValue || '—'}
                                  </div>
                                </div>
                                <div>
                                  <div className="text-xs font-medium text-muted-foreground">
                                    {currentCopy.suggestionProposedLabel}
                                  </div>
                                  <div className="mt-1 text-sm text-foreground">
                                    {card.suggestedValue}
                                  </div>
                                </div>
                              </div>
                            ) : null}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </section>

                {drawerError ? (
                  <FeedbackBanner tone="error" onDismiss={() => setDrawerError(null)}>
                    {drawerError}
                  </FeedbackBanner>
                ) : null}

                {applyMessage ? (
                  <FeedbackBanner tone={applyMessageTone} onDismiss={() => setApplyMessage(null)}>
                    {applyMessage}
                  </FeedbackBanner>
                ) : null}
              </div>
            )}
          </div>

          <div className="border-t border-border px-6 py-5">
            <button
              type="button"
              onClick={() => void handleApplySelected()}
              disabled={
                applyLoading ||
                selectedCount === 0 ||
                (plan?.extraction_metadata.needs_manual_review &&
                  !manualReviewAcknowledged)
              }
              className="inline-flex h-12 w-full items-center justify-center rounded-2xl bg-foreground px-5 text-sm font-medium text-background transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {applyLoading
                ? currentCopy.applyButtonLoading
                : currentCopy.applyButton}
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}