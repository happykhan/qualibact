import fs from 'fs';
import path from 'path';
import Link from 'next/link';

const SCHEME_DESCRIPTIONS: Record<string, string> = {
  'REFSEQ-QC-v1':
    'Quality control of NCBI RefSeq reference genomes using simulated short reads, Shovill assembly, and CheckM2 completeness/contamination checks.',
  'qualibact-v1.0':
    'Species-specific thresholds derived from AllTheBacteria (2.4M genomes) and RefSeq complete genomes using Isolation Forest outlier detection.',
  'qualibact-v1.1':
    'Refined thresholds incorporating additional genome sets beyond AllTheBacteria, with species-specific adjustments to qualibact-v1.0 criteria.',
  'enterobase-v2.3':
    'Third-party assembly-QC cutoffs from the EnteroBase QA pipeline (Zhou et al., 2020). Genus-level, single-tier (FAIL only), applied only to species EnteroBase actively curates. Surfaced for side-by-side comparison; never the preferred scheme.',
};

export default function MethodsIndex() {
  const methodsDir = path.join(process.cwd(), 'content', 'methods');
  let schemes: string[] = [];
  try {
    schemes = fs
      .readdirSync(methodsDir, { withFileTypes: true })
      .filter((d) => d.isFile() && (d.name.endsWith('.mdx') || d.name.endsWith('.md')))
      .map((d) => d.name.replace(/\.mdx?$/, ''));
    // Explicit ordering: qualibact-v1.0 → v1.1 → REFSEQ (then any others
    // alphabetically). The default scheme is v1.0; v1.1 is the active
    // refinement track; REFSEQ is the reference-genome QC scheme.
    const ORDER = ['qualibact-v1.0', 'qualibact-v1.1', 'REFSEQ-QC-v1'];
    schemes.sort((a, b) => {
      const ia = ORDER.indexOf(a);
      const ib = ORDER.indexOf(b);
      if (ia !== -1 && ib !== -1) return ia - ib;
      if (ia !== -1) return -1;
      if (ib !== -1) return 1;
      return a.localeCompare(b);
    });
  } catch {
    schemes = [];
  }

  return (
    <div className="py-8">
      <div className="space-y-4">
        <h1 className="text-3xl font-header font-bold mb-2">Methods</h1>
        <p className="text-neutral-700 dark:text-neutral-300">
          Select a QC scheme to view its specific methods and notes.
        </p>
        {schemes.length === 0 ? (
          <div className="text-neutral-600 dark:text-neutral-400">No method pages available yet.</div>
        ) : (
          <ul className="space-y-3">
            {schemes.map((scheme) => (
              <li key={scheme}>
                <Link href={`/methods/${scheme}`} className="text-brand-600 hover:underline dark:text-brand-400 font-medium">
                  {scheme}
                </Link>
                {SCHEME_DESCRIPTIONS[scheme] && (
                  <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-0.5 ml-0">
                    {SCHEME_DESCRIPTIONS[scheme]}
                  </p>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
