#!/usr/bin/env node
import {existsSync, readFileSync} from 'node:fs';
import {join, resolve} from 'node:path';

const root = resolve(process.argv[2] || '.');
const requiredFiles = [
  'src/components/ui/pagination-controls.tsx',
  'src/lib/pagination.ts',
  'src/app/[locale]/(dashboard)/jobs/page.tsx',
  'src/app/[locale]/(dashboard)/matches/page.tsx',
  'src/app/[locale]/(dashboard)/saved/page.tsx',
  'src/components/employer/jobs/employer-jobs-page.tsx',
];

const failures = [];
for (const file of requiredFiles) {
  const path = join(root, file);
  if (!existsSync(path)) {
    failures.push(`Missing pagination UX file: ${file}`);
  }
}

const expectations = [
  ['src/app/[locale]/(dashboard)/jobs/page.tsx', ['useJobsQuery(query, {page, pageSize})', '<PaginationControls']],
  ['src/app/[locale]/(dashboard)/matches/page.tsx', ['useMatchesQuery({page, pageSize})', '<PaginationControls']],
  ['src/app/[locale]/(dashboard)/saved/page.tsx', ['useSavedJobsQuery({page, pageSize, status: statusFilter})', '<PaginationControls']],
  ['src/components/employer/jobs/employer-jobs-page.tsx', ['paginateClientItems', '<PaginationControls']],
  ['src/hooks/use-api-queries.ts', ['placeholderData: (previous) => previous', 'queryKeys.jobs.saved(params)']],
  ['src/lib/api.ts', ['buildJobsQuery', 'buildSavedJobsQuery']],
];

for (const [file, needles] of expectations) {
  const path = join(root, file);
  if (!existsSync(path)) continue;
  const contents = readFileSync(path, 'utf8');
  for (const needle of needles) {
    if (!contents.includes(needle)) {
      failures.push(`${file} is missing expected marker: ${needle}`);
    }
  }
}

for (const locale of ['tr', 'en', 'de']) {
  const file = `messages/${locale}.json`;
  const path = join(root, file);
  if (!existsSync(path)) {
    failures.push(`Missing locale file: ${file}`);
    continue;
  }
  const contents = readFileSync(path, 'utf8');
  for (const key of ['paginationPrevious', 'paginationNext', 'paginationPageSize', 'paginationSummary']) {
    if (!contents.includes(`"${key}"`)) {
      failures.push(`${file} is missing ${key}`);
    }
  }
}

if (failures.length > 0) {
  console.error('Pagination UX checks failed:');
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log('Pagination UX checks passed.');
