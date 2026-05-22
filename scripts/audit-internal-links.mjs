#!/usr/bin/env node
// Internal-link audit. Run AFTER `next build` — walks the static export
// in out/ and verifies every <a href="/..."> resolves to a page or file
// in the same export. Catches stale routes like /requests when the
// actual page lives at /organism-requests/.
//
// Exits non-zero on the first broken link list.
//
// Usage:
//   npm run build && node scripts/audit-internal-links.mjs

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT_DIR = path.join(REPO_ROOT, 'out');
const PUBLIC_DIR = path.join(REPO_ROOT, 'public');

// Hosts on R2 that aren't in `out/` — links to /static/... and a couple
// of bulky endpoints under /api/v2/ get served from R2 in production, so
// they shouldn't fail the audit if missing locally.
const R2_PREFIXES = ['/static/'];

if (!fs.existsSync(OUT_DIR)) {
  console.error(`out/ not found — run \`npm run build\` first (${OUT_DIR})`);
  process.exit(2);
}

/** Recursively walk a directory, yielding absolute file paths. */
function* walk(dir) {
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) yield* walk(p);
    else yield p;
  }
}

// Extract internal hrefs from a chunk of HTML. We only care about absolute
// site paths (starting with /), and we strip the #anchor before lookup.
// Both <a href="..."> and <link href="..."> count; the latter catches
// preloaded routes, sitemaps, etc.
const HREF_RE = /\s(?:href|src)="(\/[^"#?]*)/g;

function extractLinks(html) {
  const out = new Set();
  for (const m of html.matchAll(HREF_RE)) out.add(m[1]);
  return out;
}

/** Does path `p` resolve to something inside out/ or public/ (R2-bound)? */
function resolveLink(p) {
  if (R2_PREFIXES.some((pref) => p.startsWith(pref))) {
    // Best-effort local check — also accept if the file is in public/static/.
    const local = path.join(REPO_ROOT, p);
    if (fs.existsSync(local)) return 'r2-or-local';
    return 'r2-only'; // production-only, we trust R2 here
  }
  const trimmed = p.replace(/\/$/, '');
  const candidates = [
    path.join(OUT_DIR, p, 'index.html'),
    path.join(OUT_DIR, `${trimmed}.html`),
    path.join(OUT_DIR, p),
    path.join(OUT_DIR, trimmed),
    path.join(PUBLIC_DIR, p),
    path.join(PUBLIC_DIR, trimmed),
  ];
  for (const c of candidates) {
    if (fs.existsSync(c) && !fs.statSync(c).isDirectory()) return c;
    if (fs.existsSync(c) && fs.statSync(c).isDirectory()) {
      const idx = path.join(c, 'index.html');
      if (fs.existsSync(idx)) return idx;
    }
  }
  return null;
}

const broken = []; // { from, to }
const seenLinks = new Set();
let pagesScanned = 0;

for (const file of walk(OUT_DIR)) {
  if (!file.endsWith('.html')) continue;
  pagesScanned++;
  const html = fs.readFileSync(file, 'utf8');
  const links = extractLinks(html);
  for (const link of links) {
    const key = `${file}\t${link}`;
    if (seenLinks.has(key)) continue;
    seenLinks.add(key);
    // Skip Next.js internal chunks (their .js / .css always exist when build succeeds)
    if (link.startsWith('/_next/')) continue;
    const resolved = resolveLink(link);
    if (!resolved) {
      broken.push({
        from: path.relative(OUT_DIR, file),
        to: link,
      });
    }
  }
}

console.log(`Scanned ${pagesScanned} HTML pages, ${seenLinks.size} unique link occurrences.`);

if (broken.length > 0) {
  console.error(`\nFAIL: ${broken.length} broken internal link(s):\n`);
  // Group by target to keep output readable.
  const byTarget = new Map();
  for (const b of broken) {
    if (!byTarget.has(b.to)) byTarget.set(b.to, []);
    byTarget.get(b.to).push(b.from);
  }
  const sorted = [...byTarget.entries()].sort((a, b) => b[1].length - a[1].length);
  for (const [to, froms] of sorted) {
    console.error(`  ${to}  (linked from ${froms.length} page${froms.length === 1 ? '' : 's'})`);
    for (const f of froms.slice(0, 3)) console.error(`    ↪ ${f}`);
    if (froms.length > 3) console.error(`    ↪ … and ${froms.length - 3} more`);
  }
  process.exit(1);
}

console.log('OK: no broken internal links.');
