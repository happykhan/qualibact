import Link from 'next/link';
import AttributionBlock from '@/components/AttributionBlock';

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
  /** Optional authored MDX content rendered between the procedural intro and the attribution block. */
  children?: React.ReactNode;
}

function formatCount(n: number): string {
  return n.toLocaleString('en-US');
}

export default function SchemeIntroBlock({ species, scheme, counts, children }: Props) {
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
