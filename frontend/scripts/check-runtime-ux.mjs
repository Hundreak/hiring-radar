#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const ROOT = path.resolve(process.argv[2] || process.cwd());
const requiredFiles = [
  'src/components/performance/route-loading-shell.tsx',
  'src/components/ai/copilot-widget-loader.tsx',
  'src/app/[locale]/(dashboard)/loading.tsx',
  'src/app/[locale]/employer/loading.tsx',
];

const failures = [];

for (const rel of requiredFiles) {
  const abs = path.join(ROOT, rel);
  if (!fs.existsSync(abs)) {
    failures.push(`Missing runtime UX file: ${rel}`);
  }
}

const appShellPath = path.join(ROOT, 'src/components/layout/app-shell.tsx');
if (fs.existsSync(appShellPath)) {
  const appShell = fs.readFileSync(appShellPath, 'utf8');
  if (!appShell.includes('CopilotWidgetLoader')) {
    failures.push('AppShell must render CopilotWidgetLoader so the heavy copilot panel is deferred.');
  }
  if (appShell.includes("@/components/ai/copilot-widget';")) {
    failures.push('AppShell still imports the eager CopilotWidget directly.');
  }
}

const loaderPath = path.join(ROOT, 'src/components/ai/copilot-widget-loader.tsx');
if (fs.existsSync(loaderPath)) {
  const loader = fs.readFileSync(loaderPath, 'utf8');
  if (!loader.includes('dynamic(') || !loader.includes('ssr: false')) {
    failures.push('CopilotWidgetLoader must use next/dynamic with ssr: false.');
  }
}

if (failures.length > 0) {
  console.error('Runtime UX performance checks failed:');
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log('Runtime UX performance checks passed.');
