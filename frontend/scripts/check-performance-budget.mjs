#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';

const ROOT = path.resolve(process.argv[2] || process.cwd());
const budgetPath = path.join(ROOT, 'performance-budget.json');

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function formatBytes(bytes) {
  const units = ['B', 'KiB', 'MiB', 'GiB'];
  let value = Number(bytes);
  let unit = units[0];
  for (let index = 0; index < units.length - 1 && value >= 1024; index += 1) {
    value /= 1024;
    unit = units[index + 1];
  }
  return `${value.toFixed(value >= 10 || unit === 'B' ? 0 : 1)} ${unit}`;
}

function walk(dir, predicate = () => true) {
  if (!fs.existsSync(dir)) {
    return [];
  }
  const entries = fs.readdirSync(dir, {withFileTypes: true});
  const results = [];
  for (const entry of entries) {
    if (entry.name === 'node_modules' || entry.name === '.git') {
      continue;
    }
    const entryPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...walk(entryPath, predicate));
      continue;
    }
    if (entry.isFile() && predicate(entryPath)) {
      results.push(entryPath);
    }
  }
  return results;
}

function relative(filePath) {
  return path.relative(ROOT, filePath).split(path.sep).join('/');
}

function gzipSize(filePath) {
  const input = fs.readFileSync(filePath);
  return zlib.gzipSync(input, {level: 9}).byteLength;
}

function fail(message) {
  failures.push(message);
}

if (!fs.existsSync(budgetPath)) {
  console.error(`Performance budget config not found: ${budgetPath}`);
  process.exit(1);
}

const budget = readJson(budgetPath);
const failures = [];
const warnings = [];

const publicDir = path.join(ROOT, 'public');
const publicExtensions = new Set(budget.public.assetExtensions || []);
const publicAssets = walk(publicDir, (filePath) => publicExtensions.has(path.extname(filePath).toLowerCase()));
const publicAssetStats = publicAssets.map((filePath) => ({
  path: relative(filePath),
  size: fs.statSync(filePath).size
}));
const publicTotalBytes = publicAssetStats.reduce((total, asset) => total + asset.size, 0);

if (publicTotalBytes > budget.public.maxTotalBytes) {
  fail(`Public asset total is ${formatBytes(publicTotalBytes)}; budget is ${formatBytes(budget.public.maxTotalBytes)}.`);
}

for (const asset of publicAssetStats) {
  if (asset.size > budget.public.maxAssetBytes) {
    fail(`${asset.path} is ${formatBytes(asset.size)}; per-asset public budget is ${formatBytes(budget.public.maxAssetBytes)}.`);
  }
}

const srcDir = path.join(ROOT, 'src');
const sourceFiles = walk(srcDir, (filePath) => ['.ts', '.tsx'].includes(path.extname(filePath).toLowerCase()));
for (const filePath of sourceFiles) {
  const size = fs.statSync(filePath).size;
  const rel = relative(filePath);
  if (size > budget.source.maxSourceFileBytes) {
    fail(`${rel} is ${formatBytes(size)}; source file budget is ${formatBytes(budget.source.maxSourceFileBytes)}.`);
  }
  if (rel.startsWith('src/app/') && size > budget.source.maxAppRouteFileBytes) {
    fail(`${rel} is ${formatBytes(size)}; app route file budget is ${formatBytes(budget.source.maxAppRouteFileBytes)}.`);
  }
}

const messageDir = path.join(ROOT, 'messages');
const messageFiles = walk(messageDir, (filePath) => path.extname(filePath).toLowerCase() === '.json');
for (const filePath of messageFiles) {
  const size = fs.statSync(filePath).size;
  if (size > budget.source.maxMessageFileBytes) {
    fail(`${relative(filePath)} is ${formatBytes(size)}; message file budget is ${formatBytes(budget.source.maxMessageFileBytes)}.`);
  }
}

const nextStaticDir = path.join(ROOT, '.next', 'static');
if (!fs.existsSync(nextStaticDir)) {
  if (budget.build.required) {
    fail('Next build artifacts are required for performance budget checks, but .next/static was not found. Run npm run build first.');
  } else {
    warnings.push('No .next/static build artifacts found; source/public budgets checked, build chunk budgets skipped.');
  }
} else if (process.env.HIRING_RADAR_PERF_SKIP_BUILD_BUDGET === '1') {
  warnings.push('Skipped Next build chunk budgets because HIRING_RADAR_PERF_SKIP_BUILD_BUDGET=1.');
} else {
  const jsChunks = walk(nextStaticDir, (filePath) => filePath.endsWith('.js'));
  const cssChunks = walk(nextStaticDir, (filePath) => filePath.endsWith('.css'));
  const jsGzipSizes = jsChunks.map((filePath) => ({path: relative(filePath), gzip: gzipSize(filePath)}));
  const cssGzipSizes = cssChunks.map((filePath) => ({path: relative(filePath), gzip: gzipSize(filePath)}));
  const totalJsGzip = jsGzipSizes.reduce((total, item) => total + item.gzip, 0);
  const totalCssGzip = cssGzipSizes.reduce((total, item) => total + item.gzip, 0);

  if (totalJsGzip > budget.build.maxTotalJsGzipBytes) {
    fail(`Total gzip JS chunk size is ${formatBytes(totalJsGzip)}; budget is ${formatBytes(budget.build.maxTotalJsGzipBytes)}.`);
  }
  if (totalCssGzip > budget.build.maxTotalCssGzipBytes) {
    fail(`Total gzip CSS chunk size is ${formatBytes(totalCssGzip)}; budget is ${formatBytes(budget.build.maxTotalCssGzipBytes)}.`);
  }
  for (const chunk of jsGzipSizes) {
    if (chunk.gzip > budget.build.maxSingleJsChunkGzipBytes) {
      fail(`${chunk.path} gzip size is ${formatBytes(chunk.gzip)}; single JS chunk budget is ${formatBytes(budget.build.maxSingleJsChunkGzipBytes)}.`);
    }
  }
  for (const chunk of cssGzipSizes) {
    if (chunk.gzip > budget.build.maxSingleCssChunkGzipBytes) {
      fail(`${chunk.path} gzip size is ${formatBytes(chunk.gzip)}; single CSS chunk budget is ${formatBytes(budget.build.maxSingleCssChunkGzipBytes)}.`);
    }
  }
}

const largestPublicAssets = publicAssetStats
  .sort((a, b) => b.size - a.size)
  .slice(0, 5)
  .map((asset) => `  - ${asset.path}: ${formatBytes(asset.size)}`)
  .join('\n') || '  - none';

console.log('Performance budget summary');
console.log(`- Public assets: ${formatBytes(publicTotalBytes)} / ${formatBytes(budget.public.maxTotalBytes)}`);
console.log(`- Source files checked: ${sourceFiles.length}`);
console.log(`- Message files checked: ${messageFiles.length}`);
console.log('- Largest public assets:');
console.log(largestPublicAssets);

for (const warning of warnings) {
  console.warn(`Warning: ${warning}`);
}

if (failures.length > 0) {
  console.error('\nPerformance budget failed:');
  for (const item of failures) {
    console.error(`- ${item}`);
  }
  console.error('\nFix options: compress/convert images, move heavy assets behind dynamic loading, split large route files, or intentionally raise the budget with a documented reason.');
  process.exit(1);
}

console.log('Performance budget check passed.');
