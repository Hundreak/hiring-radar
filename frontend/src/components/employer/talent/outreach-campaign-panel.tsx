'use client';

import {
  AlertTriangle,
  ArrowRight,
  AtSign,
  BadgeCheck,
  Briefcase,
  CalendarClock,
  CheckCircle2,
  ClipboardCopy,
  Clock3,
  FileText,
  Gauge,
  Info,
  Layers3,
  Mail,
  MessageCircle,
  MousePointer2,
  PenLine,
  RefreshCcw,
  Send,
  ShieldCheck,
  Sparkles,
  Target,
  TimerReset,
  Users,
  WandSparkles,
  type LucideIcon,
} from 'lucide-react';
import {useMemo, useState} from 'react';

import {CampaignDetailDrawer} from '@/components/employer/talent/campaign-detail-drawer';
import {ScoreBadge, StatusBadge, SurfaceCard} from '@/components/employer/ui';
import {Button} from '@/components/ui/button';
import {formatCompactNumber} from '@/lib/employer-format';
import {getTalentWorkflowCopy} from '@/lib/employer-talent-workflow-copy';
import {cn} from '@/lib/utils';
import type {EmployerCandidateOpportunity} from '@/types/employer';
import type {
  EmployerOutreachCampaign,
  EmployerOutreachCampaignCreatePayload,
} from '@/types/employer-outreach';

type OutreachTone = 'warm' | 'direct' | 'premium' | 'technical';
type OutreachChannel = 'email' | 'linkedin' | 'whatsapp';
type OutreachTemplate = 'role-fit' | 'quick-intro' | 'technical-depth' | 'salary-transparent';
type PersonalizationDepth = 'balanced' | 'deep' | 'concise';
type FollowUpCadence = 'none' | 'three_day' | 'five_day';

type OutreachCampaignPanelProps = {
  candidates: EmployerCandidateOpportunity[];
  selectedCandidateId?: number;
  onSelect: (candidateId: number) => void;
  onOpenProfile: (candidateId: number) => void;
  onTagCandidates?: (candidateIds: number[], tag: string) => void;
  onNoteCandidates?: (candidateIds: number[], note: string) => void;
  onCreateCampaign?: (payload: EmployerOutreachCampaignCreatePayload) => Promise<void> | void;
  campaignDrafts?: EmployerOutreachCampaign[];
  syncState?: 'syncing' | 'synced' | 'offline';
  locale: string;
};

const CHANNEL_META: Record<OutreachChannel, {label: string; helper: string; icon: LucideIcon; responseBoost: number; risk: string}> = {
  email: {label: 'E-posta', helper: 'Kurumsal, ölçülebilir ve takip edilebilir', icon: Mail, responseBoost: 4, risk: 'Konu satırı net olmalı'},
  linkedin: {label: 'LinkedIn', helper: 'Pasif adaylara sıcak ve profesyonel temas', icon: AtSign, responseBoost: 7, risk: 'Mesaj kısa tutulmalı'},
  whatsapp: {label: 'WhatsApp', helper: 'Sıcak adaylarda hızlı kapanış', icon: MessageCircle, responseBoost: 10, risk: 'İzin ve bağlam hassas'},
};

const TONE_META: Record<OutreachTone, {label: string; helper: string}> = {
  warm: {label: 'Sıcak', helper: 'Samimi ama profesyonel'},
  direct: {label: 'Net', helper: 'Kısa, aksiyon odaklı'},
  premium: {label: 'Premium', helper: 'Üst düzey aday dili'},
  technical: {label: 'Teknik', helper: 'Beceri kanıtını öne çıkarır'},
};

const TEMPLATE_META: Record<OutreachTemplate, {label: string; helper: string; badge: string}> = {
  'role-fit': {label: 'Rol uyumu', helper: 'Match gerekçesini anlatır', badge: 'Genel'},
  'quick-intro': {label: 'Hızlı tanışma', helper: 'Cevap bariyerini düşürür', badge: 'Kısa'},
  'technical-depth': {label: 'Teknik derinlik', helper: 'Senior/lead adaylar için', badge: 'Senior'},
  'salary-transparent': {label: 'Şeffaf teklif', helper: 'Maaş ve çalışma modelini açar', badge: 'Şeffaf'},
};

const FOLLOW_UP_META: Record<FollowUpCadence, {label: string; helper: string}> = {
  none: {label: 'Takip yok', helper: 'Sadece ilk temas'},
  three_day: {label: '3 gün sonra', helper: 'Sıcak adaylar için ideal'},
  five_day: {label: '5 gün sonra', helper: 'Daha sakin takip'},
};

const PERSONALIZATION_META: Record<PersonalizationDepth, {label: string; helper: string}> = {
  concise: {label: 'Kısa', helper: 'LinkedIn/WhatsApp için uygun'},
  balanced: {label: 'Dengeli', helper: 'En iyi varsayılan'},
  deep: {label: 'Derin', helper: 'Senior adaylarda kanıtlı anlatım'},
};

function salaryText(candidate: EmployerCandidateOpportunity) {
  if (!candidate.salaryExpectation) return 'beklenti belirtilmemiş';
  const {min, max, currency} = candidate.salaryExpectation;
  return `${formatCompactNumber(min)}-${formatCompactNumber(max)} ${currency}`;
}

function availabilityLabel(candidate: EmployerCandidateOpportunity) {
  if (candidate.availability === 'immediate') return 'hemen';
  if (candidate.availability === 'two_weeks') return '2 hafta içinde';
  if (candidate.availability === 'one_month') return '1 ay içinde';
  return 'pasif ama değerlendirilebilir';
}

function workModelLabel(candidate: EmployerCandidateOpportunity) {
  if (candidate.workPreference === 'remote') return 'remote';
  if (candidate.workPreference === 'hybrid') return 'hibrit';
  if (candidate.workPreference === 'office') return 'ofis';
  return 'esnek';
}

function getCandidateResponseScore(candidate: EmployerCandidateOpportunity, channel: OutreachChannel) {
  const availabilityBoost = candidate.availability === 'immediate' ? 13 : candidate.availability === 'two_weeks' ? 9 : candidate.availability === 'one_month' ? 4 : -4;
  const sourceBoost = candidate.source === 'talent_radar' ? 6 : candidate.source === 'referral' ? 8 : candidate.source === 'linkedin' ? 5 : 2;
  const score = Math.round(candidate.intentScore * 0.48 + candidate.matchScore * 0.28 + availabilityBoost + sourceBoost + CHANNEL_META[channel].responseBoost);
  return Math.max(34, Math.min(96, score));
}

function getPrimarySkill(candidate: EmployerCandidateOpportunity) {
  return candidate.skills.find((skill) => skill.matched)?.name ?? candidate.skills[0]?.name ?? 'rol odağı';
}

function matchedSkillsText(candidate: EmployerCandidateOpportunity, limit = 3) {
  return candidate.skills.filter((skill) => skill.matched).slice(0, limit).map((skill) => skill.name).join(', ') || getPrimarySkill(candidate);
}

function buildSubject(candidate: EmployerCandidateOpportunity, template: OutreachTemplate) {
  const skill = getPrimarySkill(candidate);
  if (template === 'technical-depth') return `${skill} deneyiminiz için kısa bir rol paylaşımı`;
  if (template === 'salary-transparent') return `Şeffaf rol paylaşımı: ${candidate.targetRole ?? skill}`;
  if (template === 'quick-intro') return `${candidate.name.split(' ')[0]}, kısa bir tanışma yapabilir miyiz?`;
  return `${candidate.targetRole ?? skill} rolü için güçlü bir eşleşme`;
}

function buildMessage({
  candidate,
  tone,
  template,
  channel,
  includeSalary,
  includeCalendar,
  followUp,
  personalizationDepth,
}: {
  candidate: EmployerCandidateOpportunity;
  tone: OutreachTone;
  template: OutreachTemplate;
  channel: OutreachChannel;
  includeSalary: boolean;
  includeCalendar: boolean;
  followUp: FollowUpCadence;
  personalizationDepth: PersonalizationDepth;
}) {
  const firstName = candidate.name.split(' ')[0] ?? candidate.name;
  const primarySkill = getPrimarySkill(candidate);
  const matchedSkills = matchedSkillsText(candidate, personalizationDepth === 'deep' ? 4 : 3);
  const workModel = workModelLabel(candidate);
  const salary = salaryText(candidate);
  const availability = availabilityLabel(candidate);
  const evidenceLine = personalizationDepth === 'deep'
    ? `Profilinizde ${matchedSkills} tarafında güçlü kanıtlar ve ${candidate.experience} yıllık deneyim sinyali görüyorum.`
    : personalizationDepth === 'concise'
      ? `${matchedSkills} odağınız rolümüzle örtüşüyor.`
      : `${matchedSkills} tarafındaki deneyiminiz ve ${candidate.matchScore}/100 match sinyali açık rolümüzle güçlü bir uyum gösteriyor.`;

  const opener = tone === 'premium'
    ? `Merhaba ${firstName},\n\nProfilinizi incelerken özellikle ${primarySkill} tarafındaki derinlik ve ürün etkisi dikkatimi çekti.`
    : tone === 'technical'
      ? `Merhaba ${firstName},\n\n${primarySkill} odağındaki teknik deneyiminiz açık rolümüzün gereksinimleriyle güçlü eşleşiyor.`
      : tone === 'direct'
        ? `Merhaba ${firstName},\n\nAçık rolümüzle profiliniz arasında güçlü bir eşleşme görüyoruz.`
        : `Merhaba ${firstName},\n\nProfilinizi gördüm ve açık rolümüzle oldukça iyi bir uyum olabileceğini düşündüm.`;

  const templateBody = template === 'quick-intro'
    ? `${evidenceLine}\n\nUygunsa bu hafta 15 dakikalık kısa bir tanışma yapıp rolün kapsamını, ekip yapısını ve süreci paylaşmak isterim.`
    : template === 'technical-depth'
      ? `${evidenceLine}\n\nRolde teknik sahiplik, ölçeklenebilir ürün kararları ve ekip içi kalite standardı kritik. Bu yüzden ilk görüşmede teknik kapsamı açıkça konuşmak isteriz.`
      : template === 'salary-transparent'
        ? `${evidenceLine}\n\nRol ${workModel} çalışma modelinde. ${includeSalary ? `Görünen beklenti bandınız (${salary}) üzerinden şeffaf bir değerlendirme yapabiliriz.` : 'Maaş ve çalışma modeli beklentilerini ilk görüşmede netleştirebiliriz.'}`
        : `${evidenceLine}\n\nÖne çıkan uyum sinyalleri:\n- Match skoru: ${candidate.matchScore}/100\n- Öne çıkan beceriler: ${matchedSkills}\n- Çalışma modeli uyumu: ${workModel}\n- Müsaitlik: ${availability}`;

  const channelLine = channel === 'whatsapp'
    ? 'İsterseniz önce kısa bir WhatsApp mesajıyla rolün ana detaylarını paylaşabilirim.'
    : channel === 'linkedin'
      ? 'LinkedIn üzerinden kısa bir tanışma ile başlayıp detayları paylaşabiliriz.'
      : 'Size rol kapsamını, ekip yapısını ve süreci kısa bir e-posta akışıyla net paylaşabiliriz.';

  const calendarLine = includeCalendar ? '\n\nUygunsa takvim linkimi paylaşabilirim; size uygun 15-20 dakikalık bir slot seçebilirsiniz.' : '';
  const followUpLine = followUp === 'none' ? '' : `\n\nNot: Yanıt verememeniz durumunda ${followUp === 'three_day' ? '3' : '5'} gün sonra kısa bir takip mesajı göndereceğim.`;
  const salaryLine = includeSalary && template !== 'salary-transparent' ? `\n\nSüreci şeffaf yürütmek için maaş bandı, çalışma modeli ve görüşme adımlarını ilk görüşmede net paylaşacağız.` : '';

  return `${opener}\n\n${templateBody}\n\n${channelLine}${salaryLine}${calendarLine}${followUpLine}\n\nİlgilenir misiniz?`;
}

function evaluateMessageQuality(message: string, subject: string, selectedCount: number, channel: OutreachChannel) {
  const words = message.trim().split(/\s+/).filter(Boolean).length;
  const hasQuestion = /\?/.test(message);
  const hasSalary = message.toLocaleLowerCase('tr-TR').includes('maaş');
  const hasCalendar = message.toLocaleLowerCase('tr-TR').includes('takvim') || message.toLocaleLowerCase('tr-TR').includes('slot');
  const tooLong = channel === 'linkedin' ? words > 145 : channel === 'whatsapp' ? words > 95 : words > 220;
  const tooShort = words < 45;
  const subjectWeak = channel === 'email' && subject.trim().length < 12;

  const warnings: string[] = [];
  const strengths: string[] = [];
  const blockers: string[] = [];

  if (tooLong) warnings.push(`${CHANNEL_META[channel].label} için mesaj biraz uzun; yanıt oranı düşebilir.`);
  if (tooShort) warnings.push('Mesaj çok kısa; adayın neden seçildiği yeterince görünmeyebilir.');
  if (subjectWeak) blockers.push('E-posta için daha net bir konu satırı gerekli.');
  if (!hasQuestion) warnings.push('Mesaj net bir soru/CTA ile bitmiyor.');
  if (selectedCount > 8) warnings.push('İlk taslak için 8+ aday geniş bir kitle; kişiselleştirme kontrolü önerilir.');

  if (hasSalary) strengths.push('Maaş/şeffaflık sinyali var.');
  if (hasCalendar) strengths.push('Takvim/sonraki adım net.');
  if (hasQuestion) strengths.push('Cevap vermesi kolay bir CTA var.');
  if (words >= 60 && !tooLong) strengths.push('Uzunluk kanal için dengeli.');

  const score = Math.max(32, Math.min(98, 86 - warnings.length * 9 - blockers.length * 18 + strengths.length * 4));
  return {score, warnings, strengths, blockers, words};
}

function getReadinessTone(score: number): 'success' | 'warning' | 'danger' | 'info' {
  if (score >= 82) return 'success';
  if (score >= 68) return 'warning';
  return 'danger';
}

export function OutreachCampaignPanel({
  candidates,
  selectedCandidateId,
  locale,
  onSelect,
  onOpenProfile,
  onTagCandidates,
  onNoteCandidates,
  onCreateCampaign,
  campaignDrafts = [],
  syncState = 'synced',
}: OutreachCampaignPanelProps) {
  const [selectedIds, setSelectedIds] = useState<number[]>(() => candidates.slice(0, 3).map((candidate) => candidate.id));
  const [channel, setChannel] = useState<OutreachChannel>('email');
  const [tone, setTone] = useState<OutreachTone>('warm');
  const [template, setTemplate] = useState<OutreachTemplate>('role-fit');
  const [includeSalary, setIncludeSalary] = useState(true);
  const [includeCalendar, setIncludeCalendar] = useState(true);
  const [followUp, setFollowUp] = useState<FollowUpCadence>('three_day');
  const [personalizationDepth, setPersonalizationDepth] = useState<PersonalizationDepth>('balanced');
  const [campaignCreated, setCampaignCreated] = useState(false);
  const [campaignSaving, setCampaignSaving] = useState(false);
  const [campaignError, setCampaignError] = useState<string | null>(null);
  const [messageEdits, setMessageEdits] = useState<Record<number, string>>({});
  const [subjectEdits, setSubjectEdits] = useState<Record<number, string>>({});
  const [previewMode, setPreviewMode] = useState<'composer' | 'quality' | 'drafts'>('composer');
  const copy = getTalentWorkflowCopy(locale);
  const [selectedDraftId, setSelectedDraftId] = useState<string | null>(null);

  const selectedCandidates = useMemo(
    () => candidates.filter((candidate) => selectedIds.includes(candidate.id)),
    [candidates, selectedIds]
  );

  const activeCandidate = useMemo(() => {
    return candidates.find((candidate) => candidate.id === selectedCandidateId)
      ?? selectedCandidates[0]
      ?? candidates[0];
  }, [candidates, selectedCandidateId, selectedCandidates]);

  const activeCandidateId = activeCandidate?.id ?? 0;
  const selectedDraft = useMemo(
    () => campaignDrafts.find((draft) => draft.id === selectedDraftId) ?? null,
    [campaignDrafts, selectedDraftId]
  );

  const generatedSubject = activeCandidate ? buildSubject(activeCandidate, template) : '';
  const activeSubject = subjectEdits[activeCandidateId] ?? generatedSubject;
  const generatedMessage = activeCandidate
    ? buildMessage({candidate: activeCandidate, tone, template, channel, includeSalary, includeCalendar, followUp, personalizationDepth})
    : '';
  const activeMessage = messageEdits[activeCandidateId] ?? generatedMessage;

  const avgResponse = useMemo(() => {
    if (selectedCandidates.length === 0) return 0;
    return Math.round(selectedCandidates.reduce((total, candidate) => total + getCandidateResponseScore(candidate, channel), 0) / selectedCandidates.length);
  }, [selectedCandidates, channel]);

  const quality = useMemo(
    () => evaluateMessageQuality(activeMessage, activeSubject, selectedCandidates.length, channel),
    [activeMessage, activeSubject, selectedCandidates.length, channel]
  );

  const highIntentCount = selectedCandidates.filter((candidate) => candidate.intentScore >= 80).length;
  const immediateCount = selectedCandidates.filter((candidate) => candidate.availability === 'immediate' || candidate.availability === 'two_weeks').length;
  const readinessScore = Math.round(avgResponse * 0.45 + quality.score * 0.4 + Math.min(18, selectedCandidates.length * 2));

  const toggleCandidate = (candidateId: number) => {
    setSelectedIds((current) => current.includes(candidateId) ? current.filter((id) => id !== candidateId) : [...current, candidateId]);
    onSelect(candidateId);
    setCampaignCreated(false);
  };

  const resetActiveMessage = () => {
    setMessageEdits((current) => {
      const next = {...current};
      delete next[activeCandidateId];
      return next;
    });
    setSubjectEdits((current) => {
      const next = {...current};
      delete next[activeCandidateId];
      return next;
    });
  };

  const candidateMessagePayload = selectedCandidates.map((candidate) => {
    const subject = subjectEdits[candidate.id] ?? buildSubject(candidate, template);
    const message = messageEdits[candidate.id] ?? buildMessage({candidate, tone, template, channel, includeSalary, includeCalendar, followUp, personalizationDepth});
    return {candidate_id: candidate.id, subject, message, response_score: getCandidateResponseScore(candidate, channel)};
  });

  const createCampaign = async () => {
    if (selectedCandidates.length === 0 || campaignSaving) return;

    const candidateIds = selectedCandidates.map((candidate) => candidate.id);
    const note = `${CHANNEL_META[channel].label} kanalıyla ${TEMPLATE_META[template].label.toLocaleLowerCase('tr-TR')} davet kampanyasına eklendi. Mesaj kalite skoru: ${quality.score}/100.`;

    setCampaignSaving(true);
    setCampaignError(null);
    try {
      if (onCreateCampaign) {
        await onCreateCampaign({
          name: `${TEMPLATE_META[template].label} / ${CHANNEL_META[channel].label} / ${selectedCandidates.length} aday`,
          candidate_ids: candidateIds,
          channel,
          tone,
          template,
          include_salary: includeSalary,
          include_calendar: includeCalendar,
          message_preview: activeMessage,
          response_rate: avgResponse,
          metadata: {
            composer_version: 'v2',
            subject_preview: activeSubject,
            selected_count: selectedCandidates.length,
            high_intent_count: highIntentCount,
            immediate_count: immediateCount,
            personalization_depth: personalizationDepth,
            follow_up_cadence: followUp,
            quality_score: quality.score,
            readiness_score: readinessScore,
            warnings: quality.warnings,
            blockers: quality.blockers,
            candidate_messages: candidateMessagePayload,
          },
        });
      } else {
        onTagCandidates?.(candidateIds, 'Davet gönderilecek');
        onNoteCandidates?.(candidateIds, note);
      }
      setCampaignCreated(true);
    } catch {
      setCampaignError('Taslak backend’e kaydedilemedi. Ekranda lokal olarak işaretlendi; backend çalışınca tekrar deneyin.');
      onTagCandidates?.(candidateIds, 'Davet gönderilecek');
      onNoteCandidates?.(candidateIds, note);
    } finally {
      setCampaignSaving(false);
    }
  };

  const ChannelIcon = CHANNEL_META[channel].icon;
  const syncLabel = syncState === 'syncing' ? 'Senkronize ediliyor' : syncState === 'offline' ? 'Offline fallback' : 'Backend senkron';

  return (
    <div className="space-y-4">
      <SurfaceCard variant="accent" padding="none" className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_0%,rgba(56,189,248,0.2),transparent_36%),radial-gradient(circle_at_80%_10%,rgba(99,102,241,0.18),transparent_32%)]" />
        <div className="relative grid gap-5 p-5 xl:grid-cols-[minmax(0,1fr)_420px]">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge tone="ai" icon={<WandSparkles className="size-3.5" />}>Outreach Composer v2</StatusBadge>
              <StatusBadge tone={syncState === 'offline' ? 'warning' : 'success'} icon={<ShieldCheck className="size-3.5" />}>{syncLabel}</StatusBadge>
              <StatusBadge tone="info" icon={<Layers3 className="size-3.5" />}>Kişiselleştirilmiş varyantlar</StatusBadge>
            </div>
            <h2 className="mt-4 max-w-3xl text-2xl font-black tracking-[-0.04em] text-foreground sm:text-3xl">
              Adaya özel davet mesajını yaz, kontrol et ve kampanya taslağına dönüştür.
            </h2>
            <p className="mt-2 max-w-3xl text-sm leading-7 text-muted-foreground">
              Bu ekran artık sadece mesaj üretmiyor; kanal uygunluğu, spam riski, yanıt olasılığı ve kişiselleştirme kalitesini birlikte gösteren bir outreach çalışma masası.
            </p>
            <div className="mt-5 grid gap-3 sm:grid-cols-3">
              <HeroMetric icon={Users} label="Seçili aday" value={selectedCandidates.length} helper={`${highIntentCount} yüksek niyet`} />
              <HeroMetric icon={MousePointer2} label={copy.outreach.responseEstimate} value={`${avgResponse}%`} helper={copy.outreach.channels[channel].label} />
              <HeroMetric icon={Gauge} label="Hazırlık skoru" value={`${Math.min(99, readinessScore)}`} helper="kalite + yanıt + kapsam" />
            </div>
          </div>

          <div className="rounded-[28px] border border-border/80 bg-surface/85 p-4 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur-xl">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">Kampanya readiness</p>
                <p className="mt-2 text-4xl font-black tracking-[-0.06em] text-foreground">{Math.min(99, readinessScore)}<span className="text-base text-muted-foreground">/100</span></p>
              </div>
              <ScoreBadge score={Math.min(99, readinessScore)} label="Ready" />
            </div>
            <div className="mt-4 space-y-2">
              <ReadinessRow label="Mesaj kalitesi" value={quality.score} />
              <ReadinessRow label="Ortalama yanıt" value={avgResponse} />
              <ReadinessRow label="Sıcak aday yoğunluğu" value={selectedCandidates.length ? Math.round((highIntentCount / selectedCandidates.length) * 100) : 0} />
            </div>
          </div>
        </div>
      </SurfaceCard>

      <div className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
        <SurfaceCard variant="elevated" padding="none" className="overflow-hidden">
          <div className="border-b border-border/70 p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-black text-foreground">Kampanya ayarları</p>
                <p className="text-xs font-semibold text-muted-foreground">Kanal, ton, şablon ve guardrail</p>
              </div>
              <StatusBadge tone="info">v2 composer</StatusBadge>
            </div>
          </div>

          <div className="space-y-4 p-4">
            <OptionGroup label="Kanal" value={channel} onChange={(value) => { setChannel(value as OutreachChannel); setCampaignCreated(false); }} options={CHANNEL_META} />
            <OptionGroup label={copy.outreach.messageTone} value={tone} onChange={(value) => { setTone(value as OutreachTone); setCampaignCreated(false); }} options={TONE_META} />
            <TemplateGallery value={template} onChange={(value) => { setTemplate(value); setCampaignCreated(false); }} />
            <CompactOptionGroup label={copy.outreach.personalizationDepth} value={personalizationDepth} onChange={(value) => setPersonalizationDepth(value as PersonalizationDepth)} options={PERSONALIZATION_META} />
            <CompactOptionGroup label={copy.outreach.followUpCadence} value={followUp} onChange={(value) => setFollowUp(value as FollowUpCadence)} options={FOLLOW_UP_META} />

            <div className="rounded-2xl border border-border bg-surface-muted/40 p-3">
              <p className="text-xs font-black uppercase tracking-[0.14em] text-muted-foreground">Mesaj guardrails</p>
              <ToggleRow label="Maaş şeffaflığı" checked={includeSalary} onChange={setIncludeSalary} helper="İlk görüşmede bandı konuşma vaadi" />
              <ToggleRow label="Takvim CTA" checked={includeCalendar} onChange={setIncludeCalendar} helper="Adayın cevap bariyerini düşürür" />
              <div className="mt-3 rounded-2xl border border-success/20 bg-success/10 p-3 text-xs font-semibold leading-5 text-muted-foreground">
                <span className="font-black text-foreground">Güvenlik:</span> mesaj yalnızca beceri, rol uyumu, müsaitlik ve açık iş bilgileri üzerinden üretilir; hassas özellik veya varsayım kullanmaz.
              </div>
            </div>
          </div>
        </SurfaceCard>

        <div className="grid gap-4 2xl:grid-cols-[minmax(0,1fr)_460px]">
          <SurfaceCard variant="elevated" padding="none" className="overflow-hidden">
            <div className="border-b border-border/70 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-black text-foreground">Hedef aday listesi</p>
                  <p className="text-xs font-semibold text-muted-foreground">Varyant üretilecek adayları seç</p>
                </div>
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm" onClick={() => setSelectedIds(candidates.filter((candidate) => candidate.intentScore >= 78).slice(0, 8).map((candidate) => candidate.id))}>Sıcakları seç</Button>
                  <Button variant="ghost" size="sm" onClick={() => setSelectedIds(candidates.slice(0, 5).map((candidate) => candidate.id))}>İlk 5</Button>
                  <Button variant="ghost" size="sm" onClick={() => setSelectedIds([])}>Temizle</Button>
                </div>
              </div>
            </div>
            <div className="max-h-[720px] space-y-3 overflow-y-auto p-4">
              {candidates.map((candidate) => {
                const selected = selectedIds.includes(candidate.id);
                const score = getCandidateResponseScore(candidate, channel);
                return (
                  <button
                    key={candidate.id}
                    type="button"
                    onClick={() => toggleCandidate(candidate.id)}
                    onDoubleClick={() => onOpenProfile(candidate.id)}
                    className={cn(
                      'w-full rounded-[24px] border bg-surface p-4 text-left transition hover:border-primary/35 hover:bg-surface-strong focus:outline-none focus:ring-4 focus:ring-[var(--ring)]',
                      selected ? 'border-primary/55 ring-4 ring-[var(--ring)]' : 'border-border'
                    )}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex min-w-0 items-start gap-3">
                        <span className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,var(--primary),var(--accent))] text-xs font-black text-primary-foreground">
                          {candidate.initials}
                        </span>
                        <span className="min-w-0">
                          <span className="flex flex-wrap items-center gap-2">
                            <span className="truncate text-sm font-black text-foreground">{candidate.name}</span>
                            {selected && <CheckCircle2 className="size-4 text-success" />}
                          </span>
                          <span className="mt-1 line-clamp-1 text-xs font-semibold text-muted-foreground">{candidate.headline}</span>
                          <span className="mt-2 flex flex-wrap gap-2 text-[11px] font-bold text-muted-foreground">
                            <span className="inline-flex items-center gap-1"><Briefcase className="size-3.5" />{candidate.experience} yıl</span>
                            <span className="inline-flex items-center gap-1"><CalendarClock className="size-3.5" />{availabilityLabel(candidate)}</span>
                            <span className="inline-flex items-center gap-1"><MousePointer2 className="size-3.5" />{candidate.source}</span>
                          </span>
                        </span>
                      </div>
                      <div className="flex shrink-0 flex-col items-end gap-2">
                        <ScoreBadge score={score} label="Yanıt" size="sm" />
                        <span className={cn('rounded-full px-2.5 py-1 text-[11px] font-black', score >= 78 ? 'bg-success/10 text-success' : score >= 62 ? 'bg-warning/10 text-warning' : 'bg-danger/10 text-danger')}>
                          {score >= 78 ? 'Sıcak' : score >= 62 ? 'Orta' : 'Dikkat'}
                        </span>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </SurfaceCard>

          <SurfaceCard variant="elevated" padding="none" className="overflow-hidden 2xl:sticky 2xl:top-4 2xl:self-start">
            <div className="border-b border-border/70 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-black text-foreground">Composer</p>
                  <p className="text-xs font-semibold text-muted-foreground">Konu, mesaj, kalite ve taslak geçmişi</p>
                </div>
                <div className="inline-flex rounded-2xl border border-border bg-surface p-1">
                  {[
                    ['composer', 'Mesaj', PenLine],
                    ['quality', 'Kontrol', ShieldCheck],
                    ['drafts', 'Taslak', FileText],
                  ].map(([id, label, Icon]) => (
                    <button
                      key={id as string}
                      type="button"
                      onClick={() => setPreviewMode(id as typeof previewMode)}
                      className={cn(
                        'inline-flex h-8 items-center gap-1.5 rounded-xl px-2.5 text-[11px] font-black transition',
                        previewMode === id ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground hover:bg-surface-muted hover:text-foreground'
                      )}
                    >
                      <Icon className="size-3.5" />
                      {label as string}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {activeCandidate ? (
              <div className="space-y-4 p-4">
                <div className="rounded-[24px] border border-border bg-surface-muted/45 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate text-base font-black text-foreground">{activeCandidate.name}</p>
                      <p className="mt-1 line-clamp-1 text-sm font-semibold text-muted-foreground">{activeCandidate.headline}</p>
                    </div>
                    <ScoreBadge score={activeCandidate.matchScore} label="Match" size="sm" />
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-2">
                    <MiniSignal icon={Target} label="Intent" value={`${activeCandidate.intentScore}/100`} />
                    <MiniSignal icon={Clock3} label="Yanıt" value={`${getCandidateResponseScore(activeCandidate, channel)}%`} />
                    <MiniSignal icon={ChannelIcon} label="Kanal" value={CHANNEL_META[channel].label} />
                    <MiniSignal icon={PenLine} label="Şablon" value={TEMPLATE_META[template].label} />
                  </div>
                </div>

                {previewMode === 'composer' && (
                  <div className="space-y-3">
                    <label className="block">
                      <span className="text-xs font-black uppercase tracking-[0.14em] text-muted-foreground">Konu satırı</span>
                      <input
                        value={activeSubject}
                        onChange={(event) => setSubjectEdits((current) => ({...current, [activeCandidate.id]: event.target.value}))}
                        className="mt-2 h-11 w-full rounded-2xl border border-border bg-surface px-3 text-sm font-bold text-foreground outline-none transition focus:border-primary/40 focus:ring-4 focus:ring-[var(--ring)]"
                      />
                    </label>
                    <label className="block">
                      <span className="text-xs font-black uppercase tracking-[0.14em] text-muted-foreground">Mesaj metni</span>
                      <textarea
                        value={activeMessage}
                        onChange={(event) => {
                          setCampaignCreated(false);
                          setMessageEdits((current) => ({...current, [activeCandidate.id]: event.target.value}));
                        }}
                        rows={14}
                        className="mt-2 w-full resize-y rounded-[24px] border border-border bg-surface p-4 text-sm font-semibold leading-7 text-foreground outline-none transition focus:border-primary/40 focus:ring-4 focus:ring-[var(--ring)]"
                      />
                    </label>
                    <div className="flex flex-wrap gap-2">
                      <Button variant="secondary" size="sm" className="gap-2" onClick={() => void navigator.clipboard?.writeText(activeMessage)}>
                        <ClipboardCopy className="size-4" />
                        Kopyala
                      </Button>
                      <Button variant="ghost" size="sm" className="gap-2" onClick={resetActiveMessage}>
                        <RefreshCcw className="size-4" />
                        AI metne dön
                      </Button>
                      <Button variant="ghost" size="sm" className="gap-2" onClick={() => onOpenProfile(activeCandidate.id)}>
                        <Target className="size-4" />
                        360 aç
                      </Button>
                    </div>
                  </div>
                )}

                {previewMode === 'quality' && (
                  <QualityPanel quality={quality} channel={channel} readinessScore={Math.min(99, readinessScore)} />
                )}

                {previewMode === 'drafts' && (
                  <DraftsPanel campaignDrafts={campaignDrafts} onOpenDraft={(draftId) => setSelectedDraftId(draftId)} />
                )}

                {campaignError && (
                  <div className="rounded-2xl border border-warning/25 bg-warning/10 p-3 text-sm font-semibold leading-6 text-warning">
                    {campaignError}
                  </div>
                )}
                {campaignCreated && (
                  <div className="rounded-2xl border border-success/25 bg-success/10 p-3 text-sm font-semibold leading-6 text-success">
                    Kampanya taslağı kaydedildi. Seçili adaylara davet etiketi ve kampanya notu işlendi.
                  </div>
                )}

                <Button
                  className="h-12 w-full gap-2 rounded-[22px]"
                  disabled={selectedCandidates.length === 0 || campaignSaving || quality.blockers.length > 0}
                  onClick={createCampaign}
                >
                  {campaignSaving ? <TimerReset className="size-4 animate-spin" /> : <Send className="size-4" />}
                  {campaignSaving ? copy.outreach.saving : quality.blockers.length > 0 ? copy.outreach.fixBlocker : copy.outreach.saveDraft}
                </Button>
              </div>
            ) : (
              <div className="p-4 text-sm font-semibold text-muted-foreground">{copy.outreach.selectToPreview}</div>
            )}
          </SurfaceCard>
        </div>
      </div>
      <CampaignDetailDrawer
        campaign={selectedDraft}
        candidates={candidates}
        open={Boolean(selectedDraft)}
        onClose={() => setSelectedDraftId(null)}
        onOpenCandidate={(candidateId) => {
          onSelect(candidateId);
          onOpenProfile(candidateId);
        }}
        locale={locale}
      />
    </div>
  );
}

function HeroMetric({icon: Icon, label, value, helper}: {icon: LucideIcon; label: string; value: string | number; helper: string}) {
  return (
    <div className="rounded-[24px] border border-border/80 bg-surface/80 p-4 shadow-sm backdrop-blur-xl">
      <div className="flex items-center gap-3">
        <span className="flex size-10 items-center justify-center rounded-2xl bg-primary/10 text-primary"><Icon className="size-5" /></span>
        <div>
          <p className="text-xs font-black uppercase tracking-[0.14em] text-muted-foreground">{label}</p>
          <p className="text-2xl font-black tracking-[-0.04em] text-foreground">{value}</p>
          <p className="text-xs font-semibold text-muted-foreground">{helper}</p>
        </div>
      </div>
    </div>
  );
}

function ReadinessRow({label, value}: {label: string; value: number}) {
  return (
    <div className="rounded-2xl border border-border bg-surface-muted/45 p-3">
      <div className="flex items-center justify-between gap-3 text-xs font-black text-foreground">
        <span>{label}</span>
        <span>{value}/100</span>
      </div>
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-surface-muted">
        <div className="h-full rounded-full bg-[linear-gradient(90deg,var(--primary),var(--accent))]" style={{width: `${Math.max(8, Math.min(100, value))}%`}} />
      </div>
    </div>
  );
}

function OptionGroup({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Record<string, {label: string; helper: string; icon?: LucideIcon}>;
}) {
  return (
    <div>
      <p className="mb-2 text-xs font-black uppercase tracking-[0.14em] text-muted-foreground">{label}</p>
      <div className="space-y-2">
        {Object.entries(options).map(([id, option]) => {
          const selected = value === id;
          const Icon = option.icon ?? Sparkles;
          return (
            <button
              key={id}
              type="button"
              onClick={() => onChange(id)}
              className={cn(
                'w-full rounded-2xl border p-3 text-left transition focus:outline-none focus:ring-4 focus:ring-[var(--ring)]',
                selected ? 'border-primary/45 bg-primary/10' : 'border-border bg-surface hover:border-primary/30 hover:bg-surface-strong'
              )}
            >
              <span className="flex items-start gap-3">
                <span className={cn('flex size-9 shrink-0 items-center justify-center rounded-xl', selected ? 'bg-primary text-primary-foreground' : 'bg-surface-muted text-muted-foreground')}>
                  <Icon className="size-4" />
                </span>
                <span>
                  <span className="block text-sm font-black text-foreground">{option.label}</span>
                  <span className="block text-xs font-semibold leading-5 text-muted-foreground">{option.helper}</span>
                </span>
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function CompactOptionGroup({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Record<string, {label: string; helper: string}>;
}) {
  return (
    <div>
      <p className="mb-2 text-xs font-black uppercase tracking-[0.14em] text-muted-foreground">{label}</p>
      <div className="grid gap-2">
        {Object.entries(options).map(([id, option]) => (
          <button
            key={id}
            type="button"
            onClick={() => onChange(id)}
            className={cn(
              'rounded-2xl border px-3 py-2 text-left transition focus:outline-none focus:ring-4 focus:ring-[var(--ring)]',
              value === id ? 'border-primary/45 bg-primary/10' : 'border-border bg-surface hover:border-primary/30 hover:bg-surface-strong'
            )}
          >
            <span className="block text-sm font-black text-foreground">{option.label}</span>
            <span className="block text-xs font-semibold text-muted-foreground">{option.helper}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function TemplateGallery({value, onChange}: {value: OutreachTemplate; onChange: (value: OutreachTemplate) => void}) {
  return (
    <div>
      <p className="mb-2 text-xs font-black uppercase tracking-[0.14em] text-muted-foreground">Şablon</p>
      <div className="grid gap-2">
        {Object.entries(TEMPLATE_META).map(([id, template]) => {
          const selected = value === id;
          return (
            <button
              key={id}
              type="button"
              onClick={() => onChange(id as OutreachTemplate)}
              className={cn(
                'rounded-2xl border p-3 text-left transition focus:outline-none focus:ring-4 focus:ring-[var(--ring)]',
                selected ? 'border-primary/45 bg-primary/10' : 'border-border bg-surface hover:border-primary/30 hover:bg-surface-strong'
              )}
            >
              <span className="flex items-start justify-between gap-3">
                <span>
                  <span className="block text-sm font-black text-foreground">{template.label}</span>
                  <span className="block text-xs font-semibold leading-5 text-muted-foreground">{template.helper}</span>
                </span>
                <span className="rounded-full border border-border bg-surface-muted px-2.5 py-1 text-[10px] font-black text-muted-foreground">{template.badge}</span>
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function ToggleRow({label, helper, checked, onChange}: {label: string; helper: string; checked: boolean; onChange: (checked: boolean) => void}) {
  return (
    <label className="mt-3 flex items-center justify-between gap-3 rounded-xl bg-surface px-3 py-2 text-sm font-bold text-foreground">
      <span>
        <span className="block">{label}</span>
        <span className="block text-xs font-semibold text-muted-foreground">{helper}</span>
      </span>
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} className="accent-[var(--primary)]" />
    </label>
  );
}

function MiniSignal({icon: Icon, label, value}: {icon: LucideIcon; label: string; value: string}) {
  return (
    <div className="rounded-2xl border border-border bg-surface px-3 py-2">
      <div className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-[0.13em] text-muted-foreground">
        <Icon className="size-3.5" />
        {label}
      </div>
      <p className="mt-1 truncate text-xs font-black text-foreground">{value}</p>
    </div>
  );
}

function QualityPanel({
  quality,
  channel,
  readinessScore,
}: {
  quality: ReturnType<typeof evaluateMessageQuality>;
  channel: OutreachChannel;
  readinessScore: number;
}) {
  const tone = getReadinessTone(quality.score);
  return (
    <div className="space-y-3">
      <div className="rounded-[24px] border border-border bg-surface p-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-black text-foreground">Mesaj kalite kontrolü</p>
            <p className="mt-1 text-xs font-semibold text-muted-foreground">{CHANNEL_META[channel].risk} · {quality.words} kelime</p>
          </div>
          <ScoreBadge score={quality.score} label="Kalite" />
        </div>
        <div className="mt-4 grid gap-2 sm:grid-cols-2">
          <MiniSignal icon={Gauge} label="Ready" value={`${readinessScore}/100`} />
          <MiniSignal icon={ChannelIconFor(channel)} label="Kanal" value={CHANNEL_META[channel].label} />
        </div>
      </div>

      {quality.blockers.length > 0 && <FindingList tone="danger" icon={AlertTriangle} title="Bloker" items={quality.blockers} />}
      {quality.warnings.length > 0 && <FindingList tone="warning" icon={Info} title="İyileştirme önerileri" items={quality.warnings} />}
      {quality.strengths.length > 0 && <FindingList tone={tone === 'success' ? 'success' : 'info'} icon={BadgeCheck} title="Güçlü yanlar" items={quality.strengths} />}
    </div>
  );
}

function ChannelIconFor(channel: OutreachChannel): LucideIcon {
  return CHANNEL_META[channel].icon;
}

function FindingList({tone, icon: Icon, title, items}: {tone: 'success' | 'warning' | 'danger' | 'info'; icon: LucideIcon; title: string; items: string[]}) {
  const toneClass = tone === 'success'
    ? 'border-success/25 bg-success/10 text-success'
    : tone === 'warning'
      ? 'border-warning/25 bg-warning/10 text-warning'
      : tone === 'danger'
        ? 'border-danger/25 bg-danger/10 text-danger'
        : 'border-primary/25 bg-primary/10 text-primary';
  return (
    <div className={cn('rounded-[24px] border p-4', toneClass)}>
      <div className="flex items-center gap-2 text-sm font-black">
        <Icon className="size-4" />
        {title}
      </div>
      <ul className="mt-3 space-y-2 text-sm font-semibold leading-6">
        {items.map((item) => <li key={item}>• {item}</li>)}
      </ul>
    </div>
  );
}

function DraftsPanel({campaignDrafts, onOpenDraft}: {campaignDrafts: EmployerOutreachCampaign[]; onOpenDraft: (draftId: string) => void}) {
  if (campaignDrafts.length === 0) {
    return (
      <div className="rounded-[24px] border border-border bg-surface-muted/45 p-5 text-center">
        <FileText className="mx-auto size-8 text-muted-foreground" />
        <p className="mt-3 text-sm font-black text-foreground">Henüz kampanya taslağı yok</p>
        <p className="mt-1 text-xs font-semibold leading-5 text-muted-foreground">İlk taslağı oluşturduğunda burada kanal, yanıt oranı ve aday sayısı görünecek.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {campaignDrafts.slice(0, 5).map((draft) => (
        <button
          key={draft.id}
          type="button"
          onClick={() => onOpenDraft(draft.id)}
          className="w-full rounded-[22px] border border-border bg-surface p-3 text-left transition hover:border-primary/35 hover:bg-surface-strong focus:outline-none focus:ring-4 focus:ring-[var(--ring)]"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="truncate text-sm font-black text-foreground">{draft.name}</p>
              <p className="mt-1 text-xs font-semibold text-muted-foreground">{draft.candidate_ids.length} aday · {draft.channel} · {draft.response_rate}% yanıt</p>
            </div>
            <StatusBadge tone="info">{draft.status}</StatusBadge>
          </div>
          {draft.message_preview && <p className="mt-3 line-clamp-3 text-xs font-semibold leading-5 text-muted-foreground">{draft.message_preview}</p>}
          <span className="mt-3 inline-flex items-center gap-1.5 text-xs font-black text-primary">Kuyruğu aç <ArrowRight className="size-3.5" /></span>
        </button>
      ))}
    </div>
  );
}
