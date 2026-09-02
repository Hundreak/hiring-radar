#!/usr/bin/env node
import {existsSync, readFileSync} from 'node:fs';
import {join} from 'node:path';

const root = process.argv[2] || process.cwd();
const checks = [
  {
    path: 'src/app/[locale]/(dashboard)/settings/security/page.tsx',
    includes: [
      'SecurityCenterHero',
      'SecurityMetricCard',
      'SecurityActionRail',
      'securityScore',
      'scrollToSecuritySection',
      'id="security-password"',
      'id="security-sessions"',
    ],
  },
  {
    path: 'src/components/settings/security-center-primitives.tsx',
    includes: [
      'data-security-center="hero"',
      'data-security-center="metric"',
      'data-security-center="actions"',
      'SecurityActionCard',
    ],
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

for (const locale of ['tr', 'en', 'de']) {
  const messageFile = join(root, `messages/${locale}.json`);
  const content = readFileSync(messageFile, 'utf8');
  for (const needle of [
    '"center"',
    '"scoreLabel"',
    '"checklistLabel"',
    '"twoFactor"',
    '"sessions"',
  ]) {
    if (!content.includes(needle)) {
      failures.push(`messages/${locale}.json: missing ${needle}`);
    }
  }
}

if (failures.length) {
  console.error('Security center UX checks failed:');
  for (const failure of failures) console.error(` - ${failure}`);
  process.exit(1);
}

console.log('Security center UX checks passed.');
