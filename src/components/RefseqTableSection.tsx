import React from 'react';
import Link from 'next/link';

interface RefseqTableSectionProps {
  species: string;
  preferredVersion: string;
  refseqUrl?: string;
  jsonUrl?: string;
  assemblyStatsUrl?: string;
  lastUpdated?: string;
}

export default function RefseqTableSection({ species, preferredVersion, refseqUrl, jsonUrl, assemblyStatsUrl, lastUpdated }: RefseqTableSectionProps) {
  const speciesLabel = species.replace(/_/g, ' ');
  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div className="flex-1 pr-0 md:pr-4">
          <h3 className="text-lg font-header font-semibold text-neutral-900 dark:text-neutral-100">Table of included RefSeq complete genomes</h3>
          <p className="text-neutral-700 dark:text-neutral-400 mt-1">
            A table of complete RefSeq genomes for <em>{speciesLabel}</em> used to calibrate this scheme. The file includes accessions, some sample information, genome size, GC content, and other key metrics.
          </p>
        </div>
        <div className="flex-shrink-0">
          {refseqUrl ? (
            <a href={refseqUrl} className="btn btn-primary" aria-label="Download RefSeq table">Download table</a>
          ) : jsonUrl ? (
            <a href={jsonUrl} className="btn btn-ghost" aria-label="Open RefSeq JSON">Open RefSeq JSON</a>
          ) : (
            <div className=" text-neutral-600 dark:text-neutral-400">RefSeq table not available.</div>
          )}
        </div>
      </div>

      {assemblyStatsUrl && (
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between border-t border-neutral-200 dark:border-neutral-700 pt-4">
          <div className="flex-1 pr-0 md:pr-4">
            <h3 className="text-lg font-header font-semibold text-neutral-900 dark:text-neutral-100">AllTheBacteria assembly inputs</h3>
            <p className="text-neutral-700 dark:text-neutral-400 mt-1">
              Per-assembly inputs the engine used to derive the <em>{speciesLabel}</em> reference distribution for this scheme: sample, sylph species call, N50, contig count, longest contig, total length, completeness, contamination, total coding sequences, genome size, GC content. Gzipped CSV.
            </p>
          </div>
          <div className="flex-shrink-0">
            <a href={assemblyStatsUrl} className="btn btn-primary" aria-label="Download assembly stats">Download table</a>
          </div>
        </div>
      )}
    </div>
  );
}
