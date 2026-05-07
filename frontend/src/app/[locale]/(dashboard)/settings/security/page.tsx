'use client';

import {useTranslations} from 'next-intl';
import {useCallback, useEffect, useState} from 'react';

import {SettingsField} from '@/components/settings/field';
import {SettingsSection} from '@/components/settings/settings-section';
import {Button} from '@/components/ui/button';
import {Input} from '@/components/ui/input';
import {api, ApiError} from '@/lib/api';
import type {LoginHistoryItem, SessionItem, TotpStatusResponse} from '@/lib/api';

export default function SettingsSecurityPage() {
  const t = useTranslations('settings.security');

  const [curPw, setCurPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [pwMsg, setPwMsg] = useState<{text: string; ok: boolean} | null>(null);

  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [history, setHistory] = useState<LoginHistoryItem[]>([]);
  const [totpStatus, setTotpStatus] = useState<TotpStatusResponse>({enabled: false, verified: false});
  const [totpModal, setTotpModal] = useState<{secret: string; uri: string} | null>(null);
  const [totpCode, setTotpCode] = useState('');
  const [totpMsg, setTotpMsg] = useState('');

  const [emailModal, setEmailModal] = useState(false);
  const [emailNewAddr, setEmailNewAddr] = useState('');
  const [emailPw, setEmailPw] = useState('');
  const [emailCodeSent, setEmailCodeSent] = useState(false);
  const [emailCode, setEmailCode] = useState('');
  const [emailMsg, setEmailMsg] = useState('');

  const [deleteModal, setDeleteModal] = useState(false);
  const [deleteReason, setDeleteReason] = useState('');
  const [deletePw, setDeletePw] = useState('');
  const [deleteMsg, setDeleteMsg] = useState('');

  const loadData = useCallback(async () => {
    try {
      const [s, h, ts] = await Promise.all([
        api.getSessions(),
        api.getLoginHistory(),
        api.getTotpStatus(),
      ]);
      setSessions(s);
      setHistory(h);
      setTotpStatus(ts);
    } catch { /* silent */ }
  }, []);

  useEffect(() => { void loadData(); }, [loadData]);

  async function handleChangePassword() {
    setPwMsg(null);
    try {
      await api.changePassword(curPw, newPw, confirmPw);
      setPwMsg({text: t('passwordUpdated'), ok: true});
      setCurPw(''); setNewPw(''); setConfirmPw('');
      void loadData();
    } catch (e) {
      setPwMsg({text: e instanceof ApiError ? e.detail : 'Error', ok: false});
    }
  }

  async function handleEndSession(id: number) {
    await api.endSession(id);
    setSessions((prev) => prev.filter((s) => s.id !== id));
  }

  async function handleEndAllOthers() {
    await api.endAllOtherSessions();
    void loadData();
  }

  async function handleSetupTotp() {
    const res = await api.setupTotp();
    setTotpModal({secret: res.secret, uri: res.otpauth_uri});
    setTotpCode('');
    setTotpMsg('');
  }

  async function handleVerifyTotp() {
    setTotpMsg('');
    try {
      await api.verifyTotp(totpCode);
      setTotpModal(null);
      setTotpStatus({enabled: true, verified: true});
    } catch (e) {
      setTotpMsg(e instanceof ApiError ? e.detail : 'Invalid code');
    }
  }

  async function handleDisableTotp() {
    await api.disableTotp();
    setTotpStatus({enabled: false, verified: false});
  }

  async function handleRequestEmailChange() {
    setEmailMsg('');
    try {
      await api.requestEmailChange(emailNewAddr, emailPw);
      setEmailCodeSent(true);
    } catch (e) {
      setEmailMsg(e instanceof ApiError ? e.detail : 'Error');
    }
  }

  async function handleConfirmEmailChange() {
    setEmailMsg('');
    try {
      await api.confirmEmailChange(emailCode);
      setEmailModal(false);
      setEmailCodeSent(false);
      setEmailNewAddr(''); setEmailPw(''); setEmailCode('');
      void loadData();
    } catch (e) {
      setEmailMsg(e instanceof ApiError ? e.detail : 'Error');
    }
  }

  async function handleDeleteAccount() {
    setDeleteMsg('');
    try {
      await api.deleteAccount(deletePw, deleteReason);
      window.location.href = '/';
    } catch (e) {
      setDeleteMsg(e instanceof ApiError ? e.detail : 'Error');
    }
  }

  const eventLabel = (type: string) => {
    const map: Record<string, string> = {
      login_success: t('successfulLogin'),
      login_failed: t('failedLogin'),
      password_changed: t('passwordChanged'),
      login_magic_link: t('loginMagicLink'),
      login_google_oauth: t('loginGoogleOauth'),
      email_changed: t('emailChanged'),
    };
    return map[type] ?? type;
  };

  const eventStatus = (type: string): 'success' | 'danger' | 'info' => {
    if (type === 'login_failed') return 'danger';
    if (type === 'login_success' || type === 'login_magic_link' || type === 'login_google_oauth') return 'success';
    return 'info';
  };

  function formatRelativeDate(iso: string | null) {
    if (!iso) return '';
    const d = new Date(iso);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return t('timeJustNow');
    if (diffMins < 60) return t('timeMinutesAgo', {count: diffMins});
    const diffHrs = Math.floor(diffMins / 60);
    if (diffHrs < 24) return t('timeHoursAgo', {count: diffHrs});
    const diffDays = Math.floor(diffHrs / 24);
    if (diffDays < 7) return t('timeDaysAgo', {count: diffDays});
    return d.toLocaleDateString();
  }

  return (
    <div className="space-y-6">
      {/* ── Password ── */}
      <SettingsSection title={t('passwordSection')} description={t('passwordSectionDesc')}>
        <SettingsField label={t('fields.currentPassword')}>
          <Input type="password" value={curPw} onChange={(e) => setCurPw(e.target.value)} />
        </SettingsField>
        <SettingsField label={t('fields.newPassword')} hint={t('passwordHint')}>
          <Input type="password" value={newPw} onChange={(e) => setNewPw(e.target.value)} />
        </SettingsField>
        <SettingsField label={t('fields.confirmPassword')}>
          <Input type="password" value={confirmPw} onChange={(e) => setConfirmPw(e.target.value)} />
        </SettingsField>
        {pwMsg && (
          <p className={`text-xs ${pwMsg.ok ? 'text-success' : 'text-danger'}`}>{pwMsg.text}</p>
        )}
        <div className="flex items-center gap-3">
          <Button onClick={handleChangePassword}>{t('updatePassword')}</Button>
          <Button variant="ghost" onClick={() => { setCurPw(''); setNewPw(''); setConfirmPw(''); setPwMsg(null); }}>
            {t('cancel')}
          </Button>
        </div>
      </SettingsSection>

      {/* ── Login methods ── */}
      <SettingsSection title={t('loginMethodsTitle')} description={t('loginMethodsDesc')}>
        <ToggleRow
          title={t('magicLinkTitle')}
          description={t('magicLinkDescription')}
          activeLabel={t('active')}
          inactiveLabel={t('inactive')}
          on
        />
        <div className="flex items-center justify-between rounded-xl border border-border bg-surface-muted px-4 py-3">
          <div className="min-w-0">
            <div className="text-sm font-medium text-foreground/80">{t('twoFactorTitle')}</div>
            <div className="mt-0.5 text-xs text-muted-foreground">{t('twoFactorDescription')}</div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            {totpStatus.enabled && totpStatus.verified ? (
              <button
                type="button"
                onClick={handleDisableTotp}
                className="rounded-md border border-border px-2.5 py-1 text-[11px] text-muted-foreground hover:bg-surface-strong"
              >
                {t('disable')}
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSetupTotp}
                className="rounded-md border border-primary/30 bg-primary/15 px-2.5 py-1 text-[11px] font-medium text-secondary-foreground"
              >
                {t('new2fa')}
              </button>
            )}
            <StatusDot on={totpStatus.enabled && totpStatus.verified} activeLabel={t('active')} inactiveLabel={t('inactive')} />
          </div>
        </div>
        <ToggleRow
          title={t('newDeviceTitle')}
          description={t('newDeviceDescription')}
          activeLabel={t('active')}
          inactiveLabel={t('inactive')}
          on
        />
      </SettingsSection>

      {/* ── Active sessions ── */}
      <SettingsSection title={t('sessionsTitle')} description={t('sessionsDesc')}>
        {sessions.length === 0 ? (
          <p className="text-xs text-muted-foreground">{t('noSessions')}</p>
        ) : (
          <div className="space-y-2">
            {sessions.map((s) => (
              <div key={s.id} className="flex items-center justify-between rounded-xl border border-border bg-surface-muted px-4 py-3">
                <div className="flex items-center gap-3">
                  <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" className="text-primary">
                      <rect x="2" y="3" width="12" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.2" />
                      <path d="M5 14h6" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
                      <path d="M8 11v3" stroke="currentColor" strokeWidth="1.2" />
                    </svg>
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-foreground/80">{s.device_label || t('unknownDevice')}</span>
                      {s.is_current && (
                        <span className="rounded-full bg-success/15 px-2 py-0.5 text-[10px] font-medium text-success">
                          {t('thisDevice')}
                        </span>
                      )}
                    </div>
                    <div className="mt-0.5 flex items-center gap-2 text-[11px] text-muted-foreground">
                      <span>{s.ip_address}</span>
                      <span className="text-border">·</span>
                      <span>{t('sessionStarted')} {formatRelativeDate(s.created_at)}</span>
                    </div>
                  </div>
                </div>
                {!s.is_current && (
                  <button
                    type="button"
                    onClick={() => handleEndSession(s.id)}
                    className="rounded-md border border-border px-2.5 py-1 text-[11px] text-muted-foreground hover:border-danger/30 hover:text-danger transition"
                  >
                    {t('endSession')}
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
        {sessions.length > 1 && (
          <div className="pt-2">
            <Button variant="outline" size="sm" onClick={handleEndAllOthers}>
              {t('endAllSessions')}
            </Button>
          </div>
        )}
      </SettingsSection>

      {/* ── Login history ── */}
      <SettingsSection title={t('loginHistoryTitle')} description={t('loginHistoryDesc')}>
        {history.length === 0 ? (
          <p className="text-xs text-muted-foreground">{t('noHistory')}</p>
        ) : (
          <div className="space-y-1">
            {history.slice(0, 5).map((e) => {
              const st = eventStatus(e.event_type);
              const dotColor = st === 'success' ? 'bg-success' : st === 'danger' ? 'bg-danger' : 'bg-primary';
              return (
                <div key={e.id} className="flex items-center justify-between rounded-lg border border-border/40 bg-surface-muted/40 px-3 py-2.5 transition hover:bg-surface-muted">
                  <div className="flex items-center gap-2.5">
                    <span className={`size-2 shrink-0 rounded-full ${dotColor}`} />
                    <div>
                      <span className="text-xs text-foreground/70">{eventLabel(e.event_type)}</span>
                      {e.detail && <span className="ml-1.5 text-[10px] text-muted-foreground/60">— {e.detail}</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-3 text-[10px] text-muted-foreground/60">
                    <span>{e.ip_address}</span>
                    <span>{formatRelativeDate(e.created_at)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </SettingsSection>

      {/* ── Danger zone ── */}
      <SettingsSection title={t('dangerZone')} description={t('dangerZoneDesc')}>
        <DangerRow
          title={t('changeEmail')}
          description={t('changeEmailDesc')}
          buttonLabel={t('changeEmailBtn')}
          onClick={() => { setEmailModal(true); setEmailMsg(''); setEmailCodeSent(false); setEmailNewAddr(''); setEmailPw(''); setEmailCode(''); }}
        />
        <DangerRow
          title={t('terminateAll')}
          description={t('terminateAllDesc')}
          buttonLabel={t('terminateAllBtn')}
          onClick={handleEndAllOthers}
        />
        <DangerRow
          title={t('deleteAccount')}
          description={t('deleteAccountDesc')}
          buttonLabel={t('deleteAccountBtn')}
          destructive
          onClick={() => { setDeleteModal(true); setDeleteMsg(''); setDeleteReason(''); setDeletePw(''); }}
        />
      </SettingsSection>

      {/* ── TOTP Modal ── */}
      {totpModal && (
        <Modal onClose={() => setTotpModal(null)}>
          <h3 className="text-sm font-semibold text-foreground">{t('totpSetupTitle')}</h3>
          <p className="mt-1 text-xs text-muted-foreground">{t('totpSetupDesc')}</p>
          <div className="mt-4 rounded-xl bg-surface-muted p-5 text-center">
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-2">{t('totpSecretLabel')}</div>
            <code className="text-sm font-mono break-all text-foreground/90 tracking-wider">{totpModal.secret}</code>
          </div>
          <div className="mt-4 space-y-3">
            <SettingsField label={t('totpSetupCode')}>
              <Input
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value)}
                maxLength={6}
                className="text-center text-lg tracking-[0.3em]"
              />
            </SettingsField>
            {totpMsg && <p className="text-xs text-danger">{totpMsg}</p>}
            <Button className="w-full" onClick={handleVerifyTotp}>{t('totpSetupConfirm')}</Button>
          </div>
        </Modal>
      )}

      {/* ── Email Change Modal ── */}
      {emailModal && (
        <Modal onClose={() => setEmailModal(false)}>
          <h3 className="text-sm font-semibold text-foreground">{t('emailModalTitle')}</h3>
          <p className="mt-1 text-xs text-muted-foreground">{t('emailModalDesc')}</p>

          {!emailCodeSent ? (
            <div className="mt-4 space-y-3">
              <SettingsField label={t('emailModalNewEmail')}>
                <Input
                  type="email"
                  value={emailNewAddr}
                  onChange={(e) => setEmailNewAddr(e.target.value)}
                  placeholder="new@example.com"
                />
              </SettingsField>
              <SettingsField label={t('emailModalPassword')} hint={t('emailModalPasswordHint')}>
                <Input type="password" value={emailPw} onChange={(e) => setEmailPw(e.target.value)} />
              </SettingsField>
              {emailMsg && <p className="text-xs text-danger">{emailMsg}</p>}
              <Button className="w-full" onClick={handleRequestEmailChange} disabled={!emailNewAddr.trim() || !emailPw}>
                {t('emailModalSendCode')}
              </Button>
            </div>
          ) : (
            <div className="mt-4 space-y-3">
              <div className="rounded-xl bg-success/10 border border-success/20 p-3">
                <p className="text-xs text-success">{t('emailModalCodeSent')}</p>
                <p className="mt-1 text-[11px] text-muted-foreground">{emailNewAddr}</p>
              </div>
              <SettingsField label={t('emailModalCode')}>
                <Input
                  value={emailCode}
                  onChange={(e) => setEmailCode(e.target.value)}
                  maxLength={6}
                  className="text-center text-lg tracking-[0.3em]"
                  placeholder="000000"
                />
              </SettingsField>
              {emailMsg && <p className="text-xs text-danger">{emailMsg}</p>}
              <Button className="w-full" onClick={handleConfirmEmailChange} disabled={emailCode.length < 6}>
                {t('emailModalConfirm')}
              </Button>
            </div>
          )}
        </Modal>
      )}

      {/* ── Delete Account Modal ── */}
      {deleteModal && (
        <Modal onClose={() => setDeleteModal(false)}>
          <div className="flex items-center gap-2.5 mb-1">
            <div className="flex size-8 items-center justify-center rounded-lg bg-danger/15">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" className="text-danger">
                <path d="M8 3v6M8 11.5v.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                <circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1.2" />
              </svg>
            </div>
            <h3 className="text-sm font-semibold text-danger">{t('deleteModalTitle')}</h3>
          </div>
          <p className="text-xs text-muted-foreground">{t('deleteModalDesc')}</p>
          <div className="mt-4 space-y-3">
            <SettingsField label={t('deleteModalReason')}>
              <textarea
                className="w-full rounded-lg border border-border bg-surface-muted px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary resize-none"
                rows={3}
                value={deleteReason}
                onChange={(e) => setDeleteReason(e.target.value)}
              />
            </SettingsField>
            <SettingsField label={t('deleteModalPassword')}>
              <Input type="password" value={deletePw} onChange={(e) => setDeletePw(e.target.value)} />
            </SettingsField>
            {deleteMsg && <p className="text-xs text-danger">{deleteMsg}</p>}
            <button
              type="button"
              onClick={handleDeleteAccount}
              disabled={!deletePw}
              className="w-full rounded-lg border border-danger/40 bg-danger/15 px-4 py-2.5 text-xs font-medium text-danger hover:bg-danger/25 disabled:opacity-40 transition"
            >
              {t('deleteModalConfirm')}
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}

/* ── Shared components ── */

function Modal({children, onClose}: {children: React.ReactNode; onClose: () => void}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div
        className="relative w-full max-w-md rounded-2xl border border-border bg-surface p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 text-muted-foreground hover:text-foreground transition"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>
        {children}
      </div>
    </div>
  );
}

function ToggleRow({title, description, activeLabel, inactiveLabel, on}: {
  title: string; description: string; activeLabel: string; inactiveLabel: string; on: boolean;
}) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-border bg-surface-muted px-4 py-3">
      <div className="min-w-0">
        <div className="text-sm font-medium text-foreground/80">{title}</div>
        <div className="mt-0.5 text-xs text-muted-foreground">{description}</div>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <div className={`relative h-5 w-9 rounded-full ${on ? 'bg-primary' : 'bg-border'} opacity-60`}>
          <span className={`absolute top-0.5 block size-4 rounded-full bg-white transition-transform ${on ? 'translate-x-4' : 'translate-x-0.5'}`} />
        </div>
        <StatusDot on={on} activeLabel={activeLabel} inactiveLabel={inactiveLabel} />
      </div>
    </div>
  );
}

function StatusDot({on, activeLabel, inactiveLabel}: {on: boolean; activeLabel: string; inactiveLabel: string}) {
  return (
    <span className={`text-[10px] ${on ? 'text-success' : 'text-muted-foreground'}`}>
      {on ? activeLabel : inactiveLabel}
    </span>
  );
}

function DangerRow({title, description, buttonLabel, destructive = false, onClick}: {
  title: string; description: string; buttonLabel: string; destructive?: boolean; onClick: () => void;
}) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-danger/20 bg-danger/[0.04] px-4 py-3">
      <div className="min-w-0">
        <div className="text-sm font-medium text-foreground/80">{title}</div>
        <div className="mt-0.5 text-xs text-muted-foreground">{description}</div>
      </div>
      <button
        type="button"
        onClick={onClick}
        className={`shrink-0 rounded-md border px-3 py-1.5 text-[11px] font-medium transition ${
          destructive
            ? 'border-danger/40 bg-danger/15 text-danger hover:bg-danger/25'
            : 'border-border bg-surface-muted text-muted-foreground hover:bg-surface-strong'
        }`}
      >
        {buttonLabel}
      </button>
    </div>
  );
}
