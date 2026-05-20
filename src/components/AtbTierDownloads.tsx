import React from 'react';

interface Props {
  atbPassPath?: string | null;
  atbWarnPath?: string | null;
  atbFailPath?: string | null;
}

export default function AtbTierDownloads({ atbPassPath, atbWarnPath, atbFailPath }: Props) {
  if (!atbPassPath && !atbWarnPath && !atbFailPath) return null;
  return (
    <section className="card p-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <div className="font-semibold text-neutral-800 dark:text-neutral-200">All-The-Bacteria — PASS / WARN / FAIL genome lists</div>
          <p className="text-neutral-600 dark:text-neutral-400 mt-1">
            The published rounded thresholds (the values in the table above) were applied to the full AllTheBacteria-2024-08 set for this species. Each row carries the per-metric verdict and, where applicable, the reason a genome was demoted to WARN or FAIL. Files are gzipped CSV.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3 justify-end">
          {atbPassPath && <a href={atbPassPath} className="btn btn-primary">PASS genomes</a>}
          {atbWarnPath && <a href={atbWarnPath} className="btn btn-ghost">WARN genomes</a>}
          {atbFailPath && <a href={atbFailPath} className="btn btn-ghost">FAIL genomes</a>}
        </div>
      </div>
    </section>
  );
}
