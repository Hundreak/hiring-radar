import {readFileSync} from 'node:fs';
import {join} from 'node:path';

const root = process.cwd();
const page = readFileSync(join(root, 'src/app/[locale]/(dashboard)/settings/notifications/page.tsx'), 'utf8');
const api = readFileSync(join(root, 'src/lib/api.ts'), 'utf8');
const types = readFileSync(join(root, 'src/types/user.ts'), 'utf8');

const requiredPageTokens = [
  'Communication control center',
  'api.getUserNotificationPreferences',
  'api.updateUserNotificationPreferences',
  'quiet_hours_enabled',
  'security_alerts_enabled',
];

for (const token of requiredPageTokens) {
  if (!page.includes(token)) {
    throw new Error(`Notification center page is missing token: ${token}`);
  }
}

for (const token of ['getUserNotificationPreferences', 'updateUserNotificationPreferences']) {
  if (!api.includes(token)) {
    throw new Error(`API client is missing ${token}.`);
  }
}

for (const token of ['UserNotificationPreference', 'UpdateUserNotificationPreferenceRequest']) {
  if (!types.includes(token)) {
    throw new Error(`User types are missing ${token}.`);
  }
}

console.log('Notification center UX checks passed.');
