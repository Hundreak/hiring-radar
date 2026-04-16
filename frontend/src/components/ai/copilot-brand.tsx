'use client';

type CopilotSize = 'sm' | 'md' | 'lg';

function getMetrics(size: CopilotSize) {
  if (size === 'sm') {
    return {
      wrapper: 'size-10',
      emblem: 40,
    };
  }

  if (size === 'lg') {
    return {
      wrapper: 'size-14',
      emblem: 56,
    };
  }

  return {
    wrapper: 'size-12',
    emblem: 48,
  };
}

function CoreSiftEmblem({size}: {size: number}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      role="img"
      aria-label="CoreSift AI"
      className="drop-shadow-[0_10px_26px_rgba(109,71,255,0.34)]"
    >
      <defs>
        <radialGradient id="cs-bg-core" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(34 24) rotate(47) scale(58 54)">
          <stop offset="0" stopColor="#304D98" />
          <stop offset="0.38" stopColor="#1B2E67" />
          <stop offset="0.78" stopColor="#0F1C45" />
          <stop offset="1" stopColor="#09152F" />
        </radialGradient>
        <radialGradient id="cs-inner-glow" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(35 27) rotate(49) scale(42 39)">
          <stop offset="0" stopColor="#DDF4FF" stopOpacity="0.48" />
          <stop offset="0.38" stopColor="#A5CFFF" stopOpacity="0.18" />
          <stop offset="1" stopColor="#A5CFFF" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="cs-crescent-main" x1="27" y1="17" x2="72" y2="80" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#E6F8FF" />
          <stop offset="0.28" stopColor="#BFE8FF" />
          <stop offset="0.58" stopColor="#93BFFF" />
          <stop offset="0.82" stopColor="#9B8DFF" />
          <stop offset="1" stopColor="#D7B7FF" />
        </linearGradient>
        <linearGradient id="cs-crescent-accent" x1="26" y1="48" x2="80" y2="77" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#99C4FF" />
          <stop offset="0.54" stopColor="#A888FF" />
          <stop offset="1" stopColor="#E3C1FF" />
        </linearGradient>
        <linearGradient id="cs-signature" x1="38" y1="39" x2="70" y2="59" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#D8F4FF" />
          <stop offset="0.55" stopColor="#B7D6FF" />
          <stop offset="1" stopColor="#D8C6FF" />
        </linearGradient>
        <filter id="cs-soft-shadow" x="-24" y="-24" width="148" height="148" colorInterpolationFilters="sRGB">
          <feGaussianBlur stdDeviation="4" result="blur" />
          <feColorMatrix
            in="blur"
            type="matrix"
            values="1 0 0 0 0
                    0 1 0 0 0
                    0 0 1 0 0
                    0 0 0 0.24 0"
          />
        </filter>
      </defs>

      <g filter="url(#cs-soft-shadow)">
        <circle cx="50" cy="50" r="46" fill="#0B1533" />
      </g>
      <circle cx="50" cy="50" r="46" fill="url(#cs-bg-core)" />
      <circle cx="50" cy="50" r="45.2" stroke="rgba(227,234,255,0.14)" strokeWidth="1.6" />
      <circle cx="50" cy="50" r="33" fill="url(#cs-inner-glow)" />

      <path
        d="M72.6 20.4C61.6 16.4 49.1 16.8 38.4 22.4C22.6 30.7 13.3 48.4 16.2 66.1C18.4 79.4 26.1 90.5 37.4 96.4C31 90.3 26.8 82.4 25.8 73.5C23.7 55.8 32.3 38.6 47.8 30.3C56.2 25.9 65.8 24.4 74.8 26L72.6 20.4Z"
        fill="url(#cs-crescent-main)"
      />
      <path
        d="M32.8 66.7C37.2 76.6 45.8 84.4 56.6 87.4C67.5 90.4 79.1 88.3 88.1 81.8C80.2 90.9 69 96.3 57.1 96.4C44.3 96.6 32.3 90.6 24.9 80.2L32.8 66.7Z"
        fill="url(#cs-crescent-accent)"
        fillOpacity="0.96"
      />
      <path
        d="M73.4 20.8C60.5 16.4 46.2 18.2 34.9 25.6C22.5 33.8 15.3 47.9 15.6 62.7"
        stroke="rgba(250,252,255,0.52)"
        strokeWidth="1.5"
        strokeLinecap="round"
      />

      <path
        d="M38.2 59.4C43.6 53.2 49.3 48.6 55 46.3C57.9 45.1 60.9 44.5 63.8 44.8C66.8 45 68.8 46.4 69.8 48.8C70.9 51.6 70.3 54.2 68 56.4C65.2 59 61 60.4 55.3 60.5C51.8 60.6 48.4 60.2 44.8 59.2"
        stroke="url(#cs-signature)"
        strokeWidth="3.6"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.96"
      />
      <path
        d="M57.8 44.8C59.6 49 61.2 53.1 62.6 57.2"
        stroke="url(#cs-signature)"
        strokeWidth="2.8"
        strokeLinecap="round"
        opacity="0.88"
      />

      <g fill="#F7F5FF">
        <path d="M53.2 24.6L55.4 31.1L61.9 33.3L55.4 35.5L53.2 42L51 35.5L44.5 33.3L51 31.1L53.2 24.6Z" />
        <path d="M71.8 31.2L72.8 34L75.6 35L72.8 36L71.8 38.8L70.8 36L68 35L70.8 34L71.8 31.2Z" opacity="0.84" />
        <path d="M30.4 59.8L31.3 62.4L33.9 63.3L31.3 64.2L30.4 66.8L29.5 64.2L26.9 63.3L29.5 62.4L30.4 59.8Z" opacity="0.76" />
      </g>
    </svg>
  );
}

export function CopilotMark({size = 'md'}: {size?: CopilotSize}) {
  const metrics = getMetrics(size);

  return (
    <span className={`relative inline-flex shrink-0 items-center justify-center rounded-full ${metrics.wrapper}`}>
      <CoreSiftEmblem size={metrics.emblem} />
    </span>
  );
}

export function CopilotBrand({subtitle, stacked = true}: {subtitle?: string | null; stacked?: boolean}) {
  const subtitleText = subtitle?.trim() || null;

  if (!stacked) {
    return (
      <div className="flex items-center gap-3">
        <CopilotMark size="md" />
        <div className="min-w-0">
          <div className="text-[11px] font-semibold uppercase tracking-[0.34em] text-accent/90">CoreSift AI</div>
          {subtitleText ? <div className="mt-0.5 text-sm font-semibold text-foreground">{subtitleText}</div> : null}
        </div>
      </div>
    );
  }

  return (
    <div className="flex w-[92px] shrink-0 flex-col items-center justify-center text-center">
      <CopilotMark size="lg" />
      <div className="mt-2 text-[10px] font-semibold uppercase leading-tight tracking-[0.36em] text-accent/90">CoreSift AI</div>
      {subtitleText ? <div className="mt-1 text-[11px] font-medium leading-4 text-muted-foreground">{subtitleText}</div> : null}
    </div>
  );
}
