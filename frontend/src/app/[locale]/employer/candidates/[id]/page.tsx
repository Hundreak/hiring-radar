'use client';

import {useParams} from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  Award,
  Bookmark,
  Briefcase,
  Building2,
  Calendar,
  CheckCircle2,
  ChevronRight,
  Clock,
  Download,
  FileText,
  Globe,
  GraduationCap,
  Mail,
  MapPin,
  MessageSquare,
  Phone,
  Send,
  Sparkles,
  Star,
  ThumbsDown,
  ThumbsUp,
  X,
  XCircle,
} from 'lucide-react';
import {useState} from 'react';

import {Badge} from '@/components/ui/badge';
import {Button} from '@/components/ui/button';
import {cn} from '@/lib/utils';

/* ─── Demo data ─── */
const CANDIDATE_DETAILS: Record<number, {
  name: string;
  initials: string;
  headline: string;
  email: string;
  phone: string;
  location: string;
  experience: number;
  matchScore: number;
  skills: {name: string; level: string}[];
  education: {school: string; degree: string; field: string; years: string}[];
  experience_entries: {title: string; company: string; period: string; description: string}[];
  summary: string;
  aiAssessment: string;
  strengths: string[];
  gaps: string[];
  languages: {name: string; level: string}[];
  certifications: string[];
}> = {
  1: {
    name: 'Ahmet Yılmaz',
    initials: 'AY',
    headline: 'Senior React Developer',
    email: 'ahmet.yilmaz@email.com',
    phone: '+90 532 123 4567',
    location: 'İstanbul, Türkiye',
    experience: 6,
    matchScore: 96,
    skills: [
      {name: 'React', level: 'Uzman'},
      {name: 'TypeScript', level: 'Uzman'},
      {name: 'Node.js', level: 'İleri'},
      {name: 'GraphQL', level: 'İleri'},
      {name: 'Next.js', level: 'İleri'},
      {name: 'CSS/Tailwind', level: 'Uzman'},
    ],
    education: [
      {school: 'İstanbul Teknik Üniversitesi', degree: 'Lisans', field: 'Bilgisayar Mühendisliği', years: '2013-2018'},
    ],
    experience_entries: [
      {title: 'Senior Frontend Developer', company: 'TechCorp A.Ş.', period: '2021 - Günümüz', description: 'Büyük ölçekli React uygulamaları geliştirme. Mikro-frontend mimarisi kurulumu. 8 kişilik frontend ekibine liderlik.'},
      {title: 'Frontend Developer', company: 'StartupX', period: '2019 - 2021', description: 'Sıfırdan React/TypeScript ürün geliştirme. Design system oluşturma. CI/CD pipeline kurulumu.'},
      {title: 'Junior Web Developer', company: 'AgencyXYZ', period: '2018 - 2019', description: 'Çeşitli müşteri projelerinde frontend geliştirme. Responsive tasarım implementasyonu.'},
    ],
    summary: '6 yıllık deneyime sahip, React ve modern JavaScript ekosisteminde uzmanlaşmış frontend geliştirici. Mikro-frontend mimarileri, design sistemleri ve performans optimizasyonu konularında güçlü. Takım liderliği ve mentorluk deneyimi var.',
    aiAssessment: 'Aday, pozisyon gereksinimleriyle %96 oranında eşleşiyor. React ve TypeScript konusunda derin uzmanlığı var. Takım liderliği deneyimi ve ölçeklenebilir mimari bilgisi güçlü yönleri. GraphQL ve Next.js deneyimi değer katıyor. İletişim becerileri ve proje yönetimi deneyimi ek avantaj. Mülakat sürecinde mimari kararlar ve performans optimizasyonu konuları derinleştirilebilir.',
    strengths: ['React/TypeScript uzmanlığı', 'Mikro-frontend mimarisi deneyimi', 'Takım liderliği ve mentorluk', 'GraphQL ve modern API tasarımı', 'Performans optimizasyonu'],
    gaps: ['Backend deneyimi sınırlı (pozisyon için kritik değil)', 'Go dili bilgisi yok'],
    languages: [
      {name: 'Türkçe', level: 'Ana dil'},
      {name: 'İngilizce', level: 'C1 - İleri'},
    ],
    certifications: ['AWS Certified Developer', 'Meta Frontend Professional'],
  },
  2: {
    name: 'Zeynep Kaya',
    initials: 'ZK',
    headline: 'Product Designer (UI/UX)',
    email: 'zeynep.kaya@email.com',
    phone: '+90 533 987 6543',
    location: 'Ankara, Türkiye',
    experience: 5,
    matchScore: 92,
    skills: [
      {name: 'Figma', level: 'Uzman'},
      {name: 'Design Systems', level: 'Uzman'},
      {name: 'Prototyping', level: 'İleri'},
      {name: 'User Research', level: 'İleri'},
      {name: 'HTML/CSS', level: 'Orta'},
    ],
    education: [
      {school: 'Orta Doğu Teknik Üniversitesi', degree: 'Lisans', field: 'Grafik Tasarım', years: '2014-2019'},
    ],
    experience_entries: [
      {title: 'Senior Product Designer', company: 'DesignHub', period: '2022 - Günümüz', description: 'B2B SaaS ürünlerinde end-to-end tasarım süreci. Design system yönetimi. Kullanıcı araştırmaları ve usability testleri.'},
      {title: 'UI/UX Designer', company: 'CreativeAgency', period: '2020 - 2022', description: 'Mobil ve web uygulamaları için UI tasarımı. Etkileşim tasarımı ve prototipleme.'},
      {title: 'Junior Designer', company: 'StartupCo', period: '2019 - 2020', description: 'Marka kimliği ve web tasarımı. UI kit oluşturma.'},
    ],
    summary: '5 yıllık deneyimli ürün tasarımcısı. Design sistemleri ve kullanıcı araştırmaları konusunda uzman. B2B SaaS ürünlerinde end-to-end tasarım süreci yönetimi. Figma ve modern tasarım araçlarında ileri düzey.',
    aiAssessment: 'Aday, pozisyon gereksinimleriyle %92 oranında eşleşiyor. Design sistemleri ve Figma konusunda uzman seviyede. Kullanıcı araştırmaları deneyimi ve B2B SaaS geçmişi güçlü yönleri. HTML/CSS bilgisi developerlarla iletişimi kolaylaştırıyor.',
    strengths: ['Design systems uzmanlığı', 'Kullanıcı araştırmaları deneyimi', 'Figma ve modern araçlar', 'B2B SaaS ürün deneyimi'],
    gaps: ['Canlı ürün deneyimi sınırlı', 'Motion design deneyimi az'],
    languages: [
      {name: 'Türkçe', level: 'Ana dil'},
      {name: 'İngilizce', level: 'B2 - Orta/İleri'},
    ],
    certifications: ['Google UX Design Certificate'],
  },
};

const FALLBACK_CANDIDATE = {
  name: 'Aday',
  initials: 'AD',
  headline: 'Yazılım Geliştirici',
  email: 'aday@email.com',
  phone: '+90 5XX XXX XXXX',
  location: 'Türkiye',
  experience: 3,
  matchScore: 75,
  skills: [
    {name: 'JavaScript', level: 'İleri'},
    {name: 'React', level: 'Orta'},
    {name: 'Node.js', level: 'Orta'},
  ],
  education: [
    {school: 'Üniversite', degree: 'Lisans', field: 'Bilgisayar Mühendisliği', years: '2015-2020'},
  ],
  experience_entries: [
    {title: 'Software Developer', company: 'Teknoloji Şirketi', period: '2020 - Günümüz', description: 'Web uygulamaları geliştirme.'},
  ],
  summary: 'Yazılım geliştirme alanında deneyimli aday.',
  aiAssessment: 'Aday pozisyonla orta düzeyde eşleşiyor.',
  strengths: ['Temel yazılım becerileri'],
  gaps: ['Uzmanlaşma alanı belirgin değil'],
  languages: [
    {name: 'Türkçe', level: 'Ana dil'},
    {name: 'İngilizce', level: 'B1 - Orta'},
  ],
  certifications: [],
};

function MatchBreakdown({score, strengths, gaps}: {score: number; strengths: string[]; gaps: string[]}) {
  const breakdownItems = [
    {label: 'Beceri Uyumu', value: Math.round(score * 0.98), weight: 35},
    {label: 'Deneyim', value: Math.round(score * 0.95), weight: 25},
    {label: 'Eğitim', value: Math.round(score * 0.92), weight: 15},
    {label: 'Lokasyon', value: Math.round(score * 0.88), weight: 15},
    {label: 'Dil', value: Math.round(score * 0.94), weight: 10},
  ];

  const colors = score >= 85 ? {text: 'text-match-high', fill: 'bg-match-high'} : score >= 70 ? {text: 'text-match-mid', fill: 'bg-match-mid'} : {text: 'text-match-low', fill: 'bg-match-low'};

  return (
    <div className="space-y-4">
      {/* Overall Score */}
      <div className="flex items-center gap-6">
        <div className={cn('score-ring-lg animate-score-pop', colors.fill.replace('bg-', 'border-'), colors.text)}>
          <span>{score}</span>
        </div>
        <div>
          <div className="text-sm font-bold text-foreground">Genel Eşleşme Skoru</div>
          <div className="text-xs text-muted-foreground mt-0.5">
            {score >= 90 ? 'Mükemmel uyum — Hemen iletişime geçin' : score >= 80 ? 'Çok iyi uyum — Kısa listeye alın' : 'İyi uyum — Değerlendirmeye değer'}
          </div>
        </div>
      </div>

      {/* Breakdown bars */}
      <div className="space-y-2.5 pt-2">
        {breakdownItems.map((item) => (
          <div key={item.label}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-muted-foreground">{item.label}</span>
              <span className="text-xs font-bold text-foreground">{item.value}%</span>
            </div>
            <div className="match-bar-bg">
              <div
                className={cn('match-bar-fill', colors.fill.split(' ')[0])}
                style={{width: `${item.value}%`}}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Strengths */}
      <div className="rounded-2xl border border-primary/20 bg-primary/[0.04] p-4">
        <div className="flex items-center gap-2 mb-3">
          <CheckCircle2 className="size-4 text-success" />
          <span className="text-xs font-bold uppercase tracking-wide text-success">Güçlü Yönler</span>
        </div>
        <ul className="space-y-1.5">
          {strengths.map((s) => (
            <li key={s} className="flex items-start gap-2 text-[13px] text-foreground">
              <ThumbsUp className="size-3.5 mt-0.5 text-success shrink-0" />
              {s}
            </li>
          ))}
        </ul>
      </div>

      {/* Gaps */}
      <div className="rounded-2xl border border-warning/20 bg-warning/[0.04] p-4">
        <div className="flex items-center gap-2 mb-3">
          <XCircle className="size-4 text-warning" />
          <span className="text-xs font-bold uppercase tracking-wide text-warning">Gelişim Alanları</span>
        </div>
        <ul className="space-y-1.5">
          {gaps.map((g) => (
            <li key={g} className="flex items-start gap-2 text-[13px] text-foreground">
              <ThumbsDown className="size-3.5 mt-0.5 text-warning shrink-0" />
              {g}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default function CandidateDetailPage() {
  const params = useParams();
  const id = Number(params.id);
  const candidate = CANDIDATE_DETAILS[id] || FALLBACK_CANDIDATE;
  const [saved, setSaved] = useState(false);

  const scoreColor = candidate.matchScore >= 85 ? 'text-match-high' : candidate.matchScore >= 70 ? 'text-match-mid' : 'text-match-low';

  return (
    <div className="space-y-6">
      {/* Back + Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <Link
          href="/tr/employer/candidates"
          className="inline-flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground transition"
        >
          <ArrowLeft className="size-4" />
          Adaylara Dön
        </Link>
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setSaved(!saved)}
          >
            <Bookmark className={cn('size-4 mr-2', saved && 'fill-primary text-primary')} />
            {saved ? 'Kaydedildi' : 'Kaydet'}
          </Button>
          <Button size="sm" variant="secondary">
            <Send className="size-4 mr-2" />
            Mesaj Gönder
          </Button>
          <Button size="sm">
            <Mail className="size-4 mr-2" />
            İletişime Geç
          </Button>
        </div>
      </div>

      {/* Profile Header */}
      <div className="surface-card p-6">
        <div className="flex flex-col sm:flex-row items-start gap-5">
          <div className="candidate-avatar size-20 text-2xl rounded-3xl">{candidate.initials}</div>
          <div className="flex-1 min-w-0">
            <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-1">
              <h1 className="text-xl font-bold">{candidate.name}</h1>
              <div className="flex items-center gap-2">
                <Badge tone={candidate.matchScore >= 90 ? 'success' : candidate.matchScore >= 75 ? 'info' : 'warning'} className="text-[11px]">
                  {candidate.matchScore}% Eşleşme
                </Badge>
                <Badge tone="default" className="text-[11px]">{candidate.experience} Yıl Deneyim</Badge>
              </div>
            </div>
            <p className="text-sm text-muted-foreground mb-3">{candidate.headline}</p>
            <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-1.5">
                <MapPin className="size-3.5" />
                {candidate.location}
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Mail className="size-3.5" />
                {candidate.email}
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Phone className="size-3.5" />
                {candidate.phone}
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Globe className="size-3.5" />
                {candidate.languages.map((l) => l.name).join(', ')}
              </span>
            </div>
          </div>
          <div className="flex flex-col items-center gap-1 shrink-0 self-center">
            <div className={cn(
              'flex size-16 items-center justify-center rounded-full border-4 text-lg font-extrabold text-white',
              scoreColor.replace('text-', 'border-').replace('match-', 'bg-')
            )}>
              {candidate.matchScore}
            </div>
            <span className="text-[10px] text-muted-foreground font-semibold">MATCH</span>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="employer-grid-2" style={{gridTemplateColumns: '1fr 360px', gap: '20px'}}>
        {/* Left Column */}
        <div className="space-y-5">
          {/* Professional Summary */}
          <div className="surface-card p-5">
            <h2 className="text-sm font-bold mb-3 flex items-center gap-2">
              <FileText className="size-4 text-muted-foreground" />
              Profesyonel Özet
            </h2>
            <p className="text-[13px] leading-relaxed text-foreground">{candidate.summary}</p>
          </div>

          {/* Experience */}
          <div className="surface-card p-5">
            <h2 className="text-sm font-bold mb-4 flex items-center gap-2">
              <Briefcase className="size-4 text-muted-foreground" />
              İş Deneyimi
            </h2>
            <div className="space-y-4">
              {candidate.experience_entries.map((exp, i) => (
                <div key={i} className="relative pl-5 border-l-2 border-border">
                  <div className="absolute -left-[5px] top-1.5 size-2 rounded-full bg-primary" />
                  <div className="text-sm font-semibold">{exp.title}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">
                    <span className="inline-flex items-center gap-1">
                      <Building2 className="size-3" />
                      {exp.company}
                    </span>
                    <span className="mx-2">·</span>
                    <span className="inline-flex items-center gap-1">
                      <Calendar className="size-3" />
                      {exp.period}
                    </span>
                  </div>
                  <p className="text-[12px] text-muted-foreground mt-1.5 leading-relaxed">{exp.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Education */}
          <div className="surface-card p-5">
            <h2 className="text-sm font-bold mb-4 flex items-center gap-2">
              <GraduationCap className="size-4 text-muted-foreground" />
              Eğitim
            </h2>
            <div className="space-y-3">
              {candidate.education.map((edu, i) => (
                <div key={i} className="flex items-start gap-3">
                  <div className="flex size-9 items-center justify-center rounded-xl bg-secondary text-secondary-foreground shrink-0">
                    <GraduationCap className="size-4" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold">{edu.school}</div>
                    <div className="text-xs text-muted-foreground">{edu.degree} · {edu.field}</div>
                    <div className="text-[11px] text-muted-foreground mt-0.5">{edu.years}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Skills */}
          <div className="surface-card p-5">
            <h2 className="text-sm font-bold mb-4 flex items-center gap-2">
              <Sparkles className="size-4 text-muted-foreground" />
              Yetenekler
            </h2>
            <div className="flex flex-wrap gap-2">
              {candidate.skills.map((skill) => (
                <div key={skill.name} className="flex items-center gap-2 rounded-xl border border-border bg-surface-muted px-3 py-2">
                  <span className="text-[12px] font-semibold">{skill.name}</span>
                  <span className="text-[10px] text-muted-foreground font-medium">{skill.level}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Certifications */}
          {candidate.certifications.length > 0 && (
            <div className="surface-card p-5">
              <h2 className="text-sm font-bold mb-3 flex items-center gap-2">
                <Award className="size-4 text-muted-foreground" />
                Sertifikalar
              </h2>
              <div className="flex flex-wrap gap-2">
                {candidate.certifications.map((cert) => (
                  <Badge key={cert} tone="accent" className="text-[11px]">{cert}</Badge>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Match Analysis & Actions */}
        <div className="space-y-5">
          {/* Match Analysis */}
          <div className="surface-card p-5">
            <h2 className="text-sm font-bold mb-4 flex items-center gap-2">
              <Sparkles className="size-4 text-accent" />
              Eşleşme Analizi
            </h2>
            <MatchBreakdown score={candidate.matchScore} strengths={candidate.strengths} gaps={candidate.gaps} />
          </div>

          {/* AI Assessment */}
          <div className="surface-card p-5 border-primary/20">
            <div className="flex items-center gap-2 mb-3">
              <div className="flex size-7 items-center justify-center rounded-lg bg-secondary">
                <Sparkles className="size-4 text-secondary-foreground" />
              </div>
              <h2 className="text-sm font-bold">AI Değerlendirmesi</h2>
            </div>
            <p className="text-[12px] leading-relaxed text-muted-foreground">{candidate.aiAssessment}</p>
          </div>

          {/* Quick Actions */}
          <div className="surface-card p-5">
            <h2 className="text-sm font-bold mb-4">İşlemler</h2>
            <div className="space-y-2">
              <Button className="w-full justify-start" size="sm">
                <CheckCircle2 className="size-4 mr-2" />
                Kısa Listeye Al
              </Button>
              <Button variant="secondary" className="w-full justify-start" size="sm">
                <Calendar className="size-4 mr-2" />
                Mülakat Planla
              </Button>
              <Button variant="secondary" className="w-full justify-start" size="sm">
                <Download className="size-4 mr-2" />
                CV İndir
              </Button>
              <Button variant="ghost" className="w-full justify-start text-danger hover:text-danger hover:bg-danger/10" size="sm">
                <X className="size-4 mr-2" />
                Reddet
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
