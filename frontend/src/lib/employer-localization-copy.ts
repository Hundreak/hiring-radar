import {normalizeEmployerLanguage, type EmployerLanguage} from './employer-copy';

export type LocalizationTerm = {
  concept: string;
  tr: string;
  en: string;
  note: string;
};

export type LocalizationCheck = {
  label: string;
  value: number;
  detail: string;
};

export type LocalizationRisk = {
  term: string;
  replacement: string;
  severity: 'high' | 'medium' | 'low';
  reason: string;
};

export function getEmployerLocalizationLanguage(locale: string): EmployerLanguage {
  return normalizeEmployerLanguage(locale);
}

const glossary: LocalizationTerm[] = [
  {concept: 'candidate', tr: 'Aday', en: 'Candidate', note: 'İnsan ve profil bağlamında “talent” yerine aday kullanılır.'},
  {concept: 'job', tr: 'İlan', en: 'Job', note: 'İşveren arayüzünde “job post” karşılığıdır.'},
  {concept: 'pipeline', tr: 'Süreç', en: 'Pipeline', note: 'Adayın işe alım aşamalarını ifade eder.'},
  {concept: 'shortlist', tr: 'Kısa liste', en: 'Shortlist', note: 'Öne alınan aday havuzu.'},
  {concept: 'match score', tr: 'Uyum puanı', en: 'Match score', note: 'Karar değil, açıklanabilir karar desteğidir.'},
  {concept: 'intent score', tr: 'Niyet puanı', en: 'Intent score', note: 'Adayın yanıt/ilgi olasılığı sinyali.'},
  {concept: 'outreach', tr: 'Davet', en: 'Outreach', note: 'Adaya ilk temas ve kampanya akışı.'},
  {concept: 'campaign', tr: 'Kampanya', en: 'Campaign', note: 'Toplu ya da tekil davet taslağı.'},
  {concept: 'review', tr: 'Kontrol', en: 'Review', note: 'İnsan kontrolü gerektiren durum.'},
  {concept: 'blocked', tr: 'Engelli', en: 'Blocked', note: 'Gönderime engel olan kalite veya uyumluluk durumu.'},
  {concept: 'sourcing', tr: 'Aday kaynağı', en: 'Sourcing', note: 'Aday bulma ve kaynak yönetimi bağlamında kullanılır.'},
  {concept: 'workspace', tr: 'Çalışma alanı', en: 'Workspace', note: 'Şirket/ekip hesabı bağlamında.'},
  {concept: 'hiring manager', tr: 'İşe alım yöneticisi', en: 'Hiring manager', note: 'Aday kararına katılan iş birimi yöneticisi.'},
  {concept: 'SLA', tr: 'Hedef süre', en: 'SLA', note: 'Türkçe arayüzde teknik kısaltma yerine anlaşılır ifade tercih edilir.'},
  {concept: 'RBAC', tr: 'Rol tabanlı yetkilendirme', en: 'RBAC', note: 'İlk kullanımda açık yazılır; gerekiyorsa parantez içinde kısaltma verilir.'},
];

export function getEmployerLocalizationCopy(locale: string) {
  const lang = getEmployerLocalizationLanguage(locale);

  if (lang === 'tr') {
    return {
      lang,
      page: {
        eyebrow: 'Dil kalite merkezi',
        title: 'Türkçe ve İngilizce ürün dilini üretim kalitesinde yönetin',
        description:
          'İşveren panelinde Türkçe seçildiğinde tamamen Türkçe, İngilizce seçildiğinde tamamen İngilizce bir deneyim hedeflenir. Bu merkez terim sözlüğünü, kalite kontrollerini ve çeviri politikasını görünür kılar.',
        primaryAction: 'Dil denetimini çalıştır',
        secondaryAction: 'Sözlüğü dışa aktar',
        activePolicy: 'Aktif dil politikası',
        productLanguage: 'Ürün dili',
        strictTurkish: 'Katı Türkçe',
        strictEnglish: 'Temiz İngilizce',
      },
      metrics: [
        {label: 'Türkçe kapsama', value: 94, detail: 'İşveren ana akışlarındaki görünür metinlerin Türkçeleştirme oranı'},
        {label: 'İngilizce kapsama', value: 96, detail: 'İngilizce rotalarda kalan Türkçe metin kontrolü'},
        {label: 'Terim tutarlılığı', value: 91, detail: 'Aynı kavram için tek karşılık kullanımı'},
        {label: 'Erişilebilir metin', value: 89, detail: 'Buton, aria etiketi ve boş durum açıklığı'},
      ] satisfies LocalizationCheck[],
      sections: {
        glossary: 'Ürün terim sözlüğü',
        glossaryDesc: 'Türkçe ve İngilizce karşılıklar tek yerden yönetilir. Yeni ekran eklenirken bu tablo referans alınmalıdır.',
        policy: 'Çeviri politikası',
        policyDesc: 'Türkçe arayüzde gereksiz İngilizce ürün terimi kullanılmaz; marka adı veya teknik kısaltma gerekiyorsa açıklama ile verilir.',
        risks: 'Kalan dil riskleri',
        risksDesc: 'Üretim öncesi temizlenmesi gereken İngilizce/Türkçe karışımı veya belirsiz terimler.',
        checklist: 'Yayın öncesi kontrol listesi',
      },
      glossary,
      policies: [
        {title: 'Türkçe tamamen Türkçe olmalı', detail: 'Pipeline, shortlist, match, intent, review gibi terimler Türkçe karşılıklarıyla gösterilir.'},
        {title: 'İngilizce rotalarda Türkçe kırıntı kalmamalı', detail: '/en rotasında buton, rozet, boş durum ve hata mesajları İngilizce olmalıdır.'},
        {title: 'Yapay zekâ karar vermez, destek verir', detail: 'Uyum puanı ve öneriler insan onayı gerektiren karar desteği olarak anlatılır.'},
        {title: 'Erişilebilirlik metni de çevrilir', detail: 'Aria label, ekran okuyucu metni, hata ve boş durum açıklamaları da iki dile bağlanır.'},
      ],
      risks: [
        {term: 'Pipeline', replacement: 'Süreç', severity: 'high', reason: 'Türkçe kullanıcı için belirsiz ve ürün jargonu gibi durur.'},
        {term: 'Shortlist', replacement: 'Kısa liste', severity: 'high', reason: 'Aday yönetiminde sık görülen ana aksiyon.'},
        {term: 'Match', replacement: 'Uyum', severity: 'medium', reason: 'Skor bağlamında “uyum puanı” daha anlaşılır.'},
        {term: 'Review Board', replacement: 'Kontrol panosu', severity: 'medium', reason: 'Kampanya gönderimi insan kontrolünü anlatmalıdır.'},
        {term: 'Workspace', replacement: 'Çalışma alanı', severity: 'low', reason: 'B2B ayar ekranlarında tutarlı kullanılmalı.'},
      ] satisfies LocalizationRisk[],
      checklist: [
        'Yeni component içinde görünür metin hardcoded yazılmadı.',
        'Buton ve link metinleri iki dilde kontrol edildi.',
        'Boş durum, hata ve yükleniyor metinleri iki dile bağlı.',
        'Türkçe rotada gereksiz İngilizce ürün terimi yok.',
        'İngilizce rotada Türkçe kalıntı yok.',
        'Aria label ve yardımcı metinler yerelleştirildi.',
      ],
      severity: {high: 'Yüksek', medium: 'Orta', low: 'Düşük'},
    };
  }

  return {
    lang,
    page: {
      eyebrow: 'Language quality center',
      title: 'Manage Turkish and English product language at production quality',
      description:
        'When employers choose Turkish, the experience should be fully Turkish; when they choose English, it should be fully English. This center makes terminology, checks and translation policy visible.',
      primaryAction: 'Run language audit',
      secondaryAction: 'Export glossary',
      activePolicy: 'Active language policy',
      productLanguage: 'Product language',
      strictTurkish: 'Strict Turkish',
      strictEnglish: 'Clean English',
    },
    metrics: [
      {label: 'Turkish coverage', value: 94, detail: 'Localization coverage for visible employer workflows'},
      {label: 'English coverage', value: 96, detail: 'Check for Turkish remnants inside English routes'},
      {label: 'Terminology consistency', value: 91, detail: 'Single approved term per product concept'},
      {label: 'Accessible copy', value: 89, detail: 'Button, aria label and empty-state clarity'},
    ] satisfies LocalizationCheck[],
    sections: {
      glossary: 'Product glossary',
      glossaryDesc: 'Turkish and English equivalents are managed in one place. New screens should use this table as the reference.',
      policy: 'Translation policy',
      policyDesc: 'The Turkish UI avoids unnecessary English product jargon; brand names and technical abbreviations are explained when needed.',
      risks: 'Remaining language risks',
      risksDesc: 'Mixed-language or ambiguous terms that should be cleaned before production release.',
      checklist: 'Pre-release checklist',
    },
    glossary,
    policies: [
      {title: 'Turkish must be fully Turkish', detail: 'Terms like pipeline, shortlist, match, intent and review use their approved Turkish equivalents.'},
      {title: 'English routes must not contain Turkish remnants', detail: 'Buttons, badges, empty states and errors should be English under /en.'},
      {title: 'AI supports decisions; it does not decide', detail: 'Match scores and recommendations are explained as human-reviewed decision support.'},
      {title: 'Accessibility copy is localized too', detail: 'Aria labels, screen-reader text, errors and empty-state descriptions are also language-aware.'},
    ],
    risks: [
      {term: 'Pipeline', replacement: 'Süreç', severity: 'high', reason: 'Main workflow term in Turkish routes.'},
      {term: 'Shortlist', replacement: 'Kısa liste', severity: 'high', reason: 'Core candidate-management action.'},
      {term: 'Match', replacement: 'Uyum', severity: 'medium', reason: '“Match score” should become “uyum puanı” in Turkish.'},
      {term: 'Review Board', replacement: 'Kontrol panosu', severity: 'medium', reason: 'Should describe human review clearly.'},
      {term: 'Workspace', replacement: 'Çalışma alanı', severity: 'low', reason: 'Should be consistent in B2B settings.'},
    ] satisfies LocalizationRisk[],
    checklist: [
      'No visible copy is hardcoded inside new components.',
      'Button and link labels are checked in both languages.',
      'Empty, error and loading states are language-aware.',
      'Turkish routes avoid unnecessary English product jargon.',
      'English routes contain no Turkish remnants.',
      'Aria labels and helper copy are localized.',
    ],
    severity: {high: 'High', medium: 'Medium', low: 'Low'},
  };
}
