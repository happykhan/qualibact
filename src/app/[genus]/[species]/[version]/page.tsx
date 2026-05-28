import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import fs from 'fs';
import path from 'path';
import SchemeDetails from '../SchemeDetails';

interface VersionPageProps {
  params: Promise<{ genus: string; species: string; version: string }>;
}

interface IndexEntry {
  species: string;
  name?: string;
  preferred_scheme?: string;
  schemes: { scheme: string; manifest_url: string }[];
}

function loadIndex(p: string): { species: IndexEntry[] } | null {
  if (!fs.existsSync(p)) return null;
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

// We pre-render species pages for every (species, scheme) pair across
// both the canonical /api/v2/index.json (QualiBact's own schemes) and
// /api/v2/external/index.json (third-party schemes like enterobase-v2.3).
// Without merging both, external scheme routes wouldn't get static
// params and the build would 404 them.
export async function generateStaticParams() {
  const idxs = [
    loadIndex(path.join(process.cwd(), 'public', 'api', 'v2', 'index.json')),
    loadIndex(path.join(process.cwd(), 'public', 'api', 'v2', 'external', 'index.json')),
  ].filter((x): x is { species: IndexEntry[] } => x !== null);
  const seen = new Set<string>();
  const params: { genus: string; species: string; version: string }[] = [];
  for (const idx of idxs) {
    for (const entry of idx.species) {
      const genus = entry.species.split('_')[0];
      if (!genus) continue;
      for (const s of entry.schemes) {
        const key = `${entry.species}/${s.scheme}`;
        if (seen.has(key)) continue;
        seen.add(key);
        params.push({ genus, species: entry.species, version: s.scheme });
      }
    }
  }
  return params;
}

export async function generateMetadata({ params }: VersionPageProps): Promise<Metadata> {
  const { species, version } = await params;
  const prettyName = species.replace(/_/g, ' ');
  return {
    title: `${prettyName} - ${version}`,
    description: `QC scheme ${version} thresholds and metrics for ${prettyName} genome assemblies.`,
  };
}

export default async function VersionPage({ params }: VersionPageProps) {
  const { genus, species, version } = await params;
  // Look in both indices — canonical first (so the preferred-scheme
  // hint is sourced from QualiBact's own registry), then the external
  // registry for third-party schemes.
  const qbIdx = loadIndex(path.join(process.cwd(), 'public', 'api', 'v2', 'index.json'));
  const extIdx = loadIndex(path.join(process.cwd(), 'public', 'api', 'v2', 'external', 'index.json'));

  const qbEntry = qbIdx?.species.find((s) => s.species === species);
  const extEntry = extIdx?.species.find((s) => s.species === species);
  const entry = qbEntry ?? extEntry;
  if (!entry) notFound();

  const allSchemeSet = new Set<string>([
    ...(qbEntry?.schemes.map((s) => s.scheme) ?? []),
    ...(extEntry?.schemes.map((s) => s.scheme) ?? []),
  ]);
  if (!allSchemeSet.has(version)) notFound();

  const preferredVersion = qbEntry?.preferred_scheme ?? version;
  const allSchemes = [...allSchemeSet];

  return (
    <div className="py-8">
      <div className="space-y-8">
        <h1 className="text-3xl font-bold font-header">
          QC Scheme: {version} for <em>{species.replace(/_/g, ' ')}</em>
        </h1>
        <SchemeDetails species={species} version={version} />

        {allSchemes.length > 1 && (
          <div className="card p-6 space-y-4">
            <h3 className="text-xl font-semibold font-header text-neutral-800 dark:text-neutral-200">
              All QC schemes for this species
            </h3>
            <div className="flex flex-wrap gap-3">
              {allSchemes.map((v) => (
                <a
                  key={v}
                  href={`/${genus}/${species}/${v}`}
                  className={`inline-flex items-center px-4 py-2 rounded-full border ${
                    v === version
                      ? 'border-brand-600 bg-brand-50 dark:bg-brand-900'
                      : 'border-brand-500'
                  } text-brand-600 dark:text-brand-300 hover:bg-brand-50 dark:hover:bg-brand-900`}
                  aria-current={v === version ? 'page' : undefined}
                >
                  {v === preferredVersion && v !== version
                    ? `${v} (preferred)`
                    : v === version
                    ? `${v} (current)`
                    : v}
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
