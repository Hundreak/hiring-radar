import {GENERATED_TURKISH_UNIVERSITY_NAMES} from './turkish-universities.generated';

export type UniversityOption = {
  name: string;
  city: string;
  type: 'devlet' | 'vakıf';
  departments: string[];
};

export const TURKISH_UNIVERSITY_OPTIONS: UniversityOption[] = [
  {
    name: 'Boğaziçi Üniversitesi',
    city: 'İstanbul',
    type: 'devlet',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Endüstri Mühendisliği', 'Makine Mühendisliği', 'Ekonomi', 'İşletme'],
  },
  {
    name: 'Orta Doğu Teknik Üniversitesi',
    city: 'Ankara',
    type: 'devlet',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Endüstri Mühendisliği', 'Makine Mühendisliği', 'Havacılık ve Uzay Mühendisliği', 'İnşaat Mühendisliği'],
  },
  {
    name: 'İstanbul Teknik Üniversitesi',
    city: 'İstanbul',
    type: 'devlet',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik Mühendisliği', 'Elektronik ve Haberleşme Mühendisliği', 'Yapay Zekâ ve Veri Mühendisliği', 'Makine Mühendisliği', 'Endüstri Mühendisliği'],
  },
  {
    name: 'Yıldız Teknik Üniversitesi',
    city: 'İstanbul',
    type: 'devlet',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik Mühendisliği', 'Elektronik ve Haberleşme Mühendisliği', 'Mekatronik Mühendisliği', 'Endüstri Mühendisliği'],
  },
  {
    name: 'Hacettepe Üniversitesi',
    city: 'Ankara',
    type: 'devlet',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Endüstri Mühendisliği', 'Fizik Mühendisliği', 'Tıp', 'İşletme'],
  },
  {
    name: 'Ankara Üniversitesi',
    city: 'Ankara',
    type: 'devlet',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'İstatistik', 'Hukuk', 'İşletme', 'Tıp'],
  },
  {
    name: 'Ege Üniversitesi',
    city: 'İzmir',
    type: 'devlet',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Makine Mühendisliği', 'Biyomühendislik', 'İşletme', 'Psikoloji'],
  },
  {
    name: 'Dokuz Eylül Üniversitesi',
    city: 'İzmir',
    type: 'devlet',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Endüstri Mühendisliği', 'Denizcilik İşletmeleri Yönetimi', 'İşletme'],
  },
  {
    name: 'İzmir Yüksek Teknoloji Enstitüsü',
    city: 'İzmir',
    type: 'devlet',
    departments: ['Bilgisayar Mühendisliği', 'Elektronik ve Haberleşme Mühendisliği', 'Mimarlık', 'Makine Mühendisliği', 'Malzeme Bilimi ve Mühendisliği'],
  },
  {
    name: 'Gebze Teknik Üniversitesi',
    city: 'Kocaeli',
    type: 'devlet',
    departments: ['Bilgisayar Mühendisliği', 'Elektronik Mühendisliği', 'Makine Mühendisliği', 'Malzeme Bilimi ve Mühendisliği', 'İşletme'],
  },
  {
    name: 'Marmara Üniversitesi',
    city: 'İstanbul',
    type: 'devlet',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'İşletme', 'İktisat', 'Hukuk', 'İletişim'],
  },
  {
    name: 'İstanbul Üniversitesi',
    city: 'İstanbul',
    type: 'devlet',
    departments: ['Bilgisayar Mühendisliği', 'İşletme', 'İktisat', 'Hukuk', 'Psikoloji', 'Gazetecilik'],
  },
  {
    name: 'İstanbul Üniversitesi-Cerrahpaşa',
    city: 'İstanbul',
    type: 'devlet',
    departments: ['Bilgisayar Mühendisliği', 'Elektronik ve Otomasyon', 'Hemşirelik', 'Tıp', 'Veterinerlik'],
  },
  {
    name: 'Sakarya Üniversitesi',
    city: 'Sakarya',
    type: 'devlet',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Makine Mühendisliği', 'Endüstri Mühendisliği', 'Yönetim Bilişim Sistemleri'],
  },
  {
    name: 'Bursa Uludağ Üniversitesi',
    city: 'Bursa',
    type: 'devlet',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Makine Mühendisliği', 'Otomotiv Mühendisliği', 'İşletme'],
  },
  {
    name: 'Karadeniz Teknik Üniversitesi',
    city: 'Trabzon',
    type: 'devlet',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Yazılım Mühendisliği', 'İnşaat Mühendisliği', 'İşletme'],
  },
  {
    name: 'Eskişehir Teknik Üniversitesi',
    city: 'Eskişehir',
    type: 'devlet',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Havacılık Elektrik ve Elektroniği', 'Makine Mühendisliği', 'Endüstri Mühendisliği'],
  },
  {
    name: 'Anadolu Üniversitesi',
    city: 'Eskişehir',
    type: 'devlet',
    departments: ['Yönetim Bilişim Sistemleri', 'İşletme', 'İktisat', 'Çalışma Ekonomisi ve Endüstri İlişkileri', 'Halkla İlişkiler ve Reklamcılık'],
  },
  {
    name: 'Akdeniz Üniversitesi',
    city: 'Antalya',
    type: 'devlet',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Makine Mühendisliği', 'Turizm İşletmeciliği', 'İşletme'],
  },
  {
    name: 'Çukurova Üniversitesi',
    city: 'Adana',
    type: 'devlet',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Makine Mühendisliği', 'Tekstil Mühendisliği', 'İşletme'],
  },
  {
    name: 'Erciyes Üniversitesi',
    city: 'Kayseri',
    type: 'devlet',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Biyomedikal Mühendisliği', 'Makine Mühendisliği', 'İşletme'],
  },
  {
    name: 'Gazi Üniversitesi',
    city: 'Ankara',
    type: 'devlet',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Makine Mühendisliği', 'Endüstri Mühendisliği', 'İktisat'],
  },
  {
    name: 'Koç Üniversitesi',
    city: 'İstanbul',
    type: 'vakıf',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Endüstri Mühendisliği', 'İşletme', 'Ekonomi', 'Psikoloji'],
  },
  {
    name: 'Sabancı Üniversitesi',
    city: 'İstanbul',
    type: 'vakıf',
    departments: ['Bilgisayar Bilimi ve Mühendisliği', 'Elektronik Mühendisliği', 'Endüstri Mühendisliği', 'Yönetim Bilimleri', 'Ekonomi'],
  },
  {
    name: 'Bilkent Üniversitesi',
    city: 'Ankara',
    type: 'vakıf',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Endüstri Mühendisliği', 'İşletme', 'Ekonomi', 'İletişim ve Tasarımı'],
  },
  {
    name: 'Özyeğin Üniversitesi',
    city: 'İstanbul',
    type: 'vakıf',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Makine Mühendisliği', 'Endüstri Mühendisliği', 'İşletme'],
  },
  {
    name: 'Bahçeşehir Üniversitesi',
    city: 'İstanbul',
    type: 'vakıf',
    departments: ['Bilgisayar Mühendisliği', 'Yazılım Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Yapay Zekâ Mühendisliği', 'İşletme'],
  },
  {
    name: 'Yeditepe Üniversitesi',
    city: 'İstanbul',
    type: 'vakıf',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Genetik ve Biyomühendislik', 'Endüstri Mühendisliği', 'Psikoloji'],
  },
  {
    name: 'TOBB Ekonomi ve Teknoloji Üniversitesi',
    city: 'Ankara',
    type: 'vakıf',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Endüstri Mühendisliği', 'Makine Mühendisliği', 'İşletme'],
  },
  {
    name: 'TED Üniversitesi',
    city: 'Ankara',
    type: 'vakıf',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Endüstri Mühendisliği', 'Psikoloji', 'İşletme'],
  },
  {
    name: 'İstanbul Bilgi Üniversitesi',
    city: 'İstanbul',
    type: 'vakıf',
    departments: ['Bilgisayar Mühendisliği', 'Yazılım Geliştirme', 'İletişim Tasarımı', 'İşletme', 'Uluslararası İlişkiler'],
  },
  {
    name: 'İstanbul Aydın Üniversitesi',
    city: 'İstanbul',
    type: 'vakıf',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Mimarlık', 'İşletme', 'Psikoloji'],
  },
  {
    name: 'Başkent Üniversitesi',
    city: 'Ankara',
    type: 'vakıf',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Yönetim Bilişim Sistemleri', 'İşletme', 'Psikoloji'],
  },
  {
    name: 'Atılım Üniversitesi',
    city: 'Ankara',
    type: 'vakıf',
    departments: ['Bilgisayar Mühendisliği', 'Yazılım Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Mekatronik Mühendisliği', 'İşletme'],
  },
  {
    name: 'Kadir Has Üniversitesi',
    city: 'İstanbul',
    type: 'vakıf',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Yönetim Bilişim Sistemleri', 'İşletme', 'Psikoloji'],
  },
  {
    name: 'Türk-Alman Üniversitesi',
    city: 'İstanbul',
    type: 'devlet',
    departments: ['Bilgisayar Mühendisliği', 'Elektrik-Elektronik Mühendisliği', 'Endüstri Mühendisliği', 'Makine Mühendisliği', 'İşletme'],
  },
  {
    name: 'Galatasaray Üniversitesi',
    city: 'İstanbul',
    type: 'devlet',
    departments: ['Bilgisayar Mühendisliği', 'Endüstri Mühendisliği', 'İktisat', 'İşletme', 'Uluslararası İlişkiler'],
  },
];

export function findUniversityByName(name: string) {
  const normalized = name.trim().toLocaleLowerCase('tr-TR');
  if (!normalized) return null;
  return (
    TURKISH_UNIVERSITY_OPTIONS.find(
      (option) => option.name.trim().toLocaleLowerCase('tr-TR') === normalized,
    ) ?? null
  );
}

export const DEFAULT_SKILL_CATEGORIES = [
  'Yazılım',
  'Donanım',
  'Veri / AI',
  'Tasarım',
  'Proje / Operasyon',
  'Dil / İletişim',
  'Diğer',
] as const;


export const OFFICIAL_TURKISH_UNIVERSITY_NAMES = Array.from(new Set([
  ...GENERATED_TURKISH_UNIVERSITY_NAMES,
  ...TURKISH_UNIVERSITY_OPTIONS.map((item) => item.name),
])).sort((left, right) => left.localeCompare(right, 'tr'));
