#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const root = process.cwd();

const checks = [
  {
    label: 'Legacy detailed profile API must not remain in frontend/api surface',
    file: 'src/lib/api.ts',
    forbidden: [/\bgetDetailedProfile\s*\(/, /\bupdateDetailedProfile\s*\(/],
  },
  {
    label: 'Legacy detailed profile types must not remain in frontend/user types',
    file: 'src/types/user.ts',
    forbidden: [/\binterface\s+UserDetailedProfile\b/, /\binterface\s+UserDetailedProfileUpdate\b/],
  },
  {
    label: 'Profile workspace must still depend on aggregate contract',
    file: 'src/components/profile/profile-aggregate-workspace.tsx',
    required: [/(applyAggregateSnapshot|applyWorkspaceAggregate)/, /(refreshAggregateSilently|refreshWorkspace|refreshWorkspaceState)/, /(workspaceMessage|workspaceFeedback|message|errorMessage)/],
  },
  {
    label: 'CV upload module must keep aggregate refresh semantics',
    file: 'src/components/profile/cv-upload-module.tsx',
    required: [/workspace_refresh_required/, /onWorkspaceRefresh/],
  },
  {
    label: 'Feedback banner must remain a client component with the exported surface',
    file: 'src/components/ui/feedback-banner.tsx',
    required: [/^'use client';/m, /export\s+function\s+FeedbackBanner/, /export\s+type\s+FeedbackTone/],
  },
  {
    label: 'Profile workspace must not expose raw browser confirm dialogs',
    file: 'src/components/profile/profile-aggregate-workspace.tsx',
    forbidden: [/window\.confirm\s*\(/],
  },
  {
    label: 'Profile workspace must not render raw avatar status string anymore',
    file: 'src/components/profile/profile-aggregate-workspace.tsx',
    forbidden: [/profile\.avatar\.status/],
  },
  {
    label: 'User menu must handle logout and profile refresh flows',
    file: 'src/components/layout/user-menu.tsx',
    required: [/api\.logout\(/, /(refreshProfile|loadProfileSurface)\(/, /loggingOut|logoutBusy|isLoggingOut/],
  },
  {
    label: 'Notifications settings page must keep guarded save/logout states',
    file: 'src/app/[locale]/\(dashboard\)/settings/notifications/page.tsx',
    required: [/saving/, /api\.logout\(/],
  },
];

function read(file) {
  const absolute = path.join(root, file);
  if (!fs.existsSync(absolute)) {
    return {ok: false, reason: `Missing file: ${file}`};
  }
  return {ok: true, text: fs.readFileSync(absolute, 'utf8')};
}

const failures = [];
const lines = [];

for (const check of checks) {
  const loaded = read(check.file);
  if (!loaded.ok) {
    failures.push(`${check.label} -> ${loaded.reason}`);
    continue;
  }
  const text = loaded.text;
  let passed = true;

  for (const pattern of check.required ?? []) {
    if (!pattern.test(text)) {
      passed = false;
      failures.push(`${check.label} -> missing required pattern ${pattern} in ${check.file}`);
    }
  }

  for (const pattern of check.forbidden ?? []) {
    if (pattern.test(text)) {
      passed = false;
      failures.push(`${check.label} -> found forbidden pattern ${pattern} in ${check.file}`);
    }
  }

  lines.push(`${passed ? 'PASS' : 'FAIL'}  ${check.label}`);
}

console.log('=== Phase 1A Frontend Contract Audit ===');
for (const line of lines) console.log(line);

if (failures.length > 0) {
  console.error('\nDetailed failures:');
  for (const item of failures) console.error(`- ${item}`);
  process.exit(1);
}

console.log('\nAll contract checks passed.');
