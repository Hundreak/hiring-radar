'use client';

import {useId} from 'react';

type CopilotSize = 'sm' | 'md' | 'lg';

interface SizeMetrics {
  wrapper: string;
  emblem: number;
}

function getMetrics(size: CopilotSize): SizeMetrics {
  if (size === 'sm') return {wrapper: 'size-9', emblem: 36};
  if (size === 'lg') return {wrapper: 'size-12', emblem: 48};
  return {wrapper: 'size-10', emblem: 40};
}

// Bold C-arc mark: 270° sweep with gradient, two terminal dots.
// Reads at any size; unique gradient IDs prevent DOM collisions when multiple instances coexist.
function CoreSiftEmblem({size}: {size: number}) {
  const uid = useId().replace(/:/g, 'x');
  const bgId = `cs-bg-${uid}`;
  const arcId = `cs-arc-${uid}`;
  const glowId = `cs-glow-${uid}`;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      role="img"
      aria-label="CoreSift AI"
    >
      <defs>
        <radialGradient id={bgId} cx="38%" cy="32%" r="68%" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#1c2d58" />
          <stop offset="55%" stopColor="#0c152e" />
          <stop offset="100%" stopColor="#060a1d" />
        </radialGradient>

        <linearGradient id={arcId} x1="74" y1="26" x2="50" y2="80" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#93c5fd" />
          <stop offset="48%" stopColor="#818cf8" />
          <stop offset="100%" stopColor="#c084fc" />
        </linearGradient>

        <filter id={glowId} x="-38%" y="-38%" width="176%" height="176%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Background */}
      <circle cx="50" cy="50" r="46" fill={`url(#${bgId})`} />
      <circle cx="50" cy="50" r="45.5" stroke="rgba(148,163,255,0.10)" strokeWidth="1" />

      {/* Primary arc: 270° CCW from (74,26) through left side to (74,74) */}
      <path
        d="M74,26 A34,34 0 1,0 74,74"
        stroke={`url(#${arcId})`}
        strokeWidth="8"
        strokeLinecap="round"
        fill="none"
        filter={`url(#${glowId})`}
      />

      {/* Top terminal — bright anchor at the arc head */}
      <circle cx="74" cy="26" r="5" fill="#bfdbfe" opacity="0.90" />

      {/* Bottom terminal — softer tail */}
      <circle cx="74" cy="74" r="3" fill="#c4b5fd" opacity="0.58" />
    </svg>
  );
}

export function CopilotMark({size = 'md'}: {size?: CopilotSize}) {
  const metrics = getMetrics(size);
  return (
    <span
      className={`relative inline-flex shrink-0 items-center justify-center rounded-full drop-shadow-[0_4px_18px_rgba(129,140,248,0.38)] ${metrics.wrapper}`}
    >
      <CoreSiftEmblem size={metrics.emblem} />
    </span>
  );
}

export function CopilotBrand({subtitle, stacked = true}: {subtitle?: string | null; stacked?: boolean}) {
  const subtitleText = subtitle?.trim() || null;

  return (
    <div className="flex items-center gap-2.5">
      <CopilotMark size={stacked ? 'md' : 'sm'} />
      <div className="min-w-0">
        <div className="text-[13px] font-semibold leading-none tracking-[-0.01em] text-white/90">
          CoreSift AI
        </div>
        {subtitleText ? (
          <div className={`mt-1 leading-tight text-slate-400 ${stacked ? 'text-xs' : 'text-[11px]'}`}>
            {subtitleText}
          </div>
        ) : null}
      </div>
    </div>
  );
}
