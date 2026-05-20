import fs from 'fs';
import path from 'path';
import yaml from 'js-yaml';

export interface PriorityEntry {
  name: string;
  resistance: string;
  species?: string;
  /** When no direct species/genus match exists, link to this species as the closest available proxy. */
  proxySpecies?: string;
  genusGroup?: string[];
  note?: string;
}

export interface PriorityTier {
  name: 'Critical' | 'High' | 'Medium';
  entries: PriorityEntry[];
}

export interface PriorityList {
  year: number;
  citation: string;
  citationUrl?: string;
  tiers: PriorityTier[];
}

interface DataFile {
  lists: PriorityList[];
}

function loadData(): DataFile {
  const p = path.join(process.cwd(), 'content', 'who-priority', 'data.yml');
  return yaml.load(fs.readFileSync(p, 'utf8')) as DataFile;
}

export function getList(year: number): PriorityList {
  const data = loadData();
  const list = data.lists.find((l) => l.year === year);
  if (!list) {
    throw new Error(`No WHO priority list for year ${year}`);
  }
  return list;
}

interface ApiIndexEntry {
  species: string;
}

interface ApiIndex {
  species: ApiIndexEntry[];
}

let cachedIndex: Set<string> | null = null;

function loadSpeciesSet(): Set<string> {
  if (cachedIndex) return cachedIndex;
  const p = path.join(process.cwd(), 'public', 'api', 'v2', 'index.json');
  const data = JSON.parse(fs.readFileSync(p, 'utf8')) as ApiIndex;
  cachedIndex = new Set(data.species.map((s) => s.species));
  return cachedIndex;
}

export function speciesExists(species: string): boolean {
  return loadSpeciesSet().has(species);
}

export function genusSpeciesList(genus: string): string[] {
  const all = loadSpeciesSet();
  return Array.from(all).filter((k) => k.startsWith(`${genus}_`)).sort();
}

export function speciesHref(species: string): string {
  const [genus] = species.split('_');
  return `/${genus}/${species}`;
}

export function genusHref(genus: string): string {
  return `/${genus}`;
}
