import type { MetadataRoute } from 'next';
import fs from 'fs';
import path from 'path';

export const dynamic = 'force-static';

interface IndexEntry {
  species: string;
  schemes: { scheme: string }[];
}

export default function sitemap(): MetadataRoute.Sitemap {
  const base = 'https://qualibact.org';
  const now = new Date();

  const entries: MetadataRoute.Sitemap = [
    { url: `${base}/`, lastModified: now, changeFrequency: 'monthly', priority: 1.0 },
    { url: `${base}/species/`, lastModified: now, changeFrequency: 'weekly', priority: 0.9 },
    { url: `${base}/summary/`, lastModified: now, changeFrequency: 'weekly', priority: 0.8 },
    { url: `${base}/priority-pathogens/`, lastModified: now, changeFrequency: 'monthly', priority: 0.8 },
    { url: `${base}/priority-pathogens/2017/`, lastModified: now, changeFrequency: 'yearly', priority: 0.4 },
    { url: `${base}/compare/`, lastModified: now, changeFrequency: 'monthly', priority: 0.7 },
    { url: `${base}/methods/`, lastModified: now, changeFrequency: 'monthly', priority: 0.6 },
    { url: `${base}/contributing/`, lastModified: now, changeFrequency: 'monthly', priority: 0.4 },
    { url: `${base}/organism-requests/`, lastModified: now, changeFrequency: 'monthly', priority: 0.4 },
    { url: `${base}/faq/`, lastModified: now, changeFrequency: 'monthly', priority: 0.4 },
  ];

  const idxPath = path.join(process.cwd(), 'public', 'api', 'v2', 'index.json');
  if (!fs.existsSync(idxPath)) return entries;

  const idx = JSON.parse(fs.readFileSync(idxPath, 'utf8')) as { species: IndexEntry[] };
  const genera = new Set<string>();

  for (const entry of idx.species) {
    const genus = entry.species.split('_')[0];
    if (genus) genera.add(genus);
    entries.push({
      url: `${base}/${genus}/${entry.species}/`,
      lastModified: now,
      changeFrequency: 'weekly',
      priority: 0.7,
    });
    for (const s of entry.schemes) {
      entries.push({
        url: `${base}/${genus}/${entry.species}/${s.scheme}/`,
        lastModified: now,
        changeFrequency: 'weekly',
        priority: 0.6,
      });
    }
  }

  for (const genus of genera) {
    entries.push({
      url: `${base}/${genus}/`,
      lastModified: now,
      changeFrequency: 'weekly',
      priority: 0.6,
    });
  }

  return entries;
}
