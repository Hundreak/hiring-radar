#!/usr/bin/env node
import {readFileSync, existsSync} from 'node:fs';
import {join} from 'node:path';

const root = process.argv[2] || process.cwd();
const checks = [
  {
    path: 'src/lib/auth-session-events.ts',
    includes: ['AUTH_SESSION_EXPIRED_EVENT', 'shouldEmitSessionExpired', 'emitSessionExpiredFromApiError'],
  },
  {
    path: 'src/lib/auth-redirect.ts',
    includes: ['buildLoginRedirectHref', 'role', 'redirect'],
  },
  {
    path: 'src/components/auth/session-expiry-boundary.tsx',
    includes: ['onSessionExpired', 'queryClient.clear()', 'role="alertdialog"'],
  },
  {
    path: 'src/lib/api.ts',
    includes: ['emitSessionExpiredFromApiError(path, error)', 'emitSessionExpiredFromApiError(\'/user/profile/ai-audit/export\'', 'throw error'],
  },
  {
    path: 'src/components/providers/query-provider.tsx',
    includes: ['<SessionExpiryBoundary />'],
  },
  {
    path: 'src/components/auth/auth-guard.tsx',
    includes: ['buildLoginRedirectHref', "surface: 'candidate'"],
  },
  {
    path: 'src/components/employer/employer-auth-gate.tsx',
    includes: ['buildLoginRedirectHref', "surface: 'employer'"],
  },
];

const failures = [];
for (const check of checks) {
  const absolute = join(root, check.path);
  if (!existsSync(absolute)) {
    failures.push(`${check.path}: missing file`);
    continue;
  }
  const content = readFileSync(absolute, 'utf8');
  for (const needle of check.includes) {
    if (!content.includes(needle)) {
      failures.push(`${check.path}: missing ${needle}`);
    }
  }
}

const events = readFileSync(join(root, 'src/lib/auth-session-events.ts'), 'utf8');
if (!events.includes("'/user/auth/login-password'") || !events.includes("'/employer/auth/login'")) {
  failures.push('src/lib/auth-session-events.ts: auth start endpoints must be excluded from global expiry events');
}

if (failures.length) {
  console.error('Auth session UX checks failed:');
  for (const failure of failures) console.error(` - ${failure}`);
  process.exit(1);
}

console.log('Auth session UX checks passed.');
