#!/usr/bin/env node
import {readFileSync, existsSync} from 'node:fs';
import {join} from 'node:path';

const root = process.argv[2] ?? '.';
const requiredFiles = [
  'src/components/employer/compliance/employer-compliance-page.tsx',
  'src/app/[locale]/employer/compliance/page.tsx',
  'src/lib/api.ts',
  'src/hooks/use-api-queries.ts',
  'src/lib/query-keys.ts',
  'src/types/user.ts',
];

const missing = requiredFiles.filter((file) => !existsSync(join(root, file)));
if (missing.length) {
  console.error(`Missing employer audit evidence files:\n${missing.join('\n')}`);
  process.exit(1);
}

const api = readFileSync(join(root, 'src/lib/api.ts'), 'utf8');
const hooks = readFileSync(join(root, 'src/hooks/use-api-queries.ts'), 'utf8');
const page = readFileSync(join(root, 'src/components/employer/compliance/employer-compliance-page.tsx'), 'utf8');

const checks = [
  ['API list endpoint', api.includes('/employer/compliance/audit-events')],
  ['API export endpoint', api.includes('/employer/compliance/audit-events/export')],
  ['React Query hook', hooks.includes('useEmployerAuditEventsQuery')],
  ['CSV export action', page.includes("format: 'csv'") && page.includes('window.open')],
  ['JSON export action', page.includes('exportEmployerAuditEvents')],
  ['Sensitivity badges', page.includes('EmployerAuditSensitivity') && page.includes('sensitivityTone')],
];

const failed = checks.filter(([, ok]) => !ok).map(([name]) => name);
if (failed.length) {
  console.error(`Employer audit evidence checks failed:\n${failed.join('\n')}`);
  process.exit(1);
}

console.log('Employer audit evidence UX checks passed.');
