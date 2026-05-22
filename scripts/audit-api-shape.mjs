#!/usr/bin/env node
// /api/v2/ public-contract validator. Run AFTER `next build` (or against
// public/ if the build hasn't run) — asserts the shape of the JSON blobs
// downstream consumers (SpecCheck, Kleborate, the MCP) depend on.
//
// Hand-rolled checks (no Zod / Ajv) to keep CI deps light. Fail-fast:
// exits non-zero on the first violation with a useful message.
//
// Usage:
//   node scripts/audit-api-shape.mjs

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT = path.join(REPO_ROOT, 'out');
const PUBLIC_ = path.join(REPO_ROOT, 'public');

function load(rel) {
  const tried = [path.join(OUT, rel), path.join(PUBLIC_, rel)];
  for (const p of tried) {
    if (fs.existsSync(p)) return { path: p, data: JSON.parse(fs.readFileSync(p, 'utf8')) };
  }
  fail(`could not find ${rel} in either out/ or public/`);
}

const failures = [];
function fail(msg) {
  failures.push(msg);
}
function assert(cond, msg) {
  if (!cond) failures.push(msg);
}

// ----- /api/v2/index.json --------------------------------------------------

const idx = load('api/v2/index.json');
console.log(`Checking ${path.relative(REPO_ROOT, idx.path)}`);
assert(typeof idx.data === 'object' && idx.data !== null, 'index.json: top-level must be object');
assert(typeof idx.data.schema_version === 'string', 'index.json: schema_version (string) missing');
assert(typeof idx.data.generated_at === 'string', 'index.json: generated_at (string) missing');
assert(typeof idx.data.species_count === 'number', 'index.json: species_count (number) missing');
assert(Array.isArray(idx.data.species), 'index.json: species must be an array');
if (Array.isArray(idx.data.species) && idx.data.species.length > 0) {
  const sample = idx.data.species[0];
  assert(typeof sample.species === 'string', 'index.json: species[i].species (string) missing');
  assert(Array.isArray(sample.schemes), 'index.json: species[i].schemes must be an array');
  assert(
    sample.schemes.every((s) => typeof s.scheme === 'string'),
    'index.json: every species[i].schemes[j].scheme must be a string',
  );
}
// Cross-check: declared species_count matches the array length.
if (Array.isArray(idx.data.species) && typeof idx.data.species_count === 'number') {
  assert(
    idx.data.species.length === idx.data.species_count,
    `index.json: species_count=${idx.data.species_count} but species.length=${idx.data.species.length}`,
  );
}

// ----- /api/v2/thresholds.json --------------------------------------------

const t = load('api/v2/thresholds.json');
console.log(`Checking ${path.relative(REPO_ROOT, t.path)}`);
assert(typeof t.data.species === 'object' && t.data.species !== null, 'thresholds.json: species must be a dict');
const firstSpeciesKey = Object.keys(t.data.species ?? {})[0];
if (firstSpeciesKey) {
  const spBlob = t.data.species[firstSpeciesKey];
  assert(
    typeof spBlob.schemes === 'object' && spBlob.schemes !== null,
    `thresholds.json: ${firstSpeciesKey}.schemes must be a dict`,
  );
  const firstSchemeKey = Object.keys(spBlob.schemes ?? {})[0];
  if (firstSchemeKey) {
    const schemeBlob = spBlob.schemes[firstSchemeKey];
    assert(
      Array.isArray(schemeBlob.thresholds),
      `thresholds.json: ${firstSpeciesKey}.schemes.${firstSchemeKey}.thresholds must be an array`,
    );
    if (Array.isArray(schemeBlob.thresholds) && schemeBlob.thresholds.length > 0) {
      const row = schemeBlob.thresholds[0];
      for (const k of ['metric', 'final_lower', 'final_upper', 'warn_lower', 'warn_upper', 'source']) {
        assert(k in row, `thresholds.json: ${firstSpeciesKey}/${firstSchemeKey} threshold row missing key '${k}'`);
      }
      assert(typeof row.metric === 'string', `thresholds.json: metric must be a string`);
      assert(typeof row.source === 'string', `thresholds.json: source must be a string`);
    }
  }
}

// Cross-reference: every species in index.json should appear in thresholds.json
if (Array.isArray(idx.data.species)) {
  const tKeys = new Set(Object.keys(t.data.species ?? {}));
  const missing = idx.data.species
    .map((s) => s.species)
    .filter((sp) => !tKeys.has(sp));
  assert(
    missing.length === 0,
    `cross-ref: ${missing.length} species in index.json but missing from thresholds.json (e.g. ${missing.slice(0, 3).join(', ')})`,
  );
}

// ----- /api/v2/thresholds.csv (header sanity only) -------------------------

const csvCandidates = [path.join(OUT, 'api/v2/thresholds.csv'), path.join(PUBLIC_, 'api/v2/thresholds.csv')];
let csvPath = null;
for (const c of csvCandidates) if (fs.existsSync(c)) { csvPath = c; break; }
if (csvPath) {
  console.log(`Checking ${path.relative(REPO_ROOT, csvPath)} (header only)`);
  const header = fs.readFileSync(csvPath, 'utf8').split('\n', 1)[0].split(',');
  const required = ['species', 'scheme', 'metric', 'FINAL_lower', 'FINAL_upper', 'WARN_lower', 'WARN_upper', 'source'];
  for (const col of required) {
    assert(header.includes(col), `thresholds.csv header missing column '${col}' (got ${header.length} cols: ${header.slice(0, 8).join(', ')}...)`);
  }
} else {
  console.warn('thresholds.csv not found — skipping CSV header check.');
}

// ----- summary --------------------------------------------------------------

if (failures.length > 0) {
  console.error(`\nFAIL: ${failures.length} contract violation(s):`);
  for (const f of failures) console.error(`  - ${f}`);
  process.exit(1);
}
console.log('\nOK: /api/v2/ public contract intact.');
