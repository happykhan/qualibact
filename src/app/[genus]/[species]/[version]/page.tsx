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

function loadIndex(): { species: IndexEntry[] } | null {
  const p = path.join(process.cwd(), 'public', 'api', 'v2', 'index.json');
  if (!fs.existsSync(p)) return null;
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

export async function generateStaticParams() {
  const idx = loadIndex();
  if (!idx) return [];
  const params: { genus: string; species: string; version: string }[] = [];
  for (const entry of idx.species) {
    const genus = entry.species.split('_')[0];
    if (!genus) continue;
    for (const s of entry.schemes) {
      params.push({ genus, species: entry.species, version: s.scheme });
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
  const idx = loadIndex();
  if (!idx) notFound();

  const entry = idx.species.find((s) => s.species === species);
  if (!entry || !entry.schemes.find((s) => s.scheme === version)) {
    notFound();
  }
  const preferredVersion = entry.preferred_scheme ?? version;
  const allSchemes = entry.schemes.map((s) => s.scheme);

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
