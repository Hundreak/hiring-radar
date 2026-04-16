import type {UserCvEnterpriseAts, UserCvEnterpriseMetadata, UserCvEnterpriseRedaction} from '@/types/user';

export type EnterpriseLocale = 'tr' | 'en' | 'de';
export type EnterpriseSignalIntent = 'neutral' | 'positive' | 'caution';

const COPY = {
  tr: {
    relation: {
      exact_duplicate: 'Aynı CV',
      updated_version: 'Güncel versiyon',
      related_variant: 'Benzer versiyon',
      first_observed: 'İlk gözlem',
      unknown: 'Bilinmiyor',
    },
    cache: {
      exact_hit: 'Tam yeniden kullanım',
      partial_reuse: 'Kısmi yeniden kullanım',
      miss: 'Yeni parse',
      unknown: 'Bilinmiyor',
    },
    ats: {high: 'Güçlü', medium: 'Dengeli', low: 'İyileştirilmeli', unknown: 'Bilinmiyor'},
    redactionReady: 'Hazır',
    redactionUnavailable: 'Hazır değil',
    piiFindingsSuffix: 'PII bulgusu',
    noteDuplicate: 'Bu CV daha önce görülen bir içerikle çok yüksek benzerlik gösteriyor.',
    noteVersion: 'Bu belge aynı adayın daha yeni bir versiyonu gibi görünüyor.',
    noteCache: 'Motor, önceki parse çıktısının bir bölümünü yeniden kullanabiliyor.',
    noteAts: 'ATS uyumluluğu zayıf görünüyor. Bölüm yapısı ve okunabilirliği gözden geçir.',
    noteRedaction: 'Anonim inceleme için redacted çıktı üretilebilir.',
    piiTypes: {
      person_name: 'İsim',
      email: 'E-posta',
      phone: 'Telefon',
      address: 'Adres',
      profile_handle: 'Profil bağlantısı',
      date_of_birth: 'Doğum tarihi',
      unknown: 'Kişisel veri',
    },
  },
  en: {
    relation: {
      exact_duplicate: 'Exact duplicate',
      updated_version: 'Updated version',
      related_variant: 'Related variant',
      first_observed: 'First observed',
      unknown: 'Unknown',
    },
    cache: {
      exact_hit: 'Exact reuse',
      partial_reuse: 'Partial reuse',
      miss: 'Fresh parse',
      unknown: 'Unknown',
    },
    ats: {high: 'Strong', medium: 'Balanced', low: 'Needs work', unknown: 'Unknown'},
    redactionReady: 'Ready',
    redactionUnavailable: 'Unavailable',
    piiFindingsSuffix: 'PII findings',
    noteDuplicate: 'This CV is highly similar to a document that was already parsed.',
    noteVersion: 'This document looks like a newer version of the same candidate profile.',
    noteCache: 'The engine can reuse parts of a previous parse for this document.',
    noteAts: 'ATS compatibility looks weak. Review section structure and readability.',
    noteRedaction: 'A redacted artifact can be generated for anonymous review.',
    piiTypes: {
      person_name: 'Name',
      email: 'Email',
      phone: 'Phone',
      address: 'Address',
      profile_handle: 'Profile link',
      date_of_birth: 'Date of birth',
      unknown: 'Personal data',
    },
  },
  de: {
    relation: {
      exact_duplicate: 'Exaktes Duplikat',
      updated_version: 'Aktualisierte Version',
      related_variant: 'Verwandte Variante',
      first_observed: 'Erstbeobachtung',
      unknown: 'Unbekannt',
    },
    cache: {
      exact_hit: 'Vollständige Wiederverwendung',
      partial_reuse: 'Teilweise Wiederverwendung',
      miss: 'Neue Analyse',
      unknown: 'Unbekannt',
    },
    ats: {high: 'Stark', medium: 'Solide', low: 'Verbesserungsbedarf', unknown: 'Unbekannt'},
    redactionReady: 'Bereit',
    redactionUnavailable: 'Nicht verfügbar',
    piiFindingsSuffix: 'PII-Hinweise',
    noteDuplicate: 'Dieser CV ist einem bereits verarbeiteten Dokument sehr ähnlich.',
    noteVersion: 'Dieses Dokument wirkt wie eine neuere Version desselben Kandidaten.',
    noteCache: 'Die Engine kann Teile eines früheren Parse-Ergebnisses wiederverwenden.',
    noteAts: 'Die ATS-Kompatibilität wirkt schwächer. Struktur und Lesbarkeit prüfen.',
    noteRedaction: 'Für eine anonyme Prüfung kann eine redigierte Version erzeugt werden.',
    piiTypes: {
      person_name: 'Name',
      email: 'E-Mail',
      phone: 'Telefon',
      address: 'Adresse',
      profile_handle: 'Profil-Link',
      date_of_birth: 'Geburtsdatum',
      unknown: 'Personenbezogene Daten',
    },
  },
} as const;

function getLocaleCopy(locale: EnterpriseLocale) {
  return COPY[locale];
}

export function formatEnterpriseRelationValue(
  relation: string | null | undefined,
  locale: EnterpriseLocale
): string {
  if (!relation) {
    return '—';
  }

  const copy = getLocaleCopy(locale);
  return copy.relation[relation as keyof typeof copy.relation] ?? relation;
}

export function formatEnterpriseCacheStatusValue(
  status: string | null | undefined,
  locale: EnterpriseLocale
): string {
  if (!status) {
    return '—';
  }

  const copy = getLocaleCopy(locale);
  return copy.cache[status as keyof typeof copy.cache] ?? status;
}

export function formatEnterpriseAtsValue(
  ats: UserCvEnterpriseAts | null | undefined,
  locale: EnterpriseLocale
): string {
  if (!ats || ats.score === null || ats.score === undefined) {
    return '—';
  }

  const copy = getLocaleCopy(locale);
  const level = ats.level
    ? copy.ats[ats.level as keyof typeof copy.ats] ?? ats.level
    : copy.ats.unknown;
  return `${ats.score}/100 · ${level}`;
}

export function formatEnterpriseRedactionValue(
  redaction: UserCvEnterpriseRedaction | null | undefined,
  locale: EnterpriseLocale
): string {
  if (!redaction) {
    return '—';
  }

  const copy = getLocaleCopy(locale);
  if (!redaction.available) {
    return copy.redactionUnavailable;
  }

  return `${copy.redactionReady} · ${redaction.pii_findings_count} ${copy.piiFindingsSuffix}`;
}

export function formatEnterprisePiiTypes(
  piiTypes: string[] | null | undefined,
  locale: EnterpriseLocale
): string {
  if (!piiTypes || piiTypes.length === 0) {
    return '—';
  }

  const copy = getLocaleCopy(locale);
  return piiTypes
    .map((value) => copy.piiTypes[value as keyof typeof copy.piiTypes] ?? value)
    .join(', ');
}

export function buildEnterpriseSignalNote(
  metadata: UserCvEnterpriseMetadata | null | undefined,
  locale: EnterpriseLocale
): string | null {
  if (!metadata) {
    return null;
  }

  const copy = getLocaleCopy(locale);
  if (metadata.fingerprint.relation === 'exact_duplicate') {
    return copy.noteDuplicate;
  }
  if (metadata.fingerprint.relation === 'updated_version') {
    return copy.noteVersion;
  }
  if (metadata.ats.level === 'low') {
    return copy.noteAts;
  }
  if (metadata.cache.exact_reusable || metadata.cache.partial_reusable) {
    return copy.noteCache;
  }
  if (metadata.redaction.available && metadata.redaction.pii_findings_count > 0) {
    return copy.noteRedaction;
  }

  return null;
}

export function getEnterpriseSignalIntent(
  metadata: UserCvEnterpriseMetadata | null | undefined
): EnterpriseSignalIntent {
  if (!metadata) {
    return 'neutral';
  }

  if (
    metadata.fingerprint.relation === 'exact_duplicate' ||
    metadata.ats.level === 'low'
  ) {
    return 'caution';
  }

  if (
    metadata.cache.exact_reusable ||
    metadata.fingerprint.relation === 'updated_version'
  ) {
    return 'positive';
  }

  return 'neutral';
}
