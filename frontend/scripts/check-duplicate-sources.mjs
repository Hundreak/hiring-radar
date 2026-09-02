#!/usr/bin/env node
import {createHash} from 'node:crypto';
import {existsSync, readdirSync, readFileSync} from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const FRONTEND_ROOT = process.cwd();
const SOURCE_ROOT = path.join(FRONTEND_ROOT, 'src');
const EXTENSIONS = new Set(['.ts', '.tsx', '.js', '.jsx', '.css', '.json']);
const IGNORED_DIRS = new Set(['node_modules', '.next', 'out', 'coverage', 'dist', 'build']);

function walk(dir) {
  const entries = readdirSync(dir, {withFileTypes: true});
  const files = [];

  for (const entry of entries) {
    if (IGNORED_DIRS.has(entry.name)) continue;

    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...walk(fullPath));
      continue;
    }

    if (entry.isFile() && EXTENSIONS.has(path.extname(entry.name))) {
      files.push(fullPath);
    }
  }

  return files;
}

function fingerprint(filePath) {
  const content = readFileSync(filePath, 'utf8').replace(/\r\n/g, '\n').trim();
  return createHash('sha256').update(content).digest('hex');
}

if (!existsSync(SOURCE_ROOT)) {
  console.error(`Source directory not found: ${SOURCE_ROOT}`);
  process.exit(1);
}

const buckets = new Map();
for (const file of walk(SOURCE_ROOT)) {
  const statKey = fingerprint(file);
  const relativePath = path.relative(FRONTEND_ROOT, file);
  const bucket = buckets.get(statKey) ?? [];
  bucket.push(relativePath);
  buckets.set(statKey, bucket);
}

const duplicates = [...buckets.values()]
  .filter((paths) => paths.length > 1)
  .sort((left, right) => left[0].localeCompare(right[0]));

if (duplicates.length > 0) {
  console.error('Duplicate frontend source files detected. Keep one source of truth and replace route aliases with shared modules.');
  for (const group of duplicates) {
    console.error('\nDuplicate group:');
    for (const file of group) console.error(`  - ${file}`);
  }
  process.exit(1);
}

console.log('No duplicate frontend source files detected.');
