export type CvReviewLocaleKey = 'tr' | 'en' | 'de';

export type CvReviewCopy = {
  title: string;
  subtitle: string;
  loading: string;
  empty: string;
  sourceFile: string;
  parserVersion: string;
  parseStatus: string;
  generatedAt: string;
  selectedChanges: string;
  applySelected: string;
  applying: string;
  resetSelection: string;
  refresh: string;
  currentValue: string;
  suggestedValue: string;
  itemsToAdd: string;
  education: string;
  experience: string;
  languages: string;
  headline: string;
  summary: string;
  remotePreference: string;
  skills: string;
  targetRoles: string;
  preferredLocations: string;
  applySuccess: string;
  applyPartial: string;
  nothingSelected: string;
  failedToLoad: string;
  failedToApply: string;
  noActionableChanges: string;
  noSelectionState: string;
  sourceFormat: string;
  extractionMethod: string;
  ocrUsage: string;
  extractionNote: string;
  extractionQuality: string;
  reviewHints: string;
  manualReviewStatus: string;
  defaultApplySafety: string;
  fallbackReason: string;
  recommendedNextAction: string;
  manualReviewRequiredValue: string;
  manualReviewNotRequiredValue: string;
  defaultApplySafeValue: string;
  defaultApplyUnsafeValue: string;
  fallbackReasonNone: string;
  fallbackReasonExtractionFailed: string;
  fallbackReasonNoTextDetected: string;
  fallbackReasonOcrNoTextDetected: string;
  fallbackReasonLowQualityOcr: string;
  fallbackReasonLowTextVolume: string;
  fallbackReasonOcrReviewRecommended: string;
  nextActionSafeToApply: string;
  nextActionReviewBeforeApply: string;
  nextActionReuploadOrEditManually: string;
  nextActionReuploadAsDocument: string;
  operatorManualReviewBanner: string;
  operatorSafeBanner: string;
  operatorAcknowledgeLabel: string;
  operatorAcknowledgeHint: string;
  safeFlowTitle: string;
  safeFlowHint: string;
  manualFlowTitle: string;
  manualFlowHint: string;
  applySelectedSafe: string;
  applySelectedReviewed: string;
  qualityHigh: string;
  qualityMedium: string;
  qualityLow: string;
  hintExtractionFailed: string;
  hintOcrNoTextDetected: string;
  hintNoTextDetected: string;
  hintOcrSource: string;
  hintLowTextVolume: string;
  hintMediumTextVolume: string;
  hintManualReviewRecommended: string;
  reviewSummaryTitle: string;
  reviewRequiredCount: string;
  reviewRecommendedCount: string;
  safeCount: string;
  selectedRiskCount: string;
  selectedReviewRecommendedCount: string;
  focusFieldsTitle: string;
  riskReasonsTitle: string;
  reviewRequiredBadge: string;
  reviewRecommendedBadge: string;
  safeBadge: string;
  reasonLowConfidence: string;
  reasonMediumConfidence: string;
  reasonHighConfidence: string;
  reasonMissingValue: string;
  reasonSparseContent: string;
  reasonOcrSource: string;
  reasonManualReviewFlow: string;
  reasonLowTextVolume: string;
  reasonMediumTextVolume: string;
  reasonExtractionReviewHint: string;
  reasonSelectedRiskyChange: string;
  reasonSelectedReviewRecommended: string;
  confidenceTitle: string;
  signalsTitle: string;
  collectionEmpty: string;
  ocrBanner: string;
  enterpriseSignalsTitle: string;
  enterpriseSignalsSubtitle: string;
  enterpriseDuplicateLabel: string;
  enterpriseCacheLabel: string;
  enterpriseAtsLabel: string;
  enterpriseRedactionLabel: string;
  enterprisePiiLabel: string;
  enterpriseRecommendationsTitle: string;
  parseStatusValues: Record<string, string>;
  severityToneDescription: Record<UserCvFieldReviewSeverity, string>;
};

export const CV_REVIEW_COPY: Record<CvReviewLocaleKey, CvReviewCopy> = {
  tr: {
    title: 'CV inceleme merkezi',
    subtitle:
      'Alan bazlı risk sinyallerini kontrol et, güven seviyelerini karşılaştır ve yalnızca doğruladığın değişiklikleri profile uygula.',
    loading: 'Aday verileri analiz ediliyor, lütfen bekleyin...',
    empty: 'Henüz incelenecek bir CV önerisi oluşmadı.',
    sourceFile: 'Kaynak dosya',
    parserVersion: 'Parser sürümü',
    parseStatus: 'Parse durumu',
    generatedAt: 'Üretilme zamanı',
    selectedChanges: 'Seçili değişiklik',
    applySelected: 'Seçilileri uygula',
    applying: 'Uygulanıyor...',
    resetSelection: 'Varsayılan seçimi yükle',
    refresh: 'Yenile',
    currentValue: 'Mevcut değer',
    suggestedValue: 'Önerilen değer',
    itemsToAdd: 'Eklenecek öğeler',
    education: 'Eğitim',
    experience: 'Deneyim',
    languages: 'Diller',
    headline: 'Başlık',
    summary: 'Özet',
    remotePreference: 'Çalışma tercihi',
    skills: 'Beceriler',
    targetRoles: 'Hedef roller',
    preferredLocations: 'Tercih edilen lokasyonlar',
    applySuccess: 'Seçili CV önerileri başarıyla uygulandı.',
    applyPartial:
      'Bazı öneriler uygulandı. Kalan değişiklikleri tekrar gözden geçirebilirsin.',
    nothingSelected: 'Uygulamak için en az bir değişiklik seçmelisin.',
    failedToLoad: 'CV inceleme verileri yüklenemedi.',
    failedToApply: 'CV değişiklikleri uygulanamadı.',
    noActionableChanges:
      'Bu CV için uygulanabilir yeni bir değişiklik görünmüyor.',
    noSelectionState: 'Devam etmek için en az bir değişiklik seç.',
    sourceFormat: 'Dosya formatı',
    extractionMethod: 'Extraction yöntemi',
    ocrUsage: 'OCR kullanımı',
    extractionNote: 'Extraction notu',
    extractionQuality: 'Extraction kalitesi',
    reviewHints: 'Review ipuçları',
    manualReviewStatus: 'Manuel inceleme durumu',
    defaultApplySafety: 'Varsayılan apply güvenliği',
    fallbackReason: 'Fallback nedeni',
    recommendedNextAction: 'Önerilen sonraki aksiyon',
    manualReviewRequiredValue: 'Gerekli',
    manualReviewNotRequiredValue: 'Gerekli değil',
    defaultApplySafeValue: 'Güvenli',
    defaultApplyUnsafeValue: 'Güvenli değil',
    fallbackReasonNone: 'Yok',
    fallbackReasonExtractionFailed: 'Extraction başarısız',
    fallbackReasonNoTextDetected: 'Metin tespit edilemedi',
    fallbackReasonOcrNoTextDetected: 'OCR metin tespit edemedi',
    fallbackReasonLowQualityOcr: 'Düşük kaliteli OCR',
    fallbackReasonLowTextVolume: 'Düşük metin hacmi',
    fallbackReasonOcrReviewRecommended: 'OCR sonrası inceleme önerilir',
    nextActionSafeToApply: 'Doğrudan apply edilebilir',
    nextActionReviewBeforeApply: 'Apply öncesi incele',
    nextActionReuploadOrEditManually: 'Yeniden yükle veya manuel düzenle',
    nextActionReuploadAsDocument: 'Doküman olarak yeniden yükle',
    operatorManualReviewBanner:
      'Bu CV ekstra dikkat istiyor. Uygulamadan önce seçili alanları manuel olarak doğrula.',
    operatorSafeBanner:
      'Bu CV güvenli apply akışına uygun görünüyor. Onay olmadan doğrudan uygulayabilirsin.',
    operatorAcknowledgeLabel:
      'Seçili alanları manuel olarak doğruladım ve yine de uygulamak istiyorum.',
    operatorAcknowledgeHint:
      'Bu extraction sonucu manuel inceleme gerektiriyor. Devam etmek için açık onay vermelisin.',
    safeFlowTitle: 'Güvenli apply akışı',
    safeFlowHint:
      'Güvenli alanlar yine de gözden geçirilebilir, ancak sistem bu CV’yi varsayılan apply için uygun görüyor.',
    manualFlowTitle: 'Manuel inceleme akışı',
    manualFlowHint:
      'Riskli alanlar öne çıkarıldı. Özellikle seçili riskli değişiklikleri doğrulamadan uygulama yapma.',
    applySelectedSafe: 'Güvenli seçimi uygula',
    applySelectedReviewed: 'İncelenmiş seçimi uygula',
    qualityHigh: 'Yüksek',
    qualityMedium: 'Orta',
    qualityLow: 'Düşük',
    hintExtractionFailed: 'Extraction başarısız oldu',
    hintOcrNoTextDetected: 'OCR çalıştı ancak metin tespit edilemedi',
    hintNoTextDetected: 'Metin tespit edilemedi',
    hintOcrSource: 'Kaynak görsel/OCR tabanlı',
    hintLowTextVolume: 'Düşük metin hacmi',
    hintMediumTextVolume: 'Orta metin hacmi',
    hintManualReviewRecommended: 'Manuel inceleme önerilir',
    reviewSummaryTitle: 'Risk özeti',
    reviewRequiredCount: 'Zorunlu inceleme',
    reviewRecommendedCount: 'Önerilen inceleme',
    safeCount: 'Güvenli alan',
    selectedRiskCount: 'Seçili riskli alan',
    selectedReviewRecommendedCount: 'Seçili dikkat alanı',
    focusFieldsTitle: 'Öncelikli kontrol alanları',
    riskReasonsTitle: 'Nedenler',
    reviewRequiredBadge: 'İnceleme gerekli',
    reviewRecommendedBadge: 'İnceleme önerilir',
    safeBadge: 'Güvenli',
    reasonLowConfidence: 'Düşük confidence',
    reasonMediumConfidence: 'Orta confidence',
    reasonHighConfidence: 'Yüksek confidence',
    reasonMissingValue: 'Eksik değer',
    reasonSparseContent: 'Seyrek içerik',
    reasonOcrSource: 'OCR kaynağı',
    reasonManualReviewFlow: 'Manuel review akışı',
    reasonLowTextVolume: 'Düşük metin hacmi',
    reasonMediumTextVolume: 'Orta metin hacmi',
    reasonExtractionReviewHint: 'Extraction uyarısı',
    reasonSelectedRiskyChange: 'Seçili riskli değişiklik',
    reasonSelectedReviewRecommended: 'Seçili dikkat önerisi',
    confidenceTitle: 'Confidence',
    signalsTitle: 'Sinyaller',
    collectionEmpty: 'Bu bölüm için öneri yok.',
    ocrBanner:
      'Bu CV OCR ile işlendi. Orta ve düşük riskli alanları özellikle dikkatle doğrula.',
    enterpriseSignalsTitle: 'Operasyonel sinyaller',
    enterpriseSignalsSubtitle:
      'Belge ilişkisi, parse yeniden kullanımı, ATS okunabilirliği ve anonim inceleme hazırlığı tek görünümde özetlenir.',
    enterpriseDuplicateLabel: 'Belge ilişkisi',
    enterpriseCacheLabel: 'Parse yeniden kullanımı',
    enterpriseAtsLabel: 'ATS skoru',
    enterpriseRedactionLabel: 'Anonim inceleme',
    enterprisePiiLabel: 'PII türleri',
    enterpriseRecommendationsTitle: 'Öne çıkan öneriler',
    parseStatusValues: {
      pending: 'Beklemede',
      parsed: 'Analiz edildi',
      failed: 'Başarısız',
      empty: 'Boş',
    },
    severityToneDescription: {
      safe: 'Bu alan yüksek güven veriyor.',
      review_recommended: 'Bu alan uygulanmadan önce gözden geçirilmeli.',
      review_required: 'Bu alan manuel doğrulama olmadan uygulanmamalı.',
    },
  },
  en: {
    title: 'CV review center',
    subtitle:
      'Inspect field-level risk signals, compare confidence levels, and apply only the changes you trust.',
    loading: 'Candidate data is being analyzed. Please wait...',
    empty: 'There is no CV review suggestion yet.',
    sourceFile: 'Source file',
    parserVersion: 'Parser version',
    parseStatus: 'Parse status',
    generatedAt: 'Generated at',
    selectedChanges: 'Selected changes',
    applySelected: 'Apply selected',
    applying: 'Applying...',
    resetSelection: 'Reset default selection',
    refresh: 'Refresh',
    currentValue: 'Current value',
    suggestedValue: 'Suggested value',
    itemsToAdd: 'Items to add',
    education: 'Education',
    experience: 'Experience',
    languages: 'Languages',
    headline: 'Headline',
    summary: 'Summary',
    remotePreference: 'Work preference',
    skills: 'Skills',
    targetRoles: 'Target roles',
    preferredLocations: 'Preferred locations',
    applySuccess: 'Selected CV suggestions were applied successfully.',
    applyPartial:
      'Some suggestions were applied. You can review the remaining changes again.',
    nothingSelected: 'Select at least one change before applying.',
    failedToLoad: 'CV review data could not be loaded.',
    failedToApply: 'CV changes could not be applied.',
    noActionableChanges: 'There are no new actionable CV changes right now.',
    noSelectionState: 'Select at least one change to continue.',
    sourceFormat: 'File format',
    extractionMethod: 'Extraction method',
    ocrUsage: 'OCR usage',
    extractionNote: 'Extraction note',
    extractionQuality: 'Extraction quality',
    reviewHints: 'Review hints',
    manualReviewStatus: 'Manual review status',
    defaultApplySafety: 'Default apply safety',
    fallbackReason: 'Fallback reason',
    recommendedNextAction: 'Recommended next action',
    manualReviewRequiredValue: 'Required',
    manualReviewNotRequiredValue: 'Not required',
    defaultApplySafeValue: 'Safe',
    defaultApplyUnsafeValue: 'Not safe',
    fallbackReasonNone: 'None',
    fallbackReasonExtractionFailed: 'Extraction failed',
    fallbackReasonNoTextDetected: 'No text detected',
    fallbackReasonOcrNoTextDetected: 'OCR found no text',
    fallbackReasonLowQualityOcr: 'Low-quality OCR',
    fallbackReasonLowTextVolume: 'Low text volume',
    fallbackReasonOcrReviewRecommended: 'OCR review recommended',
    nextActionSafeToApply: 'Safe to apply directly',
    nextActionReviewBeforeApply: 'Review before apply',
    nextActionReuploadOrEditManually: 'Re-upload or edit manually',
    nextActionReuploadAsDocument: 'Re-upload as document',
    operatorManualReviewBanner:
      'This CV needs extra care. Validate the selected fields manually before applying.',
    operatorSafeBanner:
      'This CV appears eligible for the safe apply flow. You can apply it directly without extra confirmation.',
    operatorAcknowledgeLabel:
      'I manually reviewed the selected fields and still want to apply them.',
    operatorAcknowledgeHint:
      'This extraction result requires manual review. Explicit acknowledgement is required to continue.',
    safeFlowTitle: 'Safe apply flow',
    safeFlowHint:
      'Safe fields can still be inspected, but the system considers this CV fit for default apply.',
    manualFlowTitle: 'Manual review flow',
    manualFlowHint:
      'Risky fields are highlighted for you. Do not apply selected risky changes without validation.',
    applySelectedSafe: 'Apply safe selection',
    applySelectedReviewed: 'Apply reviewed selection',
    qualityHigh: 'High',
    qualityMedium: 'Medium',
    qualityLow: 'Low',
    hintExtractionFailed: 'Extraction failed',
    hintOcrNoTextDetected: 'OCR ran but found no text',
    hintNoTextDetected: 'No text detected',
    hintOcrSource: 'Image/OCR source',
    hintLowTextVolume: 'Low text volume',
    hintMediumTextVolume: 'Medium text volume',
    hintManualReviewRecommended: 'Manual review recommended',
    reviewSummaryTitle: 'Risk summary',
    reviewRequiredCount: 'Review required',
    reviewRecommendedCount: 'Review recommended',
    safeCount: 'Safe fields',
    selectedRiskCount: 'Selected risky fields',
    selectedReviewRecommendedCount: 'Selected caution fields',
    focusFieldsTitle: 'Priority review fields',
    riskReasonsTitle: 'Reasons',
    reviewRequiredBadge: 'Review required',
    reviewRecommendedBadge: 'Review recommended',
    safeBadge: 'Safe',
    reasonLowConfidence: 'Low confidence',
    reasonMediumConfidence: 'Medium confidence',
    reasonHighConfidence: 'High confidence',
    reasonMissingValue: 'Missing value',
    reasonSparseContent: 'Sparse content',
    reasonOcrSource: 'OCR source',
    reasonManualReviewFlow: 'Manual review flow',
    reasonLowTextVolume: 'Low text volume',
    reasonMediumTextVolume: 'Medium text volume',
    reasonExtractionReviewHint: 'Extraction warning',
    reasonSelectedRiskyChange: 'Selected risky change',
    reasonSelectedReviewRecommended: 'Selected caution change',
    confidenceTitle: 'Confidence',
    signalsTitle: 'Signals',
    collectionEmpty: 'No suggestion in this section yet.',
    ocrBanner:
      'This CV was processed with OCR. Give medium- and high-risk fields extra attention before applying.',

    enterpriseSignalsTitle: 'Operational signals',
    enterpriseSignalsSubtitle:
      'Document relationship, parse reuse, ATS readability, and anonymous review readiness are summarized in one place.',
    enterpriseDuplicateLabel: 'Document relationship',
    enterpriseCacheLabel: 'Parse reuse',
    enterpriseAtsLabel: 'ATS score',
    enterpriseRedactionLabel: 'Anonymous review',
    enterprisePiiLabel: 'PII types',
    enterpriseRecommendationsTitle: 'Top recommendations',
    parseStatusValues: {
      pending: 'Pending',
      parsed: 'Parsed',
      failed: 'Failed',
      empty: 'Empty',
    },
    severityToneDescription: {
      safe: 'This field looks dependable.',
      review_recommended: 'This field should be reviewed before it is applied.',
      review_required: 'This field should not be applied without manual validation.',
    },
  },
  de: {
    title: 'CV-Review-Zentrum',
    subtitle:
      'Prüfe Feldrisiken, vergleiche Confidence-Signale und übernimm nur die Änderungen, denen du vertraust.',
    loading: 'Kandidatendaten werden analysiert. Bitte kurz warten...',
    empty: 'Derzeit gibt es keinen CV-Vorschlag zur Prüfung.',
    sourceFile: 'Quelldatei',
    parserVersion: 'Parser-Version',
    parseStatus: 'Parse-Status',
    generatedAt: 'Erstellt am',
    selectedChanges: 'Ausgewählte Änderungen',
    applySelected: 'Ausgewähltes übernehmen',
    applying: 'Wird übernommen...',
    resetSelection: 'Standardauswahl zurücksetzen',
    refresh: 'Aktualisieren',
    currentValue: 'Aktueller Wert',
    suggestedValue: 'Vorgeschlagener Wert',
    itemsToAdd: 'Hinzuzufügende Einträge',
    education: 'Ausbildung',
    experience: 'Berufserfahrung',
    languages: 'Sprachen',
    headline: 'Überschrift',
    summary: 'Zusammenfassung',
    remotePreference: 'Arbeitsmodell',
    skills: 'Skills',
    targetRoles: 'Zielrollen',
    preferredLocations: 'Bevorzugte Standorte',
    applySuccess: 'Die ausgewählten CV-Vorschläge wurden erfolgreich übernommen.',
    applyPartial:
      'Einige Vorschläge wurden übernommen. Die übrigen Änderungen kannst du erneut prüfen.',
    nothingSelected: 'Wähle mindestens eine Änderung aus.',
    failedToLoad: 'CV-Review-Daten konnten nicht geladen werden.',
    failedToApply: 'CV-Änderungen konnten nicht übernommen werden.',
    noActionableChanges:
      'Für diesen CV gibt es aktuell keine neuen umsetzbaren Änderungen.',
    noSelectionState: 'Wähle mindestens eine Änderung aus, um fortzufahren.',
    sourceFormat: 'Dateiformat',
    extractionMethod: 'Extraktionsmethode',
    ocrUsage: 'OCR-Nutzung',
    extractionNote: 'Extraktionshinweis',
    extractionQuality: 'Extraktionsqualität',
    reviewHints: 'Prüfhinweise',
    manualReviewStatus: 'Status der manuellen Prüfung',
    defaultApplySafety: 'Sicherheit für Standard-Apply',
    fallbackReason: 'Fallback-Grund',
    recommendedNextAction: 'Empfohlener nächster Schritt',
    manualReviewRequiredValue: 'Erforderlich',
    manualReviewNotRequiredValue: 'Nicht erforderlich',
    defaultApplySafeValue: 'Sicher',
    defaultApplyUnsafeValue: 'Nicht sicher',
    fallbackReasonNone: 'Kein Grund',
    fallbackReasonExtractionFailed: 'Extraktion fehlgeschlagen',
    fallbackReasonNoTextDetected: 'Kein Text erkannt',
    fallbackReasonOcrNoTextDetected: 'OCR hat keinen Text erkannt',
    fallbackReasonLowQualityOcr: 'OCR-Qualität zu niedrig',
    fallbackReasonLowTextVolume: 'Geringes Textvolumen',
    fallbackReasonOcrReviewRecommended: 'Prüfung nach OCR empfohlen',
    nextActionSafeToApply: 'Direkt übernehmbar',
    nextActionReviewBeforeApply: 'Vorher prüfen',
    nextActionReuploadOrEditManually: 'Neu hochladen oder manuell bearbeiten',
    nextActionReuploadAsDocument: 'Als Dokument neu hochladen',
    operatorManualReviewBanner:
      'Dieser CV benötigt besondere Aufmerksamkeit. Prüfe die ausgewählten Felder manuell, bevor du sie übernimmst.',
    operatorSafeBanner:
      'Dieser CV scheint für den sicheren Apply-Flow geeignet zu sein. Eine zusätzliche Bestätigung ist nicht nötig.',
    operatorAcknowledgeLabel:
      'Ich habe die ausgewählten Felder manuell geprüft und möchte sie trotzdem übernehmen.',
    operatorAcknowledgeHint:
      'Dieses Extraktionsergebnis erfordert eine manuelle Prüfung. Für das Fortfahren ist eine explizite Bestätigung nötig.',
    safeFlowTitle: 'Sicherer Apply-Flow',
    safeFlowHint:
      'Sichere Felder können weiterhin geprüft werden, aber das System stuft diesen CV als geeignet für Standard-Apply ein.',
    manualFlowTitle: 'Manueller Prüf-Flow',
    manualFlowHint:
      'Risikoreiche Felder werden hervorgehoben. Übernimm ausgewählte riskante Änderungen nicht ohne Validierung.',
    applySelectedSafe: 'Sichere Auswahl übernehmen',
    applySelectedReviewed: 'Geprüfte Auswahl übernehmen',
    qualityHigh: 'Hoch',
    qualityMedium: 'Mittel',
    qualityLow: 'Niedrig',
    hintExtractionFailed: 'Extraktion fehlgeschlagen',
    hintOcrNoTextDetected: 'OCR wurde ausgeführt, aber kein Text erkannt',
    hintNoTextDetected: 'Kein Text erkannt',
    hintOcrSource: 'Bild-/OCR-Quelle',
    hintLowTextVolume: 'Geringes Textvolumen',
    hintMediumTextVolume: 'Mittleres Textvolumen',
    hintManualReviewRecommended: 'Manuelle Prüfung empfohlen',
    reviewSummaryTitle: 'Risikoübersicht',
    reviewRequiredCount: 'Pflichtprüfung',
    reviewRecommendedCount: 'Empfohlene Prüfung',
    safeCount: 'Sichere Felder',
    selectedRiskCount: 'Ausgewählte Risikofelder',
    selectedReviewRecommendedCount: 'Ausgewählte Vorsichtsfelder',
    focusFieldsTitle: 'Priorisierte Prüffelder',
    riskReasonsTitle: 'Begründungen',
    reviewRequiredBadge: 'Prüfung erforderlich',
    reviewRecommendedBadge: 'Prüfung empfohlen',
    safeBadge: 'Sicher',
    reasonLowConfidence: 'Niedrige Confidence',
    reasonMediumConfidence: 'Mittlere Confidence',
    reasonHighConfidence: 'Hohe Confidence',
    reasonMissingValue: 'Fehlender Wert',
    reasonSparseContent: 'Wenig Inhalt',
    reasonOcrSource: 'OCR-Quelle',
    reasonManualReviewFlow: 'Manueller Prüf-Flow',
    reasonLowTextVolume: 'Geringes Textvolumen',
    reasonMediumTextVolume: 'Mittleres Textvolumen',
    reasonExtractionReviewHint: 'Extraktionswarnung',
    reasonSelectedRiskyChange: 'Ausgewählte riskante Änderung',
    reasonSelectedReviewRecommended: 'Ausgewählte Vorsichtsänderung',
    confidenceTitle: 'Confidence',
    signalsTitle: 'Signale',
    collectionEmpty: 'Für diesen Bereich gibt es noch keinen Vorschlag.',
    ocrBanner:
      'Dieser CV wurde mit OCR verarbeitet. Prüfe Felder mit mittlerem oder hohem Risiko besonders sorgfältig.',
    enterpriseSignalsTitle: 'Operative Signale',
    enterpriseSignalsSubtitle:
      'Dokumentbeziehung, Parse-Wiederverwendung, ATS-Lesbarkeit und Bereitschaft für anonyme Prüfung werden kompakt zusammengefasst.',
    enterpriseDuplicateLabel: 'Dokumentbeziehung',
    enterpriseCacheLabel: 'Parse-Wiederverwendung',
    enterpriseAtsLabel: 'ATS-Score',
    enterpriseRedactionLabel: 'Anonyme Prüfung',
    enterprisePiiLabel: 'PII-Typen',
    enterpriseRecommendationsTitle: 'Wichtige Empfehlungen',
        
    parseStatusValues: {
      pending: 'Ausstehend',
      parsed: 'Analysiert',
      failed: 'Fehlgeschlagen',
      empty: 'Leer',
    },
    severityToneDescription: {
      safe: 'Dieses Feld wirkt verlässlich.',
      review_recommended: 'Dieses Feld sollte vor der Übernahme geprüft werden.',
      review_required: 'Dieses Feld darf nicht ohne manuelle Validierung übernommen werden.',
    },
  },
};
