#!/usr/bin/env node
import {readdirSync, readFileSync, statSync} from 'node:fs';
import {join, relative} from 'node:path';

const root = process.argv[2] ?? 'src';
const maxLines = Number(process.env.FRONTEND_COMPONENT_MAX_LINES ?? '2000');
const extensions = new Set(['.ts', '.tsx']);
const ignoredFragments = new Set(['node_modules', '.next']);
const offenders = [];

function hasSupportedExtension(filePath) {
  return [...extensions].some((extension) => filePath.endsWith(extension));
}

function walk(dir) {
  for (const entry of readdirSync(dir)) {
    const path = join(dir, entry);
    if ([...ignoredFragments].some((fragment) => path.includes(fragment))) {
      continue;
    }
    const stat = statSync(path);
    if (stat.isDirectory()) {
      walk(path);
      continue;
    }
    if (!hasSupportedExtension(path)) {
      continue;
    }
    const lineCount = readFileSync(path, 'utf8').split('\n').length;
    if (lineCount > maxLines) {
      offenders.push({path: relative(process.cwd(), path), lineCount});
    }
  }
}

walk(root);

offenders.sort((a, b) => b.lineCount - a.lineCount);

if (offenders.length > 0) {
  console.error(`Frontend component/source size budget exceeded. Limit: ${maxLines} lines.`);
  for (const offender of offenders) {
    console.error(`- ${offender.path}: ${offender.lineCount} lines`);
  }
  process.exit(1);
}

console.log(`Frontend component/source size check passed. Limit: ${maxLines} lines.`);
