'use client';

import Link from 'next/link';
import {useEffect, useMemo, useState} from 'react';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ClipboardCheck,
  Copy,
  ExternalLink,
  Globe2,
  Loader2,
  RefreshCw,
  Route,
  Server,
  ShieldCheck,
  TerminalSquare,
} from 'lucide-react';
import {
  getEmployerProductionQaCopy,
  type QaEndpoint,
  type QaSeverity,
} from '@/lib/employer-production-qa-copy';

const statusTone: Record<QaSeverity, string> = {
  pass: 'border-emerald-400/25 bg-emerald-500/10 text-emerald-100',
  warning: 'border-amber-400/25 bg-amber-500/10 text-amber-100',
  fail: 'border-rose-400/25 bg-rose-500/10 text-rose-100',
  manual: 'border-sky-400/25 bg-sky-500/10 text-sky-100',
};

const statusDot: Record<QaSeverity, string> = {
  pass: 'bg-emerald-300',
  warning: 'bg-amber-300',
  fail: 'bg-rose-300',
  manual: 'bg-sky-300',
};

type LiveCheckResult = {
  status: QaSeverity;
  label: string;
  detail: string;
  checkedAt?: string;
};

function StatusPill({status, label}: {status: QaSeverity; label: string}) {
  return (
    <span className={`inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-xs font-semibold ${statusTone[status]}`}>
      <span className={`size-1.5 rounded-full ${statusDot[status]}`} />
      {label}
    </span>
  );
}

function MetricCard({label, value, detail, status, statusLabel}: {label: string; value: string; detail: string; status: QaSeverity; statusLabel: string}) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.055] p-5 shadow-2xl shadow-slate-950/20 backdrop-blur">
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-medium text-slate-300">{label}</p>
        <StatusPill status={status} label={statusLabel} />
      </div>
      <p className="mt-4 text-3xl font-semibold tracking-tight text-white">{value}</p>
      <p className="mt-2 text-sm leading-6 text-slate-400">{detail}</p>
    </div>
  );
}

async function runEndpointCheck(endpoint: QaEndpoint): Promise<LiveCheckResult> {
  const startedAt = new Date();
  try {
    const response = await fetch(endpoint.path, {
      method: endpoint.method,
      credentials: 'include',
      cache: 'no-store',
      headers: {'Accept': 'application/json'},
    });

    const ok = response.ok;
    const authWarning = response.status === 401 || response.status === 403;
    return {
      status: ok ? 'pass' : authWarning ? 'warning' : 'fail',
      label: `${response.status} ${response.statusText || ''}`.trim(),
      detail: ok ? 'OK' : authWarning ? 'Auth required or session missing' : 'Endpoint returned an error',
      checkedAt: startedAt.toLocaleTimeString(),
    };
  } catch (error) {
    return {
      status: 'fail',
      label: 'Network error',
      detail: error instanceof Error ? error.message : 'Request failed',
      checkedAt: startedAt.toLocaleTimeString(),
    };
  }
}

export function EmployerProductionQaPage({locale}: {locale: string}) {
  const copy = useMemo(() => getEmployerProductionQaCopy(locale), [locale]);
  const [activeSection, setActiveSection] = useState<'routes' | 'language' | 'backend' | 'checklist' | 'commands'>('routes');
  const [liveChecks, setLiveChecks] = useState<Record<string, LiveCheckResult>>({});
  const [isChecking, setIsChecking] = useState(false);
  const [copiedCommand, setCopiedCommand] = useState<string | null>(null);

  const statusCounts = useMemo(() => {
    const all = [...copy.routes, ...copy.languageChecks, ...copy.smokeChecklist];
    return all.reduce(
      (acc, item) => ({...acc, [item.status]: acc[item.status] + 1}),
      {pass: 0, warning: 0, fail: 0, manual: 0} as Record<QaSeverity, number>,
    );
  }, [copy.routes, copy.languageChecks, copy.smokeChecklist]);

  const runChecks = async () => {
    setIsChecking(true);
    const results = await Promise.all(copy.endpoints.map(async (endpoint) => [endpoint.id, await runEndpointCheck(endpoint)] as const));
    setLiveChecks(Object.fromEntries(results));
    setIsChecking(false);
  };

  useEffect(() => {
    void runChecks();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locale]);

  const copyCommand = async (id: string, command: string) => {
    try {
      await navigator.clipboard.writeText(command);
      setCopiedCommand(id);
      setTimeout(() => setCopiedCommand(null), 1600);
    } catch {
      setCopiedCommand(null);
    }
  };

  const sectionButton = (id: typeof activeSection, label: string, Icon: typeof Route) => (
    <button
      type="button"
      onClick={() => setActiveSection(id)}
      className={`inline-flex min-h-11 items-center gap-2 rounded-2xl border px-4 text-sm font-semibold transition ${
        activeSection === id
          ? 'border-cyan-300/40 bg-cyan-300/15 text-cyan-50 shadow-lg shadow-cyan-950/20'
          : 'border-white/10 bg-white/[0.04] text-slate-300 hover:border-white/20 hover:bg-white/[0.07] hover:text-white'
      }`}
    >
      <Icon className="size-4" />
      {label}
    </button>
  );

  return (
    <div className="mx-auto flex w-full max-w-[1500px] flex-col gap-6 px-4 py-5 sm:px-6 lg:px-8 lg:py-8">
      <section className="overflow-hidden rounded-[2rem] border border-cyan-300/15 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.2),transparent_34%),linear-gradient(135deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))] p-6 shadow-2xl shadow-slate-950/40 sm:p-8">
        <div className="grid gap-8 lg:grid-cols-[1.35fr_0.65fr] lg:items-end">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.28em] text-cyan-100">
              <ClipboardCheck className="size-3.5" />
              {copy.hero.eyebrow}
            </div>
            <h1 className="mt-5 max-w-4xl text-3xl font-semibold tracking-tight text-white sm:text-5xl">{copy.hero.title}</h1>
            <p className="mt-4 max-w-3xl text-base leading-8 text-slate-300 sm:text-lg">{copy.hero.description}</p>
            <div className="mt-6 flex flex-wrap gap-3">
              <button type="button" onClick={() => setActiveSection('routes')} className="inline-flex min-h-11 items-center gap-2 rounded-2xl bg-cyan-300 px-4 text-sm font-bold text-slate-950 shadow-lg shadow-cyan-950/30 hover:bg-cyan-200">
                <Route className="size-4" />
                {copy.hero.primaryAction}
              </button>
              <button type="button" onClick={() => setActiveSection('commands')} className="inline-flex min-h-11 items-center gap-2 rounded-2xl border border-white/12 bg-white/8 px-4 text-sm font-semibold text-white hover:bg-white/12">
                <TerminalSquare className="size-4" />
                {copy.hero.secondaryAction}
              </button>
            </div>
          </div>
          <div className="rounded-3xl border border-white/10 bg-white/[0.06] p-5">
            <div className="flex items-center gap-3">
              <div className="flex size-12 items-center justify-center rounded-2xl bg-emerald-300/15 text-emerald-100">
                <ShieldCheck className="size-6" />
              </div>
              <div>
                <p className="text-sm font-semibold text-white">{copy.releaseGate.title}</p>
                <p className="text-xs text-slate-400">{copy.releaseGate.description}</p>
              </div>
            </div>
            <div className="mt-5 space-y-3 text-sm text-slate-300">
              <p className="rounded-2xl border border-emerald-300/15 bg-emerald-300/10 p-3 text-emerald-100">{copy.releaseGate.ready}</p>
              <p className="rounded-2xl border border-amber-300/15 bg-amber-300/10 p-3 text-amber-100">{copy.releaseGate.manual}</p>
              <p className="rounded-2xl border border-rose-300/15 bg-rose-300/10 p-3 text-rose-100">{copy.releaseGate.blocked}</p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {copy.metrics.map((metric) => (
          <MetricCard key={metric.label} {...metric} statusLabel={copy.labels.status[metric.status]} />
        ))}
      </section>

      <section className="grid gap-3 rounded-3xl border border-white/10 bg-white/[0.035] p-3 sm:flex sm:flex-wrap">
        {sectionButton('routes', copy.nav.routes, Route)}
        {sectionButton('language', copy.nav.language, Globe2)}
        {sectionButton('backend', copy.nav.backend, Server)}
        {sectionButton('checklist', copy.nav.checklist, ClipboardCheck)}
        {sectionButton('commands', copy.nav.commands, TerminalSquare)}
      </section>

      {activeSection === 'routes' && (
        <section className="rounded-[2rem] border border-white/10 bg-slate-950/55 p-5 shadow-2xl shadow-slate-950/20 sm:p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-2xl font-semibold text-white">{copy.labels.routeMatrix}</h2>
              <p className="mt-1 text-sm text-slate-400">{copy.labels.passCount}: {statusCounts.pass} · {copy.labels.manualCount}: {statusCounts.manual} · {copy.labels.warningCount}: {statusCounts.warning}</p>
            </div>
          </div>
          <div className="mt-5 grid gap-3">
            {copy.routes.map((route) => (
              <article key={route.id} className="rounded-3xl border border-white/10 bg-white/[0.045] p-4 transition hover:border-cyan-300/25 hover:bg-white/[0.065]">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusPill status={route.status} label={copy.labels.status[route.status]} />
                      <span className="rounded-full border border-white/10 bg-white/[0.05] px-2.5 py-1 text-xs font-semibold text-slate-300">{route.owner}</span>
                    </div>
                    <h3 className="mt-3 text-lg font-semibold text-white">{route.label}</h3>
                    <p className="mt-1 text-sm leading-6 text-slate-400">{route.description}</p>
                    <p className="mt-2 break-all rounded-2xl border border-white/8 bg-slate-950/60 px-3 py-2 font-mono text-xs text-cyan-100">{route.path}</p>
                  </div>
                  <Link href={route.path} className="inline-flex min-h-10 shrink-0 items-center justify-center gap-2 rounded-2xl border border-cyan-300/20 bg-cyan-300/10 px-4 text-sm font-semibold text-cyan-50 hover:bg-cyan-300/15">
                    {copy.labels.open}
                    <ExternalLink className="size-4" />
                  </Link>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {route.checks.map((check) => (
                    <span key={check} className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs font-medium text-slate-300">
                      <CheckCircle2 className="size-3.5 text-emerald-200" />
                      {check}
                    </span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      {activeSection === 'language' && (
        <section className="grid gap-4 lg:grid-cols-[1fr_0.72fr]">
          <div className="rounded-[2rem] border border-white/10 bg-slate-950/55 p-5 sm:p-6">
            <h2 className="text-2xl font-semibold text-white">{copy.labels.languageMatrix}</h2>
            <div className="mt-5 grid gap-3">
              {copy.languageChecks.map((item) => (
                <article key={item.id} className="rounded-3xl border border-white/10 bg-white/[0.045] p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <h3 className="font-semibold text-white">{item.label}</h3>
                    <StatusPill status={item.status} label={copy.labels.status[item.status]} />
                  </div>
                  <p className="mt-2 text-sm leading-6 text-slate-400">{item.description}</p>
                </article>
              ))}
            </div>
          </div>
          <div className="rounded-[2rem] border border-amber-300/15 bg-amber-300/[0.055] p-5 sm:p-6">
            <div className="flex items-center gap-3">
              <AlertTriangle className="size-6 text-amber-100" />
              <h3 className="text-lg font-semibold text-white">{copy.releaseGate.title}</h3>
            </div>
            <p className="mt-3 text-sm leading-7 text-amber-50/80">{copy.releaseGate.description}</p>
            <div className="mt-5 grid gap-3">
              <div className="rounded-2xl border border-white/10 bg-slate-950/35 p-4 text-sm text-slate-200">{copy.releaseGate.manual}</div>
              <div className="rounded-2xl border border-white/10 bg-slate-950/35 p-4 text-sm text-slate-200">{copy.releaseGate.blocked}</div>
            </div>
          </div>
        </section>
      )}

      {activeSection === 'backend' && (
        <section className="rounded-[2rem] border border-white/10 bg-slate-950/55 p-5 sm:p-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-2xl font-semibold text-white">{copy.labels.backendHealth}</h2>
              <p className="mt-1 text-sm text-slate-400">{copy.labels.live}</p>
            </div>
            <button type="button" onClick={runChecks} disabled={isChecking} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-2xl border border-cyan-300/20 bg-cyan-300/10 px-4 text-sm font-semibold text-cyan-50 hover:bg-cyan-300/15 disabled:cursor-not-allowed disabled:opacity-60">
              {isChecking ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
              {copy.labels.retry}
            </button>
          </div>
          <div className="mt-5 grid gap-3">
            {copy.endpoints.map((endpoint) => {
              const result = liveChecks[endpoint.id];
              return (
                <article key={endpoint.id} className="rounded-3xl border border-white/10 bg-white/[0.045] p-4">
                  <div className="grid gap-4 lg:grid-cols-[1fr_0.7fr_0.45fr] lg:items-start">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded-full border border-white/10 bg-white/[0.06] px-2.5 py-1 text-xs font-bold text-white">{endpoint.method}</span>
                        <span className="break-all font-mono text-xs text-cyan-100">{endpoint.path}</span>
                      </div>
                      <h3 className="mt-3 font-semibold text-white">{endpoint.label}</h3>
                      <p className="mt-1 text-sm text-slate-400">{endpoint.description}</p>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-slate-950/45 p-3 text-sm text-slate-300">
                      <span className="text-slate-500">{copy.labels.expected}: </span>{endpoint.expected}
                    </div>
                    <div className="flex flex-col items-start gap-2 lg:items-end">
                      <StatusPill status={result?.status ?? 'manual'} label={result?.label ?? copy.labels.status.manual} />
                      <p className="text-xs text-slate-400">{result?.checkedAt ? `${copy.labels.checked}: ${result.checkedAt}` : result?.detail}</p>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      )}

      {activeSection === 'checklist' && (
        <section className="rounded-[2rem] border border-white/10 bg-slate-950/55 p-5 sm:p-6">
          <h2 className="text-2xl font-semibold text-white">{copy.labels.smokeChecklist}</h2>
          <div className="mt-5 grid gap-3 md:grid-cols-2">
            {copy.smokeChecklist.map((item) => (
              <article key={item.id} className="rounded-3xl border border-white/10 bg-white/[0.045] p-4">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="font-semibold text-white">{item.label}</h3>
                  <StatusPill status={item.status} label={copy.labels.status[item.status]} />
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-400">{item.description}</p>
              </article>
            ))}
          </div>
        </section>
      )}

      {activeSection === 'commands' && (
        <section className="rounded-[2rem] border border-white/10 bg-slate-950/55 p-5 sm:p-6">
          <h2 className="text-2xl font-semibold text-white">{copy.labels.commandCenter}</h2>
          <div className="mt-5 grid gap-3">
            {copy.commands.map((command) => (
              <article key={command.label} className="rounded-3xl border border-white/10 bg-white/[0.045] p-4">
                <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                  <div className="min-w-0">
                    <h3 className="font-semibold text-white">{command.label}</h3>
                    <p className="mt-1 text-sm text-slate-400">{command.description}</p>
                    <pre className="mt-3 overflow-x-auto rounded-2xl border border-white/10 bg-slate-950/70 p-3 text-xs leading-6 text-cyan-50"><code>{command.command}</code></pre>
                  </div>
                  <button type="button" onClick={() => copyCommand(command.label, command.command)} className="inline-flex min-h-10 shrink-0 items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/[0.06] px-4 text-sm font-semibold text-white hover:bg-white/[0.1]">
                    <Copy className="size-4" />
                    {copiedCommand === command.label ? copy.labels.copied : copy.labels.copy}
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      <section className="grid gap-4 rounded-[2rem] border border-white/10 bg-white/[0.035] p-5 text-sm text-slate-300 sm:grid-cols-4 sm:p-6">
        <div className="flex items-center gap-3"><Activity className="size-5 text-emerald-200" /><span>{copy.labels.passCount}: {statusCounts.pass}</span></div>
        <div className="flex items-center gap-3"><AlertTriangle className="size-5 text-amber-200" /><span>{copy.labels.warningCount}: {statusCounts.warning}</span></div>
        <div className="flex items-center gap-3"><ClipboardCheck className="size-5 text-sky-200" /><span>{copy.labels.manualCount}: {statusCounts.manual}</span></div>
        <div className="flex items-center gap-3"><ShieldCheck className="size-5 text-rose-200" /><span>{copy.labels.failCount}: {statusCounts.fail}</span></div>
      </section>
    </div>
  );
}
