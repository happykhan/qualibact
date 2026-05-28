import Link from 'next/link';
import AttributionBlock from '@/components/AttributionBlock';

export interface ExternalSchemeNotes {
  /** What the matching genus block in the upstream config was called. */
  matchedBlock?: string;
  /** Metric (or aliasing) key -> upstream value, for criteria QualiBact doesn't model. */
  outOfScope?: Record<string, string>;
  /** Human-readable description of the source (e.g. EnteroBase QA pipeline notes). */
  source?: string;
}

interface Props {
  species: string;
  scheme: string;
  counts: {
    genome_count?: number;
    refseq_count?: number;
    pass_count?: number;
    warn_count?: number;
    fail_count?: number;
  };
  /** When present, the scheme is third-party (e.g. enterobase-v2.3); we surface
   *  the out-of-scope criteria here so users see what QualiBact's table omits. */
  externalNotes?: ExternalSchemeNotes;
  /** Optional authored MDX content rendered between the procedural intro and the attribution block. */
  children?: React.ReactNode;
}

function formatCount(n: number): string {
  return n.toLocaleString('en-US');
}

// Friendly labels + formatters for the upstream metric keys we surface
// when an external scheme (currently enterobase-v2.3) is the active view.
const EXTERNAL_METRIC_LABELS: Record<string, { label: string; format?: (v: string) => string }> = {
  'min accepted quality': {
    label: 'Minimum accepted base quality (phred)',
    format: (v) => `≥ ${v}`,
  },
  'max percent of low quality sites': {
    label: 'Maximum fraction of low-quality sites',
    format: (v) => {
      const n = Number(v);
      return Number.isFinite(n) ? `≤ ${(n * 100).toFixed(1)} %` : `≤ ${v}`;
    },
  },
  'proportion of correct species': {
    label: 'Minimum species-call agreement (Kraken)',
    format: (v) => {
      const n = Number(v);
      return Number.isFinite(n) ? `≥ ${(n * 100).toFixed(0)} %` : `≥ ${v}`;
    },
  },
  'allow species': {
    label: 'Also accepted under this block',
    format: (v) => v,
  },
};

export default function SchemeIntroBlock({ species, scheme, counts, externalNotes, children }: Props) {
  // counts.genome_count is the non-RefSeq (ATB) subset from the engine's
  // summary.csv; counts.refseq_count is the RefSeq subset. The full
  // dataset used to fit the distribution is the SUM.
  const other = counts.genome_count ?? 0;
  const refseq = counts.refseq_count ?? 0;
  const total = other + refseq;

  const bold = (n: number) => (
    <strong className="font-semibold text-neutral-900 dark:text-neutral-100">
      {formatCount(n)}
    </strong>
  );
  let derived: React.ReactNode;
  if (total === 0) {
    derived = 'No genome counts are available for this scheme.';
  } else if (refseq > 0 && other > 0) {
    derived = (
      <>Derived from {bold(total)} genomes: {bold(refseq)} from RefSeq and {bold(other)} from other sources.</>
    );
  } else if (refseq > 0) {
    derived = <>Derived from {bold(refseq)} RefSeq genomes.</>;
  } else {
    derived = <>Derived from {bold(total)} genomes.</>;
  }

  const pass = counts.pass_count;
  const warn = counts.warn_count;
  const fail = counts.fail_count;
  const haveTiers =
    typeof pass === 'number' && typeof warn === 'number' && typeof fail === 'number';
  const tierTotal = haveTiers ? (pass! + warn! + fail!) : 0;

  return (
    <div className="card p-6 space-y-4">
      <p className="text-neutral-700 dark:text-neutral-300">
        {derived}{' '}
        For the derivation pipeline and the PASS / WARN / FAIL verdict
        model, see the{' '}
        <Link
          href={`/methods/${scheme}`}
          className="text-brand-700 dark:text-brand-300 underline underline-offset-2 hover:text-brand-900 dark:hover:text-brand-200"
        >
          methods page for {scheme}
        </Link>.
      </p>

      {externalNotes && externalNotes.outOfScope && Object.keys(externalNotes.outOfScope).length > 0 && (
        <div className="rounded border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800/50 p-3 text-sm">
          <p className="font-semibold text-neutral-800 dark:text-neutral-200 mb-2">
            Additional criteria from {scheme}
            {externalNotes.matchedBlock && externalNotes.matchedBlock !== 'default' && (
              <span className="font-normal text-neutral-600 dark:text-neutral-400">
                {' '}(matched against the upstream <code className="font-mono text-xs">{externalNotes.matchedBlock}</code> block)
              </span>
            )}
          </p>
          <p className="text-neutral-600 dark:text-neutral-400 mb-2">
            QualiBact tracks only assembly-level metrics. The upstream scheme additionally checks the following, which aren&apos;t part of QualiBact&apos;s threshold table:
          </p>
          <dl className="grid grid-cols-1 sm:grid-cols-[auto,1fr] gap-x-4 gap-y-1">
            {Object.entries(externalNotes.outOfScope).map(([key, value]) => {
              const meta = EXTERNAL_METRIC_LABELS[key];
              return (
                <div key={key} className="contents">
                  <dt className="text-neutral-700 dark:text-neutral-300">{meta?.label ?? key}</dt>
                  <dd className="font-mono text-neutral-900 dark:text-neutral-100">
                    {meta?.format ? meta.format(value) : value}
                  </dd>
                </div>
              );
            })}
          </dl>
        </div>
      )}

      {haveTiers && tierTotal > 0 && (
        <p className="text-neutral-700 dark:text-neutral-300">
          Applied to the full All-The-Bacteria dataset, these thresholds
          place{' '}
          <strong className="text-emerald-700 dark:text-emerald-300">
            {formatCount(pass!)}
          </strong>{' '}
          genome{pass === 1 ? '' : 's'} at PASS,{' '}
          <strong className="text-amber-700 dark:text-amber-300">
            {formatCount(warn!)}
          </strong>{' '}
          at WARN, and{' '}
          <strong className="text-red-700 dark:text-red-300">
            {formatCount(fail!)}
          </strong>{' '}
          at FAIL ({formatCount(tierTotal)} assessed in total). The per-tier
          genome lists can be downloaded below in <code>.csv.gz</code> format;
          the FAIL list also records the reason each assembly was rejected.
        </p>
      )}

      {children}

      <AttributionBlock species={species} scheme={scheme} embedded />
    </div>
  );
}
