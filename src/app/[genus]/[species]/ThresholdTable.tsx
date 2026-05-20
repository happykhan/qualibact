'use client';

import { useState } from 'react';

export interface ThresholdRow {
  metric: string;
  /** Rounded FAIL bound from the engine's {Species}_metrics.csv — what downstream tools see. */
  rounded_lower: number | null;
  rounded_upper: number | null;
  /** Unrounded FAIL bound from summary.csv (engine's FINAL_LOWER / FINAL_UPPER). */
  raw_lower: number | null;
  raw_upper: number | null;
  /** Rounded WARN bound from the engine's {Species}_metrics.csv. */
  warn_lower: number | null;
  warn_upper: number | null;
  /** Unrounded WARN bound from summary.csv (engine's WARN_LOWER / WARN_UPPER). */
  raw_warn_lower: number | null;
  raw_warn_upper: number | null;
}

export interface ThresholdTableProps {
  rows: ThresholdRow[];
  summaryHasMy: boolean;
  metricsURL?: string;
}

function fmt(v: number | null | undefined): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return '-';
  if (Math.abs(v) >= 1000) return v.toLocaleString('en', { maximumFractionDigits: 0 });
  return v.toLocaleString('en', { maximumFractionDigits: 4 });
}

/**
 * GC_Content (and any other 1-decimal-friendly percentage metric)
 * gets aggressive directional rounding in the Rounded view:
 * - lower bounds floor to 1 decimal (open the door slightly wider)
 * - upper bounds ceil to 1 decimal (open the door slightly wider)
 * The engine emits GC at inconsistent precision (38.68 vs 38.8 vs 39.17),
 * which looked jagged on the published table.
 */
function gcRound(v: number | null | undefined, side: 'lower' | 'upper'): number | null | undefined {
  if (v === null || v === undefined || !Number.isFinite(v)) return v;
  return side === 'lower'
    ? Math.floor(v * 10) / 10
    : Math.ceil(v * 10) / 10;
}

function isGcRoundable(metric: string, mode: 'rounded' | 'raw'): boolean {
  return mode === 'rounded' && metric === 'GC_Content';
}

export default function ThresholdTable({ rows, summaryHasMy, metricsURL }: ThresholdTableProps) {
  const [mode, setMode] = useState<'rounded' | 'raw'>('rounded');

  return (
    <>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="inline-flex rounded-full border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-900 p-1">
          {(['rounded', 'raw'] as const).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setMode(m)}
              aria-pressed={mode === m}
              className={[
                'px-4 py-1 text-xs font-medium rounded-full transition-colors',
                mode === m
                  ? 'bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 shadow-sm'
                  : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100',
              ].join(' ')}
            >
              {m === 'rounded' ? 'Rounded (published)' : 'Raw (pre-rounding)'}
            </button>
          ))}
        </div>
        <p className="text-[11px] text-neutral-500 dark:text-neutral-400">
          {mode === 'rounded'
            ? 'Both Fail and Warn bands shown as the published rounded values — easier to cite and consistent across the species page, CSV downloads, and downstream QC tools.'
            : 'Both Fail and Warn bands shown as the engine’s unrounded statistical bounds, exactly as derived from the reference distribution.'}
        </p>
      </div>

      {!summaryHasMy && (
        <div className="mb-4 rounded border border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-950/40 px-3 py-2 text-xs text-amber-800 dark:text-amber-200">
          The reference data for this scheme is from an older engine run and doesn&apos;t carry the values needed to compute the warn / fail bands below. The engine is being re-run; bands will populate once that lands.
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-200 dark:border-neutral-700">
              <th className="py-2 pr-4 text-left font-semibold">Metric</th>
              <th className="py-2 px-4 text-right font-semibold text-red-700 dark:text-red-300">Fail below</th>
              <th className="py-2 px-4 text-right font-semibold text-amber-700 dark:text-amber-300">Warn below</th>
              <th className="py-2 px-4 text-right font-semibold text-amber-700 dark:text-amber-300">Warn above</th>
              <th className="py-2 pl-4 text-right font-semibold text-red-700 dark:text-red-300">Fail above</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => {
              let failLow = mode === 'rounded' ? row.rounded_lower : row.raw_lower;
              let failHigh = mode === 'rounded' ? row.rounded_upper : row.raw_upper;
              let warnLow = mode === 'rounded' ? row.warn_lower : row.raw_warn_lower;
              let warnHigh = mode === 'rounded' ? row.warn_upper : row.raw_warn_upper;
              if (isGcRoundable(row.metric, mode)) {
                failLow = gcRound(failLow, 'lower') ?? null;
                warnLow = gcRound(warnLow, 'lower') ?? null;
                warnHigh = gcRound(warnHigh, 'upper') ?? null;
                failHigh = gcRound(failHigh, 'upper') ?? null;
              }
              return (
                <tr key={row.metric} className={i % 2 === 0 ? '' : 'bg-neutral-50 dark:bg-neutral-800/50'}>
                  <td className="py-2 pr-4 font-mono">{row.metric}</td>
                  <td className="py-2 px-4 text-right font-mono text-red-700 dark:text-red-300">{fmt(failLow)}</td>
                  <td className="py-2 px-4 text-right font-mono text-amber-700 dark:text-amber-300">{fmt(warnLow)}</td>
                  <td className="py-2 px-4 text-right font-mono text-amber-700 dark:text-amber-300">{fmt(warnHigh)}</td>
                  <td className="py-2 pl-4 text-right font-mono text-red-700 dark:text-red-300">{fmt(failHigh)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="mt-3 text-xs text-neutral-500 dark:text-neutral-400">
        <strong>How to read this:</strong> a value between the two warn columns is typical for this species and
        passes QC. A value between a warn column and the corresponding fail column is borderline &mdash; worth a manual
        look but not an outright failure. A value outside the fail columns is unusual enough to fail QC.
      </p>

      {metricsURL && (
        <div className="mt-3 flex justify-end">
          <a href={metricsURL} className="btn btn-primary" download>
            Download CSV
          </a>
        </div>
      )}
    </>
  );
}
