import React from 'react';
import Link from 'next/link';
import { staticUrl } from '@/lib/static-url';

export interface SummaryStatRow {
  metric: string;
  distribution: string | null;
  count: number | null;
  mean: number | null;
  std: number | null;
  min: number | null;
  q1: number | null;
  median: number | null;
  q3: number | null;
  max: number | null;
}

interface Props {
  species: string;
  version: string;
  hasSummary: boolean;
  summaryStats?: SummaryStatRow[];
}

function fmt(v: number | null | undefined, opts?: { decimals?: number }): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return '–';
  const dec = opts?.decimals;
  if (Math.abs(v) >= 1000) return v.toLocaleString('en', { maximumFractionDigits: dec ?? 0 });
  return v.toLocaleString('en', { maximumFractionDigits: dec ?? 2 });
}

export default async function MetricsSummaryCard({
  species, version, hasSummary, summaryStats,
}: Props) {
  const staticPrefix = staticUrl(`/static/species/${species}/${version}`);

  return (
    <section className="mb-6 w-full mt-4">
      <div className="card p-4 flex flex-col gap-3">
        <div className="space-y-3">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div>
                <div className="font-semibold text-neutral-800 dark:text-neutral-200">Summary table</div>
                <p className=" text-neutral-600 dark:text-neutral-400 mt-1">
                  This table summarises the distribution of each metric, including standard deviation, mean, median, and percentiles.
                </p>
                <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
                  A combined summary table across all species is available on the{' '}
                  <Link
                    href="/summary"
                    className="text-brand-700 dark:text-brand-300 underline underline-offset-2 hover:text-brand-900 dark:hover:text-brand-200"
                  >
                    summary page
                  </Link>.
                </p>
              </div>
              {hasSummary && (
                <div className="flex flex-wrap gap-2 justify-end">
                  <a href={`${staticPrefix}/summary.csv`} className="btn btn-primary">summary.csv</a>
                </div>
              )}
            </div>
          {!hasSummary && <div className="text-neutral-500 text-sm">Summary CSVs not available.</div>}
          {summaryStats && summaryStats.length > 0 && (
            <details className="mt-2 group">
              <summary className="cursor-pointer text-sm text-brand-700 dark:text-brand-300 hover:underline select-none">
                Show summary statistics inline
              </summary>
              <div className="mt-3 overflow-x-auto">
                <table className="min-w-full text-xs">
                  <thead>
                    <tr className="border-b border-neutral-200 dark:border-neutral-700 text-neutral-600 dark:text-neutral-400">
                      <th className="py-1.5 pr-3 text-left font-semibold">Metric</th>
                      <th className="py-1.5 px-2 text-left font-semibold">Distribution</th>
                      <th className="py-1.5 px-2 text-right font-semibold">n</th>
                      <th className="py-1.5 px-2 text-right font-semibold">Mean</th>
                      <th className="py-1.5 px-2 text-right font-semibold">SD</th>
                      <th className="py-1.5 px-2 text-right font-semibold">Min</th>
                      <th className="py-1.5 px-2 text-right font-semibold">Q1</th>
                      <th className="py-1.5 px-2 text-right font-semibold">Median</th>
                      <th className="py-1.5 px-2 text-right font-semibold">Q3</th>
                      <th className="py-1.5 pl-2 text-right font-semibold">Max</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summaryStats.map((r, i) => (
                      <tr key={r.metric} className={i % 2 === 0 ? '' : 'bg-neutral-50 dark:bg-neutral-800/50'}>
                        <td className="py-1 pr-3 font-mono">{r.metric}</td>
                        <td className="py-1 px-2 text-neutral-600 dark:text-neutral-400">{r.distribution ?? '–'}</td>
                        <td className="py-1 px-2 text-right font-mono">{r.count != null ? r.count.toLocaleString('en') : '–'}</td>
                        <td className="py-1 px-2 text-right font-mono">{fmt(r.mean)}</td>
                        <td className="py-1 px-2 text-right font-mono">{fmt(r.std)}</td>
                        <td className="py-1 px-2 text-right font-mono">{fmt(r.min)}</td>
                        <td className="py-1 px-2 text-right font-mono">{fmt(r.q1)}</td>
                        <td className="py-1 px-2 text-right font-mono">{fmt(r.median)}</td>
                        <td className="py-1 px-2 text-right font-mono">{fmt(r.q3)}</td>
                        <td className="py-1 pl-2 text-right font-mono">{fmt(r.max)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="text-[11px] text-neutral-500 dark:text-neutral-400 mt-2">
                  Full statistics including KS test vs RefSeq and Wasserstein distance are in the downloadable <code>summary.csv</code>.
                </p>
              </div>
            </details>
          )}
        </div>

      </div>
    </section>
  );
}
