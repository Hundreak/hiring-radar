import type {SupportedLocale} from '@/types/user';

export type ProfileWorkspaceCopy = {
  eyebrow: string;
  title: string;
  subtitle: string;
  loadingTitle: string;
  loadingBody: string;
  genericError: string;
  profileCompletion: string;
  profilePhotoTitle: string;
  profilePhotoBody: string;
  uploadProfilePhoto: string;
  uploadingProfilePhoto: string;
  profilePhotoSaved: string;
  profileOverviewTitle: string;
  basicsTitle: string;
  basicsBody: string;
  preferencesTitle: string;
  preferencesBody: string;
  experiencesTitle: string;
  educationTitle: string;
  languagesTitle: string;
  skillsTitle: string;
  healthTitle: string;
  healthBody: string;
  saveBasics: string;
  savePreferences: string;
  saving: string;
  savedBasics: string;
  savedPreferences: string;
  savedExperience: string;
  deletedExperience: string;
  savedEducation: string;
  deletedEducation: string;
  savedLanguage: string;
  savedLanguageWithDocument: string;
  savedLanguageWithoutDocument: string;
  deletedLanguage: string;
  savedSkill: string;
  savedSkillWithEvidence: string;
  savedSkillWithoutEvidence: string;
  deletedSkill: string;
  addExperience: string;
  addEducation: string;
  addLanguage: string;
  addSkill: string;
  edit: string;
  update: string;
  save: string;
  cancel: string;
  delete: string;
  deleting: string;
  noExperiences: string;
  noEducation: string;
  noLanguages: string;
  noSkills: string;
  fullName: string;
  email: string;
  phone: string;
  headline: string;
  summary: string;
  targetRoles: string;
  preferredLocations: string;
  workModes: string;
  salaryExpectation: string;
  relocation: string;
  relocationUnset: string;
  relocationYes: string;
  relocationNo: string;
  experienceRole: string;
  experienceCompany: string;
  experienceStart: string;
  experienceEnd: string;
  experienceCurrent: string;
  experienceDescription: string;
  educationInstitution: string;
  educationInstitutionHint: string;
  educationInstitutionFallback: string;
  educationDegree: string;
  educationField: string;
  educationFieldHint: string;
  educationFieldFallback: string;
  educationStart: string;
  educationEnd: string;
  languageName: string;
  languageLevel: string;
  languageCertificate: string;
  languageDocument: string;
  languageIssuer: string;
  languageDocumentSaved: string;
  skillName: string;
  skillCategory: string;
  skillProficiency: string;
  skillYears: string;
  skillEvidenceNote: string;
  skillEvidenceFile: string;
  skillEvidenceSaved: string;
  skillCategoriesTitle: string;
  noProfilePhoto: string;
  currentBadge: string;
  previewEmpty: string;
  remote: string;
  hybrid: string;
  onsite: string;
  sectionDone: string;
  sectionPartial: string;
  sectionMissing: string;
  manualEntryNote: string;
  healthDrawerButton: string;
  healthDrawerTitle: string;
  healthDrawerSubtitle: string;
  healthDrawerCompletionLabel: string;
  healthDrawerStrongAreas: string;
  healthDrawerFocusAreas: string;
  healthDrawerSuggestions: string;
  healthDrawerEmpty: string;
};

export const profileWorkspaceCopy: Record<SupportedLocale, ProfileWorkspaceCopy> = {
  tr: {
    eyebrow: 'Profil alanı',
    title: 'Profilini düzenle ve güçlendir',
    subtitle:
      'Temel bilgilerini, deneyimlerini, eğitimini ve becerilerini sade bir akışla yönet. Yaptığın her değişiklik aynı profil kaynağına güvenli şekilde yazılır.',
    loadingTitle: 'Profil hazırlanıyor',
    loadingBody: 'Son bilgiler ve CV alanı yükleniyor.',
    genericError: 'İşlem tamamlanamadı. Lütfen tekrar dene.',
    profileCompletion: 'Profil doluluğu',
    profilePhotoTitle: 'Profil fotoğrafı',
    profilePhotoBody: 'Kullanıcı menüsünde ve profil alanında görünen fotoğrafını güncelle.',
    uploadProfilePhoto: 'Profil Fotoğrafı Yükle',
    uploadingProfilePhoto: 'Profil fotoğrafı yükleniyor...',
    profilePhotoSaved: 'Profil fotoğrafın güncellendi.',
    profileOverviewTitle: 'Öne çıkan profil bilgileri',
    basicsTitle: 'Temel bilgiler',
    basicsBody: 'Adını, iletişim bilgilerini ve kısa profil anlatımını güncelle.',
    preferencesTitle: 'Hedefler ve tercihler',
    preferencesBody: 'Aradığın rolü, lokasyonları ve çalışma düzenini belirle.',
    experiencesTitle: 'Deneyimler',
    educationTitle: 'Eğitim',
    languagesTitle: 'Diller',
    skillsTitle: 'Beceriler',
    healthTitle: 'Profil sağlığı',
    healthBody: 'Hangi alanların tamamlandığını ve nerede güçlendirme gerektiğini takip et.',
    saveBasics: 'Temel bilgileri kaydet',
    savePreferences: 'Tercihleri kaydet',
    saving: 'Kaydediliyor...',
    savedBasics: 'Temel bilgiler güncellendi.',
    savedPreferences: 'Tercihler güncellendi.',
    savedExperience: 'Deneyim kaydedildi.',
    deletedExperience: 'Deneyim kaldırıldı.',
    savedEducation: 'Eğitim bilgisi kaydedildi.',
    deletedEducation: 'Eğitim kaldırıldı.',
    savedLanguage: 'Dil bilgisi kaydedildi.',
    savedLanguageWithDocument: 'Dil bilgisi ve belgesi kaydedildi.',
    savedLanguageWithoutDocument: 'Dil bilgisi kaydedildi. Belge yüklemesi tamamlanmadı; yeniden deneyebilirsin.',
    deletedLanguage: 'Dil kaldırıldı.',
    savedSkill: 'Beceri kaydedildi.',
    savedSkillWithEvidence: 'Beceri ve kanıt dosyası kaydedildi.',
    savedSkillWithoutEvidence: 'Beceri kaydedildi. Kanıt dosyası yüklenemedi; yeniden deneyebilirsin.',
    deletedSkill: 'Beceri kaldırıldı.',
    addExperience: 'Deneyim ekle',
    addEducation: 'Eğitim ekle',
    addLanguage: 'Dil ekle',
    addSkill: 'Beceri ekle',
    edit: 'Düzenle',
    update: 'Güncelle',
    save: 'Kaydet',
    cancel: 'İptal',
    delete: 'Sil',
    deleting: 'Siliniyor...',
    noExperiences: 'Henüz deneyim eklemedin.',
    noEducation: 'Henüz eğitim eklemedin.',
    noLanguages: 'Henüz dil eklemedin.',
    noSkills: 'Henüz beceri eklemedin.',
    fullName: 'Ad Soyad',
    email: 'E-posta',
    phone: 'Telefon',
    headline: 'Profil başlığı',
    summary: 'Kısa özet',
    targetRoles: 'Hedef roller',
    preferredLocations: 'Tercih edilen lokasyonlar',
    workModes: 'Çalışma şekli',
    salaryExpectation: 'Ücret beklentisi',
    relocation: 'Taşınma durumu',
    relocationUnset: 'Şimdilik belirtmek istemiyorum',
    relocationYes: 'Gerekirse taşınabilirim',
    relocationNo: 'Taşınmayı düşünmüyorum',
    experienceRole: 'Rol / Pozisyon',
    experienceCompany: 'Şirket',
    experienceStart: 'Başlangıç yılı',
    experienceEnd: 'Bitiş yılı',
    experienceCurrent: 'Bu rolde hâlâ çalışıyorum',
    experienceDescription: 'Kısa açıklama',
    educationInstitution: 'Üniversite / Kurum',
    educationInstitutionHint: 'Listeden seçebilir veya doğrudan yazabilirsin.',
    educationInstitutionFallback: 'Üniversite adı yaz',
    educationDegree: 'Derece / Program',
    educationField: 'Bölüm',
    educationFieldHint: 'Seçili üniversite için bölüm listesi varsa aşağıda görünür.',
    educationFieldFallback: 'Bölüm adı yaz',
    educationStart: 'Başlangıç yılı',
    educationEnd: 'Bitiş yılı',
    languageName: 'Dil',
    languageLevel: 'Seviye',
    languageCertificate: 'Belge adı',
    languageDocument: 'Sertifika / Belge Yükle',
    languageIssuer: 'Belgeyi veren kurum',
    languageDocumentSaved: 'Dil belgesi yüklendi.',
    skillName: 'Beceri adı',
    skillCategory: 'Kategori',
    skillProficiency: 'Seviye / Yetkinlik notu',
    skillYears: 'Deneyim yılı',
    skillEvidenceNote: 'Açıklama / kanıt notu',
    skillEvidenceFile: 'Belge / Kanıt Yükle',
    skillEvidenceSaved: 'Beceri kanıtı güncellendi.',
    skillCategoriesTitle: 'Kategori seç',
    noProfilePhoto: 'Henüz profil fotoğrafı eklenmedi.',
    currentBadge: 'Güncel',
    previewEmpty: 'Henüz içerik görünmüyor.',
    remote: 'Uzaktan',
    hybrid: 'Hibrit',
    onsite: 'Ofiste',
    sectionDone: 'Tamam',
    sectionPartial: 'Kısmi',
    sectionMissing: 'Eksik',
    manualEntryNote: 'Resmî veri kaynağına tam bağlanamadığı alanlarda serbest girişe de izin verilir.',
    healthDrawerButton: 'Profil sağlığını gör',
    healthDrawerTitle: 'Profil sağlığı',
    healthDrawerSubtitle: 'Profilinin güçlü taraflarını ve hızlıca güçlendirebileceğin alanları tek panelden takip et.',
    healthDrawerCompletionLabel: 'Genel görünüm',
    healthDrawerStrongAreas: 'Güçlü görünen alanlar',
    healthDrawerFocusAreas: 'Bir dokunuşla güçlenecek alanlar',
    healthDrawerSuggestions: 'Kısa iyileştirme önerileri',
    healthDrawerEmpty: 'Şimdilik ek öneri görünmüyor.',
  },
  en: {
    eyebrow: 'Profile workspace',
    title: 'Edit and strengthen your profile',
    subtitle: 'Manage your core details, experience, education, and skills in one calm workspace.',
    loadingTitle: 'Preparing your profile',
    loadingBody: 'Latest profile and CV data are loading.',
    genericError: 'The request could not be completed. Please try again.',
    profileCompletion: 'Profile completion',
    profilePhotoTitle: 'Profile photo',
    profilePhotoBody: 'Update the image shown in your user menu and profile workspace.',
    uploadProfilePhoto: 'Upload Profile Photo',
    uploadingProfilePhoto: 'Uploading profile photo...',
    profilePhotoSaved: 'Your profile photo has been updated.',
    profileOverviewTitle: 'Profile highlights',
    basicsTitle: 'Core details',
    basicsBody: 'Update your name, contact details, and short summary.',
    preferencesTitle: 'Goals and preferences',
    preferencesBody: 'Set your target roles, locations, and work preferences.',
    experiencesTitle: 'Experience',
    educationTitle: 'Education',
    languagesTitle: 'Languages',
    skillsTitle: 'Skills',
    healthTitle: 'Profile health',
    healthBody: 'Track what is complete and where you can improve next.',
    saveBasics: 'Save core details',
    savePreferences: 'Save preferences',
    saving: 'Saving...',
    savedBasics: 'Core details updated.',
    savedPreferences: 'Preferences updated.',
    savedExperience: 'Experience saved.',
    deletedExperience: 'Experience removed.',
    savedEducation: 'Education saved.',
    deletedEducation: 'Education removed.',
    savedLanguage: 'Language saved.',
    savedLanguageWithDocument: 'Language and document saved.',
    savedLanguageWithoutDocument: 'Language saved. The document could not be uploaded; you can try again.',
    deletedLanguage: 'Language removed.',
    savedSkill: 'Skill saved.',
    savedSkillWithEvidence: 'Skill and proof file saved.',
    savedSkillWithoutEvidence: 'Skill saved. The proof file could not be uploaded; you can try again.',
    deletedSkill: 'Skill removed.',
    addExperience: 'Add experience',
    addEducation: 'Add education',
    addLanguage: 'Add language',
    addSkill: 'Add skill',
    edit: 'Edit',
    update: 'Update',
    save: 'Save',
    cancel: 'Cancel',
    delete: 'Delete',
    deleting: 'Deleting...',
    noExperiences: 'No experience entries yet.',
    noEducation: 'No education entries yet.',
    noLanguages: 'No language entries yet.',
    noSkills: 'No skill entries yet.',
    fullName: 'Full name',
    email: 'Email',
    phone: 'Phone',
    headline: 'Profile headline',
    summary: 'Short summary',
    targetRoles: 'Target roles',
    preferredLocations: 'Preferred locations',
    workModes: 'Work style',
    salaryExpectation: 'Salary expectation',
    relocation: 'Relocation',
    relocationUnset: 'Prefer not to say yet',
    relocationYes: 'Open to relocation',
    relocationNo: 'Not considering relocation',
    experienceRole: 'Role / Title',
    experienceCompany: 'Company',
    experienceStart: 'Start year',
    experienceEnd: 'End year',
    experienceCurrent: 'I still work here',
    experienceDescription: 'Short description',
    educationInstitution: 'University / School',
    educationInstitutionHint: 'Choose from the list or type your own entry.',
    educationInstitutionFallback: 'Type university name',
    educationDegree: 'Degree / Program',
    educationField: 'Department',
    educationFieldHint: 'Department suggestions appear when available.',
    educationFieldFallback: 'Type department name',
    educationStart: 'Start year',
    educationEnd: 'End year',
    languageName: 'Language',
    languageLevel: 'Level',
    languageCertificate: 'Document name',
    languageDocument: 'Upload Certificate / Document',
    languageIssuer: 'Issuer',
    languageDocumentSaved: 'Language document uploaded.',
    skillName: 'Skill name',
    skillCategory: 'Category',
    skillProficiency: 'Level / proficiency note',
    skillYears: 'Years of experience',
    skillEvidenceNote: 'Description / proof note',
    skillEvidenceFile: 'Upload Proof / Document',
    skillEvidenceSaved: 'Skill proof updated.',
    skillCategoriesTitle: 'Choose a category',
    noProfilePhoto: 'No profile photo yet.',
    currentBadge: 'Current',
    previewEmpty: 'Nothing visible yet.',
    remote: 'Remote',
    hybrid: 'Hybrid',
    onsite: 'On-site',
    sectionDone: 'Done',
    sectionPartial: 'Partial',
    sectionMissing: 'Missing',
    manualEntryNote: 'Where official catalog data is incomplete, manual entry remains available.',
    healthDrawerButton: 'View profile health',
    healthDrawerTitle: 'Profile health',
    healthDrawerSubtitle: 'Track the areas that already look strong and the ones that would benefit from a quick touch.',
    healthDrawerCompletionLabel: 'Overall picture',
    healthDrawerStrongAreas: 'Strong areas',
    healthDrawerFocusAreas: 'Areas to strengthen',
    healthDrawerSuggestions: 'Quick improvement ideas',
    healthDrawerEmpty: 'No additional suggestion is visible right now.',
  },
  de: {
    eyebrow: 'Profilbereich',
    title: 'Profil bearbeiten und stärken',
    subtitle: 'Verwalte deine Kerninformationen, Erfahrungen, Ausbildung und Skills in einem ruhigen Arbeitsbereich.',
    loadingTitle: 'Profil wird vorbereitet',
    loadingBody: 'Die neuesten Profil- und CV-Daten werden geladen.',
    genericError: 'Die Aktion konnte nicht abgeschlossen werden. Bitte versuche es erneut.',
    profileCompletion: 'Profilfortschritt',
    profilePhotoTitle: 'Profilfoto',
    profilePhotoBody: 'Aktualisiere das Bild, das im Nutzermenü und im Profilbereich angezeigt wird.',
    uploadProfilePhoto: 'Profilfoto hochladen',
    uploadingProfilePhoto: 'Profilfoto wird hochgeladen...',
    profilePhotoSaved: 'Dein Profilfoto wurde aktualisiert.',
    profileOverviewTitle: 'Profil auf einen Blick',
    basicsTitle: 'Grunddaten',
    basicsBody: 'Aktualisiere Name, Kontakt und Kurzprofil.',
    preferencesTitle: 'Ziele und Präferenzen',
    preferencesBody: 'Lege Zielrollen, Orte und Arbeitsweise fest.',
    experiencesTitle: 'Erfahrungen',
    educationTitle: 'Ausbildung',
    languagesTitle: 'Sprachen',
    skillsTitle: 'Skills',
    healthTitle: 'Profilstatus',
    healthBody: 'Verfolge, was vollständig ist und wo du noch stärken kannst.',
    saveBasics: 'Grunddaten speichern',
    savePreferences: 'Präferenzen speichern',
    saving: 'Speichern...',
    savedBasics: 'Grunddaten aktualisiert.',
    savedPreferences: 'Präferenzen aktualisiert.',
    savedExperience: 'Erfahrung gespeichert.',
    deletedExperience: 'Erfahrung entfernt.',
    savedEducation: 'Ausbildung gespeichert.',
    deletedEducation: 'Ausbildung entfernt.',
    savedLanguage: 'Sprache gespeichert.',
    savedLanguageWithDocument: 'Sprache und Dokument gespeichert.',
    savedLanguageWithoutDocument: 'Sprache gespeichert. Das Dokument konnte nicht hochgeladen werden; du kannst es erneut versuchen.',
    deletedLanguage: 'Sprache entfernt.',
    savedSkill: 'Skill gespeichert.',
    savedSkillWithEvidence: 'Skill und Nachweisdatei gespeichert.',
    savedSkillWithoutEvidence: 'Skill gespeichert. Die Nachweisdatei konnte nicht hochgeladen werden; du kannst es erneut versuchen.',
    deletedSkill: 'Skill entfernt.',
    addExperience: 'Erfahrung hinzufügen',
    addEducation: 'Ausbildung hinzufügen',
    addLanguage: 'Sprache hinzufügen',
    addSkill: 'Skill hinzufügen',
    edit: 'Bearbeiten',
    update: 'Aktualisieren',
    save: 'Speichern',
    cancel: 'Abbrechen',
    delete: 'Löschen',
    deleting: 'Wird gelöscht...',
    noExperiences: 'Noch keine Erfahrungseinträge.',
    noEducation: 'Noch keine Ausbildungseinträge.',
    noLanguages: 'Noch keine Spracheinträge.',
    noSkills: 'Noch keine Skills eingetragen.',
    fullName: 'Vollständiger Name',
    email: 'E-Mail',
    phone: 'Telefon',
    headline: 'Profilüberschrift',
    summary: 'Kurzprofil',
    targetRoles: 'Zielrollen',
    preferredLocations: 'Bevorzugte Standorte',
    workModes: 'Arbeitsweise',
    salaryExpectation: 'Gehaltswunsch',
    relocation: 'Umzug',
    relocationUnset: 'Noch offen',
    relocationYes: 'Umzugsbereit',
    relocationNo: 'Kein Umzug geplant',
    experienceRole: 'Rolle / Position',
    experienceCompany: 'Unternehmen',
    experienceStart: 'Startjahr',
    experienceEnd: 'Endjahr',
    experienceCurrent: 'Ich arbeite noch dort',
    experienceDescription: 'Kurze Beschreibung',
    educationInstitution: 'Universität / Einrichtung',
    educationInstitutionHint: 'Aus der Liste wählen oder frei eingeben.',
    educationInstitutionFallback: 'Universität eingeben',
    educationDegree: 'Abschluss / Programm',
    educationField: 'Studienfach',
    educationFieldHint: 'Fachvorschläge erscheinen, wenn verfügbar.',
    educationFieldFallback: 'Studienfach eingeben',
    educationStart: 'Startjahr',
    educationEnd: 'Endjahr',
    languageName: 'Sprache',
    languageLevel: 'Niveau',
    languageCertificate: 'Dokumentname',
    languageDocument: 'Zertifikat / Dokument hochladen',
    languageIssuer: 'Aussteller',
    languageDocumentSaved: 'Sprachdokument hochgeladen.',
    skillName: 'Skill-Name',
    skillCategory: 'Kategorie',
    skillProficiency: 'Niveau / Hinweis',
    skillYears: 'Jahre Erfahrung',
    skillEvidenceNote: 'Beschreibung / Nachweisnotiz',
    skillEvidenceFile: 'Nachweis / Dokument hochladen',
    skillEvidenceSaved: 'Skill-Nachweis aktualisiert.',
    skillCategoriesTitle: 'Kategorie wählen',
    noProfilePhoto: 'Noch kein Profilfoto.',
    currentBadge: 'Aktuell',
    previewEmpty: 'Noch nichts sichtbar.',
    remote: 'Remote',
    hybrid: 'Hybrid',
    onsite: 'Vor Ort',
    sectionDone: 'Fertig',
    sectionPartial: 'Teilweise',
    sectionMissing: 'Fehlt',
    manualEntryNote: 'Wenn offizielle Katalogdaten fehlen, bleibt freie Eingabe möglich.',
    healthDrawerButton: 'Profilstatus ansehen',
    healthDrawerTitle: 'Profilstatus',
    healthDrawerSubtitle: 'Behalte im Blick, was bereits stark wirkt und wo ein kurzer Feinschliff hilft.',
    healthDrawerCompletionLabel: 'Gesamtbild',
    healthDrawerStrongAreas: 'Starke Bereiche',
    healthDrawerFocusAreas: 'Bereiche mit Potenzial',
    healthDrawerSuggestions: 'Schnelle Verbesserungen',
    healthDrawerEmpty: 'Aktuell ist keine weitere Empfehlung sichtbar.',
  },
};
