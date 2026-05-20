import fs from 'fs';
import path from 'path';
import yaml from 'js-yaml';

export interface Contributor {
  id: string;
  name: string;
  affiliation: string;
  country?: string;
  orcid?: string;
}

export interface Funding {
  id: string;
  name: string;
  note?: string;
  country?: string;
}

export interface Attribution {
  species: string;
  scheme: string;
  contributors: string[];
  funding?: string[];
  note?: string;
}

interface DataFile {
  contributors?: Contributor[];
  funding?: Funding[];
  attributions?: Attribution[];
}

let cached: DataFile | null = null;

function load(): DataFile {
  if (cached) return cached;
  const p = path.join(process.cwd(), 'content', 'contributors.yml');
  if (!fs.existsSync(p)) {
    cached = {};
    return cached;
  }
  cached = (yaml.load(fs.readFileSync(p, 'utf8')) as DataFile) ?? {};
  return cached;
}

export function getContributors(): Contributor[] {
  return load().contributors ?? [];
}

export function getFunding(): Funding[] {
  return load().funding ?? [];
}

export function getAttributions(): Attribution[] {
  return load().attributions ?? [];
}

export interface ResolvedAttribution {
  species: string;
  scheme: string;
  contributors: Contributor[];
  funding: Funding[];
  note?: string;
}

/** All attributions for a given (species, scheme) with names resolved. */
export function attributionsFor(species: string, scheme: string): ResolvedAttribution[] {
  const data = load();
  const contribById = new Map((data.contributors ?? []).map((c) => [c.id, c]));
  const fundingById = new Map((data.funding ?? []).map((f) => [f.id, f]));
  return (data.attributions ?? [])
    .filter((a) => a.species === species && a.scheme === scheme)
    .map((a) => ({
      species: a.species,
      scheme: a.scheme,
      contributors: a.contributors.map((id) => contribById.get(id)).filter(Boolean) as Contributor[],
      funding: (a.funding ?? []).map((id) => fundingById.get(id)).filter(Boolean) as Funding[],
      note: a.note,
    }));
}

/** Reverse index: for each contributor, which (species, scheme) pairs did they contribute to. */
export function contributionsByContributor(): Record<string, Attribution[]> {
  const out: Record<string, Attribution[]> = {};
  for (const a of getAttributions()) {
    for (const cid of a.contributors) {
      out[cid] = out[cid] ?? [];
      out[cid].push(a);
    }
  }
  return out;
}
