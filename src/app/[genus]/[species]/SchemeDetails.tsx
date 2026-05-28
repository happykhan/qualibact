import fs from 'fs';
import path from 'path';
import MarkdownRenderer from '@/components/MarkdownRenderer';
import CdsGenomePlot from '@/components/CdsGenomePlot';
import MetricRefseqPlotGroup from '@/components/MetricRefseqPlotGroup';
import RefseqTableSection from '@/components/RefseqTableSection';
import MetricsSummaryCard from '@/components/MetricsSummaryCard';
import AtbTierDownloads from '@/components/AtbTierDownloads';
import FilteredPlotGrid from '@/components/FilteredPlotGrid';
import SchemeIntroBlock from '@/components/SchemeIntroBlock';
import AttributionBlock from '@/components/AttributionBlock';
import EngineFlagsBanner from '@/components/EngineFlagsBanner';
import { staticUrl } from '@/lib/static-url';
import ThresholdTable, { type ThresholdRow as TableRow } from './ThresholdTable';

interface Props {
  species: string;
  version: string;
}

interface ThresholdRow {
  metric: string;
  lower: number | string | null;
  upper: number | string | null;
  /** Rounded WARN bounds from engine's {Species}_metrics.csv (via build_manifests.py). */
  warn_lower?: number | null;
  warn_upper?: number | null;
  /** Legacy aggregate fields kept for backwards compatibility (unused by this page). */
  ml_lower?: number | null;
  ml_upper?: number | null;
  auto_lower?: number | null;
  auto_upper?: number | null;
  refseq_lower?: number | null;
  refseq_upper?: number | null;
}

interface EngineFlagSignal {
  signal: string;
  flag: 'info' | 'warn' | 'error' | string;
  fraction?: number | null;
  count?: number | null;
  n?: number | null;
  interpretation?: string | null;
}

interface EngineFlags {
  severity?: 'info' | 'warn' | 'error' | null;
  low_count_flag?: string | null;
  fired_signals?: EngineFlagSignal[];
}

// The legacy fail-buffer helpers used to compute WARN bounds from FAIL ±
// buffer. Now the engine emits both tiers natively (read via manifest
// warn_lower/upper + summary.csv WARN_LOWER/UPPER), so these are
// retained only for documentation purposes.

interface Manifest {
  schema_version: string;
  species: string;
  scheme: string;
  counts: { genome_count: number; refseq_count: number; final_count?: number; filtered_out_count?: number };
  warnings: {
    low_genome: boolean;
    species_separation: boolean;
    notes: string[];
    engine?: EngineFlags;
  };
  thresholds: ThresholdRow[];
  plots: Record<string, unknown>;
  filtered_plot_files: string[];
  has_cds_plot: boolean;
  sidecars: Record<string, string | null>;
}

function loadSchemeManifest(species: string, version: string): Manifest | null {
  const p = path.join(process.cwd(), 'public', 'static', 'species', species, version, 'manifest.json');
  if (!fs.existsSync(p)) return null;
  try {
    return JSON.parse(fs.readFileSync(p, 'utf8')) as Manifest;
  } catch {
    return null;
  }
}

export default async function SchemeDetails({ species, version }: Props) {
  const speciesPath = `static/species/${species}/${version}`;

  // Phase B: load the per-(species, scheme) manifest directly instead of
  // walking website_summary.json. The manifest is self-contained — all
  // thresholds, plot inventory, counts, warnings, sidecar paths.
  const manifest = loadSchemeManifest(species, version);
  if (!manifest) return null;

  // MDX content is optional — only used for authored notes specific
  // to this (species, scheme), e.g. rationale paragraphs or contributor
  // attributions. The boilerplate intro (counts, methods link) is
  // rendered procedurally by SchemeIntroBlock below, so MDX is no
  // longer required for every scheme.
  const mdxPath = path.join(process.cwd(), 'content', species, `${version}.mdx`);
  const rawMarkdown = fs.existsSync(mdxPath) ? fs.readFileSync(mdxPath, 'utf8') : '';
  // Strip frontmatter + any whitespace-only body so we can decide
  // whether to render the MDX card at all.
  const bodyMatch = rawMarkdown.match(/^---\n[\s\S]*?\n---\n*([\s\S]*)$/);
  const markdownBody = (bodyMatch ? bodyMatch[1] : rawMarkdown).trim();
  const hasAuthoredContent = markdownBody.length > 0;

  // External (third-party) schemes ship an `enterobase-notes.json` (or
  // similar) sidecar with the criteria QualiBact deliberately doesn't
  // track in its threshold table. Pull it in so SchemeIntroBlock can
  // surface those values on the species page.
  let externalNotes: { matchedBlock?: string; outOfScope?: Record<string, string>; source?: string } | undefined;
  const externalNotesPath = path.join(
    process.cwd(), 'public', 'static', 'species', species, version, 'enterobase-notes.json'
  );
  if (fs.existsSync(externalNotesPath)) {
    try {
      const raw = JSON.parse(fs.readFileSync(externalNotesPath, 'utf8'));
      externalNotes = {
        matchedBlock: raw.matched_block,
        outOfScope: raw.out_of_scope_for_qualibact,
        source: raw.source,
      };
    } catch {
      externalNotes = undefined;
    }
  }

  // Sidecar file URLs come straight from the manifest.sidecars block;
  // values are full relative paths under public/static/species/, so we
  // just prepend /static/species/.
  const sidecars = manifest.sidecars || {};
  const staticSpecies = (p: string | null | undefined) => (p ? staticUrl(`/static/species/${p}`) : undefined);

  const refseqUrl = staticSpecies(sidecars.refseq_archive);
  const jsonUrl = staticSpecies(sidecars.species_json);
  const metricsURL = staticSpecies(sidecars.metrics_csv);
  const assemblyStatsPath = staticSpecies(sidecars.assembly_stats_archive);
  const atbPassPath = staticSpecies(sidecars.atb_pass_archive);
  const atbWarnPath = staticSpecies(sidecars.atb_warn_archive);
  const atbFailPath = staticSpecies(sidecars.atb_fail_archive);
  const hasSummary = !!sidecars.summary_csv;

  // RefSeq metric plots from manifest plots data
  const refseqMetrics: { metric: string; hist?: string; qq?: string }[] = [];
  const plots = manifest.plots || {};
  for (const [metric, plotData] of Object.entries(plots)) {
    if (metric === 'CDS_vs_Genome_Size') continue;
    if (typeof plotData === 'object' && plotData !== null) {
      const pd = plotData as { histogram_kde?: string; qqplot?: string };
      const hist = pd.histogram_kde ? staticUrl(`/static/species/${pd.histogram_kde}`) : undefined;
      const qq = pd.qqplot ? staticUrl(`/static/species/${pd.qqplot}`) : undefined;
      if (hist || qq) {
        refseqMetrics.push({ metric, hist, qq });
      }
    }
  }

  // CDS plot from manifest
  let cdsPath: string | undefined;
  if (manifest.has_cds_plot) {
    const cdsPlotPath = plots.CDS_vs_Genome_Size;
    if (typeof cdsPlotPath === 'string') {
      cdsPath = staticUrl(`/static/species/${cdsPlotPath}`);
    } else {
      cdsPath = staticUrl(`/${speciesPath}/${species}_CDS_vs_Genome_Size.png`);
    }
  }

  // Filtered plots from manifest file list
  const filteredItems: { filename: string; path: string }[] = [];
  const filteredFiles: string[] = manifest.filtered_plot_files || [];
  for (const f of filteredFiles) {
    filteredItems.push({ filename: f, path: staticUrl(`/${speciesPath}/filtered_plots/${f}`) });
  }

  const thresholds: ThresholdRow[] = manifest.thresholds || [];

  // Per-metric stats from summary.csv. We pull FINAL_LOWER / FINAL_UPPER (the
  // ML-adjusted bounds the engine emits) as the WARN-band edges, and
  // compute FAIL as MY_* ± 10% — a fixed safety buffer beyond the
  // ML-validated range so borderline assemblies get flagged rather than
  // outright rejected. See WORKPLAN-v1.1.md, decision 2026-05-13.
  interface DistStats {
    median: number; q1: number; q3: number; count: number;
    /** Additional summary stats from summary.csv — distribution shape +
     *  mean / std / min / max — for the collapsed summary table below
     *  the threshold card. */
    distribution: string | null;
    mean: number | null;
    std: number | null;
    min: number | null;
    max: number | null;
    /** Engine's unrounded FINAL_LOWER / FINAL_UPPER — the raw FAIL bound. */
    myLower: number | null; myUpper: number | null;
    /** Engine's unrounded WARN_LOWER / WARN_UPPER — the raw WARN bound. */
    warnLowerRaw: number | null; warnUpperRaw: number | null;
  }
  const METRIC_ALIASES: Record<string, string> = {
    Completeness: 'Completeness_Specific',
    number: 'no_of_contigs',
  };
  const distByMetric = new Map<string, DistStats>();
  let summaryHasMy = false;
  const summaryCsvPath = path.join(process.cwd(), 'public', 'static', 'species', species, version, 'summary.csv');
  if (fs.existsSync(summaryCsvPath)) {
    const csv = fs.readFileSync(summaryCsvPath, 'utf8').trim().split('\n');
    if (csv.length >= 2) {
      const header = csv[0].split(',').map((h) => h.trim());
      const ix = (col: string) => header.indexOf(col);
      const iMetric = ix('metric');
      const iMedian = ix('median');
      const iQ1 = ix('q1');
      const iQ3 = ix('q3');
      const iCount = ix('count');
      const iDistribution = ix('distribution');
      const iMean = ix('mean');
      const iStd = ix('std');
      const iMin = ix('min');
      const iMax = ix('max');
      const iMyLower = ix('FINAL_LOWER');
      const iMyUpper = ix('FINAL_UPPER');
      const iWarnLower = ix('WARN_LOWER');
      const iWarnUpper = ix('WARN_UPPER');
      summaryHasMy = iMyLower >= 0 && iMyUpper >= 0;
      if (iMetric >= 0 && iMedian >= 0 && iQ1 >= 0 && iQ3 >= 0) {
        for (let r = 1; r < csv.length; r++) {
          const cells = csv[r].split(',');
          const rawMetric = (cells[iMetric] || '').trim();
          if (!rawMetric) continue;
          const metric = METRIC_ALIASES[rawMetric] ?? rawMetric;
          let median = Number(cells[iMedian]);
          let q1 = Number(cells[iQ1]);
          let q3 = Number(cells[iQ3]);
          const count = iCount >= 0 ? Number(cells[iCount]) : NaN;
          let myLower = iMyLower >= 0 ? Number(cells[iMyLower]) : NaN;
          let myUpper = iMyUpper >= 0 ? Number(cells[iMyUpper]) : NaN;
          let warnLowerRaw = iWarnLower >= 0 ? Number(cells[iWarnLower]) : NaN;
          let warnUpperRaw = iWarnUpper >= 0 ? Number(cells[iWarnUpper]) : NaN;
          // Engine output stores GC_Content inconsistently — sometimes as a
          // fraction (0–1), sometimes as a percentage (0–100), and sometimes
          // mixed within a single row (e.g. FINAL_LOWER=0.3009 alongside
          // FINAL_UPPER=31). Normalise each value individually rather than at
          // row level.
          const toPct = (n: number) => (metric === 'GC_Content' && Number.isFinite(n) && Math.abs(n) <= 1.5) ? n * 100 : n;
          median = toPct(median);
          q1 = toPct(q1);
          q3 = toPct(q3);
          if (Number.isFinite(myLower)) myLower = toPct(myLower);
          if (Number.isFinite(myUpper)) myUpper = toPct(myUpper);
          if (Number.isFinite(warnLowerRaw)) warnLowerRaw = toPct(warnLowerRaw);
          if (Number.isFinite(warnUpperRaw)) warnUpperRaw = toPct(warnUpperRaw);
          // Extra summary stats — used to render the collapsed
          // "Summary statistics" table inside MetricsSummaryCard.
          const distribution = iDistribution >= 0 ? (cells[iDistribution] || '').trim() || null : null;
          let mean = iMean >= 0 ? Number(cells[iMean]) : NaN;
          const std = iStd >= 0 ? Number(cells[iStd]) : NaN;
          let min = iMin >= 0 ? Number(cells[iMin]) : NaN;
          let max = iMax >= 0 ? Number(cells[iMax]) : NaN;
          if (Number.isFinite(mean)) mean = toPct(mean);
          if (Number.isFinite(min)) min = toPct(min);
          if (Number.isFinite(max)) max = toPct(max);
          // std doesn't get GC unit-normalised (it's a spread, not a value)

          if (Number.isFinite(median) && Number.isFinite(q1) && Number.isFinite(q3)) {
            distByMetric.set(metric, {
              median, q1, q3, count,
              distribution,
              mean: Number.isFinite(mean) ? mean : null,
              std: Number.isFinite(std) ? std : null,
              min: Number.isFinite(min) ? min : null,
              max: Number.isFinite(max) ? max : null,
              warnLowerRaw: Number.isFinite(warnLowerRaw) ? warnLowerRaw : null,
              warnUpperRaw: Number.isFinite(warnUpperRaw) ? warnUpperRaw : null,
              myLower: Number.isFinite(myLower) ? myLower : null,
              myUpper: Number.isFinite(myUpper) ? myUpper : null,
            });
          }
        }
      }
    }
  }
  // counts.genome_count is the non-RefSeq subset; total used for the
  // reference distribution = non_refseq + refseq.
  const nonRefseqCount = manifest.counts.genome_count ?? 0;
  const refSeqCount = manifest.counts.refseq_count ?? 0;
  const nGenomes = nonRefseqCount + refSeqCount;
  // FAIL boundary = WARN ± buffer. Sizes / counts get a proportional 10%
  // buffer; percentage metrics get a fixed ±1 pp because biology doesn't
  // tolerate proportional swings on a 0–100 scale (a genome 2% off the
  // species GC mean is a different species, not "borderline").
  const PCT_METRICS = new Set(['GC_Content', 'Completeness_Specific', 'Contamination']);
  function failLowerFor(metric: string, warn: number): number {
    return PCT_METRICS.has(metric) ? warn - 1 : warn * 0.9;
  }
  function failUpperFor(metric: string, warn: number): number {
    return PCT_METRICS.has(metric) ? warn + 1 : warn * 1.1;
  }

  // Authored caveats from content/species-notes.yml — folded into the
  // engine flag banner below so we have one warning surface, not two.
  const speciesNotes: string[] = manifest.warnings.notes || [];

  // Engine self-report (flags.json) is the canonical warning surface.
  // The legacy low_genome / species_separation booleans now come through
  // as the engine's low_count_flag / quality_signals — no duplicate
  // amber banner needed.
  const engineFlags = manifest.warnings.engine;

  return (
    <div className="w-full max-w-7xl mx-auto space-y-6">
      <EngineFlagsBanner
        severity={engineFlags?.severity}
        fired={engineFlags?.fired_signals}
        lowCountFlag={engineFlags?.low_count_flag}
        nonRefseqCount={nonRefseqCount}
        notes={speciesNotes}
      />

      <SchemeIntroBlock species={species} scheme={version} counts={manifest.counts} externalNotes={externalNotes}>
        {hasAuthoredContent && <MarkdownRenderer content={markdownBody} />}
      </SchemeIntroBlock>

      <MetricsSummaryCard
        species={species}
        version={version}
        hasSummary={hasSummary}
        summaryStats={Array.from(distByMetric.entries()).map(([metric, d]) => ({
          metric,
          distribution: d.distribution,
          count: Number.isFinite(d.count) ? d.count : null,
          mean: d.mean,
          std: d.std,
          min: d.min,
          q1: d.q1,
          median: d.median,
          q3: d.q3,
          max: d.max,
        }))}
      />

      {thresholds.length > 0 && (
        <section className="card p-6">
          <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2 mb-3">
            <h3 className="font-header font-semibold text-neutral-900 dark:text-neutral-100">
              Suggested thresholds for <em>{species.replace(/_/g, ' ')}</em> ({version})
            </h3>
            {nGenomes > 0 && (
              <p className="text-xs text-neutral-600 dark:text-neutral-400">
                Derived from{' '}
                <span className="font-semibold text-neutral-800 dark:text-neutral-200">
                  {nGenomes.toLocaleString('en')}
                </span>{' '}
                genomes
                {refSeqCount > 0 && (
                  <>
                    {' '}including{' '}
                    <span className="font-semibold text-neutral-800 dark:text-neutral-200">
                      {refSeqCount.toLocaleString('en')}
                    </span>{' '}
                    RefSeq references
                  </>
                )}
              </p>
            )}
          </div>

          <ThresholdTable
            rows={thresholds.map((row): TableRow => {
              const dist = distByMetric.get(row.metric);
              // FAIL bound — rounded comes from manifest (engine metrics.csv),
              // raw comes from summary.csv FINAL_LOWER / FINAL_UPPER.
              const failRoundedLow = row.lower === '' || row.lower === null || row.lower === undefined ? null : Number(row.lower);
              const failRoundedHigh = row.upper === '' || row.upper === null || row.upper === undefined ? null : Number(row.upper);
              const failRawLow = dist?.myLower ?? null;
              const failRawHigh = dist?.myUpper ?? null;
              // WARN bound — rounded comes from manifest.warn_lower / warn_upper
              // (engine metrics.csv WARN_lower/upper), raw comes from
              // summary.csv WARN_LOWER / WARN_UPPER.
              const wrLow = row.warn_lower == null ? null : Number(row.warn_lower);
              const wrHigh = row.warn_upper == null ? null : Number(row.warn_upper);
              const warnRoundedLow = Number.isFinite(wrLow) ? wrLow : null;
              const warnRoundedHigh = Number.isFinite(wrHigh) ? wrHigh : null;
              const warnRawLow = dist?.warnLowerRaw ?? null;
              const warnRawHigh = dist?.warnUpperRaw ?? null;
              // Side suppression: only show a side if the FAIL has a
              // published bound on that side.
              return {
                metric: row.metric,
                rounded_lower: failRoundedLow !== null ? failRoundedLow : null,
                rounded_upper: failRoundedHigh !== null ? failRoundedHigh : null,
                raw_lower: failRoundedLow !== null ? failRawLow : null,
                raw_upper: failRoundedHigh !== null ? failRawHigh : null,
                warn_lower: failRoundedLow !== null ? warnRoundedLow : null,
                warn_upper: failRoundedHigh !== null ? warnRoundedHigh : null,
                raw_warn_lower: failRoundedLow !== null ? warnRawLow : null,
                raw_warn_upper: failRoundedHigh !== null ? warnRawHigh : null,
              };
            })}
            summaryHasMy={summaryHasMy}
            metricsURL={metricsURL}
            hideModeToggle={!!externalNotes}
          />
        </section>
      )}

      <AtbTierDownloads
        atbPassPath={atbPassPath}
        atbWarnPath={atbWarnPath}
        atbFailPath={atbFailPath}
      />

      {cdsPath && (
        <div className="card p-6">
          <h2 className="text-xl font-semibold mb-3 font-header text-neutral-900 dark:text-neutral-100">CDS vs Genome Size</h2>
          <CdsGenomePlot src={cdsPath} />
        </div>
      )}

      {refseqMetrics.length > 0 && (
        <div className="card p-6 space-y-3">
          <h2 className="text-xl font-semibold mb-1 font-header text-neutral-900 dark:text-neutral-100">RefSeq distributions</h2>
          <MetricRefseqPlotGroup species={species} version={version} initialMetrics={refseqMetrics} />
        </div>
      )}

      {/* RefSeq + assembly-stats downloads only make sense for QualiBact's
          own (calibrated-from-data) schemes. External schemes like
          enterobase-v2.3 don't ship a reference cohort, so the whole
          card would just read "RefSeq table not available" — hide it. */}
      {(refseqUrl || jsonUrl || assemblyStatsPath) && (
        <div className="card p-6">
          <RefseqTableSection species={species} preferredVersion={version} refseqUrl={refseqUrl} jsonUrl={jsonUrl} assemblyStatsUrl={assemblyStatsPath} />
        </div>
      )}

      {filteredItems.length > 0 && (
        <div className="card p-6">
          <h2 className="text-xl font-semibold mb-2 font-header text-neutral-900 dark:text-neutral-100">Filtered plots</h2>
          <FilteredPlotGrid items={filteredItems} />
        </div>
      )}
    </div>
  );
}
