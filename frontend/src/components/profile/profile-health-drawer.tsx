'use client';

import {useEffect, useRef} from 'react';

import type {ProfileCompletionSection, ProfileSuggestionItem} from '@/types/profile';
import {publishRightSurface} from '@/lib/copilot-ui';

type DrawerCopy = {
  title: string;
  subtitle: string;
  completionLabel: string;
  strongAreasTitle: string;
  focusAreasTitle: string;
  suggestionsTitle: string;
  emptyLabel: string;
  close: string;
};

function labelForStatus(status: ProfileCompletionSection['status']) {
  if (status === 'done') return 'Tamam';
  if (status === 'partial') return 'Geliştirilebilir';
  return 'Eksik';
}

function labelForImpact(level: string, copy: DrawerCopy) {
  const locale = copy.close === 'Close' ? 'en' : copy.close === 'Schließen' ? 'de' : 'tr';
  if (locale === 'en') {
    if (level === 'high') return 'Priority';
    if (level === 'medium') return 'Helpful';
    if (level === 'low') return 'Nice to have';
    return 'Suggestion';
  }
  if (locale === 'de') {
    if (level === 'high') return 'Priorität';
    if (level === 'medium') return 'Sinnvoll';
    if (level === 'low') return 'Optional';
    return 'Empfehlung';
  }
  if (level === 'high') return 'Öncelikli';
  if (level === 'medium') return 'Faydalı';
  if (level === 'low') return 'İyi olur';
  return 'Öneri';
}

function toneClasses(status: ProfileCompletionSection['status']) {
  if (status === 'done') return 'border-emerald-200 bg-emerald-50 text-emerald-700';
  if (status === 'partial') return 'border-amber-200 bg-amber-50 text-amber-700';
  return 'border-rose-200 bg-rose-50 text-rose-700';
}

export function ProfileHealthDrawer({open, onClose, completionScore, sections, suggestions, copy}: {open: boolean; onClose: () => void; completionScore: number; sections: ProfileCompletionSection[]; suggestions: ProfileSuggestionItem[]; copy: DrawerCopy;}) {
  const strongAreas = sections.filter((section) => section.status === 'done');
  const focusAreas = sections.filter((section) => section.status !== 'done');
  const drawerRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined') return undefined;

    const emitSurfaceState = () => {
      const width = open && drawerRef.current ? drawerRef.current.getBoundingClientRect().width : 0;
      publishRightSurface({open, width, source: 'profile-health-drawer'});
    };

    emitSurfaceState();
    if (!open) {
      return () => publishRightSurface({open: false, width: 0, source: 'profile-health-drawer'});
    }

    const frame = window.requestAnimationFrame(emitSurfaceState);
    const observer = new ResizeObserver(() => emitSurfaceState());
    if (drawerRef.current) observer.observe(drawerRef.current);
    window.addEventListener('resize', emitSurfaceState);

    return () => {
      window.cancelAnimationFrame(frame);
      observer.disconnect();
      window.removeEventListener('resize', emitSurfaceState);
      publishRightSurface({open: false, width: 0, source: 'profile-health-drawer'});
    };
  }, [open]);

  return (
    <>
      <div
        className={[
          'fixed inset-0 z-40 transition-all duration-300',
          open ? 'pointer-events-auto bg-black/20 backdrop-blur-[3px]' : 'pointer-events-none bg-transparent backdrop-blur-none',
        ].join(' ')}
        onClick={onClose}
      />

      <aside
        ref={drawerRef}
        data-noytera-right-surface={open ? 'open' : 'closed'}
        data-right-drawer={open ? 'open' : 'closed'}
        data-drawer-side="right"
        data-state={open ? 'open' : 'closed'}
        className={[
          'fixed right-0 top-0 z-50 h-full w-full max-w-xl transform border-l border-border bg-background shadow-[0_30px_80px_-40px_rgba(15,23,42,0.5)] transition-transform duration-300',
          open ? 'translate-x-0' : 'translate-x-full',
        ].join(' ')}
        aria-hidden={!open}
      >
        <div className="flex h-full flex-col">
          <div className="flex items-start justify-between gap-4 border-b border-border px-6 py-5">
            <div className="space-y-1">
              <h3 className="text-lg font-semibold tracking-tight text-foreground">{copy.title}</h3>
              <p className="text-sm leading-6 text-muted-foreground">{copy.subtitle}</p>
            </div>
            <button type="button" onClick={onClose} className="inline-flex h-10 items-center justify-center rounded-2xl border border-border bg-background px-4 text-sm font-medium text-foreground transition hover:bg-muted">{copy.close}</button>
          </div>

          <div className="flex-1 overflow-y-auto px-6 py-6">
            <section className="rounded-3xl border border-border bg-background p-5">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <div className="text-sm font-semibold text-foreground">{copy.completionLabel}</div>
                  <p className="mt-1 text-sm leading-6 text-muted-foreground">Profilinin hangi alanlarda güçlü olduğunu ve hangi başlıklarda kısa dokunuş gerektiğini buradan takip edebilirsin.</p>
                </div>
                <div className="rounded-full border border-border bg-muted/30 px-4 py-2 text-sm font-semibold text-foreground">%{Math.round(completionScore)}</div>
              </div>
              <div className="mt-4 h-3 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full bg-foreground transition-all duration-500" style={{width: `${Math.min(Math.max(completionScore, 0), 100)}%`}} /></div>
            </section>

            <section className="mt-5 rounded-3xl border border-border bg-background p-5">
              <div className="text-sm font-semibold text-foreground">{copy.strongAreasTitle}</div>
              <div className="mt-4 space-y-3">
                {strongAreas.length > 0 ? strongAreas.map((section) => (
                  <div key={section.key} className="rounded-2xl border border-border bg-muted/20 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-foreground">{section.label}</div>
                        <p className="mt-1 text-sm leading-6 text-muted-foreground">Bu alan görünür durumda. Dilersen küçük düzenlemelerle daha da netleştirebilirsin.</p>
                      </div>
                      <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-medium ${toneClasses(section.status)}`}>{labelForStatus(section.status)}</span>
                    </div>
                  </div>
                )) : <div className="rounded-2xl border border-dashed border-border px-4 py-4 text-sm text-muted-foreground">{copy.emptyLabel}</div>}
              </div>
            </section>

            <section className="mt-5 rounded-3xl border border-border bg-background p-5">
              <div className="text-sm font-semibold text-foreground">{copy.focusAreasTitle}</div>
              <div className="mt-4 space-y-3">
                {focusAreas.length > 0 ? focusAreas.map((section) => (
                  <div key={section.key} className="rounded-2xl border border-border bg-muted/20 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-foreground">{section.label}</div>
                        <p className="mt-1 text-sm leading-6 text-muted-foreground">Bu başlık tamamlandığında profilin çok daha güven veren ve anlaşılır görünecek.</p>
                      </div>
                      <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-medium ${toneClasses(section.status)}`}>{labelForStatus(section.status)}</span>
                    </div>
                  </div>
                )) : <div className="rounded-2xl border border-dashed border-border px-4 py-4 text-sm text-muted-foreground">{copy.emptyLabel}</div>}
              </div>
            </section>

            <section className="mt-5 rounded-3xl border border-border bg-background p-5">
              <div className="text-sm font-semibold text-foreground">{copy.suggestionsTitle}</div>
              <div className="mt-4 space-y-3">
                {suggestions.length > 0 ? suggestions.slice(0, 6).map((item) => (
                  <div key={item.id} className="rounded-2xl border border-border bg-muted/20 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-semibold text-foreground">{item.title}</div>
                      <span className="inline-flex rounded-full border border-border bg-background px-3 py-1 text-xs font-medium text-muted-foreground">{labelForImpact(item.impact_level, copy)}</span>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.description}</p>
                  </div>
                )) : <div className="rounded-2xl border border-dashed border-border px-4 py-4 text-sm text-muted-foreground">{copy.emptyLabel}</div>}
              </div>
            </section>
          </div>
        </div>
      </aside>
    </>
  );
}
