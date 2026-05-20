import InteractiveTable from '@/components/InteractiveTable';
import { staticUrl } from '@/lib/static-url';
import fs from 'fs';
import path from 'path';

interface ThresholdRow extends Record<string, unknown> {
  species: string;
  scheme: string;
  metric: string;
  engine: string;
  fail_below: number | string;
  warn_below: number | string;
  warn_above: number | string;
  fail_above: number | string;
}

interface StatRow extends Record<string, unknown> {
  species: string;
  metric: string;
  count: number | string;
  mean: number | string;
  median: number | string;
  std: number | string;
  q1: number | string;
  q3: number | string;
  refseq_count: number | string;
}

interface CountRow extends Record<string, unknown> {
  species: string;
  scheme: string;
  engine: string;
  total_genome_count: number | string;
  non_refseq_count: number | string;
  refseq_count: number | string;
  pass_count: number | string;
  warn_count: number | string;
  fail_count: number | string;
}

function readCsv(file: string): { headers: string[]; rows: string[][] } {
  if (!fs.existsSync(file)) return { headers: [], rows: [] };
  const text = fs.readFileSync(file, 'utf8');
  const lines = text.trim().split('\n');
  if (lines.length < 2) return { headers: [], rows: [] };
  const headers = lines[0].split(',').map((h) => h.trim());
  const rows = lines.slice(1).map((line) => line.split(','));
  return { headers, rows };
}

function toNum(v: string): number | string {
  const s = v.trim();
  if (s === '') return '';
  const n = Number(s);
  return Number.isFinite(n) ? n : s;
}

function loadAggregateThresholds(): ThresholdRow[] {
  const { headers, rows } = readCsv(
    path.join(process.cwd(), 'public', 'api', 'v2', 'thresholds.csv')
  );
  if (!headers.length) return [];
  const ix = (col: string) => headers.indexOf(col);
  const iSp = ix('species');
  const iSc = ix('scheme');
  const iMe = ix('metric');
  const iLo = ix('lower');
  const iUp = ix('upper');
  const iMl = ix('ml_lower');
  const iMu = ix('ml_upper');
  const iEng = ix('engine_severity');
  if (iSp < 0 || iLo < 0) return [];
  return rows.map((cells) => {
    const lowerStr = (cells[iLo] ?? '').trim();
    const upperStr = (cells[iUp] ?? '').trim();
    // Side-suppress warn boundaries that have no published fail counterpart.
    return {
      species: (cells[iSp] ?? '').trim(),
      scheme: (cells[iSc] ?? '').trim(),
      metric: (cells[iMe] ?? '').trim(),
      engine: iEng >= 0 ? (cells[iEng] ?? '').trim() : '',
      fail_below: toNum(lowerStr),
      warn_below: lowerStr === '' ? '' : toNum((cells[iMl] ?? '').trim()),
      warn_above: upperStr === '' ? '' : toNum((cells[iMu] ?? '').trim()),
      fail_above: toNum(upperStr),
    };
  });
}

function loadStats(): StatRow[] {
  const { headers, rows } = readCsv(
    path.join(process.cwd(), 'public', 'static', 'summary', 'summary_statistics.csv')
  );
  if (!headers.length) return [];
  const ix = (col: string) => headers.indexOf(col);
  const i = {
    species: ix('species'),
    metric: ix('metric'),
    count: ix('count'),
    mean: ix('mean'),
    median: ix('median'),
    std: ix('std'),
    q1: ix('q1'),
    q3: ix('q3'),
    refseq_count: ix('refseq_count'),
  };
  return rows.map((c) => ({
    species: (c[i.species] ?? '').trim().replace(/_/g, ' '),
    metric: (c[i.metric] ?? '').trim(),
    count: toNum(c[i.count] ?? ''),
    mean: toNum(c[i.mean] ?? ''),
    median: toNum(c[i.median] ?? ''),
    std: toNum(c[i.std] ?? ''),
    q1: toNum(c[i.q1] ?? ''),
    q3: toNum(c[i.q3] ?? ''),
    refseq_count: toNum(c[i.refseq_count] ?? ''),
  }));
}

function loadCounts(): CountRow[] {
  const { headers, rows } = readCsv(
    path.join(process.cwd(), 'public', 'static', 'summary', 'species_counts.csv')
  );
  if (!headers.length) return [];
  const ix = (col: string) => headers.indexOf(col);
  const i = {
    species: ix('species'),
    scheme: ix('scheme'),
    engine: ix('engine_severity'),
    total_genome_count: ix('total_genome_count'),
    non_refseq_count: ix('non_refseq_count'),
    refseq_count: ix('refseq_count'),
    pass_count: ix('pass_count'),
    warn_count: ix('warn_count'),
    fail_count: ix('fail_count'),
  };
  return rows.map((c) => ({
    species: (c[i.species] ?? '').trim(),
    scheme: i.scheme >= 0 ? (c[i.scheme] ?? '').trim() : '',
    engine: i.engine >= 0 ? (c[i.engine] ?? '').trim() : '',
    total_genome_count: toNum(c[i.total_genome_count] ?? ''),
    non_refseq_count: toNum(c[i.non_refseq_count] ?? ''),
    refseq_count: toNum(c[i.refseq_count] ?? ''),
    pass_count: toNum(c[i.pass_count] ?? ''),
    warn_count: toNum(c[i.warn_count] ?? ''),
    fail_count: toNum(c[i.fail_count] ?? ''),
  }));
}

const THRESHOLD_COLUMNS = [
  { key: 'species', label: 'Species', sortable: true, type: 'string' as const, italic: true },
  { key: 'scheme', label: 'Scheme', sortable: true, type: 'string' as const },
  { key: 'engine', label: 'Engine flag', sortable: true, type: 'string' as const, renderAs: 'badge' as const },
  { key: 'metric', label: 'Metric', sortable: true, type: 'string' as const },
  { key: 'fail_below', label: 'Fail below', sortable: true, type: 'number' as const },
  { key: 'warn_below', label: 'Warn below', sortable: true, type: 'number' as const },
  { key: 'warn_above', label: 'Warn above', sortable: true, type: 'number' as const },
  { key: 'fail_above', label: 'Fail above', sortable: true, type: 'number' as const },
];

const STAT_COLUMNS = [
  { key: 'species', label: 'Species', sortable: true, type: 'string' as const, italic: true },
  { key: 'metric', label: 'Metric', sortable: true, type: 'string' as const },
  { key: 'count', label: 'n', sortable: true, type: 'number' as const },
  { key: 'mean', label: 'Mean', sortable: true, type: 'number' as const },
  { key: 'median', label: 'Median', sortable: true, type: 'number' as const },
  { key: 'std', label: 'SD', sortable: true, type: 'number' as const },
  { key: 'q1', label: 'Q1', sortable: true, type: 'number' as const },
  { key: 'q3', label: 'Q3', sortable: true, type: 'number' as const },
  { key: 'refseq_count', label: 'RefSeq n', sortable: true, type: 'number' as const },
];

const COUNT_COLUMNS = [
  { key: 'species', label: 'Species', sortable: true, type: 'string' as const, italic: true },
  { key: 'scheme', label: 'Scheme', sortable: true, type: 'string' as const },
  { key: 'engine', label: 'Engine flag', sortable: true, type: 'string' as const, renderAs: 'badge' as const },
  { key: 'total_genome_count', label: 'Total genomes', sortable: true, type: 'number' as const },
  { key: 'non_refseq_count', label: 'Other sources', sortable: true, type: 'number' as const },
  { key: 'refseq_count', label: 'RefSeq', sortable: true, type: 'number' as const },
  { key: 'pass_count', label: 'PASS', sortable: true, type: 'number' as const },
  { key: 'warn_count', label: 'WARN', sortable: true, type: 'number' as const },
  { key: 'fail_count', label: 'FAIL', sortable: true, type: 'number' as const },
];

function DownloadButton({ href, name, label }: { href: string; name: string; label: string }) {
  return (
    <a
      href={href}
      download={name}
      className="inline-flex items-center gap-2 px-4 py-2 bg-brand-600 text-white rounded hover:bg-brand-700 transition-colors text-sm whitespace-nowrap"
    >
      {label}
    </a>
  );
}

export default function Summary() {
  const thresholds = loadAggregateThresholds();
  const stats = loadStats();
  const counts = loadCounts();
  const xlsxExists = (rel: string) =>
    fs.existsSync(path.join(process.cwd(), 'public', ...rel.split('/').filter(Boolean)));
  const hasXlsx = xlsxExists('/api/v2/thresholds.xlsx');
  const hasStatsXlsx = xlsxExists('/static/summary/summary_statistics.xlsx');
  const hasCountsXlsx = xlsxExists('/static/summary/species_counts.xlsx');

  return (
    <div className="py-8 space-y-12">
      <header>
        <h1 className="text-3xl font-bold font-header mb-3">Summary</h1>
        <p className="text-neutral-700 dark:text-neutral-300 max-w-3xl">
          Downloadable tables of QualiBact thresholds and reference distributions
          across every species, derived from each species&apos; preferred QC
          scheme. The <a href="#quality-criteria" className="underline">quality
          criteria table</a> below is the primary dataset; the other tables
          describe the reference distributions those thresholds were fit from.
          For programmatic access see the{' '}
          <a href="#api" className="underline">API endpoints</a> section.
        </p>
      </header>

      {/* Primary table — visually elevated. */}
      <section
        id="quality-criteria"
        className="rounded-lg border-2 border-brand-600/30 dark:border-brand-400/30 bg-brand-50/40 dark:bg-brand-900/10 p-6"
      >
        <div className="flex flex-wrap items-start justify-between gap-4 mb-2">
          <div>
            <span className="inline-block text-xs font-semibold uppercase tracking-wider text-brand-700 dark:text-brand-300 mb-1">
              Primary dataset
            </span>
            <h2 className="text-2xl font-bold font-header">Quality criteria</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            <DownloadButton
              href={staticUrl('/api/v2/thresholds.csv')}
              name="qualibact-thresholds.csv"
              label="Download CSV"
            />
            {hasXlsx && (
              <DownloadButton
                href={staticUrl('/api/v2/thresholds.xlsx')}
                name="qualibact-thresholds.xlsx"
                label="Download Excel"
              />
            )}
          </div>
        </div>
        <p className="text-neutral-700 dark:text-neutral-300 mb-4 max-w-3xl">
          Per-species, per-metric quality thresholds. Each row gives four
          boundaries: <strong>Fail below</strong> and <strong>Fail above</strong>{' '}
          are the published cut-offs that downstream tools consume;{' '}
          <strong>Warn below</strong> and <strong>Warn above</strong> are the
          tighter inner boundaries derived from the reference distribution. A
          value inside the warn range passes, between warn and fail it warns,
          and outside fail it fails. This is the same data the per-species
          pages render.
        </p>
        {thresholds.length > 0 ? (
          <InteractiveTable
            data={thresholds}
            columns={THRESHOLD_COLUMNS}
            searchPlaceholder="Search by species, scheme, or metric..."
            initialPageSize={10}
          />
        ) : (
          <p className="text-sm text-neutral-500">Threshold table unavailable.</p>
        )}
      </section>

      <section id="summary-statistics">
        <div className="flex flex-wrap items-start justify-between gap-4 mb-2">
          <h2 className="text-2xl font-bold font-header">Summary statistics</h2>
          <div className="flex flex-wrap gap-2">
            <DownloadButton
              href={staticUrl('/static/summary/summary_statistics.csv')}
              name="summary_statistics.csv"
              label="Download CSV"
            />
            {hasStatsXlsx && (
              <DownloadButton
                href={staticUrl('/static/summary/summary_statistics.xlsx')}
                name="summary_statistics.xlsx"
                label="Download Excel"
              />
            )}
          </div>
        </div>
        <p className="text-neutral-700 dark:text-neutral-300 mb-4 max-w-3xl">
          Per-metric distribution statistics for each species (preferred QC
          scheme only). The preview below shows the most useful columns; the
          full CSV also includes RefSeq comparison statistics (KS test,
          Wasserstein distance) and pre-filter bounds. Useful for building your
          own thresholds or diagnosing how a candidate assembly sits within the
          reference distribution.
        </p>
        {stats.length > 0 ? (
          <InteractiveTable
            data={stats}
            columns={STAT_COLUMNS}
            searchPlaceholder="Search by species or metric..."
            initialPageSize={10}
          />
        ) : (
          <p className="text-sm text-neutral-500">Summary statistics unavailable.</p>
        )}
      </section>

      <section id="species-counts">
        <div className="flex flex-wrap items-start justify-between gap-4 mb-2">
          <h2 className="text-2xl font-bold font-header">Species count summary</h2>
          <div className="flex flex-wrap gap-2">
            <DownloadButton
              href={staticUrl('/static/summary/species_counts.csv')}
              name="species_counts.csv"
              label="Download CSV"
            />
            {hasCountsXlsx && (
              <DownloadButton
                href={staticUrl('/static/summary/species_counts.xlsx')}
                name="species_counts.xlsx"
                label="Download Excel"
              />
            )}
          </div>
        </div>
        <p className="text-neutral-700 dark:text-neutral-300 mb-4 max-w-3xl">
          Per species: how many reference genomes contributed to the thresholds
          (split between RefSeq and other sources), the engine&apos;s quality
          flag for that reference dataset, and how the published thresholds
          partition the broader All-The-Bacteria dataset into PASS / WARN /
          FAIL tiers. Use this to sanity-check thresholds for species with
          small reference sets or non-PASS engine flags.
        </p>
        {counts.length > 0 ? (
          <InteractiveTable
            data={counts}
            columns={COUNT_COLUMNS}
            searchPlaceholder="Search by species..."
            initialPageSize={10}
          />
        ) : (
          <p className="text-sm text-neutral-500">Species counts unavailable.</p>
        )}
      </section>

      <section id="api" className="border-t border-neutral-200 dark:border-neutral-700 pt-8">
        <h2 className="text-2xl font-bold font-header mb-3">API endpoints</h2>
        <p className="text-neutral-700 dark:text-neutral-300 mb-4 max-w-3xl">
          QualiBact ships a small set of versioned static endpoints under{' '}
          <code className="font-mono text-sm">/api/v2/</code> so that downstream
          tools can fetch thresholds without scraping HTML. These files are
          regenerated on every site build from the per-species manifests.
        </p>
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700 text-sm">
            <thead>
              <tr className="bg-neutral-50 dark:bg-neutral-700">
                <th className="px-4 py-2 text-left border-b">Endpoint</th>
                <th className="px-4 py-2 text-left border-b">What it is</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="px-4 py-2 border-b font-mono">
                  <a className="text-brand-600 hover:underline" href={staticUrl('/api/v2/thresholds.csv')}>
                    /api/v2/thresholds.csv
                  </a>
                </td>
                <td className="px-4 py-2 border-b">
                  Long-form CSV: one row per (species, scheme, metric) with
                  fail/warn lower &amp; upper bounds. The source for the table
                  above.
                </td>
              </tr>
              <tr className="bg-neutral-50 dark:bg-neutral-700">
                <td className="px-4 py-2 border-b font-mono">
                  <a className="text-brand-600 hover:underline" href={staticUrl('/api/v2/thresholds.json')}>
                    /api/v2/thresholds.json
                  </a>
                </td>
                <td className="px-4 py-2 border-b">
                  Same data as the CSV but JSON-keyed and grouped, easier for
                  programmatic consumption.
                </td>
              </tr>
              {hasXlsx && (
                <tr>
                  <td className="px-4 py-2 border-b font-mono">
                    <a className="text-brand-600 hover:underline" href={staticUrl('/api/v2/thresholds.xlsx')}>
                      /api/v2/thresholds.xlsx
                    </a>
                  </td>
                  <td className="px-4 py-2 border-b">
                    Same rows as the CSV, packaged as an Excel workbook for
                    direct opening in spreadsheet software.
                  </td>
                </tr>
              )}
              <tr>
                <td className="px-4 py-2 border-b font-mono">
                  <a className="text-brand-600 hover:underline" href={staticUrl('/api/v2/index.json')}>
                    /api/v2/index.json
                  </a>
                </td>
                <td className="px-4 py-2 border-b">
                  Manifest: schema version, generation timestamp, list of
                  available species and the endpoint paths.
                </td>
              </tr>
              <tr className="bg-neutral-50 dark:bg-neutral-700">
                <td className="px-4 py-2 border-b font-mono">
                  /static/species/&#123;species&#125;/&#123;scheme&#125;/manifest.json
                </td>
                <td className="px-4 py-2 border-b">
                  Per-species, per-scheme bundle: thresholds, distribution
                  summary, plot URLs, and warning flags. One file per pair —
                  the same one the per-species pages read.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-3">
          The path prefix <code className="font-mono">v2</code> means the schema
          will not break compatibly. A schema change that does break consumers
          gets a new prefix (<code className="font-mono">v3</code>) and{' '}
          <code className="font-mono">v2</code> stays in place until usage drops.
        </p>
      </section>
    </div>
  );
}
