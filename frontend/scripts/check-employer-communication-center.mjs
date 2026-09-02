#!/usr/bin/env node
import {readFileSync, existsSync} from 'node:fs';
import {join, resolve} from 'node:path';

const root = resolve(process.argv[2] ?? '.');
const requiredFiles = [
  'src/components/employer/settings/employer-settings-page.tsx',
  'src/lib/api.ts',
  'src/hooks/use-api-queries.ts',
  'src/lib/query-keys.ts',
  'src/types/user.ts',
];

for (const relative of requiredFiles) {
  if (!existsSync(join(root, relative))) {
    console.error(`Missing required employer communication center file: ${relative}`);
    process.exit(1);
  }
}

const settingsPage = readFileSync(join(root, 'src/components/employer/settings/employer-settings-page.tsx'), 'utf8');
const api = readFileSync(join(root, 'src/lib/api.ts'), 'utf8');
const hooks = readFileSync(join(root, 'src/hooks/use-api-queries.ts'), 'utf8');
const queryKeys = readFileSync(join(root, 'src/lib/query-keys.ts'), 'utf8');
const types = readFileSync(join(root, 'src/types/user.ts'), 'utf8');
const copy = readFileSync(join(root, 'src/lib/employer-page-copy.ts'), 'utf8');

const checks = [
  [settingsPage.includes('useEmployerCommunicationPreferencesQuery'), 'settings page must use communication preferences query'],
  [settingsPage.includes('useUpdateEmployerCommunicationPreferencesMutation'), 'settings page must use communication preferences mutation'],
  [(settingsPage + copy).includes('route_campaign_review_to'), 'settings page must expose campaign routing'],
  [(settingsPage + copy).includes('security_alerts_enabled'), 'settings page must keep security alerts visible'],
  [api.includes('/employer/settings/communication-preferences'), 'api client must call employer communication preferences endpoint'],
  [hooks.includes('useEmployerCommunicationPreferencesQuery'), 'hooks must include employer communication preferences query'],
  [hooks.includes('useUpdateEmployerCommunicationPreferencesMutation'), 'hooks must include employer communication preferences mutation'],
  [queryKeys.includes('communicationPreferences'), 'query keys must include employer communication preferences'],
  [types.includes('EmployerCommunicationPreferencesResponse'), 'types must include employer communication preference response'],
];

for (const [ok, message] of checks) {
  if (!ok) {
    console.error(message);
    process.exit(1);
  }
}

console.log('Employer communication center UX checks passed.');
