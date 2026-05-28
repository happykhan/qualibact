#!/usr/bin/env node
// Spot-check that published thresholds are intact. Once a (species,
// scheme) pair is shipped, its numbers are frozen for the life of that
// scheme version — any change requires a new scheme version (v1.1 ->
// v1.2 etc.). This script doesn't snapshot every row; it spot-checks a
// hand-curated representative slice in
// scripts/baselines/spot-check-thresholds.json and asserts:
//
//   1. each fixture row appears in /api/v2/thresholds.json with the
//      expected numeric / source values, AND
//   2. (when page_url + page_substring are given) the formatted number
//      actually renders on the species page HTML in out/.
//
// Catches the high-signal regressions — a scheme silently mutating, a
// species page failing to display its pinned upper, etc. — without
// flagging every irrelevant float-rounding nudge.
//
// Usage:
//   node scripts/audit-thresholds-frozen.mjs

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const FIXTURE = path.join(REPO_ROOT, 'scripts', 'baselines', 'spot-check-thresholds.json');
const OUT_DIR = path.join(REPO_ROOT, 'out');
const PUBLIC_DIR = path.join(REPO_ROOT, 'public');

const thresholdsPath = [
  path.join(OUT_DIR, 'api', 'v2', 'thresholds.json'),
  path.join(PUBLIC_DIR, 'api', 'v2', 'thresholds.json'),
].find(fs.existsSync);
if (!thresholdsPath) {
  console.error('thresholds.json not found in out/ or public/. Run `npm run build` first.');
  process.exit(2);
}
const thresholds = JSON.parse(fs.readFileSync(thresholdsPath, 'utf8'));
const fixtureRaw = JSON.parse(fs.readFileSync(FIXTURE, 'utf8'));
const fixtures = fixtureRaw.filter((row) => row.species); // skip the leading _comment block

const failures = [];
let checked = 0;
let pageChecks = 0;

for (const f of fixtures) {
  const ctx = `${f.species}/${f.scheme}/${f.metric}`;
  const sp = thresholds.species?.[f.species];
  if (!sp) {
    failures.push(`${ctx}: species missing from /api/v2/thresholds.json`);
    continue;
  }
  const schemeBlob = sp.schemes?.[f.scheme];
  if (!schemeBlob) {
    failures.push(`${ctx}: scheme '${f.scheme}' missing for ${f.species}`);
    continue;
  }
  const row = schemeBlob.thresholds?.find((r) => r.metric === f.metric);
  if (!row) {
    failures.push(`${ctx}: metric '${f.metric}' missing from threshold rows`);
    continue;
  }
  checked++;
  for (const field of ['final_lower', 'final_upper', 'warn_lower', 'warn_upper', 'source']) {
    if (f[field] === undefined) continue; // fixture didn't assert this field
    if (JSON.stringify(row[field]) !== JSON.stringify(f[field])) {
      failures.push(
        `${ctx}: ${field} = ${JSON.stringify(row[field])}, expected ${JSON.stringify(f[field])}`,
      );
    }
  }

  // Optional: also verify the page renders the expected formatted number.
  if (f.page_url && f.page_substring && fs.existsSync(OUT_DIR)) {
    const trimmed = f.page_url.replace(/\/$/, '');
    const htmlCandidates = [
      path.join(OUT_DIR, f.page_url, 'index.html'),
      path.join(OUT_DIR, `${trimmed}.html`),
    ];
    const htmlPath = htmlCandidates.find(fs.existsSync);
    if (!htmlPath) {
      failures.push(`${ctx}: page ${f.page_url} not found in out/`);
      continue;
    }
    pageChecks++;
    const html = fs.readFileSync(htmlPath, 'utf8');
    if (!html.includes(f.page_substring)) {
      failures.push(
        `${ctx}: '${f.page_substring}' not found on rendered page ${f.page_url}`,
      );
    }
  } else if (f.page_url && fs.existsSync(OUT_DIR)) {
    // No substring asserted — just sanity-check the page exists.
    const trimmed = f.page_url.replace(/\/$/, '');
    const exists = [
      path.join(OUT_DIR, f.page_url, 'index.html'),
      path.join(OUT_DIR, `${trimmed}.html`),
    ].some(fs.existsSync);
    if (!exists) {
      failures.push(`${ctx}: page ${f.page_url} not found in out/`);
    }
  }
}

console.log(`Spot-checked ${checked}/${fixtures.length} API row(s), ${pageChecks} rendered-page substring(s).`);

if (failures.length === 0) {
  console.log('OK: spot-check passes — published thresholds and pages render as expected.');
  process.exit(0);
}

console.error(`\nFAIL: ${failures.length} spot-check violation(s):`);
for (const f of failures) console.error(`  - ${f}`);
console.error(
  '\nIf the change is intentional (publishing a new scheme version), update\n' +
    'scripts/baselines/spot-check-thresholds.json with the new expected values.',
);
process.exit(1);
