import type {SupportedLocale} from '@/types/user';

export type CvUploadCopy = {
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

export const cvUploadCopy: Record<SupportedLocale, CvUploadCopy> = {
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
